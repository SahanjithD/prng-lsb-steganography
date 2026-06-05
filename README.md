# PRNG-Based LSB Image Steganography

**Using Random Pixel and Bit Selection for Secure Image Steganography**

---

## Problem Statement

Traditional LSB steganography embeds data sequentially in the first LSB, creating predictable patterns that can be easily detected by steganalysis tools. It also lacks key-based security, allowing attackers to attempt extraction without any secret key.

## Objectives

- Implement a baseline **Sequential LSB** steganography method.
- Develop a **PRNG-based Adaptive LSB** scheme using a secret key for random pixel and bit selection.
- Experimentally compare both methods to demonstrate improved security and image quality.

## Overview

This project implements and compares two LSB steganography approaches for RGB images (PNG/BMP):

| Approach | Pixel Selection | Bit Plane | Key-Based Security |
|----------|----------------|-----------|-------------------|
| **Sequential LSB** (baseline) | Sequential (0, 1, 2, …) | Always bit-0 (LSB) | None |
| **PRNG-Based Adaptive LSB** (modified) | Random permutation seeded by key | Random (bit-0 or bit-1) | Secret key seeds the PRNG |

## Setup

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Embed a message using the sequential (baseline) method
python main.py embed --method sequential --image images/cover.png --message "Hello"

# Embed a message using the PRNG-based method (requires a key)
python main.py embed --method prng --image images/cover.png --message "Hello" --key "secret123"

# Extract from a sequential stego image
python main.py extract --method sequential --image results/stego_sequential.png

# Extract from a PRNG stego image (requires the same key)
python main.py extract --method prng --image results/stego_prng.png --key "secret123"

# Run a full comparison experiment (both methods side-by-side)
python main.py compare --image images/cover.png --message "Hello" --key "secret123"
```

## Evaluation Metrics

| Metric | What It Measures | Good Result |
|--------|-----------------|-------------|
| **PSNR** | Image quality (dB) | ≥ 40 dB |
| **Histogram Analysis** | Statistical detectability (chi-square) | Lower difference = harder to detect |
| **RS Steganalysis** | Security strength (R-S group analysis) | Lower estimated embedding rate |
| **Embedding Capacity** | Efficiency (bits/bytes embeddable) | Higher usable capacity |

## Expected Outcome

The PRNG-based method is expected to:
- Maintain high image quality (comparable PSNR to the baseline).
- Significantly reduce detectability by steganalysis tools (lower RS detection, smaller histogram shifts).
- Provide key-based security — extraction is impossible without the correct key.

## Project Structure

```
prng-lsb-steganography/
├── src/
│   ├── __init__.py            # Package init
│   ├── utils.py               # Shared helpers (binary conversion, image I/O)
│   ├── sequential_lsb.py      # Baseline: sequential LSB embed/extract
│   ├── prng_lsb.py            # Modified: PRNG-based adaptive LSB embed/extract
│   └── metrics.py             # PSNR, histogram analysis, RS steganalysis, capacity
├── main.py                    # CLI entry point (embed / extract / compare)
├── images/                    # Input cover images (PNG/BMP)
├── results/                   # Output stego images, plots, and reports
├── requirements.txt           # Python dependencies
├── IMPLEMENTATION_PLAN.md     # Detailed implementation plan & algorithm design
└── README.md                  # This file
```

## Scope

- **In scope:** Python-based steganography for RGB images (PNG/BMP), software-based experiments.
- **Out of scope:** Audio/video steganography, deep learning methods, hardware implementations.

## Dependencies

- Python 3.10+
- NumPy
- OpenCV (`opencv-python`)
- Pillow
- Matplotlib
