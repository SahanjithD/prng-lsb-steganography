# Implementation Plan

**PRNG-Based LSB Image Steganography Using Random Pixel and Bit Selection**

---

## Development Phases

```
Phase 1 ─► Phase 2 ─► Phase 3 ─► Phase 4 ─► Phase 5
utils.py    seq_lsb    prng_lsb   metrics    main.py
(done)      (done)     (pending)  (pending)  (pending)
```

---

## Phase 1 — Utilities & Image I/O (`src/utils.py`) ✅

Shared helpers used by both steganography methods.

| Function | Purpose |
|----------|---------|
| `text_to_bits(text)` | Convert plaintext → binary string (UTF-8, 8 bits per byte) |
| `bits_to_text(bits)` | Reverse: binary string → plaintext |
| `encode_message_length(length)` | Encode message bit-length as a 32-bit binary header |
| `decode_message_length(header_bits)` | Decode the 32-bit header back to an integer |
| `load_image(path)` | Load PNG/BMP via Pillow, convert to RGB, return NumPy array |
| `save_image(image, path)` | Save NumPy RGB array as lossless PNG |
| `get_max_capacity(image, bits_per_channel)` | Calculate max embeddable bits (minus header) |

### Design Decisions
- **32-bit header** allows messages up to ~512 MB (more than enough for any image).
- **Pillow for I/O** — reliable RGB conversion, handles RGBA/grayscale/palette automatically.
- **Lossless PNG output** — JPEG would destroy embedded data.

---

## Phase 2 — Baseline Sequential LSB (`src/sequential_lsb.py`) ✅

The naive baseline that the PRNG method improves upon.

### Embedding Algorithm
```
1. Convert message → bits
2. Prepend 32-bit length header → payload = header + message_bits
3. Flatten image to 1-D array of pixel-channel values (row-major: R,G,B,R,G,B,...)
4. For i = 0 to len(payload)-1:
       flat[i] = (flat[i] AND 0xFE) OR payload_bit[i]     # clear LSB, set to message bit
5. Reshape back to (H, W, 3) → stego image
```

### Extraction Algorithm
```
1. Flatten stego image to 1-D array
2. Read LSB of flat[0..31] → decode as 32-bit integer → msg_len
3. Read LSB of flat[32..32+msg_len-1] → message_bits
4. Convert message_bits → plaintext
```

### Weaknesses (by design — these motivate Phase 3)
- Pixels are modified in a fixed, predictable order (top-left → bottom-right).
- Only bit-0 is used — all changes concentrated in the lowest bit plane.
- No key required — anyone can attempt extraction.
- Easily detected by histogram analysis and RS steganalysis.

---

## Phase 3 — PRNG-Based Adaptive LSB (`src/prng_lsb.py`) 🔲

The core contribution: key-based random pixel and multi-LSB selection.

### Key Improvements

| Feature | Sequential (Phase 2) | PRNG-Based (Phase 3) |
|---------|---------------------|---------------------|
| Pixel selection | Sequential (0, 1, 2, …) | Random permutation seeded by key |
| Bit plane | Always bit-0 | Random: bit-0 or bit-1 |
| Security | None (no key) | Secret key required |
| Detectability | High (predictable pattern) | Low (spread across image) |

### Embedding Algorithm
```
1. Accept secret key (string)
2. Seed PRNG: rng = random.Random(key)
3. total_channels = H × W × 3
4. Generate random permutation of indices [0, total_channels)  →  perm
5. Convert message → bits, prepend 32-bit header  →  payload
6. Flatten image to 1-D array
7. For i = 0 to len(payload)-1:
       channel_idx = perm[i]
       bit_plane = rng.randint(0, 1)          # 0 = bit-0 (LSB), 1 = bit-1
       if bit_plane == 0:
           flat[channel_idx] = (flat[channel_idx] AND 0xFE) OR payload_bit[i]
       else:
           flat[channel_idx] = (flat[channel_idx] AND 0xFD) OR (payload_bit[i] << 1)
8. Reshape → stego image
```

### Extraction Algorithm
```
1. Re-seed PRNG with the same key → identical perm and bit_plane sequence
2. Flatten stego image
3. For i = 0 to HEADER_BITS-1:
       Read bit from flat[perm[i]] at the corresponding bit_plane
4. Decode header → msg_len
5. For i = HEADER_BITS to HEADER_BITS+msg_len-1:
       Read bit from flat[perm[i]] at the corresponding bit_plane
6. Convert bits → plaintext
```

### Why `random.Random(key)` (instance-based)?
- Keeps PRNG state isolated — won't interfere with other random calls.
- Fully deterministic for the same key — extraction reproduces the exact same sequence.

---

## Phase 4 — Evaluation Metrics (`src/metrics.py`) 🔲

### 4.1 PSNR (Peak Signal-to-Noise Ratio)
```
MSE  = (1 / N) × Σ (cover[i] - stego[i])²
PSNR = 10 × log₁₀(255² / MSE)
```
- Higher PSNR → less distortion → better quality.
- Threshold: ≥ 40 dB is considered good for steganography.
- Returns `inf` if images are identical (MSE = 0).

### 4.2 Histogram Analysis
- Compute 256-bin histogram per channel (R, G, B) for both cover and stego.
- **Chi-square distance** quantifies the difference:
  ```
  χ² = Σ (cover_hist[i] - stego_hist[i])² / (cover_hist[i] + ε)
  ```
- **Visual comparison**: overlaid histogram plots saved to `results/`.
- Lower χ² → less statistical disturbance → harder to detect.

### 4.3 RS Steganalysis
- Classify non-overlapping pixel groups (block_size = 4) into:
  - **Regular (R)**: flipping increases smoothness.
  - **Singular (S)**: flipping decreases smoothness.
  - **Unchanged (U)**: no change.
- Apply both positive and negative flipping masks.
- Estimate embedding rate from the relationship between R and S groups.
- Lower estimated rate → steganalysis thinks less data is hidden → better security.

### 4.4 Embedding Capacity
```
Sequential:  capacity = H × W × 3 × 1 - 32  (1 bit per channel)
PRNG:        capacity = H × W × 3 × 1 - 32  (same pixel count, but multi-bit-plane selection)
```
- Report in bits, bytes, and as percentage of image file size.

---

## Phase 5 — Experiment Runner (`main.py`) 🔲

### CLI Sub-commands

| Command | Description |
|---------|-------------|
| `embed` | Embed a message using sequential or PRNG method |
| `extract` | Extract a message from a stego image |
| `compare` | Run full experiment: embed with both, compute all metrics, output comparison |

### Comparison Workflow
```
1. Load cover image from images/
2. Embed message with Sequential LSB → stego_seq
3. Embed message with PRNG LSB (with key) → stego_prng
4. Compute for both:
   - PSNR(cover, stego)
   - Histogram chi-square(cover, stego) per channel
   - RS steganalysis(stego)
   - Embedding capacity
5. Print comparison table to console
6. Save stego images to results/
7. Save histogram plots to results/
8. Save summary report to results/
```

### Expected Console Output
```
============================================================
  COMPARISON: Sequential LSB vs PRNG-Based LSB
============================================================
Cover image : images/cover.png (512x512)
Message     : "Hello, World!" (104 bits)
PRNG Key    : "secret123"
------------------------------------------------------------
Metric                  | Sequential  | PRNG-Based
------------------------|-------------|-------------
PSNR (dB)               |    51.14    |    49.87
Histogram χ² (R)        |    12.45    |     3.21
Histogram χ² (G)        |    11.78    |     2.95
Histogram χ² (B)        |    13.02    |     3.47
RS Est. Embed Rate      |     0.42    |     0.08
Capacity (bytes)        |    98272    |    98272
------------------------------------------------------------
Stego images saved to results/
Histogram plots saved to results/
============================================================
```

---

## Dependencies

```
numpy              # Array operations
opencv-python      # Image processing (used in metrics)
Pillow             # Image I/O (load/save PNG/BMP)
matplotlib         # Histogram plots and visualisation
```

---

## Progress Tracker

| Phase | File | Status |
|-------|------|--------|
| 1 | `src/utils.py` | ✅ Complete |
| 2 | `src/sequential_lsb.py` | ✅ Complete |
| 3 | `src/prng_lsb.py` | 🔲 Pending |
| 4 | `src/metrics.py` | 🔲 Pending |
| 5 | `main.py` | 🔲 Pending |
