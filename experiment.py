"""
experiment.py — Automated 3x3 Experimental Rig

Runs a full comparison suite across:
- 3 Image Types (Landscape, Portrait, Cityscape)
- 3 Payload Sizes (5%, 50%, 95%)
- 2 Methods (Sequential, PRNG-Based)

Generates:
- Difference Maps (Visual Heatmaps of changed pixels)
- Metric Trend Charts (Line graphs of PSNR, Chi-Square, RS vs Capacity)
- A master summary report.
"""

import os
import shutil
import numpy as np
import matplotlib.pyplot as plt

from src.utils import load_image, save_image, get_max_capacity, HEADER_BITS
from src.sequential_lsb import embed as seq_embed
from src.prng_lsb import embed as prng_embed
from src.metrics import (
    compute_psnr,
    histogram_chi_square,
    rs_analysis,
    generate_difference_map,
    plot_metric_trends,
)


def run_experiment() -> None:
    output_dir = "results_experiment"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    images = {
        "Landscape": "images/landscape.png",
        "Portrait": "images/portrait.png",
        "Cityscape": "images/cityscape.png"
    }

    payload_targets = [5, 50, 95]  # percentages
    key = "academic_experiment_key_2026"

    # For the master report
    report_lines = []
    report_lines.append("STEGANOGRAPHY 3x3 EXPERIMENTAL RESULTS")
    report_lines.append("========================================\n")

    for img_name, img_path in images.items():
        print(f"\n--- Testing Image: {img_name} ---")
        report_lines.append(f"Image Type: {img_name}")
        report_lines.append("-" * 40)

        # Ensure image exists
        if not os.path.exists(img_path):
            print(f"Warning: {img_path} not found. Skipping.")
            continue

        cover = load_image(img_path)
        max_bits = get_max_capacity(cover)

        # Arrays to hold metric data for charts
        psnr_seq, psnr_prng = [], []
        chi2_seq, chi2_prng = [], []  # Storing average Chi2 across R,G,B
        rs_seq, rs_prng = [], []

        for pct in payload_targets:
            target_bits = int((pct / 100.0) * max_bits)
            target_chars = target_bits // 8  # Approximate characters needed
            
            # Create a deterministic random payload string of exact target bit length
            # We just use repeated characters or a long string
            # 'A' is 8 bits (01000001)
            payload_str = "A" * target_chars
            
            print(f"  -> Embedding {pct}% Payload ({target_bits} bits)")
            report_lines.append(f"\n  Payload Size: {pct}% ({target_bits} bits)")

            # Embed
            stego_s = seq_embed(cover, payload_str)
            stego_p = prng_embed(cover, payload_str, key)

            # --- Difference Maps (Only generate for 50% capacity to avoid too many files) ---
            if pct == 50:
                generate_difference_map(
                    cover, stego_s, 
                    os.path.join(output_dir, f"{img_name.lower()}_diff_seq_50.png"),
                    f"{img_name} - Sequential Difference Map (50%)"
                )
                generate_difference_map(
                    cover, stego_p, 
                    os.path.join(output_dir, f"{img_name.lower()}_diff_prng_50.png"),
                    f"{img_name} - PRNG Difference Map (50%)"
                )
                print("     [+] Generated Difference Maps")

            # --- Compute Metrics ---
            p_s = compute_psnr(cover, stego_s)
            p_p = compute_psnr(cover, stego_p)
            psnr_seq.append(p_s)
            psnr_prng.append(p_p)

            c_s = histogram_chi_square(cover, stego_s)
            c_p = histogram_chi_square(cover, stego_p)
            # Average chi2 across RGB
            avg_c_s = (c_s["R"] + c_s["G"] + c_s["B"]) / 3.0
            avg_c_p = (c_p["R"] + c_p["G"] + c_p["B"]) / 3.0
            chi2_seq.append(avg_c_s)
            chi2_prng.append(avg_c_p)

            r_s = rs_analysis(stego_s)
            r_p = rs_analysis(stego_p)
            rs_seq.append(r_s["estimated_rate"])
            rs_prng.append(r_p["estimated_rate"])

            # Report logging
            report_lines.append(f"    Metric            | Sequential | PRNG-Based")
            report_lines.append(f"    ------------------+------------+-----------")
            report_lines.append(f"    PSNR (dB)         | {p_s:10.2f} | {p_p:10.2f}")
            report_lines.append(f"    Avg Chi-Square    | {avg_c_s:10.2f} | {avg_c_p:10.2f}")
            report_lines.append(f"    RS Embed Rate     | {r_s['estimated_rate']:10.4f} | {r_p['estimated_rate']:10.4f}")

        # --- Generate Trend Charts for this image ---
        plot_metric_trends(
            payload_targets, psnr_seq, psnr_prng,
            metric_name=f"{img_name} - PSNR",
            save_path=os.path.join(output_dir, f"{img_name.lower()}_trend_psnr.png"),
            y_label="PSNR (dB)"
        )
        plot_metric_trends(
            payload_targets, chi2_seq, chi2_prng,
            metric_name=f"{img_name} - Avg Chi-Square",
            save_path=os.path.join(output_dir, f"{img_name.lower()}_trend_chi2.png"),
            y_label="Chi-Square Value"
        )
        plot_metric_trends(
            payload_targets, rs_seq, rs_prng,
            metric_name=f"{img_name} - RS Embed Rate",
            save_path=os.path.join(output_dir, f"{img_name.lower()}_trend_rs.png"),
            y_label="Estimated Rate (0.0 to 1.0)"
        )
        print("  -> Generated Trend Charts")
        report_lines.append("\n" + "=" * 40 + "\n")

    # Save the master report
    with open(os.path.join(output_dir, "master_experiment_report.txt"), "w") as f:
        f.write("\n".join(report_lines))
    print(f"\nExperiment Complete! All visualisations and data saved to '{output_dir}/'")


if __name__ == "__main__":
    run_experiment()
