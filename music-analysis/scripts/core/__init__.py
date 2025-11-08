"""MP3 Playlist Analyzer & Normalizer - Core Modules"""

__version__ = "0.1.0"

# Export core modules for easy importing
from . import utils
from . import audio_features
from . import downloader
from . import md_parser
from . import playlist_spotify
from . import playlist_ytmusic
from . import search_match
from . import visualize

__all__ = [
    'utils',
    'audio_features',
    'downloader',
    'md_parser',
    'playlist_spotify',
    'playlist_ytmusic',
    'search_match',
    'visualize',
]
