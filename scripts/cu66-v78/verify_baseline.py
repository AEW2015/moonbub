#!/usr/bin/env python3
"""Verify the frozen V69-V77 CU66 baseline and V78 parent ancestry."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v78/baseline-sources.json"
PINNED_COMMIT = "f6c2b50112fc3bb1db99b86aac0aec4d03483355"
V77_FILES = 122


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = json.loads(PIN.read_text(encoding="utf-8"))
    if pins.get("baseline_commit") != PINNED_COMMIT:
        raise ValueError("unexpected V77 baseline commit pin")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PINNED_COMMIT, "HEAD"],
        cwd=ROOT, check=False,
    )
    if ancestor.returncode:
        raise ValueError(f"V77 baseline {PINNED_COMMIT} is not an ancestor of HEAD")
    if pins.get("bundle_file_counts", {}).get("v77") != V77_FILES:
        raise ValueError("baseline source pin has wrong V77 manifest count")
    for relpath, expected_hash in pins.get("source_sha256", {}).items():
        target = ROOT / relpath
        if not target.is_file() or sha256(target) != expected_hash:
            raise ValueError(f"pinned baseline source mismatch: {relpath}")
    manifest = ROOT / "docs/cu66-v77/bundle-manifest.json"
    entries = json.loads(manifest.read_text(encoding="utf-8"))["files_sha256"]
    if len(entries) != V77_FILES:
        raise ValueError(f"V77 manifest count {len(entries)} != {V77_FILES}")
    for relpath, expected_hash in entries.items():
        target = ROOT / relpath
        if not target.is_file() or sha256(target) != expected_hash:
            raise ValueError(f"V77 frozen bundle mismatch: {relpath}")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/cu66-v77/verify_baseline.py")],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("V77 and prior baseline verifiers failed: " +
                         (result.stdout + result.stderr).strip())
    print(f"V78_BASELINE_INTEGRITY_PASS v77={V77_FILES}; {PINNED_COMMIT} is ancestor of HEAD; "
          "V77 bundle and V69-V76 baseline verifiers passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V78_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
