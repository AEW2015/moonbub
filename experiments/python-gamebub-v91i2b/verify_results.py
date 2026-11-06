#!/usr/bin/env python3
"""Independent audit of V91i2b refill ownership and paired V91i2a controls."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
RTL = ROOT / "fpga/experiments/cu66-v91i2b"
OLD = ROOT / "fpga/experiments/cu66-v91i2"
VECTORS = ROOT / "experiments/python-gamebub-v91i2/vectors"
SEEDS = (911201, 911202)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def trace(path: Path, receipt: dict) -> list[dict]:
    packed = path.read_bytes()
    assert sha(packed) == receipt["gzip_sha256"]
    raw = gzip.decompress(packed)
    assert sha(raw) == receipt["jsonl_sha256"]
    rows = [json.loads(line) for line in raw.splitlines() if line]
    assert len(rows) == receipt["records"]
    return rows


def get_expected_cases():
    """Use the frozen independent V91i2 parser and V88 entropy oracle."""
    frozen_path = ROOT / "experiments/python-gamebub-v91i2/verify_results.py"
    spec = importlib.util.spec_from_file_location("frozen_v91i2_independent_auditor", frozen_path)
    frozen = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(frozen)
    codec_path = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
    codec_spec = importlib.util.spec_from_file_location("frozen_br88_strict_reader", codec_path)
    frozen.BR88 = importlib.util.module_from_spec(codec_spec)
    assert codec_spec and codec_spec.loader
    codec_spec.loader.exec_module(frozen.BR88)
    cases = frozen.read_cases()
    manifest = load(VECTORS / "manifest.json")
    manifest_by_id = {row["id"]: row for row in manifest["cases"]}
    expected = {}
    for row in cases:
        ident = row["id"]
        if row["expected_error"] not in (0, 147):
            expected[ident] = {"error": row["expected_error"], "tuples": [], "refill_bytes": 0}
            continue
        packet = bytes.fromhex(row["packet_hex"])
        parsed = frozen.parse_packet(
            packet, bytes.fromhex(row["operations_hex"]),
            bytes.fromhex(row["prior_qscale_hex"]) if row["prior_qscale_hex"] != "-" else bytes(1350),
            bytes.fromhex(row["current_qscale_hex"]), row["ref_valid"], row["ref_fid"],
            row["ref_generation"], row["qcache_valid"], row["cache_fid"],
            row["cache_generation"], frozen.frozen_hidden(),
            decode_planes=2 if row["expected_error"] == 147 else 3)
        tuples = []
        plane_limit = 2 if row["expected_error"] == 147 else 3
        for plane, p in enumerate(parsed["planes"][:plane_limit]):
            dense_hex = row[f"dense{'Y' if plane == 0 else 'Cb' if plane == 1 else 'Cr'}_hex"]
            raw = bytes.fromhex(dense_hex) if dense_hex not in ("", "-") else b""
            assert raw == p["dense"]
            for ordinal, tile in enumerate(p["tiles"]):
                block = raw[ordinal * 128:(ordinal + 1) * 128]
                tuples.append({"plane": plane, "block": ordinal, "tile": tile,
                               "qcell": frozen.cell_for(plane, tile),
                               "qscale": parsed["qscales"][frozen.cell_for(plane, tile)],
                               "coefficient_count": 64,
                               "coefficient_hash": frozen.fnv_coefficient_block(block)})
        origin = manifest_by_id[ident]
        assert sha(packet) == origin["packet_sha256"]
        expected[ident] = {"error": row["expected_error"], "tuples": tuples,
                           "refill_bytes": sum(p["span"]["length"] for p in parsed["planes"] if p["span"]),
                           "fid": origin["fid"], "packet_sha256": sha(packet)}
    return cases, expected, frozen


def main() -> None:
    cases, expected, frozen = get_expected_cases()
    vector_manifest = load(VECTORS / "manifest.json")
    vector_hashes = {"cases.tsv": sha((VECTORS / "cases.tsv").read_bytes()),
                     "manifest.json": sha((VECTORS / "manifest.json").read_bytes())}
    assert vector_hashes["cases.tsv"] == "54fe65f22dd8d0fc45b1fd0444e12632e1d800269705371f677aae5e6b8b5abc"
    assert vector_hashes["manifest.json"] == "dc8a7e378f09e25e0b78795b6042eca0c6a957765c1352fa3fe4b373bf70b4e0"
    v91i2_verifier = ROOT / "experiments/python-gamebub-v91i2/verify_results.py"
    codec = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
    old_audit = load(ROOT / "experiments/python-gamebub-v91i2/audit.json")
    assert old_audit["independent_parser"] == "experiments/python-gamebub-v91i2/verify_results.py"

    selected = {}
    for path in sorted((RTL / "pipeline-attempts").glob("*/results.json")):
        report = load(path)
        if report.get("schema") == "cu66-v91i2b-refill-overlap-rtl-v1" and report.get("status") == "PASS_BOUNDED_REFILL_OVERLAP_WITH_EXACT_CONTROL" and report.get("seed") in SEEDS:
            selected[report["seed"]] = path
    assert set(selected) == set(SEEDS), f"need final attempts for both seeds; got {sorted(selected)}"

    old_summary = load(ROOT / "experiments/python-gamebub-v91i2/summary.json")
    old_by_seed = {row["seed"]: row for row in old_summary["retained_rtl_attempts"]}
    all_results = []
    cycle_comparisons = []
    aggregate_queue_pops = []
    tuple_total = 0
    for seed in SEEDS:
        path = selected[seed]
        report = load(path)
        for name, digest in report["source_sha256"].items():
            assert sha((ROOT / name).read_bytes()) == digest, f"source drift: {name}"
        for name, digest in report["vectors_sha256"].items():
            assert sha((path.parent / "vectors" / name).read_bytes()) == digest, f"vector drift: {name}"
        for name, digest in report["artifacts_sha256"].items():
            assert sha((path.parent / name).read_bytes()) == digest, f"artifact drift: {name}"
        assert report["baseline_control"]["status"] == "PASS_EXACT_FROZEN_CONTROL"
        assert report["baseline_control"]["exact_ordered_tile_rows"] == 63412

        mode_rows = {}
        for mode, label in ((0, "serial"), (1, "overlap")):
            raw_path = path.parent / f"simulation-{label}.jsonl"
            raw_hash = report["artifacts_sha256"][raw_path.name]
            assert sha(raw_path.read_bytes()) == raw_hash
            parsed_rows = [json.loads(line) for line in raw_path.read_text().splitlines() if line]
            cases_rows = [row for row in parsed_rows if row.get("type") == "case"]
            verdicts = [row for row in parsed_rows if row.get("type") == "verdict"]
            assert len(cases_rows) == 22 and len(verdicts) == 1
            assert verdicts[0]["status"] == "TEST_PASS" and verdicts[0]["seed"] == seed
            assert verdicts[0]["refill_overlap"] == mode
            required_directed = {
                "abort_accepted_write_drain_blocks_start", "warm_reset_accepted_write_drain_blocks_start",
                "abort_held_mapped_coefficient", "good_retry_after_failed_frame_without_reset",
                "partial_cache_load_abort_releases_owner", "one_shot_cache_requires_fresh_preload",
                "zero_frame_epoch_rejected", "snapshot_inputs_latched_every_case",
                "serial_cache_tag_latched_first_byte", "all_coefficients_and_mapped_tuple_fields_exact",
            }
            if mode:
                required_directed |= {"abort_queued_and_pending_refill", "warm_reset_queued_and_pending_refill"}
            directed_rows = [row for row in parsed_rows if row.get("type") == "directed"]
            assert {row["name"] for row in directed_rows} == required_directed
            assert len(directed_rows) == len(required_directed) and all(row["status"] == "PASS" for row in directed_rows)
            assert verdicts[0]["directed_checks"] == len(required_directed)
            assert set(verdicts[0]["directed_check_names"]) == required_directed
            by_key = {(row["id"], int(row["memory_profile"])): row for row in cases_rows}
            assert len(by_key) == 22
            mode_rows[label] = by_key

        # Independently reconcile all user-visible coefficient tuples.
        serial_events = trace(path.parent / "tile-events-serial.jsonl.gz", report["tile_traces"]["serial"])
        overlap_events = trace(path.parent / "tile-events-overlap.jsonl.gz", report["tile_traces"]["overlap"])
        assert len(serial_events) == len(overlap_events) == 63412
        grouped = {"serial": {}, "overlap": {}}
        for label, events in (("serial", serial_events), ("overlap", overlap_events)):
            for event in events:
                key = (event["id"], int(event["memory_profile"]))
                grouped[label].setdefault(key, []).append(event)
        for case in cases:
            ident = case["id"]
            exp = expected[ident]
            for profile in (0, 1):
                key = (ident, profile)
                left = grouped["serial"].get(key, [])
                right = grouped["overlap"].get(key, [])
                for label, events in (("serial", left), ("overlap", right)):
                    result = mode_rows[label][key]
                    assert result["error"] == exp["error"]
                    assert result["status"] == "PASS"
                    assert result["requests"] == result["acks"] and not result["pending_drain"]
                    assert not result["full_frame_publication"]
                    assert len(events) == len(exp["tuples"])
                    queue = result["refill_queue"]
                    if label == "serial":
                        assert all(queue[field] == 0 for field in (
                            "requests", "responses", "pops", "stalls", "cancel_queued", "cancel_pending",
                            "max_count", "max_owned", "final_count", "final_pending", "observed_requests",
                            "observed_responses", "observed_pops", "observed_stalls", "observed_max_count",
                            "observed_max_owned"))
                    for actual, wanted in zip(events, exp["tuples"], strict=True):
                        for field in ("plane", "block", "tile", "qcell", "qscale", "coefficient_count", "coefficient_hash"):
                            assert actual[field] == wanted[field], (label, ident, profile, field)
                    if label == "overlap":
                        assert queue["requests"] == queue["responses"] == queue["pops"]
                        assert queue["pops"] == result["refill_bytes"]
                        assert result["refill_bytes"] == exp["refill_bytes"]
                        assert queue["requests"] == queue["observed_requests"]
                        assert queue["responses"] == queue["observed_responses"]
                        assert queue["pops"] == queue["observed_pops"]
                        assert queue["final_count"] == 0 and not queue["final_pending"]
                        assert queue["max_count"] <= 2 and queue["max_owned"] <= 2
                        assert queue["observed_max_owned"] <= 2
                        assert queue["stalls"] == queue["observed_stalls"]
                        assert queue["cancel_queued"] == queue["cancel_pending"] == 0
                        if exp["error"] in (0, 147):
                            assert queue["requests"] == result["refill_bytes"]
                            assert queue["requests"] == exp["refill_bytes"]
                        else:
                            assert queue["requests"] == 0
                        tuple_total += len(events) if seed == SEEDS[0] else 0
                # Address/time may differ in overlap mode; metadata ordering must not.
                assert [{k: e[k] for k in ("plane", "block", "tile", "qcell", "qscale", "coefficient_count", "coefficient_hash", "frame_epoch", "child_epoch")}
                        for e in left] == [
                            {k: e[k] for k in ("plane", "block", "tile", "qcell", "qscale", "coefficient_count", "coefficient_hash", "frame_epoch", "child_epoch")}
                            for e in right]

        for profile in (0, 1):
            serial_rows = [mode_rows["serial"][key] for key in mode_rows["serial"] if key[1] == profile]
            overlap_rows = [mode_rows["overlap"][key] for key in mode_rows["overlap"] if key[1] == profile]
            bytes_in = sum(row["refill_bytes"] for row in overlap_rows)
            starts = sum(row["core_starts"] for row in overlap_rows)
            measured_saving = sum(row["cycles"] for row in serial_rows) - sum(row["cycles"] for row in overlap_rows)
            fixed_service_saving = 2 * bytes_in - 2 * starts
            if profile == 0:
                assert measured_saving == fixed_service_saving
            else:
                # SLOW profiles use different wall-clock random draw counts after overlap;
                # retain their measured total without claiming paired ready-sequence parity.
                assert bytes_in == 93570 and starts == 18
            cycle_comparisons.append({"seed": seed, "memory_profile": profile,
                                      "refill_bytes": bytes_in, "child_starts": starts,
                                      "measured_serial_minus_overlap_cycles": measured_saving,
                                      "fixed_service_saving_formula": fixed_service_saving,
                                      "paired_ready_trace_claimed": profile == 0})
        aggregate_queue_pops.append({"seed": seed,
                                      "mode1_queue_pops_both_profiles": sum(
                                          row["refill_queue"]["pops"] for row in mode_rows["overlap"].values()),
                                      "mode1_expected_bytes_both_profiles": sum(
                                          row["refill_bytes"] for row in mode_rows["overlap"].values())})
        assert aggregate_queue_pops[-1]["mode1_queue_pops_both_profiles"] == 187140
        assert aggregate_queue_pops[-1]["mode1_expected_bytes_both_profiles"] == 187140

        # Mode 0 is required to retain exact legacy case timing and tuple trace.
        old_receipt_path = ROOT / old_by_seed[seed]["path"]
        old_receipt = load(old_receipt_path)
        old_sim = [json.loads(line) for line in (old_receipt_path.parent / "simulation.jsonl").read_text().splitlines() if line]
        old_case_rows = [row for row in old_sim if row.get("type") == "case"]
        new_serial_rows = [row for row in mode_rows["serial"].values()]
        assert len(old_case_rows) == len(new_serial_rows) == 22
        for old_row in old_case_rows:
            new_row = mode_rows["serial"][(old_row["id"], int(old_row["memory_profile"]))]
            assert all(new_row[field] == value for field, value in old_row.items())
        old_tiles = trace(old_receipt_path.parent / old_receipt["tile_trace"]["path"], old_receipt["tile_trace"])
        assert len(serial_events) == len(old_tiles)
        assert all(all(event[field] == old_event[field] for field in old_event)
                   for event, old_event in zip(serial_events, old_tiles, strict=True))

        # Reconcile standalone RTL directed ownership/error tests and requested static configs.
        standalone = report["standalone_verdict"]
        assert standalone["status"] == "TEST_PASS" and standalone["owner_bound"] == 2
        queue_path = path.parent / "queue.jsonl"
        queue_records = [json.loads(line) for line in queue_path.read_text().splitlines() if line]
        directed = [r for r in queue_records if r.get("type") == "directed"]
        assert len(directed) == 12 and all(r["status"] == "PASS" for r in directed)
        assert {r["name"] for r in directed} == set(standalone["directed_check_names"])
        for row in directed:
            assert row["max_count"] <= 2 and row["max_owned"] <= 2
            assert row["final_count"] == row["final_pending"] == 0
            assert row["requests"] == row["responses"] + row["cancel_pending"]
            assert row["responses"] == row["pops"] + row["cancel_queued"]
            assert row["error"] == (1 if row["name"] in {
                "mismatched_response_epoch_rejected", "missing_one_edge_response_rejected",
                "unsolicited_response_rejected"} else 0)
        directed_by_name = {row["name"]: row for row in directed}
        assert directed_by_name["full_two_owner_hold_then_simultaneous_push_pop"]["max_owned"] == 2
        assert directed_by_name["abort_two_queued_bytes"]["cancel_queued"] == 2
        assert directed_by_name["abort_registered_read_response"]["cancel_pending"] == 1
        assert directed_by_name["replacement_start_cancels_old_response"]["cancel_pending"] == 1
        assert directed_by_name["replacement_start_cancels_full_queue"]["cancel_queued"] == 2
        assert report["case_rows"] == 44
        all_results.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()),
                            "seed": seed, "attempt_status": report["status"],
                            "source_sha256": report["source_sha256"],
                            "vectors_sha256": report["vectors_sha256"],
                            "baseline_control": report["baseline_control"],
                            "serial_trace_records": len(serial_events),
                            "overlap_trace_records": len(overlap_events),
                            "standalone_directed_checks": len(directed)})

    assert len({json.dumps(row["source_sha256"], sort_keys=True) for row in all_results}) == 1
    assert len({json.dumps(row["vectors_sha256"], sort_keys=True) for row in all_results}) == 1
    nonpassing = []
    selected_paths = set(selected.values())
    for path in sorted((RTL / "pipeline-attempts").glob("*/results.json")):
        if path in selected_paths:
            continue
        report = load(path)
        nonpassing.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes()),
                           "seed": report.get("seed"), "status": report.get("status"),
                           "error_class": report.get("error_class"),
                           "baseline_control": report.get("baseline_control")})
    audit = {
        "schema": "cu66-v91i2b-independent-refill-audit-v1",
        "status": "PASS_INDEPENDENT_REFILL_AND_EXACT_CONTROL_AUDIT",
        "auditor": {"path": str(Path(__file__).relative_to(ROOT)),
                    "sha256": sha(Path(__file__).read_bytes())},
        "vectors": {**vector_hashes, "case_count": len(cases)},
        "independent_tuple_oracle": {
            "path": "experiments/python-gamebub-v91i2/verify_results.py",
            "sha256": sha((ROOT / "experiments/python-gamebub-v91i2/verify_results.py").read_bytes()),
            "entropy_oracle": {"path": str(codec.relative_to(ROOT)), "sha256": sha(codec.read_bytes())},
            "tuple_rows_per_seed": 63412,
        },
        "owner_contract": {"fifo_slots": 2, "pending_registered_response_owner": 1,
                           "total_owners_bound": 2, "no_bypass": True,
                           "byte_address_epoch_last_and_tuple_order_checked": True},
        "attempts": all_results,
        "retained_nonpassing_attempts": nonpassing,
        "tuple_rows_independently_checked": tuple_total,
        "queue_pop_reconciliation": aggregate_queue_pops,
        "cycle_comparison": cycle_comparisons,
        "scope": "Two-slot registered-byte refill ownership, exact 0-mode cycle/traffic/fence parity with frozen V91i2a, exact coefficient tuple oracle/order for both modes, and directed cancellation/error ownership only. This does not cover dequantization/IDCT, pixel reconstruction, frame acceptance/publication, physical fit, hardware throughput, or full-frame latency.",
    }
    (AREA / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(audit["status"], "attempts=" + str(len(all_results)), "tuples=" + str(tuple_total))


if __name__ == "__main__":
    main()
