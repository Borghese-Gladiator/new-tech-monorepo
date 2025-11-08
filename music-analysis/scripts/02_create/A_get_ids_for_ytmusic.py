#!/usr/bin/env python3
"""
Parse markdown and search/match tracks on YouTube Music.

Usage:
    poetry run python scripts/02_create/A_get_ids_for_ytmusic.py [--config settings.yaml] [--force]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from scripts.core import md_parser, search_match, utils


def main():
    parser = argparse.ArgumentParser(description="Parse markdown and search for tracks on YouTube Music")
    parser.add_argument("--config", default="./settings.yaml", help="Path to configuration file")
    parser.add_argument("--force", action="store_true", help="Force re-processing of existing tracks")
    args = parser.parse_args()

    # Load configuration
    cfg = utils.load_config(args.config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("GET IDs: Searching for YouTube Music video IDs")
    logger.info("=" * 60)

    # Parse markdown
    input_md = cfg.get('input_markdown', './data/playlist_clean.txt')
    max_items = cfg.get('max_items')

    logger.info(f"Parsing markdown: {input_md}")
    tracks = md_parser.parse_markdown_file(input_md, max_items=max_items)

    if not tracks:
        logger.error("No tracks found in markdown file")
        sys.exit(1)

    logger.info(f"Parsed {len(tracks)} tracks")

    # Initialize search matcher
    matcher = search_match.create_search_matcher(cfg)

    # Search and match tracks
    manifest_data = []
    failed_lines = []

    for i, track in enumerate(tracks, 1):
        logger.info(f"[{i}/{len(tracks)}] Processing: {track.raw_line[:80]}")

        # Search for track on YouTube Music
        download_url, spotify_id, ytmusic_video_id, source = matcher.search_track(track)

        # Determine if resolved
        resolved = bool(ytmusic_video_id)

        if not resolved:
            reason = "No YouTube Music matches found"
            logger.warning(f"Failed to resolve: {track.raw_line[:80]}")
            failed_lines.append(track.raw_line)
        else:
            reason = None
            logger.info(f"Resolved via {source}: {ytmusic_video_id}")

        # Build manifest entry
        entry = {
            'raw_line': track.raw_line,
            'artist': track.artist,
            'title': track.title,
            'ytmusic_video_id': ytmusic_video_id,
            'download_url': download_url,
            'source': source,
            'resolved': resolved,
            'reason': reason,
        }
        manifest_data.append(entry)

    # Save manifest
    manifest_path = cfg.get('ytmusic_manifest_path', './data/ytmusic_track_manifest.parquet')
    utils.ensure_dir(Path(manifest_path).parent)

    df = pd.DataFrame(manifest_data)
    df.to_parquet(manifest_path, index=False)
    logger.info(f"Saved manifest to {manifest_path}")

    # Write failed inputs
    if failed_lines:
        failed_log = cfg.get('ytmusic_failed_log', './outputs/ytmusic_failed_inputs.txt')
        utils.write_failed_inputs(failed_lines, failed_log)
        logger.warning(f"Failed to resolve {len(failed_lines)}/{len(tracks)} tracks")
    else:
        logger.info("All tracks resolved successfully!")

    logger.info(f"YouTube Music GET IDs complete: {len(manifest_data) - len(failed_lines)}/{len(manifest_data)} resolved")


if __name__ == "__main__":
    main()
