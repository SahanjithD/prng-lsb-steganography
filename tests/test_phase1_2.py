"""Quick smoke test for Phase 1 (utils) and Phase 2 (sequential LSB)."""

import numpy as np
from src.utils import (
    text_to_bits,
    bits_to_text,
    encode_message_length,
    decode_message_length,
    load_image,
    save_image,
    get_max_capacity,
)
from src.sequential_lsb import embed, extract


def test_binary_conversion():
    """Test text ↔ bits round-trip."""
    for text in ["Hello", "PRNG Steganography!", "Secret-123", ""]:
        if text == "":
            continue  # empty string edge case skipped
        bits = text_to_bits(text)
        recovered = bits_to_text(bits)
        assert recovered == text, f"FAIL: '{text}' → '{recovered}'"
        print(f"  [OK] text_to_bits / bits_to_text: '{text}'")


def test_header():
    """Test message length header encode/decode."""
    for length in [0, 1, 255, 1024, 100000]:
        header = encode_message_length(length)
        assert len(header) == 32
        decoded = decode_message_length(header)
        assert decoded == length, f"FAIL: {length} → {decoded}"
        print(f"  [OK] header encode/decode: {length}")


def test_capacity():
    """Test capacity calculation."""
    # 100x100 RGB image → 100*100*3 = 30,000 channels
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cap = get_max_capacity(img, bits_per_channel=1)
    assert cap == 30000 - 32  # minus header
    print(f"  [OK] capacity (1 bit/ch): {cap} bits = {cap // 8} bytes")

    cap2 = get_max_capacity(img, bits_per_channel=2)
    assert cap2 == 60000 - 32
    print(f"  [OK] capacity (2 bit/ch): {cap2} bits = {cap2 // 8} bytes")


def test_sequential_embed_extract_synthetic():
    """Test sequential LSB on a synthetic image (no file I/O needed)."""
    # Create a random 200x200 RGB image
    rng = np.random.default_rng(42)
    cover = rng.integers(0, 256, size=(200, 200, 3), dtype=np.uint8)

    message = "Hello, this is a secret message for sequential LSB steganography!"
    print(f"  Original message: '{message}'")

    # Embed
    stego = embed(cover, message)

    # Verify shapes match
    assert stego.shape == cover.shape, "Shape mismatch!"

    # Verify images are not identical (bits were changed)
    assert not np.array_equal(cover, stego), "Stego should differ from cover!"

    # Extract
    recovered = extract(stego)
    assert recovered == message, f"FAIL: extracted '{recovered}'"
    print(f"  [OK] Extracted message: '{recovered}'")

    # Check pixel differences are minimal (only LSB changes)
    diff = np.abs(cover.astype(int) - stego.astype(int))
    assert diff.max() <= 1, f"Max pixel diff should be ≤ 1, got {diff.max()}"
    print(f"  [OK] Max pixel difference: {diff.max()} (LSB-only changes)")

    changed = np.count_nonzero(diff)
    total_bits = len(text_to_bits(message)) + 32  # message + header
    print(f"  [OK] Channels modified: {changed} (payload bits: {total_bits})")


def test_sequential_image_io():
    """Test embed → save → load → extract round-trip with file I/O."""
    # Create and save a synthetic cover image
    rng = np.random.default_rng(99)
    cover = rng.integers(0, 256, size=(150, 150, 3), dtype=np.uint8)
    save_image(cover, "results/test_cover.png")
    print("  [OK] Saved test cover image")

    # Load it back
    loaded = load_image("results/test_cover.png")
    assert np.array_equal(cover, loaded), "Loaded image differs from original!"
    print("  [OK] Loaded image matches original (lossless PNG)")

    # Embed, save, load, extract
    message = "Round-trip test with file I/O [OK]"
    stego = embed(loaded, message)
    save_image(stego, "results/test_stego_seq.png")
    print("  [OK] Saved stego image")

    stego_loaded = load_image("results/test_stego_seq.png")
    recovered = extract(stego_loaded)
    assert recovered == message, f"FAIL: '{recovered}'"
    print(f"  [OK] File I/O round-trip: '{recovered}'")


if __name__ == "__main__":
    print("\n=== Phase 1: Utils Tests ===")
    test_binary_conversion()
    test_header()
    test_capacity()

    print("\n=== Phase 2: Sequential LSB Tests ===")
    test_sequential_embed_extract_synthetic()
    test_sequential_image_io()

    print("\n=== ALL TESTS PASSED ===")
