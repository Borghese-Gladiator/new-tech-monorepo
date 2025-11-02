# MP3 Playlist Analyzer & Normalizer

A comprehensive Python toolkit for building, analyzing, and managing music playlists across Spotify and YouTube Music platforms. Features audio feature extraction using librosa, automatic playlist creation, and rich visualizations.

## Features

- 📝 **Markdown-based playlist input** - Simple text format for track lists
- 🔍 **Multi-platform search** - Find tracks on Spotify and YouTube Music
- 📥 **Audio download** - Fetch high-quality MP3s from YouTube/YouTube Music
- 🎵 **Audio analysis** - Extract 100+ audio features using librosa
- 📊 **Visualizations** - Generate insightful charts (PCA, correlations, spectral analysis)
- 🎼 **Playlist sync** - Create synchronized playlists on Spotify and YouTube Music
- 🔊 **Loudness normalization** - Optional LUFS-based audio normalization
- 🔄 **Deduplication** - Smart fuzzy matching to avoid duplicate tracks

## Requirements

- Python 3.10+
- ffmpeg (for audio processing)
- Poetry (for dependency management)
- Spotify API credentials
- YouTube Music account (for playlist management)

## Installation

### 1. Install system dependencies

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt-get install ffmpeg
```

#### Windows
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### 2. Clone and setup

```bash
cd mp3-analyzer
make setup
```

This will:
- Install Poetry (if not already installed)
- Create a virtual environment
- Install all Python dependencies

### 3. Configure API credentials

#### Spotify Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add `http://localhost:8888/callback` as a Redirect URI
4. Copy your Client ID and Client Secret

Create a `.env` file from the template:
```bash
cp .env.example .env
```

Edit `.env` and fill in your Spotify credentials:
```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_USERNAME=your_spotify_username
```

#### YouTube Music Setup

Authenticate with YouTube Music:
```bash
make ytmusic-setup
# or
poetry run ytmusicapi oauth
```

This will:
1. Open a browser window for authentication
2. Save your credentials to `./secrets/ytmusic_headers.json`

Update `.env` with the headers path:
```env
YTMUSIC_HEADERS_PATH=./secrets/ytmusic_headers.json
```

## Usage

### Quick Start

1. Edit `data/playlist.md` with your tracks:

```markdown
# My Playlist

- Daft Punk – Digital Love [album: Discovery]
- Nujabes - Luv(sic) pt3 (feat. Shing02)
- https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp
- Kavinsky – Nightcall
```

2. Run the full pipeline:

```bash
make run
```

This will:
- Parse the markdown file
- Search for tracks on Spotify and YouTube Music
- Download audio files
- Extract audio features
- Generate visualizations
- Create playlists on both platforms

### Individual Commands

Run specific stages of the pipeline:

```bash
# Parse markdown and search for tracks
poetry run python -m src.cli ingest

# Download audio files
poetry run python -m src.cli download

# Extract features and generate visualizations
poetry run python -m src.cli analyze

# Create/update playlists
poetry run python -m src.cli playlists

# Run everything
poetry run python -m src.cli all
```

Or use the Makefile shortcuts:

```bash
make ingest      # Parse and search
make download    # Download audio
make analyze     # Extract features
make playlists   # Create playlists
make run         # Full pipeline
```

### Command Options

```bash
# Force re-processing
poetry run python -m src.cli all --force

# Clear existing playlists before adding tracks
poetry run python -m src.cli playlists --clear

# Use custom config file
poetry run python -m src.cli all --config custom_settings.yaml
```

## Markdown Format

The input markdown file supports multiple track formats:

### Artist - Title Format
```markdown
- Daft Punk – Digital Love
- Artist - Title (feat. Guest)
```

### With Metadata Hints
```markdown
- Daft Punk – Digital Love [album: Discovery]
- Nujabes – Luv(sic) pt3 [note: amazing track]
```

### Direct URLs
```markdown
- https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp
- https://music.youtube.com/watch?v=xxxxxxxxxxx
- https://www.youtube.com/watch?v=xxxxxxxxxxx
```

### Local Files
```markdown
- /path/to/local/file.mp3
```

### Markdown Lists
```markdown
- [ ] Track with checkbox
- [x] Completed track
* Bullet point
- Regular dash
```

## Audio Features

The analyzer extracts 100+ audio features per track:

### Temporal Features
- **Duration** - Track length in seconds
- **Tempo** - BPM (beats per minute)
- **Beat count** - Number of detected beats
- **Beat strength** - Average onset strength

### Loudness & Dynamics
- **RMS energy** - Root mean square energy (mean, std, median, quartiles)
- **Dynamic range** - Loudness variation in dB
- **Zero crossing rate** - Frequency of signal sign changes

### Timbre & Spectral Features
- **MFCCs** - 13 Mel-frequency cepstral coefficients (mean, std, median, quartiles each)
- **Spectral centroid** - "Brightness" of sound (mean, std, median, quartiles)
- **Spectral bandwidth** - Frequency range (mean, std, median, quartiles)
- **Spectral rolloff** - Frequency below which 85% of energy is contained
- **Spectral flatness** - Measure of noisiness vs. tonality
- **Spectral contrast** - Difference between peaks and valleys across 7 frequency bands

### Harmonic & Pitch Features
- **Chroma** - 12 pitch class intensities (C, C#, D, ...)
- **Tonnetz** - 6-dimensional tonal centroid features

All features are aggregated per track and saved to `outputs/audio_features.csv`.

## Visualizations

The analyzer generates the following charts in `outputs/figures/`:

1. **`hist_tempo_bpm.png`** - Distribution of track tempos
2. **`scatter_centroid_vs_bandwidth.png`** - Spectral brightness vs. bandwidth
3. **`correlation_heatmap.png`** - Feature correlation matrix
4. **`pca_tracks.png`** - 2D PCA visualization of track similarity
5. **`boxplot_mfcc_means.png`** - Distribution of MFCC coefficients

## Configuration

Edit `settings.yaml` to customize behavior:

```yaml
# Input/Output
input_markdown: ./data/playlist.md
audio_out_dir: ./outputs/audio
features_csv: ./outputs/audio_features.csv
failed_log: ./outputs/failed_inputs.txt

# Processing
max_items: 100
fuzzy_threshold: 80  # Minimum match score (0-100)

# Audio
target_lufs: -14.0  # Loudness normalization target
mp3_bitrate: 320    # kbps

# Playlists
target_playlist_name: "Normalized Mix"
yt_search_filter: "songs"  # or "videos"

# Feature extraction
n_mfcc: 13
spectral_rolloff_pct: 0.85

# Visualization
figure_dpi: 150
tempo_bins: 30
```

## Project Structure

```
mp3-analyzer/
├── src/
│   ├── cli.py                 # Main CLI entry point
│   ├── md_parser.py           # Markdown parser
│   ├── search_match.py        # Track search & matching
│   ├── downloader.py          # Audio download (yt-dlp)
│   ├── features.py            # Feature extraction (librosa)
│   ├── visualize.py           # Chart generation (matplotlib)
│   ├── playlist_spotify.py    # Spotify playlist management
│   ├── playlist_ytmusic.py    # YouTube Music playlist management
│   └── utils.py               # Utilities (logging, normalization)
├── tests/
│   ├── test_md_parser.py      # Parser tests
│   ├── test_dedupe.py         # Deduplication tests
│   └── test_features.py       # Feature extraction tests
├── data/
│   └── playlist.md            # Input track list
├── outputs/
│   ├── audio/                 # Downloaded MP3s
│   ├── figures/               # Generated charts
│   ├── audio_features.csv     # Feature data
│   └── failed_inputs.txt      # Tracks that failed
├── secrets/
│   └── ytmusic_headers.json   # YouTube Music auth
├── settings.yaml              # Configuration
├── .env                       # API credentials
├── pyproject.toml            # Poetry dependencies
├── Makefile                   # Build targets
└── README.md                  # This file
```

## Development

### Run tests

```bash
make test
```

### Format code

```bash
make format
```

### Run linters

```bash
make lint
```

### Clean generated files

```bash
make clean
```

## Troubleshooting

### ffmpeg not found
```
Error: ffmpeg is required but not installed
```
**Solution**: Install ffmpeg (see Installation section)

### Spotify authentication fails
```
Error: Spotify credentials not provided
```
**Solution**: Check that `.env` file exists and contains valid credentials

### YouTube Music 403 errors
```
Error: Failed to search YouTube Music: 403
```
**Solution**: Re-run `make ytmusic-setup` to refresh authentication

### No tracks found
```
Error: No tracks found in markdown file
```
**Solution**: Check that `data/playlist.md` exists and contains valid track entries

### Rate limiting
If you hit API rate limits:
- Reduce `max_items` in `settings.yaml`
- Add delays between requests (will be implemented in future version)
- Use direct URLs instead of search queries

## Advanced Usage

### Loudness Normalization

Enable LUFS-based loudness normalization:

```yaml
# settings.yaml
target_lufs: -14.0  # Target loudness in LUFS
```

This applies 2-pass loudnorm filter during download/conversion.

### Custom Search Filters

For YouTube Music, choose search filter:

```yaml
yt_search_filter: "songs"   # More specific, music-only
# or
yt_search_filter: "videos"  # Broader, includes music videos
```

### Fuzzy Matching Threshold

Adjust matching sensitivity:

```yaml
fuzzy_threshold: 80   # Stricter (fewer false positives)
fuzzy_threshold: 60   # Looser (more matches)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run `make check` to verify
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [librosa](https://librosa.org/) - Audio analysis
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Audio download
- [spotipy](https://spotipy.readthedocs.io/) - Spotify API
- [ytmusicapi](https://ytmusicapi.readthedocs.io/) - YouTube Music API

## Support

For issues, questions, or suggestions, please open an issue on GitHub.
