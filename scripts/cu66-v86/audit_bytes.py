#!/usr/bin/env python3
"""Independently audit retained CS86 packet byte counts against V85 and controls."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V86_DIR = ROOT / "experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a"
V85_DIR = ROOT / "experiments/python-gamebub-v85/wire-attempts/20261106T130658877580Z-53860fda"
OUT = ROOT / "experiments/python-gamebub-v86/byte-audit.json"
V86_RESULT = V86_DIR / "results.json"
V85_RESULT = V85_DIR / "results.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def stats(values):
    return {
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
        "total": sum(values),
    }


def paired_counts(rows):
    return {
        "smaller": sum(row["byte_delta"] < 0 for row in rows),
        "equal": sum(row["byte_delta"] == 0 for row in rows),
        "larger": sum(row["byte_delta"] > 0 for row in rows),
        "fits_49152": sum(row["wire_bytes"] <= 49152 for row in rows),
    }


def by_identity(row):
    return row["cohort"], row["ordinal"], row["fid"]


def load_report(path, expected_status):
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("status") != expected_status or report.get("sources") != 457:
        raise ValueError(f"unexpected retained report status/coverage: {path}")
    return report


def verify_length(row):
    if sum(row["components"].values()) != row["wire_bytes"]:
        raise ValueError(f"component sum mismatch at {row.get('configuration')} {by_identity(row)}")


def main():
    v86_report = load_report(V86_RESULT, "PASS_NATIVE_FULL_FRAME_PARITY")
    v85_report = load_report(V85_RESULT, "PASS_NATIVE_FULL_FRAME_PARITY")
    v86_rows = read_rows(V86_DIR / "frames.jsonl")
    v85_rows = read_rows(V85_DIR / "frames.jsonl")
    if (len(v86_rows) != 457 * 6 or len(v85_rows) != 457 * 4
            or v86_report.get("received_packets") != len(v86_rows)
            or v85_report.get("received_packets") != len(v85_rows)):
        raise ValueError("retained report/row coverage mismatch")
    for report, directory in ((v86_report, V86_DIR), (v85_report, V85_DIR)):
        expected = report.get("artifacts_sha256", {}).get("frames.jsonl")
        if not expected or sha256(directory / "frames.jsonl") != expected:
            raise ValueError(f"frames.jsonl hash mismatch: {directory}")
    source_paths = {
        "v86_builder": ROOT / "scripts/cu66-v86/run_wire.py",
        "v86_receiver": ROOT / "experiments/python-gamebub-v86/receiver.cpp",
        "v85_builder": ROOT / "scripts/cu66-v85/run_wire.py",
        "v85_receiver": ROOT / "experiments/python-gamebub-v85/receiver.cpp",
    }
    for name in ("v86_builder", "v86_receiver"):
        rel = str(source_paths[name].relative_to(ROOT))
        if v86_report.get("source_sha256", {}).get(rel) != sha256(source_paths[name]):
            raise ValueError(f"V86 source hash mismatch: {rel}")
    for name in ("v85_builder", "v85_receiver"):
        rel = str(source_paths[name].relative_to(ROOT))
        if v85_report.get("source_sha256", {}).get(rel) != sha256(source_paths[name]):
            raise ValueError(f"V85 source hash mismatch: {rel}")
    for row in v86_rows + v85_rows:
        verify_length(row)
        if row["byte_delta"] != row["wire_bytes"] - row["original_packet_bytes"]:
            raise ValueError(f"paired delta mismatch at {by_identity(row)}")

    v86_configs = {item["name"]: item for item in v86_report["configurations"]}
    if len(v86_configs) != 6:
        raise ValueError("expected six V86 configurations")
    v86_by_config = {name: [] for name in v86_configs}
    for row in v86_rows:
        if row["configuration"] not in v86_by_config:
            raise ValueError(f"unknown V86 config {row['configuration']}")
        v86_by_config[row["configuration"]].append(row)

    full_summary = {}
    for name, rows in v86_by_config.items():
        if len(rows) != 457:
            raise ValueError(f"incomplete V86 configuration {name}")
        full_summary[name] = {
            "kind": v86_configs[name]["kind"],
            "cap": v86_configs[name]["cap"],
            "sources": len(rows),
            "wire_bytes": stats([row["wire_bytes"] for row in rows]),
            "paired_byte_delta_vs_original": stats([row["byte_delta"] for row in rows]),
            **paired_counts(rows),
        }

    old_rows = {(row["cap"], by_identity(row)): row for row in v85_rows}
    v86_rows_by_pair = {
        (row["configuration"], by_identity(row)): row for row in v86_rows
    }
    baseline_comparisons = {}
    unchanged = ("qmap", "chunk_directory", "AB38_payloads", "HUD", "outer_CRC")
    for cap in (256, 65536):
        name = f"copy_v2_cap{cap}"
        deltas = []
        for identity in sorted(by_identity(row) for row in v86_by_config[name]):
            newer = v86_rows_by_pair[(name, identity)]
            older = old_rows[(cap, identity)]
            delta = newer["wire_bytes"] - older["wire_bytes"]
            if delta != -148:
                raise ValueError(f"V85/V86 byte delta is not -148 at cap={cap}, {identity}: {delta}")
            if (older["components"].get("header") != 256
                    or newer["components"].get("header") != 128
                    or older["components"].get("mode_map", 0)
                    - newer["components"].get("mode_body", 0) != 20):
                raise ValueError(f"unexpected envelope sizes at cap={cap}, {identity}")
            for key in unchanged:
                if older["components"].get(key) != newer["components"].get(key):
                    raise ValueError(f"component {key} differs at cap={cap}, {identity}")
            deltas.append(delta)
        baseline_comparisons[str(cap)] = {
            "pairs": len(deltas),
            "wire_byte_delta_v86_minus_v85": stats(deltas),
            "verified_constant_delta": -148,
            "removed_bytes": {"old_header_to_new_header": 128, "nested_mode_map_header": 20},
            "unchanged_components": list(unchanged),
        }

    pair_map = {}
    for config in ("copy_v2_cap256", "copy_group_cap256",
                   "copy_v2_cap65536", "copy_group_cap65536"):
        pair_map[config] = {by_identity(row): row for row in v86_by_config[config]}
    group_comparisons = {}
    for cap in (256, 65536):
        old_name, new_name = f"copy_v2_cap{cap}", f"copy_group_cap{cap}"
        deltas = []
        mode_lengths = []
        for identity, baseline in pair_map[old_name].items():
            grouped = pair_map[new_name][identity]
            delta = grouped["wire_bytes"] - baseline["wire_bytes"]
            expected_delta = (grouped["components"]["mode_body"]
                              - baseline["components"]["mode_body"])
            if delta != expected_delta:
                raise ValueError(f"group body is not the only byte delta at cap={cap}, {identity}")
            for key in ("header", "qmap", "chunk_directory", "AB38_payloads", "HUD", "outer_CRC"):
                if grouped["components"][key] != baseline["components"][key]:
                    raise ValueError(f"group changed non-map component {key} at cap={cap}, {identity}")
            if grouped["map_method"] != (0 if grouped["key"] else 3):
                raise ValueError(f"unexpected group map method at cap={cap}, {identity}")
            deltas.append(delta)
            mode_lengths.append(grouped["components"]["mode_body"]
                                - baseline["components"]["mode_body"])
        group_comparisons[str(cap)] = {
            "pairs": len(deltas),
            "group_minus_copy_v2_wire_bytes": stats(deltas),
            "group_minus_copy_v2_mode_body_bytes": stats(mode_lengths),
            "keys_method_0": sum(row["key"] and row["map_method"] == 0 for row in v86_by_config[new_name]),
            "deltas_method_3": sum((not row["key"]) and row["map_method"] == 3 for row in v86_by_config[new_name]),
            "only_changed_component": "mode_body",
        }

    whole_copy_group = full_summary["copy_group_cap65536"]["wire_bytes"]["total"]
    original_total = sum(row["original_packet_bytes"] for row in v86_by_config["copy_group_cap65536"])
    whole_all_visible = full_summary["all_visible_cap65536"]["wire_bytes"]["total"]
    output = {
        "schema": "cu66-v86-byte-audit-v1",
        "status": "PASS_INDEPENDENT_BYTE_AUDIT",
        "inputs": {
            "v86_results": str(V86_RESULT.relative_to(ROOT)),
            "v86_results_sha256": sha256(V86_RESULT),
            "v86_frames": str((V86_DIR / "frames.jsonl").relative_to(ROOT)),
            "v86_frames_sha256": sha256(V86_DIR / "frames.jsonl"),
            "v85_results": str(V85_RESULT.relative_to(ROOT)),
            "v85_results_sha256": sha256(V85_RESULT),
            "v85_frames": str((V85_DIR / "frames.jsonl").relative_to(ROOT)),
            "v85_frames_sha256": sha256(V85_DIR / "frames.jsonl"),
            "audit_script": "scripts/cu66-v86/audit_bytes.py",
            "audit_script_sha256": sha256(Path(__file__).resolve()),
            "wire_sources_sha256": {
                name: sha256(path) for name, path in source_paths.items()
            },
        },
        "coverage": {
            "v86_sources": v86_report["sources"],
            "v86_packets": len(v86_rows),
            "v86_native_status": v86_report["status"],
            "v85_sources": v85_report["sources"],
            "v85_packets": len(v85_rows),
            "v85_native_status": v85_report["status"],
        },
        "v86_configurations": full_summary,
        "copy_v2_against_frozen_v85": baseline_comparisons,
        "copy_group_against_copy_v2": group_comparisons,
        "whole_plane_totals": {
            "original_packet_bytes": original_total,
            "copy_group_cap65536_bytes": whole_copy_group,
            "copy_group_minus_original_bytes": whole_copy_group - original_total,
            "copy_group_percent_below_original": round((original_total - whole_copy_group) * 100 / original_total, 6),
            "all_visible_cap65536_bytes": whole_all_visible,
            "all_visible_minus_original_bytes": whole_all_visible - original_total,
            "paired_comparison_scope": "actual CS86 full packet bytes versus retained original packet bytes; all-visible control uses the same CS86 envelope",
        },
        "claims_excluded": [
            "FPGA or ESP32 integration, capacity, or timing",
            "sustained 30 fps or sub-10-ms completion",
            "general compression superiority beyond the retained corpus and configurations",
        ],
    }
    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE_V86_BYTE_AUDIT {OUT.relative_to(ROOT)}")
    print(json.dumps(output["whole_plane_totals"], sort_keys=True))


if __name__ == "__main__":
    main()
