#!/usr/bin/env python3
"""
Extract audio features and generate visualizations.

Usage:
    poetry run python scripts/analyze.py [--config settings.yaml]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from scripts.core import audio_features, utils, visualize


def main():
    parser = argparse.ArgumentParser(description="Extract audio features and generate visualizations")
    parser.add_argument("--config", default="./settings.yaml", help="Path to configuration file")
    args = parser.parse_args()

    # Load configuration
    cfg = utils.load_config(args.config)
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("ANALYZE: Extracting features and generating visualizations")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' and 'download' scripts first")
        sys.exit(1)

    df = pd.read_parquet(manifest_path)
    logger.info(f"Loaded manifest with {len(df)} tracks")

    # Filter tracks with audio files
    audio_tracks = df[df['audio_path'].notna()].copy()

    if audio_tracks.empty:
        logger.error("No audio files found in manifest")
        logger.error("Run 'download' script first")
        sys.exit(1)

    logger.info(f"Found {len(audio_tracks)} tracks with audio files")

    # Extract features
    audio_paths = audio_tracks['audio_path'].tolist()
    features_list = audio_features.extract_features_batch(
        audio_paths,
        n_mfcc=cfg.get('n_mfcc', 13),
        spectral_rolloff_pct=cfg.get('spectral_rolloff_pct', 0.85),
        spectral_contrast_bands=cfg.get('spectral_contrast_bands', 7),
    )

    if not features_list:
        logger.error("No features extracted")
        sys.exit(1)

    # Create features DataFrame
    features_df = pd.DataFrame(features_list)

    # Merge with manifest metadata
    features_df = features_df.merge(
        audio_tracks[['audio_path', 'artist', 'title', 'album', 'source', 'spotify_id', 'ytmusic_video_id']],
        left_on='path',
        right_on='audio_path',
        how='left',
        suffixes=('', '_meta'),
    )

    # Save features CSV
    features_csv = cfg.get('features_csv', './outputs/audio_features.csv')
    utils.ensure_dir(Path(features_csv).parent)
    features_df.to_csv(features_csv, index=False)
    logger.info(f"Saved features to {features_csv}")

    # Generate visualizations
    fig_dir = cfg.get('fig_dir', './outputs/figures')
    visualize.generate_all_visualizations(
        features_df,
        output_dir=fig_dir,
        dpi=cfg.get('figure_dpi', 150),
        tempo_bins=cfg.get('tempo_bins', 30),
    )

    logger.info("ANALYZE complete")


if __name__ == "__main__":
    main()
