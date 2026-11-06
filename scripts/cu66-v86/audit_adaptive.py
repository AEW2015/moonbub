#!/usr/bin/env python3
"""Independently audit retained offline adaptive byte selection and replay."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTIVE = ROOT / "experiments/python-gamebub-v86/adaptive"
ATTEMPT = ADAPTIVE / "attempts/20261106T140824748437Z-23b07c06"
WIRE = ROOT / "experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a"
OUT = ROOT / "experiments/python-gamebub-v86/adaptive-audit.json"
CONFIGS = (
    "copy_v2_cap256", "copy_group_cap256", "all_visible_cap256",
    "copy_v2_cap65536", "copy_group_cap65536", "all_visible_cap65536",
)
COMPARE_FIELDS = (
    "accepted", "fid", "generation", "canonical_sha256", "hud_sha256",
    "display_sha256", "coefficient_sha256", "root", "seal", "wire_bytes",
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def key(row):
    return row["cohort"], row["ordinal"], row["fid"]


def main():
    selected = read_json(ADAPTIVE / "results.json")
    attempt_report_path = ROOT / selected["selected_report"]
    need(attempt_report_path == ATTEMPT / "results.json", "selected attempt path differs")
    attempt = read_json(attempt_report_path)
    wire_report_path = WIRE / "results.json"
    wire_report = read_json(wire_report_path)
    adaptive_rows = read_rows(ATTEMPT / "frames.jsonl")
    wire_rows = read_rows(WIRE / "frames.jsonl")
    need(attempt["status"] == "PASS_NATIVE_RATE_ONLY_MIXED_HISTORY_AND_REPLAY", "adaptive attempt status")
    need(wire_report["status"] == "PASS_NATIVE_FULL_FRAME_PARITY", "wire reference status")
    need(len(adaptive_rows) == 457 and len(wire_rows) == 457 * 6, "row count mismatch")
    need(attempt["native_sources"] == 457 and attempt["accepted_new_packets"] == 457
         and attempt["accepted_exact_replays"] == 457, "adaptive report coverage mismatch")
    need(attempt["configuration_order"] == wire_report["configurations"], "configuration order mismatch")

    # Verify every source pin carried by the adaptive report, including the
    # full-wire reference, candidate builder, receiver, and adaptive selector.
    for report_name, report in (("selected", selected), ("attempt", attempt)):
        for rel, expected in report["source_sha256"].items():
            path = ROOT / rel
            need(path.is_file() and sha256(path) == expected,
                 f"{report_name} source hash mismatch: {rel}")
    need(attempt["wire_report"] == str(wire_report_path.relative_to(ROOT)), "wire report path mismatch")
    need(attempt["wire_report_sha256"] == sha256(wire_report_path), "wire report hash mismatch")
    need(selected["wire_report_sha256"] == sha256(wire_report_path), "selected wire report hash mismatch")
    need(attempt["artifacts_sha256"].get("frames.jsonl") == sha256(ATTEMPT / "frames.jsonl"),
         "adaptive attempt frames hash mismatch")
    need(attempt["artifacts_sha256"].get("sources.tar.gz") == sha256(ATTEMPT / "sources.tar.gz"),
         "adaptive source archive hash mismatch")
    need(attempt["source_archive_sha256"] == sha256(ATTEMPT / "sources.tar.gz"), "archive pin mismatch")

    # Tie the container's receiver hash observation to the exact binary retained
    # with the qualified full-wire campaign.
    wire_binary = WIRE / "receiver.bin"
    binary_hash = sha256(wire_binary)
    need(attempt["receiver_binary_sha256"] == binary_hash, "receiver binary hash differs from qualified wire binary")
    need(wire_report["artifacts_sha256"].get("receiver.bin") == binary_hash,
         "qualified wire report binary artifact hash mismatch")

    # Bind every file recorded in the existing 17-file adaptive manifest.
    manifest = read_json(ADAPTIVE / "artifact-manifest.json")
    manifest_files = manifest.get("files", {})
    need(len(manifest_files) == 17, "adaptive artifact manifest file count is not 17")
    for rel, expected in manifest_files.items():
        path = ROOT / rel
        need(path.is_file() and sha256(path) == expected, f"adaptive manifest hash mismatch: {rel}")

    full = {}
    for row in wire_rows:
        full[(key(row), row["configuration"])] = row
    need(len(full) == 457 * 6, "duplicate/missing full-wire source/configuration pair")

    new_rows = adaptive_rows
    replay_rows = adaptive_rows
    need(all(row["replayed"]["replayed"] and row["decoded"]["replayed"] is False
             for row in new_rows), "new-packet/replay flags mismatch")

    choice_counts = {name: 0 for name in CONFIGS}
    cohort_counts = {str(cohort): 0 for cohort in range(4)}
    candidate_comparison_counts = {name: {"smaller": 0, "equal": 0, "larger": 0}
                                   for name in CONFIGS}
    selected_total = original_total = 0
    all_visible_total = 0
    selected_savings = []
    group_savings = []
    original_savings = []
    all_visible_savings = []
    transition_count = 0
    previous_by_cohort = {}
    for row in new_rows:
        identity = key(row)
        cohort_counts[str(row["cohort"])] += 1
        candidates = row["candidates"]
        need(len(candidates) == 6 and [item["configuration"] for item in candidates] == list(CONFIGS),
             f"candidate list/order mismatch at {identity}")
        for candidate in candidates:
            reference = full[(identity, candidate["configuration"])]
            need(candidate["wire_bytes"] == reference["wire_bytes"]
                 and candidate["packet_sha256"] == reference["packet_sha256"],
                 f"candidate differs from full-wire truth at {identity} {candidate['configuration']}")
            need(candidate["wire_bytes"] == reference["wire_bytes"], "candidate wire byte mismatch")
            if candidate["wire_bytes"] < row["wire_bytes"]:
                candidate_comparison_counts[candidate["configuration"]]["smaller"] += 1
            elif candidate["wire_bytes"] == row["wire_bytes"]:
                candidate_comparison_counts[candidate["configuration"]]["equal"] += 1
            else:
                candidate_comparison_counts[candidate["configuration"]]["larger"] += 1

        winner = min(enumerate(candidates), key=lambda pair: (pair[1]["wire_bytes"], pair[0]))[1]
        need(row["configuration"] == winner["configuration"], f"non-minimal/tie-order choice at {identity}")
        chosen = full[(identity, row["configuration"])]
        need(row["wire_bytes"] == chosen["wire_bytes"]
             and row["packet_sha256"] == chosen["packet_sha256"], f"selected packet differs at {identity}")
        need(all(row["decoded"].get(field) == chosen["decoded"].get(field) for field in COMPARE_FIELDS),
             f"selected native decode differs from full-wire row at {identity}")
        need(row["decoded"]["wire_bytes"] == row["wire_bytes"], f"selected decode byte count mismatch at {identity}")
        choice_counts[row["configuration"]] += 1
        previous = previous_by_cohort.get(row["cohort"])
        if previous is not None and previous != row["configuration"]:
            transition_count += 1
        previous_by_cohort[row["cohort"]] = row["configuration"]

        selected_total += row["wire_bytes"]
        original = chosen["original_packet_bytes"]
        original_total += original
        selected_savings.append(chosen["original_packet_bytes"] - row["wire_bytes"])
        group = full[(identity, "copy_group_cap65536")]["wire_bytes"]
        all_visible = full[(identity, "all_visible_cap65536")]["wire_bytes"]
        group_savings.append(group - row["wire_bytes"])
        all_visible_savings.append(all_visible - row["wire_bytes"])
        original_savings.append(original - row["wire_bytes"])
        all_visible_total += all_visible

    # Check each replay's output equality with the just-accepted result, with
    # only the replayed marker changing from false to true.
    for index, (new, replay) in enumerate(zip(new_rows, replay_rows, strict=True)):
        need(key(new) == key(replay), f"replay identity mismatch at row {index}")
        need(new["decoded"]["replayed"] is False and replay["replayed"]["replayed"] is True,
             f"replay marker mismatch at row {index}")
        for field in COMPARE_FIELDS:
            need(new["decoded"].get(field) == replay["replayed"].get(field),
                 f"replay output changed field {field} at row {index}")
        need(set(new["decoded"]) == set(replay["replayed"]), f"replay output fields differ at row {index}")

    expected_counts = {"0": 119, "1": 119, "2": 119, "3": 100}
    need(cohort_counts == expected_counts, f"cohort distribution mismatch: {cohort_counts}")
    need(transition_count == 72, f"adaptive transition count differs: {transition_count}")
    need(selected_total == 7929974 and group_savings == [
        full[(key(row), "copy_group_cap65536")]["wire_bytes"] - row["wire_bytes"]
        for row in new_rows
    ], "selected/group byte calculation mismatch")
    need(sum(group_savings) == 979, "group savings total mismatch")
    need(sum(all_visible_savings) == 78751, "all-visible savings total mismatch")
    need(sum(original_savings) == 16837, "original packet savings total mismatch")
    need(all(value >= 0 for value in all_visible_savings), "selected choice regresses against all-visible")
    need(sum(value > 0 for value in all_visible_savings) == 406
         and sum(value == 0 for value in all_visible_savings) == 51,
         "all-visible paired improvement/equality counts mismatch")
    need(all(row["wire_bytes"] <= 49152 for row in new_rows), "selected packet exceeds 49,152-byte budget")
    need(selected_total == sum(row["wire_bytes"] for row in new_rows), "selected bytes total mismatch")
    need(original_total == 7946811 and all_visible_total == 8008725, "reference totals mismatch")

    output = {
        "schema": "cu66-v86-adaptive-independent-audit-v1",
        "status": "PASS_ADAPTIVE_BYTE_AND_REPLAY_AUDIT",
        "inputs": {
            "adaptive_selected_report": str((ADAPTIVE / "results.json").relative_to(ROOT)),
            "adaptive_selected_report_sha256": sha256(ADAPTIVE / "results.json"),
            "adaptive_attempt_report": str(attempt_report_path.relative_to(ROOT)),
            "adaptive_attempt_report_sha256": sha256(attempt_report_path),
            "adaptive_rows": str((ATTEMPT / "frames.jsonl").relative_to(ROOT)),
            "adaptive_rows_sha256": sha256(ATTEMPT / "frames.jsonl"),
            "qualified_full_wire_report": str(wire_report_path.relative_to(ROOT)),
            "qualified_full_wire_report_sha256": sha256(wire_report_path),
            "qualified_full_wire_rows": str((WIRE / "frames.jsonl").relative_to(ROOT)),
            "qualified_full_wire_rows_sha256": sha256(WIRE / "frames.jsonl"),
            "adaptive_manifest_sha256": sha256(ADAPTIVE / "artifact-manifest.json"),
            "adaptive_manifest_files_verified": len(manifest_files),
            "receiver_binary_sha256": binary_hash,
            "pinned_source_count_verified": len(attempt["source_sha256"]),
            "audit_script": "scripts/cu66-v86/audit_adaptive.py",
            "audit_script_sha256": sha256(Path(__file__).resolve()),
        },
        "coverage": {
            "unique_source_frames": 457,
            "new_packet_calls": len(new_rows),
            "exact_replay_calls": len(replay_rows),
            "total_receiver_calls": len(new_rows) + len(replay_rows),
            "cohort_sources": cohort_counts,
            "candidates_per_new_source": 6,
            "candidate_packet_pairs_checked_against_full_wire": 457 * 6,
            "all_selected_packets_fit_49152": True,
        },
        "deterministic_selection": {
            "rule": "minimum complete packet bytes, then first configuration in qualified configuration order",
            "configuration_order": list(CONFIGS),
            "choices": choice_counts,
            "cross_variant_transitions_recomputed": transition_count,
            "selected_total_bytes": selected_total,
        },
        "paired_byte_savings": {
            "vs_fixed_copy_group_cap65536": sum(group_savings),
            "vs_matched_all_visible_cap65536": sum(all_visible_savings),
            "vs_original_CU66_packets": sum(original_savings),
            "vs_all_visible_per_frame": {
                "improved": sum(value > 0 for value in all_visible_savings),
                "equal": sum(value == 0 for value in all_visible_savings),
                "regressed": sum(value < 0 for value in all_visible_savings),
            },
            "totals": {
                "adaptive_selected": selected_total,
                "fixed_copy_group_cap65536": selected_total + sum(group_savings),
                "matched_all_visible_cap65536": all_visible_total,
                "original_CU66": original_total,
            },
        },
        "scope": [
            "Offline selector over six pre-encoded complete packet candidates per source; not a live encoder benchmark.",
            "914 receiver calls are 457 unique source frames plus 457 immediate exact replays.",
            "Byte-minimizing rule only; no decode-cost, memory, latency, energy, FPGA, or ESP32 objective/result.",
            "No sustained 30-fps or sub-10-ms proof.",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE_V86_ADAPTIVE_AUDIT {OUT.relative_to(ROOT)}")
    print(json.dumps(output["paired_byte_savings"], sort_keys=True))


if __name__ == "__main__":
    main()
