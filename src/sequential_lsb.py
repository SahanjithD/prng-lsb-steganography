"""
sequential_lsb.py — Baseline Sequential LSB Steganography.

Embeds and extracts messages by sequentially replacing the least significant
bit (bit-0) of each pixel-channel value. This is the naive baseline approach
that the PRNG method improves upon.
"""

import numpy as np
from src.utils import (
    text_to_bits,
    bits_to_text,
    encode_message_length,
    decode_message_length,
    get_max_capacity,
    HEADER_BITS,
)


def embed(cover_image: np.ndarray, message: str) -> np.ndarray:
    """
    Embed a text message into a cover image using sequential LSB replacement.

    Algorithm:
        1. Convert message to bits and prepend a 32-bit length header.
        2. Flatten the image into a 1-D array of pixel-channel values.
        3. Sequentially replace the LSB (bit-0) of each value with the
           next bit from the payload (header + message).
        4. Reshape back to the original image dimensions.

    Args:
        cover_image: NumPy RGB array (H x W x 3), dtype uint8.
        message: The plaintext message to embed.

    Returns:
        Stego image as a NumPy array (same shape as cover_image).

    Raises:
        ValueError: If the message is too large for the cover image.
    """
    # --- 1. Prepare the payload ---
    message_bits = text_to_bits(message)
    msg_len = len(message_bits)

    # Check capacity (1 bit per channel for sequential)
    max_bits = get_max_capacity(cover_image, bits_per_channel=1)
    if msg_len > max_bits:
        raise ValueError(
            f"Message too large: {msg_len} bits required, "
            f"but image can hold at most {max_bits} bits."
        )

    # Full payload = length header + message bits
    header = encode_message_length(msg_len)
    payload = header + message_bits

    # --- 2. Flatten image to 1-D channel array ---
    stego = cover_image.copy()
    flat = stego.flatten()  # shape: (H * W * 3,)

    # --- 3. Embed sequentially ---
    for i, bit_char in enumerate(payload):
        bit = int(bit_char)
        # Clear the LSB, then set it to the message bit
        flat[i] = (flat[i] & 0xFE) | bit

    # --- 4. Reshape and return ---
    stego = flat.reshape(cover_image.shape)
    return stego


def extract(stego_image: np.ndarray) -> str:
    """
    Extract a hidden message from a stego image using sequential LSB reading.

    Algorithm:
        1. Flatten the image to a 1-D channel array.
        2. Read the first HEADER_BITS LSBs to recover the message length.
        3. Read exactly that many additional LSBs for the message.
        4. Convert the extracted bits back to plaintext.

    Args:
        stego_image: NumPy RGB array containing hidden data.

    Returns:
        The extracted plaintext message.

    Raises:
        ValueError: If the decoded length is invalid or exceeds image capacity.
    """
    flat = stego_image.flatten()

    # --- 1. Extract the header ---
    header_bits = ""
    for i in range(HEADER_BITS):
        header_bits += str(flat[i] & 1)

    msg_len = decode_message_length(header_bits)

    # Sanity check
    max_possible = len(flat) - HEADER_BITS
    if msg_len < 0 or msg_len > max_possible:
        raise ValueError(
            f"Invalid message length decoded: {msg_len} "
            f"(max possible: {max_possible})."
        )

    # --- 2. Extract the message bits ---
    message_bits = ""
    for i in range(HEADER_BITS, HEADER_BITS + msg_len):
        message_bits += str(flat[i] & 1)

    # --- 3. Convert to text ---
    return bits_to_text(message_bits)
