#!/usr/bin/env python3
"""Verify frozen V86 bytes and retained bundle integrity for V87."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V86_COMMIT = "e8c8e45604a96cfab149cd670d0a43faac60ba81"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V86_COMMIT, "--")
    allowed = ("docs/cu66-v87/", "scripts/cu66-v87/",
               "experiments/python-gamebub-v87/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V86 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V86_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V86 baseline {V86_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v86/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V86 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V87_BASELINE_INTEGRITY_PASS parent_v86={V86_COMMIT}; "
          "V86 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V87_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
