#!/bin/bash
# Read the tool input from stdin (Claude Code passes it as JSON)
input=$(cat)
command=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('command',''))")

# Bail silently if not in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  exit 0
fi

# Only act on git add/commit/push
if ! echo "$command" | grep -qE "git (add|commit|push)"; then
  exit 0
fi

# Check if any tracked files changed but no .md files changed
changed_files=$(git diff --name-only HEAD 2>/dev/null)
changed_md=$(echo "$changed_files" | grep -c "\.md$")
changed_code=$(echo "$changed_files" | grep -cv "\.md$")

if [ "$changed_code" -gt 0 ] && [ "$changed_md" -eq 0 ]; then
  echo "WARNING: Code changes detected but no .md files updated. Consider updating CLAUDE.md or README before committing."
  exit 1  # Blocks the git operation
fi

exit 0
