#!/usr/bin/env python3
"""
Search for YouTube Music IDs for tracks in playlist.

Reads from: data/playlist_cleaned.txt
Writes to: data/ytmusic_ids.txt

Output format: Artist - Title  # ID: VIDEO_ID

Usage:
    poetry run python scripts/02_create/A_get_ids_for_ytmusic.py
"""
import os
import sys
from pathlib import Path

from loguru import logger
from ytmusicapi import YTMusic

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)
logger.add(
    "logs/ytmusic_search.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    rotation="10 MB",
)

# Hard-coded paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "01_B_cleaned_playlist.md"
OUTPUT_FILE = PROJECT_ROOT / "data" / "02_A_ytmusic_track_ids.txt"
FAILED_FILE = PROJECT_ROOT / "data" / "02_A_ytmusic_failed_tracks.txt"
# YTMusic browser headers file - generate with: ytmusicapi browser
BROWSER_FILE = PROJECT_ROOT / "browser.json"


def parse_track_line(line: str) -> tuple[str, str, str]:
    """
    Parse a track line into artist and title.

    Args:
        line: Track line in format "Artist - Title"

    Returns:
        Tuple of (original_line, artist, title)
    """
    line = line.strip()

    # Remove leading bullet points and numbering
    line = line.lstrip('-*•').strip()
    line = line.lstrip('0123456789.').strip()

    # Remove year headers
    if line.startswith('#'):
        return None, None, None

    # Parse artist - title format
    if ' - ' not in line:
        logger.warning(f"Skipping malformed line (no ' - ' separator): {line[:60]}")
        return None, None, None

    parts = line.split(' - ', 1)
    if len(parts) != 2:
        logger.warning(f"Skipping malformed line: {line[:60]}")
        return None, None, None

    artist = parts[0].strip()
    title = parts[1].strip()

    if not artist or not title:
        logger.warning(f"Skipping line with empty artist or title: {line[:60]}")
        return None, None, None

    return line, artist, title


def search_ytmusic(ytmusic: YTMusic, artist: str, title: str) -> str | None:
    """
    Search YouTube Music for a track.

    Args:
        ytmusic: YTMusic client
        artist: Artist name
        title: Track title

    Returns:
        Video ID if found, None otherwise
    """
    # Build search query
    query = f"{artist} {title}"

    try:
        # Search YouTube Music
        results = ytmusic.search(query, filter="songs", limit=5)

        if not results:
            logger.debug(f"No results for: {query}")
            return None

        # Use first result (best match)
        top_result = results[0]
        video_id = top_result.get('videoId')

        if video_id:
            result_artist = top_result.get('artists', [{}])[0].get('name', 'Unknown') if top_result.get('artists') else 'Unknown'
            result_title = top_result.get('title', 'Unknown')
            logger.debug(f"Found: {result_artist} - {result_title} → {video_id}")
            return video_id
        else:
            logger.debug(f"No video ID in result for: {query}")
            return None

    except Exception as e:
        logger.error(f"Search error for '{query}': {e}")
        return None


def main():
    logger.info("=" * 80)
    logger.info("YouTube Music ID Search")
    logger.info("=" * 80)

    # Validate input file
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.error("Run the preprocessing scripts first to generate 01_B_cleaned_playlist.md")
        sys.exit(1)

    logger.info(f"Input file: {INPUT_FILE}")
    logger.info(f"Output file: {OUTPUT_FILE}")

    # Initialize YouTube Music client
    if not BROWSER_FILE.exists():
        logger.error(f"YouTube Music browser headers file not found: {BROWSER_FILE}")
        logger.error("")
        logger.error("To set up authentication:")
        logger.error("  1. Open YouTube Music in Chrome: https://music.youtube.com")
        logger.error("  2. Open DevTools (F12) → Network tab")
        logger.error("  3. Filter by 'browse' and click any request")
        logger.error("  4. Right-click → Copy → Copy as cURL")
        logger.error("  5. Run: ytmusicapi browser")
        logger.error("  6. Paste the cURL command when prompted")
        logger.error("  7. This creates browser.json in your directory")
        logger.error("")
        sys.exit(1)

    try:
        ytmusic = YTMusic(str(BROWSER_FILE))
        logger.info("✓ YouTube Music client initialized with browser headers")
    except Exception as e:
        logger.error(f"Failed to initialize YouTube Music client: {e}")
        logger.error("Your browser.json may be invalid or expired")
        logger.error("Try regenerating: ytmusicapi browser")
        sys.exit(1)

    # Read input file
    logger.info(f"Reading tracks from: {INPUT_FILE}")
    with INPUT_FILE.open('r', encoding='utf-8') as f:
        lines = f.readlines()

    logger.info(f"Total lines read: {len(lines)}")

    # Load existing results to skip (for resume capability)
    existing_tracks = set()
    if OUTPUT_FILE.exists():
        logger.info(f"Found existing results file. Loading to resume...")
        with OUTPUT_FILE.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('#') and '# ID:' in line:
                    # Extract track name (everything before # ID:)
                    track = line.split('# ID:')[0].strip()
                    existing_tracks.add(track)
        logger.info(f"Loaded {len(existing_tracks)} existing results. Will skip these.")

    # Load existing failed tracks
    existing_failed = set()
    if FAILED_FILE.exists():
        with FAILED_FILE.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.startswith('#'):
                    existing_failed.add(line.strip())

    # Process tracks
    results = []
    failed = []
    skipped = 0

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    FAILED_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Initialize or append to output files
    file_mode = 'a' if OUTPUT_FILE.exists() else 'w'
    if file_mode == 'w':
        with OUTPUT_FILE.open('w', encoding='utf-8') as f:
            f.write("# YouTube Music IDs\n")
            f.write("# Results are written incrementally as tracks are found\n")
            f.write("#\n")

    file_mode = 'a' if FAILED_FILE.exists() else 'w'
    if file_mode == 'w':
        with FAILED_FILE.open('w', encoding='utf-8') as f:
            f.write("# Tracks that could not be found on YouTube Music\n")
            f.write("#\n")

    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue

        # Parse track
        original, artist, title = parse_track_line(line)

        if not artist or not title:
            skipped += 1
            continue

        # Skip if already processed
        if original in existing_tracks:
            logger.debug(f"[{i}/{len(lines)}] Skipping (already found): {artist} - {title}")
            results.append((original, None))  # Count it but don't search
            continue

        if original in existing_failed:
            logger.debug(f"[{i}/{len(lines)}] Skipping (previously failed): {artist} - {title}")
            failed.append(original)  # Count it but don't search
            continue

        # Progress logging
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(lines)} tracks processed...")

        logger.info(f"[{i}/{len(lines)}] Searching: {artist} - {title}")

        # Search YouTube Music
        video_id = search_ytmusic(ytmusic, artist, title)

        if video_id:
            # Success - write immediately
            results.append((original, video_id))
            with OUTPUT_FILE.open('a', encoding='utf-8') as f:
                f.write(f"{original}  # ID: {video_id}\n")
            logger.success(f"✓ Found ID: {video_id}")
        else:
            # Failed - write immediately
            failed.append(original)
            with FAILED_FILE.open('a', encoding='utf-8') as f:
                f.write(f"{original}\n")
            logger.warning(f"✗ Not found: {artist} - {title}")

    # Update headers with final counts
    logger.info("=" * 80)
    logger.info("Updating final statistics...")

    # Read existing results
    with OUTPUT_FILE.open('r', encoding='utf-8') as f:
        content = f.readlines()

    # Update header with final count
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        f.write("# YouTube Music IDs\n")
        f.write(f"# Generated: {len(results)} tracks found\n")
        f.write(f"# Failed: {len(failed)} tracks not found\n")
        f.write("#\n")
        # Write all results (skip old header)
        for line in content:
            if not line.startswith('#'):
                f.write(line)

    logger.info(f"✓ Results written to: {OUTPUT_FILE}")

    # Update failed file header
    if failed:
        with FAILED_FILE.open('r', encoding='utf-8') as f:
            content = f.readlines()

        with FAILED_FILE.open('w', encoding='utf-8') as f:
            f.write("# Tracks that could not be found on YouTube Music\n")
            f.write(f"# Total: {len(failed)}\n")
            f.write("#\n")
            # Write all failed (skip old header)
            for line in content:
                if not line.startswith('#'):
                    f.write(line)

        logger.warning(f"✗ Failed tracks written to: {FAILED_FILE}")

    # Summary
    logger.info("=" * 80)
    logger.info("Summary:")
    logger.info(f"  Total lines: {len(lines)}")
    logger.info(f"  Skipped: {skipped} (malformed/empty)")
    logger.info(f"  Processed: {len(results) + len(failed)}")
    logger.info(f"  ✓ Found: {len(results)} ({len(results)/(len(results)+len(failed))*100:.1f}%)")
    logger.info(f"  ✗ Not found: {len(failed)} ({len(failed)/(len(results)+len(failed))*100:.1f}%)")
    logger.info("=" * 80)

    if failed:
        logger.warning(f"Review failed tracks in: {FAILED_FILE}")


if __name__ == "__main__":
    main()
