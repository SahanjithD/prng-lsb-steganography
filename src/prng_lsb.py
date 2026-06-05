"""
prng_lsb.py — PRNG-Based Adaptive LSB Steganography.

Uses a secret key to seed a PRNG for random pixel-channel selection and
multi-LSB bit-plane selection. This is the modified/improved approach that
resists steganalysis better than the sequential baseline.

Key improvements over sequential LSB:
    - Pixels are selected in a random permutation order (not sequential).
    - Each bit is embedded into a randomly chosen bit plane (bit-0 or bit-1).
    - Extraction is impossible without the correct secret key.
"""

import random
import numpy as np

from src.utils import (
    text_to_bits,
    bits_to_text,
    encode_message_length,
    decode_message_length,
    get_max_capacity,
    HEADER_BITS,
)


def _generate_embedding_plan(
    key: str, total_channels: int, num_bits: int
) -> list[tuple[int, int]]:
    """
    Generate a deterministic embedding plan from the secret key.

    Uses the key to seed an instance-based PRNG that produces:
        1. A random permutation of pixel-channel indices (no repeats).
        2. A random bit-plane choice (0 or 1) for each selected position.

    The PRNG is instance-based (random.Random) so it doesn't interfere
    with global random state, and is fully reproducible for the same key.

    Args:
        key: Secret key string used to seed the PRNG.
        total_channels: Total available pixel-channels (H * W * 3).
        num_bits: Number of bits to embed (header + message).

    Returns:
        List of (channel_index, bit_plane) tuples, length = num_bits.

    Raises:
        ValueError: If num_bits exceeds the number of available channels.
    """
    if num_bits > total_channels:
        raise ValueError(
            f"Payload ({num_bits} bits) exceeds available channels ({total_channels})."
        )

    # Seed an isolated PRNG instance with the key
    rng = random.Random(key)

    # Generate a random permutation of all channel indices, then take
    # only the first num_bits entries (avoids shuffling more than needed)
    indices = list(range(total_channels))
    rng.shuffle(indices)
    selected_indices = indices[:num_bits]

    # For each selected index, choose a random bit plane (0 or 1)
    plan = []
    for idx in selected_indices:
        bit_plane = rng.randint(0, 1)  # 0 = LSB (bit-0), 1 = bit-1
        plan.append((idx, bit_plane))

    return plan


def embed(cover_image: np.ndarray, message: str, key: str) -> np.ndarray:
    """
    Embed a message using PRNG-based random pixel and multi-LSB selection.

    Algorithm:
        1. Convert message to bits and prepend a 32-bit length header.
        2. Seed PRNG with the secret key.
        3. Generate an embedding plan: random (channel_index, bit_plane) pairs.
        4. For each payload bit, modify the chosen bit plane of the
           chosen pixel-channel in the flattened image.

    Args:
        cover_image: NumPy RGB array (H x W x 3), dtype uint8.
        message: The plaintext message to embed.
        key: Secret key for PRNG seeding.

    Returns:
        Stego image as a NumPy array (same shape as cover_image).

    Raises:
        ValueError: If the message is too large for the cover image.
    """
    # --- 1. Prepare the payload ---
    message_bits = text_to_bits(message)
    msg_len = len(message_bits)

    max_bits = get_max_capacity(cover_image, bits_per_channel=1)
    if msg_len > max_bits:
        raise ValueError(
            f"Message too large: {msg_len} bits required, "
            f"but image can hold at most {max_bits} bits."
        )

    header = encode_message_length(msg_len)
    payload = header + message_bits

    # --- 2. Generate the embedding plan ---
    total_channels = cover_image.shape[0] * cover_image.shape[1] * 3
    plan = _generate_embedding_plan(key, total_channels, len(payload))

    # --- 3. Flatten and embed ---
    stego = cover_image.copy()
    flat = stego.flatten()

    for i, bit_char in enumerate(payload):
        bit = int(bit_char)
        channel_idx, bit_plane = plan[i]

        if bit_plane == 0:
            # Modify bit-0 (LSB): clear bit-0, then set it
            flat[channel_idx] = (flat[channel_idx] & 0xFE) | bit
        else:
            # Modify bit-1: clear bit-1, then set it
            flat[channel_idx] = (flat[channel_idx] & 0xFD) | (bit << 1)

    # --- 4. Reshape and return ---
    stego = flat.reshape(cover_image.shape)
    return stego


def extract(stego_image: np.ndarray, key: str) -> str:
    """
    Extract a hidden message using the same secret key.

    Algorithm:
        1. Re-seed the PRNG with the same key to regenerate the
           identical embedding plan.
        2. Read the header bits from their (channel_index, bit_plane)
           locations to recover the message length.
        3. Read the message bits from the remaining plan entries.
        4. Convert bits back to plaintext.

    Args:
        stego_image: NumPy RGB array containing hidden data.
        key: The same secret key used during embedding.

    Returns:
        The extracted plaintext message.

    Raises:
        ValueError: If the decoded length is invalid.
    """
    flat = stego_image.flatten()
    total_channels = len(flat)

    # --- 1. Extract the header first ---
    # We need at least HEADER_BITS to read the length.
    # Generate a plan for HEADER_BITS entries to read the header.
    header_plan = _generate_embedding_plan(key, total_channels, HEADER_BITS)

    header_bits = ""
    for channel_idx, bit_plane in header_plan:
        if bit_plane == 0:
            header_bits += str(flat[channel_idx] & 1)
        else:
            header_bits += str((flat[channel_idx] >> 1) & 1)

    msg_len = decode_message_length(header_bits)

    # Sanity check
    max_possible = total_channels - HEADER_BITS
    if msg_len < 0 or msg_len > max_possible:
        raise ValueError(
            f"Invalid message length decoded: {msg_len} "
            f"(max possible: {max_possible}). Wrong key?"
        )

    # --- 2. Generate the full plan (header + message) ---
    full_plan = _generate_embedding_plan(key, total_channels, HEADER_BITS + msg_len)

    # --- 3. Extract message bits (skip the header entries) ---
    message_bits = ""
    for i in range(HEADER_BITS, HEADER_BITS + msg_len):
        channel_idx, bit_plane = full_plan[i]
        if bit_plane == 0:
            message_bits += str(flat[channel_idx] & 1)
        else:
            message_bits += str((flat[channel_idx] >> 1) & 1)

    # --- 4. Convert to text ---
    return bits_to_text(message_bits)
