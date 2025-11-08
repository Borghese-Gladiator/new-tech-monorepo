"""
Parse markdown playlist files and extract track information.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from loguru import logger


@dataclass
class TrackRequest:
    """Represents a track parsed from markdown with metadata."""

    raw_line: str
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    url: Optional[str] = None
    local_path: Optional[str] = None


def parse_markdown_file(file_path: str, max_items: Optional[int] = None) -> List[TrackRequest]:
    """
    Parse a markdown file and extract track information.

    Args:
        file_path: Path to markdown file
        max_items: Maximum number of tracks to parse (None for all)

    Returns:
        List of TrackRequest objects
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    tracks = []

    with path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines and headers
            if not line or line.startswith('#'):
                continue

            # Skip lines that don't start with bullet points
            if not line.startswith(('-', '*', '•')):
                continue

            # Remove bullet point
            clean_line = line.lstrip('-*•').strip()

            if not clean_line:
                continue

            # Try to parse artist - title format
            artist, title = None, None
            if ' - ' in clean_line:
                parts = clean_line.split(' - ', 1)
                if len(parts) == 2:
                    artist, title = parts[0].strip(), parts[1].strip()

            track = TrackRequest(
                raw_line=clean_line,
                artist=artist,
                title=title,
            )

            tracks.append(track)

            # Check max_items limit
            if max_items and len(tracks) >= max_items:
                logger.info(f"Reached max_items limit: {max_items}")
                break

    logger.info(f"Parsed {len(tracks)} tracks from {file_path}")
    return tracks
