#!/usr/bin/env python3
"""
audio_worker.py - Processes files from the normalize queue one at a time.
Uses LUFS measurement to determine if normalization is needed regardless of codec.

Queue file: /var/lib/audio-norm/queue.txt
Log: /var/lib/audio-norm/worker.log
Completed: /var/lib/audio-norm/completed.txt
Failed: /var/lib/audio-norm/failed.txt
"""

import subprocess
import logging
import sys
import shutil
import json
import time
import re
import os
from pathlib import Path

# --- Config ---
QUEUE_FILE      = Path("/var/lib/audio-norm/queue.txt")
COMPLETED_FILE  = Path("/var/lib/audio-norm/completed.txt")
FAILED_FILE     = Path("/var/lib/audio-norm/failed.txt")
LOG_FILE        = Path("/var/lib/audio-norm/worker.log")
LOCK_FILE       = Path("/var/lib/audio-norm/processing.lock")
AUDIO_BITRATE   = "192k"
LOUDNORM        = "loudnorm=I=-16:TP=-1.5:LRA=11"
LUFS_TARGET     = -16.0
LUFS_THRESHOLD  = 2.0   # skip if within 2 LUFS of target
POLL_INTERVAL   = 10    # seconds between queue checks when idle
MIN_FREE_GB     = 5     # minimum free space before processing

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [worker] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def acquire_lock() -> bool:
    """Acquire processing lock. Returns False if already locked."""
    if LOCK_FILE.exists():
        pid = LOCK_FILE.read_text().strip()
        log.warning(f"Lock held by pid {pid}, skipping")
        return False
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_lock() -> None:
    """Release processing lock."""
    LOCK_FILE.unlink(missing_ok=True)


def measure_lufs(filepath: Path) -> float | None:
    """
    Measure integrated loudness of file using loudnorm analysis pass.
    Returns LUFS value or None on failure.
    """
    cmd = [
        "ffmpeg", "-i", str(filepath),
        "-af", f"{LOUDNORM}:print_format=json",
        "-f", "null", "-",
    ]
    try:
        log.info(f"Measuring LUFS: {filepath.name}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 min max for analysis
        )

        stderr = result.stderr
        match = re.search(r'\{[^{}]*"input_i"\s*:[^{}]*\}', stderr, re.DOTALL)
        if not match:
            log.warning(f"Could not parse loudnorm output for: {filepath.name}")
            return None

        data = json.loads(match.group())
        lufs = float(data.get("input_i", "nan"))

        if lufs == float("nan") or lufs < -100:
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


def needs_normalization(filepath: Path) -> bool:
    """
    Determine if file needs normalization based on LUFS measurement.
    Returns True if normalization needed, False if already within threshold.
    """
    lufs = measure_lufs(filepath)

    if lufs is None:
        log.warning(f"Could not measure LUFS, will normalize: {filepath.name}")
        return True

    diff = abs(lufs - LUFS_TARGET)
    if diff <= LUFS_THRESHOLD:
        log.info(f"Already normalized ({lufs:.1f} LUFS, within {LUFS_THRESHOLD} of target), skipping: {filepath.name}")
        return False

    log.info(f"Needs normalization ({lufs:.1f} LUFS, {diff:.1f} from target): {filepath.name}")
    return True


def get_audio_info(filepath: Path) -> dict | None:
    """Return first audio stream info, or None on failure."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(filepath)
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
    """Verify output file has valid video and AAC audio streams."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        str(filepath)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        streams = data.get("streams", [])

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_aac   = any(
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
        log.error(f"Verification failed: {filepath.name}: {e}")
        return False


def check_free_space(filepath: Path) -> bool:
    """Check there is enough free space on the target filesystem."""
    try:
        stat = shutil.disk_usage(filepath.parent)
        free_gb = stat.free / (1024 ** 3)
        if free_gb < MIN_FREE_GB:
            log.error(f"Low disk space: {free_gb:.1f}GB free, need {MIN_FREE_GB}GB")
            return False
        return True
    except Exception as e:
        log.error(f"Could not check disk space: {e}")
        return False


def transcode(filepath: Path) -> bool:
    """
    Transcode audio to AAC with loudnorm.
    Replaces original on success.
    Returns True on success, False on failure.
    """
    if not filepath.exists():
        log.error(f"File no longer exists: {filepath}")
        return False

    if not check_free_space(filepath):
        return False

    info = get_audio_info(filepath)
    if info is None:
        log.error(f"Could not read audio info: {filepath.name}")
        return False

    codec    = info.get("codec_name", "unknown")
    channels = info.get("channels", "?")

    if not acquire_lock():
        return False

    try:
        # LUFS check — skip if already normalized regardless of codec
        if not needs_normalization(filepath):
            return True

        tmp = filepath.with_suffix(".tmp.mkv")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(filepath),
            "-map", "0",
            "-c:v", "copy",
            "-c:s", "copy",
            "-c:a", "aac",
            "-b:a", AUDIO_BITRATE,
            "-strict", "-2",
            "-af", LOUDNORM,
            str(tmp)
        ]

        log.info(f"Transcoding ({codec} ch:{channels}): {filepath.name}")
        log.info(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600
        )

        if result.returncode != 0:
            log.error(f"FFmpeg failed (code {result.returncode}): {filepath.name}")
            log.error(result.stderr[-2000:])
            tmp.unlink(missing_ok=True)
            return False

        if not tmp.exists() or tmp.stat().st_size < 1024 * 1024:
            log.error(f"Output missing or too small: {tmp}")
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
        filepath.with_suffix(".tmp.mkv").unlink(missing_ok=True)
        return False
    except Exception as e:
        log.error(f"Unexpected error: {filepath.name}: {e}")
        filepath.with_suffix(".tmp.mkv").unlink(missing_ok=True)
        return False
    finally:
        release_lock()


def read_queue() -> list[str]:
    """Read current queue entries."""
    if not QUEUE_FILE.exists():
        return []
    return [
        line.strip()
        for line in QUEUE_FILE.read_text().splitlines()
        if line.strip()
    ]


def remove_from_queue(filepath: str) -> None:
    """Remove a specific entry from the queue."""
    entries = read_queue()
    remaining = [e for e in entries if e != filepath]
    QUEUE_FILE.write_text("\n".join(remaining) + "\n" if remaining else "")


def log_completed(filepath: str) -> None:
    """Append to completed log."""
    COMPLETED_FILE.touch(exist_ok=True)
    with COMPLETED_FILE.open("a") as f:
        f.write(filepath + "\n")


def log_failed(filepath: str) -> None:
    """Append to failed log."""
    FAILED_FILE.touch(exist_ok=True)
    with FAILED_FILE.open("a") as f:
        f.write(filepath + "\n")


def process_queue() -> None:
    """Main worker loop — poll queue and process files."""
    log.info(f"Worker started. Target: {LUFS_TARGET} LUFS, threshold: ±{LUFS_THRESHOLD} LUFS")

    while True:
        queue = read_queue()

        if not queue:
            time.sleep(POLL_INTERVAL)
            continue

        filepath_str = queue[0]
        filepath = Path(filepath_str)

        log.info(f"Dequeued: {filepath.name}")

        success = transcode(filepath)

        if success:
            remove_from_queue(filepath_str)
            log_completed(filepath_str)
        else:
            remove_from_queue(filepath_str)
            log_failed(filepath_str)
            log.error(f"Failed, moved to failed log: {filepath.name}")

        time.sleep(2)


if __name__ == "__main__":
    for f in [QUEUE_FILE, COMPLETED_FILE, FAILED_FILE, LOG_FILE]:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

    # Clean up stale lock on startup
    if LOCK_FILE.exists():
        log.warning("Stale lock found on startup, removing")
        release_lock()

    try:
        process_queue()
    except KeyboardInterrupt:
        log.info("Worker stopped by user")
        release_lock()
        sys.exit(0)
