#!/usr/bin/env python3
"""Verify frozen V87 bytes and retained bundle integrity for V88."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V87_COMMIT = "beb84ef6aeacaf506450bc1669ce7d5fde445f93"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_frozen_paths():
    diff = git("diff", "--name-only", V87_COMMIT, "--")
    allowed = ("docs/cu66-v88/", "scripts/cu66-v88/",
               "experiments/python-gamebub-v88/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        sample = ", ".join(changed[:12])
        raise ValueError(f"V87 tracked paths differ from frozen bytes ({len(changed)}): {sample}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V87_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V87 baseline {V87_COMMIT} is not an ancestor of HEAD")
    verify_frozen_paths()
    result = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v87/bundle_manifest.py")],
                            cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V87 bundle check failed: {(result.stdout + result.stderr).strip()}")
    print(f"V88_BASELINE_INTEGRITY_PASS parent_v87={V87_COMMIT}; "
          "V87 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V88_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
