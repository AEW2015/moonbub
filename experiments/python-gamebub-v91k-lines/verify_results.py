#!/usr/bin/env python3
"""Independent audit of the V91k aligned 128-bit line adapter comparison.

The frozen canonical-input and RGB arithmetic helpers are reused from the
source-pinned V91k cache auditor.  This file independently derives the byte
request stream, aligned physical-line sequence, line payload hashes, complete
coverage, and comparison receipts.  It does not import either producer model.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
LINE_AREA = ROOT / "fpga/experiments/cu66-v91k-lines"
ATTEMPTS = LINE_AREA / "comparison-attempts"
BASELINE = "1e974dcaab4b86646b0480f8987d3469316c06b3"
PASS_STATUS = "PASS_EXACT_X16_PRICED_ALIGNED_LINES"
SCHEMA = "cu66-v91k-aligned-lines-comparison-v1"
SEEDS = (911701, 911702)
FROZEN_OLD_AUDITOR_SHA256 = "bfd2b521b45c97182fbc6786e680b9c1cbac2dc1093375c9b17d483c484f76db"
FNV_OFFSET, FNV_PRIME = 1469598103934665603, 1099511628211
MASK64 = (1 << 64) - 1
EXPECTED_IDS = ("actual_001", "actual_006", "actual_043", "actual_031",
                "actual_006_varied_qcache", "structural_all_copy_zero_residual")
LINE_CHECKS = {
    "abort_unaccepted_line_offer", "warm_reset_unaccepted_line_offer",
    "abort_cb_fill_pending_drain", "warm_reset_cb_fill_pending_drain",
    "abort_cr_fill_pending_drain", "warm_reset_cr_fill_pending_drain",
    "abort_luma_pending_drain", "warm_reset_luma_pending_drain",
    "abort_late_cb_fill_eviction", "warm_reset_late_cb_fill_eviction",
    "abort_late_cr_fill_eviction", "warm_reset_late_cr_fill_eviction",
    "abort_local_6", "warm_reset_local_6", "abort_local_7", "warm_reset_local_7",
    "abort_held_pixel", "warm_reset_held_pixel", "abort_last_fill_ack_same_edge",
    "warm_reset_last_fill_ack_same_edge", "wrong_epoch_cb_fill", "bus_error_cb_fill",
    "wrong_epoch_cr_fill", "bus_error_cr_fill", "wrong_epoch_luma", "bus_error_luma",
    "zero_epoch_rejected", "start_epoch_snapshot_immutable",
    "complete_rows_only_and_parity_ownership",
    "registered_lookup_odd_even_edges_and_bottom_alias", "clean_retry_after_cancel_and_fault",
    "abort_physical_ack_same_edge", "warm_reset_physical_ack_same_edge",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fnv_byte(h: int, value: int) -> int:
    return ((h ^ value) * FNV_PRIME) & MASK64


def fnv_u32(h: int, value: int) -> int:
    for shift in (0, 8, 16, 24):
        h = fnv_byte(h, (value >> shift) & 0xFF)
    return h


def load_old_auditor():
    path = AREA.parent / "python-gamebub-v91k-cache" / "verify_results.py"
    packed = path.read_bytes()
    assert sha(packed) == FROZEN_OLD_AUDITOR_SHA256, "pinned V91k helper changed"
    spec = importlib.util.spec_from_file_location("frozen_v91k_cache_auditor", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, sha(packed)


def physical_schedule(frame: bytes) -> dict:
    """Derive all byte requests, then first-occurrence aligned lines by plane."""
    assert len(frame) == 518400
    addresses: list[int] = []
    next_row = 0
    for y in range(480):
        last = min(y // 2 + 1, 239)
        while next_row <= last:
            for base in (345600, 432000):
                addresses.extend(base + next_row * 360 + x for x in range(360))
            next_row += 1
        addresses.extend(y * 720 + x for x in range(720))
    assert len(addresses) == 518400
    assert len(set(addresses)) == 518400

    plane_last: list[int | None] = [None, None, None]
    physical: list[int] = []
    for address in addresses:
        plane = 0 if address < 345600 else (1 if address < 432000 else 2)
        line = address & ~15
        if plane_last[plane] != line:
            physical.append(line)
            plane_last[plane] = line
    assert len(physical) == 32400
    byte_hash = FNV_OFFSET
    seen = bytearray(len(frame))
    for address in addresses:
        assert not seen[address]
        seen[address] = 1
        byte_hash = fnv_byte(fnv_u32(byte_hash, address), frame[address])
    assert all(seen)

    line_hash = FNV_OFFSET
    seen_line = bytearray((len(frame) + 15) // 16)
    line_payload_bytes = 0
    for address in physical:
        assert address % 16 == 0 and address + 16 <= len(frame)
        index = address // 16
        assert not seen_line[index], ("duplicate line", address)
        seen_line[index] = 1
        line_hash = fnv_u32(line_hash, address)
        for value in frame[address:address + 16]:
            line_hash = fnv_byte(line_hash, value)
            line_payload_bytes += 1
    assert all(seen_line), "aligned requests must cover every canonical byte"
    return {
        "byte_read_hash": f"{byte_hash:016x}",
        "physical_line_hash": f"{line_hash:016x}",
        "byte_reads": len(addresses), "physical_reads": len(physical),
        "physical_payload_bytes": line_payload_bytes,
        "x16_beats": len(physical) * 8,
        "line_hits": len(addresses) - len(physical),
        "lines_by_plane": {"Y": 21600, "Cb": 5400, "Cr": 5400},
    }


def read_cases(path: Path) -> tuple[list[dict], list[dict]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return ([r for r in rows if r.get("type") == "case"],
            [r for r in rows if r.get("type") == "verdict"])


def audit_case_log(attempt: Path, label: str, seed: int, frames: dict, goldens: dict,
                   helper: dict) -> dict:
    path = attempt / (f"{label}.jsonl" if label.startswith("edge-") else f"simulation-{label}.jsonl")
    cases, verdicts = read_cases(path)
    edge = label.startswith("edge-")
    lines = label.endswith("lines")
    expected_n = 2 if edge else 12
    expected_pixels = 691200 if edge else 4147200
    assert len(cases) == expected_n and len(verdicts) == 1
    verdict = verdicts[0]
    assert verdict["status"] == "TEST_PASS" and verdict["seed"] == seed
    assert (verdict["cases"], verdict["pixels"], verdict["reads_per_frame"]) == (expected_n, expected_pixels, 518400)
    assert verdict["directed_checks"] == (33 if lines else 29)
    if lines:
        assert LINE_CHECKS <= set(verdict["directed_check_names"])
        assert verdict["directed_checks"] == 33 and len(verdict["directed_check_names"]) == 33
        assert verdict["physical_reads_per_frame"] == 32400
        assert verdict["line_slots_logical_bytes"] == 48
    seen = set()
    for row in cases:
        key = (row["id"], str(row["memory_profile"]))
        assert key in frames and key not in seen
        seen.add(key)
        frame = frames[key]
        rgb = helper.convert_rgb565(frame)
        sched = physical_schedule(frame)
        assert rgb == goldens[row["id"]]
        assert row["status"] == "PASS" and row["seed"] == seed
        assert row["pixels"] == 345600 and row["reads"] == row["responses"] == 518400
        assert int(row["canonical_input_hash"]) == helper.fnv_bytes(frame)
        assert int(row["rgb565_hash"]) == helper.fnv_bytes(rgb)
        assert int(row["read_schedule_hash"]) == int(sched["byte_read_hash"], 16)
        assert row["publication"] is False
        assert row["cycles"] > 0 and row["first_read"] > 0
        assert row["last_response"] >= row["first_read"]
        assert row["first_output"] >= row["first_read"] and row["last_output"] >= row["first_output"]
        assert row["output_stalls"] >= 0 and row["request_stalls"] >= 0
        if row["memory_profile"] == 1:
            assert row["output_stalls"] > 0 and row["request_stalls"] > 0
        assert row["luma_reads"] == 345600 and row["chroma_reads"] == 172800
        assert row["row_fills"] == 240
        assert row["lookups"] == row["lookup_responses"] == row["cache_hits"] == 345600
        assert int(row["lookup_hash"]) == int(helper.lookup_schedule(), 16)
        assert row["final_row_valid"] == 3 and row["final_row_tags"] == [238, 239]
        if lines:
            assert row["physical_reads"] == row["physical_responses"] == sched["physical_reads"]
            assert row["physical_x16_beats"] == sched["x16_beats"]
            assert row["line_misses"] == sched["physical_reads"]
            assert row["line_hits"] == sched["line_hits"]
            assert int(row["physical_read_hash"]) == int(sched["physical_line_hash"], 16)
            assert row["byte_response_hash"] == row["read_schedule_hash"]
    assert seen == set(frames)
    return {"verdict": verdict, "cases": cases, "log_sha256": sha(path.read_bytes())}


def audit_trace(attempt: Path, receipt: dict, canonical: dict, label: str, seed: int,
                line_rows: dict) -> dict:
    packed = (attempt / receipt["path"]).read_bytes()
    raw = gzip.decompress(packed)
    assert sha(packed) == receipt["gzip_sha256"] and sha(raw) == receipt["raw_sha256"]
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    expected_n = 480 if label.startswith("edge") else 2880
    assert len(rows) == receipt["rows"] == expected_n
    groups: dict[tuple[str, int], list[dict]] = {}
    for row in rows:
        assert row["type"] == "row_fill"
        groups.setdefault((row["id"], int(row["memory_profile"])), []).append(row)
    assert len(groups) == (2 if label.startswith("edge") else 12)
    for key, items in groups.items():
        assert (key[0], str(key[1])) in canonical
        assert len(items) == 240
        assert [int(r["row"]) for r in items] == list(range(240))
        assert [int(r["slot"]) for r in items] == [i & 1 for i in range(240)]
        assert all(int(r["cb_acks"]) == 360 and int(r["cr_acks"]) == 360 for r in items)
        assert all(int(r["epoch"]) > 0 and int(r["cycle"]) > 0 for r in items)
        case = line_rows[key]
        assert all(int(r["epoch"]) == int(case["epoch"]) for r in items)
        assert all(int(a["cycle"]) < int(b["cycle"]) for a, b in zip(items, items[1:]))
    return {"rows": len(rows), "raw_sha256": sha(raw), "gzip_sha256": sha(packed)}


def audit_attempt(report_path: Path, helper, expected_inputs: dict) -> dict:
    report_path = report_path.resolve()
    attempt = report_path.parent
    report = json.loads(report_path.read_text(encoding="utf-8"))
    seed = int(report["seed"])
    assert seed in SEEDS
    assert report["schema"] == SCHEMA and report["status"] == PASS_STATUS
    ancestry = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASELINE,
         report["source_revision"]],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    assert ancestry.returncode == 0, ("attempt source revision is not a descendant of the pinned baseline",
                                      report["source_revision"], ancestry.stderr.decode("utf-8", "replace"))
    assert report["full_frame_publication_timestamp"] is None
    for field in ("hardware_distinct_30fps_proven", "full_frame_decode_under10ms_proven",
                  "mapped_cache_fit_proven", "monolithic_full_frame_rtl_proven"):
        assert report[field] is False
    assert "128-bit line FAST eight data edges" in report["service_rule"]
    assert "No command-accurate SDRAM" in report["service_rule"]

    for rel, digest in report["source_sha256"].items():
        live = ROOT / rel
        snap = attempt / "sources" / rel
        assert live.is_file() and sha(live.read_bytes()) == digest, (rel, "live source pin")
        assert snap.is_file() and sha(snap.read_bytes()) == digest, (rel, "source snapshot pin")
    for rel, digest in report["inputs_sha256"].items():
        assert sha((ROOT / rel).read_bytes()) == digest, (rel, "live input pin")
    source = report["source_canonical_receipt"]
    src_report = ROOT / source["source_report"]
    src_gzip = ROOT / source["path"]
    assert source["source_seed"] == seed - 200
    v91k_summary_path = ROOT / "experiments/python-gamebub-v91k/summary.json"
    v91k_summary = json.loads(v91k_summary_path.read_text(encoding="utf-8"))
    selected_v91k = next(row for row in v91k_summary["attempts"] if row["seed"] == source["source_seed"])
    assert source["source_report"] == selected_v91k["path"]
    assert source["source_report_sha256"] == selected_v91k["sha256"]
    assert sha(src_report.read_bytes()) == source["source_report_sha256"]
    assert sha(src_gzip.read_bytes()) == source["sha256"]
    assert gzip.decompress(src_gzip.read_bytes()) == gzip.decompress(helper.INPUT_CANONICAL.read_bytes())
    assert source["rows"] == 12
    src = json.loads(src_report.read_text(encoding="utf-8"))
    assert src["seed"] == source["source_seed"] and src["status"] == "PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY"
    assert source["path"] == str(Path(source["source_report"]).parent / src["canonical_actual"]["path"])

    copies = {
        "canonical_actual.tsv.gz": src_gzip,
        "rgb_goldens.tsv.gz": ROOT / "experiments/python-gamebub-v91k/vectors/rgb_goldens.tsv.gz",
        "edge_actual.tsv.gz": ROOT / "experiments/python-gamebub-v91k-cache/vectors/edge_actual.tsv.gz",
        "edge_rgb_goldens.tsv.gz": ROOT / "experiments/python-gamebub-v91k-cache/vectors/edge_rgb_goldens.tsv.gz",
        "v91k-source-report.json": src_report,
        "model-results.json": ROOT / "experiments/python-gamebub-v91k-cache/model-results.json",
    }
    for name, source_path in copies.items():
        dest = attempt / "inputs" / name
        assert dest.is_file() and dest.read_bytes() == source_path.read_bytes(), (name, "input snapshot mismatch")
    expanded = {row["path"]: row for row in report["input_expansions"]}
    expected_expansions = {
        "canonical_actual.tsv": (copies["canonical_actual.tsv.gz"], 12),
        "rgb_goldens.tsv": (copies["rgb_goldens.tsv.gz"], 6),
        "edge_actual.tsv": (copies["edge_actual.tsv.gz"], 2),
        "edge_rgb_goldens.tsv": (copies["edge_rgb_goldens.tsv.gz"], 1),
    }
    assert set(expanded) == set(expected_expansions)
    for name, (source_path, row_count) in expected_expansions.items():
        receipt = expanded[name]
        packed = (attempt / receipt["compressed_path"]).read_bytes()
        raw = gzip.decompress(packed)
        assert sha(packed) == receipt["compressed_sha256"] == sha(source_path.read_bytes())
        assert sha(raw) == receipt["raw_sha256"]
        assert len(raw.splitlines()) == receipt["rows"] == row_count
        assert raw == gzip.decompress(source_path.read_bytes())
    for rel, digest in report["artifacts_sha256"].items():
        artifact = attempt / rel
        assert artifact.is_file() and sha(artifact.read_bytes()) == digest, (rel, "artifact digest")
    assert all(c["exit_code"] == 0 for c in report["commands"])
    builds = [c for c in report["commands"] if "--build" in c["argv"]]
    assert len(builds) == 2
    for c in builds:
        cmd = " ".join(c["argv"])
        assert "--assert" in cmd and "-Wall" in cmd and "-Wextra -Werror" in cmd

    canonical, goldens, _ = helper.read_frozen_inputs()
    frames = dict(canonical)
    edge_frames, edge_goldens = helper.load_edge_inputs()
    frames.update(edge_frames)
    goldens = dict(goldens)
    goldens.update(edge_goldens)
    expected_frames = {k: v for k, v in frames.items() if k[0] != "cache_edge_pattern"}
    expected_edge = {k: v for k, v in frames.items() if k[0] == "cache_edge_pattern"}
    assert len(expected_frames) == 12 and len(expected_edge) == 2
    for key, frame in frames.items():
        assert helper.convert_rgb565(frame) == goldens[key[0]], (key, "independent RGB recomputation")
    control = audit_case_log(attempt, "control", seed, expected_frames, goldens, helper)
    lines = audit_case_log(attempt, "lines", seed, expected_frames, goldens, helper)
    edge_control = audit_case_log(attempt, "edge-control", seed, expected_edge, goldens, helper)
    edge_lines = audit_case_log(attempt, "edge-lines", seed, expected_edge, goldens, helper)
    for label, actual, n, pixels in (("control", control, 12, 4147200), ("lines", lines, 12, 4147200)):
        v = report["verdicts"][label]
        assert v["status"] == "TEST_PASS" and v["seed"] == seed
        assert (v["cases"], v["pixels"], v["reads_per_frame"]) == (n, pixels, 518400)
    for label, actual, n, pixels in (("control", edge_control, 2, 691200), ("lines", edge_lines, 2, 691200)):
        v = report["edge_verdicts"][label]
        assert v["status"] == "TEST_PASS" and v["seed"] == seed
        assert (v["cases"], v["pixels"], v["reads_per_frame"]) == (n, pixels, 518400)

    line_case_map = {(r["id"], int(r["memory_profile"])): r for r in lines["cases"]}
    trace_out = {}
    for name, receipt, canonical_rows, case_rows in (
        ("lines", report["row_trace"], expected_frames, line_case_map),
        ("edge-lines", report["edge_row_trace"], expected_edge,
         {(r["id"], int(r["memory_profile"])): r for r in edge_lines["cases"]}),
    ):
        trace_out[name] = audit_trace(attempt, receipt, canonical_rows, name, seed, case_rows)
    comparison = []
    for a, b in zip(control["cases"], lines["cases"]):
        assert (a["id"], a["memory_profile"]) == (b["id"], b["memory_profile"])
        comparison.append({"id": a["id"], "memory_profile": a["memory_profile"],
                           "control_cycles": a["cycles"], "lines_cycles": b["cycles"],
                           "cycle_delta_lines_minus_control": b["cycles"] - a["cycles"]})
    return {
        "seed": seed, "attempt": str(report_path.relative_to(ROOT)),
        "results_sha256": sha(report_path.read_bytes()), "status": report["status"],
        "source_sha256": report["source_sha256"], "inputs_sha256": report["inputs_sha256"],
        "artifact_count": len(report["artifacts_sha256"]), "command_count": len(report["commands"]),
        "control_cases": len(control["cases"]), "line_cases": len(lines["cases"]),
        "edge_control_cases": len(edge_control["cases"]), "edge_line_cases": len(edge_lines["cases"]),
        "line_trace": trace_out, "frame_cycle_comparisons": comparison,
        "directed_checks": lines["verdict"]["directed_check_names"],
        "service_rule": report["service_rule"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", action="append", type=Path,
                        help="attempt results.json; repeat for each seed (auto-select current source passes otherwise)")
    parser.add_argument("--output", type=Path, default=AREA / "audit.json")
    args = parser.parse_args()
    helper, helper_sha = load_old_auditor()
    reports = args.attempt or sorted(ATTEMPTS.glob("*/results.json"))
    current_passes: dict[int, list[Path]] = {seed: [] for seed in SEEDS}
    retained_failures = []
    superseded_passes = []
    for path in reports:
        item = json.loads(path.read_text(encoding="utf-8"))
        if item.get("status") != PASS_STATUS:
            attempt = path.parent
            retained_failures.append({"path": str(path.relative_to(ROOT)),
                                      "sha256": sha(path.read_bytes()), "status": item.get("status"),
                                      "error_class": item.get("error_class"), "error": item.get("error"),
                                      "retained_file_sha256": {
                                          str(p.relative_to(attempt)): sha(p.read_bytes())
                                          for p in sorted(attempt.rglob("*")) if p.is_file()}})
            continue
        seed = int(item.get("seed", -1))
        if seed not in SEEDS:
            continue
        current = all((ROOT / rel).is_file() and sha((ROOT / rel).read_bytes()) == digest
                      for rel, digest in item.get("source_sha256", {}).items())
        if current:
            current_passes[seed].append(path)
        else:
            superseded_passes.append({"path": str(path.relative_to(ROOT)),
                                      "sha256": sha(path.read_bytes()), "seed": seed,
                                      "status": item.get("status"),
                                      "source_sha256": item.get("source_sha256"),
                                      "superseded_reason": "source_pins_no_longer_current"})
    chosen = {}
    for seed in SEEDS:
        assert current_passes[seed], f"no current-source passing aligned-lines report for seed {seed}"
        chosen[seed] = max(current_passes[seed], key=lambda p: p.stat().st_mtime_ns)
    audited = [audit_attempt(chosen[seed], helper, {}) for seed in SEEDS]
    result = {
        "schema": "cu66-v91k-aligned-lines-independent-audit-v1",
        "status": "PASS_CURRENT_SOURCE_BOTH_SEEDS_EXACT_ALIGNED_LINES_AND_CONTROL",
        "baseline_revision": BASELINE,
        "scope": "Independent audit of exact V91k RGB565 replay with three plane-specific aligned 128-bit line slots, priced as eight x16 beats plus response service. This is not full-frame decode, HUD validation/publication, a command-accurate SDRAM model, mapped fit, hardware FPS, or a <10 ms claim.",
        "independence": {
            "producer_model_imported": False,
            "frozen_helper": "experiments/python-gamebub-v91k-cache/verify_results.py",
            "frozen_helper_sha256": helper_sha,
            "base_converter_recomputed": True,
            "byte_address_schedule_recomputed": True,
            "aligned_line_sequence_recomputed": True,
            "line_payload_bytes_rehashed": True,
            "all_canonical_bytes_covered_once": True,
        },
        "line_schedule": {
            "canonical_frame_bytes": 518400,
            "byte_requests_per_frame": 518400,
            "physical_lines_per_frame": 32400,
            "x16_beats_per_frame": 259200,
            "payload_bytes_per_frame": 518400,
            "line_hits_per_frame": 486000,
            "line_misses_per_frame": 32400,
            "physical_line_coverage": "all aligned 16-byte addresses over the three planes exactly once",
        },
        "attempts": audited,
        "superseded_passing_attempts": superseded_passes,
        "retained_failed_attempts": retained_failures,
        "attempts_selected": {str(x["seed"]): x["attempt"] for x in audited},
        "hardware_distinct_30fps_proven": False,
        "full_frame_decode_under10ms_proven": False,
        "full_frame_publication_proven": False,
        "monolithic_full_frame_rtl_proven": False,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "seeds": [x["seed"] for x in audited],
                      "output": str(args.output), "line_reads_per_frame": 32400}, sort_keys=True))


if __name__ == "__main__":
    main()
