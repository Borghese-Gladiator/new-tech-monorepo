"""
Visualization module for audio features.

Creates static matplotlib charts (one plot per figure, no custom colors).
"""
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from .utils import ensure_dir


def generate_all_visualizations(
    df: pd.DataFrame,
    output_dir: str = "./outputs/figures",
    dpi: int = 150,
    tempo_bins: int = 30,
) -> None:
    """
    Generate all visualization charts.

    Args:
        df: DataFrame with audio features
        output_dir: Directory to save figures
        dpi: Figure DPI
        tempo_bins: Number of bins for tempo histogram
    """
    ensure_dir(output_dir)
    output_path = Path(output_dir)

    logger.info("Generating visualizations...")

    # 1. Histogram of tempo
    plot_tempo_histogram(df, output_path / "hist_tempo_bpm.png", dpi, tempo_bins)

    # 2. Scatter: spectral centroid vs bandwidth
    plot_centroid_vs_bandwidth(df, output_path / "scatter_centroid_vs_bandwidth.png", dpi)

    # 3. Correlation heatmap
    plot_correlation_heatmap(df, output_path / "correlation_heatmap.png", dpi)

    # 4. PCA 2D scatter
    plot_pca_tracks(df, output_path / "pca_tracks.png", dpi)

    # 5. Boxplot of MFCC means
    plot_mfcc_boxplot(df, output_path / "boxplot_mfcc_means.png", dpi)

    logger.info(f"Saved all visualizations to {output_dir}")


def plot_tempo_histogram(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 150,
    bins: int = 30,
) -> None:
    """
    Plot histogram of tempo (BPM).

    Args:
        df: DataFrame with audio features
        output_path: Output file path
        dpi: Figure DPI
        bins: Number of histogram bins
    """
    if 'tempo_bpm' not in df.columns:
        logger.warning("No tempo_bpm column found, skipping tempo histogram")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(df['tempo_bpm'].dropna(), bins=bins, edgecolor='black')
    plt.xlabel('Tempo (BPM)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Tempo (BPM)')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Saved: {output_path}")


def plot_centroid_vs_bandwidth(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 150,
) -> None:
    """
    Plot scatter of spectral centroid vs bandwidth.

    Args:
        df: DataFrame with audio features
        output_path: Output file path
        dpi: Figure DPI
    """
    if 'spectral_centroid_mean' not in df.columns or 'spectral_bandwidth_mean' not in df.columns:
        logger.warning("Missing spectral columns, skipping centroid vs bandwidth scatter")
        return

    plt.figure(figsize=(10, 6))
    plt.scatter(
        df['spectral_centroid_mean'],
        df['spectral_bandwidth_mean'],
        alpha=0.6,
    )
    plt.xlabel('Spectral Centroid (Hz)')
    plt.ylabel('Spectral Bandwidth (Hz)')
    plt.title('Spectral Centroid vs Bandwidth')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Saved: {output_path}")


def plot_correlation_heatmap(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 150,
) -> None:
    """
    Plot correlation heatmap of numeric features.

    Args:
        df: DataFrame with audio features
        output_path: Output file path
        dpi: Figure DPI
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.empty:
        logger.warning("No numeric columns found, skipping correlation heatmap")
        return

    # Compute correlation matrix
    corr = numeric_df.corr()

    # Plot
    plt.figure(figsize=(12, 10))
    plt.imshow(corr, aspect='auto', cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(label='Correlation')

    # Add ticks (limit to avoid overcrowding)
    max_ticks = 50
    if len(corr.columns) <= max_ticks:
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=90, fontsize=6)
        plt.yticks(range(len(corr.columns)), corr.columns, fontsize=6)
    else:
        # Show only every nth tick
        step = len(corr.columns) // max_ticks + 1
        tick_positions = list(range(0, len(corr.columns), step))
        tick_labels = [corr.columns[i] for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=90, fontsize=6)
        plt.yticks(tick_positions, tick_labels, fontsize=6)

    plt.title('Feature Correlation Matrix')
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Saved: {output_path}")


def plot_pca_tracks(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 150,
) -> None:
    """
    Plot 2D PCA of track features.

    Args:
        df: DataFrame with audio features
        output_path: Output file path
        dpi: Figure DPI
    """
    # Select only numeric columns and drop NaNs
    numeric_df = df.select_dtypes(include=[np.number]).dropna()

    if numeric_df.empty or len(numeric_df) < 2:
        logger.warning("Not enough data for PCA, skipping PCA plot")
        return

    # Standardize features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(numeric_df)

    # Apply PCA
    pca = PCA(n_components=2)
    pca_features = pca.fit_transform(scaled_features)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(pca_features[:, 0], pca_features[:, 1], alpha=0.6)
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
    plt.title('PCA of Track Features')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Saved: {output_path}")


def plot_mfcc_boxplot(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 150,
) -> None:
    """
    Plot boxplots of MFCC means.

    Args:
        df: DataFrame with audio features
        output_path: Output file path
        dpi: Figure DPI
    """
    # Find all MFCC mean columns
    mfcc_cols = [col for col in df.columns if col.startswith('mfcc') and col.endswith('_mean')]

    if not mfcc_cols:
        logger.warning("No MFCC mean columns found, skipping MFCC boxplot")
        return

    # Sort columns numerically
    mfcc_cols = sorted(mfcc_cols, key=lambda x: int(x.replace('mfcc', '').replace('_mean', '')))

    # Prepare data for boxplot
    mfcc_data = [df[col].dropna().values for col in mfcc_cols]

    # Create labels (e.g., "0", "1", "2", ...)
    labels = [col.replace('mfcc', '').replace('_mean', '') for col in mfcc_cols]

    plt.figure(figsize=(12, 6))
    plt.boxplot(mfcc_data, labels=labels)
    plt.xlabel('MFCC Coefficient')
    plt.ylabel('Mean Value')
    plt.title('Distribution of MFCC Means Across Tracks')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    logger.info(f"Saved: {output_path}")
