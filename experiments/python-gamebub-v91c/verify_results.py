#!/usr/bin/env python3
"""Independent evidence audit for V91c packet vectors and packet RTL receipts."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import math
import random
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91c"
VECTORS = AREA / "packet-vectors"
RTL = ROOT / "fpga/experiments/cu66-v91c"
SEEDS = (910232, 910233)
EXPECTED_SELECTED = ((0, 0), (0, 1), (0, 3), (3, 50))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def packed_hash(values: list[int]) -> str:
    return sha(struct.pack("<" + "h" * len(values), *values))


def tuple_outputs(coeffs: list[int], blocks: int, raw: bool) -> list[list[int]]:
    if raw:
        return [[b, i, coeffs[b * 64 + i]] for b in range(blocks) for i in range(64)]
    order = sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                              i // 8 if (i // 8 + i % 8) % 2 else -(i // 8)))
    limits = (1, 6, 21, 64)
    out = [[b, 0, coeffs[b * 64]] for b in range(blocks)]
    for lo, hi in zip(limits, limits[1:]):
        for b in range(blocks):
            for slot in range(lo, hi):
                i = order[slot]
                value = coeffs[b * 64 + i]
                if value:
                    out.append([b, i, value])
    return out


def verify_vectors() -> dict:
    index_path = VECTORS / "index.json"
    index = json.loads(index_path.read_text())
    assert index["schema"] == "cu66-v91c-br88-fullpacket-vectors-v1"
    assert tuple(map(tuple, index["selection"])) == EXPECTED_SELECTED
    assert index["actual_chunks"] == 12 and index["synthetic_packets"] == 4 and index["packets"] == 16
    fixture = VECTORS / index["fixture"]["path"]
    compressed = fixture.read_bytes()
    raw = gzip.decompress(compressed)
    assert sha(compressed) == index["fixture"]["gzip_sha256"]
    assert sha(raw) == index["fixture"]["jsonl_sha256"]

    for rel, expected in index["source_sha256"].items():
        assert file_sha(ROOT / rel) == expected, f"source pin mismatch: {rel}"
    source_info = index["source_data"]
    data_path = ROOT / "experiments/python-gamebub-v88/entropy" / source_info["path"]
    assert file_sha(data_path) == source_info["gzip_sha256"]

    codec_path = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
    data_path_py = ROOT / "experiments/python-gamebub-v88/entropy/data.py"
    codec = load_module("v91c_audit_frozen_codec", codec_path)
    data = load_module("v91c_audit_frozen_data", data_path_py)
    actual = {}
    selected_seen = set()
    for frame in data.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        if identity not in EXPECTED_SELECTED:
            continue
        selected_seen.add(identity)
        for p, plane in enumerate(frame["variants"]["65536"]):
            for t, chunk in enumerate(plane):
                key = f"actual:c{identity[0]}:f{identity[1]}:p{p}:t{t}"
                coeffs = codec.decode(chunk["br88"], chunk["blocks"], 1)
                assert packed_hash(coeffs) == chunk["coefficient_sha256"]
                assert sha(chunk["br88"]) == chunk["br88_sha256"]
                actual[key] = (chunk["br88"], chunk["blocks"], coeffs,
                               {"cohort": identity[0], "fid": identity[1], "plane": p,
                                "chunk": t, "packet_sha256": chunk["br88_sha256"],
                                "coefficient_sha256": chunk["coefficient_sha256"]})
    assert selected_seen == set(EXPECTED_SELECTED) and len(actual) == 12

    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 16
    seen_ids = set()
    tuple_count = 0
    actual_count = raw_count = 0
    for row in rows:
        case_id = row["id"]
        assert case_id not in seen_ids
        seen_ids.add(case_id)
        packet = bytes.fromhex(row["packet_hex"])
        blocks = row["blocks"]
        assert sha(packet) == row["packet_sha256"]
        assert row["expected_error"] == 0
        coeffs = codec.decode(packet, blocks, 1)
        assert packed_hash(coeffs) == row["coefficient_sha256"] == row["canonical_dense_sha256"]
        raw_mode = bool(packet[5] & 1)
        expected = tuple_outputs(coeffs, blocks, raw_mode)
        assert row["expected"] == expected, case_id
        tuple_count += len(expected)
        if row["case_type"] == "actual":
            actual_count += 1
            assert case_id in actual
            src_packet, src_blocks, src_coeffs, source = actual[case_id]
            assert (packet, blocks, coeffs, row["source"]) == (src_packet, src_blocks, src_coeffs, source)
        elif raw_mode:
            raw_count += 1
    assert set(actual) == {row["id"] for row in rows if row["case_type"] == "actual"}
    assert actual_count == 12 and raw_count == 2 and tuple_count == 84389
    case_output_counts = {row["id"]: len(row["expected"]) for row in rows}
    return {"packet_rows": len(rows), "actual_chunks": actual_count,
            "synthetic_packets": len(rows) - actual_count, "tuple_count": tuple_count,
            "raw_packets": raw_count, "fixture_sha256": sha(compressed),
            "jsonl_sha256": sha(raw), "frozen_oracle": "V88 codec.decode",
            "case_output_counts": case_output_counts,
            "source_pins": index["source_sha256"],
            "source_data_gzip_sha256": source_info["gzip_sha256"]}


def verify_rtl(vectors: dict) -> dict:
    receipts = []
    selected_hashes = None
    public = json.loads((RTL / "results.json").read_text())
    public_selected = public.pop("selected_report")
    for seed in SEEDS:
        candidates = []
        for result_path in (RTL / "attempts").glob("*/results.json"):
            result = json.loads(result_path.read_text())
            if result.get("seed") == seed and result.get("status") == "PASS_PACKET_SIMULATION":
                candidates.append((result_path, result))
        assert candidates, f"missing passing receipt for seed {seed}"
        result_path, result = sorted(candidates, key=lambda item: item[0].parent.name)[-1]
        attempt = result_path.parent
        if seed == public["seed"]:
            assert public_selected == str(result_path.relative_to(ROOT))
            assert public == result, "public RTL result must bind the entire selected attempt receipt"
        assert result["verdict"]["status"] == "TEST_PASS"
        assert result["verdict"]["seed"] == seed
        assert result["vector_cases"] == 16 and result["actual_packets"] == 12
        assert result["verdict"]["outputs_per_configuration"] == vectors["tuple_count"]
        assert result["verdict"]["configurations"] == 8
        assert result["verdict"]["directed_checks"] == 200
        assert result["vectors_sha256"] == vectors["fixture_sha256"]
        for rel, expected in result["source_sha256"].items():
            assert file_sha(ROOT / rel) == expected, f"RTL source pin mismatch: {rel}"
        for rel, expected in result["artifacts_sha256"].items():
            assert file_sha(attempt / rel) == expected, f"RTL artifact pin mismatch: {rel}"
        for command in result["commands"]:
            assert command["exit_code"] == 0, (seed, command)
        compile_command = next(" ".join(command["argv"]) for command in result["commands"]
                               if command["log"] == "compile.log")
        assert "--assert" in compile_command and "-Wall" in compile_command and "-Werror" in compile_command
        compile_log = (attempt / "compile.log").read_text()
        assert not __import__("re").search(r"%Warning|\bwarning:", compile_log, __import__("re").IGNORECASE)
        sim = [json.loads(line) for line in (attempt / "simulation.jsonl").read_text().splitlines()]
        case_rows = [r for r in sim if r.get("type") == "case"]
        total_rows = [r for r in sim if r.get("type") == "total"]
        verdict_rows = [r for r in sim if r.get("type") == "verdict"]
        assert len(case_rows) == 16 * 8
        configs = {(serial, width, stalls) for serial in (0, 1) for width in (16, 32) for stalls in (0, 1)}
        expected_cases = {(case_id, serial, width, stalls)
                          for case_id in vectors["case_output_counts"]
                          for serial, width, stalls in configs}
        observed_cases = {(r["id"], r["serial"], r["word_bits"], r["stalls"]) for r in case_rows}
        assert observed_cases == expected_cases
        assert all(r["outputs"] == vectors["case_output_counts"][r["id"]] for r in case_rows)
        assert len(total_rows) == 8 and len(verdict_rows) == 1
        assert verdict_rows[0] == result["verdict"]
        assert len({(r["serial"], r["word_bits"], r["stalls"]) for r in total_rows}) == 8
        for total in total_rows:
            rows = [r for r in case_rows if (r["serial"], r["word_bits"], r["stalls"]) ==
                    (total["serial"], total["word_bits"], total["stalls"])]
            for field in ("cycles", "input_accepted", "outputs", "output_stall"):
                assert total[field] == sum(r[field] for r in rows), (seed, field)
        # Reconstruct aggregate and selected-source populations from case rows.
        populations = {"actual": [r for r in case_rows if r["id"].startswith("actual:")],
                       "synthetic": [r for r in case_rows if r["id"].startswith("synthetic:")]
                       }
        for r in case_rows:
            if r["id"].startswith("actual:"):
                population = r["id"].split(":p", 1)[0]
                populations.setdefault(population, []).append(r)
        pop_expected = {}
        for population, members in populations.items():
            for serial, width, stalls in configs:
                subset = [r for r in members if (r["serial"], r["word_bits"], r["stalls"]) == (serial, width, stalls)]
                if not subset:
                    continue
                pop_expected[(population, width, serial, stalls)] = {
                    "streams": len(subset), "cycles": sum(r["cycles"] for r in subset),
                    "input_accepted": sum(r["input_accepted"] for r in subset),
                    "outputs": sum(r["outputs"] for r in subset),
                    "output_stall": sum(r["output_stall"] for r in subset)}
        pop_report = {(r["population"], r["word_bits"], r["serial"], r["stalls"]): r
                      for r in result["population_totals"]}
        assert pop_report.keys() == pop_expected.keys()
        for key, expected in pop_expected.items():
            assert all(pop_report[key][field] == val for field, val in expected.items()), key
        comp_expected = {}
        for population in populations:
            for width in (16, 32):
                for stalls in (0, 1):
                    fast = pop_expected.get((population, width, 0, stalls))
                    serial_total = pop_expected.get((population, width, 1, stalls))
                    if fast and serial_total:
                        comp_expected[(population, width, stalls)] = (fast["cycles"], serial_total["cycles"])
        comp_report = {(r["population"], r["word_bits"], r["stalls"]): r
                       for r in result["population_comparisons"]}
        assert comp_report.keys() == comp_expected.keys()
        for key, (fast_cycles, serial_cycles) in comp_expected.items():
            report = comp_report[key]
            assert report["fast_cycles"] == fast_cycles and report["serial_cycles"] == serial_cycles
            assert math.isclose(report["serial_over_fast"], serial_cycles / fast_cycles, rel_tol=1e-12)
        # The result receipt must pin the exact source revision used by this attempt.
        pinset = result["source_sha256"]
        assert pinset["fpga/experiments/cu66-v91c/br88_packet.sv"] == file_sha(RTL / "br88_packet.sv")
        assert pinset["fpga/experiments/cu66-v91c/tb_packet.cpp"] == file_sha(RTL / "tb_packet.cpp")
        assert pinset["scripts/cu66-v91c/run_rtl.py"] == file_sha(ROOT / "scripts/cu66-v91c/run_rtl.py")
        if selected_hashes is None:
            selected_hashes = pinset
        else:
            assert pinset == selected_hashes, "seed receipts use different RTL inputs"
        for rel, expected in result["artifacts_sha256"].items():
            p = attempt / rel
            if rel.startswith("sources/"):
                assert file_sha(p) == expected, (seed, rel)
        receipts.append({"seed": seed, "attempt": attempt.name,
                         "cases": len(case_rows), "configurations": result["verdict"]["configurations"],
                         "tuples_per_configuration": result["verdict"]["outputs_per_configuration"],
                         "directed_checks": result["verdict"]["directed_checks"],
                         "result_sha256": file_sha(result_path),
                         "source_sha256": pinset,
                         "artifact_sha256": result["artifacts_sha256"]})
    return {"seed_receipts": receipts, "identical_source_pins": True}


def align16(n: int) -> int:
    return (n + 15) // 16 * 16


def packed_image(coeffs: list[int], blocks: int, raw: bool, counts: tuple[int, int, int]) -> bytes:
    """Rebuild the selected fixed-layout image without importing scratch.py."""
    header = struct.pack("<8I", 0x43393150, blocks, int(raw), *counts,
                         32 + (align16(blocks * 128) if raw else
                               sum(align16(n) for n in (blocks * 2, *(4 * c for c in counts)))), 0)
    order = sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                              i // 8 if (i // 8 + i % 8) % 2 else -(i // 8)))
    limits = (1, 6, 21, 64)
    segments: list[bytes] = []
    if raw:
        segments.append(struct.pack("<" + "h" * len(coeffs), *coeffs))
    else:
        segments.append(struct.pack("<" + "h" * blocks, *(coeffs[b * 64] for b in range(blocks))))
        for band, (lo, hi) in enumerate(zip(limits, limits[1:])):
            width = hi - lo
            records = []
            for block in range(blocks):
                for scan_pos in range(lo, hi):
                    raster = order[scan_pos]
                    value = coeffs[block * 64 + raster]
                    if value:
                        linear = block * width + scan_pos - lo
                        records.append(struct.pack("<I", (block << 19) | (raster << 13) | (value & 0x1fff)))
            segments.append(b"".join(records))
    image = bytearray(header)
    for segment in segments:
        image.extend(segment)
        image.extend(bytes(align16(len(segment)) - len(segment)))
    return bytes(image)


def verify_scratch() -> dict:
    summary_path = AREA / "scratch-results.json"
    summary = json.loads(summary_path.read_text())
    assert summary["schema"] == "cu66-v91c-packed-scratch-v1"
    assert summary["status"] == "PASS_FULL_CORPUS_PACKED_SCRATCH"
    assert summary["scratch_RTL_implemented"] is False
    assert summary["full_30fps_proven"] is False and summary["complete_under10ms_proven"] is False
    assert summary["assumptions"] == {
        "capacity_bytes": 262144, "max_blocks": 8192, "header_bytes": 32,
        "burst_bytes": 16, "read_cycles_per_burst": 18, "write_cycles_per_burst": 16,
        "schedule": "Per event: Random(910300 + transaction epoch).randrange(5) held samples; not FPGA cycles."}
    attempt_rel = Path(summary["selected_report"])
    attempt_path = ROOT / attempt_rel
    result = json.loads(attempt_path.read_text())
    public_result = dict(summary)
    assert public_result.pop("selected_report") == str(attempt_rel)
    assert public_result == result, "public scratch summary must bind the full selected attempt receipt"
    assert result["status"] == "PASS_FULL_CORPUS_PACKED_SCRATCH"
    attempt = attempt_path.parent
    assert summary["artifacts_sha256"] == result["artifacts_sha256"]
    for rel, expected in result["source_sha256"].items():
        assert file_sha(ROOT / rel) == expected, f"scratch source pin mismatch: {rel}"
    for rel, expected in result["artifacts_sha256"].items():
        path = attempt / rel
        assert file_sha(path) == expected, f"scratch artifact hash mismatch: {rel}"
        if rel.startswith("sources/"):
            source_rel = rel[len("sources/"):]
            assert file_sha(ROOT / source_rel) == expected, f"snapshot differs: {source_rel}"

    # Rebuild the source identity/order and coefficient/event facts from frozen V88 data.
    entropy = ROOT / "experiments/python-gamebub-v88/entropy"
    codec = load_module("v91c_scratch_audit_codec", entropy / "codec.py")
    data = load_module("v91c_scratch_audit_data", entropy / "data.py")
    context = load_module("v91c_scratch_audit_context", ROOT / "experiments/python-gamebub-v91b/context.py")
    rows = [json.loads(line) for line in (attempt / "chunks.jsonl").read_text().splitlines()]
    assert len(rows) == 1371
    row_at = 0
    source_ids = set()
    totals = {key: 0 for key in (
        "coefficient_values", "used_bytes", "padding_bytes", "dense_reservation_bytes",
        "ideal_dense_clear_scatter_read_bytes", "ideal_bitmap_external_value_bytes",
        "bitmap_clear_bytes", "packed_bus_bytes", "hypothetical_memory_busy_cycles")}
    totals.update(sources=0, chunks=0, sparse_writes=0, held_samples=0, write_bursts=0, read_bursts=0)
    budget_counts = {budget: [0, 0] for budget in (65536, 131072, 262144, 524288)}
    max_values = {}
    max_rows = {}
    epoch = 0
    for frame in data.iter_frames():
        identity = (frame["cohort"], frame["fid"])
        assert identity not in source_ids
        source_ids.add(identity)
        for plane_no, plane in enumerate(frame["variants"]["65536"]):
            for chunk_no, chunk in enumerate(plane):
                row = rows[row_at]
                row_at += 1
                blocks = chunk["blocks"]
                assert 1 <= blocks <= 8192
                packet = chunk["br88"]
                assert row["packet_sha256"] == chunk["br88_sha256"] == sha(packet)
                assert (row["cohort"], row["fid"], row["ordinal"], row["plane"], row["chunk"]) == (
                    identity[0], identity[1], frame["ordinal"], plane_no, chunk_no)
                coeffs = codec.decode(packet, blocks, 1)
                assert packed_hash(coeffs) == row["coefficient_sha256"] == chunk["coefficient_sha256"]
                contexts, raw_values = context.parse_chunk(packet, blocks)
                raw_mode = raw_values is not None
                counts = (0, 0, 0) if raw_mode else tuple(c.event_count for c in contexts[1:])
                assert bool(row["raw"]) == raw_mode and row["ac_counts"] == list(counts)
                writes = blocks * 64 if raw_mode else blocks + sum(counts)
                sizes = [blocks * 128] if raw_mode else [blocks * 2, *(n * 4 for n in counts)]
                used_bytes = 32 + sum(align16(size) for size in sizes)
                padding_bytes = sum(align16(size) - size for size in sizes)
                dense_bytes = blocks * 128
                bursts = used_bytes // 16
                derived = {
                    "blocks": blocks, "used_bytes": used_bytes, "padding_bytes": padding_bytes,
                    "dense_reservation_bytes": dense_bytes, "coefficient_values": blocks * 64,
                    "ideal_dense_clear_scatter_read_bytes": 256 * blocks + 2 * writes,
                    "ideal_bitmap_external_value_bytes": 4 * writes,
                    "bitmap_clear_bytes": 8 * blocks, "packed_bus_bytes": 32 * bursts,
                    "hypothetical_memory_busy_cycles": 34 * bursts,
                }
                for key, val in derived.items():
                    assert row[key] == val, (row["cohort"], row["fid"], row["plane"], row["chunk"], key)
                image = packed_image(coeffs, blocks, raw_mode, counts)
                assert len(image) == used_bytes and row["scratch_sha256"] == sha(image)
                st = row["stats"]
                assert st["accepted"] == writes
                assert st["write_bursts"] == st["read_bursts"] == bursts
                assert st["pending_high_water"] == 1
                assert st["write_assembler_high_water"] <= 16 and st["read_cache_high_water"] <= 4
                assert st["tile_coefficients"] == 64 and st["ac_lookahead_records"] == 3
                epoch += 1
                rng = random.Random(910300 + epoch)
                expected_holds = sum(rng.randrange(5) for _ in range(writes))
                assert st["held_samples"] == expected_holds
                for key in totals:
                    if key in row:
                        totals[key] += row[key]
                totals["sparse_writes"] += writes
                totals["held_samples"] += expected_holds
                totals["write_bursts"] += bursts
                totals["read_bursts"] += bursts
                for budget in budget_counts:
                    budget_counts[budget][0] += used_bytes <= budget
                    budget_counts[budget][1] += dense_bytes <= budget
                for key in ("used_bytes", "dense_reservation_bytes", "hypothetical_memory_busy_cycles"):
                    if key not in max_values or row[key] > max_values[key]:
                        max_values[key] = row[key]
                        max_rows[key] = {field: row[field] for field in ("cohort", "fid", "plane", "chunk")}
                totals["chunks"] += 1
        totals["sources"] += 1
    assert row_at == len(rows) and len(source_ids) == 457
    assert summary["totals"] == result["totals"] == totals
    expected_budget = [dict(capacity_bytes=b, packed_fit=budget_counts[b][0], dense_fit=budget_counts[b][1])
                       for b in budget_counts]
    assert summary["budget_sweep"] == result["budget_sweep"] == expected_budget
    expected_max = {key: {"value": max_values[key], "identity": max_rows[key]} for key in max_values}
    assert summary["maxima"] == result["maxima"] == expected_max
    assert result["directed_checks"] == 11 and result["synthetic_cases"] == 4

    # Synthetic replacement/raw edge cases are checked against their oracle rows.
    vector_rows = {r["id"]: r for r in
                   (json.loads(line) for line in gzip.decompress((VECTORS / "packets.jsonl.gz").read_bytes()).decode().splitlines())}
    synthetic = json.loads((attempt / "synthetic.json").read_text())
    assert {r["id"] for r in synthetic} == {name for name in vector_rows if name.startswith("synthetic:")}
    synthetic_epoch = 1371
    for item in synthetic:
        source = vector_rows[item["id"]]
        packet = bytes.fromhex(source["packet_hex"])
        coeffs = codec.decode(packet, source["blocks"], 1)
        expected_hash = packed_hash(coeffs)
        raw_mode = bool(packet[5] & 1)
        counts = tuple(item["ready"]["ac_counts"])
        image_hash = sha(packed_image(coeffs, source["blocks"], raw_mode, counts))
        for mode in ("ready", "stalled"):
            synthetic_epoch += 1
            entry = item[mode]
            assert entry["coefficient_sha256"] == expected_hash == source["coefficient_sha256"]
            assert entry["scratch_sha256"] == image_hash
            assert entry["coefficient_values"] == source["blocks"] * 64
            assert entry["used_bytes"] == (32 + sum(align16(n) for n in
                   ([source["blocks"] * 128] if packet[5] else
                    [source["blocks"] * 2, *(4 * n for n in entry["ac_counts"])])))
            if mode == "ready":
                assert entry["stats"]["held_samples"] == 0
            else:
                count = entry["stats"]["accepted"]
                rng = random.Random(910300 + synthetic_epoch)
                assert entry["stats"]["held_samples"] == sum(rng.randrange(5) for _ in range(count))
    return {"sources": 457, "chunks": len(rows), "coefficient_values": totals["coefficient_values"],
            "sparse_writes": totals["sparse_writes"], "held_samples": totals["held_samples"],
            "used_bytes": totals["used_bytes"], "padding_bytes": totals["padding_bytes"],
            "budget_sweep": expected_budget, "maximum_used_bytes": max_values["used_bytes"],
            "selected_attempt": attempt.name, "selected_result_sha256": file_sha(attempt_path),
            "source_sha256": result["source_sha256"],
            "artifact_sha256": result["artifacts_sha256"],
            "source_and_artifact_pins": "PASS"}


def main() -> None:
    vectors = verify_vectors()
    rtl = verify_rtl(vectors)
    scratch = verify_scratch()
    audit = {
        "schema": "cu66-v91c-independent-evidence-audit-v1",
        "status": "PASS_VECTORS_RTL_AND_PACKED_SCRATCH",
        "checks": {"vectors": vectors, "rtl": rtl, "scratch": scratch},
        "scope": "Independent frozen-packet reconstruction, RTL receipt accounting, and packed-scratch corpus/cost re-derivation. No synthesis, physical memory fit, frame publication store, or end-to-end latency claim.",
    }
    out = AREA / "audit.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
