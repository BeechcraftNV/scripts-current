# Download Organizer Scripts 🗂️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Shell](https://img.shields.io/badge/Shell-Bash-green.svg)](https://www.gnu.org/software/bash/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-blue.svg)](https://github.com/)

A collection of Bash scripts to automatically organize files from your Downloads directory into categorized folders. Keep your Downloads clean and organized with smart file categorization based on extensions.

## 🚀 Quick Start

```bash
# Clone the repository
git clone <your-repo-url>
cd scripts-current

# Make scripts executable
chmod +x *.sh

# Test with dry run (safe - no files moved)
./organize_safe.sh
```

## 📋 Table of Contents

- [Features](#-features)
- [Script Overview](#-script-overview)
- [Installation](#-installation)
- [Usage](#-usage)
- [File Categories](#-file-categories)
- [Configuration](#-configuration)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [GitHub Actions](#-github-actions)
- [Contributing](#-contributing)

## ✨ Features

- **Smart Categorization**: Automatically sorts files by extension into logical folders
- **Multiple Script Variants**: Choose between safe, interactive, and optimized versions
- **Dry Run Mode**: Preview changes before actually moving files
- **Large File Handling**: Special prompts for large ISO files (>1GB)
- **Comprehensive Logging**: Verbose mode for detailed operation tracking
- **Error Handling**: Robust error handling with `set -euo pipefail`
- **Customizable**: Easy to add new categories and file extensions
- **Cross-Platform**: Works on Linux and macOS

## 🛠️ Script Overview

| Script | Purpose | Safety Level | Key Features |
|--------|---------|--------------|-------------|
| `organize_safe.sh` | **Beginner-friendly** | 🟢 Highest | Defaults to dry-run, uses `find` for safe file handling |
| `organize_downloads.sh` | **Main script** | 🟡 Interactive | User prompts for large ISOs, detailed logging |
| `organize_downloads_fixed.sh` | **Production** | 🟡 Enhanced | Improved file handling, prevents shell globbing issues |
| `analyze_downloads.sh` | **Analysis tool** | 🟢 Read-only | Preview categorization without moving files |
| `debug_organize.sh` | **Debugging** | 🟢 Limited | Process only 5 files for troubleshooting |
| `test_organize.sh` | **Testing** | 🟡 Minimal | Simplified logic for development testing |
| `test_simple.sh` | **Basic test** | 🟢 Safe | Process 3 files for quick validation |
| `test_array.sh` | **Array testing** | 🟢 Single file | Test associative array functionality |
| `setup-actions-git.sh` | **CI/CD setup** | 🟡 Git operations | Creates GitHub Actions workflows |

## 📦 Installation

### Prerequisites
- Bash 4.0+ (for associative arrays)
- Standard Unix tools (`find`, `stat`, `mv`)

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd scripts-current

# Make all scripts executable
chmod +x *.sh

# Optional: Add to PATH for system-wide access
echo 'export PATH="$PATH:/path/to/scripts-current"' >> ~/.bashrc
source ~/.bashrc
```

## 🎯 Usage

### Basic Usage

```bash
# Safe mode (dry run by default)
./organize_safe.sh

# Main script with interactive prompts
./organize_downloads.sh

# Preview what would happen
DRY_RUN=true ./organize_downloads.sh

# Enable verbose logging
VERBOSE=true ./organize_downloads.sh
```

### Custom Directories

```bash
# Organize a different source directory
DOWNLOADS_DIR="$HOME/Desktop" ./organize_safe.sh

# Use custom destination
ORGANIZE_DIR="$HOME/Sorted" ./organize_downloads.sh

# Combine options
DOWNLOADS_DIR="/tmp/files" ORGANIZE_DIR="/tmp/organized" DRY_RUN=true ./organize_safe.sh
```

## 📁 File Categories

Files are automatically sorted into these categories:

| Category | Extensions | Example Files |
|----------|------------|---------------|
| **Documents** | `pdf`, `docx`, `doc`, `txt`, `odt`, `rtf`, `epub` | reports.pdf, resume.docx |
| **Images** | `jpg`, `jpeg`, `png`, `gif`, `bmp`, `svg`, `webp`, `tiff` | photo.jpg, screenshot.png |
| **Audio** | `mp3`, `wav`, `flac`, `aac`, `ogg`, `m4a` | music.mp3, podcast.wav |
| **Video** | `mp4`, `mkv`, `mov`, `avi`, `wmv`, `webm` | movie.mp4, clip.mov |
| **Archives** | `zip`, `tar`, `gz`, `bz2`, `xz`, `7z`, `rar` | backup.zip, source.tar.gz |
| **Packages** | `deb`, `rpm`, `appimage`, `snap`, `dmg`, `msi` | app.deb, installer.msi |
| **Config** | `conf`, `cfg`, `ini`, `json`, `yaml`, `toml`, `md` | config.json, README.md |
| **ISOs** | `iso` | ubuntu.iso, game.iso |
| **Torrents** | `torrent` | linux.torrent |
| **Maps** | `kml`, `gpx`, `kmz` | route.gpx, map.kml |
| **NZB** | `nzb` | download.nzb |
| **Other** | *anything else* | unknown.xyz |

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOWNLOADS_DIR` | `$HOME/Downloads` | Source directory to organize |
| `ORGANIZE_DIR` | `$HOME` | Base directory for category folders |
| `DRY_RUN` | `false` (varies by script) | Preview mode - no files moved |
| `VERBOSE` | `false` | Enable detailed logging |

### Adding Custom Categories

Edit the `CATEGORIES` associative array in any script:

```bash
declare -A CATEGORIES=(
    ["Documents"]="pdf|docx?|txt|odt|rtf|epub"
    ["MyCategory"]="xyz|abc|custom"  # Add your category
    # ... existing categories
)
```

## 📝 Examples

### Example 1: Safe Organization

```bash
$ ./organize_safe.sh
Source: /home/user/Downloads
Target: /home/user
DRY RUN MODE - no files will be moved

Processing: report.pdf
  MOVE: report.pdf → Documents/
Processing: vacation.jpg
  MOVE: vacation.jpg → Images/
Processing: installer.deb
  MOVE: installer.deb → Packages/

Summary:
  Files that would be moved: 3
  Files that would be skipped: 0
  (This was a dry run - no files were actually moved)
```

### Example 2: Large ISO Handling

```bash
$ ./organize_downloads.sh
Large ISO file detected: 'ubuntu-20.04.iso' (3GB)
Move to ISOs directory? [y/N]: y
Moved 'ubuntu-20.04.iso' → ISOs/

Organization complete:
  Files moved: 1
  Files skipped: 0
```

### Example 3: Analysis Mode

```bash
$ ./analyze_downloads.sh
=== DOWNLOAD FILE CATEGORIZATION ANALYSIS ===
Source: /home/user/Downloads
Target: /home/user

Documents: 'report.pdf' - NEW (would move)
Images: 'photo.jpg' - EXISTS (would skip)
Other: 'unknown.xyz' - NEW (would move)

=== SUMMARY BY CATEGORY ===
Documents:
  - report.pdf
  - manual.docx
  Total: 2 files
```

## 🐛 Troubleshooting

### Common Issues

**Script hangs during execution:**
```bash
# Use the fixed version with better file handling
./organize_downloads_fixed.sh

# Or debug with limited processing
./debug_organize.sh
```

**Permission denied:**
```bash
# Ensure scripts are executable
chmod +x *.sh

# Check directory permissions
ls -la "$HOME/Downloads"
```

**Files not being categorized:**
```bash
# Test with a single file
./test_array.sh

# Check pattern matching
VERBOSE=true ./organize_safe.sh
```

### Debug Commands

```bash
# Test with sample files
mkdir -p /tmp/test_downloads
touch /tmp/test_downloads/{test.pdf,music.mp3,photo.jpg}
DOWNLOADS_DIR=/tmp/test_downloads DRY_RUN=true ./organize_safe.sh

# Syntax check
bash -n organize_downloads.sh

# Run with shellcheck (if available)
shellcheck *.sh
```

## 🚀 GitHub Actions

This repository includes automated CI/CD setup:

```bash
# Set up GitHub Actions workflows
./setup-actions-git.sh
```

This creates:
- **CI/CD Pipeline**: Automated testing on push to main
- **Docker Publishing**: Container images published to GitHub Container Registry
- **GitHub Pages**: Documentation deployment

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Test** your changes: `./test_organize.sh`
4. **Commit** your changes: `git commit -am 'Add feature'`
5. **Push** to the branch: `git push origin feature-name`
6. **Create** a Pull Request

### Development Workflow

```bash
# Run all tests
./test_simple.sh && ./test_array.sh && ./test_organize.sh

# Check syntax
bash -n *.sh

# Test with dry run
DRY_RUN=true ./organize_downloads.sh
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for efficient Downloads folder management
- Inspired by the need for automated file organization
- Designed with safety and flexibility in mind
