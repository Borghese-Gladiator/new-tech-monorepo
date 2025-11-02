#!/usr/bin/env python3
"""
Create or update a Spotify playlist from songs.txt.

Requires env vars:
- SPOTIPY_CLIENT_ID
- SPOTIPY_CLIENT_SECRET
- SPOTIPY_REDIRECT_URI   (e.g., http://localhost:8080/callback)

On first run, this opens a browser for approval and writes .cache

```
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_CLIENT_SECRET="your_client_secret"
export SPOTIPY_REDIRECT_URI="http://localhost:8080/callback"
```
"""

from pathlib import Path
from typing import List, Optional
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from helpers import (
    setup_logger, parse_line, backoff_retry,
    spotify_search_best_uri, spotify_add_items
)

INPUT_FILE = "songs.txt"
PLAYLIST_NAME = "My Cross-Platform Picks (Spotify)"
SPOTIFY_SCOPES = "playlist-modify-private playlist-modify-public ugc-image-upload"

def get_spotify_client(logger):
    def _auth():
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            scope=SPOTIFY_SCOPES,
            cache_path=".cache",
            open_browser=True,
            show_dialog=False,
        ))
    return backoff_retry(_auth, logger=logger, op_name="spotify.auth")

def ensure_playlist(sp: spotipy.Spotify, name: str, logger) -> str:
    playlists = backoff_retry(sp.current_user_playlists, limit=50, logger=logger, op_name="spotify.current_user_playlists")

    for pl in playlists["items"]:
        if pl["name"] == name:
            return pl["id"]

    def _create():
        me = sp.current_user()
        return sp.user_playlist_create(
            user=me["id"],
            name=name,
            public=False,  # set True if you want public by default
            description="Auto-created by script",
        )
    created = backoff_retry(_create, logger=logger, op_name="spotify.user_playlist_create")
    return created["id"]

def main():
    logger = setup_logger("spotify", "spotify_playlist.log")

    p = Path(INPUT_FILE)
    if not p.exists():
        logger.error(f"Missing {INPUT_FILE}")
        raise SystemExit(f"Missing {INPUT_FILE}")

    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    parsed = [parse_line(ln) for ln in lines]
    logger.info(f"Loaded {len(parsed)} lines from {INPUT_FILE}")

    sp = get_spotify_client(logger)
    playlist_id = ensure_playlist(sp, PLAYLIST_NAME, logger)
    logger.info(f"Spotify playlist ready: {PLAYLIST_NAME} ({playlist_id})")

    uris: List[str] = []
    not_found = 0
    for query, _ in parsed:
        try:
            uri: Optional[str] = backoff_retry(spotify_search_best_uri, sp, query, logger=logger, op_name="spotify.search_best")
        except Exception as e:
            logger.error(f"Search failed for '{query}': {e}")
            uri = None

        if uri:
            uris.append(uri)
            logger.info(f"Queued: {query} -> {uri}")
        else:
            not_found += 1
            logger.warning(f"Not found: {query}")

        time.sleep(0.05)

    if uris:
        spotify_add_items(sp, playlist_id, uris, logger=logger)
        logger.info(f"Added {len(uris)} tracks to Spotify")

    logger.info(f"Summary: total={len(parsed)}, added={len(uris)}, not_found={not_found}")
    print("Done.")

if __name__ == "__main__":
    main()
