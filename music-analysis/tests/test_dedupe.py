"""
Tests for deduplication and normalization.
"""
import pytest
from scripts.core.utils import normalize_string, create_dedup_key, deduplicate_tracks


def test_normalize_string_lowercase():
    """Test string normalization to lowercase."""
    assert normalize_string("HELLO") == "hello"
    assert normalize_string("Hello World") == "hello world"


def test_normalize_string_punctuation():
    """Test punctuation removal."""
    assert normalize_string("Hello, World!") == "hello world"
    assert normalize_string("Artist - Title") == "artist title"


def test_normalize_string_parenthetical():
    """Test parenthetical content removal."""
    assert normalize_string("Title (feat. Artist)") == "title"
    assert normalize_string("Song (Remix)") == "song"
    assert normalize_string("Track [Live]") == "track"


def test_normalize_string_whitespace():
    """Test whitespace collapsing."""
    assert normalize_string("Hello    World") == "hello world"
    assert normalize_string("  Spaced  Out  ") == "spaced out"


def test_normalize_string_accents():
    """Test accent/diacritic removal."""
    assert normalize_string("café") == "cafe"
    assert normalize_string("naïve") == "naive"


def test_create_dedup_key():
    """Test deduplication key creation."""
    key1 = create_dedup_key("Daft Punk", "Digital Love")
    key2 = create_dedup_key("daft punk", "digital love")
    assert key1 == key2

    key3 = create_dedup_key("Artist", "Title (feat. Guest)")
    key4 = create_dedup_key("Artist", "Title")
    assert key3 == key4


def test_deduplicate_tracks_basic():
    """Test basic track deduplication."""
    tracks = [
        {'artist': 'Artist', 'title': 'Title'},
        {'artist': 'Artist', 'title': 'Title'},
        {'artist': 'Other', 'title': 'Song'},
    ]

    result = deduplicate_tracks(tracks)
    assert len(result) == 2


def test_deduplicate_tracks_case_insensitive():
    """Test case-insensitive deduplication."""
    tracks = [
        {'artist': 'Daft Punk', 'title': 'Digital Love'},
        {'artist': 'daft punk', 'title': 'digital love'},
        {'artist': 'DAFT PUNK', 'title': 'DIGITAL LOVE'},
    ]

    result = deduplicate_tracks(tracks)
    assert len(result) == 1


def test_deduplicate_tracks_featuring():
    """Test deduplication with featuring artists."""
    tracks = [
        {'artist': 'Artist', 'title': 'Title'},
        {'artist': 'Artist', 'title': 'Title (feat. Guest)'},
    ]

    result = deduplicate_tracks(tracks)
    assert len(result) == 1


def test_deduplicate_tracks_punctuation():
    """Test deduplication with different punctuation."""
    tracks = [
        {'artist': 'Artist', 'title': 'Title'},
        {'artist': 'Artist', 'title': 'Title!'},
        {'artist': 'Artist', 'title': 'Title?'},
    ]

    result = deduplicate_tracks(tracks)
    assert len(result) == 1


def test_deduplicate_tracks_order():
    """Test that first occurrence is kept."""
    tracks = [
        {'artist': 'A', 'title': 'T', 'id': 1},
        {'artist': 'A', 'title': 'T', 'id': 2},
    ]

    result = deduplicate_tracks(tracks)
    assert len(result) == 1
    assert result[0]['id'] == 1


def test_deduplicate_tracks_empty():
    """Test deduplication with empty list."""
    result = deduplicate_tracks([])
    assert len(result) == 0
