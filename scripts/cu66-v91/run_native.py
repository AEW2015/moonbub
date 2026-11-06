#!/usr/bin/env python3
"""Build and measure the V91 native BR88 readers in the existing Docker toolchain."""
from __future__ import annotations

import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import struct
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91"
V88 = ROOT / "experiments/python-gamebub-v88/entropy"
CONTAINER = "gamebub-cu66-v69-build"
SELECTED = {(0, 0), (0, 1), (0, 3), (3, 50)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def u32(v: int) -> bytes:
    return struct.pack("<I", v)


def harness_input(frames, test):
    rows = []
    seen, benchmark_count = set(), 0
    for frame in frames.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        benchmark = identity in SELECTED
        if benchmark:
            seen.add(identity)
        for plane in frame["variants"]["65536"]:
            for chunk in plane:
                rows.append((chunk["blocks"], chunk["br88"], benchmark,
                             chunk["coefficient_sha256"], True))
                benchmark_count += int(benchmark)
    if seen != SELECTED or len(rows) != 1371 or benchmark_count != 12:
        raise AssertionError((len(rows), benchmark_count, seen))

    # Use the V91 directed-fixture builders without running their test suite.
    dc_data, dc_bits = test.rice_payload([0], 13, 14)
    valid_coded = test.packet(1, [(13, 255, dc_data, dc_bits),
                                  (0, 0, b"", 0), (0, 0, b"", 0),
                                  (0, 0, b"", 0)])
    valid_raw = test.packet(1, [], raw=[-2048, 2048] + [0] * 62)
    synthetic = [(1, valid_coded, False, hashlib.sha256(struct.pack("<64h", *([0] * 64))).hexdigest(), True),
                 (1, valid_raw, False, hashlib.sha256(struct.pack("<64h", -2048, 2048, *([0] * 62))).hexdigest(), True)]
    malformed = []

    def mutate(packet, offset, replacement):
        return test.crc(packet[:offset] + replacement + packet[offset + len(replacement):])

    # Mirrors the frozen V91 test_parser rejection families. Both native
    # readers must reject every case; expected hash is intentionally zeroed.
    malformed.extend([
        ("crc", valid_coded[:-1] + bytes((valid_coded[-1] ^ 1,)), 1),
        ("magic", mutate(valid_coded, 0, b"NOPE"), 1),
        ("version", mutate(valid_coded, 4, b"\x02"), 1),
        ("flags", mutate(valid_coded, 5, b"\x02"), 1),
        ("blocks", mutate(valid_coded, 6, struct.pack("<I", 2)), 1),
        ("bw", mutate(valid_coded, 10, b"\x02\x00"), 1),
        ("reserved", mutate(valid_coded, 12, b"\x01\x00"), 1),
        ("sum_lengths", mutate(valid_coded, 14, struct.pack("<I", 1)), 1),
        ("dc_k", mutate(valid_coded, 42, b"\x0e"), 1),
        ("dc_marker", mutate(valid_coded, 43, b"\x00"), 1),
        ("count_overflow", mutate(valid_coded, 30, struct.pack("<I", 7)), 1),
        ("packet_truncated", valid_coded[:-1], 1),
        ("geometry_zero", valid_coded, 0),
        ("raw_range", mutate(valid_raw, 46, struct.pack("<h", 32767)), 1),
        ("raw_fields", mutate(valid_raw, 30, struct.pack("<I", 1)), 1),
    ])
    for name, packet, blocks in malformed:
        rows.append((blocks, packet, False, "0" * 64, False))
    rows.extend(synthetic)

    output = bytearray(u32(len(rows)))
    for blocks, packet, bench, expected_hash, accepted in rows:
        if len(expected_hash) != 64:
            raise AssertionError("bad expected hash")
        output.extend(u32(blocks))
        output.extend(u32(len(packet)))
        output.extend(u32(int(bench)))
        output.extend(u32(int(accepted)))
        output.extend(packet)
        output.extend(expected_hash.encode("ascii"))
    return bytes(output), dict(cases=len(rows), actual_chunks=1371,
                               selected_benchmark_chunks=benchmark_count,
                               synthetic_valid=2, malformed=len(malformed))


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = AREA / "native-attempts" / (stamp + "-" + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True)
    build_o3 = "/build/v91-native-" + stamp
    build_san = build_o3 + "-san"
    source = AREA / "native.cpp"
    header = AREA / "native.hpp"
    script = Path(__file__).resolve()
    test_path = AREA / "test_parser.py"
    data_py, codec_py = V88 / "data.py", V88 / "codec.py"
    index_path = V88 / "index.json"
    fixture = V88 / "attempts/20261106T150638168868Z-fb236a5e/data.bin.gz"
    v85 = ROOT / "experiments/python-gamebub-v85/residual"
    native_v69 = ROOT / "experiments/cu66-native-v69"
    input_path = attempt / "cases.bin.gz"
    sources = [script, source, header, test_path, data_py, codec_py, index_path, fixture,
               v85 / "data.py", v85 / "index.json", native_v69 / "bytes.hpp",
               native_v69 / "entropy.hpp", v85 / "encode.hpp"]
    report = dict(schema="cu66-v91-native-reader-benchmark-v1", status="FAIL",
                  source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  compiler="g++", container=CONTAINER, optimized_flags=["-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror"],
                  sanitizer_flags=["-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"],
                  optimized_binary=build_o3, sanitizer_binary=build_san, commands=[],
                  timing_scope="Paired native host CPU BR88 decode calls for 12 selected chunks; CRC, grammar, bit parsing and coefficient-vector construction included; file input, hashes and whole-frame reconstruction excluded.",
                  hardware_scope="No FPGA/ESP32 cycle, routed timing or full-frame latency claim.")
    start = time.monotonic()

    def run(argv, log, timeout, input_bytes=None):
        try:
            result = subprocess.run(argv, input=input_bytes, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=timeout)
            output = result.stdout
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or b""
            (attempt / log).write_bytes(output)
            report["commands"].append(dict(argv=argv, exit_code="TIMEOUT", log=log))
            raise RuntimeError(f"timeout running {' '.join(argv)}")
        (attempt / log).write_bytes(output)
        report["commands"].append(dict(argv=argv, exit_code=result.returncode, log=log))
        if result.returncode:
            raise RuntimeError(f"command failed ({result.returncode}); see {attempt / log}")
        return output

    try:
        frames = load("v91_native_frozen_data", data_py)
        test = load("v91_native_test_fixtures", test_path)
        binary_input, counts = harness_input(frames, test)
        with input_path.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=9) as stream:
                stream.write(binary_input)
        report.update(counts=counts, input_fixture={"path": str(input_path.relative_to(ROOT)),
                                                     "gzip_sha256": sha(input_path),
                                                     "raw_sha256": hashlib.sha256(binary_input).hexdigest(),
                                                     "raw_bytes": len(binary_input)})
        (attempt / "metadata.json").write_text(json.dumps({
            "schema": "cu66-v91-native-attempt-input-v1",
            "source_commit": report["source_commit"],
            "source_sha256": report["source_sha256"],
            "counts": counts,
            "input_fixture": report["input_fixture"],
            "benchmark_ids": sorted(f"c{c}-f{f}" for c, f in SELECTED),
            "optimized_flags": report["optimized_flags"],
            "sanitizer_flags": report["sanitizer_flags"],
        }, indent=2) + "\n")
        run(["docker", "exec", CONTAINER, "g++", "--version"], "compiler-version.log", 30)
        run(["docker", "exec", CONTAINER, "g++", "-std=c++17", "-O3", "-Wall", "-Wextra", "-Werror",
             str(source), "-o", build_o3], "compile-o3.log", 300)
        run(["docker", "cp", f"{CONTAINER}:{build_o3}", str(attempt / "native-o3.bin")], "copy-o3.log", 60)
        o3 = run(["docker", "exec", "-i", CONTAINER, build_o3], "optimized-output.jsonl", 300,
                 input_bytes=binary_input)
        rows = [json.loads(line) for line in o3.decode().splitlines()]
        case_rows = [r for r in rows if r.get("kind") == "case"]
        timings = [r for r in rows if r.get("kind") == "timing"]
        done = [r for r in rows if r.get("kind") == "done"]
        if len(case_rows) != counts["cases"] or len(timings) != 7 * 12 * 2 or len(done) != 1:
            raise AssertionError((len(case_rows), len(timings), done))
        if done[0].get("status") != "PASS" or done[0].get("cases") != counts["cases"]:
            raise AssertionError(done)
        per_repeat = []
        for repeat in range(7):
            sums = {variant: sum(row["ns"] for row in timings
                                 if row["repeat"] == repeat and row["variant"] == variant)
                    for variant in ("bit", "word32")}
            per_repeat.append({"repeat": repeat, "bit_ns_per_singlepass_12_chunks": sums["bit"] / 20,
                               "word32_ns_per_singlepass_12_chunks": sums["word32"] / 20,
                               "bit_over_word32": sums["bit"] / sums["word32"]})
        ratios = [r["bit_over_word32"] for r in per_repeat]
        report.update(optimized=dict(status="PASS", done=done[0], case_rows=len(case_rows),
                                     timing_rows=len(timings), timings=timings,
                                     benchmark_plan=dict(selected_chunks=12, repeats=7,
                                                         variants_per_chunk_repeat=2,
                                                         decode_iterations_per_timing_row=20,
                                                         summary="Each repeat sums 12 chunk timings per variant and divides by 20 decode iterations, yielding one normalized pass over the selected 12 chunks; not a frame-latency measurement."),
                                     paired_repeat_summary=per_repeat,
                                     median_bit_over_word32=statistics.median(ratios),
                                     binary_sha256=sha(attempt / "native-o3.bin")))

        # Same exact binary input, verification mode suppresses all benchmark
        # loops. Compile is deliberately sequential with the O3 build.
        run(["docker", "exec", CONTAINER, "g++", "-std=c++17", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
             "-fsanitize=address,undefined", "-fno-omit-frame-pointer", str(source), "-o", build_san],
            "compile-sanitizer.log", 300)
        run(["docker", "cp", f"{CONTAINER}:{build_san}", str(attempt / "native-sanitizer.bin")],
            "copy-sanitizer.log", 60)
        sanitized = run(["docker", "exec", "-i", CONTAINER, build_san, "--verify-only"],
                        "sanitizer-output.jsonl", 300, input_bytes=binary_input)
        san_rows = [json.loads(line) for line in sanitized.decode().splitlines()]
        san_cases = [r for r in san_rows if r.get("kind") == "case"]
        san_done = [r for r in san_rows if r.get("kind") == "done"]
        if len(san_cases) != counts["cases"] or len(san_done) != 1 or san_done[0].get("status") != "PASS":
            raise AssertionError((len(san_cases), san_done))
        report["sanitizer"] = dict(status="PASS", case_rows=len(san_cases), done=san_done[0],
                                   binary_sha256=sha(attempt / "native-sanitizer.bin"),
                                   timing_collected=False)
        report.update(environment=dict(host_platform=platform.platform(),
                                       python=sys.version,
                                       container_compiler=next((line for line in
                                           (attempt / "compiler-version.log").read_text().splitlines()
                                           if line.startswith("g++")), "see compiler-version.log")),
                      output_scope="Native host CPU parser comparison only; not full frame, FPGA, embedded CPU or hardware timing.")
        # Preserve input plus source snapshots needed to reproduce the run.
        snapshot = attempt / "sources"
        for path in sources:
            target = snapshot / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        report["artifact_sha256"] = {str(p.relative_to(attempt)): sha(p)
                                     for p in attempt.rglob("*") if p.is_file()}
        # Recheck pinned inputs only after all final files/summaries exist.
        if report["source_sha256"] != {str(p.relative_to(ROOT)): sha(p) for p in sources}:
            raise AssertionError("source changed during run")
        report["status"] = "PASS"
        (AREA / "native-results.json").write_text(json.dumps(
            dict(report, selected_attempt=str(attempt.relative_to(ROOT))), indent=2) + "\n")
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["status"] = "FAIL"
        # Retain source snapshots and hashes for a failed compile/run too.
        snapshot = attempt / "sources"
        for path in sources:
            if path.exists():
                target = snapshot / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        report["artifact_sha256"] = {str(p.relative_to(attempt)): sha(p)
                                     for p in attempt.rglob("*") if p.is_file()}
        (AREA / "native-results.json").write_text(json.dumps(
            dict(report, selected_attempt=str(attempt.relative_to(ROOT))), indent=2) + "\n")
        raise
    finally:
        report["wall_seconds"] = time.monotonic() - start
        selected = dict(report, selected_attempt=str(attempt.relative_to(ROOT)))
        serialized = json.dumps(selected, indent=2) + "\n"
        (attempt / "results.json").write_text(serialized)
        (AREA / "native-results.json").write_text(serialized)
        print("V91_NATIVE_REPORT", AREA / "native-results.json", report["status"], flush=True)


if __name__ == "__main__":
    main()
