#!/usr/bin/env python3
"""Offline full-fixture replay for the sealed private AR03 compute candidate."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

FIXTURE_BYTES = 48203
FIXTURE_SHA256 = "5a39857f436fc50daaa46fc518ab13f9c168fbdadabbe95ef8bf6eeff02c0518"
EXPECTED_BYTES = 518400
EXPECTED_SHA256 = "cdb3d93c247a8210e32bfa131151b91cf4ad973ed3954f51edbd1dfbd3fda836"
SOURCE_FILES = [
    "ar03_fixture_diagnostic.sv", "tb_controls.sv", "tb_diagnostic.sv",
    "quantizers.hex",
    "parents/ar03_envelope.sv", "parents/ar03_inverse.sv",
    "parents/ar03_key_pipeline_meta.sv", "parents/ar03_key_tagged.sv",
    "parents/ar03_raster_stripes.sv", "parents/ar03_reconstruct.sv",
    "parents/canonical_tag.sv", "parents/cp02_decoder.sv",
    "parents/cp02_key_join.sv", "parents/gm01_sections.sv",
    "parents/sha256_bytes.sv",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_hex_file(path):
    raw = path.read_bytes()
    try:
        compact = re.sub(rb"\s+", b"", raw)
        logical = bytes.fromhex(compact.decode("ascii"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"{path}: expected ASCII hexadecimal bytes with optional whitespace: {exc}") from exc
    return raw, logical


def write_hex(path, data):
    path.write_text("".join(f"{byte:02x}\n" for byte in data), encoding="ascii", newline="\n")


def run_logged(command, cwd, env, logfile):
    start = time.monotonic()
    with logfile.open("wb") as stream:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
    return {"returncode": result.returncode, "wall_seconds": round(time.monotonic() - start, 3),
            "command": [str(x) for x in command], "log": logfile.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", required=True, type=Path,
                        help="external directory containing fixture.raw and expected.hex")
    parser.add_argument("--iverilog", default=r"C:\msys64\ucrt64\bin\iverilog.exe")
    parser.add_argument("--vvp", default=r"C:\msys64\ucrt64\bin\vvp.exe")
    parser.add_argument("--evidence-dir", type=Path,
                        help="directory for compile/simulation logs and run.json")
    parser.add_argument("--reuse-diagnostic-evidence", type=Path,
                        help="reuse a prior successful diagnostic compile/simulation log pair after marker validation")
    args = parser.parse_args()

    export = Path(__file__).resolve().parent
    fixture_dir = args.fixtures.resolve()
    fixture_path = fixture_dir / "fixture.raw"
    expected_path = fixture_dir / "expected.hex"
    if not fixture_path.is_file() or not expected_path.is_file():
        raise SystemExit("--fixtures must contain fixture.raw and expected.hex")
    fixture = fixture_path.read_bytes()
    expected_text, expected = parse_hex_file(expected_path)
    if len(fixture) != FIXTURE_BYTES or sha(fixture) != FIXTURE_SHA256:
        raise SystemExit(f"fixture.raw identity mismatch: bytes={len(fixture)} sha256={sha(fixture)}")
    if len(expected) != EXPECTED_BYTES or sha(expected) != EXPECTED_SHA256:
        raise SystemExit(f"expected.hex logical YUV mismatch: bytes={len(expected)} sha256={sha(expected)}")

    evidence = (args.evidence_dir or (export / "replay-evidence")).resolve()
    if evidence.exists() and any(evidence.iterdir()):
        raise SystemExit(f"evidence directory must be fresh and empty: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)

    iverilog = str(Path(args.iverilog).resolve())
    vvp = str(Path(args.vvp).resolve())
    env = dict(os.environ)
    bins = [str(Path(iverilog).parent), str(Path(vvp).parent)]
    env["PATH"] = os.pathsep.join(bins + [env.get("PATH", "")])
    result = {
        "scope": "private pre-HUD KEY tag/compute-only offline replay",
        "fixture": {"path_name": fixture_path.name, "bytes": len(fixture), "sha256": sha(fixture)},
        "expected": {"path_name": expected_path.name, "file_bytes": len(expected_text),
                     "file_sha256": sha(expected_text), "logical_bytes": len(expected),
                     "logical_sha256": sha(expected)},
        "source_hashes_before": {}, "stages": {},
        "temporary_directory_cleanup": "pending",
    }
    pinned = json.loads((export / "source-snapshot.json").read_text(encoding="utf-8"))["copied_sources"]
    pinned_hashes = {name: entry["sha256"] for name, entry in pinned.items()}
    for rel in SOURCE_FILES:
        source = export / rel
        if not source.is_file():
            raise SystemExit(f"missing exported source: {rel}")
        digest = sha(source.read_bytes())
        if rel not in pinned or digest != pinned[rel]["sha256"]:
            raise SystemExit(f"source-snapshot hash mismatch: {rel}")
        result["source_hashes_before"][rel] = digest

    with tempfile.TemporaryDirectory(prefix="ar03-compute-replay-") as temp_name:
        temp = Path(temp_name)
        for rel in SOURCE_FILES:
            dest = temp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(export / rel, dest)
        write_hex(temp / "fixture.hex", fixture)
        write_hex(temp / "expected.hex", expected)

        if args.reuse_diagnostic_evidence:
            reused = args.reuse_diagnostic_evidence.resolve()
            compile_log = reused / "diagnostic-compile.log"
            simulation_log = reused / "diagnostic-simulation.log"
            if not compile_log.is_file() or not simulation_log.is_file():
                raise SystemExit("reuse directory lacks diagnostic compile/simulation logs")
            diagnostic_text = simulation_log.read_text(errors="replace")
            if "PASS diagnostic samples=518400 ingress=48203 cycles=3000322 tag=855898f019ffddad10bef275ee7dc9c6 owner=2 busy_rejects=1 abort_recovery=1" not in diagnostic_text:
                raise SystemExit("reused diagnostic log lacks the exact full-replay PASS marker")
            result["stages"]["diagnostic_compile"] = {"returncode": 0, "reused": True,
                "log": str(compile_log), "log_sha256": sha(compile_log.read_bytes())}
            result["stages"]["diagnostic_simulation"] = {"returncode": 0, "reused": True,
                "log": str(simulation_log), "log_sha256": sha(simulation_log.read_bytes()),
                "output": diagnostic_text.strip()}
        else:
            diagnostic = (temp / "tb_diagnostic.sv").read_text(encoding="utf-8")
            assert diagnostic.count("module tb;") == 1
            (temp / "tb_diagnostic.sv").write_text(diagnostic.replace("module tb;", "module tb_diagnostic;", 1), encoding="utf-8", newline="\n")
            full_sources = ["ar03_fixture_diagnostic.sv"] + [x for x in SOURCE_FILES if x.startswith("parents/")] + ["tb_diagnostic.sv"]
            full_cmd = [iverilog, "-g2012", "-s", "tb_diagnostic", "-o", "diagnostic.vvp", *full_sources]
            result["stages"]["diagnostic_compile"] = run_logged(full_cmd, temp, env, evidence / "diagnostic-compile.log")
            if result["stages"]["diagnostic_compile"]["returncode"] != 0:
                raise SystemExit("full diagnostic Icarus compile failed; see diagnostic-compile.log")
            result["stages"]["diagnostic_simulation"] = run_logged([vvp, "-i", "diagnostic.vvp"], temp, env, evidence / "diagnostic-simulation.log")
            if result["stages"]["diagnostic_simulation"]["returncode"] != 0:
                raise SystemExit("full diagnostic simulation failed; see diagnostic-simulation.log")
            diagnostic_text = (evidence / "diagnostic-simulation.log").read_text(errors="replace")
            if "PASS diagnostic samples=518400 ingress=48203 cycles=3000322 tag=855898f019ffddad10bef275ee7dc9c6 owner=2 busy_rejects=1 abort_recovery=1" not in diagnostic_text:
                raise SystemExit("full diagnostic log lacks the exact replay PASS marker")

        controls = (temp / "tb_controls.sv").read_text(encoding="utf-8")
        assert controls.count("module tb;") == 1
        controls = controls.replace("module tb;", "module tb_controls;", 1)
        controls += r'''
// Stub required to elaborate controller-only tests. The testbench forces the
// selected event wires directly; this does not model compute functionality.
module ar03_key_tagged(
 input wire clk, reset, abort, input wire start_valid, output wire start_ready,
 input wire [63:0] start_owner, input wire [31:0] start_bytes, start_epoch,
 input wire in_valid, output wire in_ready, input wire [7:0] in_byte, input wire in_last,
 output wire sample_valid, input wire sample_ready, output wire [7:0] sample,
 output wire [63:0] sample_owner, output wire [31:0] sample_epoch, sample_frame,
 output wire [1:0] sample_plane, output wire [15:0] sample_x, sample_y, output wire sample_last,
 output wire completion_valid, input wire completion_ready,
 output wire [63:0] completion_owner, output wire [31:0] completion_epoch, completion_frame,
 output wire [127:0] completion_tag, output wire error_valid, input wire error_ready,
 output wire [3:0] error_stage, output wire [7:0] error_code, output wire [63:0] error_owner
);
 assign start_ready=1, in_ready=1, sample_valid=0, sample=0, sample_owner=0,
        sample_epoch=0, sample_frame=0, sample_plane=0, sample_x=0, sample_y=0,
        sample_last=0, completion_valid=0, completion_owner=0, completion_epoch=0,
        completion_frame=0, completion_tag=0, error_valid=0, error_stage=0,
        error_code=0, error_owner=0;
endmodule
'''
        (temp / "tb_controls.sv").write_text(controls, encoding="utf-8", newline="\n")
        control_cmd = [iverilog, "-g2012", "-s", "tb_controls", "-o", "controls.vvp",
                       "ar03_fixture_diagnostic.sv", "tb_controls.sv"]
        result["stages"]["controls_compile"] = run_logged(control_cmd, temp, env, evidence / "controls-compile.log")
        if result["stages"]["controls_compile"]["returncode"] != 0:
            raise SystemExit("controller-only Icarus compile failed; see controls-compile.log")
        result["stages"]["controls_simulation"] = run_logged([vvp, "-i", "controls.vvp"], temp, env, evidence / "controls-simulation.log")
        if result["stages"]["controls_simulation"]["returncode"] != 0:
            raise SystemExit("controller-only simulation failed; see controls-simulation.log")
        controls_text = (evidence / "controls-simulation.log").read_text(errors="replace")
        if "PASS controller checks=20 admission_watchdog=1 execution_watchdog=1 injected_error=1 stale_completion=1 reset=1" not in controls_text:
            raise SystemExit("controller log lacks the 20-check PASS marker")
        result["stages"]["diagnostic_output"] = diagnostic_text.strip()
        result["stages"]["controls_output"] = controls_text.strip()

    result["temporary_directory_cleanup"] = "TemporaryDirectory context exited"
    result["source_hashes_after"] = {rel: sha((export / rel).read_bytes()) for rel in SOURCE_FILES}
    result["exported_source_unchanged"] = result["source_hashes_before"] == result["source_hashes_after"]
    if not result["exported_source_unchanged"]:
        raise SystemExit("exported copied-source hash changed during replay")
    if result["source_hashes_after"] != pinned_hashes:
        raise SystemExit("exported source no longer matches source-snapshot.json after replay")
    result["status"] = "PASS"
    (evidence / "run.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: full 518400-sample diagnostic replay and 20 controller checks")
    print(f"Evidence: {evidence}")


if __name__ == "__main__":
    main()
