#!/usr/bin/env python3
"""Hypothetical burst-service sensitivity from retained V121 row counters."""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "experiments/python-gamebub-v122/memory-study/results.json"
OUT = ROOT / "experiments/python-gamebub-v122/memory-study/burst-sensitivity.json"
BURSTS = (8, 16, 32, 64)
TARGET_SAVINGS = 303_198  # strict: 1,553,197 - savings < 1,250,000


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ceil_div(a: int, b: int) -> int:
    return (a + b - 1) // b


def frac_obj(value: Fraction) -> dict:
    return {"numerator": value.numerator, "denominator": value.denominator,
            "decimal_6dp": f"{float(value):.6f}"}


def main() -> None:
    audit = json.loads(AUDIT.read_text())
    parent_rel = "experiments/python-gamebub-v121/integrated-study/live-guard/attempts/20261109T233010320226Z/receipt.json"
    parent = json.loads((ROOT / parent_rel).read_text())
    run = next(r for r in parent["runs"] if r.get("variant") == "row" and r.get("profile") == 1)
    live, service = run["live_case"], run["service"]
    assert live["write_requests"] == live["write_acks"] == 70_080
    assert service["request_bytes"] == 8
    assert service["expanded_bytes"] == service["acked_bytes"] == 560_640
    assert service["service_data_edges"] == 280_320
    assert service["service_overhead_edges"] == 840_385
    assert audit["row_profiles"][1]["last_outer_to_commit_cycles"] == 1_553_197
    assert audit["row_profiles"][1]["post_reconstruction_tail_cycles"] == 193_865
    parent_sha = audit["inputs"][parent_rel]
    assert digest(ROOT / parent_rel) == parent_sha
    event_rel = audit["row_profiles"][1]["event_trace"]["path"]
    event_sha = audit["row_profiles"][1]["event_trace"]["sha256"]
    assert digest(ROOT / event_rel) == event_sha

    reqs = live["write_requests"]
    bytes_total = service["expanded_bytes"]
    data_edges = service["service_data_edges"]
    overhead_per_req = Fraction(service["service_overhead_edges"], reqs)
    baseline_busy = Fraction(data_edges + service["service_overhead_edges"])
    sweep = []
    for burst_bytes in BURSTS:
        burst_count = ceil_div(bytes_total, burst_bytes)
        modeled_overhead = overhead_per_req * burst_count
        modeled_busy = Fraction(data_edges) + modeled_overhead
        saved = baseline_busy - modeled_busy
        minimum_fraction = Fraction(TARGET_SAVINGS, 1) / saved if saved > 0 else None
        sweep.append({
            "burst_bytes": burst_bytes,
            "burst_count_ceiling": burst_count,
            "modeled_overhead_edges": frac_obj(modeled_overhead),
            "unchanged_data_edges": data_edges,
            "modeled_total_busy_edges": frac_obj(modeled_busy),
            "saved_busy_edges_vs_8B_baseline": frac_obj(saved),
            "minimum_unhidden_fraction_for_strict_target": frac_obj(minimum_fraction) if minimum_fraction is not None else None,
            "target_possible_if_fraction_at_most_one": minimum_fraction is not None and minimum_fraction <= 1,
            "net_cycle_reduction_by_fraction": {str(f): frac_obj(saved * Fraction(str(f))) for f in (0, 0.25, 0.5, 0.75, 1)},
        })

    tail = audit["row_profiles"][1]["post_reconstruction_tail_cycles"]
    profile_cycles = live["last_outer_to_commit_cycles"]
    result = {
        "schema": "v122-hypothetical-burst-service-sensitivity-v1",
        "classification": "analytical sensitivity only; not measured memory behavior",
        "retained_inputs": {
            "audit_path": str(AUDIT.relative_to(ROOT)), "audit_sha256": digest(AUDIT),
            "parent_receipt_path": parent_rel, "parent_receipt_sha256": parent_sha,
            "profile1_event_path": event_rel, "profile1_event_sha256": event_sha,
        },
        "observed_profile1": {
            "post_input_cycles": profile_cycles, "write_requests": reqs, "request_bytes": service["request_bytes"],
            "expanded_bytes": bytes_total, "data_edges": data_edges, "overhead_edges": service["service_overhead_edges"],
            "mean_overhead_edges_per_8B_request": frac_obj(overhead_per_req),
            "post_reconstruction_tail_cycles": tail,
        },
        "model_assumptions": {
            "overhead_policy": "Keep the observed mean overhead per original 8-byte request constant; charge that same mean once per modeled burst.",
            "burst_count": "ceil(expanded_bytes / burst_bytes)",
            "data_edges": "Hold observed 16-bit data-edge count unchanged at 280320.",
            "unhidden_fraction": "Hypothetical fraction of saved busy edges that reduces post-input elapsed cycles; includes overlap and out-of-fence effects and is not measured.",
            "no_physical_sdram_or_controller_claim": True,
        },
        "baseline_busy_edges": frac_obj(baseline_busy),
        "required_cycle_reduction_for_strict_target": TARGET_SAVINGS,
        "sweep": sweep,
        "separate_tail_scenario": {
            "assumption": "Ideal elimination or complete overlap of the measured post-reconstruction tail alone.",
            "tail_cycles": tail,
            "remaining_post_input_cycles": profile_cycles - tail,
            "still_over_target_by_cycles": profile_cycles - tail - 1_250_000 + 1,
            "combined_with_burst_savings": False,
            "reason_not_combined": "Burst-service savings may overlap HUD or commit tail work; combining would risk double counting.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "burst_cases": len(sweep),
                      "tail_remaining_cycles": profile_cycles-tail,
                      "tail_still_over_target_by_cycles": profile_cycles-tail-1_250_000+1}, indent=2))


if __name__ == "__main__":
    main()
