#!/usr/bin/env python3
"""Independent V91j integer transform and integration trace audit.

The expected math below is rebuilt from native constants and V91i2 source
coefficient bytes.  It deliberately does not import model.py or trust its
calculated dq/residual fields.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import struct
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
VECTORS = AREA / "vectors"
CASE_TSV = ROOT / "experiments/python-gamebub-v91i2/vectors/cases.tsv"
CASE_MANIFEST = ROOT / "experiments/python-gamebub-v91i2/vectors/manifest.json"
NATIVE = ROOT / "experiments/cu66-native-v69/generated_constants.hpp"
INVERSE_RTL = ROOT / "fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv"
PIPELINE_RTL = ROOT / "fpga/experiments/cu66-v91j/cs88_pipeline_v91j.sv"
NATIVE_IDS = {"actual_001", "actual_006", "actual_043", "actual_031",
              "actual_006_varied_qcache", "actual_001_bad_third_inner_crc"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_native_array(name: str, dims: tuple[int, ...]) -> list[int]:
    src = NATIVE.read_text()
    dimtxt = r"\[" + r"\]\[".join(map(str, dims)) + r"\]"
    match = re.search(rf"\b{name}{dimtxt}=\{{(.*?)\}};", src, re.S)
    assert match, f"native constant array not found: {name}{dims}"
    values = [int(v) for v in re.findall(r"-?\d+", match.group(1))]
    count = 1
    for d in dims:
        count *= d
    assert len(values) == count, (name, len(values), count)
    return values


def constants():
    flat = parse_native_array("DCT", (8, 8))
    dct = [flat[r * 8:(r + 1) * 8] for r in range(8)]
    qflat = parse_native_array("QTABLES", (2, 3, 8, 8))
    qt = [[[qflat[((pc * 3 + sc) * 8 + y) * 8:
                   ((pc * 3 + sc) * 8 + y + 1) * 8]
            for y in range(8)] for sc in range(3)] for pc in range(2)]
    return dct, qt


def dequant(coeff: list[int], plane: int, scale: int, qt) -> tuple[list[int], bool]:
    bad = scale not in (0, 1, 2) or len(coeff) != 64 or any(v < -2048 or v > 2048 for v in coeff)
    if bad:
        return [0] * 64, True
    q = qt[0 if plane == 0 else 1][scale]
    out = [coeff[y * 8 + x] * q[y][x] for y in range(8) for x in range(8)]
    assert all(-(1 << 19) <= v < (1 << 19) for v in out)
    return out, False


def q14_round(total: int) -> int:
    # Python // is explicitly floor division for negative values, matching >>>.
    return (total + 8192) // 16384


def idct(dq: list[int], dct) -> list[int]:
    mid = [[q14_round(sum(dq[y * 8 + k] * dct[k][x] for k in range(8)))
            for x in range(8)] for y in range(8)]
    residual = [q14_round(sum(dct[k][y] * mid[k][x] for k in range(8)))
                for y in range(8) for x in range(8)]
    assert all(-(1 << 23) <= v < (1 << 23) for v in residual)
    return residual


def signed32(values: list[int]) -> bytes:
    return b"".join(struct.pack("<i", v) for v in values)


def parse_source_cases():
    csv.field_size_limit(100_000_000)
    names = ("id", "expected_error", "packet_hex", "ref_valid", "ref_fid",
             "ref_generation", "qcache_valid", "cache_fid", "cache_generation",
             "prior_qscale_hex", "current_qscale_hex", "operations_hex",
             "denseY_hex", "denseCb_hex", "denseCr_hex")
    with CASE_TSV.open(newline="", encoding="ascii") as f:
        rows = [dict(zip(names, row, strict=True)) for row in csv.reader(f, delimiter="\t")]
    assert len(rows) == 11
    return {r["id"]: r for r in rows}


def source_expected(case: dict, plane: int, tile: int, dct, qt):
    dense_name = ("denseY_hex", "denseCb_hex", "denseCr_hex")[plane]
    dense_text = case[dense_name]
    if dense_text == "-":
        return None
    dense = bytes.fromhex(dense_text)
    ops = bytes.fromhex(case["operations_hex"])
    base, count = ((0, 5400), (5400, 1350), (6750, 1350))[plane]
    if ops[base + tile] != 2:
        return None
    active = [t for t in range(count) if ops[base + t] == 2]
    ordinal = active.index(tile)
    coeff_raw = dense[ordinal * 128:(ordinal + 1) * 128]
    assert len(coeff_raw) == 128
    coeff = list(struct.unpack("<64h", coeff_raw))
    cell = (((tile // 90) // 2) * 45 + (tile % 90) // 2) if plane == 0 else tile
    scale = bytes.fromhex(case["current_qscale_hex"])[cell]
    dq, bad = dequant(coeff, plane, scale, qt)
    assert not bad, (case["id"], plane, tile, scale)
    residual = idct(dq, dct)
    return (ordinal, cell, scale, coeff_raw, signed32(dq), signed32(residual))


def verify_golden_rows(dct, qt):
    manifest = json.loads((VECTORS / "manifest.json").read_text())
    model = json.loads((AREA / "model-results.json").read_text())
    assert sha(NATIVE.read_bytes()) == manifest["source_pins"]["frozen_generated_constants_sha256"]
    assert sha(CASE_TSV.read_bytes()) == manifest["source_pins"]["v91i2_cases_tsv_sha256"]
    assert sha(CASE_MANIFEST.read_bytes()) == manifest["source_pins"]["v91i2_manifest_sha256"]
    path = VECTORS / "transform_tiles.tsv.gz"
    assert sha(path.read_bytes()) == manifest["transform_tiles"]["sha256"]
    raw_hash = hashlib.sha256()
    rows = 0
    source_cases = parse_source_cases()
    observed = set()
    with gzip.open(path, "rt", encoding="ascii", newline="") as f:
        for line in f:
            line = line.rstrip("\n")
            fields = line.split("\t")
            assert len(fields) == 9
            cid, plane_s, ordinal_s, tile_s, cell_s, scale_s, coeffhex, dqhex, reshex = fields
            plane, ordinal, tile, cell, scale = map(int, (plane_s, ordinal_s, tile_s, cell_s, scale_s))
            assert cid in NATIVE_IDS and cid in source_cases
            expected = source_expected(source_cases[cid], plane, tile, dct, qt)
            assert expected is not None, (cid, plane, tile, "not active in source packet")
            eord, ecell, escale, ecoeff, edq, eres = expected
            assert (ordinal, cell, scale) == (eord, ecell, escale)
            assert bytes.fromhex(coeffhex) == ecoeff, (cid, plane, tile, "source coefficient bytes")
            assert bytes.fromhex(dqhex) == edq, (cid, plane, tile, "independent DQ")
            assert bytes.fromhex(reshex) == eres, (cid, plane, tile, "independent residual")
            observed.add((cid, plane, tile))
            raw_hash.update((line + "\n").encode("ascii"))
            rows += 1
    assert rows == manifest["transform_tiles"]["rows"] == model["tile_rows"]
    assert raw_hash.hexdigest() == manifest["transform_tiles"]["raw_rows_sha256"]
    assert len(observed) == rows
    # Exact source placement coverage, with only the failed late-CRC plane unavailable.
    expected_keys = set()
    for cid in NATIVE_IDS:
        case = source_cases[cid]
        for plane, (base, count) in enumerate(((0, 5400), (5400, 1350), (6750, 1350))):
            if case[("denseY_hex", "denseCb_hex", "denseCr_hex")[plane]] == "-":
                continue
            ops = bytes.fromhex(case["operations_hex"])
            expected_keys.update((cid, plane, t) for t in range(count) if ops[base + t] == 2)
    assert observed == expected_keys, (len(observed), len(expected_keys))
    return {"golden_rows": rows, "golden_rows_sha256": raw_hash.hexdigest(),
            "source_coefficients_reconciled": len(observed)}


def verify_boundary(dct, qt):
    path = VECTORS / "boundary.tsv"
    manifest = json.loads((VECTORS / "manifest.json").read_text())
    assert sha(path.read_bytes()) == manifest["boundary"]["sha256"]
    seen = set()
    counts = {"valid": 0, "invalid": 0}
    with path.open(encoding="ascii") as f:
        for rawline in f:
            line = rawline.rstrip("\n")
            fields = line.split("\t")
            assert len(fields) == 7
            cid, err_s, plane_s, scale_s, chex, dhex, rhex = fields
            err, plane, scale = int(err_s), int(plane_s), int(scale_s)
            coeff = list(struct.unpack("<64h", bytes.fromhex(chex)))
            dq, bad = dequant(coeff, plane, scale, qt)
            # Component boundary code 3 is the adapter's coefficient/qcode
            # validation code; it is truth-valued for this independent oracle.
            assert (err != 0) == bad, (cid, "bad flag")
            if bad:
                assert err == 3, (cid, "expected adapter qcode/coefficient error 3")
                assert dhex == "-" and rhex == "-", (cid, "invalid output encoding")
                counts["invalid"] += 1
            else:
                residual = idct(dq, dct)
                assert bytes.fromhex(dhex) == signed32(dq), (cid, "DQ")
                assert bytes.fromhex(rhex) == signed32(residual), (cid, "IDCT")
                counts["valid"] += 1
            seen.add(cid)
    assert counts["valid"] >= 42
    assert any("dc_pos_limit" in x for x in seen) and any("ac_neg_limit" in x for x in seen)
    assert any("rounding_signed_extremes" in x for x in seen)
    # Required negative-domain validation cases must both be represented.
    assert any("invalid_coeff_-2049" in x for x in seen)
    assert any("invalid_qcode3" in x for x in seen)
    return {"boundary_cases": len(seen), "boundary_valid": counts["valid"],
            "boundary_invalid": counts["invalid"]}


def fnv64(data: bytes) -> int:
    h = 1469598103934665603
    for byte in data:
        h = ((h ^ byte) * 1099511628211) & 0xffffffffffffffff
    return h


def golden_rows():
    rows = {}
    sequence = defaultdict(list)
    with gzip.open(VECTORS / "transform_tiles.tsv.gz", "rt", encoding="ascii") as f:
        for line in f:
            cid, plane, block, tile, cell, scale, coeff, dq, residual = line.rstrip("\n").split("\t")
            key = (cid, int(plane), int(block))
            row = {"id": cid, "plane": int(plane), "block": int(block), "tile": int(tile),
                   "qcell": int(cell), "qscale": int(scale), "coeff": bytes.fromhex(coeff),
                   "dq": bytes.fromhex(dq), "residual": bytes.fromhex(residual)}
            assert key not in rows
            rows[key] = row
            sequence[cid].append(row)
    return rows, sequence


def verify_transform_trace(events, expected_rows, expected_sequence):
    grouped = defaultdict(dict)
    sequences = defaultdict(list)
    owner_registry = {}
    frame_tile_tokens = defaultdict(set)
    late_ids = {row["id"] for row in parse_source_cases().values() if int(row["expected_error"]) == 147}
    for e in events:
        assert e.get("type") == "transform", e
        stage, cid = e["stage"], e["id"]
        assert stage in ("assemble", "dequant", "residual")
        profile, plane, block = int(e["memory_profile"]), int(e["plane"]), int(e["block"])
        key = (cid, plane, block)
        assert key in expected_rows, ("unexpected trace tile", key)
        g = expected_rows[key]
        assert (int(e["tile"]), int(e["qcell"]), int(e["qscale"])) == (g["tile"], g["qcell"], g["qscale"])
        assert int(e["frame_epoch"]) > 0 and int(e["child_epoch"]) > 0 and int(e["token"]) > 0
        owner = (int(e["frame_epoch"]), int(e["token"]))
        owner_tile = (cid, profile, plane, block, int(e["child_epoch"]))
        assert owner_registry.setdefault(owner, owner_tile) == owner_tile, ("opaque owner reused", owner, owner_tile)
        if stage == "assemble":
            assert int(e["token"]) not in frame_tile_tokens[int(e["frame_epoch"])], ("duplicate frame token", owner)
            frame_tile_tokens[int(e["frame_epoch"])].add(int(e["token"]))
        assert int(e["samples"]) > 0 and int(e["samples"]) <= 64
        sample_count = int(e["samples"])
        if stage == "assemble":
            data = g["coeff"]
            assert sample_count == 64 and e["complete"] is True
        elif stage == "dequant":
            data = g["dq"]
            assert sample_count == 64 and e["complete"] is True
        else:
            data = g["residual"][:sample_count * 4]
            assert bool(e["complete"]) == (sample_count == 64)
            sequences[(cid, profile)].append((plane, block, sample_count, bool(e["complete"])))
        assert int(e["value_hash"]) == fnv64(data[:sample_count * 4] if stage == "dequant" else data)
        group_key = (cid, profile, plane, block)
        assert stage not in grouped[group_key], ("duplicate stage", group_key, stage)
        grouped[group_key][stage] = e

    # Each accepted/assembled row has exactly one assembly, DQ and residual event
    # in complete frames. The intentional late-CRC case can only expose a prefix.
    ids = {key[0] for key in expected_rows}
    profiles = {int(e["memory_profile"]) for e in events}
    assert profiles == {0, 1}
    for cid in ids:
        for profile in profiles:
            actual = sequences[(cid, profile)]
            wanted_rows = expected_sequence[cid]
            wanted = [(r["plane"], r["block"], 64, True) for r in wanted_rows]
            if cid in late_ids:
                assert actual == wanted[:len(actual)] or (
                    len(actual) > 0 and actual[:-1] == wanted[:len(actual)-1] and
                    actual[-1][:2] == wanted[len(actual)-1][:2] and
                    0 < actual[-1][2] < 64 and actual[-1][3] is False), (cid, profile, actual[-3:])
            else:
                assert actual == wanted, (cid, profile, len(actual), len(wanted))
            for r in wanted_rows:
                key = (cid, profile, r["plane"], r["block"])
                got = grouped.get(key, {})
                assert "assemble" in got and "dequant" in got, ("missing assembly/DQ", key)
                if cid not in late_ids or (r["plane"], r["block"]) in actual_keys(actual):
                    assert "residual" in got, ("missing residual", key)
                # Every event for one opaque tile owner must carry the same identity tuple.
                identities = {(int(ev["token"]), int(ev["frame_epoch"]), int(ev["child_epoch"]))
                              for ev in got.values()}
                assert len(identities) == 1, ("owner metadata changed", key)
    for epoch, tokens in frame_tile_tokens.items():
        ordered = sorted(tokens)
        assert ordered == list(range(1, len(ordered) + 1)), ("per-frame token sequence", epoch, ordered[:4])
    return {"trace_events": len(events), "transform_tiles": len(grouped),
            "trace_profiles": sorted(profiles), "late_crc_ids": sorted(late_ids),
            "opaque_owner_keys": len(owner_registry), "frame_epochs": len(frame_tile_tokens)}


def actual_keys(seq):
    return {(plane, block) for plane, block, _samples, _complete in seq}


def verify_static_contract():
    inverse = INVERSE_RTL.read_text()
    pipeline = PIPELINE_RTL.read_text()
    checks = {
        "local_error_codes_1_to_7": all(f"input_fault={i};" in inverse for i in (1, 2, 3, 4, 7))
            and "fail(5)" in inverse and "fail(6)" in inverse,
        "opaque_token_scoped_per_frame": "if(reset||start||cancel)begin" in inverse and
            "next_token<=0;" in inverse and "next_token<=next_token+1" in inverse,
        "reset_abort_transform_flush": ".abort_i(start||cancel||error!=0)" in inverse and
            ".abort_frame(start||cancel||error!=0)" in inverse,
        "bank_freed_only_after_last_residual_accept":
            "if(emit_index==63)begin\n                            bank_state[math_bank]<=FREE" in inverse,
        "transform_error_remapped_c0_namespace": "(8'hc0|inverse_error):coefficient_error" in pipeline,
        "base_error_preserved": "error=inverse_error!=0?(8'hc0|inverse_error):coefficient_error" in pipeline,
        "frame_done_waits_both_paths_and_clean_status": "coefficient_done&&inverse_done&&error==0" in pipeline,
        "base_abort_on_transform_error": "abort_packet||(inverse_error!=0&&!inverse_fault_ack)" in pipeline,
    }
    assert all(checks.values()), checks
    return checks


def audit(args, write_output=True):
    dct, qt = constants()
    result = {"schema": "cu66-v91j-independent-math-integration-audit-v1",
              "status": "PASS_MATH_ONLY", "source_sha256": {
                  str(NATIVE.relative_to(ROOT)): sha(NATIVE.read_bytes()),
                  str(CASE_TSV.relative_to(ROOT)): sha(CASE_TSV.read_bytes()),
                  str(CASE_MANIFEST.relative_to(ROOT)): sha(CASE_MANIFEST.read_bytes()),
                  str(INVERSE_RTL.relative_to(ROOT)): sha(INVERSE_RTL.read_bytes()),
                  str(PIPELINE_RTL.relative_to(ROOT)): sha(PIPELINE_RTL.read_bytes()),
                  str((AREA / "verify_results.py").relative_to(ROOT)): sha((AREA / "verify_results.py").read_bytes())},
              "math": verify_golden_rows(dct, qt), "boundary": verify_boundary(dct, qt),
              "static_contract": verify_static_contract(),
              "integration": {"status": "NOT_CHECKED", "scope": "golden math only"}}
    if args.attempt:
        report_path = Path(args.attempt).resolve()
        report = json.loads(report_path.read_text())
        attempt_root = report_path.parent
        assert report["schema"] == "cu66-v91j-integrated-inverse-rtl-v1"
        assert report["status"] == "PASS_INTEGRATED_DEQUANT_AND_IDCT_RESIDUALS"
        subprocess.run(["git", "merge-base", "--is-ancestor", "dbccd7cddcf0d8fd3c2750db326493d7a051313d", report["source_revision"]], cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert all(command.get("exit_code") == 0 for command in report["commands"])
        compile_commands = [command["argv"] for command in report["commands"] if "--build" in command["argv"]]
        assert len(compile_commands) == 2
        for argv in compile_commands:
            assert "--assert" in argv and "-Wall" in argv and argv[argv.index("-j") + 1] == "2"
        tool_version_log = (attempt_root / "tool-version.log").read_text()
        assert "5.020" in tool_version_log
        assert report["hardware_distinct_30fps_proven"] is False
        assert report["full_frame_decode_under10ms_proven"] is False
        assert report["full_frame_publication_timestamp"] is None
        for rel, digest in report["source_sha256"].items():
            snap = attempt_root / "sources" / rel
            assert snap.is_file() and sha(snap.read_bytes()) == digest, ("source snapshot hash", rel)
            live = ROOT / rel
            assert live.is_file() and sha(live.read_bytes()) == digest, ("live source hash", rel)
        for rel, digest in report["vectors_sha256"].items():
            retained = attempt_root / "vectors" / rel
            current = VECTORS / rel
            assert retained.is_file() and sha(retained.read_bytes()) == digest, ("retained vector hash", rel)
            assert current.is_file() and sha(current.read_bytes()) == digest, ("current vector hash", rel)
        copied_cases = attempt_root / report["case_input"]["path"]
        assert sha(copied_cases.read_bytes()) == report["case_input"]["sha256"] == sha(CASE_TSV.read_bytes())
        for rel, digest in report["artifacts_sha256"].items():
            artifact = attempt_root / rel
            assert artifact.is_file() and sha(artifact.read_bytes()) == digest, ("attempt artifact hash", rel)
        canonical = gzip.decompress((VECTORS / "transform_tiles.tsv.gz").read_bytes())
        assert report["input_expansion"]["uncompressed_sha256"] == sha(canonical)
        assert report["input_expansion"]["compressed_sha256"] == sha((VECTORS / "transform_tiles.tsv.gz").read_bytes())
        trace_spec = report.get("transform_trace")
        assert trace_spec and trace_spec.get("path"), "attempt lacks transform_trace receipt"
        trace_path = (report_path.parent / trace_spec["path"]).resolve()
        compressed = trace_path.read_bytes()
        assert sha(compressed) == trace_spec["gzip_sha256"]
        raw_trace = gzip.decompress(compressed)
        assert sha(raw_trace) == trace_spec["jsonl_sha256"]
        assert len(raw_trace.splitlines()) == trace_spec["records"]
        with gzip.open(trace_path, "rt", encoding="ascii") as f:
            events = [json.loads(line) for line in f if line.strip()]
        expected, sequence = golden_rows()
        trace_summary = verify_transform_trace(events, expected, sequence)
        checks = set(report["verdict"]["directed_check_names"])
        inverse_verdict = report["inverse_verdict"]
        required = {"warm_reset_accepted_write_drain_blocks_start", "abort_accepted_write_drain_blocks_start",
                    "abort_held_residual", "abort_owned_idct_job", "good_retry_after_failed_frame_without_reset",
                    "all_coefficients_and_mapped_tuple_fields_exact"}
        assert required <= checks, sorted(required - checks)
        inverse_checks = set(inverse_verdict["directed_check_names"])
        required_inverse = {"coefficient_order_rejected", "tile_metadata_immutable",
                            "partial_tile_completion_rejected", "reset_partial_tile", "abort_partial_tile",
                            "two_bank_backpressure_and_cancel", "clean_retry_after_cancel_and_error"}
        required_inverse.update(f"{op}_math_state_{state}" for op in ("reset", "abort") for state in range(1, 5))
        assert required_inverse <= inverse_checks, sorted(required_inverse - inverse_checks)
        assert report["verdict"]["assembly_comparisons"] == 2 * len(expected) * 64
        assert report["verdict"]["dequant_comparisons"] == 2 * len(expected) * 64
        assert report["verdict"]["residual_comparisons"] > 0
        assert report["input_expansion"]["rows"] == len(expected) == 31706
        assert report["vectors_sha256"]["transform_tiles.tsv.gz"] == sha((VECTORS / "transform_tiles.tsv.gz").read_bytes())
        assert report["vectors_sha256"]["boundary.tsv"] == sha((VECTORS / "boundary.tsv").read_bytes())
        assert inverse_verdict["status"] == "TEST_PASS" and inverse_verdict["boundary_cases"] == 48
        simulation_path = report_path.parent / "simulation.jsonl"
        assert sha(simulation_path.read_bytes()) == report["artifacts_sha256"]["simulation.jsonl"]
        sim_rows = [json.loads(line) for line in simulation_path.read_text().splitlines()]
        sim_cases = [row for row in sim_rows if row.get("type") == "case"]
        case_sources = parse_source_cases()
        assert len(sim_cases) == 22
        assert {(row["id"], int(row["memory_profile"])) for row in sim_cases} == {
            (cid, profile) for cid in case_sources for profile in (0, 1)}
        assert all(int(row["error"]) == int(case_sources[row["id"]]["expected_error"])
                   for row in sim_cases)
        late = [row for row in sim_rows if row.get("type") == "case" and row.get("error") == 147]
        assert len(late) == 2 and all(row["done_cycle"] == 0 for row in late)
        completed = [row for row in sim_rows if row.get("type") == "case" and row.get("error") == 0]
        assert len(completed) == 12
        assert all(row["done_cycle"] > 0 and row["pending_drain"] is False and
                   row["full_frame_publication"] is False and row["requests"] == row["acks"] and
                   row["inverse"]["max_owned_banks"] <= 2 for row in completed)
        assert sum(row["inverse"]["assembly_during_math_inputs"] for row in completed) > 0
        inverse_path = report_path.parent / "inverse.jsonl"
        assert sha(inverse_path.read_bytes()) == report["artifacts_sha256"]["inverse.jsonl"]
        inverse_rows = [json.loads(line) for line in inverse_path.read_text().splitlines()]
        boundary_source = list(csv.reader((VECTORS / "boundary.tsv").open(encoding="ascii"), delimiter="\t"))
        boundary_expected = {row[0]: int(row[1]) for row in boundary_source}
        boundary_cases = [row for row in inverse_rows if row.get("type") == "case"]
        boundary_observed = {row["id"]: int(row["error"]) for row in boundary_cases}
        assert boundary_observed == boundary_expected
        assert all(err == 3 for cid, err in boundary_observed.items() if cid.startswith("invalid_"))
        for row in boundary_cases:
            if boundary_expected[row["id"]] == 0:
                assert row["assembly_samples"] == row["dq_samples"] == row["residual_samples"] == 64
            else:
                assert row["assembly_samples"] == row["dq_samples"] == row["residual_samples"] == 0
            assert row["max_owned_banks"] <= 2
        result["integration"] = {"status": "PASS_TRACE_AND_CONTROL", **trace_summary,
                                  "transform_trace_gzip_sha256": trace_spec["gzip_sha256"],
                                  "transform_trace_jsonl_sha256": trace_spec["jsonl_sha256"],
                                  "directed_checks": sorted(checks), "inverse_directed_checks": sorted(inverse_checks),
                                  "late_crc_cases_no_done": len(late),
                                  "positive_assemble_while_math_count": sum(row["inverse"]["assembly_during_math_inputs"] for row in completed),
                                  "inverse_verdict": inverse_verdict}
        result["status"] = "PASS_INDEPENDENT_MATH_AND_INTEGRATION"
        result["attempt_seed"] = report["seed"]
    if write_output:
        out = AREA / "audit.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempt", help="audit one retained integrated V91j report (default audits both final seeds)")
    args = ap.parse_args()
    if args.attempt:
        audit(args)
        return
    reports = sorted((ROOT / "fpga/experiments/cu66-v91j/pipeline-attempts").glob("*/results.json"),
                     key=lambda p: p.parent.name)
    selected = {}
    for report_path in reports:
        try:
            report = json.loads(report_path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if report.get("status") != "PASS_INTEGRATED_DEQUANT_AND_IDCT_RESIDUALS":
            continue
        seed = report.get("seed")
        if seed not in (911401, 911402):
            continue
        # Current source/vector pins filter out passes superseded by later edits.
        if any(not (ROOT / rel).is_file() or sha((ROOT / rel).read_bytes()) != digest
               for rel, digest in report.get("source_sha256", {}).items()):
            continue
        if any(not (VECTORS / rel).is_file() or sha((VECTORS / rel).read_bytes()) != digest
               for rel, digest in report.get("vectors_sha256", {}).items()):
            continue
        selected[seed] = report_path
    assert set(selected) == {911401, 911402}, {seed: str(path) for seed, path in selected.items()}
    results = []
    for seed in (911401, 911402):
        args.attempt = str(selected[seed])
        results.append(audit(args, write_output=False))
    assert results[0]["math"] == results[1]["math"]
    result = dict(results[0])
    result.pop("integration", None)
    result["attempts"] = []
    for seed, path, per_attempt in zip((911401, 911402), (selected[911401], selected[911402]), results):
        result["attempts"].append({"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()),
                                   "seed": seed, "integration": per_attempt["integration"]})
    result.pop("attempt_seed", None)
    result["status"] = "PASS_INDEPENDENT_MATH_AND_BOTH_INTEGRATION_SEEDS"
    out = AREA / "audit.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
