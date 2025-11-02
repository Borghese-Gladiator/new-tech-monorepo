#!/usr/bin/env python3
"""
Shared helpers:
- Logging setup (console + RotatingFileHandler to ./logs/*.log)
- parse_line, extract_video_id, chunked
- backoff_retry() with detailed retry logging
- YouTube Music & Spotify search/add wrappers (with retries)
"""

from __future__ import annotations
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple, Callable, Type, Any
import random
import time
import re
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# -------- Logging --------

def setup_logger(name: str, logfile: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure a logger with both console + rotating file output to ./logs/<logfile>.
    """
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

    # Rotating file handler (5 MB, keep 5 backups)
    fh = RotatingFileHandler(logs_dir / logfile, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

# -------- Parsing --------

def parse_line(line: str) -> Tuple[str, Optional[str]]:
    """
    Parse a songs.txt line into (search_query, optional_url).
    Accepts:
      Artist - Title
      Artist - Title - Extra info
      Artist - Title => https://youtu.be/ID
      Artist - Title - https://music.youtube.com/watch?v=ID
    """
    line = line.strip()
    if not line:
        return ("", None)

    url = None
    if "=>" in line:
        left, right = line.split("=>", 1)
        url_candidate = right.strip()
        if url_candidate.startswith("http"):
            url = url_candidate
        line = left.strip()

    m = re.search(r"(https?://\S+)$", line)
    if m:
        url = m.group(1)
        line = line[: m.start()].strip(" -")

    parts = [p.strip() for p in line.split(" - ") if p.strip()]
    if len(parts) >= 2:
        artist, title = parts[0], parts[1]
        title_clean = re.sub(r"[【】\[\]（）()]+", " ", title)
        query = f"{artist} {title_clean}".strip()
    else:
        query = line
    return (query, url)


def extract_video_id(url: str | None) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"(?:v=|/video/|/watch/|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def chunked(seq: Sequence[Any], size: int) -> Iterator[Sequence[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

# -------- Backoff --------

def backoff_retry(
    fn: Callable[..., Any],
    *args: Any,
    tries: int = 6,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: float = 0.25,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
    op_name: str = "operation",
    **kwargs: Any,
) -> Any:
    """
    Call `fn(*args, **kwargs)` with capped exponential backoff + jitter.
    Logs each retry and final failure if a logger is provided.
    """
    attempt = 0
    last_exc: Optional[BaseException] = None
    while attempt < tries:
        try:
            return fn(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            attempt += 1
            if attempt >= tries:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter_span = delay * jitter
            sleep_for = max(0.0, delay + random.uniform(-jitter_span, jitter_span))
            if logger:
                logger.warning(
                    f"{op_name} failed (attempt {attempt}/{tries-1}); retrying in {sleep_for:.2f}s: {e}"
                )
            time.sleep(sleep_for)
    if logger:
        logger.error(f"{op_name} failed permanently after {tries} tries: {last_exc}")
    assert last_exc is not None
    raise last_exc

# -------- YT Music wrappers (with RapidFuzz scoring) --------
from rapidfuzz import fuzz  # type: ignore

def ytm_search_best_video_id(yt, query: str, threshold: int = 60, logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    Search YouTube Music for `query`, prefer 'songs' then 'videos'.
    Returns best videoId or None. Intended to be wrapped by backoff_retry.
    """
    if not query:
        return None
    for filt in ("songs", "videos"):
        results = yt.search(query, filter=filt, limit=12)
        if not results:
            continue
        scored = []
        for r in results:
            title = r.get("title") or ""
            artists = " ".join(a.get("name", "") for a in r.get("artists", []) if a)
            text = f"{artists} {title}".strip()
            score = fuzz.token_set_ratio(query, text)
            vid = r.get("videoId")
            if vid:
                scored.append((score, vid, text))
        if scored:
            scored.sort(reverse=True, key=lambda x: x[0])
            top = scored[0]
            if logger:
                logger.debug(f"Search '{query}' → top '{top[2]}' score {top[0]} (filter={filt})")
            if top[0] >= threshold:
                return top[1]
    return None

def ytm_add_items(yt, playlist_id: str, video_ids: List[str], logger: Optional[logging.Logger] = None) -> None:
    for chunk in chunked(video_ids, 100):
        backoff_retry(yt.add_playlist_items, playlist_id, list(chunk), logger=logger, op_name="ytm.add_playlist_items")

# -------- Spotify wrappers --------

def spotify_search_best_uri(sp, query: str, threshold: int = 60, logger: Optional[logging.Logger] = None) -> Optional[str]:
    if not query:
        return None
    res = sp.search(q=query, type="track", limit=12, market="US")
    items = res.get("tracks", {}).get("items", [])
    if not items:
        return None
    scored = []
    for t in items:
        artist_names = ", ".join(a["name"] for a in t["artists"])
        title = t["name"]
        text = f"{artist_names} {title}"
        score = fuzz.token_set_ratio(query, text)
        scored.append((score, t["uri"], text))
    scored.sort(reverse=True, key=lambda x: x[0])
    best = scored[0]
    if logger:
        logger.debug(f"Search '{query}' → top '{best[2]}' score {best[0]}")
    return best[1] if best and best[0] >= threshold else None

def spotify_add_items(sp, playlist_id: str, uris: List[str], logger: Optional[logging.Logger] = None) -> None:
    for chunk in chunked(uris, 100):
        backoff_retry(sp.playlist_add_items, playlist_id, list(chunk), logger=logger, op_name="spotify.playlist_add_items")
