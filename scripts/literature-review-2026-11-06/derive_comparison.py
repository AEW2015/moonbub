#!/usr/bin/env python3
"""Recompute review arithmetic from frozen local evidence; no codec benchmark."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs/literature-review-2026-11-06/derived-comparison.json"
INPUTS = {
    "v88_wire": "experiments/python-gamebub-v88/wire/results.json",
    "v89_observations": "experiments/python-gamebub-v89/observations/index.json",
    "v90_summary": "experiments/python-gamebub-v90/summary.json",
}


def derive():
    evidence = {k: json.loads((ROOT / v).read_text()) for k, v in INPUTS.items()}
    wire, obs, v90 = (evidence[k] for k in INPUTS)
    n = v90["native_sources"]
    assert n == wire["native_sources"] == obs["record_count"] == 457
    width, height, fps = 720, 480, 30
    pixels = width * height
    cap = 49152
    policies = []
    for row in wire["summaries"]:
        size = row["wire_bytes"]
        policies.append({
            "policy": "V88_" + row["policy"], "frames": n,
            "total_bytes": size["total"], "max_bytes": size["max"],
            "fits_49152": row["fits_49152"],
            "mean_bytes": size["total"] / n,
            "complete_frame_bits_per_pixel": size["total"] * 8 / (n * pixels),
            "nominal_30fps_mbps": size["total"] * 8 * fps / (n * 1e6),
        })
    p = v90["policy_summaries"][0]
    assert p["wire_bytes"] == v90["policy_summaries"][1]["wire_bytes"]
    assert p["selected_masks"] == v90["policy_summaries"][1]["selected_masks"]
    policies.append({
        "policy": "V90_proxy_LOW_and_HIGH_same_distinct_packets", "frames": n,
        "total_bytes": p["wire_bytes"]["total"], "max_bytes": p["wire_bytes"]["max"],
        "fits_49152": p["fits_49152"],
        "mean_bytes": p["wire_bytes"]["total"] / n,
        "complete_frame_bits_per_pixel": p["wire_bytes"]["total"] * 8 / (n * pixels),
        "nominal_30fps_mbps": p["wire_bytes"]["total"] * 8 * fps / (n * 1e6),
    })
    contexts = obs["totals"]["65536"]["contexts"]
    bits = sum(c["plain_bits"] for c in contexts)
    symbols = sum(c["rice_values"] for c in contexts)
    assert bits == 37656819 and symbols == 11435381
    # Service work only. Different resources overlap; these values cannot be
    # subtracted from modeled completion or called predicted FPGA latency.
    service = {
        "all_BR88_plain_bits": bits, "all_BR88_Rice_symbols": symbols,
        "mean_plain_bits_per_frame": bits / n,
        "mean_Rice_symbols_per_frame": symbols / n,
        "mean_bit_service_ms_at_100MHz_one_cycle_per_bit": bits / n / 1e5,
        "ideal_mean_symbol_service_ms_at_100MHz_one_cycle_per_symbol": symbols / n / 1e5,
        "interpretation": "Hypothetical isolated aggregate work, not completion-time prediction; refill, CRC, events, scatter, tables, stalls, memory, transforms and validation are excluded.",
    }
    # The source reports HLC's evaluated target rates; DSC is a whitepaper
    # example. These are rate arithmetic, not experiments on our source frames.
    rate_examples = []
    for method, bpp in [("HLC_paper_target", 1.0), ("HLC_paper_target", 1.75),
                        ("DSC_2014_whitepaper_example", 8.0),
                        ("JPEG_XS_10_to_1_from_8bit_420_example", 1.2)]:
        rate_examples.append({"method": method, "coded_bpp": bpp,
                              "image_bytes_per_frame_before_wrappers": pixels * bpp / 8,
                              "nominal_30fps_mbps_before_wrappers": pixels * bpp * fps / 1e6})
    result = {
        "schema": "post-v90-literature-review-arithmetic-v1",
        "status": "DERIVED_FROM_FROZEN_RESULTS_NOT_NEW_CODEC_OR_HARDWARE_BENCHMARK",
        "baseline_commit": "7c24b4d80b2a79a45a9a06ddc82a9ef8f83ce030",
        "input_sha256": {v: hashlib.sha256((ROOT / v).read_bytes()).hexdigest() for v in INPUTS.values()},
        "geometry": {"width": width, "height": height, "nominal_fps": fps,
                     "unique_source_frames": n, "source_family_count": 1},
        "rate_scope": "Complete research frame bytes; excludes network/QSPI framing, ACKs, retries, audio and input. Nominal 30Hz normalization, not measured throughput or native source cadence.",
        "packet_cap": {"bytes": cap, "complete_frame_bpp": cap * 8 / pixels,
                       "nominal_30fps_mbps": cap * 8 * fps / 1e6,
                       "is_physical_BRAM_or_SRAM_limit": False},
        "policies": policies,
        "V90_proxy_over_AB38_complete_bytes_percent": (policies[-1]["total_bytes"] / policies[0]["total_bytes"] - 1) * 100,
        "all_BR88_component_work": service,
        "V90_selected_oracles": v90["exact_oracles"],
        "literature_rate_examples_not_quality_matched": rate_examples,
        "FSE_DTable_logical_bytes_from_pinned_macro": [
            {"table_log": log, "one_table_bytes": 4 * (1 + (1 << log)),
             "four_tables_bytes": 16 * (1 + (1 << log))} for log in (8, 9, 10)
        ],
        "physical_30fps_proven": False, "validated_FPGA_under10ms_proven": False,
    }
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare retained arithmetic without modifying files")
    args = parser.parse_args()
    content = derive()
    if args.check:
        if OUTPUT.read_text() != content:
            raise SystemExit("Review arithmetic differs from retained output")
        print("PASS: retained arithmetic matches all three frozen evidence inputs")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content)
        print(OUTPUT)
