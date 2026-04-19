# Personal Utility Scripts

This repository contains personal utility scripts for system maintenance and automation, stored in `~/bin`.

**Git Repository:** `git@github.com:BeechcraftNV/scripts-current.git`

## Scripts

### update-all

A comprehensive system update script that handles multiple package managers with detailed reporting.

**Usage:**
```bash
update-all
```

**What it updates automatically:**
- APT packages (apt update && apt full-upgrade)
- User Flatpak packages (user installation only)
- Removes orphaned APT packages (autoremove)
- Cleans unused user Flatpak runtimes/SDKs

**What it reports:**
- Docker dangling images
- NPM & PIP outdated packages
- Firmware updates (fwupdmgr & System76)
- Flatpak EOL runtimes
- Kernel mismatch and reboot requirements (with package list)

**Key Features:**
- Color-coded comprehensive summary report (always displays, even if errors occur)
- Robust error handling - continues execution even if individual steps fail
- Failed operations tracked and reported separately
- Kernel version comparison (running vs. installed) to detect reboot needs
- Streamlined impact assessment

**Requirements:**
- sudo access for APT operations
- Bash shell

---

### check-systemd-errors

Reviews recent systemd logs for errors and provides a summary.

**Usage:**
```bash
check-systemd-errors [time-period]
```

**Examples:**
```bash
check-systemd-errors              # Last hour (default)
check-systemd-errors "today"      # All errors from today
check-systemd-errors "24 hours ago"
check-systemd-errors "since boot"
```

**Output:**
- Lists all error-priority messages from journalctl
- Provides a top-10 summary of most frequent errors
- Uses reverse chronological order (newest first)

**Requirements:**
- Access to journalctl (usually requires user to be in systemd-journal group)

---

### sync-scripts

Helper script to sync the repository with GitHub before editing.

**Usage:**
```bash
sync-scripts
```

**What it does:**
- Checks for uncommitted changes and warns if found
- Checks for unpushed commits and reminds to push
- Pulls latest from GitHub using rebase
- Shows current branch and latest commit

**Safety features:**
- Prevents pull if you have uncommitted changes
- Prevents pull if you have unpushed commits
- Provides helpful error messages with suggested commands

**Use case:** Run this before starting an editing session to ensure you're working with the latest code.

**Requirements:**
- Git repository configured with remote origin

---

### lan-scanner

Comprehensive LAN device scanner that discovers both active and sleeping devices on your network with deep-scan capabilities and custom labeling.

**Usage:**
```bash
lan-scanner [options]
```

**Options:**
- `-d, --deep`: Perform a deep scan (Top 100 ports + HTTP title + service detection)
- `-h, --help`: Show help message

**Features:**
- **Custom Labels**: Assign friendly names to devices via `~/.config/lan-scanner/labels.conf`.
- **HTTP Title Detection**: Automatically grabs web page titles in deep scan mode for better device ID.
- **Local IP Identification**: Labels your current machine as `(YOU)`.
- **Deep Scan Mode**: Identifies open ports and services (like HTTP, SSH, AirPlay).
- **Multi-Source Discovery**: Combines `nmap`, `avahi-browse` (mDNS), and ARP cache.
- **Service Integration**: Displays mDNS service names (e.g., `_googlecast`, `_ipp`) directly in the info column.
- **Enhanced Table Layout**: A clean, aligned table with prioritized hostnames, labels, and status indicators.
- **Auto-detects Network**: Finds your local subnet automatically.

**Requirements:**
- `nmap` - Network scanning tool
- `avahi-browse` - mDNS/Bonjour discovery
- `ip`, `column`, `bash`
- sudo access (script will auto-request)

---

### format-nmap

Helper script to format nmap output in a more readable, emoji-fied form.

**Usage:**
```bash
format-nmap
```

**What it does:**
- Automatically detects your current network range.
- Runs a fast ping scan.
- Formats output with 🖥️ (Host), ✓ (Status), and 🔧 (MAC).
- Uses color-coded section headers.

**Note:** This is a stylistic alternative to `lan-scanner`. For comprehensive device and service discovery, use `lan-scanner` instead.

**Requirements:**
- `nmap` - Network scanning tool
- sudo access

---

### sort_raindrops

Python script to sort Raindrop.io bookmarks and collections.

**Usage:**
```bash
sort_raindrops
```

**What it does:**
- Sorts all collections alphabetically by title
- Within each collection, sorts bookmarks by date (oldest first)
- Updates sort order via Raindrop.io API

**Setup:**
1. Get your API token from [Raindrop.io settings](https://app.raindrop.io/settings/integrations)
2. Add to your shell profile:
   ```bash
   export RAINDROP_TOKEN='your-token-here'
   ```

**Requirements:**
- Python 3
- `requests` library (`pip install requests`)
- `RAINDROP_TOKEN` environment variable

## Installation

### Clone the Repository

```bash
git clone git@github.com:BeechcraftNV/scripts-current.git ~/bin
```

Or manually place scripts in `~/bin/`.

### Add to PATH

The `~/bin` directory is typically already in your PATH on Ubuntu/Debian systems (configured in `~/.profile`).

To verify:
```bash
echo $PATH | grep -o "$HOME/bin"
```

If not in PATH, add to `~/.profile`:
```bash
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi
```

Then reload:
```bash
source ~/.profile
```

### Make Scripts Executable

```bash
chmod +x ~/bin/update-all
chmod +x ~/bin/check-systemd-errors
```

## Repository Structure

```
~/bin/
├── .gitignore                        # Excludes binaries and temp files
├── CLAUDE.md                         # Claude Code guidance
├── README.md                         # This file
├── GEMINI.md, Gemini.md              # Additional documentation
├── SCRIPT_AUDIT.md                   # Script inventory and audit log
├── Docker-update-fix.md              # Docker update notes
├── backup-media-settings             # Backs up media app settings
├── check-systemd-errors              # Systemd error checker
├── check-system-errors-glam          # Systemd error checker (glamour variant)
├── check-systemd-errors-howto.md     # Usage guide
├── check-md-before-git.sh            # Pre-commit markdown checker
├── convert-audiobook                 # MP3 to M4B audiobook converter
├── delete-gh-repos                   # GitHub repository bulk deletion tool
├── disable-sleep                     # Prevents system sleep
├── dotpull.sh                        # Updates dotfiles via chezmoi
├── fix-vaapi                         # Configures Intel hardware acceleration
├── format-nmap                       # nmap output formatter
├── fresh                             # Fresh install helper
├── fresh-editor                      # Fresh install editor setup
├── gemini-notify                     # Desktop notification helper for Gemini CLI
├── kiwix-rescan                      # Restarts Kiwix container for new ZIM files
├── lan-scanner                       # Comprehensive LAN device scanner
├── morning-tabs                      # Opens morning routine URLs
├── morning-urls.txt                  # URL list for morning-tabs
├── ncdu_cleanup_cycle                # Interactive disk usage cleanup
├── plex_analyzer.py                  # Analyzes media for Plex direct play
├── plex-preopt                       # Primary video optimization pipeline
├── plex-preopt-single-test           # Test encoder for single file verification
├── rquote                            # Random quote utility
├── sort_raindrops                    # Raindrop.io bookmark sorter
├── sync-scripts                      # Repository sync helper
├── update-all                        # System update script
├── update-docker-stacks              # Docker Compose stack updater
└── yt-dlp                            # YouTube/media downloader binary
```

### What's Tracked in Git

**Committed to repository:**
- Shell scripts (update-all, check-systemd-errors, sync-scripts, lan-scanner, format-nmap, and more)
- Python scripts (sort_raindrops, plex_analyzer.py)
- Documentation files (CLAUDE.md, README.md, GEMINI.md, etc.)
- Configuration (.gitignore)

**Excluded from version control:**
- Binary executables (chezmoi, lazydocker, logseq, uv, uvx)
- Application symlinks (claude, zed)
- Python bytecode and virtual environments
- Editor directories (.vscode/, .idea/)
- Temporary files (*.tmp, *.log, *.swp)
- Package files (*.AppImage, *.deb, *.rpm)
- Claude Code settings (.claude/)

This directory may contain these excluded items locally, but they won't be synced to GitHub.

## Script Standards

### Naming and Structure
- No file extensions (.sh, .py, etc.) - follows Unix convention (like git, docker)
- Always include shebang line (#!/bin/bash, #!/usr/bin/env python3, etc.)
- Make scripts executable: `chmod +x script-name`

### Code Quality
- Use `set -e` judiciously in bash scripts (consider if you need graceful degradation)
- For scripts that should complete and report even with failures, use explicit error checking
- Use `set -u` in bash scripts to catch undefined variables
- Include usage/help text for scripts with arguments
- Add error handling with clear messages
- Check for required commands before using: `command -v cmd`
- Use EXIT traps for cleanup and final reporting

### Common Patterns

**Temporary file cleanup:**
```bash
OUTPUT=$(mktemp)
trap 'rm -f $OUTPUT' EXIT  # Automatic cleanup on exit
```

**State tracking:**
```bash
declare -a UPDATED_ITEMS=()
declare -a SKIPPED_ITEMS=()
# Add items during execution, report at end
```

**Color output:**
```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color
```

**Command existence check:**
```bash
if command -v docker &> /dev/null; then
    # Command exists, safe to use
fi
```

### Testing
```bash
bash -n script-name    # Syntax check
bash -x script-name    # Debug mode
```

## Development Workflow

### Before Making Changes

**Always sync first:**
```bash
sync-scripts  # Pull latest changes from GitHub
```

This prevents merge conflicts and ensures you're working with the latest code.

### Making Changes

1. **Sync:** Run `sync-scripts`
2. **Edit:** Make your changes
3. **Test:** Verify the script works correctly
4. **Commit and push:**
   ```bash
   git add <files>
   git commit -m "descriptive message"
   git push
   ```

### Adding New Scripts

When adding new scripts to this repository:
1. Follow the script standards above
2. Remove file extensions from script names
3. Make executable: `chmod +x script-name`
4. Add documentation to this README
5. Update CLAUDE.md if needed for AI assistant context
6. Test thoroughly before committing
7. Use `sync-scripts` workflow for git operations

## License

Personal utility scripts for private use.
