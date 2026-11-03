"""Record source identity without changing the existing GameBub workspace."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def inventory(source):
    repos = {}
    for name, path in [("workspace", source), ("gamebub-source", source / "gamebub-source")]:
        dirty = git(path, "status", "--porcelain=v1", "-uno")
        # Tracked-file content binds the local modifications as well as HEAD.
        paths = git(path, "ls-files", "-z").split("\0")
        hashes = {}
        for rel in paths:
            item = path / rel
            if item.is_file():
                hashes[rel] = hashlib.sha256(item.read_bytes()).hexdigest()
        repos[name] = {"path": str(path), "head": git(path, "rev-parse", "HEAD"),
                       "tracked_status": dirty, "tracked_sha256": hashes}
    return repos


def public_firmware_view(data):
    source = data["gamebub-source"]
    prefix = "firmware/handheld/"
    return {"publication_scope": "Game Bub firmware tracked sources",
            "gamebub-source": {"head": source["head"],
                "tracked_status": "\n".join(line for line in source["tracked_status"].splitlines() if prefix in line),
                "tracked_sha256": {k: v for k, v in source["tracked_sha256"].items() if k.startswith(prefix)}}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(r"C:\Users\lavat\codex\gamebub"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    data = inventory(args.source)
    previous = json.loads(args.compare.read_text()) if args.compare else None
    if previous is not None and previous.get("publication_scope") == "Game Bub firmware tracked sources":
        data = public_firmware_view(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    if args.compare:
        if previous != data:
            raise SystemExit("Source inventory differs; inspect changes before attributing ownership")
        print("SOURCE_PRESERVATION_PASS published inventory scope unchanged")
        snapshot_path = Path(__file__).resolve().parents[1] / "firmware/source-snapshot.json"
        if snapshot_path.is_file():
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
            copied_source = args.source / "gamebub-source" / "firmware" / "handheld"
            changed = []
            for rel, expected in snapshot["files"].items():
                file = copied_source / rel
                if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
                    changed.append(rel)
            report = {"status": "fail" if changed else "pass", "files": len(snapshot["files"]),
                      "scope": "Original copied firmware source, including untracked files", "changed": changed}
            (args.output.parent / "source-snapshot-preservation.json").write_text(json.dumps(report, indent=2) + "\n")
            if changed:
                raise SystemExit("Original copied source changed: " + ", ".join(changed))
            print("SOURCE_SNAPSHOT_PRESERVATION_PASS", report["files"], "original files")
    else:
        print("SOURCE_INVENTORY_RECORDED", args.output)


if __name__ == "__main__":
    main()
