#!/usr/bin/env python3
"""Recompute V122 baseline and retained row-profile accounting (stdlib only)."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARENT_DIR = ROOT / "experiments/python-gamebub-v121/integrated-study/live-guard/attempts/20261109T233010320226Z"
PARENT = PARENT_DIR / "receipt.json"
V121 = ROOT / "experiments/python-gamebub-v121/results.json"
INDEX = ROOT / "experiments/python-gamebub-v121/integration/results.json"
V120_BASE = ROOT / "experiments/python-gamebub-v120/audit/baseline.json"
V120_HANDOFF = ROOT / "experiments/python-gamebub-v120/handoff.json"
OUT = ROOT / "experiments/python-gamebub-v122/memory-study/results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def main() -> None:
    parent, v121, index, base, handoff = map(load, (PARENT, V121, INDEX, V120_BASE, V120_HANDOFF))
    # The integration index guards this precise parent receipt and its results index.
    binding = index["stages"]["parent"]["receipt"]
    assert binding["path"] == str(PARENT.relative_to(ROOT))
    assert sha(PARENT) == binding["sha256"]
    assert sha(INDEX) == v121["functional_index"]["sha256"]

    rows = []
    for run in parent["runs"]:
        if run.get("variant") != "row":
            continue
        lc, f = run["live_case"], run["fences"]
        event_art = run["artifacts"]["events.jsonl"]
        event_path = PARENT_DIR / event_art["path"]
        assert sha(event_path) == event_art["sha256"]
        type_counts = {}
        last_cycles = []
        first_cycles = []
        with gzip.open(event_path, "rt", encoding="utf-8") as stream:
            for line in stream:
                event = json.loads(line)
                key = event.get("type", "unknown") + (":" + event["stage"] if "stage" in event else "")
                type_counts[key] = type_counts.get(key, 0) + 1
                if "first_cycle" in event:
                    first_cycles.append(event["first_cycle"])
                if "last_cycle" in event:
                    last_cycles.append(event["last_cycle"])
        assert sum(type_counts.values()) == event_art["rows"]
        rows.append({
            "profile": run["profile"], "seed": run["seed"], "case": lc["id"],
            "last_outer_to_commit_cycles": lc["last_outer_to_commit_cycles"],
            "commit_cycle": lc["commit_cycle"], "last_outer_cycle": lc["last_outer_cycle"],
            "canonical_bytes": lc["canonical_bytes"], "hud_bytes": lc["hud_bytes"],
            "write_requests": lc["write_requests"], "write_acks": lc["write_acks"],
            "service": run["service"], "fences": f,
            "post_reconstruction_tail_cycles": f["commit"] - f["reconstruct_done"],
            "post_last_outer_to_reconstruction_cycles": f["reconstruct_done"] - lc["last_outer_cycle"],
            "phase_edge_total": sum(f["phase_edges"]),
            "phase_edge_total_matches_start_to_commit": sum(f["phase_edges"]) == lc["start_to_commit_cycles"],
            "event_trace": {"path": str(event_path.relative_to(ROOT)), "sha256": sha(event_path),
                            "rows": event_art["rows"], "type_counts": type_counts,
                            "first_cycle_min": min(first_cycles), "last_cycle_max": max(last_cycles)},
        })
    rows.sort(key=lambda r: r["profile"])

    # Verify V121's selected origins and V120's frozen Source B input set.
    v121_sources = {}
    for alias, origin in index["source_origins"].items():
        path, expected = origin["path"], origin["sha256"]
        actual = sha(ROOT / path)
        v121_sources[path] = {"expected_sha256": expected, "current_sha256": actual, "matches": actual == expected}
    sourceb = {}
    for alias, origin in handoff["source_origins"].items():
        path, expected = origin["path"], origin["sha256"]
        actual = sha(ROOT / path)
        sourceb[path] = {"expected_sha256": expected, "current_sha256": actual, "matches": actual == expected}

    markers = []
    for item in base["protected_files"]:
        path = ROOT / item["path"]
        st = path.stat()
        markers.append({"path": item["path"], "sha256_matches": sha(path) == item["sha256"],
                        "bytes_matches": st.st_size == item["bytes"], "mtime_ns_matches": st.st_mtime_ns == item["mtime_ns"]})
    assert len(v121_sources) == 18 and all(item["matches"] for item in v121_sources.values())
    assert len(sourceb) == 18 and all(item["matches"] for item in sourceb.values())
    assert all(item["sha256_matches"] and item["bytes_matches"] and item["mtime_ns_matches"] for item in markers)
    assert len(rows) == 2 and all(r["event_trace"]["rows"] == sum(r["event_trace"]["type_counts"].values()) for r in rows)

    result = {
        "schema": "v122-retained-row-stall-audit-v1",
        "inputs": {str(p.relative_to(ROOT)): sha(p) for p in (PARENT, INDEX, V121, V120_BASE, V120_HANDOFF)},
        "baseline_125": {"WNS_ns": v121["candidate_result"]["timing"]["WNS_ns"],
                         "TNS_ns": v121["candidate_result"]["timing"]["TNS_ns"],
                         "setup_failing": v121["candidate_result"]["timing"]["setup_failing"],
                         "qualified_source_B_100MHz_unchanged": v121["source_B_18_original_files_unchanged"]},
        "row_profiles": rows,
        "row_cycle_difference_profile1_minus_profile0": rows[1]["last_outer_to_commit_cycles"] - rows[0]["last_outer_to_commit_cycles"],
        "strict_125MHz_10ms_target_cycles": 1_250_000,
        "profile1_cycles_to_save_for_strict_target": rows[1]["last_outer_to_commit_cycles"] - 1_250_000 + 1,
        "profile1_post_outer_to_reconstruction_cycles_exceeds_target_by": rows[1]["post_last_outer_to_reconstruction_cycles"] - 1_250_000 + 1,
        "row_profile_delta_is_causal_stall_attribution": False,
        "source_B_source_hashes": sourceb,
        "V121_selected_source_hashes": v121_sources,
        "protected_markers": markers,
        "attribution_gaps": ["No exclusive, non-overlapping per-cycle wait ownership counters are retained.",
                             "No calibrated RF, ESP32 CPU, or physical SDRAM latency trace exists; the three-edge service rule is an abstract model.",
                             "Validation and HUD/write stages have fence edges and overlapping stall vectors, not additive exclusive durations."],
        "next_experiment_counters": ["wait_producer_full_edges", "wait_software_hud_edges", "wait_physical_request_edges",
                                     "wait_hash_delivery_edges", "wait_service_edges", "wait_reason_priority_edges",
                                     "cpu_decode_active_edges", "cpu_decode_blocked_edges", "exclusive_stage_owner_edges"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("baseline_125", "row_cycle_difference_profile1_minus_profile0", "profile1_cycles_to_save_for_strict_target", "protected_markers")}, indent=2))


if __name__ == "__main__":
    main()
