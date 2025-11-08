#!/usr/bin/env python3
"""
Download audio files from URLs or copy local files.

Usage:
    poetry run python scripts/download.py [--config settings.yaml] [--force]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from scripts.core import downloader, utils


def main():
    parser = argparse.ArgumentParser(description="Download audio files")
    parser.add_argument("--config", default="./settings.yaml", help="Path to configuration file")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files")
    args = parser.parse_args()

    # Load configuration
    cfg = utils.load_config(args.config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("DOWNLOAD: Downloading/copying audio files")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' script first")
        sys.exit(1)

    df = pd.read_parquet(manifest_path)
    logger.info(f"Loaded manifest with {len(df)} tracks")

    # Initialize downloader
    dl = downloader.create_downloader(cfg)

    # Process tracks
    for idx, row in df.iterrows():
        if not row['resolved']:
            logger.debug(f"Skipping unresolved track: {row['raw_line'][:80]}")
            continue

        # Skip if already downloaded (unless force)
        if row['audio_path'] and Path(row['audio_path']).exists() and not args.force:
            logger.debug(f"Already downloaded: {row['audio_path']}")
            continue

        logger.info(f"[{idx + 1}/{len(df)}] Processing: {row['artist']} - {row['title']}")

        audio_path = None

        # Download from URL
        if row['download_url']:
            audio_path = dl.download_and_convert(
                url=row['download_url'],
                artist=row['artist'],
                title=row['title'],
                source_id=row['ytmusic_video_id'],
            )

        # Copy local file
        elif row['local_path']:
            audio_path = dl.copy_local_file(
                local_path=row['local_path'],
                artist=row['artist'],
                title=row['title'],
            )

        # Update manifest
        if audio_path:
            df.at[idx, 'audio_path'] = audio_path
        else:
            logger.warning(f"Failed to download/copy: {row['raw_line'][:80]}")

    # Save updated manifest
    df.to_parquet(manifest_path, index=False)
    logger.info(f"Updated manifest: {manifest_path}")

    downloaded_count = df['audio_path'].notna().sum()
    logger.info(f"Downloaded/copied {downloaded_count}/{len(df)} tracks")
    logger.info("DOWNLOAD complete")


if __name__ == "__main__":
    main()
