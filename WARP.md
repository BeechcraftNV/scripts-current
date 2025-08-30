# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This repository contains a collection of Bash scripts designed to automatically organize files from the Downloads directory into categorized folders. The core functionality is implemented across multiple script variants, each optimized for different use cases and safety considerations.

### High-Level Architecture

The project follows a pattern-matching approach using associative arrays to categorize files by extension:

```bash path=null start=null
Downloads/
├── document.pdf     → Documents/
├── music.mp3        → Audio/
├── photo.jpg        → Images/
├── installer.deb    → Packages/
└── unknown.xyz      → Other/
```

**Core Components:**
- **organize_downloads.sh** - Main production script with interactive prompts
- **organize_safe.sh** - Safe version that defaults to dry-run mode
- **organize_downloads_fixed.sh** - Improved version with better file handling
- **analyze_downloads.sh** - Analysis tool to preview organization without moving files
- **Test scripts** - Various debugging and validation utilities

## Quick Start

Test the organization (dry run):
```bash path=null start=null
./organize_downloads.sh
# Uses DRY_RUN=false by default, but shows what would happen
```

Safe preview mode:
```bash path=null start=null
./organize_safe.sh
# Defaults to DRY_RUN=true
```

Analyze current Downloads:
```bash path=null start=null
./analyze_downloads.sh
```

## Environment Configuration

All scripts respect the following environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `DOWNLOADS_DIR` | `$HOME/Downloads` | Source directory to organize |
| `ORGANIZE_DIR` | `$HOME` | Base directory for categorized folders |
| `DRY_RUN` | `false` (varies by script) | Preview mode - no files moved |
| `VERBOSE` | `false` | Enable detailed logging |

### Configuration Examples

```bash path=null start=null
# Custom source and destination
export DOWNLOADS_DIR="$HOME/Downloads"
export ORGANIZE_DIR="$HOME/Organized"
./organize_downloads.sh

# Dry run with verbose logging
DRY_RUN=true VERBOSE=true ./organize_downloads.sh

# One-liner for testing
DOWNLOADS_DIR=/tmp/test DRY_RUN=true ./organize_safe.sh
```

## Script Matrix

| Script | Purpose | Safety | Features |
|--------|---------|--------|----------|
| `organize_downloads.sh` | Main script | Interactive prompts for large ISOs | Case-insensitive matching, logging |
| `organize_safe.sh` | Safe version | Defaults to dry-run | Simplified output, safer defaults |
| `organize_downloads_fixed.sh` | Improved version | Better file handling | Uses `find` instead of shell glob |
| `analyze_downloads.sh` | Analysis tool | Read-only analysis | Preview categorization, summary stats |
| `test_organize.sh` | Test script | Minimal testing logic | Simplified version for debugging |
| `debug_organize.sh` | Debug tool | Debug file processing | ISO size checking, limited file processing |

## File Categories

The scripts organize files into these categories:

| Category | Extensions |
|----------|------------|
| Documents | `pdf`, `docx`, `doc`, `txt`, `odt`, `rtf`, `epub` |
| Config | `conf`, `cfg`, `ini`, `json`, `yaml`, `yml`, `toml`, `md` |
| Images | `jpeg`, `jpg`, `png`, `gif`, `bmp`, `svg`, `webp`, `tiff`, `tif` |
| Audio | `mp3`, `wav`, `flac`, `aac`, `ogg`, `m4a` |
| Video | `mp4`, `mkv`, `mov`, `avi`, `wmv`, `flv`, `webm`, `m4v` |
| Archives | `zip`, `tar`, `gz`, `bz2`, `xz`, `7z`, `rar` |
| ISOs | `iso` |
| Packages | `deb`, `rpm`, `appimage`, `snap`, `flatpak`, `dmg`, `msi` |
| Torrents | `torrent` |
| NZB | `nzb` |
| Maps | `kml`, `gpx`, `kmz` |
| Other | Any unmatched extensions |

## Usage Patterns

### Basic Organization
```bash path=null start=null
# Default behavior - organize ~/Downloads to ~/
./organize_downloads.sh

# See what would happen first
DRY_RUN=true ./organize_downloads.sh

# Verbose logging
VERBOSE=true ./organize_downloads.sh
```

### Custom Directories
```bash path=null start=null
# Organize different source directory
DOWNLOADS_DIR="$HOME/Inbox" ./organize_downloads.sh

# Use custom base directory
ORGANIZE_DIR="$HOME/FileSort" ./organize_downloads.sh
```

### Analysis and Testing
```bash path=null start=null
# See detailed breakdown by category
./analyze_downloads.sh

# Test array functionality
./test_array.sh

# Debug file processing issues
./debug_organize.sh
```

## Advanced Features

### Large ISO Handling

The main script includes special handling for ISO files larger than 1GB:
- Detects file size automatically  
- Prompts user for confirmation before moving
- Displays file size in GB for easy decision-making
- Skips if running in non-interactive mode

### Error Handling

All production scripts use:
```bash path=null start=null
set -euo pipefail
```
This ensures:
- Exit on any command failure (`-e`)
- Exit on undefined variables (`-u`) 
- Pipe failures are caught (`-o pipefail`)

### Safe File Processing

The `organize_downloads_fixed.sh` script uses `find` with null-termination to safely handle files with spaces and special characters:
```bash path=null start=null
mapfile -t files < <(find "$SRC" -maxdepth 1 -type f)
```

## GitHub Actions Integration

The repository includes automated CI/CD setup:

### Setup Workflows
```bash path=null start=null
./setup-actions-git.sh
```

This creates:
- **ci-pages.yml** - CI with GitHub Pages deployment
- **docker-publish.yml** - Docker image publishing to GHCR

### Workflows Created
- Builds on push to main branch
- Supports Node.js projects (npm ci, test, build)
- Publishes Docker images on version tags
- Deploys to GitHub Pages

## Development Commands

### Running Tests
```bash path=null start=null
# Test basic file processing
./test_simple.sh

# Test organization logic
./test_organize.sh  

# Test associative array handling
./test_array.sh

# Debug file processing with limited output
./debug_organize.sh
```

### Common Development Tasks
```bash path=null start=null
# Make all scripts executable
chmod +x *.sh

# Check script syntax
bash -n organize_downloads.sh

# Run shellcheck (if installed)
shellcheck *.sh

# Test with sample files
mkdir -p /tmp/test_downloads
touch /tmp/test_downloads/sample.{pdf,mp3,jpg,unknown}
DOWNLOADS_DIR=/tmp/test_downloads DRY_RUN=true ./organize_safe.sh
```

## Troubleshooting

### Common Issues

**Script hangs during execution:**
- Use `organize_downloads_fixed.sh` which uses `find` instead of shell globbing
- Check for files with unusual characters or very long names
- Run `debug_organize.sh` to isolate the problematic files

**Permission denied errors:**
```bash path=null start=null
# Ensure scripts are executable
chmod +x organize_downloads.sh

# Check directory permissions
ls -la "$DOWNLOADS_DIR"
ls -la "$ORGANIZE_DIR"
```

**Large ISO prompt not appearing:**
- Ensure script is running in interactive mode (`-t 0` test)
- Check that `DRY_RUN` is not set to `true`
- Verify ISO file is actually larger than 1GB

### Debugging File Processing
```bash path=null start=null
# Enable verbose mode
VERBOSE=true ./organize_downloads.sh

# Process only a few files for testing  
./debug_organize.sh

# Check specific file categorization
filename="test.pdf"
echo "Testing: $filename"
for category in Documents Images Audio; do
    pattern="pdf|docx?|txt"  # Documents pattern
    if [[ "${filename,,}" =~ \.(${pattern})$ ]]; then
        echo "Matches: $category"
    fi
done
```

## Customization

### Adding New Categories
Edit the `CATEGORIES` associative array in your chosen script:
```bash path=null start=null
declare -A CATEGORIES=(
    ["Documents"]="pdf|docx?|txt|odt|rtf|epub"
    ["MyCustomCategory"]="xyz|abc|custom"
    # ... existing categories
)
```

### Custom File Extensions
Modify existing patterns using extended regex:
```bash path=null start=null
["Images"]="jpe?g|png|gif|bmp|svg|webp|tiff?|heic|webm"
#                                              ^^^^^^^^^ added
```

The `?` makes the preceding character optional (e.g., `jpeg` or `jpg`, `tiff` or `tif`).
