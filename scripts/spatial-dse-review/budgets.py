#!/usr/bin/env python3
"""Analytical bounds from retained V120 evidence; NOT an ESP32/RTL simulator."""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HANDOFF = "experiments/python-gamebub-v120/handoff.json"
PARENT = "experiments/python-gamebub-v120/audit/B-parent-terminal.json"


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build():
    manifest = json.loads((ROOT / HANDOFF).read_text())
    audit = json.loads((ROOT / PARENT).read_text())
    if audit["status"] != "PASS" or audit["failed_checks"]:
        raise ValueError("Parent evidence is not a passing audit")
    origins = manifest["source_origins"]
    if len(origins) != 18:
        raise ValueError("Unexpected Source B composition")
    for source in origins.values():
        if sha(source["path"]) != source["sha256"]:
            raise ValueError("Source B changed: " + source["path"])
    rows = sorted((r for r in audit["run_results"] if r["variant"] == "row"),
                  key=lambda r: r["profile"])
    if [r["profile"] for r in rows] != [0, 1]:
        raise ValueError("Expected the two retained row-service fixtures")
    cycles = [r["last_outer_to_commit_cycles"] for r in rows]
    cap, fps, width, height = 49152, 30, 720, 480
    latency = []
    for mhz in (100, 125):
        # For integer clocks/cycles this strict bound excludes exactly 10 ms.
        exclusive = mhz * 10000
        for row in rows:
            n = row["last_outer_to_commit_cycles"]
            latency.append({
                "assumed_complete_parent_MHz": mhz,
                "profile": row["profile"], "cycles": n,
                "conditional_ms": float(Fraction(n, mhz * 1000)),
                "strict_max_cycles": exclusive - 1,
                "minimum_cycles_to_remove": max(0, n - exclusive + 1),
                "fits_arithmetic_budget_only": n < exclusive,
            })
    transport = []
    for payload, header, frame_header in ((1024, 40, 0), (1400, 40, 0), (1400, 12, 16)):
        fragments = math.ceil(cap / payload)
        total = cap + fragments * (header + 28) + frame_header
        transport.append({
            "fragment_payload_bytes": payload, "application_header_bytes": header,
            "extra_frame_header_bytes": frame_header, "fragments": fragments,
            "bytes_per_frame_including_IPv4_UDP": total,
            "required_Mbps_at_30fps": float(Fraction(total * fps * 8, 1000000)),
            "excludes": "Wi-Fi/MAC/security/retries/control/FEC; no IP options or fragmentation",
            "status": "MSV1 framing budget" if payload == 1024 else "hypothetical negotiated framing",
        })
    sensitivity = []
    for fraction in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)):
        for lanes in (1, 2, 4):
            projected = Fraction(cycles[1]) * (1 - fraction + fraction / lanes)
            sensitivity.append({
                "assumed_parallelizable_fraction": float(fraction), "lanes": lanes,
                "idealized_cycles": float(projected),
                "conditional_ms_at125": float(projected / 125000),
                "scope": "Amdahl sensitivity; unknown fraction, perfect scaling, no new overhead",
            })
    differential = cycles[1] - cycles[0]
    needed = max(0, cycles[1] - 1250000 + 1)
    rgb = width * height * 2
    yuv = width * height * 3 // 2
    return {
        "schema": "gamebub-spatial-review-analytical-bounds-v1",
        "evidence_base_commit": "ddace39683118b2fa97267f484f534ea046ed798",
        "evidence": {p: sha(p) for p in (HANDOFF, PARENT)},
        "source_B_18_hashes_verified": True,
        "qualified_component_MHz": manifest["qualified_internal_component_clock_MHz"],
        "milestones": manifest["milestones"],
        "scope": "Analytical calculations, not new RTL, CPU, RF, memory or board simulation",
        "canvas": {"width": width, "height": height, "source_fps": fps,
                   "frame_interval_ms": float(Fraction(1000, fps)),
                   "YUV420_bytes": yuv, "RGB565_bytes": rgb},
        "latency": latency,
        "profile_difference_what_if": {
            "extra_cycles": differential, "needed_reduction_for_strict125": needed,
            "fraction_of_difference_to_remove": float(Fraction(needed, differential)),
            "limit": "Difference between profiles is NOT measured causal stall attribution",
        },
        "transport": transport,
        "payload_only_Mbps": float(Fraction(cap * fps * 8, 1000000)),
        "QSPI_payload_only_lower_bounds": [
            {"clock_MHz": mhz, "lanes": 4,
             "cap_serialization_ms": float(Fraction(cap * 8, 4 * mhz * 1000)),
             "status": "40 MHz requested in current writes" if mhz == 40 else "existing slower driver option",
             "excludes": "command/address/dummy/CS/setup/credit reads/locking/CPU gaps"}
            for mhz in (10, 16, 20, 40)
        ],
        "queue_age_at_payload_rate": [
            {"bytes": n, "drain_time_ms": float(Fraction(n * 1000, cap * fps))}
            for n in (8192, 16384, 32768, cap, cap * 2)
        ],
        "illustrative_memory": {
            "assumptions": "RGB565 scanout60Hz + write30Hz + one full reference read30Hz; no reuse",
            "scanout_MBps": rgb * 60 / 1000000,
            "write_MBps": rgb * fps / 1000000,
            "reference_MBps": rgb * fps / 1000000,
            "sum_MBps": rgb * (60 + fps + fps) / 1000000,
            "raw_16bit_100MHz_ceiling_MBps": 200,
            "limit": "Not actual scanout geometry or measured controller throughput; excludes other work",
        },
        "arithmetic_at125_for10ms": {
            "cycles_per_coded_pixel": float(Fraction(1250000, width * height)),
            "cycles_per_YUV420_sample": float(Fraction(1250000, yuv)),
            "YUV420_to_cap_ratio": float(Fraction(yuv, cap)),
        },
        "ideal_lane_sensitivity": sensitivity,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("Wrote analytical bounds; 18 frozen source hashes verified:", args.output)


if __name__ == "__main__":
    main()
