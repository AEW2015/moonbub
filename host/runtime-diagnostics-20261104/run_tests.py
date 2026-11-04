"""Verify exact source bindings and run the SDK-free diagnostic formatting tests."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def verify(root):
    snapshot = json.loads((root / "source-snapshot.json").read_text(encoding="utf-8"))
    for entry in snapshot["files"]:
        path = root / entry["path"]
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise RuntimeError(f"Source binding mismatch: {entry['path']}")
    return len(snapshot["files"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rustc", default=shutil.which("rustc"), help="rustup rustc proxy")
    args = parser.parse_args()
    if not args.rustc:
        parser.error("Rust stable is required; pass the rustup rustc proxy using --rustc")
    root = Path(__file__).resolve().parent
    count = verify(root)
    with tempfile.TemporaryDirectory(prefix="moonbub-diagnostic-tests-") as directory:
        executable = Path(directory) / "diagnostic-tests.exe"
        subprocess.run([
            args.rustc, "+stable", "--edition=2021", "--test",
            str(root / "tests/runtime_diagnostics.rs"), "-o", str(executable),
        ], check=True)
        subprocess.run([str(executable), "--nocapture", "--test-threads=1"], check=True)
    verify(root)
    print(f"PASS: {count} exact source bindings; temporary compiler output removed")


if __name__ == "__main__":
    main()
