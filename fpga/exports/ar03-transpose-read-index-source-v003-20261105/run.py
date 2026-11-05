"""Replay the three source-bound transpose equivalence profiles."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = [
    "rtl/ar03_yuv_transpose_baseline.sv",
    "rtl/ar03_yuv_transpose_double_baseline.sv",
    "rtl/ar03_yuv_transpose.sv",
    "rtl/ar03_yuv_transpose_double.sv",
    "rtl/parents/ar03_yuv_transpose_single.sv",
    "rtl/parents/moonshine_burst_packer.sv",
    "rtl/parents/moonshine_sdram_burst.sv",
    "rtl/parents/moonshine_memory_burst.sv",
    "rtl/parents/sdram_model_bounded.sv",
    "sim/tb_transpose.sv",
]
VECTORS = [
    "sim/vectors/unit-sequence.hex",
    "sim/vectors/unit-column.hex",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_package():
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {row["path"]: row for row in manifest["artifacts"]}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if actual != set(expected):
        raise RuntimeError("export file set does not match manifest")
    for rel, row in expected.items():
        path = ROOT / rel
        if path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
            raise RuntimeError(f"export integrity failed: {rel}")


def external(path):
    try:
        path.relative_to(ROOT)
        return False
    except ValueError:
        pass
    try:
        ROOT.relative_to(path)
        return False
    except ValueError:
        return True


def find_tool(env_name, tool_name, fallback):
    configured = os.environ.get(env_name)
    if configured:
        return configured
    found = shutil.which(tool_name)
    if found:
        return found
    if Path(fallback).is_file():
        return fallback
    raise RuntimeError(f"{tool_name} not found; put it on PATH or set {env_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["directed", "full", "end-abort"], required=True)
    parser.add_argument("--evidence", required=True, help="fresh directory outside this export")
    args = parser.parse_args()
    out = Path(args.evidence).expanduser().resolve()
    if not external(out):
        raise RuntimeError("evidence must be outside and separate from this export")
    if out.exists():
        raise RuntimeError("evidence directory already exists; use a new path")

    verify_package()
    iverilog = find_tool(
        "IVERILOG", "iverilog", "C:/msys64/ucrt64/bin/iverilog.exe"
    )
    vvp = find_tool("VVP", "vvp", "C:/msys64/ucrt64/bin/vvp.exe")
    out.mkdir(parents=True)
    for rel in SOURCES:
        target = out / "inputs" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    for rel in VECTORS:
        shutil.copy2(ROOT / rel, out / Path(rel).name)

    mode = {"directed": 0, "full": 1, "end-abort": 2}[args.profile]
    compiled = [str(out / "inputs" / rel) for rel in SOURCES]
    executable = out / "transpose.vvp"
    compile_command = [
        iverilog,
        "-g2012",
        "-Wall",
        "-DSIMULATION",
        "-s",
        "tb_transpose",
        f"-Ptb_transpose.FULL_TEST={mode}",
        "-o",
        str(executable),
        *compiled,
    ]
    simulation_command = [vvp, "-i", str(executable)]
    hashes = {
        rel: sha256(ROOT / rel) for rel in SOURCES + VECTORS
    }
    tool_dirs = [str(Path(tool).resolve().parent) for tool in (iverilog, vvp)]
    child_env = os.environ.copy()
    child_env["PATH"] = os.pathsep.join(tool_dirs + [child_env.get("PATH", "")])
    steps = []
    for name, command in (("compile", compile_command), ("simulation", simulation_command)):
        started = time.monotonic()
        result = subprocess.run(
            command,
            cwd=out,
            env=child_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (out / f"{name}.log").write_text(result.stdout, encoding="utf-8")
        steps.append(
            {
                "name": name,
                "command": command,
                "returncode": result.returncode,
                "wall_seconds": time.monotonic() - started,
                "log": f"{name}.log",
            }
        )
        (out / "execution.json").write_text(json.dumps(steps, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            raise SystemExit(result.returncode)

    output = (out / "simulation.log").read_text(encoding="utf-8", errors="replace")
    marker = "TRANSPOSE_DIRECTED_PASS" if mode == 0 else "TRANSPOSE_FULL_PASS"
    if marker not in output:
        raise RuntimeError(f"expected completion marker missing: {marker}")
    if mode == 2 and "aborted_at_final_flush=1" not in output:
        raise RuntimeError("end-abort profile did not report final-flush abort")
    if mode == 1 and "aborted_at_final_flush=0" not in output:
        raise RuntimeError("full profile reported an unexpected final-flush abort")
    verify_package()
    result = {
        "status": "PASS_FUNCTIONAL_TRANSPOSE_ONLY",
        "profile": args.profile,
        "marker": marker,
        "summary": [line for line in output.splitlines() if "_PASS" in line],
        "source_hashes": hashes,
        "hardware_actions": "NONE",
        "ooc_or_board_claim": "NONE",
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(marker)


if __name__ == "__main__":
    main()
