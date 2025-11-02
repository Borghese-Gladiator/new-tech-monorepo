"""
Markdown parser for track lists.

Parses Markdown files containing track information in various formats:
- Artist – Title
- Artist - Title (feat. Guest)
- Direct URLs (YouTube, YouTube Music, Spotify)
- Local file paths
- Optional hints in square brackets
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from .utils import parse_url_type, extract_spotify_track_id, extract_youtube_video_id


@dataclass
class TrackRequest:
    """Represents a track request parsed from markdown."""

    raw_line: str
    artist: Optional[str] = None
    title: Optional[str] = None
    album: Optional[str] = None
    url: Optional[str] = None
    url_type: Optional[str] = None  # 'spotify', 'youtube', 'youtube_music'
    local_path: Optional[str] = None
    notes: Optional[str] = None
    hints: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        if self.url:
            return f"TrackRequest(url={self.url})"
        elif self.artist and self.title:
            return f"TrackRequest(artist={self.artist}, title={self.title})"
        else:
            return f"TrackRequest(raw_line={self.raw_line[:50]}...)"


def parse_markdown_line(line: str) -> Optional[TrackRequest]:
    """
    Parse a single line from a markdown file.

    Args:
        line: Raw line from markdown file

    Returns:
        TrackRequest object or None if line is empty/invalid
    """
    original_line = line
    line = line.strip()

    # Skip empty lines and headers
    if not line or line.startswith('#'):
        return None

    # Remove markdown list markers (-, *, •) and checkboxes
    line = re.sub(r'^[-*•]\s*', '', line)
    line = re.sub(r'^\[[ xX]\]\s*', '', line)
    line = line.strip()

    if not line:
        return None

    # Extract hints in square brackets at the end [key:value] or [value]
    hints = {}
    hint_pattern = r'\[([^\]]+)\]'
    hint_matches = re.findall(hint_pattern, line)

    for hint in hint_matches:
        if ':' in hint:
            key, value = hint.split(':', 1)
            hints[key.strip()] = value.strip()
        else:
            # Generic note
            hints['note'] = hint.strip()

    # Remove hints from the line for further processing
    line_without_hints = re.sub(hint_pattern, '', line).strip()

    # Check if it's a URL
    url_pattern = r'https?://[^\s]+'
    url_match = re.search(url_pattern, line_without_hints)

    if url_match:
        url = url_match.group(0)
        url_type = parse_url_type(url)

        # Extract any remaining text as notes
        text_without_url = re.sub(url_pattern, '', line_without_hints).strip()
        text_without_url = re.sub(r'^[-–—:]\s*', '', text_without_url).strip()

        track = TrackRequest(
            raw_line=original_line,
            url=url,
            url_type=url_type,
            notes=text_without_url if text_without_url else None,
            hints=hints,
        )

        # Try to extract artist/title from remaining text if available
        if text_without_url:
            parsed = _parse_artist_title(text_without_url)
            if parsed:
                track.artist, track.title = parsed

        return track

    # Check if it's a local file path
    if line_without_hints.endswith(('.mp3', '.wav', '.flac', '.m4a')):
        path = Path(line_without_hints)
        if path.exists() or path.is_absolute() or '/' in line_without_hints:
            return TrackRequest(
                raw_line=original_line,
                local_path=str(path),
                hints=hints,
            )

    # Parse as Artist - Title format
    parsed = _parse_artist_title(line_without_hints)
    if not parsed:
        # Couldn't parse, but create a track request anyway with the full line as title
        logger.warning(f"Could not parse artist/title from line: {line_without_hints}")
        return TrackRequest(
            raw_line=original_line,
            title=line_without_hints,
            hints=hints,
        )

    artist, title = parsed

    # Extract album from hints if present
    album = hints.get('album') or hints.get('Album')

    return TrackRequest(
        raw_line=original_line,
        artist=artist,
        title=title,
        album=album,
        hints=hints,
    )


def _parse_artist_title(text: str) -> Optional[tuple[str, str]]:
    """
    Parse artist and title from text.

    Supports both hyphen (-) and en dash (–) as separators.

    Args:
        text: Text to parse

    Returns:
        Tuple of (artist, title) or None
    """
    # Try en dash first (–)
    if '–' in text:
        parts = text.split('–', 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
            if artist and title:
                return artist, title

    # Try hyphen with spaces
    if ' - ' in text:
        parts = text.split(' - ', 1)
        if len(parts) == 2:
            artist = parts[0].strip()
            title = parts[1].strip()
            if artist and title:
                return artist, title

    # Try hyphen without spaces (less reliable, only if text contains multiple words)
    if '-' in text:
        words = text.split()
        if len(words) >= 3:  # At least "Artist - Title"
            for i, word in enumerate(words):
                if word == '-' and i > 0 and i < len(words) - 1:
                    artist = ' '.join(words[:i]).strip()
                    title = ' '.join(words[i + 1:]).strip()
                    if artist and title:
                        return artist, title

    return None


def parse_markdown_file(file_path: str, max_items: Optional[int] = None) -> List[TrackRequest]:
    """
    Parse a markdown file containing track listings.

    Args:
        file_path: Path to markdown file
        max_items: Maximum number of items to parse (None for no limit)

    Returns:
        List of TrackRequest objects
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {file_path}")

    tracks = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if max_items and len(tracks) >= max_items:
                logger.info(f"Reached max_items limit ({max_items}), stopping parse")
                break

            track = parse_markdown_line(line)
            if track:
                tracks.append(track)
                logger.debug(f"Line {line_num}: Parsed {track}")

    logger.info(f"Parsed {len(tracks)} tracks from {file_path}")
    return tracks


def format_track_query(track: TrackRequest) -> str:
    """
    Format a track request as a search query string.

    Args:
        track: TrackRequest object

    Returns:
        Search query string
    """
    parts = []

    if track.artist:
        parts.append(track.artist)

    if track.title:
        parts.append(track.title)

    if track.album and 'album' in track.hints:
        parts.append(track.album)

    return ' '.join(parts)
