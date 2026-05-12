#!/usr/bin/env python3
"""
audio_monitor.py - Watches media directories for new files and adds them to
the normalize queue.

Triggered by: systemd (audio-monitor.service)
Watches: /mnt/pool/tv and /mnt/pool/movies
Queue:   /var/lib/audio-norm/queue.txt
Log:     /var/lib/audio-norm/monitor.log

Suppression: the worker writes "<unix_ts> <path>" to completed.txt on
success. The worker's final `shutil.move(tmp, original)` is a rename inside
a watched dir and fires a moved_to event for the original path; without
suppression that would re-queue the file. We consult completed.txt and skip
paths completed within RECENTLY_COMPLETED_WINDOW seconds.
"""

import fcntl
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# --- Config ---
WATCH_DIRS  = [
    "/mnt/pool/tv",
    "/mnt/pool/movies",
]
QUEUE_FILE     = Path("/var/lib/audio-norm/queue.txt")
QUEUE_LOCK     = Path("/var/lib/audio-norm/queue.lock")
COMPLETED_FILE = Path("/var/lib/audio-norm/completed.txt")
LOG_FILE       = Path("/var/lib/audio-norm/monitor.log")
EXTENSIONS     = {".mkv", ".mp4", ".avi"}

# How long after the worker logs a completion we suppress moved_to events
# for the same path. Covers the rename-into-place race; well above worst
# realistic clock skew but short enough that genuine later events still queue.
RECENTLY_COMPLETED_WINDOW = 300  # seconds

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [monitor] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# --- Queue I/O (fcntl-locked, shared with worker) ---

class _QueueLock:
    def __enter__(self):
        QUEUE_LOCK.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(QUEUE_LOCK, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)


def _queue_entries() -> list[str]:
    if not QUEUE_FILE.exists():
        return []
    return [
        line.strip()
        for line in QUEUE_FILE.read_text().splitlines()
        if line.strip()
    ]


def _recently_completed(filepath: str) -> bool:
    """Return True if filepath appears in completed.txt within the suppression window.

    Entries written by the new worker are of the form "<unix_ts> <path>".
    Legacy entries without a timestamp are treated as outside the window
    (i.e. they do not suppress future events).
    """
    if not COMPLETED_FILE.exists():
        return False

    cutoff = time.time() - RECENTLY_COMPLETED_WINDOW
    try:
        # Read just the tail — only recent entries matter. 64 KB is plenty for
        # the suppression window's worth of completions even on a heavy night.
        with COMPLETED_FILE.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536))
            tail = f.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(f"Could not read completed.txt: {e}")
        return False

    for line in tail.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue  # legacy entry without timestamp
        ts_str, path = parts
        try:
            ts = float(ts_str)
        except ValueError:
            continue
        if path == filepath and ts >= cutoff:
            return True
    return False


def add_to_queue(filepath: str) -> None:
    """Append filepath unless it's already queued or was recently completed."""
    with _QueueLock():
        if _recently_completed(filepath):
            log.info(f"Recently completed, skipping: {filepath}")
            return
        if filepath in _queue_entries():
            log.info(f"Already in queue, skipping: {filepath}")
            return
        QUEUE_FILE.touch(exist_ok=True)
        with QUEUE_FILE.open("a") as f:
            f.write(filepath + "\n")
        log.info(f"Added to queue: {filepath}")


def is_media_file(filepath: str) -> bool:
    p = Path(filepath)
    return (
        p.suffix.lower() in EXTENSIONS
        and ".tmp." not in p.name
        and p.exists()
    )


# --- Watcher ---

_proc: subprocess.Popen | None = None


def watch() -> None:
    global _proc
    cmd = [
        "inotifywait",
        "-m",
        "-r",
        "-e", "moved_to",
        "--format", "%w%f",
        "--quiet",
    ] + WATCH_DIRS

    log.info(f"Starting monitor on: {', '.join(WATCH_DIRS)}")

    _proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        for line in _proc.stdout:
            filepath = line.strip()
            if not filepath:
                continue

            log.info(f"Event detected: {filepath}")

            if is_media_file(filepath):
                add_to_queue(filepath)
            else:
                log.info(f"Ignoring non-media file: {filepath}")
    finally:
        rc = _proc.poll()
        stderr = _proc.stderr.read() if _proc.stderr else ""
        if rc is not None and rc != 0:
            log.error(f"inotifywait exited (code {rc}): {stderr.strip()}")
        elif rc is not None:
            log.error("inotifywait exited unexpectedly")


def _graceful_shutdown(signum, _frame):
    log.info(f"Received signal {signum}, shutting down")
    if _proc is not None:
        _proc.terminate()
    sys.exit(0)


if __name__ == "__main__":
    for d in WATCH_DIRS:
        if not Path(d).exists():
            log.error(f"Watch directory not found: {d}")
            sys.exit(1)

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    try:
        watch()
    except Exception as e:
        log.error(f"Monitor error: {e}")
        sys.exit(1)
