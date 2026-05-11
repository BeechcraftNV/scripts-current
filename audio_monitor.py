#!/usr/bin/env python3
"""
audio_monitor.py - Watches media directories for new files and adds them to the normalize queue.

Triggered by: systemd service
Watches: /mnt/pool/tv and /mnt/pool/movies
Queue: /var/lib/audio-norm/queue.txt
Log: /var/lib/audio-norm/monitor.log
"""

import subprocess
import logging
import sys
import os
from pathlib import Path

# --- Config ---
WATCH_DIRS = [
    "/mnt/pool/tv",
    "/mnt/pool/movies",
]
QUEUE_FILE  = Path("/var/lib/audio-norm/queue.txt")
LOG_FILE    = Path("/var/lib/audio-norm/monitor.log")
EXTENSIONS  = {".mkv", ".mp4", ".avi"}

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [monitor] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def add_to_queue(filepath: str) -> None:
    """Add a file to the queue if not already present."""
    QUEUE_FILE.touch(exist_ok=True)
    existing = QUEUE_FILE.read_text().splitlines()

    if filepath in existing:
        log.info(f"Already in queue, skipping: {filepath}")
        return

    with QUEUE_FILE.open("a") as f:
        f.write(filepath + "\n")

    log.info(f"Added to queue: {filepath}")


def is_media_file(filepath: str) -> bool:
    """Check if the file is a media file we care about."""
    p = Path(filepath)
    return (
        p.suffix.lower() in EXTENSIONS
        and ".tmp." not in p.name
        and p.exists()
    )


def watch() -> None:
    """Run inotifywait and process events."""
    cmd = [
        "inotifywait",
        "-m",           # monitor continuously
        "-r",           # recursive
        "-e", "moved_to",  # trigger when file moved into directory
        "--format", "%w%f",  # output full path
        "--quiet",
    ] + WATCH_DIRS

    log.info(f"Starting monitor on: {', '.join(WATCH_DIRS)}")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        for line in proc.stdout:
            filepath = line.strip()
            if not filepath:
                continue

            log.info(f"Event detected: {filepath}")

            if is_media_file(filepath):
                add_to_queue(filepath)
            else:
                log.info(f"Ignoring non-media file: {filepath}")

    except KeyboardInterrupt:
        log.info("Monitor stopped by user")
        proc.terminate()
    except Exception as e:
        log.error(f"Monitor error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Verify watch directories exist
    for d in WATCH_DIRS:
        if not Path(d).exists():
            log.error(f"Watch directory not found: {d}")
            sys.exit(1)

    watch()
