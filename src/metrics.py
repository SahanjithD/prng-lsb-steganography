"""
metrics.py — Evaluation metrics for steganography comparison.

Implements PSNR, histogram analysis, RS steganalysis, and embedding
capacity measurement to quantitatively compare the sequential and
PRNG-based LSB methods.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (no GUI window)
import matplotlib.pyplot as plt

from src.utils import get_max_capacity, HEADER_BITS


# ---------------------------------------------------------------------------
# 1. PSNR (Peak Signal-to-Noise Ratio)
# ---------------------------------------------------------------------------

def compute_mse(cover: np.ndarray, stego: np.ndarray) -> float:
    """
    Compute Mean Squared Error between cover and stego images.

    MSE = (1/N) * sum((cover - stego)^2)
    where N is the total number of pixel-channel values.

    Args:
        cover: Original image, shape (H, W, 3), dtype uint8.
        stego: Stego image, same shape and dtype.

    Returns:
        MSE as a float.
    """
    diff = cover.astype(np.float64) - stego.astype(np.float64)
    return float(np.mean(diff ** 2))


def compute_psnr(cover: np.ndarray, stego: np.ndarray) -> float:
    """
    Compute PSNR in decibels.

    Formula: PSNR = 10 * log10(MAX^2 / MSE)  where MAX = 255.
    Returns float('inf') if images are identical (MSE = 0).

    Args:
        cover: Original image, shape (H, W, 3), dtype uint8.
        stego: Stego image, same shape and dtype.

    Returns:
        PSNR value in dB, or inf if identical.
    """
    mse = compute_mse(cover, stego)
    if mse == 0.0:
        return float("inf")
    return 10.0 * np.log10((255.0 ** 2) / mse)


# ---------------------------------------------------------------------------
# 2. Histogram Analysis
# ---------------------------------------------------------------------------

def compute_histogram(image: np.ndarray, channel: int) -> np.ndarray:
    """
    Compute the 256-bin histogram for a single colour channel.

    Args:
        image: RGB image array, shape (H, W, 3).
        channel: Channel index (0=R, 1=G, 2=B).

    Returns:
        1-D NumPy array of length 256 with bin counts.
    """
    return np.bincount(image[:, :, channel].ravel(), minlength=256).astype(np.float64)


def histogram_chi_square(cover: np.ndarray, stego: np.ndarray) -> dict:
    """
    Compute chi-square distance between cover and stego histograms
    for each RGB channel.

    Formula per channel:
        chi2 = sum( (cover_hist[i] - stego_hist[i])^2 / (cover_hist[i] + eps) )

    A small epsilon avoids division by zero for empty bins.

    Args:
        cover: Original image, shape (H, W, 3).
        stego: Stego image, same shape.

    Returns:
        Dict with keys 'R', 'G', 'B' and their chi-square values.
    """
    result = {}
    for ch, name in enumerate(["R", "G", "B"]):
        h_cover = compute_histogram(cover, ch)
        h_stego = compute_histogram(stego, ch)
        # Use np.maximum(h_cover, 1.0) to prevent division by zero for empty bins
        chi2 = np.sum((h_cover - h_stego) ** 2 / np.maximum(h_cover, 1.0))
        result[name] = float(chi2)
    return result


def plot_histogram_comparison(
    cover: np.ndarray, stego: np.ndarray, title: str, save_path: str | None = None
) -> None:
    """
    Plot overlaid histograms (cover vs stego) for R, G, B channels.

    Creates a figure with 3 subplots (one per channel). Each subplot
    shows the cover histogram in solid colour and the stego histogram
    as a dashed line for easy visual comparison.

    Args:
        cover: Original image, shape (H, W, 3).
        stego: Stego image, same shape.
        title: Overall figure title.
        save_path: If provided, save the figure to this path (PNG).
    """
    channel_names = ["Red", "Green", "Blue"]
    channel_colors = ["#e74c3c", "#2ecc71", "#3498db"]
    bins = np.arange(257)  # 0..256 edges for 256 bins

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle(title, fontsize=14, fontweight="bold")

    for ch in range(3):
        ax = axes[ch]
        h_cover = compute_histogram(cover, ch)
        h_stego = compute_histogram(stego, ch)

        ax.bar(
            np.arange(256), h_cover, width=1.0,
            color=channel_colors[ch], alpha=0.5, label="Cover"
        )
        ax.plot(
            np.arange(256), h_stego,
            color="black", linewidth=0.8, linestyle="--", label="Stego"
        )

        ax.set_title(channel_names[ch])
        ax.set_xlabel("Pixel Value")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        ax.set_xlim(0, 255)

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")

    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. RS Steganalysis
# ---------------------------------------------------------------------------

def _discrimination_function(group: np.ndarray) -> float:
    """
    Compute the discrimination (smoothness) function for a pixel group.

    Uses the sum of absolute differences between consecutive pixels:
        f(x) = sum(|x[i+1] - x[i]|)

    Higher values indicate less smooth (more irregular) groups.

    Args:
        group: 1-D array of pixel values.

    Returns:
        Smoothness score (float).
    """
    return float(np.sum(np.abs(np.diff(group.astype(np.float64)))))


def _flip(value: int, mask_bit: int) -> int:
    """
    Apply a flipping operation to a pixel value.

    mask_bit controls the flip:
        +1 → positive flip: 0↔1, 2↔3, 4↔5, ... (flip LSB of value)
        -1 → negative flip: -1↔0, 1↔2, 3↔4, ... (flip LSB of value+1, then subtract 1)
         0 → no flip (identity)

    Args:
        value: Original pixel value (0-255).
        mask_bit: Flip direction (+1, -1, or 0).

    Returns:
        Flipped pixel value.
    """
    if mask_bit == 0:
        return value
    if mask_bit == 1:
        # Positive flip: swap even↔odd (flip LSB)
        return value ^ 1
    if mask_bit == -1:
        # Negative flip: shift by 1, flip LSB, shift back
        # Equivalent to: -1↔0, 1↔2, 3↔4, 5↔6, ...
        return (value + 1) ^ 1 - 1
    return value


def rs_analysis(image: np.ndarray, block_size: int = 4) -> dict:
    """
    Perform Regular-Singular group steganalysis on a single channel.

    For each non-overlapping group of `block_size` pixels in each row,
    applies a flipping mask M = [0, 1, 0, 1, ...] and its negative -M.
    Groups are classified as:
        - Regular (R):  f(flipped_group) > f(original_group)
        - Singular (S): f(flipped_group) < f(original_group)
        - Unchanged (U): f(flipped_group) == f(original_group)

    The estimated embedding rate is derived from the difference between
    R and S groups under positive vs negative flipping.

    This analysis is aggregated across all RGB channels to ensure
    changes in any channel are detected.

    Args:
        image: NumPy RGB array to analyse, shape (H, W, 3).
        block_size: Number of pixels per group (default 4).

    Returns:
        Dict with:
            'R_m'     : Regular groups under positive mask
            'S_m'     : Singular groups under positive mask
            'R_neg_m' : Regular groups under negative mask
            'S_neg_m' : Singular groups under negative mask
            'total_groups'       : Total number of groups analysed
            'estimated_rate'     : Estimated embedding rate (0.0–1.0)
    """
    height, width, channels = image.shape

    # Flipping mask: alternating [1, 0, 1, 0, ...]
    mask = np.array([1 if i % 2 == 0 else 0 for i in range(block_size)])
    neg_mask = -mask  # Negative mask: [-1, 0, -1, 0, ...]

    r_m = 0    # Regular groups (positive mask)
    s_m = 0    # Singular groups (positive mask)
    r_neg = 0  # Regular groups (negative mask)
    s_neg = 0  # Singular groups (negative mask)
    total = 0

    for ch in range(channels):
        channel = image[:, :, ch]
        for row in range(height):
            for col in range(0, width - block_size + 1, block_size):
                group = channel[row, col : col + block_size].copy()
                f_orig = _discrimination_function(group)
                total += 1

                # --- Positive mask ---
                flipped_pos = np.array(
                    [_flip(int(group[j]), int(mask[j])) for j in range(block_size)],
                    dtype=np.float64,
                )
                f_pos = _discrimination_function(flipped_pos)

                if f_pos > f_orig:
                    r_m += 1
                elif f_pos < f_orig:
                    s_m += 1

                # --- Negative mask ---
                flipped_neg = np.array(
                    [_flip(int(group[j]), int(neg_mask[j])) for j in range(block_size)],
                    dtype=np.float64,
                )
                f_neg = _discrimination_function(flipped_neg)

                if f_neg > f_orig:
                    r_neg += 1
                elif f_neg < f_orig:
                    s_neg += 1

    # --- Estimate embedding rate ---
    # In a clean image: R_m ≈ R_neg_m and S_m ≈ S_neg_m
    # In a stego image: R_m increases, S_m decreases relative to their negatives
    # Estimated rate approximation using the R-S difference ratio
    if total == 0:
        estimated_rate = 0.0
    else:
        # Normalise counts
        r_m_norm = r_m / total
        s_m_norm = s_m / total
        r_neg_norm = r_neg / total
        s_neg_norm = s_neg / total

        # The embedding rate estimation:
        # When no message is embedded: R_m ≈ R_-m, S_m ≈ S_-m
        # When a message is embedded: the gap between R_m and S_m narrows
        # We use the simplified estimator:
        #   p = (R_m - S_m) / (R_-m - S_-m)  when R_-m != S_-m
        # A value close to 1.0 means no embedding; close to 0.0 means heavy embedding.
        denom = r_neg_norm - s_neg_norm
        if abs(denom) < 1e-10:
            estimated_rate = 0.0
        else:
            ratio = (r_m_norm - s_m_norm) / denom
            # Clamp the estimated rate to [0, 1]
            # ratio ≈ 1 → no embedding, ratio < 1 → embedding detected
            estimated_rate = max(0.0, min(1.0, 1.0 - ratio))

    return {
        "R_m": r_m,
        "S_m": s_m,
        "R_neg_m": r_neg,
        "S_neg_m": s_neg,
        "total_groups": total,
        "estimated_rate": round(estimated_rate, 4),
    }


# ---------------------------------------------------------------------------
# 4. Embedding Capacity
# ---------------------------------------------------------------------------

def report_capacity(image: np.ndarray) -> dict:
    """
    Report embedding capacity for both methods.

    Sequential uses 1 bit per channel (bit-0 only).
    PRNG can use up to 2 bits per channel (bit-0 and bit-1), but in
    practice each pixel-channel uses 1 random bit plane, so usable
    capacity is the same count of pixel-channels — the advantage is
    in distribution, not raw capacity.

    Args:
        image: NumPy RGB array, shape (H, W, 3).

    Returns:
        Dict with capacity info for both methods.
    """
    h, w, c = image.shape
    total_pixels = h * w
    total_channels = total_pixels * c
    image_size_bytes = h * w * c  # raw uncompressed size

    seq_bits = get_max_capacity(image, bits_per_channel=1)
    prng_bits = get_max_capacity(image, bits_per_channel=1)  # same pixel count

    return {
        "image_dimensions": f"{w}x{h}",
        "total_pixels": total_pixels,
        "total_channels": total_channels,
        "sequential_bits": seq_bits,
        "sequential_bytes": seq_bits // 8,
        "prng_bits": prng_bits,
        "prng_bytes": prng_bits // 8,
        "capacity_pct": round(100.0 * seq_bits / (image_size_bytes * 8), 2),
    }


# ---------------------------------------------------------------------------
# 5. Visualizations
# ---------------------------------------------------------------------------

def generate_difference_map(cover: np.ndarray, stego: np.ndarray, save_path: str, title: str) -> None:
    """
    Generate and save a visual difference map (heatmap).
    Pixels that are identical are black. Changed pixels are highlighted in a bright color.
    """
    diff = np.abs(cover.astype(np.int16) - stego.astype(np.int16))
    # Sum differences across channels to get a single mask (H, W)
    diff_mask = np.sum(diff, axis=2) > 0
    
    # Create an RGB image where changed pixels are bright red (or any visible color)
    diff_img = np.zeros_like(cover)
    diff_img[diff_mask] = [255, 0, 50]  # Bright red/pink for visibility
    
    plt.figure(figsize=(6, 6))
    plt.imshow(diff_img)
    plt.title(title, fontsize=14, fontweight="bold")
    plt.axis("off")
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()

def plot_metric_trends(
    payload_pcts: list[float], 
    seq_metrics: list[float], 
    prng_metrics: list[float], 
    metric_name: str, 
    save_path: str,
    y_label: str
) -> None:
    """
    Plot a line graph comparing Sequential and PRNG metrics across payload sizes.
    """
    plt.figure(figsize=(8, 5))
    plt.plot(payload_pcts, seq_metrics, marker="o", color="#e74c3c", label="Sequential LSB", linewidth=2)
    plt.plot(payload_pcts, prng_metrics, marker="s", color="#3498db", label="PRNG-Based LSB", linewidth=2)
    
    plt.title(f"{metric_name} vs Payload Size", fontsize=14, fontweight="bold")
    plt.xlabel("Payload Size (% of Capacity)", fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.7)
    
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
