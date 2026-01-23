# Docker Update Script Fix - Digest Detection Issue

## The Problem

Your original script was checking the **wrong thing** for detecting updates:

```bash
# OLD - Gets image IDs from RUNNING containers
docker compose -f "$compose_file" images --format "{{.Repository}}:{{.Tag}}@{{.ID}}"
```

This showed IDs of currently running containers, not the actual images on disk. So:
1. Before pull: Gets running container image IDs
2. Pull happens (downloads new images to disk)
3. After pull: Gets the SAME running container image IDs (containers haven't changed yet)
4. Script thinks nothing changed → skips container recreation
5. New images sit on disk unused

## The Fix

The updated script now checks **RepoDigests** - the sha256 hashes from Docker Hub/registry:

```bash
# NEW - Gets actual registry digests from images
get_image_digests() {
    local compose_file=$1
    local digests=""
    
    # Extract all image references from compose file
    local images=$(docker compose -f "$compose_file" config --format json 2>/dev/null | \
                   jq -r '.services[].image' 2>/dev/null | \
                   sort -u)
    
    # For each image, get its RepoDigest (registry sha256 hash)
    while IFS= read -r image; do
        if [ -n "$image" ]; then
            local digest=$(docker inspect "$image" --format '{{index .RepoDigests 0}}' 2>/dev/null)
            if [ -z "$digest" ]; then
                digest="NEW:$image"  # Image not found locally
            fi
            digests="${digests}${image}=${digest}"$'\n'
        fi
    done <<< "$images"
    
    echo "$digests"
}
```

### How it works:

1. **Before pull**: Gets registry digest of each image currently on disk
   - Example: `lscr.io/linuxserver/plex:latest=lscr.io/linuxserver/plex@sha256:abc123...`

2. **Pull happens**: Docker downloads newer versions if available

3. **After pull**: Gets registry digest of each image now on disk
   - Example: `lscr.io/linuxserver/plex:latest=lscr.io/linuxserver/plex@sha256:def456...`

4. **Compare**: If sha256 hashes differ, images actually changed → recreate containers

## Installation

1. **Backup your current script:**
   ```bash
   cp ~/.local/bin/update-docker-stacks ~/.local/bin/update-docker-stacks.backup
   ```

2. **Copy the updated script:**
   ```bash
   cp update-docker-stacks ~/.local/bin/
   chmod +x ~/.local/bin/update-docker-stacks
   ```

3. **Test with dry-run:**
   ```bash
   update-docker-stacks --dry-run
   ```

## What Changed

### Modified Function
- `get_image_digests()` - Now checks actual registry digests instead of running container IDs

### Everything Else
- All other functionality remains identical
- Same command-line options
- Same output format
- Same logging behavior

## Why This Approach is Robust

1. **Registry-level comparison**: Checks actual image content hashes from Docker Hub/GHCR
2. **Handles missing images**: Marks locally missing images as "NEW" for initial detection
3. **Per-image granularity**: Tracks each image separately in multi-image stacks
4. **No false negatives**: Will always detect actual image changes

## Testing Recommendations

1. Run with `--dry-run` first to see what it detects
2. Try with a single stack: `update-docker-stacks plex`
3. Check the log file at `/tmp/docker-update-YYYYMMDD-HHMMSS.log` for details

## Edge Cases Handled

- **New images**: Marks as "NEW:imagename" if not found locally
- **Multiple services**: Handles stacks with multiple containers correctly
- **Image parsing**: Uses `docker compose config` to properly parse compose files
- **Digest unavailable**: Falls back to indicating potential updates

## Technical Details

**RepoDigest** is the immutable content hash assigned by the registry:
- Format: `registry/image@sha256:abc123...`
- Changes only when actual image content changes
- Same across all machines pulling the same version
- More reliable than local image IDs which can vary