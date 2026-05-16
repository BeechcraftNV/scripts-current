#!/usr/bin/env python3
"""
audio_worker.py - Processes files from the normalize queue one at a time.
Uses LUFS measurement to gate transcoding regardless of codec.

Queue file:    /var/lib/audio-norm/queue.txt
Backlog file:  /var/lib/audio-norm/backlog.txt   (low-priority bulk additions)
Completed:     /var/lib/audio-norm/completed.txt  (format: "<unix_ts> <path>")
Failed:        /var/lib/audio-norm/failed.txt
Log:           /var/lib/audio-norm/worker.log
Processing lock: /var/lib/audio-norm/processing.lock (shared with normalize_audio.py)

Priority: queue.txt (new arrivals from audio_monitor.py) is drained first;
backlog.txt is only consulted when queue.txt is empty, so a bulk backlog
never delays normalization of newly added files. When backlog.txt is empty
or absent the worker behaves exactly as a plain single-queue worker.
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
    log_completed,
    needs_normalization,
    release_lock,
    transcode_to_aac,
)

# --- Config ---
QUEUE_FILE     = Path("/var/lib/audio-norm/queue.txt")
BACKLOG_FILE   = Path("/var/lib/audio-norm/backlog.txt")
FAILED_FILE    = Path("/var/lib/audio-norm/failed.txt")
LOG_FILE       = Path("/var/lib/audio-norm/worker.log")
QUEUE_LOCK     = Path("/var/lib/audio-norm/queue.lock")
PID_FILE       = Path("/var/lib/audio-norm/worker.pid")
POLL_INTERVAL  = 10
COMPLETED_FILE = audio_common.COMPLETED_FILE  # for startup mkdir/touch only

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
    """flock guard around queue.txt / backlog.txt mutations."""

    def __enter__(self):
        QUEUE_LOCK.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(QUEUE_LOCK, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)


def _read_queue(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def _write_queue(path: Path, entries: list[str]) -> None:
    """Atomic rewrite via tempfile + os.replace."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    body = ("\n".join(entries) + "\n") if entries else ""
    tmp.write_text(body)
    os.replace(tmp, path)


def peek_next() -> tuple[str, Path] | None:
    """Return (filepath, source_queue) for the next file to process.

    queue.txt (new arrivals) has strict priority; backlog.txt is consulted
    only when queue.txt is empty. Returns None when both queues are empty.
    """
    with _QueueLock():
        for source in (QUEUE_FILE, BACKLOG_FILE):
            entries = _read_queue(source)
            if entries:
                return entries[0], source
        return None


def remove_from_queue(source: Path, filepath_str: str) -> None:
    with _QueueLock():
        entries = _read_queue(source)
        remaining = [e for e in entries if e != filepath_str]
        _write_queue(source, remaining)


def log_failed(filepath_str: str) -> None:
    FAILED_FILE.touch(exist_ok=True)
    with FAILED_FILE.open("a") as f:
        f.write(filepath_str + "\n")


# --- Channel layout ---

# ffprobe reports channel_layout="unknown" for some sources (e.g. Bluray rips).
# The native AAC encoder refuses to open without a known layout, so map the
# channel count to a standard layout and force it via the filter chain.
_CHANNEL_LAYOUTS = {
    1: "mono", 2: "stereo", 3: "2.1", 4: "quad",
    5: "5.0", 6: "5.1", 7: "6.1", 8: "7.1",
}


def _layout_for_channels(channels) -> str | None:
    """Standard channel layout name for a channel count, or None if unknown."""
    try:
        return _CHANNEL_LAYOUTS.get(int(channels))
    except (TypeError, ValueError):
        return None


# --- Per-file processing ---

def handle_one(filepath_str: str, source: Path) -> None:
    """Process the head-of-queue file. Must be called only while holding the lock.

    `source` is the queue file the entry came from (queue.txt or backlog.txt);
    completion removes the entry from that same file.
    """
    filepath = Path(filepath_str)
    log.info(f"Dequeued: {filepath.name}")

    if not filepath.exists():
        log.error(f"File no longer exists: {filepath}")
        remove_from_queue(source, filepath_str)
        log_failed(filepath_str)
        return

    info = get_audio_info(filepath)
    if info is None:
        log.error(f"Could not read audio info: {filepath.name}")
        remove_from_queue(source, filepath_str)
        log_failed(filepath_str)
        return

    codec    = info.get("codec_name", "unknown")
    channels = info.get("channels", "?")
    layout   = info.get("channel_layout", "")

    if not needs_normalization(filepath):
        # Already within LUFS window — treat as success.
        remove_from_queue(source, filepath_str)
        log_completed(filepath_str)
        return

    # When the source layout is undefined, force one so the AAC encoder can open.
    audio_filter = audio_common.LOUDNORM
    if not layout or layout == "unknown":
        forced = _layout_for_channels(channels)
        if forced:
            audio_filter = f"aformat=channel_layouts={forced},{audio_filter}"
            log.info(f"Unknown channel layout, forcing {forced} ({channels}ch): {filepath.name}")
        else:
            log.warning(f"Unknown channel layout and unmappable count ({channels}ch): {filepath.name}")

    log.info(f"Transcoding ({codec} ch:{channels}): {filepath.name}")
    success = transcode_to_aac(filepath, audio_filter=audio_filter)

    remove_from_queue(source, filepath_str)
    if success:
        log_completed(filepath_str)
    else:
        log_failed(filepath_str)
        log.error(f"Failed, moved to failed log: {filepath.name}")


def process_queue() -> None:
    """Main loop. Lock contention retries without dequeuing or failing the file."""
    log.info("Worker started.")

    while True:
        nxt = peek_next()
        if nxt is None:
            time.sleep(POLL_INTERVAL)
            continue
        head, source = nxt
        if source is BACKLOG_FILE:
            log.info(f"Queue empty, pulling from backlog: {Path(head).name}")

        # Try to take the processing lock without blocking. If another process
        # (e.g. a manual normalize_audio.py run) holds it, wait and retry —
        # do NOT remove the entry or write to failed.txt.
        if not acquire_lock(blocking=False):
            log.info(f"Processing lock busy, retrying in {POLL_INTERVAL}s")
            time.sleep(POLL_INTERVAL)
            continue

        try:
            handle_one(head, source)
        finally:
            release_lock()

        time.sleep(2)


def _graceful_shutdown(signum, _frame):
    log.info(f"Received signal {signum}, releasing lock and exiting")
    release_lock()
    PID_FILE.unlink(missing_ok=True)
    sys.exit(0)


if __name__ == "__main__":
    for f in [QUEUE_FILE, COMPLETED_FILE, FAILED_FILE, LOG_FILE]:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.touch(exist_ok=True)

    PID_FILE.write_text(str(os.getpid()))

    if audio_common.LOCK_FILE.exists():
        log.warning("Stale lock found on startup, removing")
        release_lock()

    signal.signal(signal.SIGTERM, _graceful_shutdown)
    signal.signal(signal.SIGINT, _graceful_shutdown)

    try:
        process_queue()
    except KeyboardInterrupt:
        _graceful_shutdown(signal.SIGINT, None)
