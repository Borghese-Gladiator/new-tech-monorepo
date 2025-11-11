#!/usr/bin/env python3
"""
Download audio from YouTube Music using video IDs.

Reads video IDs from: data/02_A_ytmusic_track_ids.csv
Downloads to: data/03_downloaded_audio/

Usage:
    poetry run python scripts/03_download/download_audio_yt.py [--max N] [--force]
"""
import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO",
)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "02_A_ytmusic_track_ids.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "03_downloaded_audio"


def check_dependencies():
    """Check if yt-dlp and ffmpeg are installed."""
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        logger.info(f"✓ yt-dlp version: {result.stdout.decode().strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("✗ yt-dlp not found")
        logger.error("  Install with: poetry install")
        sys.exit(1)

    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        version_line = result.stdout.decode().split('\n')[0]
        logger.info(f"✓ ffmpeg installed: {version_line}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("✗ ffmpeg not found")
        logger.error("  Install with: brew install ffmpeg")
        sys.exit(1)


def parse_track_ids(input_file: Path):
    """Parse track IDs from the CSV file."""
    tracks = []

    with input_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tracks.append({
                'name': row['track_name'],
                'video_id': row['video_id'],
            })

    return tracks


def download_track(video_id: str, track_name: str, output_dir: Path, browser: str = "chrome", force: bool = False) -> bool:
    """
    Download a track from YouTube Music.

    Args:
        video_id: YouTube video ID
        track_name: Track name for logging
        output_dir: Directory to save the file
        browser: Browser to extract cookies from
        force: Force re-download even if file exists

    Returns:
        True if successful, False otherwise
    """
    # Construct YouTube URL (works for both YouTube and YouTube Music)
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Output template: "Artist - Title [VIDEO_ID].mp3"
    output_template = str(output_dir / f"%(artist)s - %(title)s [%(id)s].%(ext)s")

    # Check if already downloaded
    if not force:
        # Check for existing file with this video ID
        existing_files = list(output_dir.glob(f"*[{video_id}].mp3"))
        if existing_files:
            logger.debug(f"Already downloaded: {existing_files[0].name}")
            return True

    try:
        cmd = [
            'yt-dlp',
            '--cookies-from-browser', browser,  # Extract cookies from browser
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '320K',
            '--output', output_template,
            '--no-playlist',
            '--quiet',
            '--progress',
            url,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Download failed: {result.stderr}")
            return False

        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Download timeout for: {track_name}")
        return False
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download audio from YouTube Music")
    parser.add_argument("--max", type=int, help="Maximum number of tracks to download (for testing)")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files")
    parser.add_argument("--delay", type=float, default=3.0, help="Base delay in seconds for exponential backoff (default: 3.0)")
    parser.add_argument("--browser", default="chrome", help="Browser to extract cookies from (chrome, firefox, safari, edge) (default: chrome)")
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("YouTube Music Audio Downloader")
    logger.info("=" * 80)

    # Check dependencies
    check_dependencies()

    logger.info(f"Using cookies from browser: {args.browser}")
    logger.info("Note: You must be signed in to YouTube in this browser")

    # Validate input file
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        logger.error("Run the YouTube Music ID search script first:")
        logger.error("  poetry run python scripts/02_create/A_get_ids_for_ytmusic.py")
        sys.exit(1)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Parse track IDs
    tracks = parse_track_ids(INPUT_FILE)
    logger.info(f"Found {len(tracks)} tracks to download")

    if args.max:
        tracks = tracks[:args.max]
        logger.info(f"Limiting to first {args.max} tracks (--max flag)")

    if args.delay > 0:
        logger.info(f"Using exponential backoff with base delay: {args.delay}s")

    # Download tracks with exponential backoff
    success_count = 0
    failed_count = 0
    current_delay = args.delay
    consecutive_failures = 0
    max_delay = args.delay * 16  # Maximum delay is 16x base delay

    for i, track in enumerate(tracks, 1):
        logger.info(f"[{i}/{len(tracks)}] Downloading: {track['name']}")

        success = download_track(
            video_id=track['video_id'],
            track_name=track['name'],
            output_dir=OUTPUT_DIR,
            browser=args.browser,
            force=args.force,
        )

        if success:
            success_count += 1
            logger.success(f"✓ Downloaded: {track['name']}")
            consecutive_failures = 0
            # Gradually reduce delay back to base on success
            current_delay = max(args.delay, current_delay * 0.9)
        else:
            failed_count += 1
            logger.warning(f"✗ Failed: {track['name']}")
            consecutive_failures += 1
            # Exponentially increase delay on failure
            current_delay = min(max_delay, current_delay * 2)

        # Rate limiting: wait between downloads with exponential backoff
        if i < len(tracks) and args.delay > 0:
            if consecutive_failures > 0:
                logger.info(f"Waiting {current_delay:.1f}s before next download (backoff due to failures)...")
            else:
                logger.debug(f"Waiting {current_delay:.1f}s before next download...")
            time.sleep(current_delay)

    # Summary
    logger.info("=" * 80)
    logger.info("Summary:")
    logger.info(f"  Total: {len(tracks)}")
    logger.info(f"  ✓ Downloaded: {success_count}")
    logger.info(f"  ✗ Failed: {failed_count}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
