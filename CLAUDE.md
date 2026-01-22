# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal utility scripts directory (`~/.local/bin`) synced to `git@github.com:BeechcraftNV/scripts-current.git`.

**Tracked:** Bash/Python scripts and documentation
**Ignored:** Binaries, symlinks (claude, zed), AppImages, .claude/, temp files (see .gitignore)

## Git Workflow

**Always sync before editing:**
```bash
sync-scripts  # Pulls with rebase, checks for uncommitted/unpushed changes
```

Uses rebase-first approach for clean history.

## Script Standards

- **No file extensions** - Use `my-script` not `my-script.sh` (Unix convention)
- **Shebang required** - `#!/bin/bash` or `#!/usr/bin/env python3`
- **Error handling** - Start bash scripts with `set -e` (exit on error)
- **Make executable** - `chmod +x script-name`

## Code Patterns

**Temporary files with cleanup:**
```bash
OUTPUT=$(mktemp)
trap 'rm -f $OUTPUT' EXIT
```

**State tracking for summary reports:**
```bash
declare -a UPDATED_ITEMS=()
declare -a SKIPPED_ITEMS=()
```

**Color constants:**
```bash
RED='\033[0;31m' GREEN='\033[0;32m' YELLOW='\033[1;33m' BLUE='\033[0;34m' NC='\033[0m'
```

**Command existence check:**
```bash
if command -v docker &> /dev/null; then
    # safe to use
fi
```

## Testing

```bash
bash -n script-name    # Syntax check
bash -x script-name    # Debug mode
```