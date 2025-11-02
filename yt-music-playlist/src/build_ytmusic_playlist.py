#!/usr/bin/env python3
"""
Create/update a YouTube Music playlist from songs.txt with retries and logging.
First run opens a browser and creates oauth.json.
"""

from pathlib import Path
from typing import List
import time

from ytmusicapi import YTMusic

from helpers import (
    setup_logger, parse_line, extract_video_id,
    backoff_retry, ytm_search_best_video_id, ytm_add_items
)

INPUT_FILE = "songs.txt"
PLAYLIST_NAME = "My Cross-Platform Picks (YouTube Music)"
PRIVACY = "PRIVATE"  # PRIVATE | PUBLIC | UNLISTED

def ensure_playlist(yt: YTMusic, name: str, privacy: str, logger):
    def _list_playlists():
        return yt.get_library_playlists(limit=100)
    playlists = backoff_retry(_list_playlists, logger=logger, op_name="ytm.get_library_playlists")

    for pl in playlists:
        if pl.get("title") == name:
            return pl["playlistId"]

    def _create():
        return yt.create_playlist(name=name, description="Auto-created by script", privacy_status=privacy)
    return backoff_retry(_create, logger=logger, op_name="ytm.create_playlist")

def main():
    logger = setup_logger("ytmusic", "ytmusic_playlist.log")

    p = Path(INPUT_FILE)
    if not p.exists():
        logger.error(f"Missing {INPUT_FILE}")
        raise SystemExit(f"Missing {INPUT_FILE}")

    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    parsed = [parse_line(ln) for ln in lines]
    logger.info(f"Loaded {len(parsed)} lines from {INPUT_FILE}")

    token_file = "oauth.json"
    if not Path(token_file).exists():
        logger.info("Starting YouTube Music OAuth flow...")
        YTMusic.setup_oauth(token_file)
        logger.info("OAuth token saved to oauth.json")
    yt = YTMusic(token_file)

    playlist_id = ensure_playlist(yt, PLAYLIST_NAME, PRIVACY, logger)
    logger.info(f"YouTube Music playlist ready: {PLAYLIST_NAME} ({playlist_id})")

    to_add: List[str] = []
    not_found = 0
    for query, url in parsed:
        vid = extract_video_id(url)
        if vid:
            logger.info(f"Using provided URL for: {query} -> {vid}")
        else:
            try:
                vid = backoff_retry(ytm_search_best_video_id, yt, query, logger=logger, op_name="ytm.search_best")
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                vid = None

        if vid:
            to_add.append(vid)
            logger.info(f"Queued: {query} -> {vid}")
        else:
            not_found += 1
            logger.warning(f"Not found: {query}")

        time.sleep(0.05)

    if to_add:
        ytm_add_items(yt, playlist_id, to_add, logger=logger)
        logger.info(f"Added {len(to_add)} items to YT Music")

    logger.info(f"Summary: total={len(parsed)}, added={len(to_add)}, not_found={not_found}")
    print("Done.")

if __name__ == "__main__":
    main()
