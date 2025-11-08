"""
Search and match tracks on Spotify and YouTube Music.

Handles searching for tracks by artist/title and fuzzy matching to find the best candidates.
"""
import os
from typing import Dict, List, Optional, Tuple

import spotipy
from loguru import logger
from rapidfuzz import fuzz
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic

from .md_parser import TrackRequest
from .utils import extract_spotify_track_id, extract_youtube_video_id, normalize_string


class SearchMatcher:
    """Handles searching and matching tracks on Spotify and YouTube Music."""

    def __init__(
        self,
        spotify_client_id: Optional[str] = None,
        spotify_client_secret: Optional[str] = None,
        spotify_redirect_uri: Optional[str] = None,
        ytmusic_headers_path: Optional[str] = None,
        fuzzy_threshold: int = 80,
        max_candidates: int = 5,
        yt_search_filter: str = "songs",
    ):
        """
        Initialize the search matcher.

        Args:
            spotify_client_id: Spotify API client ID
            spotify_client_secret: Spotify API client secret
            spotify_redirect_uri: Spotify OAuth redirect URI
            ytmusic_headers_path: Path to ytmusicapi headers JSON
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            max_candidates: Maximum search candidates to consider
            yt_search_filter: YouTube Music search filter ('songs' or 'videos')
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.max_candidates = max_candidates
        self.yt_search_filter = yt_search_filter

        # Initialize Spotify client
        self.spotify = None
        if spotify_client_id and spotify_client_secret:
            try:
                auth_manager = SpotifyOAuth(
                    client_id=spotify_client_id,
                    client_secret=spotify_client_secret,
                    redirect_uri=spotify_redirect_uri or "http://localhost:8888/callback",
                    scope="playlist-modify-public playlist-modify-private",
                )
                self.spotify = spotipy.Spotify(auth_manager=auth_manager)
                logger.info("Spotify client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Spotify client: {e}")

        # Initialize YouTube Music client
        self.ytmusic = None
        if ytmusic_headers_path and os.path.exists(ytmusic_headers_path):
            try:
                self.ytmusic = YTMusic(ytmusic_headers_path)
                logger.info("YouTube Music client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize YouTube Music client: {e}")

    def search_track(
        self, track: TrackRequest
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Search for a track and return identifiers.

        Args:
            track: TrackRequest object

        Returns:
            Tuple of (download_url, spotify_id, ytmusic_video_id, source)
        """
        # If URL is provided, extract IDs
        if track.url:
            url_type = track.url_type

            if url_type == 'spotify':
                spotify_id = extract_spotify_track_id(track.url)
                if spotify_id:
                    logger.info(f"Using Spotify URL: {track.url}")
                    return None, spotify_id, None, 'spotify'

            elif url_type in ('youtube', 'youtube_music'):
                video_id = extract_youtube_video_id(track.url)
                if video_id:
                    download_url = track.url
                    logger.info(f"Using YouTube URL: {track.url}")
                    return download_url, None, video_id, 'youtube'

        # Build search query
        query = self._build_query(track)
        if not query:
            logger.warning(f"Cannot build query for track: {track.raw_line}")
            return None, None, None, None

        # Search on YouTube Music first (for download)
        ytmusic_video_id = None
        download_url = None
        if self.ytmusic:
            ytmusic_video_id = self._search_ytmusic(query, track)
            if ytmusic_video_id:
                download_url = f"https://music.youtube.com/watch?v={ytmusic_video_id}"

        # Search on Spotify (for playlist)
        spotify_id = None
        if self.spotify:
            spotify_id = self._search_spotify(query, track)

        # Determine source
        source = None
        if ytmusic_video_id:
            source = 'youtube_music'
        elif spotify_id:
            source = 'spotify'

        return download_url, spotify_id, ytmusic_video_id, source

    def _build_query(self, track: TrackRequest) -> str:
        """Build a search query from track information."""
        parts = []

        if track.artist:
            parts.append(track.artist)

        if track.title:
            parts.append(track.title)

        if track.album:
            parts.append(track.album)

        return ' '.join(parts).strip()

    def _search_spotify(self, query: str, track: TrackRequest) -> Optional[str]:
        """
        Search for a track on Spotify.

        Args:
            query: Search query
            track: Original track request

        Returns:
            Spotify track ID or None
        """
        if not self.spotify:
            return None

        try:
            results = self.spotify.search(q=query, type='track', limit=self.max_candidates)
            items = results.get('tracks', {}).get('items', [])

            if not items:
                logger.debug(f"No Spotify results for query: {query}")
                return None

            # Find best match using fuzzy matching
            best_match = self._find_best_match(items, track, platform='spotify')
            if best_match:
                track_id = best_match['id']
                artist = best_match['artists'][0]['name']
                title = best_match['name']
                logger.info(f"Matched on Spotify: {artist} - {title} (ID: {track_id})")
                return track_id

        except Exception as e:
            logger.error(f"Spotify search error for query '{query}': {e}")

        return None

    def _search_ytmusic(self, query: str, track: TrackRequest) -> Optional[str]:
        """
        Search for a track on YouTube Music.

        Args:
            query: Search query
            track: Original track request

        Returns:
            YouTube Music video ID or None
        """
        if not self.ytmusic:
            return None

        try:
            results = self.ytmusic.search(
                query, filter=self.yt_search_filter, limit=self.max_candidates
            )

            if not results:
                logger.debug(f"No YouTube Music results for query: {query}")
                return None

            # Find best match using fuzzy matching
            best_match = self._find_best_match(results, track, platform='ytmusic')
            if best_match:
                video_id = best_match.get('videoId')
                artist = best_match.get('artists', [{}])[0].get('name', 'Unknown')
                title = best_match.get('title', 'Unknown')
                logger.info(f"Matched on YouTube Music: {artist} - {title} (ID: {video_id})")
                return video_id

        except Exception as e:
            logger.error(f"YouTube Music search error for query '{query}': {e}")

        return None

    def _find_best_match(
        self, candidates: List[Dict], track: TrackRequest, platform: str
    ) -> Optional[Dict]:
        """
        Find the best matching candidate using fuzzy matching.

        Args:
            candidates: List of search result candidates
            track: Original track request
            platform: 'spotify' or 'ytmusic'

        Returns:
            Best matching candidate or None
        """
        if not candidates:
            return None

        # Build target string from original track
        target_parts = []
        if track.artist:
            target_parts.append(track.artist)
        if track.title:
            target_parts.append(track.title)
        target = normalize_string(' '.join(target_parts))

        best_score = 0
        best_candidate = None

        for candidate in candidates:
            # Extract artist and title from candidate
            if platform == 'spotify':
                artist = candidate.get('artists', [{}])[0].get('name', '')
                title = candidate.get('name', '')
            else:  # ytmusic
                artist_list = candidate.get('artists', [])
                artist = artist_list[0].get('name', '') if artist_list else ''
                title = candidate.get('title', '')

            # Build candidate string
            candidate_str = normalize_string(f"{artist} {title}")

            # Calculate fuzzy match score
            score = fuzz.token_set_ratio(target, candidate_str)

            logger.debug(f"Candidate: {artist} - {title} | Score: {score}")

            if score > best_score:
                best_score = score
                best_candidate = candidate

        # Check if best score meets threshold
        if best_score >= self.fuzzy_threshold:
            return best_candidate

        logger.debug(f"Best score {best_score} below threshold {self.fuzzy_threshold}")
        return None


def create_search_matcher(config: Dict) -> SearchMatcher:
    """
    Create a SearchMatcher instance from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        SearchMatcher instance
    """
    return SearchMatcher(
        spotify_client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        spotify_client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        spotify_redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        ytmusic_headers_path=os.getenv('YTMUSIC_HEADERS_PATH'),
        fuzzy_threshold=config.get('fuzzy_threshold', 80),
        max_candidates=config.get('max_search_candidates', 5),
        yt_search_filter=config.get('yt_search_filter', 'songs'),
    )
