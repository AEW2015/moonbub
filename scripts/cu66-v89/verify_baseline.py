#!/usr/bin/env python3
"""Verify the frozen V88 parent, tracked-byte boundary, and retained bundle."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V88_COMMIT = "f2292efee4b46035318e554cf981f2a957498ce6"


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, text=True,
                          capture_output=True, check=check)


def verify_tracked_paths():
    diff = git("diff", "--name-only", V88_COMMIT, "--")
    allowed = ("docs/cu66-v89/", "scripts/cu66-v89/",
               "experiments/python-gamebub-v89/")
    changed = [name for name in diff.stdout.splitlines()
               if not name.startswith(allowed)]
    if changed:
        raise ValueError("V88 tracked paths differ from frozen bytes "
                         f"({len(changed)}): {', '.join(changed[:12])}")


def main():
    ancestor = git("merge-base", "--is-ancestor", V88_COMMIT, "HEAD", check=False)
    if ancestor.returncode:
        raise ValueError(f"V88 baseline {V88_COMMIT} is not an ancestor of HEAD")
    verify_tracked_paths()
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/cu66-v88/bundle_manifest.py")],
        cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValueError(f"V88 bundle check failed: "
                         f"{(result.stdout + result.stderr).strip()}")
    print(f"V89_BASELINE_INTEGRITY_PASS parent_v88={V88_COMMIT}; "
          "V88 tracked bytes and bundle integrity passed; integrity only")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"V89_BASELINE_INTEGRITY_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
