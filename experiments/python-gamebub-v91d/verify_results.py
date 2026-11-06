#!/usr/bin/env python3
"""Independent V91d vector, packed-image and finite-memory RTL receipt audit."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import math
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91d"
VECTORS = AREA / "vectors"
RTL = ROOT / "fpga/experiments/cu66-v91d"
BASE = "4ff660d4be06ef522de977bb78badd2b64a79e72"
PIPELINE_SEEDS = (910432, 910433)
LIMITS = (1, 6, 21, 64)
ORDER = tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
INVERSE = {raster: at for at, raster in enumerate(ORDER)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    assert path.is_file(), f"missing pinned file: {path}"
    return sha(path.read_bytes())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def aligned(n: int) -> int:
    return (n + 15) // 16 * 16


def dense_from_packet(packet: bytes, blocks: int, codec) -> list[int]:
    values = codec.decode(packet, blocks, 1)
    assert len(values) == blocks * 64
    assert all(-2048 <= value <= 2048 for value in values)
    return values


def sparse_from_dense(values: list[int], blocks: int, raw: bool) -> list[list[int]]:
    if raw:
        return [[0, block, index, values[block * 64 + index]]
                for block in range(blocks) for index in range(64)]
    events = [[0, block, 0, values[block * 64]] for block in range(blocks)]
    for band, (lo, hi) in enumerate(zip(LIMITS, LIMITS[1:]), start=1):
        for block in range(blocks):
            for slot in range(lo, hi):
                index = ORDER[slot]
                value = values[block * 64 + index]
                if value:
                    events.append([band, block, index, value])
    return events


def packed_image(blocks: int, counts: list[int], raw: bool, values: list[int],
                 sparse: list[list[int]]) -> bytes:
    if raw:
        segments = [struct.pack("<" + "h" * len(values), *values)]
        starts = [32]
    else:
        dc = [event[3] for event in sparse if event[0] == 0]
        assert len(dc) == blocks
        segments = [struct.pack("<" + "h" * len(dc), *dc)]
        starts = [32]
        for band in range(1, 4):
            records = []
            for event_band, block, raster, value in sparse:
                if event_band == band:
                    assert 0 <= block < (1 << 13) and 0 <= raster < 64
                    assert -2048 <= value <= 2048 and value != 0
                    records.append(((block << 19) | (raster << 13) | (value & 0x1fff)).to_bytes(4, "little"))
            assert len(records) == counts[band - 1]
            segments.append(b"".join(records))
    used = 32 + sum(aligned(len(segment)) for segment in segments)
    header = struct.pack("<8I", 0x43393150, blocks, int(raw), *counts, used, 0)
    assert len(header) == 32
    out = bytearray(header)
    for segment in segments:
        out.extend(segment)
        out.extend(bytes(aligned(len(segment)) - len(segment)))
    assert len(out) == used
    return bytes(out)


def overbudget_probe(codec) -> dict:
    """Rebuild the valid 8,192-block packet used to test pre-write admission."""
    blocks = 8192
    bit_counts = (8192, 81920, 50000, 0)
    event_counts = [40960, 25000, 0]
    packet = bytearray(struct.pack("<4sBBIHH", b"BR88", 1, 0, blocks, 1, 0))
    packet.extend(struct.pack("<4I", *(6 + (bits + 7) // 8 for bits in bit_counts)))
    packet.extend(struct.pack("<3I", *event_counts))
    for band, bit_count in enumerate(bit_counts):
        packet.extend(struct.pack("<BBI", 0, 255 if band == 0 else 0, bit_count))
        data = bytearray((bit_count + 7) // 8)
        for position in range(bit_count):
            data[position // 8] |= 1 << (7 - position % 8)
        packet.extend(data)
    packet.extend(struct.pack("<I", __import__("zlib").crc32(packet) & 0xffffffff))
    packet = bytes(packet)
    dense = codec.decode(packet, blocks, 1)
    assert len(dense) == blocks * 64 and set(dense) == {0, -1}
    used = 32 + aligned(blocks * 2) + aligned(event_counts[0] * 4) + aligned(event_counts[1] * 4)
    assert len(packet) == 17584 and used == 280256 and used > 262144
    return {"packet_bytes": len(packet), "packet_sha256": sha(packet),
            "decoded_coefficients": len(dense), "decoded_values": sorted(set(dense)),
            "blocks": blocks, "counts": event_counts, "packed_bytes": used,
            "capacity_bytes": 262144, "valid_v88_decode": True}


def verify_vectors() -> tuple[dict, dict[str, dict]]:
    index_path = VECTORS / "index.json"
    index = json.loads(index_path.read_text())
    assert index["schema"] == "cu66-v91d-coefficient-packed-image-v1"
    assert index["parent_commit"] == index["source_commit"] == BASE
    assert index["status"] == "PASS_FROZEN_V88_COEFFICIENT_AND_PACKED_IMAGE_GOLDENS"
    assert index["packets"] == 17 and index["actual_cases"] == 12 and index["synthetic_cases"] == 4
    assert index["directed_cases"] == 1
    assert index["scratch_layout"] == {
        "burst_bytes": 16,
        "exact_capacity_case": {"one_burst_short_bytes": 262160, "raw_blocks": 2048, "used_bytes": 262176},
        "header_bytes": 32, "max_blocks": 8192,
        "packed_word": "block[31:19]|raster[18:13]|signed13[12:0]"}
    fixture = VECTORS / index["fixture"]["path"]
    compressed = fixture.read_bytes()
    raw = gzip.decompress(compressed)
    assert sha(compressed) == index["fixture"]["gzip_sha256"]
    assert sha(raw) == index["fixture"]["jsonl_sha256"]
    for rel, expected in index["source_sha256"].items():
        assert file_sha(ROOT / rel) == expected, f"vector source pin mismatch: {rel}"

    codec = load_module("v91d_independent_v88_codec", ROOT / "experiments/python-gamebub-v88/entropy/codec.py")
    overbudget = overbudget_probe(codec)
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == index["packets"]
    assert len({row["id"] for row in rows}) == len(rows)
    actual = [row for row in rows if row["case_type"] == "actual"]
    synthetic = [row for row in rows if row["case_type"] == "synthetic"]
    directed = [row for row in rows if row["case_type"] == "directed"]
    assert (len(actual), len(synthetic), len(directed)) == (12, 4, 1)
    output_count = packed_bytes = 0
    by_id = {}
    for row in rows:
        blocks, counts, raw_mode = row["blocks"], row["counts"], bool(row["raw"])
        packet = bytes.fromhex(row["packet_hex"])
        values = dense_from_packet(packet, blocks, codec)
        dense = struct.pack("<" + "h" * len(values), *values)
        sparse = sparse_from_dense(values, blocks, raw_mode)
        image = packed_image(blocks, counts, raw_mode, values, sparse)
        assert row["dense_hex"] == dense.hex(), row["id"]
        assert row["sparse"] == sparse, row["id"]
        assert row["packed_hex"] == image.hex(), row["id"]
        assert row["coefficient_sha256"] == sha(dense), row["id"]
        assert row["packed_sha256"] == sha(image), row["id"]
        assert row["used_bytes"] == len(image)
        assert row["v91c_scratch_sha256"] == row["packed_sha256"] if row["case_type"] == "actual" else True
        assert len(packet) >= 46 and packet[:4] == b"BR88"
        assert int.from_bytes(packet[6:10], "little") == blocks
        assert bool(packet[5] & 1) == raw_mode
        if raw_mode:
            assert counts == [0, 0, 0]
        else:
            assert len([e for e in sparse if e[0] == 0]) == blocks
        output_count += blocks * 64
        packed_bytes += len(image)
        by_id[row["id"]] = {"blocks": blocks, "raw": raw_mode, "counts": counts,
                             "used_bytes": len(image), "packet_bytes": len(packet),
                             "outputs": blocks * 64, "case_type": row["case_type"],
                             "packed_sha256": sha(image), "dense_sha256": sha(dense)}
    large = next(row for row in rows if row["id"] == "scratch_8192_last_record")
    assert large["blocks"] == 8192 and large["counts"] == [0, 0, 1]
    assert large["sparse"][-1] == [3, 8191, 63, -2048]
    assert len(bytes.fromhex(large["packed_hex"])) == 16432
    summary = {"packet_rows": len(rows), "actual_packets": len(actual),
               "synthetic_packets": len(synthetic), "directed_packets": len(directed),
               "dense_coefficients": output_count, "packed_image_bytes": packed_bytes,
               "fixture_sha256": sha(compressed), "jsonl_sha256": sha(raw),
               "source_sha256": index["source_sha256"], "case_ids": sorted(by_id),
               "valid_overbudget_admission_probe": overbudget}
    return summary, by_id


def check_receipt(report: dict, path: Path, schema: str, status: str,
                  expected_sources: dict[str, str] | None = None) -> dict:
    assert report["schema"] == schema and report["status"] == status
    assert report["source_revision"] == BASE
    attempt = path.parent
    for row in report["commands"]:
        assert row["exit_code"] == 0, (attempt.name, row)
        log = attempt / row["log"]
        assert log.is_file(), (attempt.name, row["log"])
    argv = [arg for row in report["commands"] for arg in row["argv"]]
    assert "--assert" in argv and "-Wall" in argv
    assert any("-Werror" in item for item in argv)
    compile_log = (attempt / "compile.log").read_text()
    assert not re.search(r"%Warning|\bwarning:", compile_log, re.IGNORECASE)
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest, (attempt.name, rel)
        snap = attempt / "sources" / rel
        assert file_sha(snap) == digest, (attempt.name, "snapshot", rel)
    if expected_sources is not None:
        assert report["source_sha256"] == expected_sources
    for rel, digest in report["artifacts_sha256"].items():
        candidate = attempt / rel
        if candidate.is_file():
            observed = file_sha(candidate)
        elif rel == "vectors.txt" and (attempt / "vectors.jsonl.gz").is_file():
            lines = []
            for line in gzip.open(attempt / "vectors.jsonl.gz", "rt"):
                case = json.loads(line)
                lines.append(" ".join(map(str, (case["id"], case["blocks"], case["packet_hex"],
                                                   case["dense_hex"], case["packed_hex"]))) + "\n")
            observed = sha("".join(lines).encode())
        else:
            raise AssertionError((attempt.name, "missing artifact", rel))
        assert observed == digest, (attempt.name, "artifact", rel)
    assert report["artifacts_sha256"].get("results.json") is None
    return {"attempt": attempt.name, "result_sha256": file_sha(path),
            "source_sha256": report["source_sha256"],
            "artifact_sha256": report["artifacts_sha256"],
            "commands": report["commands"]}


def selected_report(public_path: Path, attempts_dir: Path, schema: str, status: str,
                    key: str | None = None, value: int | None = None) -> tuple[dict, Path]:
    public = json.loads(public_path.read_text())
    selected_rel = public["selected_report"]
    path = ROOT / selected_rel
    assert path.parent.parent == attempts_dir
    report = json.loads(path.read_text())
    public_copy = dict(public)
    public_copy.pop("selected_report")
    assert public_copy == report, f"public {schema} report differs from selected attempt"
    assert report["schema"] == schema and report["status"] == status
    if key is not None:
        assert report[key] == value
    return report, path


def verify_scratch(vectors: dict, cases: dict[str, dict]) -> dict:
    report, path = selected_report(RTL / "scratch-results.json", RTL / "scratch-attempts",
                                   "cu66-v91d-scratch-rtl-v1", "PASS_SCRATCH_RTL_FINITE_MEMORY")
    receipt = check_receipt(report, path, "cu66-v91d-scratch-rtl-v1", "PASS_SCRATCH_RTL_FINITE_MEMORY")
    assert report["vectors"] == "experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz"
    assert report["vectors_sha256"] == vectors["fixture_sha256"]
    assert report["vector_index_sha256"] == file_sha(VECTORS / "index.json")
    assert report["vector_cases"] == vectors["packet_rows"]
    assert report["outputs_per_configuration"] == vectors["dense_coefficients"]
    assert report["status"] == "PASS_SCRATCH_RTL_FINITE_MEMORY"
    assert report["full_30fps_proven"] is False and report["complete_under10ms_proven"] is False
    rows = [json.loads(line) for line in (path.parent / "simulation.jsonl").read_text().splitlines()]
    case_rows = [r for r in rows if r["type"] == "case"]
    verdict_rows = [r for r in rows if r["type"] == "verdict"]
    assert len(case_rows) == len(cases) * 4 and len(verdict_rows) == 1
    verdict = verdict_rows[0]
    assert verdict == report["verdict"]
    assert verdict["status"] == "TEST_PASS" and verdict["cases"] == len(cases)
    assert verdict["configurations"] == 4 and verdict["directed"] == 26
    assert sum(verdict[k] for k in ("mask_ready_cycles", "serial_ready_cycles")) <= verdict["cycles"]
    configs = {(stall, serial) for stall in (0, 1) for serial in (0, 1)}
    observed = {(r["id"], r["stalls"], r["serial_clear"]) for r in case_rows}
    assert observed == {(case_id, stall, serial) for case_id in cases for stall, serial in configs}
    for row in case_rows:
        golden = cases[row["id"]]
        assert row["outputs"] == golden["outputs"]
        assert row["write_bursts"] == row["read_bursts"] == golden["used_bytes"] // 16
    assert sum(r["cycles"] for r in case_rows) == verdict["cycles"]
    assert sum(r["cycles"] for r in case_rows if not r["serial_clear"] and not r["stalls"]) == verdict["mask_ready_cycles"]
    assert sum(r["cycles"] for r in case_rows if r["serial_clear"] and not r["stalls"]) == verdict["serial_ready_cycles"]
    assert sum(r["write_bursts"] for r in case_rows) == sum(r["read_bursts"] for r in case_rows)
    return {"receipt": receipt, "cases": len(case_rows), "configurations": 4,
            "directed_checks": verdict["directed"], "dense_coefficients_per_configuration": vectors["dense_coefficients"],
            "aggregate_cycles": verdict["cycles"], "mask_ready_cycles": verdict["mask_ready_cycles"],
            "serial_ready_cycles": verdict["serial_ready_cycles"],
            "request_stall_cycles": verdict["request_stall_cycles"],
            "ack_wait_cycles": verdict["ack_wait_cycles"],
            "output_stall_cycles": verdict["output_stall_cycles"]}


def verify_pipeline_seed(seed: int, vectors: dict, cases: dict[str, dict],
                        expected_sources: dict[str, str] | None = None) -> tuple[dict, Path]:
    candidates = []
    for result_path in (RTL / "pipeline-attempts").glob("*/results.json"):
        result = json.loads(result_path.read_text())
        if result.get("seed") == seed and result.get("status") == "PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE":
            candidates.append((result_path, result))
    assert candidates, f"missing passing integrated receipt for seed {seed}"
    path, report = sorted(candidates, key=lambda pair: pair[0].parent.name)[-1]
    receipt = check_receipt(report, path, "cu66-v91d-integrated-pipeline-v1",
                            "PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE", expected_sources)
    assert report["seed"] == seed
    assert report["vectors_sha256"] == vectors["fixture_sha256"]
    assert report["vector_index_sha256"] == file_sha(VECTORS / "index.json")
    assert report["vector_packets"] == vectors["packet_rows"]
    assert report["verdict"]["status"] == "TEST_PASS"
    assert report["verdict"]["seed"] == seed
    assert report["verdict"]["packets"] == len(cases)
    assert report["verdict"]["configurations"] == 4
    assert report["verdict"]["case_rows"] == len(cases) * 4
    assert report["verdict"]["dense_comparisons"] == vectors["dense_coefficients"] * 4
    assert report["verdict"]["directed_checks"] == 11
    assert report["verdict"]["minimum_memory_response_delay"] >= 1
    assert report["verdict"]["maximum_memory_response_delay"] <= 501
    assert report["memory_model"].startswith("One outstanding 16B transaction")
    assert "physical SDRAM" in report["scope"] and "combinational multiport" in report["scope"]
    tb = (ROOT / "fpga/experiments/cu66-v91d/tb_pipeline.cpp").read_text()
    assert "const std::array<unsigned,4> bits{8192,81920,50000,0};" in tb
    assert "const std::array<unsigned,3> counts{40960,25000,0};" in tb
    assert 'failure=run(oversized_scratch(),false,true,0x21,false);' in tb
    assert 'require(failure.writes==0&&failure.reads==0,"over-budget packet wrote memory before admission")' in tb
    rows = [json.loads(line) for line in (path.parent / "simulation.jsonl").read_text().splitlines()]
    case_rows = [r for r in rows if r["type"] == "case"]
    verdict_rows = [r for r in rows if r["type"] == "verdict"]
    assert len(case_rows) == len(cases) * 4 and len(verdict_rows) == 1
    assert verdict_rows[0] == report["verdict"]
    config_set = {(serial, profile) for serial in (0, 1) for profile in (0, 1)}
    assert {(r["id"], r["serial_clear"], r["memory_profile"]) for r in case_rows} == {
        (case_id, serial, profile) for case_id in cases for serial, profile in config_set}
    for row in case_rows:
        golden = cases[row["id"]]
        assert row["used_bytes"] == golden["used_bytes"]
        assert row["dense_coefficients"] == golden["outputs"]
        assert row["input_bytes"] == golden["packet_bytes"]
        assert row["read_requests"] == row["write_requests"] == golden["used_bytes"] // 16
        assert row["read_requests"] + row["write_requests"] == 2 * (golden["used_bytes"] // 16)
    for case_id, golden in cases.items():
        mask = next(r for r in case_rows if r["id"] == case_id and
                    r["memory_profile"] == 0 and not r["serial_clear"])
        serial = next(r for r in case_rows if r["id"] == case_id and
                      r["memory_profile"] == 0 and r["serial_clear"])
        expected_clear_cycles = 0 if golden["raw"] else 63 * golden["blocks"]
        assert serial["cycles"] - mask["cycles"] == expected_clear_cycles, (seed, case_id)
    metric_fields = ("cycles", "input_bytes", "dense_coefficients", "read_requests",
                     "write_requests", "output_stalls", "metadata_wait", "memory_pending_edges")
    expected_totals = {}
    for population in ("actual", "other"):
        members = [r for r in case_rows if (r["id"].startswith("actual:") == (population == "actual"))]
        for profile in (0, 1):
            for serial in (0, 1):
                subset = [r for r in members if r["memory_profile"] == profile and r["serial_clear"] == serial]
                expected_totals[(population, profile, serial)] = {
                    "packets": len(subset), **{field: sum(r[field] for r in subset) for field in metric_fields}}
    observed_totals = {(r["population"], r["memory_profile"], r["serial_clear"]): r for r in report["totals"]}
    assert observed_totals.keys() == expected_totals.keys()
    for key, expected in expected_totals.items():
        assert all(observed_totals[key][field] == value for field, value in expected.items()), key
    expected_comparisons = []
    for population in ("actual", "other"):
        for profile in (0, 1):
            mask = expected_totals[(population, profile, 0)]["cycles"]
            serial = expected_totals[(population, profile, 1)]["cycles"]
            expected_comparisons.append((population, profile, mask, serial))
    observed_comparisons = {(r["population"], r["memory_profile"]): r for r in report["comparisons"]}
    assert len(observed_comparisons) == 4
    for population, profile, mask, serial in expected_comparisons:
        row = observed_comparisons[(population, profile)]
        assert row["mask_cycles"] == mask and row["serial_cycles"] == serial
        assert math.isclose(row["serial_over_mask"], serial / mask, rel_tol=1e-12)
        assert math.isclose(row["cycle_reduction_percent"], 100 * (serial - mask) / serial, rel_tol=1e-12)
    assert sum(r["cycles"] for r in case_rows) == sum(r["cycles"] for r in report["totals"])
    return {"receipt": receipt, "seed": seed, "case_rows": len(case_rows),
            "directed_checks": report["verdict"]["directed_checks"],
            "dense_comparisons": report["verdict"]["dense_comparisons"],
            "maximum_memory_response_delay": report["verdict"]["maximum_memory_response_delay"],
            "totals": report["totals"], "comparisons": report["comparisons"]}, path


def verify_expected_regression_failure() -> dict:
    """Bind the retained pre-fix reproduction of the replacement-start race."""
    path = RTL / "pipeline-attempts/20261106T175724427619Z-afe10872/results.json"
    report = json.loads(path.read_text())
    assert report["schema"] == "cu66-v91d-integrated-pipeline-v1"
    assert report["status"] == "FAIL" and report["seed"] == 910432
    assert report["error_class"] == "RuntimeError" and "Command exit 1" in report["error"]
    attempt = path.parent
    old_pipeline_source = "fpga/experiments/cu66-v91d/br88_pipeline.sv"
    assert old_pipeline_source in report["source_sha256"]
    assert report["source_sha256"][old_pipeline_source] != file_sha(RTL / "br88_pipeline.sv")
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest or rel in {
            old_pipeline_source, "fpga/experiments/cu66-v91d/tb_pipeline.cpp"}, rel
        assert file_sha(attempt / "sources" / rel) == digest, rel
    for rel, digest in report["artifacts_sha256"].items():
        candidate = attempt / rel
        if candidate.is_file():
            observed = file_sha(candidate)
        elif rel == "vectors.txt" and (attempt / "vectors.jsonl.gz").is_file():
            lines = []
            for line in gzip.open(attempt / "vectors.jsonl.gz", "rt"):
                case = json.loads(line)
                lines.append(" ".join(map(str, (case["id"], case["blocks"], case["packet_hex"],
                                                   case["dense_hex"], case["packed_hex"]))) + "\n")
            observed = sha("".join(lines).encode())
        else:
            raise AssertionError(("expected regression missing artifact", rel))
        assert observed == digest, ("expected regression artifact", rel)
    commands = report["commands"]
    assert len(commands) == 4 and [c["exit_code"] for c in commands] == [0, 0, 0, 1]
    output = (attempt / "simulation.jsonl").read_text().strip()
    assert output == "TEST_FAIL replacement start lost after write ACK error"
    return {"attempt": attempt.name, "expected_pre_fix_failure": "replacement start lost after write ACK error",
            "result_sha256": file_sha(path), "source_sha256": report["source_sha256"],
            "artifact_sha256": report["artifacts_sha256"],
            "command_exit_codes": [c["exit_code"] for c in commands],
            "simulation_sha256": report["artifacts_sha256"]["simulation.jsonl"]}


def main() -> None:
    vectors, cases = verify_vectors()
    scratch = verify_scratch(vectors, cases)
    integrated = []
    shared_sources = None
    for seed in PIPELINE_SEEDS:
        result, path = verify_pipeline_seed(seed, vectors, cases, shared_sources)
        if shared_sources is None:
            shared_sources = result["receipt"]["source_sha256"]
        integrated.append(result)
    public, public_path = selected_report(RTL / "pipeline-results.json", RTL / "pipeline-attempts",
                                          "cu66-v91d-integrated-pipeline-v1",
                                          "PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE")
    assert public["seed"] in PIPELINE_SEEDS
    assert any((RTL / "pipeline-attempts" / result["receipt"]["attempt"] / "results.json") == public_path
               for result in integrated)
    audit = {
        "schema": "cu66-v91d-independent-evidence-audit-v1",
        "status": "PASS_VECTORS_PACKED_IMAGES_AND_FINITE_MEMORY_RTL",
        "scope": "Independent V88 frozen-packet decode, sparse/dense/packed-image reconstruction, and selected standalone/integrated finite-memory RTL receipt accounting. No hardware, synthesis, physical SDRAM calibration, BRAM fit, pixel reconstruction, display, full-frame 30 fps or under-10-ms proof.",
        "parent_commit": BASE,
        "vectors": vectors,
        "standalone_rtl": scratch,
        "integrated_rtl": {"selected_seeds": integrated,
                            "identical_source_pins": True,
                            "public_selected_seed": public["seed"],
                            "retained_pre_fix_regression": verify_expected_regression_failure()},
    }
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V91D_INDEPENDENT_AUDIT_PASS")


if __name__ == "__main__":
    main()
