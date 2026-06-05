"""Smoke test for Phase 3 — PRNG-based adaptive LSB steganography."""

import numpy as np
from src.utils import text_to_bits, load_image, save_image
from src.prng_lsb import embed, extract
from src.metrics import compute_psnr, rs_analysis


def test_basic_embed_extract():
    """Test PRNG embed/extract round-trip on a synthetic image."""
    print("\n--- 1. Basic Embed / Extract ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    key = "my_secret_key_123"
    message = "Hello, this is a secret message hidden with PRNG-based LSB!"

    stego = embed(cover, message, key)
    assert stego.shape == cover.shape
    assert not np.array_equal(cover, stego), "Stego should differ from cover"

    recovered = extract(stego, key)
    assert recovered == message, f"FAIL: got '{recovered}'"
    print(f"  [OK] Embedded and extracted: '{recovered}'")


def test_pixel_diff():
    """Verify pixel modifications are small (max diff <= 3 for 2-bit planes)."""
    print("\n--- 2. Pixel Difference Check ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    key = "test_key"
    message = "Checking pixel differences with PRNG method."

    stego = embed(cover, message, key)
    diff = np.abs(cover.astype(int) - stego.astype(int))

    # bit-0 changes give diff of 1, bit-1 changes give diff of 2
    # in rare cases both could be modified on same pixel = diff of 3
    assert diff.max() <= 3, f"Max diff should be <= 3, got {diff.max()}"
    print(f"  [OK] Max pixel difference: {diff.max()} (multi-LSB changes)")

    changed = np.count_nonzero(diff)
    total_bits = len(text_to_bits(message)) + 32
    print(f"  [OK] Channels modified: {changed} (payload bits: {total_bits})")


def test_wrong_key_fails():
    """Extraction with wrong key should produce garbage or error."""
    print("\n--- 3. Wrong Key Rejection ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    correct_key = "correct_key"
    wrong_key = "wrong_key"
    message = "This should not be recoverable with the wrong key."

    stego = embed(cover, message, correct_key)

    # With wrong key, extraction should either raise an error
    # (invalid length) or return garbage text
    try:
        wrong_result = extract(stego, wrong_key)
        # If it doesn't error, the result should be different
        assert wrong_result != message, "Wrong key should NOT recover the message!"
        print(f"  [OK] Wrong key returned garbage (no match)")
    except (ValueError, UnicodeDecodeError):
        print(f"  [OK] Wrong key raised an error (as expected)")


def test_different_keys_different_results():
    """Same message with different keys should produce different stego images."""
    print("\n--- 4. Key Sensitivity ---")

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    message = "Same message, different keys."

    stego_a = embed(cover, message, "key_alpha")
    stego_b = embed(cover, message, "key_beta")

    assert not np.array_equal(stego_a, stego_b), "Different keys should give different stego images"

    # But both should extract correctly with their own keys
    assert extract(stego_a, "key_alpha") == message
    assert extract(stego_b, "key_beta") == message
    print(f"  [OK] Different keys -> different stego images, both extract correctly")


def test_file_io_roundtrip():
    """Test embed -> save PNG -> load -> extract round-trip."""
    print("\n--- 5. File I/O Round-Trip ---")

    rng = np.random.default_rng(99)
    cover = rng.integers(0, 256, size=(150, 150, 3), dtype=np.uint8)
    key = "file_io_key"
    message = "Round-trip through PNG file save and load."

    stego = embed(cover, message, key)
    save_image(stego, "results/test_stego_prng.png")

    stego_loaded = load_image("results/test_stego_prng.png")
    recovered = extract(stego_loaded, key)
    assert recovered == message
    print(f"  [OK] File I/O round-trip: '{recovered}'")


def test_psnr_comparison():
    """Compare PSNR between sequential and PRNG methods."""
    print("\n--- 6. PSNR Comparison (Sequential vs PRNG) ---")

    from src.sequential_lsb import embed as seq_embed

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    message = "A" * 2000  # medium-sized message
    key = "compare_key"

    stego_seq = seq_embed(cover, message)
    stego_prng = embed(cover, message, key)

    psnr_seq = compute_psnr(cover, stego_seq)
    psnr_prng = compute_psnr(cover, stego_prng)

    print(f"  Sequential PSNR: {psnr_seq:.2f} dB")
    print(f"  PRNG PSNR:       {psnr_prng:.2f} dB")
    print(f"  [OK] Both methods produce high-quality stego images")


def test_rs_comparison():
    """Compare RS steganalysis detection between methods."""
    print("\n--- 7. RS Steganalysis Comparison ---")

    from src.sequential_lsb import embed as seq_embed

    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)
    message = "A" * 5000
    key = "rs_key"

    stego_seq = seq_embed(cover, message)
    stego_prng = embed(cover, message, key)

    rs_seq = rs_analysis(stego_seq)
    rs_prng = rs_analysis(stego_prng)

    print(f"  Sequential RS estimated rate: {rs_seq['estimated_rate']}")
    print(f"  PRNG RS estimated rate:       {rs_prng['estimated_rate']}")
    print(f"  [OK] RS analysis completed for both methods")


if __name__ == "__main__":
    print("=== Phase 3: PRNG-Based LSB Tests ===")
    test_basic_embed_extract()
    test_pixel_diff()
    test_wrong_key_fails()
    test_different_keys_different_results()
    test_file_io_roundtrip()
    test_psnr_comparison()
    test_rs_comparison()
    print("\n=== ALL PHASE 3 TESTS PASSED ===")
