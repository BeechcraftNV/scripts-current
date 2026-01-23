# Personal Bin Directory Context

This directory (`~/.local/bin`) is a collection of personal utility scripts and application binaries/symlinks used for system maintenance, automation, and daily productivity on a Debian-based home media server.

## Project Overview

The directory serves as a central hub for custom CLI tools. It contains:
- **Custom Utility Scripts**: Hand-written Bash scripts for specialized system tasks.
- **Application Binaries/Symlinks**: Executables for installed tools like `uv`, `zed`, `claude`, and `logseq`.

## Key Scripts & Utilities

### System Maintenance

#### [update-all](./update-all)
A comprehensive system maintenance script that automates:
- **APT Updates**: Full-upgrade and autoremove.
- **Flatpak Updates**: User-level package updates and cleanup.
- **Firmware Checks**: Integration with `system76-firmware-manager` and `fwupdmgr`.
- **System Health**: Checks for EOL runtimes and reports on Docker, pip, and npm status.
- **Reboot Detection**: Compares running vs. installed kernel versions and identifies critical system service updates (systemd, dbus, udev) to recommend reboots.

#### [check-systemd-errors](./check-systemd-errors)
A diagnostic tool to quickly review systemd logs:
- **Filtering**: Shows error-level logs (`priority=err`) from a specified time period (default: 1 hour).
- **Summarization**: Provides a top-10 frequency summary of unique error messages.

### Media Management (Plex & Encoding)

Scripts focused on preparing and optimizing media for direct play on Plex.

#### [plex-preopt](./plex-preopt)
The main pipeline for optimizing video files.
- **Features:** Uses Intel VAAPI (`/dev/dri/renderD128`) for hardware transcoding. Falls back to CPU (`libx264`) if unavailable.
- **Strategy:** Smart remuxing (if codecs match) vs. transcoding. Mirrors source directory structure to `/mnt/pool/optimized`.
- **Idempotency:** Checks modification times (`mtime`) to skip already processed files.

#### [plex-preopt-single-test](./plex-preopt-single-test)
A testing tool to verify encoding settings on a single file before batch processing.
- **Usage:** `plex-preopt-single-test /path/to/file.mkv`

#### [plex_analyzer.py](./plex_analyzer.py)
A Python script to scan directories and identify files that may not Direct Play on Plex based on codecs and containers.

#### [convert-audiobook](./convert-audiobook)
Converts directories of MP3s into single `.m4b` audiobook files with chapters, utilizing the `sandreas/m4b-tool` Docker container.

### Docker Orchestration

Tools for managing a containerized environment defined in `/opt/docker/compose/`.

#### [update-docker-stacks](./update-docker-stacks)
Automated updater for Docker Compose stacks.
- **Workflow:** Pulls new images -> Compares digests -> Recreates containers only if changed -> Prunes dangling images.
- **Safety:** Includes dry-run capabilities and health checks.
- **Scope:** Operates on all `.yml` files in `/opt/docker/compose/` or specific ones passed as arguments.

### System & Git Administration

- **`dotpull.sh`**: Updates system dotfiles using `chezmoi` (pull + apply).
- **`delete-gh-repos`**: Bulk deletion tool for GitHub repositories using the GitHub CLI (`gh`).
- **`gemini-notify`**: A notification helper (visual + audio) used by AI agents to signal task completion.
- **`fix-vaapi`**: Configures permissions for Intel hardware acceleration (adds user to `render` group).
- **`morning-tabs`**: Opens morning routine URLs from `morning-urls.txt` in Brave browser.

## Architecture & Environment

- **Hardware Acceleration:** Intel Quick Sync Video (QSV) via VAAPI at `/dev/dri/renderD128`
- **Filesystem Layout:**
  - **Pool:** `/mnt/pool` (MergerFS union of drives)
  - **Docker Configs:** `/opt/docker/compose/`
  - **Logs:** Scripts log to `/tmp/` or `/var/log/` subdirectories

## Development Guidelines

New scripts should adhere to these standards:

- **Naming**: Follow Unix conventions—**no file extensions** (e.g., use `my-script`, not `my-script.sh`).
- **Shebangs**: Always include a proper shebang (e.g., `#!/bin/bash`).
- **Error Handling**: Use `set -euo pipefail` in Bash scripts.
- **Documentation**: Include usage/help text and keep docs updated.
- **Permissions**: Ensure scripts are executable (`chmod +x`).
- **Safety**: Implement `--dry-run` flags for destructive operations.

## Usage & Path

To use these scripts system-wide, ensure this directory is in your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Maintenance

- Periodically review scripts for deprecated commands.
- Test changes using `bash -n` (syntax) and `bash -x` (debug).
- Keep credentials out of scripts; use environment variables or local config files.
