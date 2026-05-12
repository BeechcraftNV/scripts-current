#!/usr/bin/env python3
"""
normalize_audio.py - Bulk audio loudness normalization for a media library.
Walks a directory, gates each file on LUFS measurement (and AAC codec by
default), transcodes the rest to AAC + loudnorm, replacing the original.

Coordinates with the systemd worker via the shared lock in
/var/lib/audio-norm/processing.lock.

Usage:
    normalize_audio.py /mnt/pool/tv/The\ Blacklist
    normalize_audio.py --dry-run /mnt/pool/tv/The\ Blacklist
    normalize_audio.py --force /mnt/pool/tv/Return\ to\ Paradise
    normalize_audio.py --dynaudnorm /mnt/pool/tv/Rizzoli\ \&\ Isles
    normalize_audio.py --force --dynaudnorm --dry-run /mnt/pool/tv/Sherlock

Flags:
    --dry-run     report what would happen, do not write
    --force       bypass both the AAC-codec skip and the LUFS skip
    --dynaudnorm  prepend dynaudnorm to the loudnorm filter chain
"""

import logging
import sys
from pathlib import Path

import audio_common
from audio_common import (
    LOUDNORM,
    acquire_lock,
    check_free_space,
    get_audio_info,
    needs_normalization,
    release_lock,
    transcode_to_aac,
)

# --- Args ---
DRY_RUN    = "--dry-run"    in sys.argv
FORCE      = "--force"      in sys.argv
DYNAUDNORM = "--dynaudnorm" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
TARGET_DIR = args[0] if args else "/mnt/pool/tv"

# --- Config ---
LOG_FILE    = "/tmp/normalize_audio.log"
SKIP_CODECS = {"aac"} if not FORCE else set()
EXTENSIONS  = {".mkv", ".mp4", ".avi"}

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)
audio_common.log = log  # route shared-module logs through this logger


def build_audio_filter() -> str:
    return f"dynaudnorm,{LOUDNORM}" if DYNAUDNORM else LOUDNORM


def main():
    target = Path(TARGET_DIR)
    if not target.exists():
        log.error(f"Target not found: {target}")
        sys.exit(1)

    flags = []
    if DRY_RUN:    flags.append("DRY-RUN")
    if FORCE:      flags.append("FORCE")
    if DYNAUDNORM: flags.append("DYNAUDNORM")
    if flags:
        log.info(f"Flags: {' | '.join(flags)}")

    audio_filter = build_audio_filter()
    log.info(f"Audio filter: {audio_filter}")

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

            # LUFS gate (bypassed by --force)
            if not FORCE and not needs_normalization(filepath):
                skipped += 1
                continue

            if DRY_RUN:
                log.info(f"WOULD PROCESS ({codec} ch:{channels}): {filepath.name}")
                would_process += 1
                continue

            if not check_free_space(filepath):
                log.error(f"Insufficient space, aborting at: {filepath.name}")
                failed += 1
                break

            log.info(f"Processing ({codec} ch:{channels}): {filepath.name}")
            if transcode_to_aac(filepath, audio_filter=audio_filter):
                success += 1
            else:
                failed += 1

        if DRY_RUN:
            log.info(
                f"Dry run complete. Would process: {would_process} | Would skip: {skipped}"
            )
        else:
            log.info(
                f"Done. Success: {success} | Skipped: {skipped} | Failed: {failed}"
            )

        log.info(f"Full log: {LOG_FILE}")

    finally:
        if not DRY_RUN:
            release_lock()


if __name__ == "__main__":
    main()
