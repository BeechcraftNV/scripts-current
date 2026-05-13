# Audio Normalization System — How It Works

## Overview

Four Python files plus a small systemd target give you two ways to normalize the audio of media files to **−16 LUFS / −1.5 dBTP / LRA 11** (the loudnorm filter target):

- **Continuous, file-by-file**: as new episodes land in `/mnt/pool/tv` or `/mnt/pool/movies`, a systemd watcher queues them and a worker transcodes one at a time.
- **One-shot, bulk**: you point `normalize_audio.py` at a directory and it walks the whole tree.

Both paths share the same `audio_common.py` module and a single processing lock so they cannot run ffmpeg simultaneously.

## The four Python files

**`audio_common.py`** — shared library, no entry point:
- `acquire_lock()` / `release_lock()` — atomic `O_EXCL` lock at `/var/lib/audio-norm/processing.lock`. Blocks up to 2 h, or `blocking=False` for a non-blocking attempt.
- `get_audio_info()` / `verify_output()` — ffprobe helpers.
- `measure_lufs()` / `needs_normalization()` — runs loudnorm's analysis pass and decides whether the file is already within ±2.0 LUFS of −16.
- `transcode_to_aac()` — the actual ffmpeg pipeline: copies video and subtitles, re-encodes audio to AAC @ 192 kbps with `loudnorm=I=-16:TP=-1.5:LRA=11`, writes to a sibling `*.tmp.<ext>`, verifies (size > 1 MB, has video + AAC), then `shutil.move` over the original.
- `log_completed()` — appends `"<unix_ts> <path>"` to `/var/lib/audio-norm/completed.txt` (used for the rename-race suppression below).
- `check_free_space()` — refuses to start if the destination filesystem has <5 GB free.

**`audio_monitor.py`** — runs `inotifywait -m -r -e moved_to` on the watched dirs. For every rename-into-place of a `.mkv` / `.mp4` / `.avi`, it appends the path to `/var/lib/audio-norm/queue.txt` under an `fcntl` flock on `queue.lock`.
- Critical trick: when the worker finishes a file, `shutil.move(tmp, original)` is itself a rename inside a watched dir — that would re-queue the file forever. So the monitor consults `completed.txt` and skips paths completed within the last 300 s.
- Ignores anything containing `.tmp.` in the filename.

**`audio_worker.py`** — main loop:
1. `peek_queue()` — read the head entry under `queue.lock`.
2. `acquire_lock(blocking=False)` on `processing.lock`. If a bulk run holds it, sleep 10 s and retry **without** dequeuing — the entry stays put.
3. Once it has the lock: `get_audio_info`, then `needs_normalization()` (LUFS gate, **codec-agnostic** — AAC files get re-measured and only re-encoded if drifted).
4. If needed, `transcode_to_aac()`; then remove from `queue.txt`, append to `completed.txt` (success) or `failed.txt` (failure).

**`normalize_audio.py`** — bulk CLI:
- Walks the target directory.
- Uses a **codec gate**, not a LUFS gate: skips files already AAC unless `--force`. This is the recent change from commit `aef71e4` ("drop LUFS pre-check, write completed.txt on success") — it trades precision for speed on big libraries.
- Takes `processing.lock` blocking up front, holds it for the whole walk, releases at the end.
- For each transcode, writes to `completed.txt` so the monitor's 300 s suppression window absorbs the rename-into-place event.

## State directory (`/var/lib/audio-norm/`)

| File | Owner | Purpose |
| --- | --- | --- |
| `queue.txt` | monitor + worker | pending paths, one per line |
| `queue.lock` | both | `fcntl` flock guarding `queue.txt` mutations |
| `processing.lock` | worker + bulk | `O_EXCL` lock; only one ffmpeg at a time |
| `completed.txt` | worker + bulk | `"<ts> <path>"` lines, used for rename-race suppression |
| `failed.txt` | worker | paths that errored |
| `monitor.log` / `worker.log` | each daemon | structured log |

## Systemd units

- `audio-monitor.service` — runs `audio_monitor.py`.
- `audio-worker.service` — runs `audio_worker.py`.
- `audio-norm.target` — groups both with `PartOf=`, so `systemctl start/stop audio-norm.target` controls them as a unit. The target is **enabled** at boot, but the member services are not — only the target's `Wants=` will pull them in. Confirm with `systemctl is-enabled audio-monitor`; if you want the watcher running after a reboot, `sudo systemctl enable audio-monitor audio-worker`.

Both services run as user `steven`, `Restart=always`, depend on `mnt-pool.mount`.

---

# Instructions for Use

## Continuous mode (already running)

You don't need to do anything for new downloads — the monitor watches `/mnt/pool/tv` and `/mnt/pool/movies` and the worker drains the queue. Useful commands:

```bash
# Status
systemctl status audio-norm.target
systemctl status audio-monitor audio-worker

# Live logs
journalctl -u audio-monitor -u audio-worker -f
tail -f /var/lib/audio-norm/worker.log
tail -f /var/lib/audio-norm/monitor.log

# Queue inspection
cat /var/lib/audio-norm/queue.txt
wc -l /var/lib/audio-norm/{queue,completed,failed}.txt

# Stop / start the whole pipeline
sudo systemctl stop  audio-norm.target
sudo systemctl start audio-norm.target

# Make it survive reboot (if it doesn't already)
sudo systemctl enable audio-monitor audio-worker
```

## Bulk mode

```bash
# Dry-run first — reports what it WOULD do, makes no changes
normalize_audio.py --dry-run "/mnt/pool/tv/The Blacklist"

# Process a directory (skips already-AAC files)
normalize_audio.py "/mnt/pool/tv/The Blacklist"

# Re-encode even AAC files (e.g. levels are off but codec is already AAC)
normalize_audio.py --force "/mnt/pool/tv/Return to Paradise"

# Add dynamic range compression before loudnorm (good for shouty/whispery shows)
normalize_audio.py --dynaudnorm "/mnt/pool/tv/Rizzoli & Isles"

# Stack flags
normalize_audio.py --force --dynaudnorm --dry-run "/mnt/pool/tv/Sherlock"
```

Notes:
- The bulk script and worker share `processing.lock`, so it's safe to kick off a bulk run while the worker service is active — the worker will simply pause until you're done.
- Log goes to `/var/lib/audio-norm/normalize_audio.log` and stdout (alongside the daemon logs).

## Manually requeue / retry

```bash
# Add a path
echo "/mnt/pool/tv/Show/Episode.mkv" | sudo tee -a /var/lib/audio-norm/queue.txt

# Retry everything that failed
sudo cp /var/lib/audio-norm/failed.txt /var/lib/audio-norm/queue.txt
sudo truncate -s0 /var/lib/audio-norm/failed.txt
```

## Troubleshooting

- **Stale processing lock**: the worker auto-clears it on startup; for the bulk script, delete it manually if a previous run died: `sudo rm /var/lib/audio-norm/processing.lock`.
- **File keeps re-queuing after a successful transcode**: check that `completed.txt` is being written and the entries have the `<ts> <path>` format — that's what powers the 300 s suppression.
- **Worker says "Processing lock busy" forever**: a bulk run (or a stuck ffmpeg) holds it. `ps -ef | grep ffmpeg` and `cat /var/lib/audio-norm/processing.lock` (it contains the PID).
- **Want different loudness target / threshold**: edit the constants at the top of `audio_common.py` (`LOUDNORM`, `LUFS_TARGET`, `LUFS_THRESHOLD`).
