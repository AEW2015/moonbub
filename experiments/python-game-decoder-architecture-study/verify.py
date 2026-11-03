"""Verify retained arithmetic and provenance; no online access by default."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from model import study

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--online", action="store_true", help="also refetch pinned openav1 README bytes; execute nothing")
    args = parser.parse_args()
    actual = json.loads((HERE / "results.json").read_text())
    assert actual == study(), "retained results differ from regenerated model"
    manifest = json.loads((HERE / "sources.json").read_text())
    for entry in manifest["local_inputs"]:
        assert digest((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
    entry = manifest["openav1_pinned_readme"]
    assert entry["commit"] in entry["url"] and len(entry["commit"]) == 40
    assert len(entry["sha256"]) == 64
    if args.online:
        with urllib.request.urlopen(entry["url"], timeout=30) as response:
            data = response.read(1024 * 1024)
        assert digest(data) == entry["sha256"], "pinned README hash differs"
    print("PASS: retained scenario results, local input hashes, pinned source metadata" +
          (", pinned remote README hash" if args.online else " (offline; remote contents not rechecked)"))


if __name__ == "__main__":
    main()
