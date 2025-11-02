#!/usr/bin/env python3
"""
Download audio for each song in songs.txt using yt-dlp, with retries + logging.
- Uses provided YouTube/YouTube Music URL if present ('=> https://...').
- Otherwise searches YouTube Music and downloads the best match.

Outputs:
- ./downloads/<Title> [<videoid>].m4a   (requires ffmpeg for best results)
- ./logs/download.log                    (detailed per-item logs)
- ./download_manifest.csv                (summary: query,video_id,status,file_path,error)

⚠️ Only download content you have rights to. Respect YouTube/Google TOS and copyright law.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Tuple
import csv
import time
import sys

from ytmusicapi import YTMusic
import yt_dlp

from helpers import (
    parse_line,
    extract_video_id,
    backoff_retry,
    ytm_search_best_video_id,
    setup_logger,
)

INPUT_FILE = "songs.txt"
DOWNLOAD_DIR = Path("downloads")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "download.log"
MANIFEST = Path("download_manifest.csv")

AUDIO_FORMAT = "m4a"  # change to "mp3" if preferred (requires ffmpeg)

def make_downloader(video_id: str):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s"),
        "format": "bestaudio/best",
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": AUDIO_FORMAT,
                "preferredquality": "0",
            }
        ],
        # Let yt-dlp handle some of its own internal retries as well
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 20,
        "continuedl": True,
        "quiet": False,
    }

    def _dl():
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.download([url])

    return _dl, url

def find_video_id(yt: YTMusic, query: str, url: Optional[str]) -> Optional[str]:
    vid = extract_video_id(url)
    if vid:
        return vid
    # backoff around search
    return backoff_retry(ytm_search_best_video_id, yt, query, tries=6, base_delay=0.6, max_delay=40)

def write_manifest_header_if_needed():
    if not MANIFEST.exists():
        with MANIFEST.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["query", "video_id", "status", "file_path", "error"])

def append_manifest(query: str, video_id: Optional[str], status: str, file_path: str = "", error: str = ""):
    with MANIFEST.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([query, video_id or "", status, file_path, error])

def main():
    logger = setup_logger("downloader", LOG_FILE)

    p = Path(INPUT_FILE)
    if not p.exists():
        logger.error("Missing %s", INPUT_FILE)
        sys.exit(2)

    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    parsed: List[Tuple[str, Optional[str]]] = [parse_line(ln) for ln in lines]
    total = len(parsed)

    # YT Music auth for search
    token_file = "oauth.json"
    if not Path(token_file).exists():
        logger.info("Starting YouTube Music OAuth; this will open a browser...")
        YTMusic.setup_oauth(token_file)
    yt = YTMusic(token_file)

    write_manifest_header_if_needed()

    found = 0
    downloaded = 0
    not_found = 0
    failures = 0

    for idx, (query, url) in enumerate(parsed, start=1):
        logger.info("[%d/%d] Resolving: %s", idx, total, query or url or "<empty line>")

        try:
            video_id = find_video_id(yt, query, url)
        except Exception as e:
            logger.warning("Search error for '%s': %s", query, e)
            append_manifest(query, None, "search_error", "", str(e))
            not_found += 1
            # brief pause before continuing
            time.sleep(0.1)
            continue

        if not video_id:
            logger.warning("Not found: %s", query)
            append_manifest(query, None, "not_found")
            not_found += 1
            time.sleep(0.05)
            continue

        found += 1
        _download_fn, resolved_url = make_downloader(video_id)
        logger.info("Downloading %s (videoId=%s)", resolved_url, video_id)

        try:
            # Heavy network step with retries
            backoff_retry(_download_fn, tries=5, base_delay=1.0, max_delay=60)
            # We can’t easily know the exact output filename here; put folder placeholder
            append_manifest(query, video_id, "downloaded", str(DOWNLOAD_DIR))
            logger.info("Downloaded OK: %s", query)
            downloaded += 1
        except Exception as e:
            failures += 1
            append_manifest(query, video_id, "download_failed", "", str(e))
            logger.error("Download FAILED for %s (videoId=%s): %s", query, video_id, e)

        # light pacing to be gentle
        time.sleep(0.05)

    logger.info("Finished. Found=%d, Downloaded=%d, NotFound=%d, Failures=%d", found, downloaded, not_found, failures)
    print(f"Done. See log: {LOG_FILE} and manifest: {MANIFEST}")

if __name__ == "__main__":
    main()
