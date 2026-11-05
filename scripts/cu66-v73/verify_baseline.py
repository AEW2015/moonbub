#!/usr/bin/env python3
"""Read-only v73 ancestor and frozen CU66 bundle integrity audit."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "fpga/experiments/cu66-v73/baseline-sources.json"
EXPECTED_COUNTS = {"v69": 4879, "v70": 460, "v71": 122, "v72": 131}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = json.loads(PIN.read_text(encoding="utf-8"))
    commit = pins["baseline_commit"]
    if commit != "41d070476c074e8caa1ccabe7ae745ba61707717":
        raise ValueError("unexpected v72 baseline commit pin")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"v72 baseline {commit} is not an ancestor of HEAD")
    for relpath, expected_hash in pins["source_sha256"].items():
        target = ROOT / relpath
        if not target.is_file() or sha256(target) != expected_hash:
            raise ValueError(f"pinned baseline source mismatch: {relpath}")
    counts = {}
    for version, expected_count in EXPECTED_COUNTS.items():
        path = ROOT / f"docs/cu66-{version}/bundle-manifest.json"
        entries = json.loads(path.read_text(encoding="utf-8"))["files_sha256"]
        counts[version] = len(entries)
        if len(entries) != expected_count:
            raise ValueError(f"{version} manifest count {len(entries)} != {expected_count}")
        if pins["bundle_file_counts"].get(version) != expected_count:
            raise ValueError(f"baseline source pin has wrong {version} manifest count")
        for relpath, expected_hash in entries.items():
            target = ROOT / relpath
            if not target.is_file() or sha256(target) != expected_hash:
                raise ValueError(f"{version} frozen bundle mismatch: {relpath}")
    # V72 verifier recursively includes the earlier baseline authorities.
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v72/verify_baseline.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError("v72 baseline verifier failed: " + (result.stdout + result.stderr).strip())
    print("V73_BASELINE_INTEGRITY_PASS " + " ".join(f"{v}={n}" for v, n in counts.items()) +
          f"; {commit} is ancestor of HEAD; prior baseline verifiers passed; integrity only")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V73_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
