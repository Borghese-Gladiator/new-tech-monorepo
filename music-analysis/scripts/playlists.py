#!/usr/bin/env python3
"""
Create/update playlists on Spotify and YouTube Music.

Usage:
    poetry run python scripts/playlists.py [--config settings.yaml] [--clear]
"""
import argparse
import random
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import playlist_spotify, playlist_ytmusic, utils


def main():
    parser = argparse.ArgumentParser(description="Create/update playlists")
    parser.add_argument("--config", default="./settings.yaml", help="Path to configuration file")
    parser.add_argument("--clear", action="store_true", help="Clear existing playlist before adding tracks")
    args = parser.parse_args()

    # Load configuration
    cfg = utils.load_config(args.config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("PLAYLISTS: Creating/updating playlists")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' script first")
        sys.exit(1)

    df = pd.read_parquet(manifest_path)
    logger.info(f"Loaded manifest with {len(df)} tracks")

    # Filter resolved tracks
    resolved_tracks = df[df['resolved']].copy()

    if resolved_tracks.empty:
        logger.error("No resolved tracks found")
        sys.exit(1)

    logger.info(f"Found {len(resolved_tracks)} resolved tracks")

    # Deduplicate
    deduplicated = utils.deduplicate_tracks(resolved_tracks.to_dict('records'))
    logger.info(f"After deduplication: {len(deduplicated)} unique tracks")

    # Randomize order
    random.shuffle(deduplicated)
    logger.info("Randomized track order")

    # Get playlist name with date
    base_name = cfg.get('target_playlist_name', 'Normalized Mix')
    playlist_name = utils.get_playlist_name_with_date(base_name)
    description = f"Auto-generated on {utils.datetime.now().strftime('%Y-%m-%d')} from Markdown source"

    # Create Spotify playlist
    spotify_ids = [t['spotify_id'] for t in deduplicated if t.get('spotify_id')]
    if spotify_ids:
        logger.info(f"Creating Spotify playlist with {len(spotify_ids)} tracks")
        try:
            spotify_mgr = playlist_spotify.create_spotify_manager()
            spotify_mgr.create_and_populate_playlist(
                playlist_name,
                spotify_ids,
                description=description,
                clear_existing=args.clear,
            )
            logger.info("Spotify playlist created successfully")
        except Exception as e:
            logger.error(f"Failed to create Spotify playlist: {e}")
    else:
        logger.warning("No Spotify track IDs found, skipping Spotify playlist")

    # Create YouTube Music playlist
    ytmusic_video_ids = [t['ytmusic_video_id'] for t in deduplicated if t.get('ytmusic_video_id')]
    if ytmusic_video_ids:
        logger.info(f"Creating YouTube Music playlist with {len(ytmusic_video_ids)} tracks")
        try:
            ytmusic_mgr = playlist_ytmusic.create_ytmusic_manager()
            ytmusic_mgr.create_and_populate_playlist(
                playlist_name,
                ytmusic_video_ids,
                description=description,
                clear_existing=args.clear,
            )
            logger.info("YouTube Music playlist created successfully")
        except Exception as e:
            logger.error(f"Failed to create YouTube Music playlist: {e}")
    else:
        logger.warning("No YouTube Music video IDs found, skipping YouTube Music playlist")

    logger.info("PLAYLISTS complete")


if __name__ == "__main__":
    main()
