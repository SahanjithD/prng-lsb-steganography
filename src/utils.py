"""
utils.py — Shared utilities for LSB steganography.

Provides binary conversion, image I/O, and message framing helpers
used by both the sequential and PRNG-based methods.
"""

import os
import numpy as np
from PIL import Image

# Fixed header length (32 bits = 4 bytes) to store message length
HEADER_BITS = 32


def text_to_bits(text: str) -> str:
    """
    Convert a UTF-8 string to a binary string ('0'/'1' characters).

    Each byte of the UTF-8 encoding is converted to an 8-bit binary
    representation and concatenated.

    Example:
        >>> text_to_bits("A")
        '01000001'
    """
    byte_data = text.encode("utf-8")
    return "".join(format(byte, "08b") for byte in byte_data)


def bits_to_text(bits: str) -> str:
    """
    Convert a binary string back to a UTF-8 string.

    The binary string is split into 8-bit chunks, each converted to
    a byte, then decoded as UTF-8.

    Example:
        >>> bits_to_text('01000001')
        'A'
    """
    # Ensure length is a multiple of 8
    if len(bits) % 8 != 0:
        raise ValueError(
            f"Binary string length ({len(bits)}) is not a multiple of 8."
        )

    byte_list = []
    for i in range(0, len(bits), 8):
        byte_val = int(bits[i : i + 8], 2)
        byte_list.append(byte_val)

    return bytes(byte_list).decode("utf-8")


def encode_message_length(length: int) -> str:
    """
    Encode message bit-length as a fixed-width binary header.

    The length is stored as a 32-bit unsigned integer, allowing messages
    of up to 2^32 - 1 bits (~512 MB).

    Args:
        length: The number of message bits to encode.

    Returns:
        A 32-character binary string representing the length.

    Raises:
        ValueError: If length is negative or exceeds 32-bit capacity.
    """
    if length < 0:
        raise ValueError("Message length cannot be negative.")
    if length >= 2**HEADER_BITS:
        raise ValueError(
            f"Message length {length} exceeds {HEADER_BITS}-bit header capacity."
        )
    return format(length, f"0{HEADER_BITS}b")


def decode_message_length(header_bits: str) -> int:
    """
    Decode the message bit-length from a binary header.

    Args:
        header_bits: A 32-character binary string.

    Returns:
        The decoded integer message length (in bits).

    Raises:
        ValueError: If header_bits is not exactly HEADER_BITS long.
    """
    if len(header_bits) != HEADER_BITS:
        raise ValueError(
            f"Header must be exactly {HEADER_BITS} bits, got {len(header_bits)}."
        )
    return int(header_bits, 2)


def load_image(path: str) -> np.ndarray:
    """
    Load an image file (PNG/BMP) and return it as a NumPy RGB array.

    The image is opened with Pillow and converted to RGB mode (stripping
    any alpha channel). The result is a uint8 NumPy array of shape (H, W, 3).

    Args:
        path: File path to the image.

    Returns:
        NumPy array of shape (height, width, 3), dtype uint8.

    Raises:
        FileNotFoundError: If the image path doesn't exist.
        ValueError: If the file is not a valid image.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")

    try:
        img = Image.open(path)
    except Exception as e:
        raise ValueError(f"Cannot open image '{path}': {e}")

    # Convert to RGB (handles RGBA, grayscale, palette, etc.)
    img = img.convert("RGB")
    return np.array(img, dtype=np.uint8)


def save_image(image: np.ndarray, path: str) -> None:
    """
    Save a NumPy RGB array as a lossless PNG image.

    Creates parent directories if they don't exist.

    Args:
        image: NumPy array of shape (H, W, 3), dtype uint8.
        path: Destination file path (should end with .png).
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img = Image.fromarray(image, mode="RGB")
    img.save(path, format="PNG")


def get_max_capacity(image: np.ndarray, bits_per_channel: int = 1) -> int:
    """
    Calculate the maximum number of message bits that can be embedded.

    Total available slots = height × width × 3 channels × bits_per_channel.
    The header (HEADER_BITS) is reserved, so usable capacity is the remainder.

    Args:
        image: The cover image as a NumPy array (H x W x 3).
        bits_per_channel: Number of LSB planes used (1 for sequential, 1-2 for PRNG).

    Returns:
        Maximum embeddable message bits (excluding the header).
    """
    height, width, channels = image.shape
    total_slots = height * width * channels * bits_per_channel
    return total_slots - HEADER_BITS
