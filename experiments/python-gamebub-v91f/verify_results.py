#!/usr/bin/env python3
"""Independent audit of V91f write overlap and frozen coefficient goldens."""
from __future__ import annotations

import ast
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91f"
RTL = ROOT / "fpga/experiments/cu66-v91f"
VECTORS = ROOT / "experiments/python-gamebub-v91e/vectors"
PASS = "PASS_BOUNDED_WRITE_OVERLAP_WITH_FROZEN_V91E_CONTROL"
METRICS = ("cycles", "used_bytes", "input_bytes", "dense_coefficients", "read_requests",
           "write_requests", "output_stalls", "metadata_wait", "memory_pending_edges")
ORDER = tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
LIMITS = (1, 6, 21, 64)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    assert path.is_file(), f"missing pinned artifact: {path}"
    return sha(path.read_bytes())


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def load_codec(path: Path):
    spec = importlib.util.spec_from_file_location("v91f_frozen_v88_codec", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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
    image = bytearray(struct.pack("<8I", 0x43393150, blocks, int(raw), *counts, used, 0))
    for segment in segments:
        image.extend(segment)
        image.extend(bytes(aligned(len(segment)) - len(segment)))
    assert len(image) == used
    return bytes(image)


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


def verify_frozen_vectors() -> tuple[dict, dict[str, dict], list[dict]]:
    index_path = VECTORS / "index.json"
    index = read(index_path)
    assert index["schema"] == "cu66-v91e-coefficient-packed-image-v1"
    assert index["parent_commit"] == "bebd308ca"
    fixture = VECTORS / "coefficients.jsonl.gz"
    compressed = fixture.read_bytes()
    raw_jsonl = gzip.decompress(compressed)
    assert sha(compressed) == index["fixture"]["gzip_sha256"]
    assert sha(raw_jsonl) == index["fixture"]["jsonl_sha256"]
    # Verify the original seventeen fixture rows are byte-identical to V91d.
    old_path = ROOT / "experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz"
    old = old_path.read_bytes()
    assert sha(old) == index["old_fixture_compatibility"]["gzip_sha256"]
    assert b"\n".join(raw_jsonl.splitlines()[:17]) + b"\n" == gzip.decompress(old)
    for rel, digest in index["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest, rel
    codec = load_codec(ROOT / "experiments/python-gamebub-v88/entropy/codec.py")
    rows = [json.loads(line) for line in raw_jsonl.splitlines()]
    assert len(rows) == 20 and len({row["id"] for row in rows}) == 20
    cases = {}
    for row in rows:
        blocks, counts, raw_mode = row["blocks"], row["counts"], bool(row["raw"])
        packet = bytes.fromhex(row["packet_hex"])
        dense = codec.decode(packet, blocks, 1)
        assert len(dense) == blocks * 64 and all(-2048 <= value <= 2048 for value in dense)
        dense_bytes = struct.pack("<" + "h" * len(dense), *dense)
        sparse = sparse_from_dense(dense, blocks, raw_mode)
        image = packed_image(blocks, counts, raw_mode, dense, sparse)
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
        cases[row["id"]] = {"blocks": blocks, "raw": raw_mode, "counts": counts,
            "used_bytes": len(image), "packet_bytes": len(packet), "outputs": blocks * 64,
            "packed_sha256": sha(image), "dense_sha256": sha(dense_bytes), "case_type": row["case_type"]}
    assert sum(row["case_type"] == "actual" for row in rows) == 15
    assert sum(case["outputs"] for case in cases.values()) == index["counts"]["dense_coefficient_outputs"]
    return {"fixture_sha256": sha(compressed), "jsonl_sha256": sha(raw_jsonl),
            "index_sha256": file_sha(index_path), "row_count": len(rows),
            "actual_rows": 15, "dense_coefficients": sum(c["outputs"] for c in cases.values()),
            "case_ids": sorted(cases)}, cases, rows


def verify_telemetry(row: dict, golden: dict, contract: dict) -> None:
    obs = row["observability"]
    ts = obs["timestamps"]
    packet, scratch = obs["packet_state_cycles"], obs["scratch_state_cycles"]
    assert len(packet) == 16 and len(scratch) == 32
    assert sum(packet) == sum(scratch) == row["cycles"]
    assert obs["overlapping_edges"]["memory_pending"] == row["memory_pending_edges"]
    if not row["write_overlap"]:
        assert scratch[9] + scratch[11] == row["memory_pending_edges"]
        assert scratch[8] + scratch[10] == row["read_requests"] + row["write_requests"] + obs["overlapping_edges"]["memory_request_stall"]
    assert scratch[20] + scratch[22] == row["dense_coefficients"] + row["output_stalls"]
    assert packet[1] == row["input_bytes"] + obs["overlapping_edges"]["input_starved"]
    assert obs["overlapping_edges"]["dense_stall"] == row["output_stalls"]
    assert obs["overlapping_edges"]["metadata_wait"] == row["metadata_wait"]
    assert ts["integrated_done"] == row["cycles"] == ts["last_dense"] + 1
    ordered = [ts[name] for name in ("first_input", "last_input", "metadata_accept", "last_sparse_coef",
        "packet_done_observed", "seal_accepted", "scratch_sealed_observed", "first_dense", "last_dense", "integrated_done")]
    assert ordered[0] >= 1 and ordered == sorted(ordered)
    expected_bands = [golden["blocks"] * 64, 0, 0, 0] if golden["raw"] else [golden["blocks"], *golden["counts"]]
    assert obs["coefficient_handshakes_by_band"] == expected_bands
    assert obs["band_end_handshakes_by_band"] == ([1, 0, 0, 0] if golden["raw"] else [1, 1, 1, 1])
    for count, first, last, end in zip(expected_bands, obs["first_coefficient_by_band"],
                                       obs["last_coefficient_by_band"], obs["band_end_by_band"]):
        assert bool(first) == bool(last) == bool(count)
        if count:
            assert ts["metadata_accept"] < first <= last < end <= ts["packet_done_observed"]
    for name, bound in contract["highwater_bounds"].items():
        assert 0 <= obs["highwaters"][name] <= bound
    assert obs["highwaters"]["outstanding_requests"] <= 1
    assert obs["highwaters"]["write_slot"] <= 1 and obs["highwaters"]["owned_lines"] <= 2
    assert row["dense_coefficients"] == golden["outputs"]
    assert row["input_bytes"] == golden["packet_bytes"]
    assert row["used_bytes"] == golden["used_bytes"]
    assert row["read_requests"] == row["write_requests"] == golden["used_bytes"] // 16
    # FLUSH_LINE is an intentional control state; failure/drain and reserved states remain unreachable.
    assert sum(scratch[index] for index in (24, 25, 27, 28, 29, 30, 31)) == 0
    counters = obs["write_overlap_counters"]
    if row["write_overlap"]:
        data_lines = row["write_requests"] - 2  # two descriptor/header bursts follow drained data writes
        assert counters["enqueues"] == counters["physical_accepts"] == counters["physical_acks"] == data_lines
        assert counters["packing_during_write_pending"] > 0 or data_lines == 0
    else:
        assert all(counters[key] == 0 for key in counters)


def verify_attempt(report_path: Path, cases: dict[str, dict], vector_summary: dict, contract: dict) -> tuple[dict, list[dict]]:
    report = read(report_path)
    assert report["schema"] == "cu66-v91f-observed-coefficient-pipeline-v1"
    assert report["status"] == PASS
    assert report["source_revision"] == "96e69d603dd4b8f6fb6aedb72baee8e89d80d5bb"
    attempt = report_path.parent
    assert report["vectors_sha256"] == vector_summary["fixture_sha256"]
    assert report["vector_index_sha256"] == vector_summary["index_sha256"]
    commands = {c["log"]: c for c in report["commands"]}
    assert {"tool-version.log", "compiler-version.log", "compile.log", "simulation.jsonl"} <= commands.keys()
    assert all(c["exit_code"] == 0 for c in report["commands"])
    if "hazard-compile.log" in commands:
        assert "hazards.jsonl" in commands and commands["hazards.jsonl"]["exit_code"] == 0
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest, rel
        assert file_sha(attempt / "sources" / rel) == digest, rel
    for rel, digest in report["artifacts_sha256"].items():
        assert file_sha(attempt / rel) == digest, rel
    assert report["artifacts_sha256"]["tool-version.log"] == file_sha(attempt / "tool-version.log")
    assert report["artifacts_sha256"]["compiler-version.log"] == file_sha(attempt / "compiler-version.log")
    assert "Verilator 5.020" in (attempt / "tool-version.log").read_text()
    assert "g++ (Ubuntu 13.3.0" in (attempt / "compiler-version.log").read_text()
    assert file_sha(attempt / "index.json") == vector_summary["index_sha256"]
    assert file_sha(attempt / "vectors.jsonl.gz") == vector_summary["fixture_sha256"]
    assert report.get("scratch_hazards")
    hazard_path = attempt / "hazards.jsonl"
    assert file_sha(hazard_path) == report["artifacts_sha256"]["hazards.jsonl"]
    hazards = [json.loads(line) for line in hazard_path.read_text().splitlines()]
    assert len(hazards) == 1 and hazards[0] == report["scratch_hazards"]
    assert hazards[0]["status"] == "TEST_PASS" and hazards[0]["directed_checks"] == 9
    assert hazards[0]["physical_accepts"] == hazards[0]["physical_acks"] == 8
    assert "hazard-compile.log" in commands and "hazards.jsonl" in commands
    trace = attempt / report["tile_trace"]["path"]
    assert file_sha(trace) == report["tile_trace"]["gzip_sha256"]
    tile_raw = gzip.decompress(trace.read_bytes())
    assert sha(tile_raw) == report["tile_trace"]["jsonl_sha256"]
    sim_path = attempt / "simulation.jsonl"
    rows = [json.loads(line) for line in sim_path.read_text().splitlines()]
    records = [r for r in rows if r["type"] == "case"]
    verdicts = [r for r in rows if r["type"] == "verdict"]
    assert len(records) == 80 and len(verdicts) == 1
    verdict = verdicts[0]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == report["seed"]
    assert verdict["packets"] == 20 and verdict["case_rows"] == 80 and verdict["directed_checks"] >= 20
    assert verdict["dense_comparisons"] == vector_summary["dense_coefficients"] * 4
    keys = {(r["id"], r["memory_profile"], r["write_overlap"]) for r in records}
    assert keys == {(identity, profile, overlap) for identity in cases for profile in (0, 1) for overlap in (0, 1)}
    by_key = {(r["id"], r["memory_profile"], r["write_overlap"]): r for r in records}
    for row in records:
        verify_telemetry(row, cases[row["id"]], contract)
    for identity in cases:
        for profile in (0, 1):
            off = by_key[(identity, profile, 0)]
            on = by_key[(identity, profile, 1)]
            assert off["request_service_hash"] == on["request_service_hash"]
            assert off["memory_pending_edges"] == on["memory_pending_edges"]
    tiles = [json.loads(line) for line in tile_raw.splitlines()]
    assert len(tiles) == sum(case["blocks"] for case in cases.values()) * 4
    seen = set()
    for tile in tiles:
        key = (tile["id"], tile["memory_profile"], tile["write_overlap"], tile["block"])
        assert key not in seen and tile["id"] in cases
        seen.add(key)
        assert 0 <= tile["block"] < cases[tile["id"]]["blocks"]
        assert tile["first_dense"] <= tile["last_dense"]
        row = by_key[(tile["id"], tile["memory_profile"], tile["write_overlap"])]
        assert tile["last_dense"] <= row["observability"]["timestamps"]["last_dense"]
    assert len(seen) == len(tiles)
    digest = file_sha(report_path)
    return {"attempt": attempt.name, "seed": report["seed"], "result_sha256": digest,
            "source_sha256": report["source_sha256"], "artifact_sha256": report["artifacts_sha256"],
            "tool_pins": {name: report["artifacts_sha256"][name] for name in ("tool-version.log", "compiler-version.log")},
            "case_rows": len(records), "directed_checks": verdict["directed_checks"]}, records


def compare_v91e(records: list[dict], seed: int) -> dict:
    audit_path = ROOT / "experiments/python-gamebub-v91e/audit.json"
    audit = read(audit_path)
    baseline = next(item for item in audit["integrated_rtl"]["selected_seeds"] if item["verdict"]["seed"] == seed)
    path = ROOT / "fpga/experiments/cu66-v91e/pipeline-attempts" / baseline["attempt"] / "results.json"
    assert file_sha(path) == baseline["result_sha256"]
    old_rows = [json.loads(line) for line in (path.parent / "simulation.jsonl").read_text().splitlines()]
    old = {(r["id"], r["memory_profile"]): r for r in old_rows if r["type"] == "case" and r["serial_clear"] == 0}
    current = {(r["id"], r["memory_profile"]): r for r in records if r["write_overlap"] == 0}
    assert len(old) == 40 and old.keys() == current.keys()
    for key, before in old.items():
        after = current[key]
        assert all(before[field] == after[field] for field in METRICS), key
    return {"status": "PASS_EXACT_FROZEN_V91E_MASK_METRICS", "baseline_report": str(path.relative_to(ROOT)),
            "baseline_result_sha256": file_sha(path), "baseline_audit_sha256": file_sha(audit_path),
            "seed": seed, "compared_rows": 40, "fields": list(METRICS), "metric_values_compared": 40 * len(METRICS)}


def compare_benefit(records: list[dict], seed: int) -> dict:
    rows = {(r["id"], r["memory_profile"], r["write_overlap"]): r for r in records}
    details = []
    for (identity, profile, overlap), on in rows.items():
        if not overlap:
            continue
        off = rows[(identity, profile, 0)]
        details.append({"id": identity, "memory_profile": profile,
                        "baseline_cycles": off["cycles"], "candidate_cycles": on["cycles"],
                        "cycles_saved": off["cycles"] - on["cycles"]})
    deltas = [row["cycles_saved"] for row in details]
    by_profile = []
    for profile in (0, 1):
        subset = [row for row in details if row["memory_profile"] == profile]
        values = [row["cycles_saved"] for row in subset]
        by_profile.append({"memory_profile": profile, "paired_cases": len(values),
            "improved": sum(x > 0 for x in values), "unchanged": sum(x == 0 for x in values),
            "regressed": sum(x < 0 for x in values), "cycles_saved_total": sum(values),
            "cycles_saved_min": min(values), "cycles_saved_max": max(values)})
    return {"seed": seed, "paired_cases": len(deltas), "improved": sum(x > 0 for x in deltas),
            "unchanged": sum(x == 0 for x in deltas), "regressed": sum(x < 0 for x in deltas),
            "cycles_saved_total": sum(deltas), "cycles_saved_min": min(deltas),
            "cycles_saved_max": max(deltas), "by_memory_profile": by_profile, "case_deltas": details,
            "interpretation": "Functional optimization comparison on the same 20 fixtures and simulated service profile; individual cases may regress. This coefficient endpoint is not full-frame publication or hardware performance."}


def verify_ownership_model() -> dict:
    source = AREA / "write-ownership-model.py"
    result_path = AREA / "write-ownership-results.json"
    result = read(result_path)
    assert result["schema"] == "v91f-write-ownership-results-v1"
    assert result["source_sha256"] == file_sha(source)
    invariants = set(result["invariants"])
    required = {
        "at most two 16-byte payload owners",
        "offered/accepted slot payload immutable",
        "accepted physical owner retires only on matching ACK, even when local slot_valid is clear",
        "wrong-epoch ACK clears local slot-valid/assembler but cannot retire pending physical owner",
        "abort/reset preserves accepted physical owner while clearing local slot_valid",
        "stale prior-epoch abort is ignored",
        "commits follow increasing line address",
        "input seal request follows data ACKs and final barrier follows both descriptor ACKs",
        "read follows final sealed/publication barrier",
    }
    assert required <= invariants
    directed = result["directed_checks"]
    assert directed["checks"] == 10
    assert result["exhaustive"]["transitions_checked"] >= 18000
    assert result["seeded_scenario"]["events_executed"] == 2500
    assert result["seeded_scenario"]["max_payload_owners"] == 2
    return {"source_sha256": file_sha(source), "result_sha256": file_sha(result_path),
            "directed_checks": directed["checks"], "exhaustive_transitions": result["exhaustive"]["transitions_checked"],
            "seed": result["seeded_scenario"]["seed"], "events_executed": result["seeded_scenario"]["events_executed"],
            "invariants": sorted(required), "scope": result["model_scope"]}


def main() -> None:
    vectors, cases, _ = verify_frozen_vectors()
    contract_path = AREA / "telemetry-contract.json"
    contract = read(contract_path)
    assert contract["schema"] == "cu66-v91f-timing-contract-v1"
    assert contract["current_endpoint"] == "One BR88 residual chunk through packed scratch and dense coefficient completion"
    public_path = RTL / "pipeline-results.json"
    public = read(public_path)
    assert public["status"] == PASS
    selected_path = ROOT / public["selected_report"]
    selected_report = read(selected_path)
    assert public == dict(selected_report, selected_report=public["selected_report"])
    current_sources = public["source_sha256"]
    attempts = []
    for path in RTL.glob("pipeline-attempts/*/results.json"):
        candidate = read(path)
        if candidate.get("status") == PASS and candidate.get("source_sha256") == current_sources:
            attempts.append((candidate.get("seed"), path))
    latest_by_seed = {}
    for seed, path in sorted(attempts, key=lambda item: item[1].parent.name):
        latest_by_seed[seed] = path
    assert set(latest_by_seed) == {910432, 910433}
    assert selected_path in latest_by_seed.values()
    audited_runs = []
    for seed, path in sorted(latest_by_seed.items()):
        receipt, records = verify_attempt(path, cases, vectors, contract)
        receipt["v91e_mask_mode_parity"] = compare_v91e(records, seed)
        receipt["paired_cycle_effect"] = compare_benefit(records, seed)
        audited_runs.append(receipt)
    report = next(item for item in audited_runs if item["seed"] == selected_report["seed"])
    ownership_model = verify_ownership_model()
    audit = {"schema": "cu66-v91f-independent-write-overlap-audit-v1",
        "status": "PASS_FROZEN_V88_GOLDENS_V91E_PARITY_BOUNDED_QUEUE_AND_FENCES",
        "scope": "Independent V88 packet decode and packed-image reconstruction for the frozen 20-case V91e fixture; verifies V91f source/artifact/tool pins, candidate dense simulation assertions and telemetry, one-slot/two-line ownership bounds, physical request service hash A/B matching, post-write-drain seal fence, and exact V91e mask-mode metric parity. Coefficient endpoint only; no full-frame publication, hardware or fps claim.",
        "parent_commit": "96e69d603dd4b8f6fb6aedb72baee8e89d80d5bb",
        "audit_source_sha256": {"experiments/python-gamebub-v91f/verify_results.py": file_sha(Path(__file__).resolve()),
            "experiments/python-gamebub-v91f/telemetry-contract.json": file_sha(contract_path)},
        "vectors": vectors,
        "integrated_rtl": {"selected_attempt": report, "audited_attempts": audited_runs,
            "timestamp_contract": contract,
            "histograms_partition_each_running_edge": True,
            "physical_pending_is_independent_of_scratch_wait_state_in_overlap_mode": True,
            "write_enqueues_equal_data_write_accepts_and_acks": True,
            "seal_waits_for_all_data_write_acks_before_descriptor_writes": True,
            "cold_warm_epoch_contract": "Accepted external write survives abort/reset/start until matching physical ACK; no replacement allocation or memory request begins before old owner drains; mismatched response does not retire the real owner.",
            "write_ownership_model": ownership_model}}
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V91F_INDEPENDENT_AUDIT_PASS")


if __name__ == "__main__":
    main()
