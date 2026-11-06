#!/usr/bin/env python3
"""Verify frozen V79 ancestry, selected source inputs, and retained evidence integrity."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v80/baseline-sources.json"
PINNED_COMMIT = "0f07d147934ff6cd1da1e9cfc60eea8547556ff4"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(script):
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                            text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"{script} failed: {(result.stdout + result.stderr).strip()}")
    return (result.stdout + result.stderr).strip()


def main():
    pins = json.loads(PIN.read_text(encoding="utf-8"))
    if pins.get("schema") != "cu66-v80-frozen-baseline-v1":
        raise ValueError("unexpected V80 baseline pin schema")
    if pins.get("baseline_commit") != PINNED_COMMIT:
        raise ValueError("unexpected V79 parent commit pin")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", PINNED_COMMIT, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"V79 parent {PINNED_COMMIT} is not an ancestor of HEAD")
    source_pins = pins.get("source_sha256")
    if not isinstance(source_pins, dict) or not source_pins:
        raise ValueError("selected frozen source pins are missing")
    for relpath, expected in source_pins.items():
        target = (ROOT / relpath).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            raise ValueError(f"pinned source is missing or outside repository: {relpath}")
        if sha256(target) != expected:
            raise ValueError(f"pinned source mismatch: {relpath}")
    run("scripts/cu66-v79/verify_baseline.py")
    run("scripts/cu66-v79/bundle_manifest.py")
    run("scripts/cu66-v79/verify_evidence.py")
    print(f"V80_BASELINE_INTEGRITY_PASS parent={PINNED_COMMIT}; "
          f"selected_source_pins={len(source_pins)}; V79 baseline, bundle, and evidence passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V80_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
