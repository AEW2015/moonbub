#!/usr/bin/env python3
"""Verify frozen V85 bytes and retained bundle integrity for V86."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V85_COMMIT = "4851b1efbd92b1f78ea98cd5db7f9b5e7d3ad0b0"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V85_COMMIT, "--")
    allowed = ("docs/cu66-v86/", "scripts/cu66-v86/",
               "experiments/python-gamebub-v86/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V85 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V85_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V85 baseline {V85_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v85/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V85 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V86_BASELINE_INTEGRITY_PASS parent_v85={V85_COMMIT}; "
          "V85 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V86_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
