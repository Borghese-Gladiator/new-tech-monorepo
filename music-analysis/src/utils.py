"""
Utility functions for logging, I/O, deduplication, and normalization.
"""
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from loguru import logger


def setup_logging(log_path: str = "./outputs/run.log") -> None:
    """
    Configure loguru logger to write to both console and file.

    Args:
        log_path: Path to the log file
    """
    # Remove default handler
    logger.remove()

    # Add console handler with INFO level
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Add file handler with DEBUG level
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
    )

    logger.info(f"Logging initialized. Log file: {log_path}")


def load_config(config_path: str = "./settings.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing configuration settings
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    logger.debug(f"Loaded configuration from {config_path}")
    return config


def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv()
    logger.debug("Environment variables loaded")


def normalize_string(text: str) -> str:
    """
    Normalize a string for comparison/deduplication.

    - Convert to lowercase
    - Remove accents and diacritics
    - Remove punctuation
    - Collapse whitespace
    - Remove parenthetical content like (feat. Artist)

    Args:
        text: Input string

    Returns:
        Normalized string
    """
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove accents/diacritics
    text = unicodedata.normalize('NFKD', text)
    text = ''.join([c for c in text if not unicodedata.combining(c)])

    # Remove parenthetical content
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)

    # Remove punctuation (keep spaces and alphanumeric)
    text = re.sub(r'[^\w\s]', ' ', text)

    # Collapse whitespace
    text = ' '.join(text.split())

    return text.strip()


def create_dedup_key(artist: str, title: str) -> str:
    """
    Create a deduplication key from artist and title.

    Args:
        artist: Artist name
        title: Track title

    Returns:
        Normalized deduplication key
    """
    combined = f"{artist} {title}"
    return normalize_string(combined)


def deduplicate_tracks(tracks: List[Dict[str, Any]], key_func=None) -> List[Dict[str, Any]]:
    """
    Deduplicate a list of tracks, keeping the first occurrence.

    Args:
        tracks: List of track dictionaries
        key_func: Optional function to extract dedup key from track dict.
                  Defaults to using 'artist' and 'title' fields.

    Returns:
        Deduplicated list of tracks
    """
    if key_func is None:
        key_func = lambda t: create_dedup_key(t.get('artist', ''), t.get('title', ''))

    seen = set()
    deduplicated = []

    for track in tracks:
        key = key_func(track)
        if key and key not in seen:
            seen.add(key)
            deduplicated.append(track)
        else:
            logger.debug(f"Duplicate track skipped: {track.get('artist')} - {track.get('title')}")

    logger.info(f"Deduplicated {len(tracks)} tracks to {len(deduplicated)} unique tracks")
    return deduplicated


def sanitize_filename(text: str, max_length: int = 200) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        text: Input string
        max_length: Maximum filename length

    Returns:
        Sanitized filename-safe string
    """
    # Remove/replace invalid characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)

    # Collapse whitespace
    text = ' '.join(text.split())

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length].rsplit(' ', 1)[0]

    return text.strip()


def ensure_dir(path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_playlist_name_with_date(base_name: str) -> str:
    """
    Append current date to playlist name.

    Args:
        base_name: Base playlist name

    Returns:
        Playlist name with date appended
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{base_name} ({date_str})"


def write_failed_inputs(failed_lines: List[str], output_path: str) -> None:
    """
    Write failed input lines to a text file.

    Args:
        failed_lines: List of original input lines that failed
        output_path: Path to output file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in failed_lines:
            f.write(f"{line}\n")

    logger.info(f"Wrote {len(failed_lines)} failed inputs to {output_path}")


def append_failed_input(failed_line: str, output_path: str) -> None:
    """
    Append a failed input line to the failed inputs file.

    Args:
        failed_line: Original input line that failed
        output_path: Path to output file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(f"{failed_line}\n")


def parse_url_type(url: str) -> Optional[str]:
    """
    Determine the type of URL (spotify, youtube, youtube_music).

    Args:
        url: URL string

    Returns:
        URL type ('spotify', 'youtube', 'youtube_music') or None
    """
    url_lower = url.lower()

    if 'open.spotify.com' in url_lower:
        return 'spotify'
    elif 'music.youtube.com' in url_lower:
        return 'youtube_music'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'

    return None


def extract_spotify_track_id(url: str) -> Optional[str]:
    """
    Extract Spotify track ID from URL.

    Args:
        url: Spotify URL

    Returns:
        Track ID or None
    """
    # Pattern: https://open.spotify.com/track/{id}?...
    match = re.search(r'spotify\.com/track/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)

    # Also handle spotify: URIs
    match = re.search(r'spotify:track:([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)

    return None


def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL.

    Args:
        url: YouTube URL

    Returns:
        Video ID or None
    """
    # Pattern: https://www.youtube.com/watch?v={id}
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # Pattern: https://youtu.be/{id}
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    # Pattern: https://music.youtube.com/watch?v={id}
    match = re.search(r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)

    return None
