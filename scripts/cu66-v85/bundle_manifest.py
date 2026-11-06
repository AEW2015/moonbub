#!/usr/bin/env python3
"""Create/check a V85-only retained artifact integrity manifest."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/cu66-v85/bundle-manifest.json"
DIRS = ("docs/cu66-v85", "scripts/cu66-v85", "experiments/python-gamebub-v85")
V84_COMMIT = "abc19dc8f24fd64875ce181aa9af7382e6e2af27"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect():
    files = []
    for name in DIRS:
        base = ROOT / name
        if base.exists():
            files.extend(path for path in base.rglob("*") if path.is_file()
                         and path != DEST and "__pycache__" not in path.parts
                         and path.suffix != ".pyc")
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(files)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = collect()
    if args.write:
        DEST.parent.mkdir(parents=True, exist_ok=True)
        DEST.write_text(json.dumps({
            "schema": "cu66-v85-bundle-v1",
            "scope": "V85 Python artifact file integrity only; functional and performance verdicts remain separate",
            "baseline_v84": V84_COMMIT,
            "files_sha256": current,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE_V85_BUNDLE files={len(current)}")
        return
    if not DEST.is_file():
        raise SystemExit("V85_BUNDLE_FAIL manifest missing; run with --write after artifacts are final")
    manifest = json.loads(DEST.read_text(encoding="utf-8"))
    previous = manifest.get("files_sha256", {})
    missing = sorted(previous.keys() - current.keys())
    extra = sorted(current.keys() - previous.keys())
    changed = sorted(key for key in previous.keys() & current.keys()
                     if previous[key] != current[key])
    if (manifest.get("schema") != "cu66-v85-bundle-v1"
            or manifest.get("baseline_v84") != V84_COMMIT
            or missing or extra or changed):
        raise SystemExit(json.dumps({"status": "FAIL", "missing": missing,
                                     "extra": extra, "changed": changed}, indent=2))
    print(f"V85_BUNDLE_FILE_INTEGRITY_PASS files={len(current)}")


if __name__ == "__main__":
    main()
