# Script Audit Report: ~/.local/bin/

Last updated: 2026-01-23

This report documents the active scripts and utilities in the local binary directory.

## Active System Utilities

*Core tools for system management and maintenance.*

| File | Purpose |
|---|---|
| `update-docker-stacks` | Docker Compose stack updater with health checks |
| `dotpull.sh` | Updates system dotfiles via `chezmoi` |
| `fix-vaapi` | Configures permissions for Intel hardware acceleration |
| `disable-sleep` | Prevents system sleep for 24/7 server operation |
| `ncdu_cleanup_cycle` | Interactive disk usage cleanup utility |
| `kiwix-rescan` | Restarts Kiwix container to pick up new ZIM files |
| `delete-gh-repos` | GitHub repository bulk deletion tool |
| `gemini-notify` | Desktop notification helper for Gemini CLI |
| `morning-tabs` | Opens morning routine URLs in Brave browser |
| `build-welcome-site` | Builds/deploys LAN welcome page with Hugo/Caddy |

## Active Media Utilities

*Tools for media processing and optimization.*

| File | Purpose |
|---|---|
| `plex-preopt` | Primary video optimization pipeline (VAAPI/CPU) |
| `plex-preopt-single-test` | Test encoder for single file verification |
| `convert-audiobook` | MP3 to M4B audiobook converter via Docker |
| `plex_analyzer.py` | Analyzes media files for Plex direct play compatibility |

## Binaries

*Compiled executables.*

| File | Type |
|---|---|
| `chezmoi` | Dotfile manager binary |
| `lazydocker` | Docker TUI binary |
| `claude` | Claude Code CLI (symlink) |

## Documentation Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Context file for Claude Code AI assistant |
| `GEMINI.md` | Context file for Gemini AI assistant |
| `SCRIPT_AUDIT.md` | This audit report |
| `Docker-update-fix.md` | Notes on Docker update script fixes |

## Audit History

- **2026-01-23**: Cleaned up duplicate shebangs in 4 scripts, improved morning-tabs error handling
- **Previous**: Removed obsolete one-off migration/setup scripts (media_ext4_migration, setup-mergerfs-pool, etc.)
