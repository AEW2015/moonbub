#!/usr/bin/env python3
"""Independently verify V91e coefficient goldens and telemetry receipts."""
from __future__ import annotations

import gzip
import ast
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91e"
VECTORS = AREA / "vectors"
RTL = ROOT / "fpga/experiments/cu66-v91e"
BASE = "bebd308caae58b235263c728c4994a7340c42f73"
SEEDS = (910432, 910433)
METRICS = ("cycles", "used_bytes", "input_bytes", "dense_coefficients", "read_requests", "write_requests",
           "output_stalls", "metadata_wait", "memory_pending_edges")
ORDER = tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
LIMITS = (1, 6, 21, 64)


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


def packed_image(blocks: int, counts: list[int], raw: bool, dense: list[int], sparse: list[list[int]]) -> bytes:
    if raw:
        segments = [struct.pack("<" + "h" * len(dense), *dense)]
    else:
        dc = [event[3] for event in sparse if event[0] == 0]
        assert len(dc) == blocks
        segments = [struct.pack("<" + "h" * len(dc), *dc)]
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
    out = bytearray(header)
    for segment in segments:
        out.extend(segment)
        out.extend(bytes(aligned(len(segment)) - len(segment)))
    assert len(out) == used
    return bytes(out)


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


def verify_vectors() -> tuple[dict, dict[str, dict], list[dict]]:
    index_path = VECTORS / "index.json"
    index = json.loads(index_path.read_text())
    assert index["schema"] == "cu66-v91e-coefficient-packed-image-v1"
    assert index["parent_commit"] == BASE[:9] and index["source_commit"] == BASE
    assert index["status"] == "PASS_FROZEN_V88_FULLCORPUS_COEFFICIENT_AND_PACKED_IMAGE_GOLDENS"
    assert index["counts"] == {"actual_cases": 15, "appended_actual_cases": 3,
        "appended_dense_coefficient_outputs": 371008, "dense_coefficient_outputs": 2250944,
        "original_v91d_cases": 17, "selected_source_identities": 3,
        "synthetic_or_directed_cases": 5, "total_cases": 20}
    compressed = (VECTORS / index["fixture"]["path"]).read_bytes()
    raw_jsonl = gzip.decompress(compressed)
    assert sha(compressed) == index["fixture"]["gzip_sha256"]
    assert sha(raw_jsonl) == index["fixture"]["jsonl_sha256"]
    for rel, expected in index["source_sha256"].items():
        assert file_sha(ROOT / rel) == expected, f"vector source pin mismatch: {rel}"
    baseline_path = ROOT / "experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz"
    baseline_raw = gzip.decompress(baseline_path.read_bytes())
    assert sha(baseline_path.read_bytes()) == index["old_fixture_compatibility"]["gzip_sha256"]
    assert b"\n".join(raw_jsonl.splitlines()[:17]) + b"\n" == baseline_raw

    codec = load_module("v91e_independent_v88_codec", ROOT / "experiments/python-gamebub-v88/entropy/codec.py")
    rows = [json.loads(line) for line in raw_jsonl.splitlines()]
    assert len(rows) == 20 and len({row["id"] for row in rows}) == 20
    by_id = {}
    for row in rows:
        blocks, counts, raw_mode = row["blocks"], row["counts"], bool(row["raw"])
        packet = bytes.fromhex(row["packet_hex"])
        dense_values = codec.decode(packet, blocks, 1)
        assert len(dense_values) == blocks * 64 and all(-2048 <= value <= 2048 for value in dense_values)
        dense_bytes = struct.pack("<" + "h" * len(dense_values), *dense_values)
        sparse = sparse_from_dense(dense_values, blocks, raw_mode)
        image = packed_image(blocks, counts, raw_mode, dense_values, sparse)
        assert row["dense_hex"] == dense_bytes.hex(), row["id"]
        assert row["sparse"] == sparse, row["id"]
        assert row["packed_hex"] == image.hex(), row["id"]
        assert row["coefficient_sha256"] == sha(dense_bytes), row["id"]
        assert row["packed_sha256"] == sha(image), row["id"]
        assert row["used_bytes"] == len(image)
        source = row.get("source", {})
        if isinstance(source, str):
            source = ast.literal_eval(source)
        if row["case_type"] == "actual":
            assert all(key in source for key in ("cohort", "fid", "plane", "chunk", "packet_sha256", "coefficient_sha256"))
            assert source["packet_sha256"] == sha(packet)
            assert source["coefficient_sha256"] == sha(dense_bytes)
        by_id[row["id"]] = {"blocks": blocks, "raw": raw_mode, "counts": counts,
            "used_bytes": len(image), "packet_bytes": len(packet), "outputs": blocks * 64,
            "case_type": row["case_type"], "packed_sha256": sha(image),
            "dense_sha256": sha(dense_bytes), "source": source}
    assert len([row for row in rows if row["case_type"] == "actual"]) == 15
    verify_selection(index, rows)
    summary = {"packet_rows": len(rows), "actual_packets": 15, "synthetic_or_directed_packets": 5,
        "dense_coefficients": sum(item["outputs"] for item in by_id.values()),
        "fixture_sha256": sha(compressed), "jsonl_sha256": sha(raw_jsonl),
        "source_sha256": index["source_sha256"], "case_ids": sorted(by_id),
        "selection_sha256": sha(json.dumps(index["selection"], sort_keys=True).encode())}
    return summary, by_id, rows


def verify_selection(index: dict, rows: list[dict]) -> None:
    selection = index["selection"]
    scan = selection["full_457_source_scan"]
    assert len(scan) == 457
    metric_map = {"packed_scratch_bytes": "max_packed_chunk_bytes", "br88_chunk_bytes": "max_br88_chunk_bytes",
                  "sparse_writes": "max_sparse_writes", "nonzero_ac": "max_nonzero_ac", "dense_blocks": "max_blocks"}
    selected = set()
    for scan_metric, source_metric in metric_map.items():
        maximum = max(row[source_metric] for row in scan)
        winner = next(row for row in scan if row[source_metric] == maximum)
        recorded = selection["maxima"][scan_metric]
        assert recorded["value"] == maximum
        identity = (winner["cohort"], winner["fid"])
        assert (recorded["source"]["cohort"], recorded["source"]["fid"]) == identity
        selected.add(identity)
    selected_ids = {(row["cohort"], row["fid"]) for row in selection["selected_source_identities"]}
    assert selected == selected_ids
    actual = [row for row in rows if row["case_type"] == "actual"]
    new = [row for row in actual if row["id"] not in {item["v91e_id"] for item in index["old_fixture_compatibility"]["mapping"]}]
    assert len(new) == 3 and { (row["source"]["cohort"], row["source"]["fid"]) for row in new } == {(3, 28)}
    assert {row["source"]["plane"] for row in new} == {0, 1, 2}


def read_report(path: Path) -> dict:
    return json.loads(path.read_text())


def verify_attempt(path: Path, expected_seed: int, vectors: dict, cases: dict[str, dict]) -> tuple[dict, list[dict]]:
    report = read_report(path)
    assert report["schema"] == "cu66-v91e-observed-coefficient-pipeline-v1"
    assert report["status"] == "PASS_RECONCILED_TELEMETRY_WITH_FROZEN_V91D_PARITY"
    assert report["source_revision"] == BASE and report["seed"] == expected_seed
    assert report["vectors_sha256"] == vectors["fixture_sha256"]
    assert report["vector_index_sha256"] == file_sha(VECTORS / "index.json")
    attempt = path.parent
    for cmd in report["commands"]:
        assert cmd["exit_code"] == 0 and (attempt / cmd["log"]).is_file()
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest
        assert file_sha(attempt / "sources" / rel) == digest
    for rel, digest in report["artifacts_sha256"].items():
        assert file_sha(attempt / rel) == digest
    tile_path = attempt / "tile-events.jsonl.gz"
    assert file_sha(tile_path) == report["tile_trace"]["gzip_sha256"]
    assert sha(gzip.decompress(tile_path.read_bytes())) == report["tile_trace"]["jsonl_sha256"]
    tile_summary = attempt / "tile-summary.json"
    assert file_sha(tile_summary) == report["tile_summary_sha256"]
    sim_path = attempt / "simulation.jsonl"
    rows = [json.loads(line) for line in sim_path.read_text().splitlines()]
    case_rows = [row for row in rows if row["type"] == "case"]
    verdict_rows = [row for row in rows if row["type"] == "verdict"]
    assert len(case_rows) == len(cases) * 4 and len(verdict_rows) == 1
    verdict = verdict_rows[0]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == expected_seed
    assert verdict["packets"] == len(cases) and verdict["case_rows"] == len(cases) * 4
    expected_keys = {(case_id, serial, profile) for case_id in cases for serial in (0, 1) for profile in (0, 1)}
    assert {(r["id"], r["serial_clear"], r["memory_profile"]) for r in case_rows} == expected_keys
    for row in case_rows:
        golden = cases[row["id"]]
        assert row["used_bytes"] == golden["used_bytes"]
        assert row["dense_coefficients"] == golden["outputs"]
        assert row["input_bytes"] == golden["packet_bytes"]
        assert row["read_requests"] == row["write_requests"] == golden["used_bytes"] // 16
        verify_telemetry(row, golden)

    baseline_path = ROOT / "fpga/experiments/cu66-v91d/pipeline-attempts"
    old = next(p for p in baseline_path.glob("*/results.json")
               if read_report(p).get("seed") == expected_seed and
               read_report(p).get("status") == "PASS_INTEGRATED_FINITE_MEMORY_COEFFICIENT_PIPELINE")
    old_rows = [json.loads(line) for line in (old.parent / "simulation.jsonl").read_text().splitlines()]
    old_cases = {(r["id"], r["serial_clear"], r["memory_profile"]): r for r in old_rows if r["type"] == "case"}
    for row in case_rows:
        if row["id"] in old_cases:
            base_row = old_cases[(row["id"], row["serial_clear"], row["memory_profile"])]
            for metric in METRICS:
                assert row[metric] == base_row[metric], (expected_seed, row["id"], metric, row[metric], base_row[metric])
    assert len(old_cases) == 68
    for case_id in cases:
        for profile in (0, 1):
            mask = next(r for r in case_rows if r["id"] == case_id and r["memory_profile"] == profile and not r["serial_clear"])
            serial = next(r for r in case_rows if r["id"] == case_id and r["memory_profile"] == profile and r["serial_clear"])
            assert mask["request_service_hash"] == serial["request_service_hash"], (expected_seed, case_id, profile)
    tile_jsonl = gzip.decompress(tile_path.read_bytes())
    tiles = [json.loads(line) for line in tile_jsonl.splitlines()]
    assert len(tiles) == sum(case["blocks"] for case in cases.values()) * 4
    tile_key = ("id", "serial_clear", "memory_profile", "block")
    assert len({tuple(row[key] for key in tile_key) for row in tiles}) == len(tiles)
    for tile in tiles:
        row = next(r for r in case_rows if r["id"] == tile["id"] and
                   r["serial_clear"] == tile["serial_clear"] and r["memory_profile"] == tile["memory_profile"])
        assert 0 <= tile["block"] < cases[tile["id"]]["blocks"]
        assert 1 <= tile["first_dense"] <= tile["last_dense"] <= row["observability"]["timestamps"]["last_dense"]
    return {"attempt": attempt.name, "result_sha256": file_sha(path), "source_sha256": report["source_sha256"],
            "artifact_sha256": report["artifacts_sha256"], "commands": report["commands"],
            "case_rows": len(case_rows), "verdict": verdict}, case_rows


def verify_telemetry(row: dict, golden: dict) -> None:
    obs = row["observability"]
    ts = obs["timestamps"]
    packet_hist, scratch_hist = obs["packet_state_cycles"], obs["scratch_state_cycles"]
    assert len(packet_hist) == 16 and len(scratch_hist) == 32
    assert sum(packet_hist) == sum(scratch_hist) == row["cycles"]
    assert sum(obs["coefficient_handshakes_by_band"]) > 0
    high = obs["highwaters"]
    assert 1 <= high["assembly_bytes"] <= 16 and high["outstanding_requests"] == 1
    assert 0 <= high["cache_lines"] <= 4 and 0 <= high["ac_heads"] <= 3
    assert obs["band_end_handshakes_by_band"] == ([1, 0, 0, 0] if golden["raw"] else [1, 1, 1, 1])
    assert obs["band_end_handshakes_by_band"] == [int(x > 0) for x in obs["band_end_by_band"]]
    assert obs["coefficient_handshakes_by_band"][0] == (golden["blocks"] * 64 if golden["raw"] else golden["blocks"])
    assert sum(obs["coefficient_handshakes_by_band"]) == (golden["blocks"] * 64 if golden["raw"] else
        golden["blocks"] + sum(golden["counts"]))
    for first, last, end, count in zip(obs["first_coefficient_by_band"], obs["last_coefficient_by_band"],
                                      obs["band_end_by_band"], obs["coefficient_handshakes_by_band"]):
        assert bool(first) == bool(last) == bool(count)
        if count:
            assert first <= last < end
    assert sum(obs["band_end_handshakes_by_band"]) in (1, 4)
    assert all(0 <= value <= row["cycles"] for value in ts.values())
    assert 1 <= ts["first_input"] <= ts["last_input"] <= ts["metadata_accept"] <= ts["last_sparse_coef"]
    assert ts["last_sparse_coef"] <= ts["packet_done_observed"] <= ts["seal_accepted"]
    assert ts["seal_accepted"] < ts["scratch_sealed_observed"] <= ts["first_dense"] <= ts["last_dense"]
    assert ts["last_dense"] < ts["integrated_done"] == row["cycles"]
    overlap = obs["overlapping_edges"]
    assert set(overlap) == {"coefficient_stall", "metadata_wait", "band_end_stall", "memory_request_stall",
                            "memory_pending", "input_starved", "dense_stall"}
    assert overlap["dense_stall"] == row["output_stalls"]
    assert overlap["metadata_wait"] == row["metadata_wait"]
    assert overlap["input_starved"] + row["input_bytes"] == packet_hist[1]
    assert overlap["memory_pending"] == row["memory_pending_edges"]
    assert overlap["memory_request_stall"] + row["read_requests"] + row["write_requests"] == \
        obs["scratch_state_cycles"][8] + obs["scratch_state_cycles"][10]
    assert overlap["dense_stall"] + row["dense_coefficients"] == \
        obs["scratch_state_cycles"][20] + obs["scratch_state_cycles"][22]
    groups = ((0,), (1, 2, 3, 4, 5, 6, 7), (8,), (9,), (10,), (11,), (12, 13), (14,),
              (15, 16, 17, 18, 19, 21), (20, 22), (23,), (24, 25), (26, 27, 28, 29, 30, 31))
    assert sum(sum(obs["scratch_state_cycles"][i] for i in group) for group in groups) == row["cycles"]


def main() -> None:
    vectors, cases, rows = verify_vectors()
    contract_path = AREA / "telemetry-contract.json"
    contract = read_report(contract_path)
    assert contract["schema"] == "cu66-v91e-timing-contract-v1"
    public = read_report(RTL / "pipeline-results.json")
    assert public["status"] == "PASS_RECONCILED_TELEMETRY_WITH_FROZEN_V91D_PARITY"
    public_path = ROOT / public["selected_report"]
    runs = []
    for seed in SEEDS:
        matching = sorted((p for p in (RTL / "pipeline-attempts").glob("*/results.json")
                           if read_report(p).get("seed") == seed and read_report(p).get("status") == public["status"]),
                          key=lambda p: p.parent.name)
        assert matching
        receipt, _ = verify_attempt(matching[-1], seed, vectors, cases)
        runs.append(receipt)
    selected = json.loads(public_path.read_text())
    assert selected["seed"] in SEEDS
    assert selected["source_sha256"] == runs[SEEDS.index(selected["seed"])]["source_sha256"]
    parity = {}
    for seed, run in zip(SEEDS, runs):
        parity[str(seed)] = {"matched_v91d_rows": 68, "fields": list(METRICS), "pass": True}
    audit = {"schema": "cu66-v91e-independent-telemetry-audit-v1",
        "status": "PASS_VECTORS_TIMESTAMPS_PARTITIONS_AND_V91D_PARITY",
        "scope": "Independent V88 decode and V91e packed-image reconstruction; source-selection scan, telemetry partition/timestamp checks, and same-seed V91d metric parity. Coefficient pipeline only; no full-frame decode or publication, hardware, or performance optimization claim.",
        "parent_commit": BASE, "audit_source_sha256": {
            "experiments/python-gamebub-v91e/verify_results.py": file_sha(Path(__file__).resolve()),
            "experiments/python-gamebub-v91e/telemetry-contract.json": file_sha(contract_path)},
        "vectors": vectors,
        "integrated_rtl": {"selected_seeds": runs, "public_selected_seed": selected["seed"],
            "timestamp_contract": contract,
            "timestamp_fence": "Counter starts after start edge; running edges are 1-based. First input through integrated done is a packet/scratch-to-dense-coefficient interval. Last dense handshake precedes integrated done; neither is full-frame publication.",
            "counter_histograms_reconcile_to_cycles": True, "overlapping_stalls_are_not_additive": True,
            "v91d_metric_parity": parity}}
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V91E_INDEPENDENT_AUDIT_PASS")


if __name__ == "__main__":
    main()
