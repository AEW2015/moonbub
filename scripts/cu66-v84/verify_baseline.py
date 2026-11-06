#!/usr/bin/env python3
"""Verify frozen V83 bytes and retained bundle integrity for V84."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V83_COMMIT = "ebbc104d2be8bfe1b2a5b0ee1b10e0d524a166b6"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V83_COMMIT, "--")
    allowed = ("docs/cu66-v84/", "scripts/cu66-v84/",
               "experiments/python-gamebub-v84/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V83 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V83_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V83 baseline {V83_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v83/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V83 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V84_BASELINE_INTEGRITY_PASS parent_v83={V83_COMMIT}; "
          "V83 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V84_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
