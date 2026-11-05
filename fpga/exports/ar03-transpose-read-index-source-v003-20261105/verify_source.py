"""Verify every file in this portable source export against manifest.json."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside_root(path):
    try:
        path.relative_to(ROOT)
        return True
    except ValueError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    manifest_path = ROOT / "manifest.json"
    if args.manifest_sha256 and sha256(manifest_path) != args.manifest_sha256.lower():
        raise SystemExit("manifest SHA-256 mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest["artifacts"]
    expected = {row["path"] for row in rows}
    if len(expected) != len(rows):
        raise SystemExit("duplicate artifact path in manifest")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual != expected:
        missing = sorted(expected - actual)
        unbound = sorted(actual - expected)
        raise SystemExit(f"file set mismatch: missing={missing}; unbound={unbound}")
    for row in rows:
        path = ROOT / row["path"]
        if not inside_root(path.resolve()):
            raise SystemExit(f"artifact escapes export: {row['path']}")
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise SystemExit(f"size/hash mismatch: {row['path']}")
    print(f"SOURCE_EXPORT_INTEGRITY_PASS files={len(rows)} bytes={sum(x['bytes'] for x in rows)}")


if __name__ == "__main__":
    main()
