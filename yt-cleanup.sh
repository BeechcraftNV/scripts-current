#!/usr/bin/env bash
# Delete YT videos and sidecars older than 10  DAYS from /mnt/pool/yt

DAYS=10
YT_DIR="/mnt/pool/yt"

echo "yt-cleanup: deleting files older than $DAYS days from $YT_DIR"

find "$YT_DIR" \
  -not -path "$YT_DIR/safehouse/*" \
  \( -name "*.mkv" \
     -o -name "*.mp4" \
     -o -name "*.srt" \
     -o -name "*.nfo" \
     -o -name "*.webp" \
     -o -name "*.part" \
     -o -name "*.ytdl" \
     -o -name "*-poster.jpg" \
     -o -name "*-thumb.jpg" \) \
  -mtime +"$DAYS" \
  -print \
  -delete

# Remove empty directories left behind (but not the root itself)
find "$YT_DIR" -mindepth 1 -type d -empty -delete \
  && echo "yt-cleanup: empty directories removed"

echo "yt-cleanup: done"