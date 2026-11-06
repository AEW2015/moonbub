#!/usr/bin/env python3
"""Verify the frozen V81 baseline and its retained integrity checks for V82."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V81_COMMIT = "83efb7ae627757aefdfd22e2a355720ff01bfb72"


def run(script):
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                            text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"{script} failed: {(result.stdout + result.stderr).strip()}")
    return (result.stdout + result.stderr).strip()


def main():
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", V81_COMMIT, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"V81 parent {V81_COMMIT} is not an ancestor of HEAD")
    run("scripts/cu66-v81/verify_baseline.py")
    run("scripts/cu66-v81/bundle_manifest.py")
    run("scripts/cu66-v81/verify_evidence.py")
    print(f"V82_BASELINE_INTEGRITY_PASS parent_v81={V81_COMMIT}; "
          "frozen V81 baseline, bundle, and evidence passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V82_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
