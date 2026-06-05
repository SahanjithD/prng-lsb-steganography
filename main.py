"""
main.py — CLI entry point for PRNG-Based LSB Image Steganography.

Supports embedding, extraction, and full comparison experiments
between the sequential and PRNG-based methods.

Usage:
    python main.py embed   --method sequential --image <path> --message <text> [--output <dir>]
    python main.py embed   --method prng       --image <path> --message <text> --key <key> [--output <dir>]
    python main.py extract --method sequential  --image <path>
    python main.py extract --method prng        --image <path> --key <key>
    python main.py compare --image <path> --message <text> --key <key> [--output <dir>]
"""

import argparse
import sys
import os

from src.utils import load_image, save_image
from src import sequential_lsb, prng_lsb
from src.metrics import (
    compute_psnr,
    histogram_chi_square,
    plot_histogram_comparison,
    rs_analysis,
    report_capacity,
)


def cmd_embed(args: argparse.Namespace) -> None:
    """Handle the 'embed' sub-command."""
    raise NotImplementedError


def cmd_extract(args: argparse.Namespace) -> None:
    """Handle the 'extract' sub-command."""
    raise NotImplementedError


def cmd_compare(args: argparse.Namespace) -> None:
    """
    Run the full comparison experiment:
        1. Embed with both methods.
        2. Compute PSNR, histogram chi-square, RS analysis for both.
        3. Print comparison table.
        4. Save stego images and plots to the output directory.
    """
    raise NotImplementedError


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with embed / extract / compare sub-commands."""
    parser = argparse.ArgumentParser(
        description="PRNG-Based LSB Image Steganography"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- embed ---
    p_embed = subparsers.add_parser("embed", help="Embed a message into an image")
    p_embed.add_argument("--method", choices=["sequential", "prng"], required=True)
    p_embed.add_argument("--image", required=True, help="Path to cover image")
    p_embed.add_argument("--message", required=True, help="Message to embed")
    p_embed.add_argument("--key", default=None, help="Secret key (required for PRNG)")
    p_embed.add_argument("--output", default="results", help="Output directory")

    # --- extract ---
    p_extract = subparsers.add_parser("extract", help="Extract a message from a stego image")
    p_extract.add_argument("--method", choices=["sequential", "prng"], required=True)
    p_extract.add_argument("--image", required=True, help="Path to stego image")
    p_extract.add_argument("--key", default=None, help="Secret key (required for PRNG)")

    # --- compare ---
    p_compare = subparsers.add_parser("compare", help="Run full comparison experiment")
    p_compare.add_argument("--image", required=True, help="Path to cover image")
    p_compare.add_argument("--message", required=True, help="Message to embed")
    p_compare.add_argument("--key", required=True, help="Secret key for PRNG method")
    p_compare.add_argument("--output", default="results", help="Output directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "embed": cmd_embed,
        "extract": cmd_extract,
        "compare": cmd_compare,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
