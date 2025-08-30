#!/usr/bin/env bash
set -euo pipefail

declare -A CATEGORIES=(
    ["Documents"]="pdf|docx?|txt|odt|rtf|epub"
    ["Config"]="conf|cfg|ini|json|yaml|yml|toml|md"
    ["NZB"]="nzb"
)

SRC="/home/steven/Downloads"

echo "Testing associative array iteration..."

shopt -s nullglob nocaseglob

for f in "$SRC"/*; do
    [[ -d "$f" ]] && continue
    
    filename=$(basename "$f")
    filename_lower="${filename,,}"
    echo "Processing: $filename"
    
    # Check each category
    for category in "${!CATEGORIES[@]}"; do
        pattern="${CATEGORIES[$category]}"
        echo "  Testing category '$category' with pattern '$pattern'"
        if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
            echo "  MATCH: $category"
            break
        else
            echo "  No match for $category"
        fi
    done
    
    # Just process 1 file
    break
done

echo "Done"
