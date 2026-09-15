---
name: "hls-ts-downloader"
description: "Download video stream segments (*.ts) from an HLS playlist or segment list and join/concatenate them in order into a single playable video file (TS/MP4). Use when the user needs to download video segments from a URL or m3u8 playlist, stitch together TS fragments, or assemble chunked video streams."
---

# HLS / TS Segment Downloader & Joiner

Download chunked video stream segments (`*.ts`) referenced in an HLS playlist (`.m3u8`) or plain text segment list, download them concurrently with retry logic and caching, and concatenate them in exact sequence into a playable video file.

## Features

- **Concurrent Downloading**: Uses multi-threading (default 16 workers) with exponential backoff retries.
- **Resume & Caching**: Automatically skips already downloaded segments with non-zero size.
- **Order-Preserving Concatenation**: Segments are joined strictly according to their playlist order (binary concatenation for MPEG-TS).
- **Stream Verification**: Automatically validates duration and bitrate using `ffprobe` if installed.
- **Lossless MP4 Remuxing**: Optional remuxing to MP4 using `ffmpeg -c copy` without re-encoding quality loss.
- **Zero External Python Dependencies**: Built entirely with Python's standard library (`urllib`, `concurrent.futures`, `argparse`).

## Quick Start CLI

The skill provides an executable CLI script located at:
`~/.agents/skills/hls-ts-downloader/scripts/download_and_join.py`

### Basic Usage

When you have a list file (`list.txt` or `playlist.m3u8`) and a base URL:

```bash
python3 ~/.agents/skills/hls-ts-downloader/scripts/download_and_join.py \
  --list list.txt \
  --base-url "https://example.com/path/to/stream/" \
  --output video.ts
```

### Remuxing to MP4 with Cleanup

```bash
python3 ~/.agents/skills/hls-ts-downloader/scripts/download_and_join.py \
  --list list.txt \
  --base-url "https://example.com/path/to/stream/" \
  --output video.ts \
  --mp4 \
  --clean-segments
```

### Full Absolute URLs in Playlist

If `list.txt` or `playlist.m3u8` already contains absolute URLs (`http://...` or `https://...`), `--base-url` can be omitted:

```bash
python3 ~/.agents/skills/hls-ts-downloader/scripts/download_and_join.py \
  --list playlist.m3u8 \
  --output full_movie.ts
```

## Options Reference

| Option | Flag | Default | Description |
|---|---|---|---|
| `--list` | `-l` | *Required* | Path to playlist or list file (`list.txt`, `.m3u8`). |
| `--base-url` | `-b` | `""` | Base URL prepended to relative segment paths. |
| `--output` | `-o` | `output.ts` | Target output file path. |
| `--segments-dir` | `-d` | `segments` | Directory to store downloaded segment files. |
| `--workers` | `-w` | `16` | Number of concurrent download workers. |
| `--retries` | `-r` | `5` | Retry attempts per segment before failing. |
| `--header` | | `[]` | Custom HTTP headers (e.g. `--header "Referer: ..."`). |
| `--user-agent` | | Chrome UA | Custom HTTP User-Agent string. |
| `--mp4` | | `false` | Remux to MP4 using ffmpeg (`-c copy`) without re-encoding. |
| `--clean-segments` | | `false` | Remove the segment directory after successful join. |

## Workflow Steps

When executing this task for a user:

1. **Inspect the Playlist / List**:
   - Check if lines starting with `#` contain encryption tags (e.g. `#EXT-X-KEY`). If unencrypted, standard TS concatenation works natively.
   - Determine whether segment entries are relative paths (`seg-1.ts`) or full URLs.
2. **Download & Concatenate**:
   - Run `download_and_join.py` with appropriate `--workers` (12–24) and base URL.
   - For long downloads, run in the background and update the user with progress.
3. **Verify Stream Integrity**:
   - Inspect the resulting file using `ffprobe`:
     ```bash
     ffprobe -v error -show_entries format=duration,size,bit_rate -of default=noprint_wrappers=1 output.ts
     ```
4. **Report Results**:
   - Provide the user with the output file path, duration, file size, and codec information.
