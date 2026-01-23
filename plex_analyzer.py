#!/usr/bin/env python3
import os
import subprocess
import json

def get_video_info(file_path):
    """Uses ffprobe to get detailed information about a video file."""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error processing {file_path}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {file_path}: {e}")
        return None

def is_likely_direct_play_compatible(video_info):
    """
    Checks if a video file is likely to direct play on a wide range of modern Plex clients.
    This is based on common, widely supported codecs and containers.
    This is an *assumption* and not a guarantee for all clients.
    """
    if not video_info or 'streams' not in video_info:
        return False, "No valid video info or streams found."

    video_stream = None
    audio_stream = None
    for stream in video_info['streams']:
        if stream['codec_type'] == 'video':
            video_stream = stream
        elif stream['codec_type'] == 'audio':
            # Prioritize a common audio codec if multiple exist
            if not audio_stream or stream['codec_name'].lower() in ['aac', 'ac3']:
                audio_stream = stream

    if not video_stream:
        return False, "No video stream found."
    if not audio_stream:
        return False, "No audio stream found."

    # Check video codec
    video_codec = video_stream['codec_name'].lower()
    if video_codec not in ['h264', 'hevc']: # H.264 is widely compatible, HEVC (H.265) is increasingly common
        return False, f"Unsupported video codec: {video_codec}"

    # Check audio codec
    audio_codec = audio_stream['codec_name'].lower()
    if audio_codec not in ['aac', 'ac3']: # AAC and AC3 are widely compatible
        return False, f"Unsupported audio codec: {audio_codec}"

    # Check container format (format_name is usually the extension without dot, or similar)
    container_format = video_info['format']['format_name'].lower()
    # Common container formats that often direct play
    if not any(f in container_format for f in ['mp4', 'mkv', 'mov']):
        return False, f"Uncommon container: {container_format}"

    # Additional checks can be added here, e.g., for resolution, bitrate, etc.
    # For simplicity, we'll focus on codecs and container for basic compatibility.

    return True, "Likely direct play compatible."

def main():
    target_directory = input("Enter the directory to scan: ").strip()

    if not os.path.isdir(target_directory):
        print(f"Error: Directory '{target_directory}' not found.")
        return

    video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.ts', '.m2ts')
    compatible_files = []
    needs_conversion_files = []
    unprocessed_files = [] # Files that couldn't be analyzed by ffprobe

    print(f"\nScanning directory: {target_directory}")
    print("This may take some time depending on the number and size of video files...\n")

    for root, _, files in os.walk(target_directory):
        for file in files:
            if file.lower().endswith(video_extensions):
                full_path = os.path.join(root, file)
                print(f"Analyzing: {full_path}")
                video_info = get_video_info(full_path)
                if video_info:
                    is_compatible, reason = is_likely_direct_play_compatible(video_info)
                    if is_compatible:
                        compatible_files.append((full_path, reason))
                    else:
                        needs_conversion_files.append((full_path, reason))
                else:
                    unprocessed_files.append(full_path)

    print("\n--- Scan Results ---")
    print(f"Total video files found: {len(compatible_files) + len(needs_conversion_files) + len(unprocessed_files)}")
    print(f"Files likely Direct Play compatible: {len(compatible_files)}")
    print(f"Files likely need conversion (or transcode): {len(needs_conversion_files)}")
    print(f"Files that could not be processed: {len(unprocessed_files)}")

    if compatible_files:
        print("\n--- Details of Likely Direct Play Compatible Files ---")
        for path, reason in compatible_files:
            print(f"- {path} ({reason})")

    if needs_conversion_files:
        print("\n--- Details of Files Likely Needing Conversion/Transcoding ---")
        for path, reason in needs_conversion_files:
            print(f"- {path} ({reason})")

    if unprocessed_files:
        print("\n--- Details of Unprocessed Files (Check ffprobe errors) ---")
        for path in unprocessed_files:
            print(f"- {path}")

    # You can add logic here for conversion later, perhaps asking the user
    # which files to convert or providing a separate function.
    print("\nNote: 'Likely Direct Play compatible' is an assumption based on common codecs and containers. Actual direct play depends on your Plex client.")

if __name__ == "__main__":
    main()
