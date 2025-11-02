# YouTube Music Playlist
I have a text file with like 1500~ songs. This folder holds scripts to find the songs, add them to playlists, and download them.

- script to build YouTube Music playlist
- script to build Spotify playlist
- script to download all the songs from YouTube

## Notes
First time using `uv` to handle dependencies for my Python project

Setup
- uv installation
  ```
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  ```
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- `uv venv`
- `venv\Scripts\activate`
- `uv init yt-music-playlist`

Dependencies
- `uv add ruff`
- `uv run ruff check` -> run check
- `uv add --dev pytest`

Run Code (generated from ChatGPT)
- `uv run python build_ytmusic_playlist.py`
- `uv run python build_spotify_playlist.py`
- `uv run python download_from_youtube.py   # downloads audio to ./downloads/`

Run Tests
- `venv\Scripts\activate && pytest`
