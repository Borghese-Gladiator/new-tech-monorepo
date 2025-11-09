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
INPUT_FILE = PROJECT_ROOT / "data" / "playlist_cleaned.txt"
OUTPUT_FILE = PROJECT_ROOT / "data" / "ytmusic_ids.txt"
FAILED_FILE = PROJECT_ROOT / "data" / "ytmusic_failed.txt"
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
        logger.error("Run the preprocessing scripts first to generate playlist_cleaned.txt")
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

    # Process tracks
    results = []
    failed = []
    skipped = 0

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue

        # Parse track
        original, artist, title = parse_track_line(line)

        if not artist or not title:
            skipped += 1
            continue

        # Progress logging
        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(lines)} tracks processed...")

        logger.info(f"[{i}/{len(lines)}] Searching: {artist} - {title}")

        # Search YouTube Music
        video_id = search_ytmusic(ytmusic, artist, title)

        if video_id:
            # Success
            results.append((original, video_id))
            logger.success(f"✓ Found ID: {video_id}")
        else:
            # Failed
            failed.append(original)
            logger.warning(f"✗ Not found: {artist} - {title}")

    # Write results
    logger.info("=" * 80)
    logger.info("Writing results...")

    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        f.write("# YouTube Music IDs\n")
        f.write(f"# Generated: {len(results)} tracks found\n")
        f.write(f"# Failed: {len(failed)} tracks not found\n")
        f.write("#\n")

        for track, video_id in results:
            # Format: Artist - Title  # ID: VIDEO_ID
            f.write(f"{track}  # ID: {video_id}\n")

    logger.info(f"✓ Results written to: {OUTPUT_FILE}")

    # Write failed tracks
    if failed:
        with FAILED_FILE.open('w', encoding='utf-8') as f:
            f.write("# Tracks that could not be found on YouTube Music\n")
            f.write(f"# Total: {len(failed)}\n")
            f.write("#\n")

            for track in failed:
                f.write(f"{track}\n")

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
