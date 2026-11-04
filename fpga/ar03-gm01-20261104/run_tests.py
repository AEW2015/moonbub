#!/usr/bin/env python3
"""Rebuild the scoped GM01 vector/simulation evidence in temporary storage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
EXPECTED = "GM01_SECTIONS_PASS cases=62 certified=28 rejected=34 block_descriptors=178469 cancel_cases=12"
SOURCE_FILES = ("gm01_sections.sv", "tb_gm01_sections.sv", "prepare_vectors.py", "requirements-oracle.txt")
NATIVE_COMMIT = "c9c0bf4bcbe5c95f38b50bf6e190b84822886d53"
NATIVE_PATH_LINE = b"native_repo=Path('C:/Users/lavat/codex/sunshine-gamebub-dxgi-work')"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.write_text(data, encoding="utf-8", newline="\n")


def find_tool(name, known_bins):
    for candidate in (name, name + ".exe"):
        found = shutil.which(candidate)
        if found:
            return Path(found).resolve()
    for directory in known_bins:
        candidate = directory / (name + ".exe")
        if candidate.is_file():
            return candidate.resolve()
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="the frozen MoonBub AR03 oracle Git checkout at 27a4dde6a7e2ea4fab09d892551ef542f05c8965")
    parser.add_argument("--native-source", type=Path, required=True,
                        help="the native-review Git checkout at c9c0bf4bcbe5c95f38b50bf6e190b84822886d53")
    parser.add_argument("--oracle-python", type=Path,
                        help="Python executable with requirements-oracle.txt installed; defaults to this Python")
    parser.add_argument("--log-dir", type=Path, required=True,
                        help="persistent destination for logs/result only")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    native_source = args.native_source.expanduser().resolve()
    log_dir = args.log_dir.expanduser().resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    snapshot_path = HERE / "source-snapshot.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    if snapshot.get("schema") != "ar03-gm01-source-export-v1":
        raise SystemExit("unsupported source snapshot schema")
    records = {entry["export_path"]: entry for entry in snapshot["files"]}
    if set(records) != set(SOURCE_FILES):
        raise SystemExit("snapshot must bind exactly the four source files")
    for name in SOURCE_FILES:
        data = (HERE / name).read_bytes()
        rec = records[name]
        if len(data) != rec["bytes"] or sha(data) != rec["sha256"]:
            raise SystemExit(f"source snapshot mismatch: {name}")

    oracle_python = args.oracle_python.expanduser().resolve() if args.oracle_python else Path(sys.executable).resolve()
    if not oracle_python.is_file():
        raise SystemExit(f"oracle Python executable not found: {oracle_python}")
    kit_head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                              capture_output=True, text=True)
    if kit_head.returncode or kit_head.stdout.strip() != "27a4dde6a7e2ea4fab09d892551ef542f05c8965":
        save(log_dir / "preflight.log", kit_head.stdout + kit_head.stderr)
        raise SystemExit("source checkout is not the pinned 27a4dde6a7e2ea4fab09d892551ef542f05c8965 commit")
    native_head = subprocess.run(["git", "-C", str(native_source), "rev-parse", "HEAD"],
                                 capture_output=True, text=True)
    native_pin = subprocess.run(["git", "-C", str(native_source), "cat-file", "-e",
                                 f"{NATIVE_COMMIT}^{{commit}}"], capture_output=True, text=True)
    if native_head.returncode or native_pin.returncode:
        save(log_dir / "native-preflight.log", native_head.stdout + native_head.stderr +
             native_pin.stdout + native_pin.stderr)
        raise SystemExit(f"native-source checkout must contain pinned commit {NATIVE_COMMIT}")

    known_bins = []
    for value in (os.environ.get("MSYS2_ROOT"), os.environ.get("MSYSTEM_PREFIX"),
                  "C:/msys64/ucrt64", "C:/msys64/mingw64", "C:/tools/msys64/ucrt64"):
        if value:
            base = Path(value)
            known_bins.extend((base / "bin", base))
    iverilog = find_tool("iverilog", known_bins)
    vvp = find_tool("vvp", known_bins)
    if not iverilog or not vvp:
        raise SystemExit("Icarus Verilog tools not found on PATH or known MSYS2 bin paths")

    result = {
        "status": "FAIL",
        "scope": "host-only GM01 section/map simulation",
        "hardware": "UNEXECUTED",
        "source_commit": kit_head.stdout.strip(),
        "parent_manifest_sha256": snapshot["parent_manifest_sha256"],
        "source_snapshot_sha256": sha(snapshot_path.read_bytes()),
        "native_source": str(native_source),
        "native_source_head": native_head.stdout.strip(),
        "native_source_commit": NATIVE_COMMIT,
        "native_path_override": "native path override only",
        "oracle_python": str(oracle_python),
        "iverilog": str(iverilog),
        "vvp": str(vvp),
        "expected_marker": EXPECTED,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="ar03-gm01-export-") as temp_name:
            temp = Path(temp_name)
            stage = temp / "stage"
            stage.mkdir()
            for name in SOURCE_FILES:
                if name != "prepare_vectors.py":
                    shutil.copyfile(HERE / name, stage / name)
                    continue
                original = (HERE / name).read_bytes()
                if sha(original) != records[name]["sha256"]:
                    raise RuntimeError("bound original vector generator changed")
                if original.count(NATIVE_PATH_LINE) != 1:
                    raise RuntimeError("expected exactly one native checkout path literal")
                native_literal = repr(native_source.as_posix()).encode("utf-8")
                staged = original.replace(NATIVE_PATH_LINE,
                                          b"native_repo=Path(" + native_literal + b")", 1)
                # Selecting the original checkout is valid too; in that case
                # the exact single substitution may leave the bytes unchanged.
                result["generator_path_changed"] = staged != original
                (stage / name).write_bytes(staged)
                result["generator_original_sha256"] = sha(original)
                result["generator_staged_sha256"] = sha(staged)
            cache = temp / "oracle-pycache"
            if cache.exists():
                raise RuntimeError("oracle cache must start absent")

            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            oracle_cmd = [str(oracle_python), "-B", "-X", f"pycache_prefix={cache}",
                          str(stage / "prepare_vectors.py"), "--source", str(source)]
            oracle_run = subprocess.run(oracle_cmd, cwd=stage, env=env,
                                        capture_output=True, text=True)
            save(log_dir / "oracle.log", oracle_run.stdout + oracle_run.stderr)
            if oracle_run.returncode:
                raise RuntimeError(f"oracle vector preparation failed ({oracle_run.returncode})")
            result["oracle_summary"] = oracle_run.stdout.strip()
            vectors_sha = sha((stage / "vectors.hex").read_bytes())
            result["vectors_sha256"] = vectors_sha
            expected_vectors_sha = snapshot.get("expected_vectors_sha256")
            if not expected_vectors_sha or vectors_sha != expected_vectors_sha:
                raise RuntimeError("generated vectors.hex SHA-256 differs from sealed parent evidence")

            sim_env = env.copy()
            bin_dir = str(iverilog.parent)
            sim_env["PATH"] = bin_dir + os.pathsep + sim_env.get("PATH", "")
            binary = temp / "gm01.vvp"
            compile_run = subprocess.run(
                [str(iverilog), "-g2012", "-Wall", "-s", "tb", "-o", str(binary),
                 "gm01_sections.sv", "tb_gm01_sections.sv"],
                cwd=stage, env=sim_env, capture_output=True, text=True)
            save(log_dir / "compile.log", compile_run.stdout + compile_run.stderr)
            if compile_run.returncode:
                raise RuntimeError(f"Icarus compile failed ({compile_run.returncode})")
            simulation = subprocess.run([str(vvp), str(binary)], cwd=stage, env=sim_env,
                                        capture_output=True, text=True)
            output = simulation.stdout + simulation.stderr
            save(log_dir / "simulation.log", output)
            if simulation.returncode:
                raise RuntimeError(f"Icarus simulation failed ({simulation.returncode})")
            if EXPECTED not in output:
                raise RuntimeError("simulation did not emit the exact expected PASS marker")
            result["status"] = "PASS_HOST_ONLY"
            result["marker"] = EXPECTED
            result["generated_fixtures_retained"] = False
    except Exception as exc:
        result["error"] = str(exc)
        save(log_dir / "result.json", json.dumps(result, indent=2) + "\n")
        raise SystemExit(str(exc))

    save(log_dir / "result.json", json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
