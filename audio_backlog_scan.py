#!/usr/bin/env python3
"""
audio_backlog_scan.py - One-shot bulk scanner for the audio-normalization
pipeline. Walks media directories, finds files whose audio is NOT already
AAC, and appends them to the low-priority backlog queue.

The systemd worker (audio_worker.py) drains backlog.txt only while
queue.txt is empty, so this bulk backlog never delays normalization of
newly added files arriving via audio_monitor.py.

This is a cleanup pass, not an ongoing service: run it once, let the
worker chip away at backlog.txt during idle time. When backlog.txt drains
the worker is back to plain single-queue behavior.

Usage:
    audio_backlog_scan.py                        # scan /mnt/pool/tv and /mnt/pool/movies
    audio_backlog_scan.py --dry-run              # report counts, write nothing
    audio_backlog_scan.py /mnt/pool/tv/Sherlock  # scan specific dir(s)

Flags:
    --dry-run   report what would be enqueued, do not touch backlog.txt
"""

import fcntl
import os
import sys
from pathlib import Path

from audio_common import get_audio_info

# --- Config ---
DEFAULT_DIRS   = ["/mnt/pool/tv", "/mnt/pool/movies"]
QUEUE_FILE     = Path("/var/lib/audio-norm/queue.txt")
BACKLOG_FILE   = Path("/var/lib/audio-norm/backlog.txt")
COMPLETED_FILE = Path("/var/lib/audio-norm/completed.txt")
FAILED_FILE    = Path("/var/lib/audio-norm/failed.txt")
QUEUE_LOCK     = Path("/var/lib/audio-norm/queue.lock")
EXTENSIONS     = {".mkv", ".mp4", ".avi"}

# --- Args ---
DRY_RUN   = "--dry-run" in sys.argv
dir_args  = [a for a in sys.argv[1:] if not a.startswith("--")]
SCAN_DIRS = dir_args if dir_args else DEFAULT_DIRS


# --- Queue lock (shared with audio_monitor.py / audio_worker.py) ---

class _QueueLock:
    def __enter__(self):
        QUEUE_LOCK.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(QUEUE_LOCK, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self._fd, fcntl.LOCK_UN)
        os.close(self._fd)


def _load_paths(path: Path) -> set[str]:
    """Plain one-path-per-line file -> set of paths."""
    if not path.exists():
        return set()
    return {line.strip() for line in path.read_text().splitlines() if line.strip()}


def _load_completed() -> set[str]:
    """completed.txt entries are "<unix_ts> <path>" (legacy: bare path)."""
    if not COMPLETED_FILE.exists():
        return set()
    paths: set[str] = set()
    for line in COMPLETED_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            paths.add(parts[1])
        else:
            paths.add(line)
    return paths


def main() -> None:
    tracked = (
        _load_paths(QUEUE_FILE)
        | _load_paths(BACKLOG_FILE)
        | _load_paths(FAILED_FILE)
        | _load_completed()
    )
    print(f"Already tracked (queue/backlog/completed/failed): {len(tracked)} paths")

    candidates: list[str] = []
    scanned = skipped_aac = skipped_tracked = probe_fail = 0

    for d in SCAN_DIRS:
        root = Path(d)
        if not root.exists():
            print(f"WARNING: scan dir not found, skipping: {d}", file=sys.stderr)
            continue
        print(f"Scanning {root} ...")
        files = sorted(
            f for f in root.rglob("*")
            if f.suffix.lower() in EXTENSIONS and ".tmp." not in f.name
        )
        for filepath in files:
            scanned += 1
            path_str = str(filepath)
            if path_str in tracked:
                skipped_tracked += 1
                continue
            info = get_audio_info(filepath)
            if info is None:
                probe_fail += 1
                continue
            if info.get("codec_name", "unknown") == "aac":
                skipped_aac += 1
                continue
            candidates.append(path_str)
            if len(candidates) % 25 == 0:
                print(f"  ... {len(candidates)} candidates ({scanned} scanned)")

    print()
    print(f"Scanned:            {scanned}")
    print(f"Skipped (AAC):      {skipped_aac}")
    print(f"Skipped (tracked):  {skipped_tracked}")
    print(f"ffprobe failures:   {probe_fail}")
    print(f"Backlog candidates: {len(candidates)}")

    if not candidates:
        print("Nothing to enqueue.")
        return

    if DRY_RUN:
        print("\n--dry-run: backlog.txt not modified. Sample candidates:")
        for c in candidates[:20]:
            print(f"  {c}")
        if len(candidates) > 20:
            print(f"  ... and {len(candidates) - 20} more")
        return

    # Append under the shared queue lock; re-dedup against backlog.txt inside
    # the lock so a re-run (or concurrent worker progress) can't double-add.
    with _QueueLock():
        existing = _load_paths(BACKLOG_FILE)
        new_entries = [c for c in candidates if c not in existing]
        BACKLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with BACKLOG_FILE.open("a") as f:
            for c in new_entries:
                f.write(c + "\n")

    print(f"\nAppended {len(new_entries)} files to {BACKLOG_FILE}")
    print("The worker will drain these whenever queue.txt is empty.")


if __name__ == "__main__":
    main()
