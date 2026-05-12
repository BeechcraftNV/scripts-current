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
LUFS_THRESHOLD = 2.0
MIN_FREE_GB    = 5
LOCK_FILE      = Path("/var/lib/audio-norm/processing.lock")
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

def measure_lufs(filepath: Path) -> float | None:
    """Measure integrated loudness via loudnorm analysis pass."""
    cmd = [
        "ffmpeg", "-i", str(filepath),
        "-af", f"{LOUDNORM}:print_format=json",
        "-f", "null", "-",
    ]
    try:
        log.info(f"Measuring LUFS: {filepath.name}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)

        match = re.search(r'\{[^{}]*"input_i"\s*:[^{}]*\}', result.stderr, re.DOTALL)
        if not match:
            log.warning(f"Could not parse loudnorm output for: {filepath.name}")
            return None

        data = json.loads(match.group())
        lufs = float(data.get("input_i", "nan"))

        if math.isnan(lufs) or lufs < -100:
            log.warning(f"Invalid LUFS measurement for: {filepath.name}")
            return None

        log.info(f"Measured {lufs:.1f} LUFS: {filepath.name}")
        return lufs

    except subprocess.TimeoutExpired:
        log.error(f"LUFS measurement timed out: {filepath.name}")
        return None
    except Exception as e:
        log.error(f"LUFS measurement failed: {filepath.name}: {e}")
        return None


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
