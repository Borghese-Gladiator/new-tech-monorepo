"""
Pytest configuration and fixtures.
"""
import numpy as np
import pytest
from pathlib import Path
import scipy.io.wavfile as wavfile


@pytest.fixture(scope="session")
def short_audio_fixture(tmp_path_factory):
    """
    Create a short audio file for testing.

    Generates a 2-second sine wave at 440 Hz.
    """
    # Create temp directory for fixtures
    fixtures_dir = tmp_path_factory.mktemp("fixtures")
    audio_path = fixtures_dir / "short.wav"

    # Generate 2 seconds of 440 Hz sine wave
    sample_rate = 22050
    duration = 2.0
    frequency = 440.0

    t = np.linspace(0, duration, int(sample_rate * duration))
    signal = np.sin(2 * np.pi * frequency * t)

    # Normalize to 16-bit PCM range
    signal = (signal * 32767).astype(np.int16)

    # Write WAV file
    wavfile.write(str(audio_path), sample_rate, signal)

    return str(audio_path)
