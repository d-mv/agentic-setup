#!/usr/bin/env python3
"""
HLS / TS Segment Downloader and Joiner.
Downloads video segments listed in an m3u8 playlist or list file concurrently with retries,
then concatenates them in exact playlist order into a single MPEG-TS file (and optionally remuxes to MP4).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Download HLS/TS segments listed in a file or playlist and concatenate them in order."
    )
    parser.add_argument(
        "--list", "-l",
        required=True,
        help="Path to playlist or file containing segment names/URLs (e.g., list.txt, playlist.m3u8)."
    )
    parser.add_argument(
        "--base-url", "-b",
        default="",
        help="Base URL prepended to relative segment names. If segment names are full URLs, this can be omitted."
    )
    parser.add_argument(
        "--output", "-o",
        default="output.ts",
        help="Target output file path (default: output.ts)."
    )
    parser.add_argument(
        "--segments-dir", "-d",
        default="segments",
        help="Directory to save downloaded segments (default: ./segments)."
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=16,
        help="Number of concurrent download workers (default: 16)."
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=5,
        help="Number of retries per segment (default: 5)."
    )
    parser.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        help="HTTP User-Agent header to use for requests."
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Custom HTTP headers in 'Key: Value' format. Can be specified multiple times."
    )
    parser.add_argument(
        "--mp4",
        action="store_true",
        help="Remux output to MP4 format using ffmpeg without re-encoding (-c copy)."
    )
    parser.add_argument(
        "--clean-segments",
        action="store_true",
        help="Remove downloaded segment files after successful joining."
    )
    return parser.parse_args()

def parse_playlist(list_file):
    segments = []
    with open(list_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            segments.append(line)
    return segments

def safe_filename_from_url(url_or_name, index):
    path = urllib.parse.urlsplit(url_or_name).path
    filename = os.path.basename(path)
    if not filename:
        return f"seg_{index:05d}.ts"
    filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    return filename

def build_segment_url(item, base_url):
    if item.startswith("http://") or item.startswith("https://"):
        return item
    if base_url:
        if not base_url.endswith("/"):
            base_url += "/"
        return urllib.parse.urljoin(base_url, item)
    return item

def download_segment(seg_url, local_path, headers, max_retries):
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return True, "cached"

    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(seg_url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    data = resp.read()
                    if len(data) > 0:
                        temp_path = local_path + ".tmp"
                        with open(temp_path, "wb") as f:
                            f.write(data)
                        os.replace(temp_path, local_path)
                        return True, f"downloaded ({len(data)} bytes)"
                    else:
                        raise ValueError("Received 0 bytes")
        except Exception as e:
            if attempt == max_retries:
                return False, f"Failed after {max_retries} attempts: {e}"
            time.sleep(1.0 * attempt)

    return False, "unknown error"

def main():
    args = parse_args()

    if not os.path.exists(args.list):
        print(f"Error: List file '{args.list}' does not exist.", file=sys.stderr)
        sys.exit(1)

    items = parse_playlist(args.list)
    total_segments = len(items)
    if total_segments == 0:
        print(f"Error: No valid segments found in '{args.list}'.", file=sys.stderr)
        sys.exit(1)

    # Validate relative paths have a base-url
    first_item = items[0]
    if not (first_item.startswith("http://") or first_item.startswith("https://")) and not args.base_url:
        print(f"Error: Segments in '{args.list}' are relative paths, but --base-url was not specified.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {total_segments} segments in '{args.list}'.")

    os.makedirs(args.segments_dir, exist_ok=True)

    headers = {"User-Agent": args.user_agent}
    for header in args.header:
        if ":" in header:
            k, v = header.split(":", 1)
            headers[k.strip()] = v.strip()

    # Prepare download queue mapping index -> (url, local_path)
    tasks = []
    seen_names = set()
    for idx, item in enumerate(items, 1):
        url = build_segment_url(item, args.base_url)
        local_name = safe_filename_from_url(item, idx)
        if local_name in seen_names:
            local_name = f"{idx:05d}_{local_name}"
        seen_names.add(local_name)

        local_path = os.path.join(args.segments_dir, local_name)
        tasks.append((idx, url, local_path))

    print(f"Downloading segments using {args.workers} concurrent workers...")
    completed = 0
    failed = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_task = {
            executor.submit(download_segment, url, path, headers, args.retries): (idx, url, path)
            for idx, url, path in tasks
        }

        for future in as_completed(future_to_task):
            idx, url, path = future_to_task[future]
            success, msg = future.result()
            completed += 1

            if not success:
                failed.append((idx, url, msg))
                print(f"\n[FAIL] Segment {idx} ({url}): {msg}", file=sys.stderr)

            if completed % 25 == 0 or completed == total_segments:
                elapsed = time.time() - start_time
                percent = completed * 100 // total_segments
                rate = completed / max(elapsed, 0.1)
                print(f"\rProgress: {completed}/{total_segments} ({percent}%) | {rate:.1f} seg/s | Elapsed: {elapsed:.1f}s", end="", flush=True)

    print()

    if failed:
        print(f"\nError: {len(failed)} segments failed to download:", file=sys.stderr)
        for idx, url, err in failed[:10]:
            print(f"  #{idx} {url}: {err}", file=sys.stderr)
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more.", file=sys.stderr)
        sys.exit(1)

    print(f"All {total_segments} segments ready.")
    print(f"Joining segments into '{args.output}'...")

    total_bytes = 0
    with open(args.output, "wb") as outfile:
        for idx, url, path in tasks:
            with open(path, "rb") as infile:
                chunk = infile.read()
                outfile.write(chunk)
                total_bytes += len(chunk)

    mb_size = total_bytes / (1024 * 1024)
    print(f"Successfully joined segments into '{args.output}' ({mb_size:.2f} MB).")

    # Verify with ffprobe if available
    if shutil.which("ffprobe"):
        print("\nVerifying video stream with ffprobe...")
        try:
            res = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration,size,bit_rate",
                    "-of", "default=noprint_wrappers=1",
                    args.output
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print("Stream Metadata:")
            for line in res.stdout.strip().splitlines():
                print(f"  {line}")
        except Exception as e:
            print(f"Warning: ffprobe verification encountered an issue: {e}", file=sys.stderr)

    # Convert to MP4 if requested
    if args.mp4:
        mp4_output = os.path.splitext(args.output)[0] + ".mp4"
        if shutil.which("ffmpeg"):
            print(f"\nRemuxing to MP4: '{mp4_output}'...")
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", args.output, "-c", "copy", mp4_output],
                    check=True,
                    capture_output=True
                )
                print(f"Successfully created MP4: '{mp4_output}'")
            except subprocess.CalledProcessError as e:
                print(f"Error remuxing with ffmpeg: {e.stderr.decode(errors='ignore')}", file=sys.stderr)
        else:
            print("\nWarning: ffmpeg is not installed; skipping MP4 remuxing.", file=sys.stderr)

    if args.clean_segments:
        print(f"\nCleaning up segment directory '{args.segments_dir}'...")
        shutil.rmtree(args.segments_dir, ignore_errors=True)
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
