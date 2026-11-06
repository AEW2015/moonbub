#!/usr/bin/env python3
"""Create/check the V78 artifact bundle integrity manifest."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/cu66-v78/bundle-manifest.json"
DIRS = ("docs/cu66-v78", "scripts/cu66-v78", "fpga/experiments/cu66-v78")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect():
    files = []
    for name in DIRS:
        files.extend(path for path in (ROOT / name).rglob("*") if path.is_file()
                     and path != DEST and "__pycache__" not in path.parts
                     and path.suffix != ".pyc")
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(files)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    current = collect()
    if args.write:
        DEST.write_text(json.dumps({
            "schema": "cu66-v78-bundle-v1",
            "scope": "V78 artifact file integrity only; functional and performance verdicts remain separate",
            "baseline_v77": "f6c2b50112fc3bb1db99b86aac0aec4d03483355",
            "files_sha256": current,
        }, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE_V78_BUNDLE files={len(current)}")
        return
    if not DEST.is_file():
        raise SystemExit("V78_BUNDLE_FAIL manifest missing; run with --write after artifacts are final")
    previous = json.loads(DEST.read_text(encoding="utf-8")).get("files_sha256", {})
    missing = sorted(previous.keys() - current.keys())
    extra = sorted(current.keys() - previous.keys())
    changed = sorted(key for key in previous.keys() & current.keys()
                     if previous[key] != current[key])
    if missing or extra or changed:
        raise SystemExit(json.dumps({"status": "FAIL", "missing": missing,
                                     "extra": extra, "changed": changed}, indent=2))
    print(f"V78_BUNDLE_FILE_INTEGRITY_PASS files={len(current)}")


if __name__ == "__main__":
    main()
