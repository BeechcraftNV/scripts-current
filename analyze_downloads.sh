#!/usr/bin/env bash

# Mirror the CATEGORIES array from organize_downloads.sh
declare -A CATEGORIES=(
    ["Documents"]="pdf|docx?|txt|odt|rtf|epub"
    ["Config"]="conf|cfg|ini|json|yaml|yml|toml|md"
    ["Images"]="jpe?g|png|gif|bmp|svg|webp|tiff?"
    ["Audio"]="mp3|wav|flac|aac|ogg|m4a"
    ["Video"]="mp4|mkv|mov|avi|wmv|flv|webm|m4v"
    ["Archives"]="zip|tar|gz|bz2|xz|7z|rar"
    ["ISOs"]="iso"
    ["Packages"]="deb|rpm|AppImage|snap|flatpak|dmg|msi"
    ["Torrents"]="torrent"
    ["Downloads"]="nzb"
    ["Maps"]="kml|gpx|kmz"
)

SRC="/home/steven/Downloads"
BASE_DIR="/home/steven"

echo "=== DOWNLOAD FILE CATEGORIZATION ANALYSIS ==="
echo "Source: $SRC"
echo "Target: $BASE_DIR"
echo

shopt -s nullglob nocaseglob

for f in "$SRC"/*; do
    # Skip if it's a directory
    if [[ -d "$f" ]]; then
        echo "DIRECTORY: $(basename "$f") - SKIPPED"
        continue
    fi
    
    filename=$(basename "$f")
    filename_lower="${filename,,}"
    matched=false
    
    # Check each category for a match
    for category in "${!CATEGORIES[@]}"; do
        pattern="${CATEGORIES[$category]}"
        if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
            target_file="$BASE_DIR/$category/$filename"
            if [[ -e "$target_file" ]]; then
                echo "$category: '$filename' - EXISTS (would skip)"
            else
                echo "$category: '$filename' - NEW (would move)"
            fi
            matched=true
            break
        fi
    done
    
    # If no category matched, move to Other
    if [[ "$matched" == "false" ]]; then
        target_file="$BASE_DIR/Other/$filename"
        if [[ -e "$target_file" ]]; then
            echo "Other: '$filename' - EXISTS (would skip)"
        else
            echo "Other: '$filename' - NEW (would move)"
        fi
    fi
done

echo
echo "=== SUMMARY BY CATEGORY ==="
for category in "${!CATEGORIES[@]}" "Other"; do
    count=0
    echo
    echo "$category:"
    for f in "$SRC"/*; do
        if [[ -d "$f" ]]; then continue; fi
        filename=$(basename "$f")
        filename_lower="${filename,,}"
        matched=false
        
        if [[ "$category" != "Other" ]]; then
            pattern="${CATEGORIES[$category]}"
            if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
                echo "  - $filename"
                ((count++))
                matched=true
            fi
        else
            # Check if it matches any category
            for cat in "${!CATEGORIES[@]}"; do
                pattern="${CATEGORIES[$cat]}"
                if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
                    matched=true
                    break
                fi
            done
            if [[ "$matched" == "false" ]]; then
                echo "  - $filename"
                ((count++))
            fi
        fi
    done
    echo "  Total: $count files"
done
