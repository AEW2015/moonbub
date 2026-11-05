"""Replay v26 checks in a fresh mutable copy; never modify the sealed export."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXPECTED = "8b40f9a06d5f9634a3686d503455a7cb736c61b2e99951722cd9fdf213beba6b"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def included_path(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Export path escapes root: {name}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--cargo")
    parser.add_argument("--rustc")
    parser.add_argument("--expected-manifest-sha256", default=EXPECTED)
    parser.add_argument("--checks", nargs="+", choices=["paths", "host", "metadata", "full-metadata"],
                        default=["paths", "host", "metadata", "full-metadata"])
    args = parser.parse_args()
    original = args.export.resolve()
    evidence = args.evidence.resolve()
    if evidence.exists():
        raise ValueError("Evidence directory already exists; choose a fresh path")
    if evidence.is_relative_to(original) or original.is_relative_to(evidence):
        raise ValueError("Evidence and sealed export must be separate directory trees")
    manifest_path = original / "manifest.json"
    if sha(manifest_path) != args.expected_manifest_sha256:
        raise ValueError("Unexpected sealed export manifest")
    manifest = json.loads(manifest_path.read_text())
    binding = json.loads((original / "source-bindings.json").read_text())
    expected = {item["path"]: item["sha256"] for item in manifest["artifacts"]}
    for item in binding["source_files"]:
        if item["path"] in expected and expected[item["path"]] != item["sha256"]:
            raise ValueError("Manifest/source binding disagreement")
        expected[item["path"]] = item["sha256"]  # Includes zero-byte selected fixtures.
    expected["manifest.json"] = args.expected_manifest_sha256
    assert len(binding["source_files"]) == 575
    for name, digest in expected.items():
        assert sha(included_path(original, name)) == digest, name

    evidence.mkdir(parents=True)
    replay = evidence / "replay-copy"
    for name in expected:
        target = included_path(replay, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(included_path(original, name), target)
    logs = evidence / "steps"
    logs.mkdir()
    steps = []

    def run(label, command):
        started = time.monotonic()
        with (logs / f"{label}.log").open("wb") as stream:
            process = subprocess.run(command, cwd=replay, stdout=stream, stderr=subprocess.STDOUT)
        steps.append({"step": label, "command": command, "returncode": process.returncode,
                      "wall_seconds": time.monotonic() - started,
                      "log": f"steps/{label}.log", "log_sha256": sha(logs / f"{label}.log")})
        if process.returncode:
            raise RuntimeError(f"Replay step failed: {label} (see {logs / (label + '.log')})")

    before_checks = {x.relative_to(replay).as_posix(): sha(x) for x in (replay / "checks").rglob("*") if x.is_file()}
    failure = None
    try:
        run("00-original-copy-integrity", [sys.executable, str(replay / "verify_source.py")])
        notice = ("MUTABLE VALIDATION COPY — NOT A SEALED BUILD SOURCE\n"
                  "Original integrity was verified before replay. The inherited 656-output\n"
                  "manifest is intentionally no longer applicable after checks overwrite checks/.\n"
                  "Do not build or publish this copy. Build from the unchanged sealed export.\n"
                  "Selected 575 inputs and new replay hashes are checked in replay-result.json.\n")
        (evidence / "REPLAY-COPY-NOT-FOR-BUILD.txt").write_text(notice, encoding="utf-8")
        (replay / "REPLAY-COPY-NOT-FOR-BUILD.txt").write_text(notice, encoding="utf-8")
        cargo = ["--cargo", args.cargo] if args.cargo else []
        rustc = ["--rustc", args.rustc] if args.rustc else []
        commands = {
            "paths": [sys.executable, str(replay / "inspect_sources.py")],
            "host": [sys.executable, str(replay / "host_check.py"), *cargo, *rustc],
            "metadata": [sys.executable, str(replay / "check_metadata.py"), *cargo],
            "full-metadata": [sys.executable, str(replay / "full_metadata.py"), *cargo],
        }
        for number, check in enumerate(dict.fromkeys(args.checks), 1):
            run(f"{number:02d}-{check}", commands[check])
    except Exception as error:
        failure = str(error)
    changed_sources = [item["path"] for item in binding["source_files"]
                       if sha(included_path(replay, item["path"])) != item["sha256"]]
    changed_original = [name for name, digest in expected.items()
                        if sha(included_path(original, name)) != digest]
    outputs = []
    for path in sorted((replay / "checks").rglob("*")):
        if path.is_file():
            name = path.relative_to(replay).as_posix()
            digest = sha(path)
            outputs.append({"path": f"replay-copy/{name}", "sha256": digest, "bytes": path.stat().st_size,
                            "origin": "replay-created-or-changed" if before_checks.get(name) != digest else "inherited-unchanged"})
    passed = not failure and not changed_sources and not changed_original
    result = {"status": "PASS" if passed else "FAIL", "sealed_export": str(original),
              "sealed_manifest_sha256": args.expected_manifest_sha256,
              "original_integrity_verified_before_copy": True, "original_export_unchanged": not changed_original,
              "selected_inputs": 575, "selected_input_changes": changed_sources,
              "original_export_changes": changed_original, "checks_run": args.checks, "steps": steps,
              "new_output_snapshot": outputs, "failure": failure,
              "inherited_656_output_manifest_applicable_to_mutable_copy": False,
              "build_source": "Use unchanged sealed_export, never replay-copy",
              "runner_sha256": sha(Path(__file__).resolve()), "target_build": "NOT_RUN", "hardware": "NONE"}
    (evidence / "replay-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"V26_COPY_REPLAY_{result['status']}: selected575 unchanged={not changed_sources}; sealed export unchanged={not changed_original}; {evidence / 'replay-result.json'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
