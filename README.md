# Personal Utility Scripts

This repository contains personal utility scripts for system maintenance and automation, stored in `~/.local/bin`.

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

**Key Features:**
- Color-coded comprehensive summary report
- Kernel version comparison (running vs. installed) to detect reboot needs
- System service update detection (systemd, dbus, udev)
- EOL runtime detection (e.g., Flatpak 23.08)
- Disk space reporting
- Intelligent reboot recommendations

**Requirements:**
- sudo access for APT and system Flatpak operations
- Bash shell

---

### update-glam

Modern, interactive version of `update-all` using Charm CLI tools (gum/glow).

**Usage:**
```bash
update-glam
```

**Dependencies:**
- `gum` - Interactive CLI components
- `glow` - Markdown renderer

**Features:**
- Interactive confirmation prompts for updates
- Spinner animations for long-running operations
- Markdown-formatted reports rendered with glow
- Interactive post-update menu for optional maintenance tasks
- Kernel version checking with visual warnings

**What it updates:**
- APT packages (with confirmation)
- System Flatpak packages

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

Comprehensive LAN device scanner that discovers both active and sleeping devices on your network.

**Usage:**
```bash
lan-scanner
```

**Features:**
- Combines nmap, mDNS/Bonjour, and ARP cache for complete device discovery
- Finds sleeping/idle devices (phones, tablets, printers)
- Shows IP address, hostname, and device manufacturer
- Color-coded status indicators (active vs. cached)
- Auto-detects network range
- Auto-elevates to sudo when needed

**What it scans:**
- **nmap with ARP:** Active devices responding to network requests
- **mDNS/Bonjour:** Apple devices, printers, smart home devices
- **ARP cache:** Recently seen devices (even if currently sleeping)

**Output includes:**
- IP address (sorted numerically)
- Hostname (from DNS, mDNS, or reverse lookup)
- Device manufacturer (from MAC address vendor database)
- Status: Active (●) or Cached/Recently Seen (○)

**Requirements:**
- `nmap` - Network scanning tool
- `avahi-browse` - mDNS/Bonjour discovery (usually pre-installed on Linux)
- sudo access (script will auto-request)

**Example output:**
```
1.  ● 192.168.29.1    │ router.local                  │ ASUSTek Computer
2.  ● 192.168.29.43   │ server.local                  │ Shenzhen Madigi
3.  ○ 192.168.29.171  │ HP846993CE62EB.local          │ HP Inc.
```

---

### format-nmap

Helper script to format nmap output in a more readable form.

**Usage:**
```bash
format-nmap
```

**What it does:**
- Runs `nmap -sn` scan on detected network
- Formats output with clear section headers
- Shows host status with visual indicators
- Displays MAC addresses and vendor info separately

**Note:** This is a simpler alternative to `lan-scanner`. For comprehensive device discovery, use `lan-scanner` instead.

**Requirements:**
- `nmap` - Network scanning tool
- sudo access

## Installation

### Clone the Repository

```bash
git clone git@github.com:BeechcraftNV/scripts-current.git ~/.local/bin-temp
cp ~/.local/bin-temp/* ~/.local/bin/
rm -rf ~/.local/bin-temp
```

Or manually place scripts in `~/.local/bin/`.

### Add to PATH

The `~/.local/bin` directory is typically already in your PATH on Ubuntu/Debian systems (configured in `~/.profile`).

To verify:
```bash
echo $PATH | grep -o "$HOME/.local/bin"
```

If not in PATH, add to `~/.profile`:
```bash
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

Then reload:
```bash
source ~/.profile
```

### Make Scripts Executable

```bash
chmod +x ~/.local/bin/update-all
chmod +x ~/.local/bin/check-systemd-errors
```

## Repository Structure

```
~/.local/bin/
├── .gitignore                        # Excludes binaries and temp files
├── CLAUDE.md                         # Claude Code guidance
├── README.md                         # This file
├── GEMINI.md, Gemini.md              # Additional documentation
├── check-systemd-errors              # Systemd error checker
├── check-systemd-errors-howto.md     # Usage guide
├── format-nmap                       # nmap output formatter
├── lan-scanner                       # Comprehensive LAN device scanner
├── sync-scripts                      # Repository sync helper
├── update-all                        # System update script
└── update-glam                       # Interactive update script (gum/glow)
```

### What's Tracked in Git

**Committed to repository:**
- Shell scripts (update-all, update-glam, check-systemd-errors, sync-scripts, lan-scanner, format-nmap)
- Documentation files (CLAUDE.md, README.md, GEMINI.md, etc.)
- Configuration (.gitignore)

**Excluded from version control:**
- Binary executables (logseq, uv, uvx)
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
- Use `set -e` in bash scripts to exit on errors
- Use `set -u` in bash scripts to catch undefined variables
- Include usage/help text for scripts with arguments
- Add error handling with clear messages
- Check for required commands before using: `command -v cmd`

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
