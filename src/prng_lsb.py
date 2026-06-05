"""
prng_lsb.py — PRNG-Based Adaptive LSB Steganography.

Uses a secret key to seed a PRNG for random pixel-channel selection and
multi-LSB bit-plane selection. This is the modified/improved approach that
resists steganalysis better than the sequential baseline.
"""

import random
import numpy as np


def _generate_embedding_plan(
    key: str, total_channels: int, num_bits: int
) -> list[tuple[int, int]]:
    """
    Generate a deterministic embedding plan from the secret key.

    Uses the key to seed a PRNG that produces:
        - A random permutation of pixel-channel indices (no repeats).
        - A random bit-plane choice (0 or 1) for each position.

    Args:
        key: Secret key string used to seed the PRNG.
        total_channels: Total available pixel-channels (H * W * 3).
        num_bits: Number of message bits to embed (including header).

    Returns:
        List of (channel_index, bit_plane) tuples.

    Raises:
        ValueError: If num_bits exceeds available capacity.
    """
    raise NotImplementedError


def embed(cover_image: np.ndarray, message: str, key: str) -> np.ndarray:
    """
    Embed a message using PRNG-based random pixel and multi-LSB selection.

    Algorithm:
        1. Seed PRNG with the secret key.
        2. Generate a random permutation of pixel-channel indices.
        3. For each message bit, select a random bit plane (bit-0 or bit-1).
        4. Embed the message bit at the chosen (pixel-channel, bit-plane).

    Args:
        cover_image: NumPy RGB array (H x W x 3), dtype uint8.
        message: The plaintext message to embed.
        key: Secret key for PRNG seeding.

    Returns:
        Stego image as a NumPy array.

    Raises:
        ValueError: If the message is too large for the cover image.
    """
    raise NotImplementedError


def extract(stego_image: np.ndarray, key: str) -> str:
    """
    Extract a hidden message using the same secret key.

    Algorithm:
        1. Re-seed the PRNG with the same key.
        2. Regenerate the same permutation and bit-plane choices.
        3. Read bits from the corresponding locations.
        4. Convert bits back to plaintext.

    Args:
        stego_image: NumPy RGB array containing hidden data.
        key: The same secret key used during embedding.

    Returns:
        The extracted plaintext message.
    """
    raise NotImplementedError
