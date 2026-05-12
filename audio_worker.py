#!/usr/bin/env python3
"""
audio_worker.py - Processes files from the normalize queue one at a time.
Uses LUFS measurement to gate transcoding regardless of codec.

Queue file:    /var/lib/audio-norm/queue.txt
Completed:     /var/lib/audio-norm/completed.txt  (format: "<unix_ts> <path>")
Failed:        /var/lib/audio-norm/failed.txt
Log:           /var/lib/audio-norm/worker.log
Processing lock: /var/lib/audio-norm/processing.lock (shared with normalize_audio.py)
"""

import fcntl
import logging
import os
import signal
import sys
import time
from pathlib import Path

import audio_common
from audio_common import (
    acquire_lock,
    get_audio_info,
    needs_normalization,
    release_lock,
    transcode_to_aac,
)

# --- Config ---
QUEUE_FILE     = Path("/var/lib/audio-norm/queue.txt")
COMPLETED_FILE = Path("/var/lib/audio-norm/completed.txt")
FAILED_FILE    = Path("/var/lib/audio-norm/failed.txt")
LOG_FILE       = Path("/var/lib/audio-norm/worker.log")
QUEUE_LOCK     = Path("/var/lib/audio-norm/queue.lock")
POLL_INTERVAL  = 10

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [worker] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)
audio_common.log = log


# --- Queue I/O (fcntl-locked) ---

class _QueueLock:
    """flock guard around queue.txt mutations."""

    def __enter__(self):
        QUEUE_LOCK.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(QUEUE_LOCK, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)


def _read_queue() -> list[str]:
    if not QUEUE_FILE.exists():
        return []
    return [
        line.strip()
        for line in QUEUE_FILE.read_text().splitlines()
        if line.strip()
    ]


def _write_queue(entries: list[str]) -> None:
    """Atomic rewrite via tempfile + os.replace."""
    tmp = QUEUE_FILE.with_suffix(QUEUE_FILE.suffix + ".tmp")
    body = ("\n".join(entries) + "\n") if entries else ""
    tmp.write_text(body)
    os.replace(tmp, QUEUE_FILE)


def peek_queue() -> str | None:
    """Read the first entry without removing it."""
    with _QueueLock():
        entries = _read_queue()
        return entries[0] if entries else None


def remove_from_queue(filepath_str: str) -> None:
    with _QueueLock():
        entries = _read_queue()
        remaining = [e for e in entries if e != filepath_str]
        _write_queue(remaining)


def log_completed(filepath_str: str) -> None:
    """Append "<unix_ts> <path>" so the monitor can suppress the rename event."""
    COMPLETED_FILE.touch(exist_ok=True)
    with COMPLETED_FILE.open("a") as f:
        f.write(f"{int(time.time())} {filepath_str}\n")


def log_failed(filepath_str: str) -> None:
    FAILED_FILE.touch(exist_ok=True)
    with FAILED_FILE.open("a") as f:
        f.write(filepath_str + "\n")


# --- Per-file processing ---

def handle_one(filepath_str: str) -> None:
    """Process the head-of-queue file. Must be called only while holding the lock."""
    filepath = Path(filepath_str)
    log.info(f"Dequeued: {filepath.name}")

    if not filepath.exists():
        log.error(f"File no longer exists: {filepath}")
        remove_from_queue(filepath_str)
        log_failed(filepath_str)
        return

    info = get_audio_info(filepath)
    if info is None:
        log.error(f"Could not read audio info: {filepath.name}")
        remove_from_queue(filepath_str)
        log_failed(filepath_str)
        return

    codec    = info.get("codec_name", "unknown")
    channels = info.get("channels", "?")

    if not needs_normalization(filepath):
        # Already within LUFS window — treat as success.
        remove_from_queue(filepath_str)
        log_completed(filepath_str)
        return

    log.info(f"Transcoding ({codec} ch:{channels}): {filepath.name}")
    success = transcode_to_aac(filepath)

    remove_from_queue(filepath_str)
    if success:
        log_completed(filepath_str)
    else:
        log_failed(filepath_str)
        log.error(f"Failed, moved to failed log: {filepath.name}")


def process_queue() -> None:
    """Main loop. Lock contention retries without dequeuing or failing the file."""
    log.info("Worker started.")

    while True:
        head = peek_queue()
        if head is None:
            time.sleep(POLL_INTERVAL)
            continue

        # Try to take the processing lock without blocking. If another process
        # (e.g. a manual normalize_audio.py run) holds it, wait and retry —
        # do NOT remove the entry or write to failed.txt.
        if not acquire_lock(blocking=False):
            log.info(f"Processing lock busy, retrying in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)
            continue

        try:
            handle_one(head)
        finally:
            release_lock()

        time.sleep(2)


def _graceful_shutdown(signum, _frame):
    log.info(f"Received signal {signum}, releasing lock and exiting")
    release_lock()
    sys.exit(0)


if __name__ == "__main__":
    for f in [QUEUE_FILE, COMPLETED_FILE, FAILED_FILE, LOG_FILE]:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

    if audio_common.LOCK_FILE.exists():
        log.warning("Stale lock found on startup, removing")
        release_lock()

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    try:
        process_queue()
    except KeyboardInterrupt:
        _graceful_shutdown(signal.SIGINT, None)
