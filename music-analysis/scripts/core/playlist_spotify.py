"""
Spotify playlist management.

Creates/updates Spotify playlists with tracks.
"""
import os
from typing import List, Optional

import spotipy
from loguru import logger
from spotipy.oauth2 import SpotifyOAuth


class SpotifyPlaylistManager:
    """Manages Spotify playlists."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        username: Optional[str] = None,
    ):
        """
        Initialize Spotify playlist manager.

        Args:
            client_id: Spotify API client ID
            client_secret: Spotify API client secret
            redirect_uri: OAuth redirect URI
            username: Spotify username
        """
        self.username = username or os.getenv('SPOTIFY_USERNAME')

        if not client_id or not client_secret:
            raise ValueError("Spotify credentials not provided")

        # Initialize Spotify client
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri or "http://localhost:8888/callback",
            scope="playlist-modify-public playlist-modify-private",
        )
        self.spotify = spotipy.Spotify(auth_manager=auth_manager)

        # Get current user if username not provided
        if not self.username:
            user_info = self.spotify.current_user()
            self.username = user_info['id']

        logger.info(f"Spotify client initialized for user: {self.username}")

    def find_or_create_playlist(self, playlist_name: str, description: str = "") -> str:
        """
        Find existing playlist by name or create a new one.

        Args:
            playlist_name: Name of the playlist
            description: Playlist description

        Returns:
            Playlist ID
        """
        # Search for existing playlist
        playlists = self.spotify.current_user_playlists()

        for playlist in playlists['items']:
            if playlist['name'] == playlist_name:
                playlist_id = playlist['id']
                logger.info(f"Found existing playlist: {playlist_name} (ID: {playlist_id})")
                return playlist_id

        # Create new playlist
        playlist = self.spotify.user_playlist_create(
            user=self.username,
            name=playlist_name,
            public=True,
            description=description,
        )
        playlist_id = playlist['id']
        logger.info(f"Created new playlist: {playlist_name} (ID: {playlist_id})")
        return playlist_id

    def add_tracks(self, playlist_id: str, track_ids: List[str], batch_size: int = 100) -> int:
        """
        Add tracks to a playlist.

        Args:
            playlist_id: Playlist ID
            track_ids: List of Spotify track IDs
            batch_size: Number of tracks to add per API call

        Returns:
            Number of tracks successfully added
        """
        if not track_ids:
            logger.warning("No tracks to add")
            return 0

        # Convert track IDs to URIs
        track_uris = [f"spotify:track:{track_id}" for track_id in track_ids]

        # Add in batches
        added_count = 0
        for i in range(0, len(track_uris), batch_size):
            batch = track_uris[i:i + batch_size]
            try:
                self.spotify.playlist_add_items(playlist_id, batch)
                added_count += len(batch)
                logger.info(f"Added {len(batch)} tracks to playlist (total: {added_count})")
            except Exception as e:
                logger.error(f"Failed to add batch {i // batch_size + 1}: {e}")

        logger.info(f"Successfully added {added_count}/{len(track_ids)} tracks to playlist")
        return added_count

    def clear_playlist(self, playlist_id: str) -> None:
        """
        Remove all tracks from a playlist.

        Args:
            playlist_id: Playlist ID
        """
        try:
            # Get all tracks
            tracks = []
            results = self.spotify.playlist_items(playlist_id)
            tracks.extend(results['items'])

            while results['next']:
                results = self.spotify.next(results)
                tracks.extend(results['items'])

            if not tracks:
                logger.info("Playlist is already empty")
                return

            # Remove all tracks
            track_uris = [item['track']['uri'] for item in tracks if item['track']]
            batch_size = 100

            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                self.spotify.playlist_remove_all_occurrences_of_items(playlist_id, batch)

            logger.info(f"Removed {len(track_uris)} tracks from playlist")

        except Exception as e:
            logger.error(f"Failed to clear playlist: {e}")

    def create_and_populate_playlist(
        self,
        playlist_name: str,
        track_ids: List[str],
        description: str = "",
        clear_existing: bool = False,
    ) -> Optional[str]:
        """
        Create (or find) a playlist and populate it with tracks.

        Args:
            playlist_name: Name of the playlist
            track_ids: List of Spotify track IDs
            description: Playlist description
            clear_existing: Whether to clear existing playlist before adding tracks

        Returns:
            Playlist ID or None on failure
        """
        try:
            # Find or create playlist
            playlist_id = self.find_or_create_playlist(playlist_name, description)

            # Clear if requested
            if clear_existing:
                self.clear_playlist(playlist_id)

            # Add tracks
            self.add_tracks(playlist_id, track_ids)

            return playlist_id

        except Exception as e:
            logger.error(f"Failed to create/populate playlist: {e}")
            return None


def create_spotify_manager() -> SpotifyPlaylistManager:
    """
    Create a SpotifyPlaylistManager from environment variables.

    Returns:
        SpotifyPlaylistManager instance
    """
    return SpotifyPlaylistManager(
        client_id=os.getenv('SPOTIFY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
        username=os.getenv('SPOTIFY_USERNAME'),
    )
