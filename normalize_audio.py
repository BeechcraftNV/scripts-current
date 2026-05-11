#!/usr/bin/env python3
"""
normalize_audio.py - Audio loudness normalization for media library.
Transcodes non-AAC audio to AAC with loudnorm filter.
Replaces original file on success.

Usage:
    python3 normalize_audio.py /mnt/pool/tv/The\ Blacklist
    python3 normalize_audio.py --dry-run /mnt/pool/tv/The\ Blacklist
    python3 normalize_audio.py --force /mnt/pool/tv/Return\ to\ Paradise
    python3 normalize_audio.py --dynaudnorm /mnt/pool/tv/Rizzoli\ \&\ Isles
    python3 normalize_audio.py --force --dynaudnorm --dry-run /mnt/pool/tv/Sherlock
"""

import subprocess
import json
import sys
import logging
import shutil
import os
import time
from pathlib import Path

# --- Args ---
DRY_RUN    = "--dry-run"    in sys.argv
FORCE      = "--force"      in sys.argv
DYNAUDNORM = "--dynaudnorm" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
TARGET_DIR = args[0] if args else "/mnt/pool/tv"

# --- Config ---
AUDIO_BITRATE = "192k"
LOUDNORM      = "loudnorm=I=-16:TP=-1.5:LRA=11"
LOG_FILE      = "/tmp/normalize_audio.log"
LOCK_FILE     = Path("/var/lib/audio-norm/processing.lock")
SKIP_CODECS   = {"aac"} if not FORCE else set()
EXTENSIONS    = {".mkv", ".mp4", ".avi"}
LOCK_WAIT     = 60    # seconds to wait between lock checks
LOCK_TIMEOUT  = 7200  # give up after 2 hours waiting

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def acquire_lock() -> bool:
    """Acquire processing lock. Waits if worker is running."""
    waited = 0
    while LOCK_FILE.exists():
        pid = LOCK_FILE.read_text().strip()
        log.info(f"Worker is processing (pid {pid}), waiting {LOCK_WAIT}s...")
        time.sleep(LOCK_WAIT)
        waited += LOCK_WAIT
        if waited >= LOCK_TIMEOUT:
            log.error("Timed out waiting for lock. Exiting.")
            return False
    LOCK_FILE.write_text(str(os.getpid()))
    log.info(f"Lock acquired (pid {os.getpid()})")
    return True


def release_lock() -> None:
    """Release processing lock."""
    LOCK_FILE.unlink(missing_ok=True)
    log.info("Lock released")


def get_audio_info(filepath: Path) -> dict | None:
    """Return first audio stream info dict, or None on failure."""
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
        log.error(f"Verification failed on {filepath.name}: {e}")
        return False


def build_audio_filter() -> str:
    """Build the audio filter chain based on flags."""
    if DYNAUDNORM:
        return f"dynaudnorm,{LOUDNORM}"
    return LOUDNORM


def transcode(filepath: Path) -> bool:
    """
    Transcode audio to AAC with loudnorm, replacing original on success.
    Returns True on success, False on failure.
    """
    tmp = filepath.with_suffix(".tmp.mkv")
    audio_filter = build_audio_filter()

    cmd = [
        "ffmpeg", "-y",
        "-i", str(filepath),
        "-map", "0",
        "-c:v", "copy",
        "-c:s", "copy",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-strict", "-2",
        "-af", audio_filter,
        str(tmp)
    ]

    log.info(f"Command: {' '.join(cmd)}")

    try:
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


def main():
    target = Path(TARGET_DIR)
    if not target.exists():
        log.error(f"Directory not found: {target}")
        sys.exit(1)

    flags = []
    if DRY_RUN:    flags.append("DRY-RUN")
    if FORCE:      flags.append("FORCE")
    if DYNAUDNORM: flags.append("DYNAUDNORM")
    if flags:
        log.info(f"Flags: {' | '.join(flags)}")

    audio_filter = build_audio_filter()
    log.info(f"Audio filter: {audio_filter}")

    # Acquire lock for entire batch run (skip in dry-run mode)
    if not DRY_RUN:
        if not acquire_lock():
            sys.exit(1)

    try:
        files = sorted([
            f for f in target.rglob("*")
            if f.suffix.lower() in EXTENSIONS
            and ".tmp." not in f.name
        ])

        log.info(f"Found {len(files)} media files in {target}")

        success       = 0
        skipped       = 0
        failed        = 0
        would_process = 0

        for filepath in files:
            info = get_audio_info(filepath)

            if info is None:
                log.warning(f"Could not determine audio codec, skipping: {filepath.name}")
                skipped += 1
                continue

            codec    = info.get("codec_name", "unknown")
            channels = info.get("channels", "?")

            if codec in SKIP_CODECS:
                log.info(f"SKIP (already {codec}): {filepath.name}")
                skipped += 1
                continue

            if DRY_RUN:
                log.info(f"WOULD PROCESS ({codec} ch:{channels}): {filepath.name}")
                would_process += 1
                continue

            log.info(f"Processing ({codec} ch:{channels}): {filepath.name}")

            if transcode(filepath):
                success += 1
            else:
                failed += 1

        if DRY_RUN:
            log.info(f"Dry run complete. Would process: {would_process} | Would skip: {skipped}")
        else:
            log.info(f"Done. Success: {success} | Skipped: {skipped} | Failed: {failed}")

        log.info(f"Full log: {LOG_FILE}")

    finally:
        if not DRY_RUN:
            release_lock()


if __name__ == "__main__":
    main()
