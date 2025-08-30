#!/usr/bin/env bash

# Configuration
SRC="${DOWNLOADS_DIR:-$HOME/Downloads}"
BASE_DIR="${ORGANIZE_DIR:-$HOME}"
DRY_RUN="${DRY_RUN:-true}"  # Default to dry run for safety

# Target directories - Fixed patterns and category names
declare -A CATEGORIES=(
    ["Documents"]="pdf|docx|doc|txt|odt|rtf|epub"
    ["Config"]="conf|cfg|ini|json|yaml|yml|toml|md"
    ["Images"]="jpeg|jpg|png|gif|bmp|svg|webp|tiff|tif"
    ["Audio"]="mp3|wav|flac|aac|ogg|m4a"
    ["Video"]="mp4|mkv|mov|avi|wmv|flv|webm|m4v"
    ["Archives"]="zip|tar|gz|bz2|xz|7z|rar"
    ["ISOs"]="iso"
    ["Packages"]="deb|rpm|appimage|snap|flatpak|dmg|msi"
    ["Torrents"]="torrent"
    ["NZB"]="nzb"
    ["Maps"]="kml|gpx|kmz"
)

# Check if source directory exists
if [[ ! -d "$SRC" ]]; then
    echo "Error: Source directory '$SRC' does not exist" >&2
    exit 1
fi

echo "Source: $SRC"
echo "Target: $BASE_DIR"
[[ "$DRY_RUN" == "true" ]] && echo "DRY RUN MODE - no files will be moved"
echo

# Create target directories
for category in "${!CATEGORIES[@]}"; do
    mkdir -p "$BASE_DIR/$category"
done
mkdir -p "$BASE_DIR/Other"

moved_count=0
skipped_count=0

# Process files
while IFS= read -r -d '' file; do
    filename=$(basename "$file")
    filename_lower="${filename,,}"
    moved=false
    
    echo "Processing: $filename"
    
    # Check each category for a match
    for category in "${!CATEGORIES[@]}"; do
        pattern="${CATEGORIES[$category]}"
        if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
            target_file="$BASE_DIR/$category/$filename"
            
            if [[ -e "$target_file" ]]; then
                echo "  SKIP: already exists in $category/"
                ((skipped_count++))
            else
                echo "  MOVE: $filename → $category/"
                if [[ "$DRY_RUN" != "true" ]]; then
                    mv "$file" "$BASE_DIR/$category/"
                fi
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
            echo "  SKIP: already exists in Other/"
            ((skipped_count++))
        else
            echo "  MOVE: $filename → Other/"
            if [[ "$DRY_RUN" != "true" ]]; then
                mv "$file" "$BASE_DIR/Other/"
            fi
            ((moved_count++))
        fi
    fi
done < <(find "$SRC" -maxdepth 1 -type f -print0)

echo
echo "Summary:"
echo "  Files that would be moved: $moved_count"
echo "  Files that would be skipped: $skipped_count"
[[ "$DRY_RUN" == "true" ]] && echo "  (This was a dry run - no files were actually moved)"
