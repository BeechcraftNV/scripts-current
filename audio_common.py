#!/usr/bin/env python3
"""
audio_common.py - Shared helpers for the audio-normalization pipeline.

Used by:
    - normalize_audio.py (manual bulk runs)
    - audio_worker.py    (systemd-driven queue worker)

Provides: atomic lock, ffprobe/loudnorm wrappers, free-space guard,
tmp-path helper that preserves the original container extension, and a
single transcode implementation both callers share.
"""

import json
import logging
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

# --- Config defaults ---
AUDIO_BITRATE  = "192k"
LOUDNORM       = "loudnorm=I=-16:TP=-1.5:LRA=11"
LUFS_TARGET    = -16.0
LUFS_THRESHOLD = 1.5
MIN_FREE_GB    = 5

# LUFS measurement: long files are sampled at several spread-out windows rather
# than decoded in full (the result only feeds the +/-LUFS_THRESHOLD skip gate).
LUFS_SAMPLE_WINDOWS      = 4      # probe windows for long files
LUFS_SAMPLE_WINDOW_SEC   = 60     # seconds per window
LUFS_SAMPLE_MIN_DURATION = 360    # files shorter than this get a full scan
LUFS_WINDOW_TIMEOUT      = 180    # per-window ffmpeg cap (s)
LUFS_FULL_TIMEOUT        = 900    # whole-file scan cap (s) - short files / fallback
LUFS_SILENCE_GATE        = -60.0  # windows quieter than this are dropped as silence
LOCK_FILE      = Path("/var/lib/audio-norm/processing.lock")
COMPLETED_FILE = Path("/var/lib/audio-norm/completed.txt")
LOCK_WAIT      = 60
LOCK_TIMEOUT   = 7200

log = logging.getLogger(__name__)


# --- Locking ---

def acquire_lock(blocking: bool = True) -> bool:
    """
    Atomic O_EXCL lock acquisition.
    If blocking=True, poll up to LOCK_TIMEOUT seconds.
    If blocking=False, return False immediately on contention.
    """
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    waited = 0
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as f:
                f.write(str(os.getpid()))
            log.info(f"Lock acquired (pid {os.getpid()})")
            return True
        except FileExistsError:
            try:
                pid = LOCK_FILE.read_text().strip()
            except Exception:
                pid = "unknown"
            if not blocking:
                log.info(f"Lock held by pid {pid}")
                return False
            log.info(f"Lock held by pid {pid}, waiting {LOCK_WAIT}s...")
            time.sleep(LOCK_WAIT)
            waited += LOCK_WAIT
            if waited >= LOCK_TIMEOUT:
                log.error("Timed out waiting for lock")
                return False


def release_lock() -> None:
    LOCK_FILE.unlink(missing_ok=True)
    log.info("Lock released")


def log_completed(filepath_str: str) -> None:
    """Append "<unix_ts> <path>" so the monitor can suppress the rename event."""
    COMPLETED_FILE.parent.mkdir(parents=True, exist_ok=True)
    COMPLETED_FILE.touch(exist_ok=True)
    with COMPLETED_FILE.open("a") as f:
        f.write(f"{int(time.time())} {filepath_str}\n")


# --- ffprobe ---

def get_audio_info(filepath: Path) -> dict | None:
    """Return first audio stream info dict, or None on failure."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(filepath),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "audio":
                return stream
    except Exception as e:
        log.error(f"ffprobe failed on {filepath}: {e}")
    return None


def verify_output(filepath: Path) -> bool:
    """Verify output has a video stream and AAC audio."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(filepath),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        streams = data.get("streams", [])

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_aac = any(
            s.get("codec_type") == "audio" and s.get("codec_name") == "aac"
            for s in streams
        )

        if not has_video:
            log.error(f"Output missing video stream: {filepath.name}")
            return False
        if not has_aac:
            log.error(f"Output audio is not AAC: {filepath.name}")
            return False
        return True

    except Exception as e:
        log.error(f"Verification failed on {filepath.name}: {e}")
        return False


# --- LUFS measurement ---

def _probe_duration(filepath: Path) -> float | None:
    """Container duration in seconds, or None if unavailable."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(filepath),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        return None


def _loudnorm_input_i(
    filepath: Path,
    ss: float | None = None,
    duration: float | None = None,
    timeout: int = LUFS_FULL_TIMEOUT,
) -> float | None:
    """One loudnorm analysis pass -> integrated loudness (input_i).

    With ss/duration set, only that window is decoded (fast input seek);
    otherwise the whole file is scanned. None on timeout/parse failure.
    """
    cmd = ["ffmpeg"]
    if ss is not None:
        cmd += ["-ss", f"{ss:.3f}"]
    cmd += ["-i", str(filepath)]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-vn", "-sn", "-af", f"{LOUDNORM}:print_format=json", "-f", "null", "-"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.error(f"LUFS measurement timed out: {filepath.name}")
        return None
    except Exception as e:
        log.error(f"LUFS measurement failed: {filepath.name}: {e}")
        return None

    match = re.search(r'\{[^{}]*"input_i"\s*:[^{}]*\}', result.stderr, re.DOTALL)
    if not match:
        log.warning(f"Could not parse loudnorm output for: {filepath.name}")
        return None
    try:
        lufs = float(json.loads(match.group()).get("input_i", "nan"))
    except (ValueError, json.JSONDecodeError):
        return None
    if math.isnan(lufs) or lufs < -100:
        return None
    return lufs


def measure_lufs(filepath: Path) -> float | None:
    """Estimate integrated loudness.

    Long files are sampled at several spread-out windows rather than decoded in
    full: the result only feeds a +/-LUFS_THRESHOLD skip decision, so a
    representative estimate suffices and avoids multi-minute full-file decodes
    (esp. high-sample-rate / lossless tracks). Short files are scanned whole.
    """
    duration = _probe_duration(filepath)

    # Short or unknown-length: cheap enough to scan in full (old behavior).
    if duration is None or duration < LUFS_SAMPLE_MIN_DURATION:
        log.info(f"Measuring LUFS (full): {filepath.name}")
        lufs = _loudnorm_input_i(filepath, timeout=LUFS_FULL_TIMEOUT)
        if lufs is not None:
            log.info(f"Measured {lufs:.1f} LUFS: {filepath.name}")
        return lufs

    # Spread N windows across the body, skipping the first/last 10% (intros,
    # credits, trailing silence) so the sample reflects program content.
    win, n = LUFS_SAMPLE_WINDOW_SEC, LUFS_SAMPLE_WINDOWS
    start, end = duration * 0.10, duration * 0.90
    span = max(end - start - win, 0.0)
    offsets = [start + span * i / (n - 1) for i in range(n)] if n > 1 else [start]

    log.info(f"Measuring LUFS (sampled {n}x{win}s of {duration/60:.0f}min): {filepath.name}")
    values = []
    for off in offsets:
        v = _loudnorm_input_i(filepath, ss=off, duration=win, timeout=LUFS_WINDOW_TIMEOUT)
        if v is not None and v >= LUFS_SILENCE_GATE:
            values.append(v)

    if not values:
        log.warning(f"No usable LUFS samples (all silent/failed): {filepath.name}")
        return None

    # Combine in the energy domain (LUFS is a power measure) so loud windows
    # weigh correctly, approximating a whole-program integrated reading.
    mean_energy = sum(10 ** (v / 10.0) for v in values) / len(values)
    lufs = 10.0 * math.log10(mean_energy)
    log.info(f"Measured {lufs:.1f} LUFS (sampled {len(values)}/{n} windows): {filepath.name}")
    return lufs


def needs_normalization(
    filepath: Path,
    target: float = LUFS_TARGET,
    threshold: float = LUFS_THRESHOLD,
) -> bool:
    """True if file is outside the target ± threshold window (or unmeasurable)."""
    lufs = measure_lufs(filepath)
    if lufs is None:
        log.warning(f"Could not measure LUFS, will normalize: {filepath.name}")
        return True

    diff = abs(lufs - target)
    if diff <= threshold:
        log.info(
            f"Already normalized ({lufs:.1f} LUFS, within {threshold} of target), "
            f"skipping: {filepath.name}"
        )
        return False

    log.info(
        f"Needs normalization ({lufs:.1f} LUFS, {diff:.1f} from target): {filepath.name}"
    )
    return True


# --- Filesystem helpers ---

def check_free_space(filepath: Path, min_gb: int = MIN_FREE_GB) -> bool:
    """True if the filesystem hosting filepath has at least min_gb free."""
    try:
        stat = shutil.disk_usage(filepath.parent)
        free_gb = stat.free / (1024 ** 3)
        if free_gb < min_gb:
            log.error(f"Low disk space: {free_gb:.1f}GB free, need {min_gb}GB")
            return False
        return True
    except Exception as e:
        log.error(f"Could not check disk space: {e}")
        return False


def tmp_path(filepath: Path) -> Path:
    """Build sibling tmp path that preserves the original extension."""
    return filepath.with_name(filepath.stem + ".tmp" + filepath.suffix)


# --- Transcode ---

def transcode_to_aac(
    filepath: Path,
    audio_filter: str = LOUDNORM,
    bitrate: str = AUDIO_BITRATE,
) -> bool:
    """
    Transcode audio to AAC with the given filter chain, replacing the original
    on success. Caller is responsible for the processing lock.
    Returns True on success, False on failure.
    """
    if not filepath.exists():
        log.error(f"File no longer exists: {filepath}")
        return False

    if not check_free_space(filepath):
        return False

    tmp = tmp_path(filepath)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(filepath),
        "-map", "0",
        "-c:v", "copy",
        "-c:s", "copy",
        "-c:a", "aac",
        "-b:a", bitrate,
        "-strict", "-2",
        "-af", audio_filter,
        str(tmp),
    ]

    log.info(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode != 0:
            log.error(f"FFmpeg failed (code {result.returncode}): {filepath.name}")
            log.error(result.stderr[-2000:])
            tmp.unlink(missing_ok=True)
            return False

        if not tmp.exists() or tmp.stat().st_size < 1024 * 1024:
            log.error(f"Output file missing or too small: {tmp}")
            tmp.unlink(missing_ok=True)
            return False

        if not verify_output(tmp):
            tmp.unlink(missing_ok=True)
            return False

        shutil.move(str(tmp), str(filepath))
        log.info(f"SUCCESS: {filepath.name}")
        return True

    except subprocess.TimeoutExpired:
        log.error(f"Timeout: {filepath.name}")
        tmp.unlink(missing_ok=True)
        return False
    except Exception as e:
        log.error(f"Unexpected error on {filepath.name}: {e}")
        tmp.unlink(missing_ok=True)
        return False
