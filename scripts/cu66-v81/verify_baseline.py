#!/usr/bin/env python3
"""Verify V80 ancestry and rerun the frozen V80 integrity checks for V81."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V80_COMMIT = "e3516437ca063b015275ff27260a754ddba79662"


def run(script):
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                            text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"{script} failed: {(result.stdout + result.stderr).strip()}")
    return (result.stdout + result.stderr).strip()


def main():
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", V80_COMMIT, "HEAD"],
                              cwd=ROOT, check=False)
    if ancestor.returncode:
        raise ValueError(f"V80 parent {V80_COMMIT} is not an ancestor of HEAD")
    run("scripts/cu66-v80/verify_baseline.py")
    run("scripts/cu66-v80/bundle_manifest.py")
    run("scripts/cu66-v80/verify_evidence.py")
    print(f"V81_BASELINE_INTEGRITY_PASS parent_v80={V80_COMMIT}; "
          "frozen V80 baseline, bundle, and evidence passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V81_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
