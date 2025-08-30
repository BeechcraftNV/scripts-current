#!/usr/bin/env bash
set -euo pipefail

# Configuration
SRC="${DOWNLOADS_DIR:-$HOME/Downloads}"
BASE_DIR="${ORGANIZE_DIR:-$HOME}"
DRY_RUN="${DRY_RUN:-false}"
VERBOSE="${VERBOSE:-false}"

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

log() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
    fi
}

# Check if source directory exists
if [[ ! -d "$SRC" ]]; then
    echo "Error: Source directory '$SRC' does not exist" >&2
    exit 1
fi

# Create target directories
for category in "${!CATEGORIES[@]}"; do
    mkdir -p "$BASE_DIR/$category"
done
mkdir -p "$BASE_DIR/Other"

log "Starting organization of '$SRC'"
log "Target base directory: '$BASE_DIR'"
[[ "$DRY_RUN" == "true" ]] && log "DRY RUN MODE - no files will be moved"

shopt -s nullglob nocaseglob
moved_count=0
skipped_count=0
processed_count=0

for f in "$SRC"/*; do
    # Skip if it's a directory
    if [[ -d "$f" ]]; then
        log "Skipping directory: $(basename "$f")"
        continue
    fi
    
    # Get filename, handling spaces properly
    filename=$(basename "$f")
    filename_lower="${filename,,}"
    moved=false
    
    # Special handling for large ISO files - ask before moving
    if [[ "$filename_lower" =~ \.iso$ ]] && [[ $(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null) -gt 1073741824 ]]; then
        size_gb=$(( $(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null) / 1073741824 ))
        if [[ "$DRY_RUN" != "true" ]] && [[ -t 0 ]]; then
            echo "Large ISO file detected: '$filename' (${size_gb}GB)"
            read -p "Move to ISOs directory? [y/N]: " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Skipping '$filename' per user request"
                ((skipped_count++))
                continue
            fi
        fi
    fi
    
    # Check each category for a match
    for category in "${!CATEGORIES[@]}"; do
        pattern="${CATEGORIES[$category]}"
        if [[ "$filename_lower" =~ \.(${pattern})$ ]]; then
            target_dir="$BASE_DIR/$category"
            target_file="$target_dir/$filename"
            
            if [[ -e "$target_file" ]]; then
                log "Skipping '$filename' - already exists in $category"
                ((skipped_count++))
            else
                if [[ "$DRY_RUN" == "true" ]]; then
                    echo "Would move: '$filename' → $category/"
                else
                    mv "$f" "$target_dir/"
                    log "Moved '$filename' → $category/"
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
            log "Skipping '$filename' - already exists in Other"
            ((skipped_count++))
        else
            if [[ "$DRY_RUN" == "true" ]]; then
                echo "Would move: '$filename' → Other/"
            else
                mv "$f" "$BASE_DIR/Other/"
                log "Moved '$filename' → Other/"
            fi
            ((moved_count++))
        fi
    fi
done

# Summary
echo "Organization complete:"
echo "  Files moved: $moved_count"
echo "  Files skipped: $skipped_count"
[[ "$DRY_RUN" == "true" ]] && echo "  (This was a dry run - no files were actually moved)"
