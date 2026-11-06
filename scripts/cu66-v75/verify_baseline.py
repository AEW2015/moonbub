#!/usr/bin/env python3
"""Read-only integrity verification for the frozen CU66 v69-v74 baseline."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v75/baseline-sources.json"
COUNTS = {"v69": 4879, "v70": 460, "v71": 122, "v72": 131, "v73": 161, "v74": 149}
PINNED_COMMIT = "f731f12b3e74507762b4984392ea41ff932a6fda"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = json.loads(PIN.read_text(encoding="utf-8"))
    if pins["baseline_commit"] != PINNED_COMMIT:
        raise ValueError("unexpected V74 baseline commit pin")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", PINNED_COMMIT, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"V74 baseline {PINNED_COMMIT} is not an ancestor of HEAD")
    for relpath, expected_hash in pins["source_sha256"].items():
        target = ROOT / relpath
        if not target.is_file() or sha256(target) != expected_hash:
            raise ValueError(f"pinned baseline source mismatch: {relpath}")
    counts = {}
    for version, expected_count in COUNTS.items():
        manifest = ROOT / f"docs/cu66-{version}/bundle-manifest.json"
        entries = json.loads(manifest.read_text(encoding="utf-8"))["files_sha256"]
        counts[version] = len(entries)
        if len(entries) != expected_count:
            raise ValueError(f"{version} manifest count {len(entries)} != {expected_count}")
        if pins["bundle_file_counts"].get(version) != expected_count:
            raise ValueError(f"baseline source pin has wrong {version} manifest count")
        for relpath, expected_hash in entries.items():
            target = ROOT / relpath
            if not target.is_file() or sha256(target) != expected_hash:
                raise ValueError(f"{version} frozen bundle mismatch: {relpath}")
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v74/verify_baseline.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("V74 baseline verifier failed: " + (result.stdout + result.stderr).strip())
    print("V75_BASELINE_INTEGRITY_PASS " + " ".join(f"{v}={n}" for v, n in counts.items()) +
          f"; {PINNED_COMMIT} is ancestor of HEAD; V74 and prior baseline verifiers passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V75_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
