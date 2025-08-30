#!/usr/bin/env bash

SRC="/home/steven/Downloads"

echo "Testing simple loop..."

shopt -s nullglob nocaseglob

for f in "$SRC"/*; do
    [[ -d "$f" ]] && continue
    
    filename=$(basename "$f")
    echo "Processing: $filename"
    
    # Just process 3 files
    ((count++)) 2>/dev/null || count=1
    [[ $count -ge 3 ]] && break
done

echo "Done"
