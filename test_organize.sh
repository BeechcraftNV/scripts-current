#!/usr/bin/env bash
set -euo pipefail

# Configuration
SRC="${DOWNLOADS_DIR:-$HOME/Downloads}"
BASE_DIR="${ORGANIZE_DIR:-$HOME}"
DRY_RUN="${DRY_RUN:-false}"

# Target directories
declare -A CATEGORIES=(
    ["Documents"]="pdf|docx?|txt|odt|rtf|epub"
    ["Config"]="conf|cfg|ini|json|yaml|yml|toml|md"
    ["Images"]="jpe?g|png|gif|bmp|svg|webp|tiff?"
    ["Audio"]="mp3|wav|flac|aac|ogg|m4a"
    ["Video"]="mp4|mkv|mov|avi|wmv|flv|webm|m4v"
    ["Archives"]="zip|tar|gz|bz2|xz|7z|rar"
    ["ISOs"]="iso"
    ["Packages"]="deb|rpm|appimage|snap|flatpak|dmg|msi"
    ["Torrents"]="torrent"
    ["NZB"]="nzb"
    ["Maps"]="kml|gpx|kmz"
)

# Create target directories
for category in "${!CATEGORIES[@]}"; do
    mkdir -p "$BASE_DIR/$category"
done
mkdir -p "$BASE_DIR/Other"

shopt -s nullglob nocaseglob
moved_count=0
skipped_count=0

for f in "$SRC"/*; do
    # Skip directories
    [[ -d "$f" ]] && continue
    
    filename=$(basename "$f")
    filename_lower="${filename,,}"
    moved=false
    
    # Check each category for a match
    for category in "${!CATEGORIES[@]}"; do
        pattern="${CATEGORIES[$category]}"
        if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
            target_file="$BASE_DIR/$category/$filename"
            
            if [[ -e "$target_file" ]]; then
                echo "SKIP: '$filename' - already exists in $category"
                ((skipped_count++))
            else
                echo "MOVE: '$filename' → $category/"
                [[ "$DRY_RUN" != "true" ]] && mv "$f" "$BASE_DIR/$category/"
                ((moved_count++))
            fi
            moved=true
            break
        fi
    done
    
    # If no category matched, move to Other
    if [[ "$moved" == "false" ]]; then
        target_file="$BASE_DIR/Other/$filename"
        if [[ -e "$target_file" ]]; then
            echo "SKIP: '$filename' - already exists in Other"
            ((skipped_count++))
        else
            echo "MOVE: '$filename' → Other/"
            [[ "$DRY_RUN" != "true" ]] && mv "$f" "$BASE_DIR/Other/"
            ((moved_count++))
        fi
    fi
done

echo "Complete: $moved_count moved, $skipped_count skipped"
