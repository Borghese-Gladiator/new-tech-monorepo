"""
Audio feature extraction using librosa.

Extracts comprehensive audio features including:
- Temporal features (duration, tempo, beats)
- Loudness/dynamics (RMS energy, dynamic range)
- Timbre/spectral features (MFCCs, centroid, bandwidth, rolloff, flatness, contrast)
- Harmonic/pitch features (chroma, tonnetz)
"""
from pathlib import Path
from typing import Dict, Optional

import librosa
import numpy as np
from loguru import logger


def extract_features(
    audio_path: str,
    n_mfcc: int = 13,
    spectral_rolloff_pct: float = 0.85,
    spectral_contrast_bands: int = 7,
) -> Optional[Dict]:
    """
    Extract comprehensive audio features from an audio file.

    Args:
        audio_path: Path to audio file
        n_mfcc: Number of MFCC coefficients
        spectral_rolloff_pct: Spectral rolloff percentage (0-1)
        spectral_contrast_bands: Number of spectral contrast bands

    Returns:
        Dictionary of features or None on failure
    """
    try:
        # Load audio file
        y, sr = librosa.load(audio_path, sr=None, mono=True)

        if len(y) < sr:  # Less than 1 second
            logger.warning(f"Audio too short: {audio_path}")
            return None

        duration = len(y) / sr
        logger.debug(f"Analyzing {audio_path} ({duration:.1f}s @ {sr}Hz)")

        features = {
            'filename': Path(audio_path).name,
            'path': audio_path,
            'samplerate': sr,
            'duration_sec': duration,
        }

        # Extract all features
        _extract_temporal_features(y, sr, features)
        _extract_loudness_features(y, sr, features)
        _extract_spectral_features(
            y, sr, features, n_mfcc, spectral_rolloff_pct, spectral_contrast_bands
        )
        _extract_harmonic_features(y, sr, features)

        logger.debug(f"Extracted {len(features)} features from {Path(audio_path).name}")
        return features

    except Exception as e:
        logger.error(f"Feature extraction failed for {audio_path}: {e}")
        return None


def _extract_temporal_features(y: np.ndarray, sr: int, features: Dict) -> None:
    """Extract temporal features: tempo, beats."""
    # Tempo and beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    features['tempo_bpm'] = float(tempo)
    features['beats_count'] = len(beat_frames)

    # Beat strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    features['beat_strength_mean'] = float(np.mean(onset_env))


def _extract_loudness_features(y: np.ndarray, sr: int, features: Dict) -> None:
    """Extract loudness and dynamics features: RMS energy, dynamic range, ZCR."""
    # RMS energy
    rms = librosa.feature.rms(y=y)[0]
    features['rms_mean'] = float(np.mean(rms))
    features['rms_std'] = float(np.std(rms))
    features['rms_median'] = float(np.median(rms))
    features['rms_q25'] = float(np.percentile(rms, 25))
    features['rms_q75'] = float(np.percentile(rms, 75))

    # Dynamic range (in dB)
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    features['dynamic_range_db'] = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    # Zero crossing rate
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features['zcr_mean'] = float(np.mean(zcr))
    features['zcr_std'] = float(np.std(zcr))
    features['zcr_median'] = float(np.median(zcr))
    features['zcr_q25'] = float(np.percentile(zcr, 25))
    features['zcr_q75'] = float(np.percentile(zcr, 75))


def _extract_spectral_features(
    y: np.ndarray,
    sr: int,
    features: Dict,
    n_mfcc: int,
    spectral_rolloff_pct: float,
    spectral_contrast_bands: int,
) -> None:
    """Extract spectral features: MFCCs, centroid, bandwidth, rolloff, flatness, contrast."""
    # MFCCs
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    for i in range(n_mfcc):
        mfcc_coeffs = mfccs[i]
        features[f'mfcc{i}_mean'] = float(np.mean(mfcc_coeffs))
        features[f'mfcc{i}_std'] = float(np.std(mfcc_coeffs))
        features[f'mfcc{i}_median'] = float(np.median(mfcc_coeffs))
        features[f'mfcc{i}_q25'] = float(np.percentile(mfcc_coeffs, 25))
        features[f'mfcc{i}_q75'] = float(np.percentile(mfcc_coeffs, 75))

    # Spectral centroid
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features['spectral_centroid_mean'] = float(np.mean(centroid))
    features['spectral_centroid_std'] = float(np.std(centroid))
    features['spectral_centroid_median'] = float(np.median(centroid))
    features['spectral_centroid_q25'] = float(np.percentile(centroid, 25))
    features['spectral_centroid_q75'] = float(np.percentile(centroid, 75))

    # Spectral bandwidth
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
    features['spectral_bandwidth_mean'] = float(np.mean(bandwidth))
    features['spectral_bandwidth_std'] = float(np.std(bandwidth))
    features['spectral_bandwidth_median'] = float(np.median(bandwidth))
    features['spectral_bandwidth_q25'] = float(np.percentile(bandwidth, 25))
    features['spectral_bandwidth_q75'] = float(np.percentile(bandwidth, 75))

    # Spectral rolloff
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=spectral_rolloff_pct)[0]
    features['spectral_rolloff_mean'] = float(np.mean(rolloff))
    features['spectral_rolloff_std'] = float(np.std(rolloff))
    features['spectral_rolloff_median'] = float(np.median(rolloff))
    features['spectral_rolloff_q25'] = float(np.percentile(rolloff, 25))
    features['spectral_rolloff_q75'] = float(np.percentile(rolloff, 75))

    # Spectral flatness
    flatness = librosa.feature.spectral_flatness(y=y)[0]
    features['spectral_flatness_mean'] = float(np.mean(flatness))
    features['spectral_flatness_std'] = float(np.std(flatness))
    features['spectral_flatness_median'] = float(np.median(flatness))
    features['spectral_flatness_q25'] = float(np.percentile(flatness, 25))
    features['spectral_flatness_q75'] = float(np.percentile(flatness, 75))

    # Spectral contrast
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, n_bands=spectral_contrast_bands)
    for i in range(contrast.shape[0]):
        band_values = contrast[i]
        features[f'spectral_contrast_band{i}_mean'] = float(np.mean(band_values))
        features[f'spectral_contrast_band{i}_std'] = float(np.std(band_values))


def _extract_harmonic_features(y: np.ndarray, sr: int, features: Dict) -> None:
    """Extract harmonic/pitch features: chroma, tonnetz."""
    # Chroma (12 pitch classes)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    for i in range(12):
        features[f'chroma_{i}'] = float(np.mean(chroma[i]))

    # Tonnetz (tonal centroid features)
    tonnetz = librosa.feature.tonnetz(y=y, sr=sr)
    for i in range(6):
        features[f'tonnetz_{i}_mean'] = float(np.mean(tonnetz[i]))
        features[f'tonnetz_{i}_std'] = float(np.std(tonnetz[i]))


def extract_features_batch(
    audio_paths: list,
    n_mfcc: int = 13,
    spectral_rolloff_pct: float = 0.85,
    spectral_contrast_bands: int = 7,
) -> list:
    """
    Extract features from multiple audio files.

    Args:
        audio_paths: List of paths to audio files
        n_mfcc: Number of MFCC coefficients
        spectral_rolloff_pct: Spectral rolloff percentage
        spectral_contrast_bands: Number of spectral contrast bands

    Returns:
        List of feature dictionaries
    """
    features_list = []

    for i, audio_path in enumerate(audio_paths, 1):
        logger.info(f"[{i}/{len(audio_paths)}] Extracting features from {Path(audio_path).name}")

        features = extract_features(
            audio_path,
            n_mfcc=n_mfcc,
            spectral_rolloff_pct=spectral_rolloff_pct,
            spectral_contrast_bands=spectral_contrast_bands,
        )

        if features:
            features_list.append(features)
        else:
            logger.warning(f"Skipping {audio_path} due to extraction failure")

    logger.info(f"Extracted features from {len(features_list)}/{len(audio_paths)} files")
    return features_list
