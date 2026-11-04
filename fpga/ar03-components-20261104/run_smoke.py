#!/usr/bin/env python3
"""Compile/run two bounded source-only smoke benches in a temporary directory."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
SNAPSHOT = ROOT / "source-snapshot.json"


def find_tool(name: str, windows_path: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(windows_path)
    if candidate.is_file():
        return str(candidate)
    raise SystemExit(f"required simulator tool not found: {name}")


def verify_source_snapshot() -> dict:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    for entry in snapshot["files"]:
        path = ROOT / entry["export_path"]
        data = path.read_bytes()
        got = hashlib.sha256(data).hexdigest()
        if len(data) != entry["bytes"] or got != entry["sha256"]:
            raise SystemExit(f"source snapshot mismatch: {entry['export_path']}")
    return snapshot


def execute(iverilog: str, vvp: str, top: str, sources: list[Path],
            expected_summary: str, outdir: Path) -> str:
    image = outdir / f"{top}.vvp"
    env = os.environ.copy()
    tool_dirs = [str(Path(iverilog).resolve().parent), str(Path(vvp).resolve().parent)]
    env["PATH"] = os.pathsep.join(tool_dirs) + os.pathsep + env.get("PATH", "")
    compile_cmd = [iverilog, "-g2012", "-Wall", "-s", top, "-o", str(image),
                   *map(str, sources)]
    compiled = subprocess.run(compile_cmd, cwd=outdir, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              env=env)
    if compiled.returncode:
        raise SystemExit(f"{top} compile failed ({compiled.returncode}):\n{compiled.stdout}")
    simulated = subprocess.run([vvp, "-i", str(image)], cwd=outdir, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=env)
    if simulated.returncode:
        raise SystemExit(f"{top} simulation failed ({simulated.returncode}):\n{simulated.stdout}")
    if expected_summary not in simulated.stdout:
        raise SystemExit(f"{top} summary missing {expected_summary!r}:\n{simulated.stdout}")
    return f"=== {top} compile ===\n{compiled.stdout}=== {top} simulation ===\n{simulated.stdout}"


def main() -> int:
    verify_source_snapshot()
    iverilog = find_tool("iverilog", r"C:\msys64\ucrt64\bin\iverilog.exe")
    vvp = find_tool("vvp", r"C:\msys64\ucrt64\bin\vvp.exe")
    cp02 = SOURCE / "fpga/experiments/ar03-entropy-20261104/variant-002-timing/cp02_decoder.sv"
    admission = SOURCE / "fpga/experiments/ar03-entropy-20261104/variant-002-timing/tb_admission.sv"
    envelope = SOURCE / "fpga/experiments/ar03-envelope-20261104/ar03_envelope.sv"
    storage = SOURCE / "fpga/experiments/ar03-envelope-20261104/tb_storage_cap.sv"
    with tempfile.TemporaryDirectory(prefix="ar03-components-smoke-") as temp:
        outdir = Path(temp)
        reports = [
            execute(iverilog, vvp, "tb_admission", [cp02, admission],
                    "ADMISSION_PASS valid=22 rejects=8 abort_offsets=16 held_first_byte=1 exact_remainder_steps=14 boundary_blocks=8192 boundary_width=256", outdir),
            execute(iverilog, vvp, "tb_storage_cap", [envelope, storage],
                    "STORAGE_PARAMETER_CAP_PASS checks=9 protocol_cap=49152 large_storage=65536 small_storage=115", outdir),
        ]
    print(f"IVERILOG={iverilog}\nVVP={vvp}")
    print("\n".join(reports), end="")
    print("AR03_COMPONENTS_SMOKE_PASS benches=2 outputs=temporary-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
