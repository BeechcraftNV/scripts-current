#!/usr/bin/env bash
set -euo pipefail

SRC="/home/steven/Downloads"

echo "Testing file processing logic..."

shopt -s nullglob nocaseglob
count=0

for f in "$SRC"/*; do
    if [[ -d "$f" ]]; then
        echo "DIRECTORY: $(basename "$f")"
        continue
    fi
    
    filename=$(basename "$f")
    filename_lower="${filename,,}"
    echo "Processing: '$filename'"
    
    # Test the ISO check that might be hanging
    if [[ "$filename_lower" =~ \.iso$ ]]; then
        echo "  ISO file detected, checking size..."
        file_size=$(stat -c%s "$f" 2>/dev/null || echo "0")
        echo "  Size: $file_size bytes"
        if [[ $file_size -gt 1073741824 ]]; then
            size_gb=$(( file_size / 1073741824 ))
            echo "  Large ISO: ${size_gb}GB"
        fi
    fi
    
    echo "  Processed successfully"
    
    # Stop after 5 files to avoid hanging
    ((count++)) || count=1
    if [[ $count -ge 5 ]]; then
        echo "Stopping after 5 files for safety"
        break
    fi
done

echo "Debug complete"
