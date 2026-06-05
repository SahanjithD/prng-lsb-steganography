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
import os
import sys

from src.utils import load_image, save_image, get_max_capacity, text_to_bits
from src import sequential_lsb, prng_lsb
from src.metrics import (
    compute_psnr,
    histogram_chi_square,
    plot_histogram_comparison,
    rs_analysis,
    report_capacity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _separator(char: str = "=", width: int = 64) -> str:
    return char * width


def _print_header(text: str, width: int = 64) -> None:
    print(_separator("=", width))
    print(f"  {text}")
    print(_separator("=", width))


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_embed(args: argparse.Namespace) -> None:
    """Handle the 'embed' sub-command."""

    # Validate key for PRNG method
    if args.method == "prng" and not args.key:
        print("Error: --key is required when using the PRNG method.")
        sys.exit(1)

    # Load cover image
    print(f"Loading cover image: {args.image}")
    cover = load_image(args.image)
    h, w, _ = cover.shape
    print(f"  Image size: {w}x{h} ({w * h * 3} channels)")

    # Check capacity
    msg_bits = len(text_to_bits(args.message))
    max_bits = get_max_capacity(cover)
    print(f"  Message: {len(args.message)} chars = {msg_bits} bits")
    print(f"  Capacity: {max_bits} bits ({max_bits // 8} bytes)")

    if msg_bits > max_bits:
        print(f"Error: Message too large ({msg_bits} bits > {max_bits} bits).")
        sys.exit(1)

    # Embed
    print(f"\nEmbedding with {args.method.upper()} method...")
    if args.method == "sequential":
        stego = sequential_lsb.embed(cover, args.message)
    else:
        stego = prng_lsb.embed(cover, args.message, args.key)

    # Save output
    os.makedirs(args.output, exist_ok=True)
    out_path = os.path.join(args.output, f"stego_{args.method}.png")
    save_image(stego, out_path)

    # Quick quality check
    psnr = compute_psnr(cover, stego)
    print(f"  PSNR: {psnr:.2f} dB")
    print(f"  Saved to: {out_path}")
    print("Done.")


def cmd_extract(args: argparse.Namespace) -> None:
    """Handle the 'extract' sub-command."""

    # Validate key for PRNG method
    if args.method == "prng" and not args.key:
        print("Error: --key is required when using the PRNG method.")
        sys.exit(1)

    # Load stego image
    print(f"Loading stego image: {args.image}")
    stego = load_image(args.image)

    # Extract
    print(f"Extracting with {args.method.upper()} method...")
    try:
        if args.method == "sequential":
            message = sequential_lsb.extract(stego)
        else:
            message = prng_lsb.extract(stego, args.key)
    except (ValueError, UnicodeDecodeError) as e:
        print(f"Error during extraction: {e}")
        print("This may indicate a wrong key or an image without hidden data.")
        sys.exit(1)

    print(f"\nExtracted message ({len(message)} chars):")
    print(_separator("-", 40))
    print(message)
    print(_separator("-", 40))


def cmd_compare(args: argparse.Namespace) -> None:
    """
    Run the full comparison experiment:
        1. Embed with both methods.
        2. Compute PSNR, histogram chi-square, RS analysis for both.
        3. Print comparison table.
        4. Save stego images and plots to the output directory.
    """
    import shutil
    if os.path.exists(args.output):
        shutil.rmtree(args.output)
    os.makedirs(args.output, exist_ok=True)

    # --- Load cover image ---
    cover = load_image(args.image)
    h, w, _ = cover.shape
    msg_bits = len(text_to_bits(args.message))

    _print_header("COMPARISON: Sequential LSB vs PRNG-Based LSB")
    print(f"  Cover image : {args.image} ({w}x{h})")
    print(f"  Message     : \"{args.message[:50]}{'...' if len(args.message) > 50 else ''}\" ({msg_bits} bits)")
    print(f"  PRNG Key    : \"{args.key}\"")
    print(_separator("-"))

    # --- Embed with both methods ---
    print("\n[1/4] Embedding messages...")
    stego_seq = sequential_lsb.embed(cover, args.message)
    stego_prng = prng_lsb.embed(cover, args.message, args.key)

    # Save stego images
    seq_path = os.path.join(args.output, "stego_sequential.png")
    prng_path = os.path.join(args.output, "stego_prng.png")
    save_image(stego_seq, seq_path)
    save_image(stego_prng, prng_path)
    print(f"  Sequential stego saved: {seq_path}")
    print(f"  PRNG stego saved:       {prng_path}")

    # --- Verify extraction ---
    print("\n[2/4] Verifying extraction...")
    extracted_seq = sequential_lsb.extract(stego_seq)
    extracted_prng = prng_lsb.extract(stego_prng, args.key)
    seq_ok = extracted_seq == args.message
    prng_ok = extracted_prng == args.message
    print(f"  Sequential extraction: {'OK' if seq_ok else 'FAILED'}")
    print(f"  PRNG extraction:       {'OK' if prng_ok else 'FAILED'}")

    # --- Compute metrics ---
    print("\n[3/4] Computing metrics...")

    # PSNR
    psnr_seq = compute_psnr(cover, stego_seq)
    psnr_prng = compute_psnr(cover, stego_prng)

    # Histogram chi-square
    chi2_seq = histogram_chi_square(cover, stego_seq)
    chi2_prng = histogram_chi_square(cover, stego_prng)

    # RS steganalysis
    rs_seq = rs_analysis(stego_seq)
    rs_prng = rs_analysis(stego_prng)

    # Capacity
    cap = report_capacity(cover)

    # --- Generate histogram plots ---
    print("\n[4/4] Generating histogram plots...")
    plot_histogram_comparison(
        cover, stego_seq,
        title="Histogram: Cover vs Sequential LSB",
        save_path=os.path.join(args.output, "histogram_sequential.png"),
    )
    plot_histogram_comparison(
        cover, stego_prng,
        title="Histogram: Cover vs PRNG-Based LSB",
        save_path=os.path.join(args.output, "histogram_prng.png"),
    )
    print(f"  Saved: {os.path.join(args.output, 'histogram_sequential.png')}")
    print(f"  Saved: {os.path.join(args.output, 'histogram_prng.png')}")

    # --- Print comparison table ---
    print()
    _print_header("RESULTS")
    print()
    print(f"  {'Metric':<28} | {'Sequential':>12} | {'PRNG-Based':>12}")
    print(f"  {'-'*28}-+-{'-'*12}-+-{'-'*12}")
    print(f"  {'PSNR (dB)':<28} | {psnr_seq:>12.2f} | {psnr_prng:>12.2f}")
    print(f"  {'Histogram Chi2 (R)':<28} | {chi2_seq['R']:>12.4f} | {chi2_prng['R']:>12.4f}")
    print(f"  {'Histogram Chi2 (G)':<28} | {chi2_seq['G']:>12.4f} | {chi2_prng['G']:>12.4f}")
    print(f"  {'Histogram Chi2 (B)':<28} | {chi2_seq['B']:>12.4f} | {chi2_prng['B']:>12.4f}")
    print(f"  {'RS Est. Embed Rate':<28} | {rs_seq['estimated_rate']:>12.4f} | {rs_prng['estimated_rate']:>12.4f}")
    print(f"  {'Capacity (bytes)':<28} | {cap['sequential_bytes']:>12} | {cap['prng_bytes']:>12}")
    print()
    print(f"  Extraction verified       |     {'OK' if seq_ok else 'FAIL':>7} |     {'OK' if prng_ok else 'FAIL':>7}")
    print(_separator("-"))

    # --- Save summary report ---
    report_path = os.path.join(args.output, "comparison_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("PRNG-Based LSB Steganography — Comparison Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Cover image : {args.image} ({w}x{h})\n")
        f.write(f"Message     : {len(args.message)} chars, {msg_bits} bits\n")
        f.write(f"PRNG Key    : {args.key}\n\n")
        f.write(f"{'Metric':<28} | {'Sequential':>12} | {'PRNG-Based':>12}\n")
        f.write(f"{'-'*28}-+-{'-'*12}-+-{'-'*12}\n")
        f.write(f"{'PSNR (dB)':<28} | {psnr_seq:>12.2f} | {psnr_prng:>12.2f}\n")
        f.write(f"{'Histogram Chi2 (R)':<28} | {chi2_seq['R']:>12.4f} | {chi2_prng['R']:>12.4f}\n")
        f.write(f"{'Histogram Chi2 (G)':<28} | {chi2_seq['G']:>12.4f} | {chi2_prng['G']:>12.4f}\n")
        f.write(f"{'Histogram Chi2 (B)':<28} | {chi2_seq['B']:>12.4f} | {chi2_prng['B']:>12.4f}\n")
        f.write(f"{'RS Est. Embed Rate':<28} | {rs_seq['estimated_rate']:>12.4f} | {rs_prng['estimated_rate']:>12.4f}\n")
        f.write(f"{'Capacity (bytes)':<28} | {cap['sequential_bytes']:>12} | {cap['prng_bytes']:>12}\n")
        f.write(f"\nExtraction: Sequential={'OK' if seq_ok else 'FAIL'}, PRNG={'OK' if prng_ok else 'FAIL'}\n")
        f.write(f"\nFiles generated:\n")
        f.write(f"  - {seq_path}\n")
        f.write(f"  - {prng_path}\n")
        f.write(f"  - {os.path.join(args.output, 'histogram_sequential.png')}\n")
        f.write(f"  - {os.path.join(args.output, 'histogram_prng.png')}\n")

    print(f"\n  Summary report saved: {report_path}")
    print(_separator("="))
    print("  Comparison complete.")
    print(_separator("="))


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
