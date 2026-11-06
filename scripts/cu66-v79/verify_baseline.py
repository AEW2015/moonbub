#!/usr/bin/env python3
"""Verify the frozen V78 parent, bundle, evidence, RTL, and benchmark inputs."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v79/baseline-sources.json"
PINNED_COMMIT = "3d0e937afcfd3e1141ffda3d65f94cb5be53deac"


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
    if pins.get("schema") != "cu66-v79-frozen-baseline-v1":
        raise ValueError("unexpected V79 baseline pin schema")
    if pins.get("baseline_commit") != PINNED_COMMIT:
        raise ValueError("unexpected V78 parent commit pin")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", PINNED_COMMIT, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"V78 parent {PINNED_COMMIT} is not an ancestor of HEAD")
    source_pins = pins.get("source_sha256")
    if not isinstance(source_pins, dict) or not source_pins:
        raise ValueError("V78 RTL/benchmark source pins are missing")
    for relpath, expected in source_pins.items():
        target = (ROOT / relpath).resolve()
        if not target.is_relative_to(ROOT.resolve()) or not target.is_file():
            raise ValueError(f"pinned V78 source is missing or outside repository: {relpath}")
        if sha256(target) != expected:
            raise ValueError(f"pinned V78 source mismatch: {relpath}")
    run("scripts/cu66-v78/verify_baseline.py")
    run("scripts/cu66-v78/bundle_manifest.py")
    run("scripts/cu66-v78/verify_evidence.py")
    print(f"V79_BASELINE_INTEGRITY_PASS parent={PINNED_COMMIT}; "
          f"v78_rtl_benchmark_pins={len(source_pins)}; V78 baseline, bundle, and evidence passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V79_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
