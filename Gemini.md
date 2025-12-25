# Personal Bin Directory - Gemini Agent Guidelines

This directory contains personal utility scripts. This file serves as the context and rule set for the Gemini CLI agent when working in this environment.

## Code Standards

### Script Structure
- **Shebangs**: All scripts must have a shebang (e.g., `#!/bin/bash`, `#!/usr/bin/env python3`).
- **Permissions**: Ensure scripts are executable (`chmod +x`).
- **Naming Convention**:
  - Use kebab-case (e.g., `my-script-name`).
  - **NO file extensions** for the final executable (e.g., create `update-system`, not `update-system.sh`).
  - This allows language migration without breaking the command interface.
- **Safety**:
  - Bash: Always use `set -e` (exit on error).
  - Bash: Use `set -u` (treat unset variables as an error) where feasible.
  - Python: Use `if __name__ == "__main__":` blocks.

### Dependencies & Environment
- **Path Independence**: Do not assume the script is run from `~/.local/bin`. Use `$(dirname "$0")` or absolute paths if referencing sibling files.
- **Portability**: Prefer standard POSIX utilities where possible, or check for tool existence (e.g., `command -v docker`) before execution.

## Documentation Requirements

- **Header**: Every script must start with a comment block explaining:
  1. What the script does.
  2. Usage examples (if arguments are required).
- **Complexity**: Add comments for complex regex or non-obvious logic.
- **Updates**: If a script is added or deprecated, update `README.md`.

## Safety & Security

- **Credentials**: NEVER hardcode API keys, passwords, or tokens. Use environment variables (e.g., `$GITHUB_TOKEN`).
- **Destructive Actions**:
  - Scripts performing deletions or overwrites should offer a `--dry-run` mode or require confirmation.
  - When writing such scripts, Gemini should explicitly ask the user to verify the logic.

## Gemini Workflow

- **Context Awareness**: Before creating new scripts, check `CLAUDE.md` and `README.md` to ensure no duplicate functionality exists.
- **Testing**:
  - After writing a script, propose a test command (e.g., `bash -n script` for syntax, or a dry-run execution).
- **Maintenance**:
  - If encountering a script with `#!/bin/sh` that uses bash-isms, propose refactoring to `#!/bin/bash`.
