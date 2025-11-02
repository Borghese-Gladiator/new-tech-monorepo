import logging
from pathlib import Path
import sys
import pytest

# --- Ensure src/ is on the import path ---
# This adds the project’s src directory so we can import helpers.py
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import helpers


# -----------------------------
# parse_line
# -----------------------------
@pytest.mark.parametrize(
    "line,expected_query,expected_url",
    [
        ("Artist - Title", "Artist Title", None),
        ("Artist - Title - Extra", "Artist Title", None),
        ("Artist - タイトル（日本語）", "Artist タイトル 日本語", None),
        (
            "Artist - Title => https://youtu.be/ABCDEFGHIJK",
            "Artist Title",
            "https://youtu.be/ABCDEFGHIJK",
        ),
        (
            "Artist - Title - https://music.youtube.com/watch?v=ZZZYYYYXXXX",
            "Artist Title",
            "https://music.youtube.com/watch?v=ZZZYYYYXXXX",
        ),
        ("  3 Doors Down - Kryptonite  ", "3 Doors Down Kryptonite", None),
        ("", "", None),
        ("   ", "", None),
    ],
)
def test_parse_line(line, expected_query, expected_url):
    q, url = helpers.parse_line(line)
    # For languages, parse_line returns f"{artist} {clean_title}" (space)
    assert q == expected_query
    assert url == expected_url


# -----------------------------
# extract_video_id
# -----------------------------
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=ABCDEFGHIJK", "ABCDEFGHIJK"),
        ("https://youtu.be/ABCDEFGHIJK", "ABCDEFGHIJK"),
        ("https://music.youtube.com/watch?v=ABCDEFGHIJK&list=whatever", "ABCDEFGHIJK"),
        ("https://youtube.com/watch?v=ABC_DEF-GhI", "ABC_DEF-GhI"),
        (None, None),
        ("https://example.com", None),
    ],
)
def test_extract_video_id(url, expected):
    assert helpers.extract_video_id(url) == expected


# -----------------------------
# chunked
# -----------------------------
def test_chunked_even():
    data = list(range(10))
    chunks = list(helpers.chunked(data, 2))
    assert chunks == [ [0,1], [2,3], [4,5], [6,7], [8,9] ]

def test_chunked_last_short():
    data = [1,2,3,4,5]
    chunks = list(helpers.chunked(data, 2))
    assert chunks == [ [1,2], [3,4], [5] ]


# -----------------------------
# backoff_retry
# -----------------------------
def test_backoff_retry_succeeds_after_failures(monkeypatch):
    calls = {"n": 0}

    def sometimes():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = helpers.backoff_retry(sometimes, tries=5, base_delay=0.1, max_delay=1.0)
    assert result == "ok"
    assert calls["n"] == 3  # failed twice, then succeeded

def test_backoff_retry_raises_after_exhaustion():
    def always_bad():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        helpers.backoff_retry(always_bad, tries=3, base_delay=0.01, max_delay=0.05, exceptions=(ValueError,))


# -----------------------------
# init_logger
# -----------------------------
def test_setup_logger_creates_file_and_handlers(tmp_path: Path):
    log_file = tmp_path / "app.log"
    logger = helpers.setup_logger("testlogger", log_file, level=logging.INFO)

    # Emits one line
    logger.info("hello")
    assert log_file.exists()
    # Ensure we have both console and file handlers attached
    assert any(h.__class__.__name__.endswith("RotatingFileHandler") for h in logger.handlers)
    assert any(h.__class__.__name__ == "StreamHandler" for h in logger.handlers)


# -----------------------------
# ytm_search_best_video_id
# -----------------------------
def test_ytm_search_best_video_id_prefers_songs_then_videos(monkeypatch):
    class FakeYT:
        def __init__(self):
            self.calls = []

        def search(self, query, filter=None, limit=12):
            self.calls.append((query, filter, limit))
            if filter == "songs":
                # Return a good match
                return [
                    {"title": "Kryptonite", "artists": [{"name": "3 Doors Down"}], "videoId": "VID123"},
                    {"title": "Other", "artists": [{"name": "Someone"}], "videoId": "VID999"},
                ]
            elif filter == "videos":
                # Would only be used if 'songs' empty
                return [
                    {"title": "Kryptonite (live)", "artists": [{"name": "3 Doors Down"}], "videoId": "VID777"}
                ]
            return []

    yt = FakeYT()
    vid = helpers.ytm_search_best_video_id(yt, "3 Doors Down Kryptonite", threshold=50)
    assert vid == "VID123"
    # Ensure songs was called first
    assert yt.calls[0][1] == "songs"


def test_ytm_search_best_video_id_none_when_no_results():
    class FakeYT:
        def search(self, *args, **kwargs):
            return []

    yt = FakeYT()
    assert helpers.ytm_search_best_video_id(yt, "nonexistent query") is None


# -----------------------------
# spotify_search_best_uri
# -----------------------------
def test_spotify_search_best_uri_scores_and_picks(monkeypatch):
    class FakeSP:
        def search(self, q, type, limit, market):
            assert type == "track"
            return {
                "tracks": {
                    "items": [
                        {
                            "name": "Kryptonite",
                            "artists": [{"name": "3 Doors Down"}],
                            "uri": "spotify:track:GOOD",
                        },
                        {
                            "name": "Something Else",
                            "artists": [{"name": "Who"}],
                            "uri": "spotify:track:BAD",
                        },
                    ]
                }
            }

    sp = FakeSP()
    uri = helpers.spotify_search_best_uri(sp, "3 Doors Down Kryptonite", threshold=50)
    assert uri == "spotify:track:GOOD"

def test_spotify_search_best_uri_returns_none_when_no_items():
    class FakeSP:
        def search(self, *args, **kwargs):
            return {"tracks": {"items": []}}

    sp = FakeSP()
    assert helpers.spotify_search_best_uri(sp, "nope") is None


# -----------------------------
# ytm_add_items / spotify_add_items chunking
# -----------------------------
def test_ytm_add_items_chunking_calls(monkeypatch):
    class FakeYT:
        def __init__(self):
            self.calls = []
        def add_playlist_items(self, playlist_id, items):
            # record call
            self.calls.append((playlist_id, list(items)))

    yt = FakeYT()
    items = [f"vid{i}" for i in range(0, 205)]  # > 2 chunks
    helpers.ytm_add_items(yt, "PLID", items)
    # Should be 3 calls: 100, 100, 5
    assert len(yt.calls) == 3
    assert len(yt.calls[0][1]) == 100
    assert len(yt.calls[1][1]) == 100
    assert len(yt.calls[2][1]) == 5

def test_spotify_add_items_chunking_calls(monkeypatch):
    class FakeSP:
        def __init__(self):
            self.calls = []
        def playlist_add_items(self, playlist_id, uris):
            self.calls.append((playlist_id, list(uris)))

    sp = FakeSP()
    uris = [f"spotify:track:{i}" for i in range(0, 101)]
    helpers.spotify_add_items(sp, "PLID", uris)
    # Should be 2 calls: 100 + 1
    assert len(sp.calls) == 2
    assert len(sp.calls[0][1]) == 100
    assert len(sp.calls[1][1]) == 1
