#!/usr/bin/env python3
"""Create/check a V87-only retained artifact integrity manifest."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/cu66-v87/bundle-manifest.json"
DIRS = ("docs/cu66-v87", "scripts/cu66-v87", "experiments/python-gamebub-v87")
V86_COMMIT = "e8c8e45604a96cfab149cd670d0a43faac60ba81"


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
            "schema": "cu66-v87-bundle-v1",
            "scope": "V87 Python artifact file integrity only; functional and performance verdicts remain separate",
            "baseline_v86": V86_COMMIT,
            "files_sha256": current,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE_V87_BUNDLE files={len(current)}")
        return
    if not DEST.is_file():
        raise SystemExit("V87_BUNDLE_FAIL manifest missing; run with --write after artifacts are final")
    manifest = json.loads(DEST.read_text(encoding="utf-8"))
    previous = manifest.get("files_sha256", {})
    missing = sorted(previous.keys() - current.keys())
    extra = sorted(current.keys() - previous.keys())
    changed = sorted(key for key in previous.keys() & current.keys()
                     if previous[key] != current[key])
    if (manifest.get("schema") != "cu66-v87-bundle-v1"
            or manifest.get("baseline_v86") != V86_COMMIT
            or missing or extra or changed):
        raise SystemExit(json.dumps({"status": "FAIL", "missing": missing,
                                     "extra": extra, "changed": changed}, indent=2))
    print(f"V87_BUNDLE_FILE_INTEGRITY_PASS files={len(current)}")


if __name__ == "__main__":
    main()
