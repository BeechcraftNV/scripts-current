# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Personal Bin Directory

This is a personal utility scripts directory (`~/.local/bin`) containing custom system maintenance and automation tools.

## Key Scripts

### update-all
Comprehensive system update script that handles multiple package managers with detailed reporting.

**What it updates automatically:**
- APT packages (apt update && apt full-upgrade)
- System and user Flatpak packages
- Removes orphaned APT packages (autoremove)
- Cleans unused Flatpak runtimes/SDKs

**What it reports (but doesn't auto-update):**
- Docker dangling images
- pip/pipx packages
- Rust/Cargo packages
- npm global packages
- Firmware updates (fwupdmgr)
- System76 firmware (if applicable)

**Key features:**
- Kernel version comparison (running vs. installed) to detect reboot needs
- System service update detection (systemd, dbus, udev)
- Color-coded comprehensive summary report
- Disk space reporting

### check-systemd-errors
Reviews recent systemd logs for errors and provides a summary.

**Usage:** `check-systemd-errors [time-period]`

**Examples:**
- `check-systemd-errors` (default: last hour)
- `check-systemd-errors "today"`
- `check-systemd-errors "24 hours ago"`

### sync-scripts
Helper script to sync the repository with GitHub before editing.

**Usage:** `sync-scripts`

**What it does:**
- Checks for uncommitted changes (prevents pull if found)
- Checks for unpushed commits (reminds to push first)
- Pulls latest from GitHub using `git pull --rebase`
- Shows current branch and latest commit

**Use case:** Run before starting an editing session to ensure working with latest code.

## Git Workflow

This directory is version controlled and synced to GitHub at `git@github.com:BeechcraftNV/scripts-current.git`.

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

### Why This Matters
- Prevents working on outdated code
- Avoids merge conflicts
- Keeps local and remote in sync
- Ensures changes aren't lost

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
- Use `set -e` in bash scripts to exit on errors
- Use `set -u` in bash scripts to catch undefined variables
- Include usage/help text for scripts with arguments
- Add error handling with clear messages
- Check for required commands before using: `command -v cmd` or `which cmd`

### Path Handling
- Use absolute paths or properly handle relative paths
- Don't assume this directory is in PATH
- For scripts referencing other local scripts, use `$(dirname "$0")`

### Compatibility
- Consider target systems (Linux/macOS/WSL)
- Avoid bash-isms if using `#!/bin/sh`

## Testing Scripts

**Syntax check:** `bash -n script.sh`
**Debug mode:** `bash -x script.sh`

## Architecture Notes

- This directory contains standalone utility scripts, not a cohesive application
- Scripts use temporary files with trap cleanup (see update-all for pattern)
- Color output uses ANSI escape codes (RED, GREEN, YELLOW, BLUE, NC)
- Arrays track state for reporting (UPDATED_ITEMS, SKIPPED_ITEMS, FAILED_ITEMS, AVAILABLE_NOT_RUN)
