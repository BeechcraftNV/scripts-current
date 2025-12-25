# Personal Utility Scripts

This directory contains personal utility scripts for system maintenance and automation.

## Scripts

### update-all

A comprehensive system update script that handles multiple package managers and provides detailed reporting.

**Usage:**
```bash
~/.local/bin/update-all
```

**What it does:**
- Updates APT packages (apt update && apt full-upgrade)
- Updates both system and user Flatpak packages
- Removes orphaned APT packages (autoremove)
- Cleans up unused Flatpak runtimes and SDKs
- Checks for EOL Flatpak runtimes (e.g., 23.08)
- Checks System76 firmware updates (if applicable)
- Reports on other update sources without auto-updating:
  - Docker dangling images
  - pip packages
  - pipx packages
  - Rust/Cargo packages
  - npm global packages
  - Firmware updates (fwupdmgr)

**Features:**
- Color-coded output for easy reading
- Comprehensive summary report showing:
  - Updated items
  - Skipped items (already current)
  - Failed operations
  - Available updates not automatically handled
- System impact assessment
- **Kernel version comparison**: Compares running kernel version (uname -r) with latest installed kernel version to determine if a reboot is required
- System service update detection (systemd, dbus, udev)
- Intelligent reboot recommendations based on:
  - Kernel version mismatch between running and installed
  - Kernel package updates detected
  - Critical system service updates
- Disk space reporting

**Requirements:**
- sudo access for APT and system Flatpak operations
- Supported package managers: apt, flatpak

**Backup:**
- `update-all_backup` - Previous version of the update script

## Setup

The `~/.local/bin` directory is typically already in your PATH on Ubuntu/Debian systems (configured in `~/.profile`).

To verify it's in your PATH:
```bash
echo $PATH | grep -o "$HOME/.local/bin"
```

If you need to add it manually, add the following to your `~/.profile`:

```bash
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
```

Then reload your shell configuration:
```bash
source ~/.profile
```

## Maintenance

Scripts in this directory should be:
- Executable: `chmod +x ~/.local/bin/script-name`
- Well-documented with comments
- Include error handling where appropriate
- Use descriptive names with lowercase and hyphens
