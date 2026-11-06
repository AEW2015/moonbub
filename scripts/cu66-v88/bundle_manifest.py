#!/usr/bin/env python3
"""Create/check a V88-only retained artifact integrity manifest."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/cu66-v88/bundle-manifest.json"
DIRS = ("docs/cu66-v88", "scripts/cu66-v88", "experiments/python-gamebub-v88")
V87_COMMIT = "beb84ef6aeacaf506450bc1669ce7d5fde445f93"


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
            "schema": "cu66-v88-bundle-v1",
            "scope": "V88 Python artifact file integrity only; functional and performance verdicts remain separate",
            "baseline_v87": V87_COMMIT,
            "files_sha256": current,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE_V88_BUNDLE files={len(current)}")
        return
    if not DEST.is_file():
        raise SystemExit("V88_BUNDLE_FAIL manifest missing; run with --write after artifacts are final")
    manifest = json.loads(DEST.read_text(encoding="utf-8"))
    previous = manifest.get("files_sha256", {})
    missing = sorted(previous.keys() - current.keys())
    extra = sorted(current.keys() - previous.keys())
    changed = sorted(key for key in previous.keys() & current.keys()
                     if previous[key] != current[key])
    if (manifest.get("schema") != "cu66-v88-bundle-v1"
            or manifest.get("baseline_v87") != V87_COMMIT
            or missing or extra or changed):
        raise SystemExit(json.dumps({"status": "FAIL", "missing": missing,
                                     "extra": extra, "changed": changed}, indent=2))
    print(f"V88_BUNDLE_FILE_INTEGRITY_PASS files={len(current)}")


if __name__ == "__main__":
    main()
