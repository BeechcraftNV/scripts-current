# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Personal Bin Directory

This is a personal utility scripts directory (`~/.local/bin`) containing custom system maintenance and automation tools for a home media server running Debian Linux.

## Repository Details

- **Git remote:** `git@github.com:BeechcraftNV/scripts-current.git`
- **Purpose:** Personal utility scripts synced across systems
- **Contains:** Executable bash scripts, binary symlinks, and downloaded tools
- **Git workflow:** Rebase-first approach to maintain clean history

### What's Tracked vs. Ignored

**Tracked (committed to git):**
- Bash scripts (update-all, check-systemd-errors, plex-preopt, update-docker-stacks, etc.)
- Python scripts (plex_analyzer.py, sort_raindrops, kiwix-rescan)
- Documentation files (CLAUDE.md, README.md, GEMINI.md, etc.)

**Ignored (see .gitignore):**
- Binary executables (chezmoi, lazydocker, logseq, uv, uvx)
- Symlinks to applications (claude, zed)
- Python bytecode and virtual environments
- Editor directories (.vscode/, .idea/)
- Temporary files (*.tmp, *.log, *.swp)
- Package files (*.AppImage, *.deb, *.rpm)
- Claude Code settings (.claude/)

## Key Scripts

### System Maintenance

#### update-all
Comprehensive system update script that handles multiple package managers with detailed reporting.

**What it updates automatically:**
- APT packages (apt update && apt full-upgrade)
- User Flatpak packages (user installation only)
- Removes orphaned APT packages (autoremove)
- Cleans unused user Flatpak runtimes/SDKs

**What it reports:**
- Gemini CLI update status
- Docker dangling images
- Firmware updates (fwupdmgr)

**Key features:**
- Background Gemini CLI update pre-fetch
- Kernel version comparison (running vs. installed) to detect reboot needs
- Color-coded comprehensive summary report that **always displays**, even if errors occur
- Robust error handling - script continues through all sections even if individual steps fail
- Failed operations tracked separately and displayed in report
- Uses EXIT trap to guarantee report display on script termination

#### check-systemd-errors
Reviews recent systemd logs for errors and provides a summary.

**Usage:** `check-systemd-errors [time-period]`

**Examples:**
- `check-systemd-errors` (default: last hour)
- `check-systemd-errors "today"`
- `check-systemd-errors "24 hours ago"`

#### check-system-errors-glam
AI-enhanced systemd error troubleshooter using Charm CLI tools and Mods.

**Dependencies:** Requires `gum`, `glow`, and `mods` installed

### Media Processing Scripts

#### plex-preopt
Pre-optimization pipeline for Plex media library.
- Converts media files to Plex-friendly MP4 format using Intel VAAPI hardware acceleration
- Automatically detects and falls back to CPU (libx264) if VAAPI unavailable
- Smart remux vs transcode decision based on codec/resolution
- Idempotent: only processes files when source is newer than output
- Mirrors source directory structure under `/mnt/pool/optimized`
- Target: H.264 video (≤1080p), AAC stereo or EAC3 5.1 audio
- Logs to `/var/log/plex-preopt/`

#### plex-preopt-single-test
Test encoding on single file before batch processing.
- Usage: `plex-preopt-single-test /path/to/file.mkv` (or uses default test file)
- Uses QP-based encoding (QP=23) with bitrate fallback
- Audio: Always AAC stereo
- Test output directory: `/mnt/pool/optimized-test`
- Provides detailed before/after statistics

#### plex_analyzer.py
Plex direct play compatibility analyzer.
- Scans directory for video files and analyzes codec/container compatibility
- Reports which files will likely direct play vs need transcoding
- Checks for H.264/HEVC video and AAC/AC3 audio in MP4/MKV/MOV containers
- Interactive: prompts for directory to scan

#### convert-audiobook
MP3 to M4B audiobook converter.
- Uses Docker container `sandreas/m4b-tool:latest` for conversion
- Automatic metadata extraction from folder name pattern: "Author - Title"
- Creates chapter markers (one per MP3 file)
- Default output: creates `.m4b` in same directory as source MP3s

### Docker Management Scripts

#### update-docker-stacks
Docker Compose stack updater.
- Updates all compose stacks in `/opt/docker/compose/`
- Each stack is a separate `.yml` file (e.g., `plex.yml`, `pihole.yml`)
- Supports dry-run mode and selective stack updates
- Pre/post image digest comparison to detect actual changes
- Health checks for critical services: Plex, Pi-hole, Sonarr, Radarr, Bazarr, Prowlarr
- Automatic cleanup of dangling images after updates
- Logs to `/tmp/docker-update-YYYYMMDD-HHMMSS.log`

#### kiwix-rescan
Kiwix ZIM library rescanner (Python).
- Restarts Kiwix container to pick up new ZIM files from `/mnt/pool/zimit`
- Kiwix web interface: `http://localhost:8473`

### GitHub Management Scripts

#### delete-gh-repos
Bulk GitHub repository deletion tool.
- Reads repository list from file (one repo per line)
- Supports two formats: `repo-name` or `username/repo-name`
- Safety features: existence checks, dry-run mode, confirmation prompt
- Requires GitHub CLI (`gh`) with `delete_repo` scope
- Rate limiting: 1 second delay between deletions

### System Utilities

#### fix-vaapi
Intel VAAPI hardware acceleration setup.
- Adds user to `render` group for `/dev/dri/renderD128` access
- Required for Intel Quick Sync Video hardware encoding in ffmpeg
- User must log out/in after running for changes to take effect

#### dotpull.sh
Chezmoi dotfiles updater.
- Pulls latest dotfiles from GitHub using chezmoi
- Auto-applies changes to home directory
- Uses `--rebase` for clean git history

#### disable-sleep
Disable system sleep/suspend for 24/7 server operation.
- Disables systemd sleep targets
- Configures systemd-logind to ignore power/lid events
- Creates backup of original logind.conf
- Requires sudo; provides instructions to re-enable

#### morning-tabs
Morning routine URL opener.
- Opens URLs from `morning-urls.txt` in Brave browser
- Looks in script directory first, then `$HOME`
- Supports comments (lines starting with #) and blank lines
- Brief delay between tabs to preserve order

#### gemini-notify
Gemini CLI notification helper.
- Sends desktop notification when Gemini CLI task completes
- Visual notification via `notify-send`
- Audible alert via system sounds or speech synthesis

#### sync-scripts
Helper script to sync the repository with GitHub before editing.
- Checks for uncommitted/unpushed changes
- Pulls latest from GitHub using `git pull --rebase`

## Common Commands

### Testing Media Encoding

```bash
# Test VAAPI hardware acceleration
ffmpeg -hide_banner -init_hw_device vaapi=va -hwaccel vaapi -f lavfi -i testsrc=duration=1:size=16x16:rate=1 -c:v h264_vaapi -frames:v 1 -f null -

# Test single file encoding before batch
plex-preopt-single-test "/path/to/movie.mkv"

# Run full media optimization
plex-preopt  # Processes all media in default directories

# Limit scope to specific directory
plex-preopt "/mnt/pool/movies/Top Gun (1986)"
```

### Docker Operations

```bash
# Update all stacks
update-docker-stacks

# Dry-run to preview changes
update-docker-stacks --dry-run

# Update specific stacks only
update-docker-stacks plex pihole sonarr

# View running containers
docker ps
```

## System Architecture

### Media Storage Layout

- Source media: `/mnt/pool/movies`, `/mnt/pool/tv`
- Optimized output: `/mnt/pool/optimized` (mirrors source structure)
- Test encoding: `/mnt/pool/optimized-test`
- Audiobooks: `/mnt/pool/audiobooks`
- mergerfs pool: `/mnt/pool` (union of multiple drives)

### Docker Compose Architecture

- All stacks in: `/opt/docker/compose/`
- One `.yml` file per stack
- Critical services: Plex (media server), Pi-hole (DNS), Sonarr/Radarr (media automation)

### Hardware Acceleration

- Intel Quick Sync Video via VAAPI
- Device: `/dev/dri/renderD128`
- Requires user in `render` group
- Fallback to CPU (libx264) if VAAPI unavailable

## Git Workflow

### Before Making Changes
**IMPORTANT:** When editing scripts in this repository, follow this workflow:

1. **Sync first:** Run `sync-scripts` to pull latest changes from GitHub
2. **Make changes:** Edit scripts as needed
3. **Test:** Verify scripts work correctly
4. **Commit and push:**
   ```bash
   git add <files>
   git commit -m "descriptive message"
   git push
   ```

### If Sync Fails
- **Uncommitted changes:** Commit them first before syncing
- **Unpushed commits:** Push them first before syncing
- **Merge conflicts:** User will need to resolve manually

## Script Standards

### Naming and Structure
- Remove file extensions (.sh, .py, etc.) from scripts in this directory
  - Follows Unix convention (like git, docker, systemctl)
  - The shebang determines execution, not the extension
- Always include shebang line (#!/bin/bash, #!/usr/bin/env python3, etc.)
- Make scripts executable: `chmod +x script-name`

### Code Quality
- Use `set -euo pipefail` in bash scripts for robust error handling
- Include usage/help text for scripts with arguments
- Add error handling with clear messages
- Check for required commands before using: `command -v cmd`

### Testing Scripts

**Syntax check:** `bash -n script-name`
**Debug mode:** `bash -x script-name`

## External Dependencies

- **ffmpeg/ffprobe**: Media encoding/probing (with Intel VAAPI support)
- **docker**: Container runtime
- **jq**: JSON parsing in docker scripts
- **gh**: GitHub CLI for repo management
- **chezmoi**: Dotfile management
- **m4b-tool** (Docker): Audiobook creation
- **hugo**: Static site generator for build-welcome-site
- **caddy**: Web server for LAN welcome site
- **ncdu**: Disk usage analyzer for cleanup script
- **notify-send**: Desktop notifications (libnotify)
- **brave-browser**: Browser for morning-tabs script
