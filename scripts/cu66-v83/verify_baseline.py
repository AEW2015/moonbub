#!/usr/bin/env python3
"""Verify the frozen V82 baseline and retained bundle integrity for V83."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V82_COMMIT = "d65ea56b44db9edfb48a664e57f18fab1122d92d"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V82_COMMIT, "--")
    allowed = ("docs/cu66-v83/", "scripts/cu66-v83/",
               "experiments/python-gamebub-v83/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V82 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V82_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V82 baseline {V82_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v82/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V82 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V83_BASELINE_INTEGRITY_PASS parent_v82={V82_COMMIT}; "
          "V82 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V83_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
