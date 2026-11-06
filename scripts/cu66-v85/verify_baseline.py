#!/usr/bin/env python3
"""Verify frozen V84 bytes and retained bundle integrity for V85."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V84_COMMIT = "abc19dc8f24fd64875ce181aa9af7382e6e2af27"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V84_COMMIT, "--")
    allowed = ("docs/cu66-v85/", "scripts/cu66-v85/",
               "experiments/python-gamebub-v85/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V84 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V84_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V84 baseline {V84_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v84/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V84 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V85_BASELINE_INTEGRITY_PASS parent_v84={V84_COMMIT}; "
          "V84 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V85_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
