#!/usr/bin/env python3
"""Independent audit of V91g2 two-bank tile overlap and frozen coefficient goldens."""
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
AREA = ROOT / "experiments/python-gamebub-v91g2"
RTL = ROOT / "fpga/experiments/cu66-v91g2"
VECTORS = ROOT / "experiments/python-gamebub-v91e/vectors"
PASS = "PASS_TWO_BANK_TILE_OVERLAP_WITH_FROZEN_V91G_CONTROL"
METRICS = ("cycles", "input_bytes", "dense_coefficients", "read_requests", "write_requests",
           "output_stalls", "metadata_wait", "memory_pending_edges", "used_bytes")
ORDER = tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
LIMITS = (1, 6, 21, 64)
TILE_HAZARD_MARKERS = (
    "A ready-low offer and held dense coefficient each remain immutable",
    "A cache ACK may arrive while dense is held",
    "Logical cancellation cannot retire the accepted read's physical owner",
    "Matching error ACK wins over dense acceptance and cache use",
    "An unrelated response fails the logical epoch",
    "Reset remains cancellation even if the matching ACK arrives while held",
    "Accepted read completion is required before next-scalar demand reuse",
    "A request first offered on the same edge as a line's final scalar",
)
TILE_OVERLAP_MARKERS = (
    "const Case c=zero_tiles(16)",
    "two ready tile-bank setup",
    "tile preparation ACK changed emitted value",
    "tile abort lost accepted read owner",
    "tile read error leaked output",
    "tile stale ACK retired actual owner",
    "tile held reset lost physical hazard",
    "tile replacement allocated before old read drain",
    "tile same-edge next owner sequence",
    "tile unaccepted read abort leaked owner",
    "tile final held completion fence",
)
TILE_RTL_ASSERTIONS = (
    "tile_mode && tile_preparing |-> !bank_ready[prep_bank]",
    "tile_mode && dense_valid |-> bank_ready[emit_bank]",
    "dense_valid && !dense_ready |=> $stable({dense_block,dense_index,dense_value,dense_epoch})",
    "17'(bank_block[emit_bank])+1==blocks |-> !outstanding && !prefetch_offer && !tile_preparing",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    assert path.is_file(), f"missing pinned artifact: {path}"
    return sha(path.read_bytes())


def read(path: Path) -> dict:
    return json.loads(path.read_text())


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


def verify_frozen_vectors() -> tuple[dict, dict[str, dict]]:
    index_path = VECTORS / "index.json"
    index = read(index_path)
    assert index["schema"] == "cu66-v91e-coefficient-packed-image-v1"
    assert index["parent_commit"] == "bebd308ca"
    fixture = VECTORS / "coefficients.jsonl.gz"
    compressed = fixture.read_bytes()
    raw_jsonl = gzip.decompress(compressed)
    assert sha(compressed) == index["fixture"]["gzip_sha256"]
    assert sha(raw_jsonl) == index["fixture"]["jsonl_sha256"]
    old = (ROOT / "experiments/python-gamebub-v91d/vectors/coefficients.jsonl.gz").read_bytes()
    assert sha(old) == index["old_fixture_compatibility"]["gzip_sha256"]
    assert b"\n".join(raw_jsonl.splitlines()[:17]) + b"\n" == gzip.decompress(old)
    for rel, digest in index["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest, rel
    codec_path = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
    spec = importlib.util.spec_from_file_location("v91g_frozen_v88_codec", codec_path)
    assert spec and spec.loader
    codec = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = codec
    spec.loader.exec_module(codec)
    rows = [json.loads(line) for line in raw_jsonl.splitlines()]
    assert len(rows) == 20 and len({row["id"] for row in rows}) == 20
    cases = {}
    for row in rows:
        blocks, counts, raw = row["blocks"], row["counts"], bool(row["raw"])
        packet = bytes.fromhex(row["packet_hex"])
        dense = codec.decode(packet, blocks, 1)
        assert len(dense) == blocks * 64 and all(-2048 <= value <= 2048 for value in dense)
        dense_bytes = struct.pack("<" + "h" * len(dense), *dense)
        sparse = sparse_from_dense(dense, blocks, raw)
        image = packed_image(blocks, counts, raw, dense, sparse)
        assert row["dense_hex"] == dense_bytes.hex(), row["id"]
        assert row["sparse"] == sparse, row["id"]
        assert row["packed_hex"] == image.hex(), row["id"]
        assert row["coefficient_sha256"] == sha(dense_bytes)
        assert row["packed_sha256"] == sha(image)
        assert row["used_bytes"] == len(image)
        source = row.get("source", {})
        if isinstance(source, str):
            source = ast.literal_eval(source)
        if row["case_type"] == "actual":
            assert all(key in source for key in ("cohort", "fid", "plane", "chunk", "packet_sha256", "coefficient_sha256"))
            assert source["packet_sha256"] == sha(packet)
            assert source["coefficient_sha256"] == sha(dense_bytes)
        cases[row["id"]] = {"blocks": blocks, "raw": raw, "counts": counts, "used_bytes": len(image),
            "packet_bytes": len(packet), "outputs": blocks * 64, "packed": image, "dense": dense,
            "packed_sha256": sha(image), "dense_sha256": sha(dense_bytes), "case_type": row["case_type"]}
    assert sum(row["case_type"] == "actual" for row in rows) == 15
    assert sum(case["outputs"] for case in cases.values()) == index["counts"]["dense_coefficient_outputs"]
    return {"fixture_sha256": sha(compressed), "jsonl_sha256": sha(raw_jsonl),
        "index_sha256": file_sha(index_path), "row_count": len(rows), "actual_rows": 15,
        "dense_coefficients": sum(c["outputs"] for c in cases.values()), "case_ids": sorted(cases)}, cases


def mix_word(value: int, word: int) -> int:
    mask, prime = (1 << 64) - 1, 1099511628211
    for byte in int(word).to_bytes(8, "little"):
        value = ((value ^ byte) * prime) & mask
    return value


def expected_service(case: dict, profile: int, seed: int) -> tuple[str, str]:
    packed = case["packed"]
    writes = list(range(32, len(packed), 16)) + [0, 16]
    total, ordered_write = 0, 1469598103934665603
    for direction, addresses in ((1, writes), (0, range(0, len(packed), 16))):
        for address in addresses:
            latency = (16 if direction else 18) + (((address >> 4) ^ seed) & 3) if profile else 1
            words = [direction, address, latency]
            if direction:
                words.extend(int.from_bytes(packed[address+j:address+j+4], "little") for j in range(0, 16, 4))
            request = 1469598103934665603
            for word in words:
                request = mix_word(request, word)
                if direction:
                    ordered_write = mix_word(ordered_write, word)
            total = (total + request) & ((1 << 64) - 1)
    return str(total), str(ordered_write)


def verify_telemetry(row: dict, golden: dict, contract: dict) -> None:
    obs, ts = row["observability"], row["observability"]["timestamps"]
    packet, scratch = obs["packet_state_cycles"], obs["scratch_state_cycles"]
    emitter = obs["emitter_state_cycles"]
    assert len(packet) == 16 and len(scratch) == 32
    assert len(emitter) == 4 and sum(emitter) == row["cycles"]
    assert sum(packet) == sum(scratch) == row["cycles"]
    assert sum(scratch[i] for indexes in contract["exclusive_scratch_groups"].values() for i in indexes) == row["cycles"]
    assert obs["overlapping_edges"]["memory_pending"] == row["memory_pending_edges"]
    if not row["tile_overlap"] or golden["raw"]:
        assert scratch[20] + scratch[22] == row["dense_coefficients"] + row["output_stalls"]
    assert packet[1] == row["input_bytes"] + obs["overlapping_edges"]["input_starved"]
    assert obs["overlapping_edges"]["dense_stall"] == row["output_stalls"]
    assert obs["overlapping_edges"]["metadata_wait"] == row["metadata_wait"]
    assert ts["integrated_done"] == row["cycles"] == ts["last_dense"] + 1
    ordered = [ts[k] for k in ("first_input", "last_input", "metadata_accept", "last_sparse_coef", "packet_done_observed",
                                  "seal_accepted", "scratch_sealed_observed", "first_dense", "last_dense", "integrated_done")]
    assert ordered[0] >= 1 and ordered == sorted(ordered)
    expected_bands = [golden["blocks"] * 64, 0, 0, 0] if golden["raw"] else [golden["blocks"], *golden["counts"]]
    assert obs["coefficient_handshakes_by_band"] == expected_bands
    assert obs["band_end_handshakes_by_band"] == ([1, 0, 0, 0] if golden["raw"] else [1, 1, 1, 1])
    for count, first, last, end in zip(expected_bands, obs["first_coefficient_by_band"],
                                       obs["last_coefficient_by_band"], obs["band_end_by_band"]):
        assert bool(first) == bool(last) == bool(count)
        if count:
            assert ts["metadata_accept"] < first <= last < end <= ts["packet_done_observed"]
        elif not golden["raw"]:
            assert end > 0
    for field, bound in contract["highwater_bounds"].items():
        assert 0 <= obs["highwaters"][field] <= bound
    assert obs["highwaters"]["outstanding_requests"] <= 1
    assert obs["highwaters"]["write_slot"] <= 1 and obs["highwaters"]["owned_lines"] <= 2
    assert row["dense_coefficients"] == golden["outputs"] and row["input_bytes"] == golden["packet_bytes"]
    assert row["used_bytes"] == golden["used_bytes"]
    assert row["read_requests"] == row["write_requests"] == golden["used_bytes"] // 16
    assert row["memory_line_coverage"] == {"read_once_lines": golden["used_bytes"] // 16,
                                            "write_once_lines": golden["used_bytes"] // 16}
    assert sum(scratch[i] for i in (24, 25, 30, 31)) == 0
    writes = obs["write_overlap_counters"]
    assert writes["enqueues"] == writes["physical_accepts"] == writes["physical_acks"] == row["write_requests"] - 2
    prefetch = obs["read_prefetch_counters"]
    assert set(prefetch) == {"offers", "physical_accepts", "physical_acks", "uses", "dense_during_pending", "drain_wait_edges"}
    assert prefetch["offers"] == prefetch["physical_accepts"] == prefetch["physical_acks"] == prefetch["uses"]
    assert prefetch["physical_accepts"] <= row["read_requests"] - 2
    assert prefetch["drain_wait_edges"] == scratch[27]
    assert row["read_prefetch"] == 1
    assert obs["highwaters"]["prefetch_offer"] <= 1
    assert prefetch["dense_during_pending"] <= row["dense_coefficients"]
    assert obs["highwaters"]["tile_owned"] <= 2
    assert obs["highwaters"]["tile_ready"] <= 2
    overlap = obs["tile_overlap_counters"]
    assert set(overlap) == {"prepare_starts", "publishes", "releases", "prepare_output_overlap",
        "prepare_output_hold", "read_output_overlap", "bank_wait_edges", "both_ready_wait_edges",
        "prep_done_wait_edges", "publish_release_same_edge", "output_valid_edges"}
    expected_preparations = golden["blocks"] if row["tile_overlap"] and not golden["raw"] else 0
    assert overlap["prepare_starts"] == overlap["publishes"] == overlap["releases"] == expected_preparations
    assert overlap["output_valid_edges"] == row["dense_coefficients"] + row["output_stalls"]
    assert overlap["bank_wait_edges"] == scratch[28]
    assert overlap["prep_done_wait_edges"] == scratch[29]
    assert overlap["both_ready_wait_edges"] <= overlap["bank_wait_edges"]
    assert overlap["prepare_output_overlap"] <= row["dense_coefficients"]
    assert overlap["prepare_output_hold"] <= row["output_stalls"]
    assert overlap["read_output_overlap"] <= row["dense_coefficients"]
    assert overlap["publish_release_same_edge"] <= expected_preparations
    if row["tile_overlap"] and not golden["raw"]:
        assert emitter[1] + emitter[2] == row["dense_coefficients"] + row["output_stalls"]
    else:
        assert emitter[0] == emitter[1] == emitter[2] == 0 and emitter[3] == row["cycles"]


def verify_attempt(report_path: Path, cases: dict[str, dict], vector_summary: dict, contract: dict) -> tuple[dict, list[dict]]:
    report = read(report_path)
    assert report["schema"] == "cu66-v91g2-observed-coefficient-pipeline-v1"
    assert report["status"] == PASS
    assert report["seed"] in (910432, 910433)
    attempt = report_path.parent
    assert report["vectors_sha256"] == vector_summary["fixture_sha256"]
    assert report["vector_index_sha256"] == vector_summary["index_sha256"]
    commands = {c["log"]: c for c in report["commands"]}
    required = {"tool-version.log", "compiler-version.log", "compile.log", "hazard-compile.log", "hazards.jsonl", "simulation.jsonl"}
    assert required <= commands.keys() and all(c["exit_code"] == 0 for c in report["commands"])
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest, rel
        assert file_sha(attempt / "sources" / rel) == digest, rel
    for rel, digest in report["artifacts_sha256"].items():
        assert file_sha(attempt / rel) == digest, rel
    assert file_sha(attempt / "index.json") == vector_summary["index_sha256"]
    assert file_sha(attempt / "vectors.jsonl.gz") == vector_summary["fixture_sha256"]
    assert "Verilator 5.020" in (attempt / "tool-version.log").read_text()
    assert "g++ (Ubuntu 13.3.0" in (attempt / "compiler-version.log").read_text()
    # The standalone scratch harness keeps the nine existing write hazards;
    # the integrated pipeline verdict carries the tile bank hazard checks.
    hazard_path = attempt / "hazards.jsonl"
    hazards = [json.loads(line) for line in hazard_path.read_text().splitlines()]
    assert len(hazards) == 1 and report["scratch_hazards"] == hazards[0]
    hazard = hazards[0]
    assert hazard["status"] == "TEST_PASS" and hazard["directed_checks"] == 9
    assert hazard["physical_accepts"] == hazard["physical_acks"]
    pipeline_source = (attempt / "sources/fpga/experiments/cu66-v91g2/tb_pipeline.cpp").read_text()
    assert all(marker in pipeline_source for marker in TILE_HAZARD_MARKERS)
    assert all(marker in pipeline_source for marker in TILE_OVERLAP_MARKERS)
    scratch_source = (attempt / "sources/fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv").read_text()
    assert all(marker in scratch_source for marker in TILE_RTL_ASSERTIONS)
    tile = report["tile_trace"]
    trace = attempt / tile["path"]
    assert file_sha(trace) == tile["gzip_sha256"]
    tile_raw = gzip.decompress(trace.read_bytes())
    assert sha(tile_raw) == tile["jsonl_sha256"]
    sim_path = attempt / "simulation.jsonl"
    rows = [json.loads(line) for line in sim_path.read_text().splitlines()]
    records = [r for r in rows if r["type"] == "case"]
    verdicts = [r for r in rows if r["type"] == "verdict"]
    assert len(records) == 80 and len(verdicts) == 1
    verdict = verdicts[0]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == report["seed"]
    assert verdict["packets"] == 20 and verdict["case_rows"] == 80 and verdict["configurations"] == 4
    assert verdict["dense_comparisons"] == vector_summary["dense_coefficients"] * 4
    assert verdict["directed_checks"] == 47
    keys = {(r["id"], r["memory_profile"], r["tile_overlap"]) for r in records}
    assert keys == {(identity, profile, enabled) for identity in cases for profile in (0, 1) for enabled in (0, 1)}
    keyed = {(r["id"], r["memory_profile"], r["tile_overlap"]): r for r in records}
    for row in records:
        verify_telemetry(row, cases[row["id"]], contract)
        multiset, ordered_write = expected_service(cases[row["id"]], row["memory_profile"], report["seed"])
        assert row["request_service_multiset_hash"] == multiset, (row["id"], row["memory_profile"], row["read_prefetch"])
        assert row["ordered_write_service_hash"] == ordered_write
        assert row["serial_clear"] == 0 and row["write_overlap"] == 1 and row["read_prefetch"] == 1
    # With reordered reads, compare canonical service totals and ordered writes, not ordered read hashes.
    for identity in cases:
        for profile in (0, 1):
            a, b = keyed[(identity, profile, 0)], keyed[(identity, profile, 1)]
            assert a["ordered_write_service_hash"] == b["ordered_write_service_hash"]
    tile_rows = [json.loads(line) for line in tile_raw.splitlines()]
    assert len(tile_rows) == sum(case["blocks"] for case in cases.values()) * 4
    seen, per_key = set(), {}
    for tile_row in tile_rows:
        key = (tile_row["id"], tile_row["memory_profile"], tile_row["tile_overlap"])
        assert key in {(r["id"], r["memory_profile"], r["tile_overlap"]) for r in records}
        group = per_key.setdefault(key, [])
        assert tile_row["block"] == len(group) and tile_row["first_dense"] <= tile_row["last_dense"]
        assert tile_row["last_dense"] - tile_row["first_dense"] >= 63
        if group:
            assert tile_row["first_dense"] > group[-1]["last_dense"]
        group.append(tile_row)
        seen.add((key, tile_row["block"]))
    assert len(seen) == len(tile_rows) and per_key.keys() == {(r["id"], r["memory_profile"], r["tile_overlap"]) for r in records}
    for key, group in per_key.items():
        row = keyed[key]
        assert len(group) == cases[key[0]]["blocks"]
        assert group[0]["first_dense"] == row["observability"]["timestamps"]["first_dense"]
        assert group[-1]["last_dense"] == row["observability"]["timestamps"]["last_dense"]
    baseline = compare_v91g(records, report["seed"])
    published_baseline = report["baseline_v91g"]
    for field in ("status", "baseline_report", "baseline_result_sha256", "baseline_audit_sha256",
                  "compared_rows", "metrics", "metric_values_compared"):
        assert published_baseline[field] == baseline[field], field
    return ({"attempt": attempt.name, "seed": report["seed"], "result_sha256": file_sha(report_path),
             "source_sha256": report["source_sha256"], "artifact_sha256": report["artifacts_sha256"],
             "case_rows": len(records), "directed_checks": verdict["directed_checks"],
             "v91g_exact_control_parity": baseline,
             "read_prefetch_counters": {"offers": sum(r["observability"]["read_prefetch_counters"]["offers"] for r in records),
                "acks": sum(r["observability"]["read_prefetch_counters"]["physical_acks"] for r in records),
                "uses": sum(r["observability"]["read_prefetch_counters"]["uses"] for r in records),
                "dense_during_pending": sum(r["observability"]["read_prefetch_counters"]["dense_during_pending"] for r in records),
                "drain_wait_edges": sum(r["observability"]["read_prefetch_counters"]["drain_wait_edges"] for r in records)}}), records


def compare_v91g(records: list[dict], seed: int) -> dict:
    audit_path = ROOT / "experiments/python-gamebub-v91g/audit.json"
    audit = read(audit_path)
    control = next(item for item in audit["integrated_rtl"]["audited_attempts"] if item["seed"] == seed)
    path = ROOT / "fpga/experiments/cu66-v91g/pipeline-attempts" / control["attempt"] / "results.json"
    assert file_sha(path) == control["result_sha256"]
    old_rows = [json.loads(line) for line in (path.parent / "simulation.jsonl").read_text().splitlines()]
    old = {(r["id"], r["memory_profile"]): r for r in old_rows if r["type"] == "case" and r["serial_clear"] == 0 and r["write_overlap"] == 1 and r["read_prefetch"] == 1}
    current = {(r["id"], r["memory_profile"]): r for r in records if r["tile_overlap"] == 0}
    assert len(old) == 40 and old.keys() == current.keys()
    raw = {case["id"] for case in read_frozen_rows() if case["raw"]}
    for key, before in old.items():
        assert all(before[field] == current[key][field] for field in METRICS), key
        assert before["request_service_hash"] == current[key]["request_service_hash"], key
        if key[0] in raw:
            for overlap in (0, 1):
                candidate = next(r for r in records if (r["id"], r["memory_profile"], r["tile_overlap"]) == (*key, overlap))
                assert all(before[field] == candidate[field] for field in METRICS), ("RAW", key, overlap)
                assert before["request_service_hash"] == candidate["request_service_hash"], ("RAW", key, overlap)
    return {"status": "PASS_EXACT_FROZEN_V91G_PREFETCH_METRICS", "baseline_report": str(path.relative_to(ROOT)),
            "baseline_result_sha256": file_sha(path), "baseline_audit_sha256": file_sha(audit_path),
            "seed": seed, "compared_rows": 40, "metrics": list(METRICS), "metric_values_compared": 40 * len(METRICS),
            "raw_rows_compared_both_tile_modes": len(raw) * 2 * 2,
            "raw_metrics_compared": len(raw) * 2 * 2 * len(METRICS), "raw_service_hash_compared_both_tile_modes": True}


def read_frozen_rows() -> list[dict]:
    with gzip.open(VECTORS / "coefficients.jsonl.gz", "rt") as source:
        return [json.loads(line) for line in source]


def compare_effect(records: list[dict], seed: int) -> dict:
    rows = {(r["id"], r["memory_profile"], r["tile_overlap"]): r for r in records}
    details = []
    for (identity, profile, enabled), candidate in rows.items():
        if not enabled:
            continue
        control = rows[(identity, profile, 0)]
        details.append({"id": identity, "memory_profile": profile, "baseline_cycles": control["cycles"],
                        "candidate_cycles": candidate["cycles"], "cycles_saved": control["cycles"] - candidate["cycles"]})
    deltas = [d["cycles_saved"] for d in details]
    profiles = []
    for profile in (0, 1):
        values = [d["cycles_saved"] for d in details if d["memory_profile"] == profile]
        profiles.append({"memory_profile": profile, "paired_cases": len(values), "improved": sum(x > 0 for x in values),
            "unchanged": sum(x == 0 for x in values), "regressed": sum(x < 0 for x in values),
            "cycles_saved_total": sum(values), "cycles_saved_min": min(values), "cycles_saved_max": max(values)})
    return {"seed": seed, "paired_cases": len(deltas), "improved": sum(x > 0 for x in deltas),
        "unchanged": sum(x == 0 for x in deltas), "regressed": sum(x < 0 for x in deltas),
        "cycles_saved_total": sum(deltas), "cycles_saved_min": min(deltas), "cycles_saved_max": max(deltas),
        "by_memory_profile": profiles, "case_deltas": details,
        "interpretation": "Functional optimization comparison on the same 20 fixtures and simulated service profile; individual cases may regress. This coefficient endpoint is not full-frame publication or hardware performance."}


def verify_tile_bank_model() -> dict:
    source = AREA / "tile-bank-model.py"
    result_path = AREA / "tile-bank-results.json"
    result = read(result_path)
    assert result["schema"] == "cu66-v91g2-two-tile-bank-model-v1"
    assert result["status"] == "PASS_BOUNDED_ABSTRACT_OWNERSHIP_CHECKS"
    assert result["source_sha256"] == file_sha(source) == "306704a933f4eb5f871d47f55f537b53d44cd8e771df1236ead269e89f5fae0d"
    scope = result["scope"]
    assert scope["banks"] == 2 and scope["blocks"] == 3
    assert scope["abstract_scalars_per_block"] == 3 and scope["actual_rtl_scalars_per_block"] == 64
    assert scope["abstract_prepare_units"] == 2 and scope["cycle_accurate"] is False
    assert scope["rtl_equivalence_claimed"] is False and scope["performance_evidence"] is False
    bfs = result["bounded_bfs"]
    required_bfs = {"start_prepare", "accept_external_read", "ack_match_ok", "prepare_complete",
        "hold_output", "stall_output", "accept_output", "accept_last_output",
        "accept_last_and_prepare_complete", "response_wrong_epoch", "ack_match_error",
        "ack_error_priority_over_output", "cancel_reset", "restart_after_drain", "final_done_after_drain"}
    assert required_bfs <= set(bfs["event_coverage"])
    assert bfs["max_depth"] == 36
    assert bfs["unique_states"] == 189292 and bfs["transitions_checked"] == 503367
    directed = result["directed_checks"]
    required_directed = {"held_output_immutable", "last_scalar_prepare_handoff",
        "matching_error_priority", "wrong_epoch_retains_physical_owner", "reuse_after_handoff"}
    assert set(directed) == required_directed and all(directed.values())
    seeded = result["seeded_walk"]
    assert seeded["seed"] == 910438 and seeded["requested_steps"] == 5000
    assert seeded["actual_events"] == 5000
    assert seeded["terminal_restarts"] == 0
    assert sum(seeded["event_counts"].values()) == seeded["actual_events"]
    return {"source_sha256": file_sha(source), "result_sha256": file_sha(result_path),
        "scope": scope, "bfs_max_depth": bfs["max_depth"], "bfs_unique_states": bfs["unique_states"],
        "bfs_transitions_checked": bfs["transitions_checked"],
        "bfs_required_events": sorted(required_bfs), "directed_checks": sorted(directed),
        "seed": seeded["seed"], "requested_steps": seeded["requested_steps"],
        "actual_events": seeded["actual_events"], "terminal_restarts": seeded["terminal_restarts"],
        "limits": ["Three abstract scalars per tile and two abstract preparation steps; not a cycle or RTL equivalence model.",
            "Unaccepted request-offer backpressure and cancellation are covered by directed RTL hazards, not this event model."]}


def main() -> None:
    vectors, cases = verify_frozen_vectors()
    contract_path = AREA / "telemetry-contract.json"
    contract = read(contract_path)
    assert contract["schema"] == "cu66-v91g2-timing-contract-v1"
    assert contract["current_endpoint"] == "One BR88 residual chunk through packed scratch and dense coefficient completion"
    public_path = RTL / "pipeline-results.json"
    public = read(public_path)
    assert public["status"] == PASS
    selected_path = ROOT / public["selected_report"]
    selected_report = read(selected_path)
    assert public == dict(selected_report, selected_report=public["selected_report"])
    current_sources = public["source_sha256"]
    attempts_by_seed = {}
    for path in sorted(RTL.glob("pipeline-attempts/*/results.json"), key=lambda p: p.parent.name):
        candidate = read(path)
        if candidate.get("status") == PASS and candidate.get("source_sha256") == current_sources:
            attempts_by_seed[candidate.get("seed")] = path
    assert set(attempts_by_seed) == {910432, 910433}
    assert selected_path in attempts_by_seed.values()
    audited = []
    for seed, path in sorted(attempts_by_seed.items()):
        receipt, records = verify_attempt(path, cases, vectors, contract)
        receipt["paired_tile_overlap_effect"] = compare_effect(records, seed)
        audited.append(receipt)
    chosen = next(r for r in audited if r["seed"] == selected_report["seed"])
    tile_model = verify_tile_bank_model()
    audit = {"schema": "cu66-v91g2-independent-two-tile-bank-overlap-audit-v1",
        "status": "PASS_FROZEN_V88_GOLDENS_V91G_CONTROL_TWO_BANK_OWNERSHIP_AND_FENCES",
        "scope": "Independent V88 packet decode and packed-image reconstruction for the frozen 20-case V91e fixture; verifies V91g2 source/artifact/tool pins, dense simulation assertions and telemetry, two-bank tile preparation/emission ownership, fixture-derived canonical read/write service signatures, once-per-line traffic coverage, exact nine-metric and ordered-service V91g tile-overlap-off parity at seeds 910432/910433, and exact RAW-path parity in both tile modes. The abstract bank model is bounded event evidence, not an RTL or timing proof. Coefficient endpoint only; no full-frame publication, hardware or fps claim.",
        "parent_commit": selected_report["source_revision"],
        "audit_source_sha256": {"experiments/python-gamebub-v91g2/verify_results.py": file_sha(Path(__file__).resolve()),
            "experiments/python-gamebub-v91g2/telemetry-contract.json": file_sha(contract_path)},
        "vectors": vectors,
        "integrated_rtl": {"selected_attempt": chosen, "audited_attempts": audited, "timestamp_contract": contract,
            "tile_bank_ownership": "At most two occupied tile banks; an emitting bank is distinct from a preparing bank; a prepared tile cannot be reused until its 64th scalar is accepted; an accepted external read remains physically owned through abort, reset, replacement start, matching error, and stale response drain; final done follows final dense acceptance, all bank releases and pending-read drain.",
            "raw_path": "Exact V91g prefetch-enabled legacy metrics and ordered service hash are compared for both tile_overlap=0 and tile_overlap=1.",
            "service_signature_method": contract["service_signature"],
            "full_frame_validated_decode_under10ms_proven": False, "hardware_distinct_30fps_proven": False,
            "physical_clock_fit_or_memory_controller_calibration_proven": False},
        "tile_bank_model": tile_model}
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V91G2_INDEPENDENT_AUDIT_PASS")


if __name__ == "__main__":
    main()
