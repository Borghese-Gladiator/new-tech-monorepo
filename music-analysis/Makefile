.PHONY: setup install test run clean format lint help

# Default target
.DEFAULT_GOAL := help

help:  ## Show this help message
	@echo "MP3 Playlist Analyzer & Normalizer"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## Set up the project (install Poetry if needed and create virtual environment)
	@echo "Setting up project..."
	@command -v poetry >/dev/null 2>&1 || { echo "Installing Poetry..."; curl -sSL https://install.python-poetry.org | python3 -; }
	poetry install
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "  1. Copy .env.example to .env and fill in your API credentials"
	@echo "  2. Set up Spotify credentials at https://developer.spotify.com/dashboard/"
	@echo "  3. Set up YouTube Music headers with: poetry run ytmusicapi oauth"
	@echo "  4. Edit data/playlist.md with your tracks"
	@echo "  5. Run: make run"

install:  ## Install dependencies with Poetry
	poetry install

test:  ## Run tests with pytest
	poetry run pytest -v

run:  ## Run the full pipeline (ingest, download, analyze, playlists)
	poetry run python -m src.cli all

ingest:  ## Parse markdown and search for tracks
	poetry run python -m src.cli ingest

download:  ## Download audio files
	poetry run python -m src.cli download

analyze:  ## Extract features and generate visualizations
	poetry run python -m src.cli analyze

playlists:  ## Create/update playlists on Spotify and YouTube Music
	poetry run python -m src.cli playlists

clean:  ## Clean up generated files and caches
	rm -rf outputs/
	rm -rf data/track_manifest.parquet
	rm -rf data/audio_raw/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

format:  ## Format code with black
	poetry run black src/ tests/

lint:  ## Run linters (ruff and mypy)
	poetry run ruff check src/ tests/
	poetry run mypy src/

check:  ## Run format, lint, and test
	$(MAKE) format
	$(MAKE) lint
	$(MAKE) test

ytmusic-setup:  ## Set up YouTube Music OAuth headers
	@echo "Follow the instructions to authenticate with YouTube Music..."
	poetry run ytmusicapi oauth

spotify-info:  ## Show Spotify setup information
	@echo "Spotify API Setup:"
	@echo "  1. Go to https://developer.spotify.com/dashboard/"
	@echo "  2. Create a new app"
	@echo "  3. Add http://localhost:8888/callback as a Redirect URI"
	@echo "  4. Copy Client ID and Client Secret to .env file"
	@echo ""
	@echo "Required .env variables:"
	@echo "  SPOTIFY_CLIENT_ID=..."
	@echo "  SPOTIFY_CLIENT_SECRET=..."
	@echo "  SPOTIFY_REDIRECT_URI=http://localhost:8888/callback"
	@echo "  SPOTIFY_USERNAME=your_spotify_username"
