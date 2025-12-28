# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Personal Bin Directory

This is a personal utility scripts directory (`~/.local/bin`) containing custom system maintenance and automation tools.

## Repository Details

- **Git remote:** `git@github.com:BeechcraftNV/scripts-current.git`
- **Purpose:** Personal utility scripts synced across systems
- **Contains:** Executable bash scripts, binary symlinks, and downloaded tools
- **Git workflow:** Rebase-first approach to maintain clean history

### What's Tracked vs. Ignored

**Tracked (committed to git):**
- Bash scripts (update-all, check-systemd-errors, sync-scripts, update-glam)
- Documentation files (CLAUDE.md, README.md, GEMINI.md, etc.)

**Ignored (see .gitignore):**
- Binary executables (logseq, uv, uvx)
- Symlinks to applications (claude, zed)
- Python bytecode and virtual environments
- Editor directories (.vscode/, .idea/)
- Temporary files (*.tmp, *.log, *.swp)
- Package files (*.AppImage, *.deb, *.rpm)
- Claude Code settings (.claude/)

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

### update-glam
Modern, interactive version of `update-all` using Charm CLI tools (gum/glow).

**Dependencies:** Requires `gum` and `glow` installed
**Features:**
- Interactive confirmation prompts
- Spinner animations for long-running operations
- Markdown-formatted reports via glow
- Interactive post-update menu

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

## Architecture Patterns

### Script Structure
All bash scripts follow consistent patterns:

1. **Error handling:**
   - Start with `set -e` to exit on errors
   - Use `set +e` temporarily when errors are expected/acceptable
   - Include descriptive error messages with context

2. **Temporary file management:**
   ```bash
   OUTPUT=$(mktemp)
   trap 'rm -f $OUTPUT' EXIT  # Automatic cleanup
   ```

3. **State tracking arrays:**
   ```bash
   declare -a UPDATED_ITEMS=()
   declare -a SKIPPED_ITEMS=()
   declare -a FAILED_ITEMS=()
   declare -a AVAILABLE_NOT_RUN=()
   ```
   Items are added during execution, then reported in final summary.

4. **Color output:**
   ```bash
   RED='\033[0;31m'
   GREEN='\033[0;32m'
   YELLOW='\033[1;33m'
   BLUE='\033[0;34m'
   NC='\033[0m'  # No Color
   ```

5. **Command checking:**
   ```bash
   if command -v docker &> /dev/null; then
       # Command exists, use it
   fi
   ```

### Output Patterns

**update-all style:** Comprehensive reporting with:
- Real-time command output during execution
- Final summary report with categorized results
- Impact assessment and reboot recommendations
- Version comparisons (running vs. installed kernel)

**update-glam style:** Interactive UX with:
- `gum spin` for progress indicators
- `gum confirm` for user prompts
- `glow` for rendering markdown reports
- `gum choose` for menu selections

### Git Integration

Scripts in this repository use `sync-scripts` to maintain sync with GitHub:
- Checks for uncommitted/unpushed changes before pull
- Uses `git pull --rebase` to maintain linear history
- Provides clear error messages with suggested commands
