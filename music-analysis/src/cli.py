"""
CLI for MP3 Playlist Analyzer & Normalizer.

Main entry point with subcommands: ingest, download, analyze, playlists, all.
"""
import random
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from loguru import logger

from . import downloader, features, md_parser, playlist_spotify, playlist_ytmusic, search_match
from . import utils, visualize

app = typer.Typer(
    name="mp3-analyzer",
    help="MP3 Playlist Analyzer & Normalizer with audio feature extraction",
)


@app.command()
def ingest(
    config: str = typer.Option("./settings.yaml", help="Path to configuration file"),
    force: bool = typer.Option(False, help="Force re-processing of existing tracks"),
) -> None:
    """
    Parse markdown and search/match tracks on Spotify and YouTube Music.
    """
    # Load configuration
    cfg = utils.load_config(config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("INGEST: Parsing markdown and searching for tracks")
    logger.info("=" * 60)

    # Parse markdown
    input_md = cfg.get('input_markdown', './data/playlist.md')
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

        # Search for track
        download_url, spotify_id, ytmusic_video_id, source = matcher.search_track(track)

        # Determine if resolved
        resolved = bool(download_url or spotify_id or ytmusic_video_id)

        if not resolved:
            reason = "No matches found"
            logger.warning(f"Failed to resolve: {track.raw_line[:80]}")
            failed_lines.append(track.raw_line)
        else:
            reason = None
            logger.info(f"Resolved via {source}")

        # Build manifest entry
        entry = {
            'raw_line': track.raw_line,
            'artist': track.artist,
            'title': track.title,
            'album': track.album,
            'url': track.url,
            'local_path': track.local_path,
            'source': source,
            'spotify_id': spotify_id,
            'ytmusic_video_id': ytmusic_video_id,
            'download_url': download_url,
            'resolved': resolved,
            'reason': reason,
            'audio_path': None,
        }
        manifest_data.append(entry)

    # Save manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    utils.ensure_dir(Path(manifest_path).parent)

    df = pd.DataFrame(manifest_data)
    df.to_parquet(manifest_path, index=False)
    logger.info(f"Saved manifest to {manifest_path}")

    # Write failed inputs
    if failed_lines:
        failed_log = cfg.get('failed_log', './outputs/failed_inputs.txt')
        utils.write_failed_inputs(failed_lines, failed_log)
        logger.warning(f"Failed to resolve {len(failed_lines)}/{len(tracks)} tracks")
    else:
        logger.info("All tracks resolved successfully!")

    logger.info("INGEST complete")


@app.command()
def download(
    config: str = typer.Option("./settings.yaml", help="Path to configuration file"),
    force: bool = typer.Option(False, help="Force re-download of existing files"),
) -> None:
    """
    Download audio files from URLs or copy local files.
    """
    # Load configuration
    cfg = utils.load_config(config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("DOWNLOAD: Downloading/copying audio files")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' command first")
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
        if row['audio_path'] and Path(row['audio_path']).exists() and not force:
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


@app.command()
def analyze(
    config: str = typer.Option("./settings.yaml", help="Path to configuration file"),
) -> None:
    """
    Extract audio features and generate visualizations.
    """
    # Load configuration
    cfg = utils.load_config(config)
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("ANALYZE: Extracting features and generating visualizations")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' and 'download' commands first")
        sys.exit(1)

    df = pd.read_parquet(manifest_path)
    logger.info(f"Loaded manifest with {len(df)} tracks")

    # Filter tracks with audio files
    audio_tracks = df[df['audio_path'].notna()].copy()

    if audio_tracks.empty:
        logger.error("No audio files found in manifest")
        logger.error("Run 'download' command first")
        sys.exit(1)

    logger.info(f"Found {len(audio_tracks)} tracks with audio files")

    # Extract features
    audio_paths = audio_tracks['audio_path'].tolist()
    features_list = features.extract_features_batch(
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


@app.command()
def playlists(
    config: str = typer.Option("./settings.yaml", help="Path to configuration file"),
    clear: bool = typer.Option(False, help="Clear existing playlist before adding tracks"),
) -> None:
    """
    Create/update playlists on Spotify and YouTube Music.
    """
    # Load configuration
    cfg = utils.load_config(config)
    utils.load_env()
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("PLAYLISTS: Creating/updating playlists")
    logger.info("=" * 60)

    # Load manifest
    manifest_path = cfg.get('manifest_path', './data/track_manifest.parquet')
    if not Path(manifest_path).exists():
        logger.error(f"Manifest not found: {manifest_path}")
        logger.error("Run 'ingest' command first")
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
                clear_existing=clear,
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
                clear_existing=clear,
            )
            logger.info("YouTube Music playlist created successfully")
        except Exception as e:
            logger.error(f"Failed to create YouTube Music playlist: {e}")
    else:
        logger.warning("No YouTube Music video IDs found, skipping YouTube Music playlist")

    logger.info("PLAYLISTS complete")


@app.command()
def all(
    config: str = typer.Option("./settings.yaml", help="Path to configuration file"),
    force: bool = typer.Option(False, help="Force re-processing"),
    clear: bool = typer.Option(False, help="Clear existing playlists"),
) -> None:
    """
    Run all commands in sequence: ingest, download, analyze, playlists.
    """
    logger.info("=" * 60)
    logger.info("RUNNING FULL PIPELINE")
    logger.info("=" * 60)

    # Run all steps
    ingest(config=config, force=force)
    download(config=config, force=force)
    analyze(config=config)
    playlists(config=config, clear=clear)

    logger.info("=" * 60)
    logger.info("FULL PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    app()
