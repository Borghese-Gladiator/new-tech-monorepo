# Music Analysis Pipeline

A comprehensive Python toolkit for extracting, normalizing, and analyzing music playlists from git history. Features YouTube Music integration, audio download with yt-dlp, and audio analysis with librosa.

## Features

- 📝 **Git History Extraction** - Extract music entries from commit history across repositories
- 🧹 **Smart Normalization** - Clean and standardize track names to "Artist - Title" format
- 🔍 **YouTube Music Search** - Find video IDs for tracks (with rate limiting)
- 📥 **Audio Download** - Download high-quality MP3s (320kbps) with exponential backoff
- 🎵 **Audio Analysis** - Extract 100+ audio features using librosa
- 📊 **Visualizations** - Generate insightful charts (PCA, correlations, spectral analysis)
- 🔄 **Resume Capability** - All scripts support interruption and resume

## Pipeline Overview

```
01_preprocess/          → Extract and normalize track names
  A_extract_lines.py       ⚙️  Extract from git history
  B_normalize_tracks_to_csv.py  ⚙️  Clean to "Artist - Title" format

02_create/              → Search for video IDs
  A_get_ids_for_ytmusic.py  ⚠️  API CALLS - YouTube Music search
  B_build_playlists_ytmusic.py  ⚠️  API CALLS - Create playlists

03_download/            → Download audio files
  download_audio_yt.py     🔐 Requires browser cookies

04_analyze/             → Extract features and visualize
  (Coming soon)

Legend:
  ⚙️  No API calls - safe to run repeatedly
  ⚠️  Makes API calls - rate limited
  🔐 Requires authentication
```

## Requirements

- Python 3.10+
- ffmpeg (for audio processing)
- Poetry (for dependency management)
- YouTube account (for downloading)
- YouTube Music browser.json (for ID search)

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
cd music-analysis
poetry install
```

### 3. Configure authentication

#### YouTube Music Setup (for ID search)

Generate browser authentication file:

```bash
# Open YouTube Music in Chrome: https://music.youtube.com
# Open DevTools (F12) → Network tab
# Filter by 'browse' and click any request
# Right-click → Copy → Copy as cURL
# Then run:
poetry run ytmusicapi browser

# This creates browser.json in your directory
```

Update `.env`:
```bash
cp .env.example .env
# Edit .env and set:
YTMUSIC_HEADERS_PATH=./browser.json
```

#### Browser Cookies (for downloading)

**You must be signed in to YouTube in your browser**. The download script will automatically extract cookies from your browser (Chrome by default).

No additional setup needed - just stay signed in!

## Usage

### Stage 1: Extract from Git History

Extract music entries from git commit history:

```bash
poetry run python scripts/01_preprocess/A_extract_lines.py
```

**Output:** `data/01_A_extracted_music_by_year.md`

### Stage 2: Normalize Track Names

Clean and standardize track names to CSV format:

```bash
poetry run python scripts/01_preprocess/B_normalize_tracks_to_csv.py
```

**Output:**
- `data/01_B_normalized_tracks.csv` (track_name, year, language)
- `data/01_B_unrecognized.txt`

⚙️ **No API calls** - Safe to run multiple times

### Stage 3: Search YouTube Music (⚠️ API Calls)

Search for video IDs on YouTube Music:

```bash
poetry run python scripts/02_create/A_get_ids_for_ytmusic.py
```

**Output:**
- `data/02_A_ytmusic_track_ids.csv` (track_name, video_id)
- `data/02_A_ytmusic_failed_tracks.txt`

⚠️ **Makes API calls:**
- Rate limited: ~1-2 requests/second
- Takes ~30 minutes for 1,700 tracks
- **Resume capability**: Skips already-found tracks
- Safe to interrupt and re-run

### Stage 4: Download Audio (🔐 Requires Browser)

Download MP3s from YouTube:

```bash
# Test with 5 tracks
poetry run python scripts/03_download/download_audio_yt.py --max 5

# Full download (default 3s delay between tracks)
poetry run python scripts/03_download/download_audio_yt.py

# More conservative (5s delay)
poetry run python scripts/03_download/download_audio_yt.py --delay 5

# Use different browser for cookies
poetry run python scripts/03_download/download_audio_yt.py --browser firefox
```

**Output:** `data/03_downloaded_audio/Artist - Title [VIDEO_ID].mp3`

🔐 **Requirements:**
- Must be signed in to YouTube in browser (Chrome/Firefox/Safari/Edge)
- Automatically extracts cookies from browser
- Keep browser running while downloading

**Features:**
- 320kbps MP3 quality
- Exponential backoff (adapts to rate limiting)
- Resume capability (skips existing files)
- 5-minute timeout per track

**Options:**
- `--max N` - Download only first N tracks (for testing)
- `--delay N` - Base delay in seconds (default: 3.0)
- `--browser BROWSER` - Browser to extract cookies from (default: chrome)
- `--force` - Re-download existing files

See [`scripts/03_download/README.md`](scripts/03_download/README.md) for detailed documentation.

## Data Flow

```
Git History (2+ repos)
    ↓
[A_extract_lines.py]  ⚙️
    ↓
01_A_extracted_music_by_year.md
    ↓
[B_normalize_tracks_to_csv.py]  ⚙️
    ↓
01_B_normalized_tracks.csv (track_name, year, language)
    ↓
[A_get_ids_for_ytmusic.py]  ⚠️  API CALLS
    ↓
02_A_ytmusic_track_ids.csv (track_name, video_id)
    ↓
[download_audio_yt.py]  🔐 Browser cookies
    ↓
03_downloaded_audio/*.mp3
    ↓
[analyze_features.py] (future)
    ↓
04_features.csv
```

## Project Structure

```
music-analysis/
├── scripts/
│   ├── 01_preprocess/
│   │   ├── A_extract_lines.py           # Extract from git history
│   │   └── B_normalize_tracks_to_csv.py # Normalize to CSV (⚙️ no API)
│   ├── 02_create/
│   │   ├── A_get_ids_for_ytmusic.py     # Search YouTube Music (⚠️ API)
│   │   └── B_build_playlists_ytmusic.py # Create playlists (⚠️ API)
│   ├── 03_download/
│   │   ├── download_audio_yt.py         # Download MP3s (🔐 browser)
│   │   └── README.md                    # Detailed docs
│   ├── core/
│   │   ├── downloader.py                # yt-dlp wrapper
│   │   ├── playlist_ytmusic.py          # YouTube Music API
│   │   └── utils.py                     # Utilities
│   └── 04_analyze/ (future)
├── data/
│   ├── 01_A_extracted_music_by_year.md       # Git extraction output
│   ├── 01_B_normalized_tracks.csv            # Normalized tracks
│   ├── 01_B_unrecognized.txt                 # Failed to parse
│   ├── 02_A_ytmusic_track_ids.csv            # Video IDs
│   ├── 02_A_ytmusic_failed_tracks.txt        # Search failures
│   └── 03_downloaded_audio/                  # MP3 files
├── outputs/
│   ├── figures/                              # Visualizations
│   └── run.log                               # Execution logs
├── logs/                                     # Script logs
├── settings.yaml                             # Configuration
├── .env                                      # API credentials
├── browser.json                              # YouTube Music auth
├── pyproject.toml                            # Poetry dependencies
├── SCRIPT_ORGANIZATION.md                    # Reorganization suggestions
└── README.md                                 # This file
```

## Configuration

Edit `settings.yaml` to customize behavior:

```yaml
# Input/Output paths
input_markdown: ./data/01_B_cleaned_playlist.md
ytmusic_manifest_path: ./data/02_A_ytmusic_track_manifest.parquet
ytmusic_playlist_name: "YT Music Normalized Mix"
audio_out_dir: ./data/03_downloaded_audio
run_log: ./outputs/run.log

# Audio processing
mp3_bitrate: 320  # kbps
target_lufs: -14.0  # Loudness normalization (optional)

# Search/matching
fuzzy_threshold: 80  # Minimum match score (0-100)
max_search_candidates: 5

# Feature extraction (future)
n_mfcc: 13
sample_rate: null  # Use native sample rate
```

## Troubleshooting

### "ffmpeg not found"
```
ERROR: ffmpeg is required but not installed
```
**Solution:** Install ffmpeg (see Installation section)

### YouTube Download Failures
```
ERROR: Sign in to confirm you're not a bot
ERROR: HTTP Error 400: Bad Request
```

**Solutions:**
1. Make sure you're signed in to YouTube in your browser
2. Keep your browser running while downloading
3. Try a different browser: `--browser firefox`
4. Update yt-dlp: `poetry run pip install --upgrade yt-dlp`

### YouTube Music Search Failures
```
ERROR: Failed to initialize YouTube Music client
```

**Solution:** Regenerate browser.json:
```bash
poetry run ytmusicapi browser
# Follow the prompts to paste cURL command
```

### Rate Limiting

If downloads are too fast:
```bash
# Increase delay to 5 seconds
poetry run python scripts/03_download/download_audio_yt.py --delay 5
```

If YouTube Music search hits limits:
- The script already includes delays
- Safe to interrupt and re-run (resumes from where it left off)
- Results are cached

## Advanced Usage

### Resume After Interruption

All scripts support resume:

**Download script:**
```bash
# Interrupted? Just re-run - it skips existing files
poetry run python scripts/03_download/download_audio_yt.py
```

**YouTube Music search:**
```bash
# Interrupted? Re-run - it skips tracks already found
poetry run python scripts/02_create/A_get_ids_for_ytmusic.py
```

### Exponential Backoff

The download script automatically adapts to rate limiting:
- **Base delay:** 3 seconds (configurable with `--delay`)
- **On failure:** Delay doubles (up to 48s max)
- **On success:** Delay reduces by 10%
- Automatically backs off if YouTube starts rejecting requests

### Custom Browser

Use cookies from a different browser:

```bash
poetry run python scripts/03_download/download_audio_yt.py --browser safari
```

Supported browsers: `chrome`, `firefox`, `safari`, `edge`

## Development

### Run tests
```bash
poetry run pytest
```

### Format code
```bash
poetry run black .
poetry run isort .
```

### Clean generated files
```bash
rm -rf data/03_downloaded_audio/*
rm -rf outputs/*
```

## Known Issues

1. **YouTube Music search** sometimes returns incorrect matches
   - Manually review `02_A_ytmusic_failed_tracks.txt`
   - Edit CSV to add missing video IDs

2. **Download script** may fail on age-restricted content
   - These tracks are skipped
   - Check logs for details

3. **Some tracks use en dash (–) instead of hyphen (-)**
   - B_normalize_tracks_to_csv.py handles most cases
   - Check `01_B_unrecognized.txt` for edge cases

## Future Enhancements

See [SCRIPT_ORGANIZATION.md](SCRIPT_ORGANIZATION.md) for proposed improvements:
- Reorganize script structure for clarity
- Add CSV format everywhere
- Mark API-calling scripts explicitly
- Better error handling and logging

## License

MIT License - see LICENSE file for details

## Acknowledgments

- [librosa](https://librosa.org/) - Audio analysis
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Audio download
- [ytmusicapi](https://ytmusicapi.readthedocs.io/) - YouTube Music API
- [loguru](https://github.com/Delgan/loguru) - Logging

## Support

For issues or questions, please open an issue on GitHub.
