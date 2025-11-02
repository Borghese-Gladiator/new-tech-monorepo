"""
Tests for Markdown parser.
"""
import pytest
from src.md_parser import parse_markdown_line, TrackRequest


def test_parse_simple_artist_title():
    """Test parsing simple Artist - Title format."""
    line = "Daft Punk - Digital Love"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Daft Punk"
    assert track.title == "Digital Love"
    assert track.url is None


def test_parse_en_dash():
    """Test parsing with en dash separator."""
    line = "Nujabes – Luv(sic) pt3"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Nujabes"
    assert track.title == "Luv(sic) pt3"


def test_parse_with_feat():
    """Test parsing with featuring artist."""
    line = "Artist - Title (feat. Guest)"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Artist"
    assert "Title" in track.title
    assert "feat" in track.title


def test_parse_with_checkbox():
    """Test parsing with markdown checkbox."""
    line = "- [ ] Kavinsky – Nightcall"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Kavinsky"
    assert track.title == "Nightcall"


def test_parse_with_checked_box():
    """Test parsing with checked markdown checkbox."""
    line = "- [x] Daft Punk - Harder Better Faster Stronger"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Daft Punk"
    assert track.title == "Harder Better Faster Stronger"


def test_parse_with_bullet():
    """Test parsing with bullet point."""
    line = "* Porter Robinson - Shelter"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Porter Robinson"
    assert track.title == "Shelter"


def test_parse_with_album_hint():
    """Test parsing with album hint."""
    line = "Daft Punk – Digital Love [album: Discovery]"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Daft Punk"
    assert track.title == "Digital Love"
    assert track.album == "Discovery"


def test_parse_spotify_url():
    """Test parsing Spotify URL."""
    line = "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.url == line
    assert track.url_type == "spotify"


def test_parse_youtube_url():
    """Test parsing YouTube URL."""
    line = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.url == line
    assert track.url_type == "youtube"


def test_parse_youtube_music_url():
    """Test parsing YouTube Music URL."""
    line = "https://music.youtube.com/watch?v=xxxxxxxxxxx"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.url == line
    assert track.url_type == "youtube_music"


def test_parse_empty_line():
    """Test parsing empty line."""
    track = parse_markdown_line("")
    assert track is None


def test_parse_header():
    """Test parsing markdown header."""
    track = parse_markdown_line("# My Playlist")
    assert track is None


def test_parse_with_notes():
    """Test parsing with notes in brackets."""
    line = "Artist - Title [note: great song]"
    track = parse_markdown_line(line)

    assert track is not None
    assert track.artist == "Artist"
    assert track.title == "Title"
    assert 'note' in track.hints
