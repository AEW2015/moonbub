#!/usr/bin/env python3
"""Independently check V89 constant sentinel report pins and row accounting."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v89/constants"
DEST = AREA / "constants-audit.json"
EXPECTED_ROWS = 457
EXPECTED_SOURCES = 457
EXPECTED_PER_FRAME = {
    "canonical_write_BL8": 1176,
    "scanout_read_BL8": 1176,
    "constant_candidate_bytes": 294 * 64,
    "constant_scanout_bytes": 294 * 64,
    "memory_busy_cycles": 39984,
    "decoder_memory_busy_cycles": 18816,
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    report_path = AREA / "results.json"
    require(report_path.is_file(), "constants/results.json is missing")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    selected_path = ROOT / report["selected_report"]
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    require(report["schema"] == selected["schema"] ==
            "cu66-v89-constant-sentinel-trace-v1", "unexpected report schema")
    require(report["status"] == selected["status"] ==
            "PASS_FIXED_PROFILE_CONSTANT_AND_NATIVE_CONTENT", "unexpected report status")
    require(report["source_sha256"] == selected["source_sha256"], "source pins differ")
    pins = report["source_sha256"]
    for name, digest in pins.items():
        path = ROOT / name
        require(path.is_file() and sha(path) == digest, f"source pin mismatch: {name}")
    require(selected["native_sources"] == EXPECTED_SOURCES, "native source count mismatch")
    frames = selected_path.with_name("frames.jsonl")
    require(frames.is_file() and sha(frames) == selected["frames_sha256"],
            "selected frames hash mismatch")
    rows = [json.loads(line) for line in frames.read_text(encoding="utf-8").splitlines()]
    require(len(rows) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS} rows, got {len(rows)}")

    row_sums = {name: 0 for name in EXPECTED_PER_FRAME}
    for index, row in enumerate(rows):
        require(row["hidden_tiles"] == 294, f"row {index}: hidden tile count mismatch")
        for policy in ("onchip", "cached", "uncached"):
            current, control = row["profiles"][policy], row["control_profiles"][policy]
            for key, delta in EXPECTED_PER_FRAME.items():
                if key.endswith("_bytes"):
                    observed = current[key]
                    require(observed == delta, f"row {index}/{policy}: {key} mismatch")
                else:
                    observed = control[key] - current[key]
                    require(observed == delta,
                            f"row {index}/{policy}: {key} delta {observed}, expected {delta}")
                if policy == "onchip":
                    row_sums[key] += delta if key.endswith("_bytes") else observed

    expected_sums = {key: delta * EXPECTED_ROWS
                     for key, delta in EXPECTED_PER_FRAME.items()}
    require(row_sums == expected_sums, "aggregate row sums mismatch")
    summaries = {item["policy"]: item for item in selected["summaries"]}
    require(set(summaries) == {"onchip", "cached", "uncached"}, "policy summary set mismatch")
    for policy, summary in summaries.items():
        require(summary["sources"] == EXPECTED_SOURCES, f"{policy}: source count mismatch")
        require(summary["avoided_data_write_BL8"] == 537432,
                f"{policy}: avoided write total mismatch")
        require(summary["avoided_scanout_read_BL8"] == 537432,
                f"{policy}: avoided scanout total mismatch")
        require(summary["generated_candidate_bytes"] == 8598912,
                f"{policy}: candidate generation total mismatch")
        require(summary["generated_scanout_bytes"] == 8598912,
                f"{policy}: scanout generation total mismatch")

    result = {
        "schema": "cu66-v89-constant-accounting-audit-v1",
        "status": "PASS",
        "selected_report": str(selected_path.relative_to(ROOT)),
        "rows": len(rows),
        "policies": sorted(summaries),
        "source_pins_checked": len(pins),
        "selected_frames_sha256": sha(frames),
        "aggregate_deltas": expected_sums,
        "per_policy_totals": {
            policy: {key: summary[key] for key in (
                "avoided_data_write_BL8", "avoided_scanout_read_BL8",
                "generated_candidate_bytes", "generated_scanout_bytes")}
            for policy, summary in summaries.items()
        },
        "scope": "Source pin and arithmetic consistency audit; it does not qualify timing or physical 30 fps.",
    }
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"V89_CONSTANT_ACCOUNTING_AUDIT_PASS rows={len(rows)} source_pins={len(pins)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"V89_CONSTANT_ACCOUNTING_AUDIT_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
