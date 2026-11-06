#!/usr/bin/env python3
"""Independent audit for V91h synchronous packet ingress staging."""
from __future__ import annotations

import ast
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v91h"
RTL = ROOT / "fpga/experiments/cu66-v91h"
VECTORS = ROOT / "experiments/python-gamebub-v91e/vectors"
PASS = "PASS_SYNCHRONOUS_STAGING_WITH_FROZEN_V91G2_CONTROL"
SEEDS = (910432, 910433)
STAGING_DIRECTED_CHECKS = {
    "unaligned_header_descriptor_partial_word",
    "padding_rejected_before_metadata",
    "abort_queued_ram_request",
    "abort_registered_ram_response",
    "reset_registered_ram_response",
    "restart_registered_ram_response",
    "held_sparse_visible_during_ram_fetch",
    "raw_pair_held_until_acceptance",
    "context_failure_cancels_inflight_fetch",
}
METRICS = ("cycles", "input_bytes", "dense_coefficients", "read_requests", "write_requests",
           "output_stalls", "metadata_wait", "memory_pending_edges", "used_bytes")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    assert path.is_file(), f"missing pinned artifact: {path}"
    return sha(path.read_bytes())


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def aligned(n: int) -> int:
    return (n + 15) // 16 * 16


ORDER = tuple(sorted(range(64), key=lambda i: (i // 8 + i % 8,
                                                i // 8 if (i // 8 + i % 8) % 2 else -(i // 8))))
LIMITS = (1, 6, 21, 64)


def packed_image(blocks, counts, raw, dense, sparse):
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


def sparse_from_dense(values, blocks, raw):
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


def verify_frozen_vectors():
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
    spec = importlib.util.spec_from_file_location("v91h_frozen_v88_codec", codec_path)
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


def expected_service(case, profile, seed):
    packed = case["packed"]
    writes = list(range(32, len(packed), 16)) + [0, 16]
    total, ordered_write = 0, 1469598103934665603
    mask, prime = (1 << 64) - 1, 1099511628211
    def mix(value, word):
        for byte in int(word).to_bytes(8, "little"):
            value = ((value ^ byte) * prime) & mask
        return value
    for direction, addresses in ((1, writes), (0, range(0, len(packed), 16))):
        for address in addresses:
            latency = (16 if direction else 18) + (((address >> 4) ^ seed) & 3) if profile else 1
            words = [direction, address, latency]
            if direction:
                words.extend(int.from_bytes(packed[address+j:address+j+4], "little") for j in range(0, 16, 4))
            request = 1469598103934665603
            for word in words:
                request = mix(request, word)
                if direction:
                    ordered_write = mix(ordered_write, word)
            total = (total + request) & mask
    return str(total), str(ordered_write)


def get_fields(row):
    """Flatten observability fields emitted by the V91g2-compatible harness."""
    obs = row.get("observability", {})
    return {**row, **obs}


def check_row(row, case, seed):
    f = get_fields(row)
    assert f["input_bytes"] == case["packet_bytes"]
    assert f["dense_coefficients"] == case["outputs"]
    assert f["used_bytes"] == case["used_bytes"]
    assert f["read_requests"] == f["write_requests"] == case["used_bytes"] // 16
    coverage = f.get("memory_line_coverage")
    if coverage is None:
        coverage = f.get("observability", {}).get("memory_line_coverage")
    assert coverage == {"read_once_lines": case["used_bytes"] // 16,
                        "write_once_lines": case["used_bytes"] // 16}
    multiset, ordered_write = expected_service(case, row["memory_profile"], seed)
    assert row.get("request_service_multiset_hash") == multiset
    assert isinstance(row.get("request_service_hash"), str) and row["request_service_hash"]
    assert row["ordered_write_service_hash"] == ordered_write


def compare_controls(all_rows, seed, cases):
    controls = {(r["id"], r["memory_profile"]): r for r in all_rows if r["sync_staging"] == 0}
    sync = {(r["id"], r["memory_profile"]): r for r in all_rows if r["sync_staging"] == 1}
    assert len(controls) == len(sync) == 40 and controls.keys() == sync.keys()
    baseline_audit_path = ROOT / "experiments/python-gamebub-v91g2/audit.json"
    baseline_audit = read(baseline_audit_path)
    attempts = baseline_audit["integrated_rtl"]["audited_attempts"]
    baseline = next(x for x in attempts if x["seed"] == seed)
    baseline_path = ROOT / "fpga/experiments/cu66-v91g2/pipeline-attempts" / baseline["attempt"] / "results.json"
    assert file_sha(baseline_path) == baseline["result_sha256"]
    baseline_rows = [json.loads(line) for line in (baseline_path.parent / "simulation.jsonl").read_text().splitlines()]
    baseline_rows = {(r["id"], r["memory_profile"]): r for r in baseline_rows
                     if r.get("type") == "case" and r.get("serial_clear") == 0 and r.get("write_overlap") == 1
                     and r.get("read_prefetch") == 1 and r.get("tile_overlap") == 1}
    assert baseline_rows.keys() == controls.keys()
    for key, row in controls.items():
        old = baseline_rows[key]
        assert all(old[name] == row[name] for name in METRICS), (key, "legacy metrics")
        assert old["request_service_hash"] == row["request_service_hash"], (key, "legacy service hash")
        assert old["ordered_write_service_hash"] == row["ordered_write_service_hash"]
        # Synchronous staging can add cycles and move the dense fence, but it must not alter function or traffic.
        candidate = sync[key]
        for name in ("input_bytes", "dense_coefficients", "read_requests", "write_requests", "used_bytes"):
            assert row[name] == candidate[name], (key, name)
        for name in ("request_service_hash", "request_service_multiset_hash", "ordered_write_service_hash",
                     "memory_line_coverage", "dense_sha256", "coefficient_sha256", "packed_sha256", "error", "error_code"):
            if name in row or name in candidate:
                assert row.get(name) == candidate.get(name), (key, name)
        assert row.get("memory_line_coverage", row.get("observability", {}).get("memory_line_coverage")) == \
               candidate.get("memory_line_coverage", candidate.get("observability", {}).get("memory_line_coverage"))
        case = cases[key[0]]
        assert row.get("dense_sha256", row.get("coefficient_sha256", case["dense_sha256"])) == case["dense_sha256"]
        assert candidate.get("dense_sha256", candidate.get("coefficient_sha256", case["dense_sha256"])) == case["dense_sha256"]
        assert row.get("packed_sha256", case["packed_sha256"]) == case["packed_sha256"]
        assert candidate.get("packed_sha256", case["packed_sha256"]) == case["packed_sha256"]
    return {"status": "PASS", "baseline_report": str(baseline_path.relative_to(ROOT)),
        "baseline_result_sha256": file_sha(baseline_path), "baseline_audit_sha256": file_sha(baseline_audit_path),
        "seed": seed, "legacy_rows": 40, "legacy_metric_values_compared": 40 * len(METRICS),
        "sync_functional_pairs": 40, "sync_metrics_allowed_to_change": ["cycles", "output_stalls", "metadata_wait", "memory_pending_edges", "timestamps"]}


def verify_attempt(path, cases, vectors):
    report = read(path)
    assert report["schema"] in ("cu66-v91h-observed-coefficient-pipeline-v1", "cu66-v91h-integrated-result-v1")
    assert report["status"] == PASS and report["seed"] in SEEDS
    attempt = path.parent
    assert report.get("vectors_sha256") == vectors["fixture_sha256"]
    assert report.get("vector_index_sha256") == vectors["index_sha256"]
    commands = {c["log"]: c for c in report["commands"]}
    assert {"tool-version.log", "compiler-version.log", "compile-legacy.log", "compile-sync.log",
            "simulation-legacy.jsonl", "simulation-sync.jsonl",
            "hazard-compile.log", "hazards.jsonl"} <= commands.keys()
    assert all(c["exit_code"] == 0 for c in report["commands"])
    argv_text = "\n".join(" ".join(c.get("argv", [])) for c in report["commands"])
    for value in (0, 1):
        assert f"-GSYNC_STAGING={value}" in argv_text
        assert f"-DSYNC_STAGING={value}" in argv_text
    for rel, digest in report["source_sha256"].items():
        assert file_sha(ROOT / rel) == digest
        assert file_sha(attempt / "sources" / rel) == digest
    for rel, digest in report["artifacts_sha256"].items():
        assert file_sha(attempt / rel) == digest
    assert file_sha(attempt / "index.json") == vectors["index_sha256"]
    assert file_sha(attempt / "vectors.jsonl.gz") == vectors["fixture_sha256"]
    versions = (attempt / "tool-version.log").read_text()
    assert "Verilator 5.020" in versions
    assert "g++ (Ubuntu 13.3.0" in (attempt / "compiler-version.log").read_text()
    hazards = [json.loads(line) for line in (attempt / "hazards.jsonl").read_text().splitlines()]
    assert len(hazards) == 1 and hazards[0]["status"] == "TEST_PASS" and hazards[0]["directed_checks"] == 9
    rows = [json.loads(line) for line in (attempt / "simulation.jsonl").read_text().splitlines()]
    records = [r for r in rows if r.get("type") == "case"]
    verdicts = [r for r in rows if r.get("type") == "verdict"]
    assert len(records) == 80 and len(verdicts) == 2
    assert {(r["id"], r["memory_profile"], r["sync_staging"]) for r in records} == {
        (identity, profile, staging) for identity in cases for profile in (0, 1) for staging in (0, 1)}
    for row in records:
        assert row["serial_clear"] == 0 and row["write_overlap"] == 1 and row["read_prefetch"] == 1 and row["tile_overlap"] == 1
        assert row["sync_staging"] in (0, 1)
        # The detailed telemetry keeps the established V91g2 packet and scratch accounting contract.
        obs = row["observability"]
        assert sum(obs["packet_state_cycles"]) == sum(obs["scratch_state_cycles"]) == row["cycles"]
        assert obs["packet_state_cycles"][1] == row["input_bytes"] + obs["overlapping_edges"]["input_starved"]
        assert obs["timestamps"]["integrated_done"] == row["cycles"] == obs["timestamps"]["last_dense"] + 1
        stage = obs["staging_counters"]
        if row["sync_staging"]:
            assert stage["writes"] == row["input_bytes"]
            assert stage["reads"] == stage["responses"]
            assert stage["buffer_highwater"] == 46
            if cases[row["id"]]["raw"]:
                assert stage["reads"] == row["input_bytes"]
                assert stage["reads_by_purpose"] == [46, 0, 0, row["input_bytes"] - 46]
            else:
                assert stage["reads"] == row["input_bytes"] + 4
                assert stage["reads_by_purpose"] == [46, 28, row["input_bytes"] - 70, 0]
        else:
            assert stage["writes"] == stage["reads"] == stage["responses"] == 0
        check_row(row, cases[row["id"]], report["seed"])
    assert {v["sync_staging"] for v in verdicts} == {0, 1}
    for verdict in verdicts:
        mode = verdict["sync_staging"]
        assert verdict["status"] == "TEST_PASS"
        assert verdict["directed_checks"] == (56 if mode else 47)
        assert verdict["case_rows"] == 40
        assert verdict["dense_comparisons"] == vectors["dense_coefficients"] * 2
        assert verdict["sync_staging_checks"] == (9 if mode else 0)
        check_name_list = verdict["sync_staging_check_names"]
        assert len(check_name_list) == (9 if mode else 0)
        check_names = set(check_name_list)
        assert check_names == (STAGING_DIRECTED_CHECKS if mode else set())
    controls = compare_controls(records, report["seed"], cases)
    return {"attempt": attempt.name, "seed": report["seed"], "result_sha256": file_sha(path),
        "source_sha256": report["source_sha256"], "artifact_sha256": report["artifacts_sha256"],
        "case_rows": len(records), "legacy_control_parity": controls,
        "directed_checks_per_mode": [v["directed_checks"] for v in verdicts],
        "sync_staging_checks_per_mode": [v["sync_staging_checks"] for v in verdicts],
        "sync_staging_check_names": [v["sync_staging_check_names"] for v in verdicts],
        "sync_staging_monitor": "one outstanding request owner and exactly one-edge registered response checked every active edge"}


def verify_source_contract(source_sha256):
    wrapper_rel = "fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv"
    sync_rel = "fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv"
    tb_rel = "fpga/experiments/cu66-v91h/tb_pipeline.cpp"
    wrapper = (ROOT / wrapper_rel).read_text()
    sync_source = (ROOT / sync_rel).read_text()
    tb = (ROOT / tb_rel).read_text()
    assert source_sha256[wrapper_rel] == file_sha(ROOT / wrapper_rel)
    assert source_sha256[sync_rel] == file_sha(ROOT / sync_rel)
    assert source_sha256[tb_rel] == file_sha(ROOT / tb_rel)
    assert "parameter integer SYNC_STAGING=1" in wrapper
    assert "generate if(SYNC_STAGING==0) begin: legacy" in wrapper
    assert "end else begin: synchronous" in wrapper
    assert "br88_packet_ingress_sync_v91h" in wrapper
    sync = sync_source.split("module br88_packet_ingress_sync_v91h", 1)[1]
    port_block = sync.split("// One byte write port", 1)[1].split("br88_context context_decoder", 1)[0]
    assert "logic [7:0] memory [0:MAX_PACKET_BYTES-1];" in sync
    assert sync.count("memory[") == 2
    assert "always_ff @(posedge clk) begin" in port_block and port_block.count("memory[") == 2
    assert "if(stage_write) memory[AW'(received)]<=in_data;" in sync
    assert "ram_valid<=stage_read_req;" in sync
    assert "ram_data<=memory[AW'(fetch_address)]; ram_addr<=fetch_address; ram_epoch<=context_epoch;" in sync
    assert "FETCH_WAIT: if(stage_read_rsp)" in sync
    assert "HEADER: begin" in sync and "if((crc^32'hffffffff)!=cached32(42))" in sync
    assert "descriptor_bits[2:0]!=0 && (fetch_bytes[6] & (8'hff >> descriptor_bits[2:0]))!=0" in sync
    assert "state<=raw_mode ? RAW : CONTEXT_START" in sync
    assert "if(stage_read_req) state<=FETCH_WAIT;" in sync
    assert "if(cancelled || context_failure) ram_valid<=0;" in sync
    assert "ram_epoch!=context_epoch || ram_addr!=fetch_address" in sync
    assert not re.search(r"assign\s+[^;]*\bmemory\s*\[", sync)
    assert not re.search(r"always_comb[^;]*\bmemory\s*\[", sync)
    for marker in ("staging one-read owner", "staging response not one edge after request",
                   "staging response ownership", "staging read request bound",
                   "staging synchronous read data", "staging accepted byte write",
                   "staging cache bound", "!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_write",
                   "if(d.stage_cancel){staging_pending=false;return;}"):
        assert marker in tb, marker
    for marker in STAGING_DIRECTED_CHECKS:
        assert f'"{marker}"' in tb, marker
    return {"wrapper_source_sha256": file_sha(ROOT / wrapper_rel),
        "synchronous_ingress_source_sha256": file_sha(ROOT / sync_rel),
        "testbench_source_sha256": file_sha(ROOT / tb_rel),
        "compile_time_parameter_and_legacy_generate_control": True,
        "single_byte_write_and_registered_single_byte_read_in_always_ff": True,
        "no_combinational_or_continuous_backing_array_read_in_sync_branch": True,
        "metadata_follows_header_crc_and_descriptor_validation": True,
        "one_pending_and_one_edge_response_checked_by_integrated_scoreboard": True,
        "epoch_and_cancel_response_ownership_checked_by_integrated_scoreboard": True}


def verify_staging_port_model():
    source = AREA / "staging-port-model.py"
    result_path = AREA / "staging-port-results.json"
    result = read(result_path)
    assert result["schema"] == "cu66-v91h-staging-port-model-v1"
    assert result["source"] == "experiments/python-gamebub-v91h/staging-port-model.py"
    assert result["source_sha256"] == file_sha(source)
    assert result["actual_scenarios"] == result["requested_scenarios"] == 9
    assert result["directed_checks_actual"] == result["directed_checks_requested"] == 6
    assert result["restarts_actual"] == result["restarts_requested"] == 1
    assert result["seed"] == 910438
    bounds = result["bounds"]
    assert bounds["registered_read_latency_edges"] == 1
    assert bounds["read_ports"] == bounds["write_ports"] == 1
    assert bounds["staging_bytes"] == 192 and bounds["header_cache_bytes"] == 46
    coverage = result["actual_event_coverage"]
    for event in ("receive_accept", "receive_hold", "full_receive_before_any_staging_read",
                  "header_crc_validated_after_receive", "descriptor6_read", "descriptor_tail_read",
                  "registered_request_edge_snapshot", "read_write_overlap_excluded", "consumer_hold",
                  "epoch_cancelled_pending_response", "epoch_stale_response_ignored",
                  "restart_after_epoch_cancel", "held_output_stable_during_next_fetch"):
        assert coverage.get(event, 0) > 0, event
    events = result["staging_port_event_counts"]
    assert events["read_requests"] == events["read_responses"] > 0
    assert events["receive_writes"] > 0
    vector_rows = result["vectors"]
    assert {v["kind"] for v in vector_rows} == {"coded", "raw"}
    assert all(v["read_accepts"] == v["read_responses"] > 0 and v["read_edges"] >= v["read_accepts"]
               for v in vector_rows)
    assert all(v["packet_bytes"] <= bounds["staging_bytes"] and v["receive_edges"] >= v["packet_bytes"]
               for v in vector_rows)
    assert events["receive_writes"] == sum(v["packet_bytes"] for v in vector_rows)
    highwater = result["buffer_highwater"]
    assert highwater["staging_address"] < bounds["staging_bytes"]
    assert highwater["header_crc_cache_bytes"] == bounds["header_cache_bytes"] == 46
    assert highwater["descriptor_and_tail_bytes"] == bounds["descriptor_bytes"] + bounds["descriptor_tail_bytes"]
    assert highwater["raw_pair_bytes"] == bounds["raw_pair_bytes"] == 2
    limits = result["limitations"]
    assert any("does not establish a Vivado RAM primitive" in item for item in limits)
    return {"source": result["source"], "source_sha256": result["source_sha256"],
        "result_sha256": file_sha(result_path), "seed": result["seed"],
        "scenarios": result["actual_scenarios"], "directed_checks": result["directed_checks_actual"],
        "restarts": result["restarts_actual"], "bounds": bounds,
        "buffer_highwater": highwater, "event_coverage": coverage, "limitations": limits,
        "rtl_equivalence_claimed": False, "bram_fit_or_timing_claimed": False}


def main():
    vectors, cases = verify_frozen_vectors()
    port_model = verify_staging_port_model()
    public_path = RTL / "pipeline-results.json"
    public = read(public_path)
    assert public["status"] == PASS
    selected_path = ROOT / public["selected_report"]
    selected = read(selected_path)
    assert public == dict(selected, selected_report=public["selected_report"])
    current_sources = public["source_sha256"]
    attempts_by_seed = {}
    for path in RTL.glob("pipeline-attempts/*/results.json"):
        report = read(path)
        if report.get("status") == PASS and report.get("source_sha256") == current_sources:
            attempts_by_seed[report.get("seed")] = path
    assert set(attempts_by_seed) == set(SEEDS) and selected_path in attempts_by_seed.values()
    source_contract = verify_source_contract(current_sources)
    audited = [verify_attempt(path, cases, vectors) for _, path in sorted(attempts_by_seed.items())]
    audit = {"schema": "cu66-v91h-independent-sync-staging-audit-v1",
        "status": "PASS_FROZEN_V88_GOLDENS_V91G2_LEGACY_CONTROL_AND_SYNC_INGRESS",
        "scope": "Independent V88 packet decode and packed-image reconstruction over the frozen 20-case V91e fixture. Audits both SYNC_STAGING compile-time modes at seeds 910432/910433, exact V91g2 tile-overlap=1 legacy parity, synchronous registered packet ingress function/traffic invariance, source/artifact/tool/command pins, integrated directed checks, and public selected-copy identity. Simulation evidence only; no BRAM inference, physical timing, full-frame publication, hardware or fps claim.",
        "parent_commit": selected.get("source_revision"),
        "audit_source_sha256": {"experiments/python-gamebub-v91h/verify_results.py": file_sha(Path(__file__).resolve())},
        "vectors": vectors, "audited_attempts": audited, "staging_port_model": port_model,
        "source_contract": source_contract,
        "contract": {"compile_time_parameter": "SYNC_STAGING", "legacy_mode": 0, "registered_packet_stage": 1,
            "cases_per_mode_per_seed": 40, "total_rows_per_seed": 80, "legacy_metrics": list(METRICS),
            "memory_profiles": [0, 1], "seeds": list(SEEDS),
            "fixed_parameters": {"serial_clear": 0, "write_overlap": 1, "read_prefetch": 1, "tile_overlap": 1},
            "sync_mode_allowed_differences": ["cycle counts", "RAW read latency", "timestamps", "overlapping wait counters"],
            "sync_functional_invariants": ["exact dense coefficient bytes/hash", "exact packed scratch bytes/hash", "error code", "canonical read/write lines exactly once", "request service hash"]},
        "evidence_limits": {"source_proves_registered_read_stage": True,
            "source_proves_no_asynchronous_array_read_in_sync_branch": True,
            "physical_bram_fit_proven": False, "achieved_clock_proven": False,
            "full_frame_validated_decode_under_10ms_proven": False, "hardware_30fps_proven": False,
            "cycle_overhead_is_not_assumed_to_be_an_optimization": True}}
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print("V91H_INDEPENDENT_AUDIT_PASS")


if __name__ == "__main__":
    main()
