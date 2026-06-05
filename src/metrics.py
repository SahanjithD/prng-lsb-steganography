"""
metrics.py — Evaluation metrics for steganography comparison.

Implements PSNR, histogram analysis, RS steganalysis, and embedding
capacity measurement to quantitatively compare the sequential and
PRNG-based LSB methods.
"""

import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. PSNR (Peak Signal-to-Noise Ratio)
# ---------------------------------------------------------------------------

def compute_mse(cover: np.ndarray, stego: np.ndarray) -> float:
    """Compute Mean Squared Error between cover and stego images."""
    raise NotImplementedError


def compute_psnr(cover: np.ndarray, stego: np.ndarray) -> float:
    """
    Compute PSNR in decibels.

    Formula: PSNR = 10 * log10(255² / MSE)
    Returns float('inf') if images are identical (MSE = 0).
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 2. Histogram Analysis
# ---------------------------------------------------------------------------

def compute_histogram(image: np.ndarray, channel: int) -> np.ndarray:
    """Compute the 256-bin histogram for a single colour channel."""
    raise NotImplementedError


def histogram_chi_square(cover: np.ndarray, stego: np.ndarray) -> dict:
    """
    Compute chi-square distance between cover and stego histograms
    for each RGB channel.

    Returns:
        Dict with keys 'R', 'G', 'B' and chi-square values.
    """
    raise NotImplementedError


def plot_histogram_comparison(
    cover: np.ndarray, stego: np.ndarray, title: str, save_path: str | None = None
) -> None:
    """
    Plot overlaid histograms (cover vs stego) for R, G, B channels.
    Optionally save the figure to disk.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 3. RS Steganalysis
# ---------------------------------------------------------------------------

def rs_analysis(image: np.ndarray, block_size: int = 4) -> dict:
    """
    Perform Regular-Singular group steganalysis.

    Classifies pixel groups into Regular (R), Singular (S), or
    Unchanged (U) categories under positive and negative flipping.

    Args:
        image: NumPy RGB array to analyse.
        block_size: Pixel group size for the analysis.

    Returns:
        Dict with R_m, S_m, R_neg_m, S_neg_m counts and estimated
        embedding rate.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# 4. Embedding Capacity
# ---------------------------------------------------------------------------

def report_capacity(image: np.ndarray) -> dict:
    """
    Report embedding capacity for both methods.

    Returns:
        Dict with 'sequential_bits', 'sequential_bytes',
        'prng_max_bits', 'prng_max_bytes', and percentage of image size.
    """
    raise NotImplementedError
