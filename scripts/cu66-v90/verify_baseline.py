#!/usr/bin/env python3
"""Verify the frozen V89 parent, tracked-byte boundary, and retained bundle."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V89_COMMIT = "d45c2bf30f43619101045a23fe3df6cad388a617"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_tracked_paths():
    diff = git("diff", "--name-only", V89_COMMIT, "--")
    allowed = ("docs/cu66-v90/", "scripts/cu66-v90/",
               "experiments/python-gamebub-v90/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        raise ValueError("V89 tracked paths differ from frozen bytes "
                         f"({len(changed)}): {', '.join(changed[:12])}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V89_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V89 baseline {V89_COMMIT} is not an ancestor of HEAD")
    verify_tracked_paths()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/cu66-v89/bundle_manifest.py")],
        cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V89 bundle check failed: "
                         f"{(result.stdout + result.stderr).strip()}")
    print(f"V90_BASELINE_INTEGRITY_PASS parent_v89={V89_COMMIT}; "
          "V89 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V90_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
