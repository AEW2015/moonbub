#!/usr/bin/env python3
"""Independently audit V89 joint row coverage, packet pins, and summaries."""
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v89/joint"
DEST = AREA / "joint-audit.json"
POLICIES = {"AB38_control", "feedback_overhead5", "feedback_overhead15", "all_BR88"}
COSTS = {"LOW", "HIGH"}
SOURCES = {(0, 0), (0, 1), (0, 3), (3, 50)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def stats(values):
    return {"min": min(values), "median": statistics.median(values),
            "max": max(values), "total": sum(values)}


def main():
    top = json.loads((AREA / "results.json").read_text(encoding="utf-8"))
    selected_path = ROOT / top["selected_report"]
    report = json.loads(selected_path.read_text(encoding="utf-8"))
    require(top["schema"] == report["schema"] == "cu66-v89-selected-joint-v1",
            "unexpected joint report schema")
    require(top["status"] == report["status"] == "PASS_SELECTED_ACTUAL_JOINT_SCHEDULES",
            "unexpected joint report status")
    require(top["source_sha256"] == report["source_sha256"], "source pin map differs")
    for name, digest in report["source_sha256"].items():
        path = ROOT / name
        require(path.is_file() and sha(path) == digest, f"source pin mismatch: {name}")

    row_path = selected_path.with_name("rows.jsonl")
    require(row_path.is_file() and
            sha(row_path) == report["artifacts_sha256"].get("rows.jsonl"),
            "selected row stream hash mismatch")
    rows = [json.loads(line) for line in row_path.read_text(encoding="utf-8").splitlines()]
    require(len(rows) == 64, f"expected 64 joint rows, got {len(rows)}")
    ids = {(r["cohort"], r["fid"]) for r in rows}
    require(ids == SOURCES, f"source identity set mismatch: {sorted(ids)}")
    expected = {(c, f, p, cost, alias)
                for c, f in SOURCES for p in POLICIES for cost in COSTS
                for alias in (False, True)}
    observed = [(r["cohort"], r["fid"], r["policy"], r["cost"], r["alias"])
                for r in rows]
    require(len(set(observed)) == 64 and set(observed) == expected,
            "joint source/policy/cost/alias coverage mismatch")
    require(report["selected_source_ids"] == [list(x) for x in sorted(SOURCES)],
            "selected source IDs mismatch")

    wire_top = json.loads((ROOT / "experiments/python-gamebub-v88/wire/results.json")
                          .read_text(encoding="utf-8"))
    wire_path = ROOT / wire_top["selected_report"]
    wire_rows_path = wire_path.with_name("frames.jsonl")
    wire_rows = [json.loads(line) for line in wire_rows_path.read_text(encoding="utf-8").splitlines()]
    packets = {(r["cohort"], r["fid"], r["policy"]): r for r in wire_rows}
    require(len(packets) == len(wire_rows), "duplicate V88 native wire identity")
    for row in rows:
        native = packets.get((row["cohort"], row["fid"], row["policy"]))
        require(native is not None, f"missing V88 native packet: {row['cohort']}/{row['fid']}/{row['policy']}")
        require(row["packet_sha256"] == native["packet_sha256"], "native packet SHA mismatch")
        require(row["wire_bytes"] == native["wire_bytes"], "native packet byte count mismatch")

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["policy"], row["cost"], row["alias"])].append(row)
    require(len(grouped) == 16 and all(len(group) == 4 for group in grouped.values()),
            "incomplete summary groups")
    summary_map = {(s["policy"], s["cost"], s["alias"]): s for s in report["summaries"]}
    require(set(summary_map) == set(grouped), "summary group identities mismatch")
    for key, group in grouped.items():
        summary = summary_map[key]
        ms = [r["conditional_decode_ms"] for r in group]
        require(summary["sources"] == 4, f"{key}: summary source count mismatch")
        require(summary["conditional_decode_ms"] == stats(ms),
                f"{key}: conditional decode summary mismatch")
        require(summary["conditional_under10ms"] == sum(r["decode_cycles"] < 1_000_000 for r in group),
                f"{key}: under-10ms count mismatch")

    lookup = {(r["cohort"], r["fid"], r["cost"], r["alias"], r["policy"]): r
              for r in rows}
    paired = {}
    for policy in sorted(POLICIES - {"AB38_control"}):
        outcomes = {"regressed": 0, "improved": 0, "equal": 0}
        deltas = []
        for cohort, fid in SOURCES:
            for cost in COSTS:
                for alias in (False, True):
                    control = lookup[cohort, fid, cost, alias, "AB38_control"]["decode_cycles"]
                    candidate = lookup[cohort, fid, cost, alias, policy]["decode_cycles"]
                    delta = candidate - control
                    deltas.append(delta)
                    outcomes["regressed" if delta > 0 else "improved" if delta < 0 else "equal"] += 1
        paired[policy] = {**outcomes, "median_delta_cycles": statistics.median(deltas),
                          "total_delta_cycles": sum(deltas),
                          "max_regression_cycles": max(deltas)}

    result = {
        "schema": "cu66-v89-joint-accounting-audit-v1",
        "status": "PASS",
        "selected_report": str(selected_path.relative_to(ROOT)),
        "rows": len(rows), "sources": len(ids), "source_pins_checked": len(report["source_sha256"]),
        "native_packets_checked": len(rows), "summary_groups_recomputed": len(grouped),
        "group_sizes": {"sources_per_policy_cost_alias": 4},
        "paired_vs_AB38": paired,
        "scope": "Row identity, native packet match, and arithmetic consistency only; timing values remain modeled schedules, not hardware qualification.",
    }
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"V89_JOINT_ACCOUNTING_AUDIT_PASS rows={len(rows)} native_packets={len(rows)} summary_groups={len(grouped)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"V89_JOINT_ACCOUNTING_AUDIT_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
