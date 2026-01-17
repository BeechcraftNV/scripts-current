# Personal Bin Directory Context

This directory (`~/.local/bin`) is a collection of personal utility scripts and application binaries/symlinks used for system maintenance, automation, and daily productivity.

## Project Overview

The directory serves as a central hub for custom CLI tools. It contains:
- **Custom Utility Scripts**: Hand-written Bash scripts for specialized system tasks.
- **Application Binaries/Symlinks**: Executables for installed tools like `uv`, `zed`, `claude`, and `logseq`.

## Key Scripts & Utilities

### [update-all](./update-all)
A comprehensive system maintenance script that automates:
- **APT Updates**: Full-upgrade and autoremove.
- **Flatpak Updates**: User-level package updates and cleanup.
- **Firmware Checks**: Integration with `system76-firmware-manager` and `fwupdmgr`.
- **System Health**: Checks for EOL runtimes and reports on Docker, pip, and npm status.
- **Reboot Detection**: Compares running vs. installed kernel versions and identifies critical system service updates (systemd, dbus, udev) to recommend reboots.

### [check-systemd-errors](./check-systemd-errors)
A diagnostic tool to quickly review systemd logs:
- **Filtering**: Shows error-level logs (`priority=err`) from a specified time period (default: 1 hour).
- **Summarization**: Provides a top-10 frequency summary of unique error messages.
- **Documentation**: Supported by [check-systemd-errors-howto.md](./check-systemd-errors-howto.md).

## Development Guidelines

Derived from [CLAUDE.md](./CLAUDE.md), new scripts should adhere to these standards:

- **Naming**: Follow Unix conventions—**no file extensions** (e.g., use `my-script`, not `my-script.sh`).
- **Shebangs**: Always include a proper shebang (e.g., `#!/bin/bash`).
- **Error Handling**: Use `set -eu` in Bash scripts to catch errors and undefined variables.
- **Documentation**: Include usage/help text and keep the main `README.md` updated.
- **Permissions**: Ensure scripts are executable (`chmod +x`).

## Usage & Path

To use these scripts system-wide, ensure this directory is in your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Maintenance

- Periodically review scripts for deprecated commands.
- Test changes using `bash -n` (syntax) and `bash -x` (debug).
- Keep credentials out of scripts; use environment variables or local config files.
