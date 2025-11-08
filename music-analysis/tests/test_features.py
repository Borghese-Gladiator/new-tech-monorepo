"""
Tests for audio feature extraction.
"""
import pytest
from scripts.core.audio_features import extract_features


def test_extract_features_basic(short_audio_fixture):
    """Test basic feature extraction."""
    features = extract_features(short_audio_fixture)

    assert features is not None
    assert 'filename' in features
    assert 'duration_sec' in features
    assert 'samplerate' in features


def test_extract_features_temporal(short_audio_fixture):
    """Test temporal features extraction."""
    features = extract_features(short_audio_fixture)

    assert 'tempo_bpm' in features
    assert 'beats_count' in features
    assert 'beat_strength_mean' in features

    assert features['tempo_bpm'] > 0
    assert features['beats_count'] >= 0


def test_extract_features_loudness(short_audio_fixture):
    """Test loudness features extraction."""
    features = extract_features(short_audio_fixture)

    # RMS features
    assert 'rms_mean' in features
    assert 'rms_std' in features
    assert 'rms_median' in features
    assert 'rms_q25' in features
    assert 'rms_q75' in features

    # Dynamic range
    assert 'dynamic_range_db' in features

    # ZCR features
    assert 'zcr_mean' in features


def test_extract_features_spectral(short_audio_fixture):
    """Test spectral features extraction."""
    features = extract_features(short_audio_fixture)

    # MFCCs
    for i in range(13):
        assert f'mfcc{i}_mean' in features
        assert f'mfcc{i}_std' in features
        assert f'mfcc{i}_median' in features
        assert f'mfcc{i}_q25' in features
        assert f'mfcc{i}_q75' in features

    # Spectral features
    assert 'spectral_centroid_mean' in features
    assert 'spectral_bandwidth_mean' in features
    assert 'spectral_rolloff_mean' in features
    assert 'spectral_flatness_mean' in features

    # Spectral contrast
    for i in range(8):  # 7 bands + 1
        assert f'spectral_contrast_band{i}_mean' in features


def test_extract_features_harmonic(short_audio_fixture):
    """Test harmonic features extraction."""
    features = extract_features(short_audio_fixture)

    # Chroma
    for i in range(12):
        assert f'chroma_{i}' in features

    # Tonnetz
    for i in range(6):
        assert f'tonnetz_{i}_mean' in features
        assert f'tonnetz_{i}_std' in features


def test_extract_features_values_valid(short_audio_fixture):
    """Test that extracted feature values are valid (not NaN/Inf)."""
    features = extract_features(short_audio_fixture)

    import math

    for key, value in features.items():
        if isinstance(value, (int, float)):
            assert not math.isnan(value), f"{key} is NaN"
            assert not math.isinf(value), f"{key} is Inf"


def test_extract_features_nonexistent_file():
    """Test feature extraction with nonexistent file."""
    features = extract_features("/nonexistent/file.wav")
    assert features is None
