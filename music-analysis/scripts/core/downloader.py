"""
Audio downloader and converter using yt-dlp and ffmpeg.

Downloads audio from YouTube/YouTube Music and converts to MP3 with optional loudness normalization.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from .utils import ensure_dir, sanitize_filename


class AudioDownloader:
    """Downloads and converts audio files."""

    def __init__(
        self,
        output_dir: str = "./data/03_downloaded_audio",
        bitrate: int = 320,
        target_lufs: Optional[float] = None,
    ):
        """
        Initialize the audio downloader.

        Args:
            output_dir: Directory to save MP3 files
            bitrate: MP3 bitrate in kbps
            target_lufs: Target LUFS for loudness normalization (None to disable)
        """
        self.output_dir = ensure_dir(output_dir)
        self.bitrate = bitrate
        self.target_lufs = target_lufs

        # Check for required tools
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check if yt-dlp and ffmpeg are installed."""
        try:
            subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                check=True,
            )
            logger.debug("yt-dlp found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("yt-dlp not found. Install with: pip install yt-dlp")
            raise RuntimeError("yt-dlp is required but not installed")

        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True,
            )
            logger.debug("ffmpeg found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg not found. Install from: https://ffmpeg.org/download.html")
            raise RuntimeError("ffmpeg is required but not installed")

    def download_and_convert(
        self,
        url: str,
        artist: Optional[str] = None,
        title: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Download audio from URL and convert to MP3.

        Args:
            url: YouTube/YouTube Music URL
            artist: Artist name for filename
            title: Track title for filename
            source_id: Source video/track ID for filename

        Returns:
            Path to downloaded MP3 file or None on failure
        """
        try:
            # Generate filename
            filename = self._generate_filename(artist, title, source_id)
            output_path = self.output_dir / filename

            # Check if file already exists
            if output_path.exists():
                logger.info(f"File already exists: {output_path}")
                return str(output_path)

            logger.info(f"Downloading: {url}")

            # Download with yt-dlp
            temp_output = self.output_dir / f"temp_{filename}"
            success = self._download_audio(url, temp_output)

            if not success:
                return None

            # Apply loudness normalization if requested
            if self.target_lufs is not None:
                logger.info(f"Applying loudness normalization to {self.target_lufs} LUFS")
                success = self._normalize_loudness(temp_output, output_path)
                temp_output.unlink(missing_ok=True)  # Clean up temp file
            else:
                # No normalization, just rename temp file
                temp_output.rename(output_path)
                success = True

            if success:
                logger.info(f"Saved to: {output_path}")
                return str(output_path)

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")

        return None

    def copy_local_file(
        self,
        local_path: str,
        artist: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[str]:
        """
        Copy a local audio file to the output directory.

        Args:
            local_path: Path to local audio file
            artist: Artist name for filename
            title: Track title for filename

        Returns:
            Path to copied file or None on failure
        """
        try:
            source = Path(local_path)
            if not source.exists():
                logger.error(f"Local file not found: {local_path}")
                return None

            # Generate filename
            filename = self._generate_filename(artist, title, "local")
            output_path = self.output_dir / filename

            # Check if file already exists
            if output_path.exists():
                logger.info(f"File already exists: {output_path}")
                return str(output_path)

            # Convert to MP3 if needed
            if source.suffix.lower() != '.mp3':
                logger.info(f"Converting {local_path} to MP3")
                success = self._convert_to_mp3(source, output_path)
                if not success:
                    return None
            else:
                # Just copy the file
                import shutil
                shutil.copy2(source, output_path)

            logger.info(f"Copied to: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to copy {local_path}: {e}")

        return None

    def _generate_filename(
        self,
        artist: Optional[str],
        title: Optional[str],
        source_id: Optional[str],
    ) -> str:
        """Generate a sanitized filename."""
        parts = []

        if artist:
            parts.append(sanitize_filename(artist))

        if title:
            parts.append(sanitize_filename(title))

        if not parts:
            parts.append("unknown")

        base = " - ".join(parts)

        if source_id:
            return f"{base} [{source_id}].mp3"
        else:
            return f"{base}.mp3"

    def _download_audio(self, url: str, output_path: Path) -> bool:
        """
        Download audio using yt-dlp and convert to MP3.

        Args:
            url: Source URL
            output_path: Output file path

        Returns:
            True on success, False on failure
        """
        try:
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', f'{self.bitrate}K',
                '--output', str(output_path),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                url,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp failed: {result.stderr}")
                return False

            return output_path.exists()

        except subprocess.TimeoutExpired:
            logger.error(f"Download timeout for: {url}")
            return False
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def _convert_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        """
        Convert audio file to MP3 using ffmpeg.

        Args:
            input_path: Input audio file
            output_path: Output MP3 file

        Returns:
            True on success, False on failure
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vn',  # No video
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Stereo
                '-b:a', f'{self.bitrate}k',
                '-y',  # Overwrite output
                str(output_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg conversion failed: {result.stderr}")
                return False

            return output_path.exists()

        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return False

    def _normalize_loudness(self, input_path: Path, output_path: Path) -> bool:
        """
        Apply loudness normalization using ffmpeg loudnorm filter (2-pass).

        Args:
            input_path: Input MP3 file
            output_path: Output normalized MP3 file

        Returns:
            True on success, False on failure
        """
        try:
            # First pass: analyze
            logger.debug("Loudness normalization: first pass (analysis)")
            cmd_analyze = [
                'ffmpeg',
                '-i', str(input_path),
                '-af', f'loudnorm=I={self.target_lufs}:TP=-1.5:LRA=11:print_format=json',
                '-f', 'null',
                '-',
            ]

            result = subprocess.run(
                cmd_analyze,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse loudnorm stats from stderr
            stderr_lines = result.stderr.split('\n')
            stats_start = False
            stats_json = []

            for line in stderr_lines:
                if '[Parsed_loudnorm' in line and '{' in line:
                    stats_start = True
                    stats_json.append(line.split('{', 1)[1])
                elif stats_start:
                    stats_json.append(line)
                    if '}' in line:
                        break

            if not stats_json:
                logger.warning("Could not parse loudnorm stats, applying simple normalization")
                return self._simple_normalize(input_path, output_path)

            # Parse JSON stats
            stats_str = '{' + ''.join(stats_json)
            stats_str = stats_str[:stats_str.rfind('}')+1]
            stats = json.loads(stats_str)

            # Second pass: normalize
            logger.debug("Loudness normalization: second pass (processing)")
            cmd_normalize = [
                'ffmpeg',
                '-i', str(input_path),
                '-af', (
                    f'loudnorm=I={self.target_lufs}:TP=-1.5:LRA=11:'
                    f'measured_I={stats["input_i"]}:'
                    f'measured_LRA={stats["input_lra"]}:'
                    f'measured_TP={stats["input_tp"]}:'
                    f'measured_thresh={stats["input_thresh"]}:'
                    f'linear=true:print_format=summary'
                ),
                '-ar', '44100',
                '-b:a', f'{self.bitrate}k',
                '-y',
                str(output_path),
            ]

            result = subprocess.run(
                cmd_normalize,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"Loudness normalization failed: {result.stderr}")
                return False

            return output_path.exists()

        except Exception as e:
            logger.error(f"Loudness normalization error: {e}")
            return self._simple_normalize(input_path, output_path)

    def _simple_normalize(self, input_path: Path, output_path: Path) -> bool:
        """
        Apply simple volume normalization as fallback.

        Args:
            input_path: Input MP3 file
            output_path: Output normalized MP3 file

        Returns:
            True on success, False on failure
        """
        try:
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-af', 'loudnorm',
                '-ar', '44100',
                '-b:a', f'{self.bitrate}k',
                '-y',
                str(output_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"Simple normalization failed: {result.stderr}")
                return False

            return output_path.exists()

        except Exception as e:
            logger.error(f"Simple normalization error: {e}")
            return False


def create_downloader(config: dict) -> AudioDownloader:
    """
    Create an AudioDownloader instance from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        AudioDownloader instance
    """
    return AudioDownloader(
        output_dir=config.get('audio_out_dir', './data/03_downloaded_audio'),
        bitrate=config.get('mp3_bitrate', 320),
        target_lufs=config.get('target_lufs'),
    )
