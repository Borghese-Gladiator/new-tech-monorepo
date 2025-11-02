"""
YouTube Music playlist management.

Creates/updates YouTube Music playlists with tracks.
"""
import os
from typing import List, Optional

from loguru import logger
from ytmusicapi import YTMusic


class YTMusicPlaylistManager:
    """Manages YouTube Music playlists."""

    def __init__(self, headers_path: Optional[str] = None):
        """
        Initialize YouTube Music playlist manager.

        Args:
            headers_path: Path to ytmusicapi headers JSON file
        """
        if not headers_path:
            headers_path = os.getenv('YTMUSIC_HEADERS_PATH')

        if not headers_path or not os.path.exists(headers_path):
            raise ValueError(f"YTMusic headers file not found: {headers_path}")

        self.ytmusic = YTMusic(headers_path)
        logger.info("YouTube Music client initialized")

    def find_playlist(self, playlist_name: str) -> Optional[str]:
        """
        Find existing playlist by name.

        Args:
            playlist_name: Name of the playlist

        Returns:
            Playlist ID or None if not found
        """
        try:
            playlists = self.ytmusic.get_library_playlists()

            for playlist in playlists:
                if playlist['title'] == playlist_name:
                    playlist_id = playlist['playlistId']
                    logger.info(f"Found existing playlist: {playlist_name} (ID: {playlist_id})")
                    return playlist_id

            logger.info(f"Playlist not found: {playlist_name}")
            return None

        except Exception as e:
            logger.error(f"Failed to search for playlist: {e}")
            return None

    def create_playlist(
        self,
        playlist_name: str,
        description: str = "",
        privacy_status: str = "PUBLIC",
    ) -> Optional[str]:
        """
        Create a new playlist.

        Args:
            playlist_name: Name of the playlist
            description: Playlist description
            privacy_status: Privacy setting ('PUBLIC', 'PRIVATE', 'UNLISTED')

        Returns:
            Playlist ID or None on failure
        """
        try:
            playlist_id = self.ytmusic.create_playlist(
                title=playlist_name,
                description=description,
                privacy_status=privacy_status,
            )
            logger.info(f"Created new playlist: {playlist_name} (ID: {playlist_id})")
            return playlist_id

        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            return None

    def add_tracks(
        self,
        playlist_id: str,
        video_ids: List[str],
        batch_size: int = 50,
    ) -> int:
        """
        Add tracks to a playlist.

        Args:
            playlist_id: Playlist ID
            video_ids: List of YouTube video IDs
            batch_size: Number of tracks to add per API call

        Returns:
            Number of tracks successfully added
        """
        if not video_ids:
            logger.warning("No tracks to add")
            return 0

        added_count = 0

        # Add in batches
        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            try:
                # YouTube Music API requires adding tracks one by one or in specific format
                # We'll add them individually for reliability
                for video_id in batch:
                    try:
                        self.ytmusic.add_playlist_items(playlist_id, [video_id])
                        added_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to add track {video_id}: {e}")

                logger.info(f"Added batch {i // batch_size + 1} (total: {added_count})")

            except Exception as e:
                logger.error(f"Failed to add batch {i // batch_size + 1}: {e}")

        logger.info(f"Successfully added {added_count}/{len(video_ids)} tracks to playlist")
        return added_count

    def remove_all_tracks(self, playlist_id: str) -> None:
        """
        Remove all tracks from a playlist.

        Args:
            playlist_id: Playlist ID
        """
        try:
            # Get playlist contents
            playlist = self.ytmusic.get_playlist(playlist_id)
            tracks = playlist.get('tracks', [])

            if not tracks:
                logger.info("Playlist is already empty")
                return

            # Extract setVideoIds for removal
            video_ids = [track['setVideoId'] for track in tracks if 'setVideoId' in track]

            if video_ids:
                self.ytmusic.remove_playlist_items(playlist_id, video_ids)
                logger.info(f"Removed {len(video_ids)} tracks from playlist")
            else:
                logger.warning("Could not find setVideoIds for removal")

        except Exception as e:
            logger.error(f"Failed to clear playlist: {e}")

    def find_or_create_playlist(
        self,
        playlist_name: str,
        description: str = "",
        privacy_status: str = "PUBLIC",
    ) -> Optional[str]:
        """
        Find existing playlist or create a new one.

        Args:
            playlist_name: Name of the playlist
            description: Playlist description
            privacy_status: Privacy setting

        Returns:
            Playlist ID or None on failure
        """
        # Try to find existing playlist
        playlist_id = self.find_playlist(playlist_name)

        if playlist_id:
            return playlist_id

        # Create new playlist
        return self.create_playlist(playlist_name, description, privacy_status)

    def create_and_populate_playlist(
        self,
        playlist_name: str,
        video_ids: List[str],
        description: str = "",
        privacy_status: str = "PUBLIC",
        clear_existing: bool = False,
    ) -> Optional[str]:
        """
        Create (or find) a playlist and populate it with tracks.

        Args:
            playlist_name: Name of the playlist
            video_ids: List of YouTube video IDs
            description: Playlist description
            privacy_status: Privacy setting
            clear_existing: Whether to clear existing playlist before adding tracks

        Returns:
            Playlist ID or None on failure
        """
        try:
            # Find or create playlist
            playlist_id = self.find_or_create_playlist(
                playlist_name,
                description,
                privacy_status,
            )

            if not playlist_id:
                return None

            # Clear if requested
            if clear_existing:
                self.remove_all_tracks(playlist_id)

            # Add tracks
            self.add_tracks(playlist_id, video_ids)

            return playlist_id

        except Exception as e:
            logger.error(f"Failed to create/populate playlist: {e}")
            return None


def create_ytmusic_manager() -> YTMusicPlaylistManager:
    """
    Create a YTMusicPlaylistManager from environment variables.

    Returns:
        YTMusicPlaylistManager instance
    """
    return YTMusicPlaylistManager(headers_path=os.getenv('YTMUSIC_HEADERS_PATH'))
