"""Smoke test for Phase 4 — all four evaluation metrics."""

import numpy as np
from src.utils import load_image, save_image
from src.sequential_lsb import embed
from src.metrics import (
    compute_mse,
    compute_psnr,
    histogram_chi_square,
    plot_histogram_comparison,
    rs_analysis,
    report_capacity,
)


def test_psnr():
    """Test PSNR on synthetic images."""
    print("\n--- 1. PSNR ---")

    # Identical images should give inf
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    mse = compute_mse(img, img)
    psnr = compute_psnr(img, img)
    assert mse == 0.0
    assert psnr == float("inf")
    print(f"  [OK] Identical images: MSE={mse}, PSNR=inf")

    # Embed a message and measure PSNR
    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    stego = embed(cover, "Hello World! This is a test message for PSNR measurement.")

    mse = compute_mse(cover, stego)
    psnr = compute_psnr(cover, stego)
    assert mse > 0
    assert psnr > 40, f"PSNR should be > 40 dB for a short message, got {psnr}"
    print(f"  [OK] Short message: MSE={mse:.4f}, PSNR={psnr:.2f} dB")

    # Larger message should have lower PSNR (more pixels modified)
    big_msg = "A" * 5000
    stego_big = embed(cover, big_msg)
    psnr_big = compute_psnr(cover, stego_big)
    assert psnr_big < psnr, "Larger message should give lower PSNR"
    print(f"  [OK] Large message:  PSNR={psnr_big:.2f} dB (lower as expected)")


def test_histogram():
    """Test histogram chi-square and plotting."""
    print("\n--- 2. Histogram Analysis ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    stego = embed(cover, "Test message for histogram analysis.")

    chi2 = histogram_chi_square(cover, stego)
    print(f"  [OK] Chi-square distances: R={chi2['R']:.4f}, G={chi2['G']:.4f}, B={chi2['B']:.4f}")
    assert all(v >= 0 for v in chi2.values()), "Chi-square values must be non-negative"

    # Identical images should have chi2 = 0
    chi2_same = histogram_chi_square(cover, cover)
    assert all(v == 0 for v in chi2_same.values())
    print(f"  [OK] Identical images: chi2 = 0 for all channels")

    # Save a histogram comparison plot
    plot_histogram_comparison(
        cover, stego,
        title="Histogram: Cover vs Sequential LSB Stego",
        save_path="results/test_histogram_comparison.png"
    )
    print(f"  [OK] Histogram plot saved to results/test_histogram_comparison.png")


def test_rs_analysis():
    """Test RS steganalysis on clean and stego images."""
    print("\n--- 3. RS Steganalysis ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)

    # Clean image — estimated rate should be low
    rs_clean = rs_analysis(cover)
    print(f"  Clean image RS:")
    print(f"    R_m={rs_clean['R_m']}, S_m={rs_clean['S_m']}, "
          f"R_-m={rs_clean['R_neg_m']}, S_-m={rs_clean['S_neg_m']}")
    print(f"    Total groups: {rs_clean['total_groups']}")
    print(f"    Estimated rate: {rs_clean['estimated_rate']}")

    # Stego image (heavy embedding) — estimated rate should be higher
    big_msg = "A" * 10000
    stego = embed(cover, big_msg)
    rs_stego = rs_analysis(stego)
    print(f"  Stego image RS (heavy embedding):")
    print(f"    R_m={rs_stego['R_m']}, S_m={rs_stego['S_m']}, "
          f"R_-m={rs_stego['R_neg_m']}, S_-m={rs_stego['S_neg_m']}")
    print(f"    Estimated rate: {rs_stego['estimated_rate']}")

    print(f"  [OK] RS analysis completed for both clean and stego images")


def test_capacity():
    """Test capacity reporting."""
    print("\n--- 4. Embedding Capacity ---")

    img = np.zeros((512, 512, 3), dtype=np.uint8)
    cap = report_capacity(img)
    print(f"  Image: {cap['image_dimensions']}")
    print(f"  Total pixels: {cap['total_pixels']}")
    print(f"  Total channels: {cap['total_channels']}")
    print(f"  Sequential capacity: {cap['sequential_bits']} bits = {cap['sequential_bytes']} bytes")
    print(f"  PRNG capacity: {cap['prng_bits']} bits = {cap['prng_bytes']} bytes")
    print(f"  Capacity as %% of image: {cap['capacity_pct']}%%")

    assert cap['sequential_bits'] == 512 * 512 * 3 - 32
    assert cap['sequential_bytes'] == (512 * 512 * 3 - 32) // 8
    print(f"  [OK] Capacity values correct")


if __name__ == "__main__":
    print("=== Phase 4: Metrics Tests ===")
    test_psnr()
    test_histogram()
    test_rs_analysis()
    test_capacity()
    print("\n=== ALL PHASE 4 TESTS PASSED ===")
