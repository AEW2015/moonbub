#!/usr/bin/env python3
"""Strict capture-window verdict for qspi-cadence-phase analysis JSON."""
import argparse
import json
from pathlib import Path


def verdict(data):
    """Return a strict modeled-window result; deadline equality is on time."""
    reasons = []
    required = ("input_frames", "distinct_input_hashes", "admitted", "busy_drops",
                "presented", "window_end_cycle", "per_frame")
    missing = [key for key in required if key not in data]
    if missing:
        return {"status": "FAIL", "reasons": ["missing fields: " + ", ".join(missing)],
                "scope": "modeled capture-window gate only; not physical proof"}

    n = data["input_frames"]
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        reasons.append("input_frames must be a positive integer")
        n = 0
    for key in ("distinct_input_hashes", "admitted", "presented"):
        if data[key] != n:
            reasons.append(f"{key}={data[key]!r}, expected {n}")
    if data["busy_drops"] != 0:
        reasons.append(f"busy_drops={data['busy_drops']!r}, expected 0")

    rows = data["per_frame"]
    deadline = data["window_end_cycle"]
    if not isinstance(rows, list) or len(rows) != n:
        reasons.append(f"per_frame count is not {n}")
        rows = []
    if not isinstance(deadline, int) or isinstance(deadline, bool):
        reasons.append("window_end_cycle must be an integer")
        deadline = None
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or sorted(ids) != list(range(n)):
        reasons.append("per_frame IDs must contain each requested ID exactly once")
    late = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("present"), int):
            reasons.append("each per_frame row must have integer present cycle")
            continue
        if deadline is not None and row["present"] > deadline:
            late.append(row.get("id"))
    if late:
        reasons.append(f"frames presented after deadline: {late[:8]}" +
                       (" ..." if len(late) > 8 else ""))
    if "presented_within_capture_window" in data:
        within = sum(isinstance(r, dict) and isinstance(r.get("present"), int)
                     and isinstance(deadline, int) and r["present"] <= deadline
                     for r in rows)
        if data["presented_within_capture_window"] != within:
            reasons.append("presented_within_capture_window disagrees with per_frame")
    return {"status": "PASS" if not reasons else "FAIL", "reasons": reasons,
            "requested_frames": n, "busy_drops": data["busy_drops"],
            "deadline_cycle_inclusive": deadline,
            "scope": "modeled capture-window gate only; not physical proof"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--output", type=Path, help="write verdict JSON separately")
    args = parser.parse_args()
    result = verdict(json.loads(args.analysis.read_text()))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
