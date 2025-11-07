#!/usr/bin/env python3
"""
Run all scripts in sequence: ingest, download, analyze, playlists.

Usage:
    poetry run python scripts/run_all.py [--config settings.yaml] [--force] [--clear]
"""
import argparse
import subprocess
import sys
from pathlib import Path

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import utils


def main():
    parser = argparse.ArgumentParser(description="Run full pipeline")
    parser.add_argument("--config", default="./settings.yaml", help="Path to configuration file")
    parser.add_argument("--force", action="store_true", help="Force re-processing")
    parser.add_argument("--clear", action="store_true", help="Clear existing playlists")
    args = parser.parse_args()

    # Load config for logging setup
    cfg = utils.load_config(args.config)
    utils.setup_logging(cfg.get('run_log', './outputs/run.log'))

    logger.info("=" * 60)
    logger.info("RUNNING FULL PIPELINE")
    logger.info("=" * 60)

    scripts_dir = Path(__file__).parent
    config_arg = f"--config={args.config}"

    # Run ingest
    logger.info("\n" + "=" * 60)
    logger.info("Step 1/4: INGEST")
    logger.info("=" * 60)
    cmd = ["python", str(scripts_dir / "ingest.py"), config_arg]
    if args.force:
        cmd.append("--force")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Ingest failed")
        sys.exit(1)

    # Run download
    logger.info("\n" + "=" * 60)
    logger.info("Step 2/4: DOWNLOAD")
    logger.info("=" * 60)
    cmd = ["python", str(scripts_dir / "download.py"), config_arg]
    if args.force:
        cmd.append("--force")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Download failed")
        sys.exit(1)

    # Run analyze
    logger.info("\n" + "=" * 60)
    logger.info("Step 3/4: ANALYZE")
    logger.info("=" * 60)
    cmd = ["python", str(scripts_dir / "analyze.py"), config_arg]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Analyze failed")
        sys.exit(1)

    # Run playlists
    logger.info("\n" + "=" * 60)
    logger.info("Step 4/4: PLAYLISTS")
    logger.info("=" * 60)
    cmd = ["python", str(scripts_dir / "playlists.py"), config_arg]
    if args.clear:
        cmd.append("--clear")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Playlists failed")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("FULL PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
