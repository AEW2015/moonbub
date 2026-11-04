#!/usr/bin/env python3
"""Evidence-first audit for the v13 cache, motion gate, and execution studies.

This module deliberately reports missing evidence as unknown. It is stdlib-only.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

INPUTS = {
    "cache_admission": ROOT / "experiments/python-game-cache-admission-study/results.json",
    "motion_gate": ROOT / "experiments/python-game-motion-gate-study/results.json",
    "execution": ROOT / "experiments/python-game-execution-study/results.json",
    "ui_cache": ROOT / "experiments/python-game-ui-cache-study/results.json",
    "credit_window": ROOT / "experiments/python-game-credit-window-study/results.json",
}
# The credit-window result is currently being regenerated after a protocol-edge
# fix. Keep any prior results.json out of the audit until its owner confirms the
# retained run and matching pins.
AWAITING_FINALIZATION: set[str] = set()


def complete_packet(row: dict) -> dict:
    """Do not treat payload size as a complete packet size."""
    size = row.get("complete_packet_bytes", row.get("packet_bytes"))
    cap = row.get("frame_cap_bytes", row.get("frame_cap"))
    return {"complete_packet_bytes": size, "frame_cap_bytes": cap,
            "fits_cap": size <= cap if isinstance(size, (int, float)) and isinstance(cap, (int, float)) else None,
            "payload_bytes": row.get("payload_bytes"), "header_bytes": row.get("header_bytes"),
            "crc_bytes": row.get("crc_bytes"),
            "complete_accounting_recorded": all(isinstance(row.get(k), (int, float))
                for k in ("payload_bytes", "header_bytes", "crc_bytes"))}


def source_identity(rows: list[dict]) -> dict:
    """Report run rows, identified source frames, unique contents, and cohort separately."""
    pairs = set()
    hashes = set()
    cohort_rows: dict[str, int] = {}
    missing_ids = 0
    for row in rows:
        sid = row.get("source_id", row.get("source"))
        fid = row.get("frame_id", row.get("id"))
        if sid is None or fid is None:
            missing_ids += 1
        else:
            pairs.add((str(sid), str(fid)))
        h = row.get("source_rgb_sha256", row.get("input_sha256", row.get("rgb_sha256")))
        if h:
            hashes.add(h)
        cohort = row.get("cohort", "unknown")
        cohort_rows[str(cohort)] = cohort_rows.get(str(cohort), 0) + 1
    return {"rows": len(rows), "unique_source_frames": len(pairs),
            "duplicate_source_frame_rows": len(rows) - missing_ids - len(pairs),
            "rows_missing_source_or_frame_id": missing_ids,
            "unique_rgb_content_hashes": len(hashes) if hashes else None,
            "cohort_rows": cohort_rows}


def explicit_cost(rows: list[dict], cost_keys: tuple[str, ...]) -> dict:
    """Sum only explicitly supplied numeric measurements; rejected work remains counted."""
    total = 0.0
    measured = 0
    rejected_total = 0.0
    rejected_measured = 0
    for row in rows:
        value = next((row[k] for k in cost_keys if isinstance(row.get(k), (int, float))), None)
        if value is None:
            continue
        total += float(value)
        measured += 1
        rejected = row.get("accepted") is False or row.get("admitted") is False or row.get("rejected") is True
        if rejected:
            rejected_total += float(value)
            rejected_measured += 1
    return {"rows_with_explicit_cost": measured, "explicit_cost_sum_ms": total if measured else None,
            "rejected_rows_with_explicit_cost": rejected_measured,
            "rejected_explicit_cost_sum_ms": rejected_total if rejected_measured else (0.0 if measured else None)}


def timing_classes(row: dict) -> dict:
    return {"actual_wall_ms": row.get("actual_wall_ms", row.get("wall_ms")),
            "charged_service_ms": row.get("charged_service_ms", row.get("service_ms")),
            "hardware_timing_proven": row.get("hardware_timing_proven") is True,
            "actual_wall_and_charged_service_separate": True}


def all_true_if_present(rows: list[dict], field: str) -> bool | None:
    """Tri-state proof: absent evidence is unknown, explicit failure is false."""
    values = [r[field] for r in rows if field in r]
    if not values:
        return None
    return len(values) == len(rows) and all(v is True for v in values)


def _counts(rows: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, "unknown"))
        out[key] = out.get(key, 0) + 1
    return out


def _logged_tests(path: Path, names: list[str]) -> dict:
    text = path.read_text() if path.is_file() else ""
    passed = {name: any(line.startswith(name + " ") and line.rstrip().endswith("ok") for line in text.splitlines()) for name in names}
    return {"log_present": path.is_file(), "tests": passed, "all_required_logged_passing": all(passed.values())}


def _resolve_pin_path(raw: str) -> Path:
    marker = "/moonbub-30fps-study/"
    if marker in raw:
        return ROOT / raw.split(marker, 1)[1]
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def _source_assertion(data: dict, filename: str, needle: str) -> bool:
    for raw in data.get("source_sha256", {}):
        path = _resolve_pin_path(raw)
        if path.name == filename and path.is_file():
            return needle in path.read_text(errors="replace")
    return False


def verify_source_pins(data_sets: list[dict]) -> dict:
    pins: dict[str, str] = {}
    for data in data_sets:
        pins.update(data.get("source_sha256", {}))
    rows = []
    for raw, expected in sorted(pins.items()):
        p = _resolve_pin_path(raw)
        def digest() -> str | None:
            if not p.is_file(): return None
            h = hashlib.sha256()
            with p.open("rb") as f:
                for block in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(block)
            return h.hexdigest()
        before, after = digest(), digest()
        rows.append({"path": str(p), "expected": expected, "actual_before": before, "actual_after": after,
                     "matches": before == expected and after == expected, "stable": before == after})
    return {"pin_count": len(rows), "all_match_and_stable": bool(rows) and all(r["matches"] and r["stable"] for r in rows),
            "missing": [r["path"] for r in rows if r["actual_before"] is None],
            "mismatched": [r["path"] for r in rows if r["actual_before"] is not None and not r["matches"]],
            "rows": rows}


def actual_wall_service_equality(cases: list[dict]) -> dict:
    pairs = {"cpu": [], "resize": [], "encode": [], "decode": []}
    for case in cases:
        r = case.get("result", {})
        for x in r.get("cpu_services", []):
            if isinstance(x.get("wall_ms"), (int, float)) and isinstance(x.get("service_ms"), (int, float)):
                pairs["cpu"].append((x["wall_ms"], x["service_ms"]))
        for x in r.get("resize_services", []):
            if isinstance(x.get("wall_ms"), (int, float)) and isinstance(x.get("service_ms"), (int, float)):
                pairs["resize"].append((x["wall_ms"], x["service_ms"]))
        for x in r.get("packets", []):
            for category, wall_key, service_key in (("encode", "encode_wall_ms", "encode_service_ms"),
                                                     ("decode", "decode_wall_ms", "decode_service_ms")):
                if isinstance(x.get(wall_key), (int, float)) and isinstance(x.get(service_key), (int, float)):
                    pairs[category].append((x[wall_key], x[service_key]))
    return {k: {"observations": len(v), "mismatches": sum(a != b for a, b in v),
                "all_equal": all(a == b for a, b in v) if v else None,
                "wall_ms_sum": sum(a for a, _ in v) if v else None,
                "service_ms_sum": sum(b for _, b in v) if v else None} for k, v in pairs.items()}


def audit_cache(data: dict) -> dict:
    cases = data.get("cases", [])
    rows = [r for c in cases for r in c.get("rows", [])]
    pairs = {(c.get("name"), r.get("id")) for c in cases for r in c.get("rows", [])}
    hashes = {r.get("source_rgb_sha256") for r in rows if r.get("source_rgb_sha256")}
    admitted = [r for r in rows if r.get("accepted") is True]
    rejected = [r for r in rows if r.get("accepted") is False]
    hits = [r for r in rows if r.get("cache", {}).get("hits", 0) > 0]
    packet_equal = [r for r in rows if r.get("whole_packets_equal") is True]
    caps = [(c.get("frame_cap"), r) for c in cases for r in c.get("rows", [])]
    summary = {c.get("name"): c.get("summary", {}).get("all", {}) for c in cases}
    highwater = max((c.get("max_cache_bytes") for c in cases if isinstance(c.get("max_cache_bytes"), int)), default=None)
    reported_ids = sum(c.get("manifest", {}).get("frame_count", 0) for c in cases)
    commit_evidence = _source_assertion(data, "cache_admission.py", "admission_before_commit")
    test_log = ROOT / "experiments/python-game-cache-admission-study/tests.log"
    regression_names = ["test_cached_fallback_candidate_is_admitted_before_commit",
                        "test_cap_rejection_no_codec_commit_and_repeat_reject_cost_paid",
                        "test_exact_hits_use_commit_and_no_transform_or_entropy",
                        "test_credit_key_drain_and_stale_cached_preview",
                        "test_sequence_byte_equality_with_bounded_two_map_cache"]
    logged_tests = _logged_tests(test_log, regression_names)
    rejected_candidate_ms = [a.get("candidate_ms") for r in rejected for a in r.get("cached_attempts", []) if isinstance(a.get("candidate_ms"), (int, float))]
    return {"case_count": len(cases), "row_count": len(rows), "paired_source_ids_declared": data.get("paired_source_ids"),
            "unique_case_frame_pairs": len(pairs), "unique_rgb_content_hashes": len(hashes),
            "cohort_rows": {k: sum(len(c.get("rows", [])) for c in cases if c.get("cohort") == k) for k in sorted({c.get("cohort") for c in cases})}, "manifest_source_ids_summed": reported_ids,
            "accepted_rows": len(admitted), "rejected_rows": len(rejected),
            "whole_packet_hash_equal_rows": len(packet_equal),
            "all_compared_whole_packets_equal": len(packet_equal) == len(rows) if rows else None,
            "complete_packet_bytes_recorded_rows": sum(isinstance(r.get("packet_bytes"), int) for r in rows),
            "all_accepted_packet_bytes_at_or_below_case_cap": all(r.get("packet_bytes", 10**99) <= cap for cap, r in caps if r.get("accepted") is True),
            "native_manifest_targets_720x480": all((c.get("manifest", {}).get("target_width"), c.get("manifest", {}).get("target_height")) == (720, 480) for c in cases if c.get("manifest", {}).get("target_width") is not None) if cases else None,
            "all_rows_720x480": all((r.get("width"), r.get("height")) == (720, 480) for r in rows) if rows else None,
            "max_cache_bytes_observed": highwater,
            "case_cache_byte_highwaters_and_limits": [{"case": c.get("name"), "observed_max_cache_bytes": c.get("max_cache_bytes"), "declared_cache_limit_bytes": c.get("cache_byte_limit")} for c in cases],
            "cache_hit_rows": len(hits), "cache_hit_attempts": sum(a.get("cache_hit") is True for r in rows for a in r.get("cached_attempts", [])),
            "rejected_candidate_attempts": sum(len(r.get("cached_attempts", [])) for r in rejected),
            "rejected_candidate_wall_ms_sum": sum(rejected_candidate_ms) if rejected_candidate_ms else None,
            "baseline_forward_calls": sum(summary[n].get("baseline_forward_calls", 0) for n in summary),
            "cached_forward_calls": sum(summary[n].get("cached_forward_calls", 0) for n in summary),
            "all_rejected_rows_have_candidate_cost": all(bool(r.get("cached_attempts")) for r in rejected),
            "cap_before_commit_source_evidence": commit_evidence,
            "regression_tests_present_and_logged_passing": logged_tests,
            "timing_scope": data.get("timing_scope"), "memory_scope": data.get("memory_scope"),
            "protocol_scope": data.get("protocol_scope"), "deployment_scope": data.get("deployment_scope")}


def audit_motion(data: dict) -> dict:
    scenes = data.get("scenes", [])
    profile_rows = [(s, p, r) for s in scenes for p, rr in s.get("profiles", {}).items() for r in rr]
    gated = [(s, r) for s, p, r in profile_rows if p == "gated_rate"]
    all_profiles = [r for _, _, r in profile_rows]
    accepted = [r for r in all_profiles if r.get("accepted") is True]
    rejected = [r for r in all_profiles if r.get("accepted") is False]
    screen_results = [r.get("gate", {}) for _, r in gated if isinstance(r.get("gate"), dict)]
    comparisons = [c for s in scenes for c in s.get("comparisons", [])]
    ids = {(s.get("name"), r.get("frame_id")) for s, _, r in profile_rows}
    hashes = {r.get("source_rgb_sha256") for r in all_profiles if r.get("source_rgb_sha256")}
    cohorts = {k: sum(len(s.get("indices", [])) for s in scenes if s.get("cohort") == k) for k in sorted({s.get("cohort") for s in scenes})}
    attempt_count = sum(len(r.get("attempts", [])) for r in all_profiles)
    gated_attempts = sum(len(r.get("attempts", [])) for _, r in gated)
    gate_executions = [g for g in screen_results if g.get("reason") == "screen_declined" or g.get("reason") == "motion_screen"]
    real_gated = [(s, r) for s, r in gated if s.get("cohort") in ("temporal_real", "heldout_real")]
    synthetic_gated = [(s, r) for s, r in gated if s.get("cohort") == "synthetic"]
    no_bm_real = sum(not any(a.get("mode") == "bm_block" for a in r.get("attempts", [])) for _, r in real_gated)
    bm_enabled_synthetic = sum(any(a.get("mode") == "bm_block" for a in r.get("attempts", [])) for _, r in synthetic_gated)
    gate_cost = [g.get("gate_ms") for g in screen_results if isinstance(g.get("gate_ms"), (int, float))]
    rejected_prepare = [r.get("prepare_ms") for r in rejected if isinstance(r.get("prepare_ms"), (int, float))]
    candidate_costs = [a.get("stages", {}).get("candidate_total_ms") for r in all_profiles for a in r.get("attempts", [])
                       if isinstance(a.get("stages", {}).get("candidate_total_ms"), (int, float))]
    test_log = ROOT / "experiments/python-game-motion-gate-study/tests.log"
    regression_names = ["test_key_and_geometry_skip_screen_without_sampling_or_bm_work",
                        "test_rejection_pays_gate_and_codec_without_credit_or_reference_change",
                        "test_screen_is_deterministic_and_does_not_mutate_current_or_anchor",
                        "test_static_screen_prevents_block_search_and_preserves_bytes",
                        "test_translation_passes_and_actual_candidate_bytes_match_controls",
                        "test_mixed_stream_credit_expiry_ack_and_decoder_are_unchanged"]
    return {"scene_count": len(scenes), "decisions_declared": data.get("decisions"), "source_ids_declared": data.get("source_ids"),
            "profile_decision_rows": len(profile_rows), "unique_scene_frame_ids": len(ids), "unique_rgb_content_hashes": len(hashes),
            "accepted_profile_rows": len(accepted), "rejected_profile_rows": len(rejected),
            "rejected_prepare_wall_ms_sum": sum(rejected_prepare) if rejected_prepare else 0.0,
            "candidate_attempt_wall_ms_sum": sum(candidate_costs) if candidate_costs else None,
            "cohort_scene_counts": cohorts, "gate_applied_decision_rows": len(gated),
            "gate_screen_evaluations": len(gate_executions), "real_gated_rows_without_bm_attempt": no_bm_real,
            "synthetic_gated_rows_with_bm_attempt": bm_enabled_synthetic,
            "gate_screen_total_ms": sum(gate_cost) if gate_cost else None,
            "gate_screen_mean_ms": sum(gate_cost) / len(gate_cost) if gate_cost else None,
            "gate_sample_comparisons": sum(g.get("comparisons", 0) for g in screen_results),
            "gated_rate_candidate_attempts": gated_attempts, "all_profile_candidate_attempts": attempt_count,
            "comparisons": len(comparisons), "same_canonical_reference_rows": sum(c.get("same_canonical_reference") is True for c in comparisons),
            "control_packet_match_rows": sum(c.get("candidate_packets_match_controls") is True for c in comparisons),
            "gated_candidate_packet_match_rows": sum(c.get("gate_candidates_match_controls") is True for c in comparisons),
            "future_frames": data.get("policy", {}).get("future_frames"), "quality_oracle_for_selection": data.get("policy", {}).get("quality_oracle_for_selection"),
            "regression_tests_present_and_logged_passing": _logged_tests(test_log, regression_names),
            "timing_scope": data.get("timing_scope"), "comparison_scope": data.get("comparison_scope"),
            "resolution_scope": data.get("resolution_scope"), "ownership_scope": data.get("ownership_scope"),
            "format_scope": data.get("format_scope"), "transport_scope": data.get("transport_scope")}


def audit_execution(data: dict) -> dict:
    cases = data.get("cases", [])
    summaries = data.get("summary", [])
    captures = strict = eventual = 0
    unresolved = 0
    strict_mismatches = 0
    paired = []
    factor_totals: dict[str, dict] = {}
    for case in cases:
        r = case.get("result", {})
        captures += int(r.get("capture_count", 0)); strict += int(r.get("presented_strict", 0)); eventual += int(r.get("presented_eventual", 0))
        end = (r.get("capture_window_ms") or [None, None])[1]
        derived = sum(p.get("at_ms", float("inf")) < end for p in r.get("presented", [])) if end is not None else None
        strict_mismatches += int(derived is not None and derived != r.get("presented_strict"))
        slots = r.get("unresolved_sender_slots") or []
        unresolved += int(any(x is not None for x in slots)
                          or any(values and any(x is not None for x in values) for values in (r.get("unresolved_ingress_frames"), r.get("unresolved_credits"), r.get("pending_ids")))
                          or r.get("waiting_at_end") is not None or any(v not in (0, None, False) for v in (r.get("unresolved_cpu") or {}).values()))
        key = f"{case.get('source')}/cache={case.get('cache')}/fast_decoder={case.get('fast_decoder')}/exact_ui={case.get('exact_ui')}"
        bucket = factor_totals.setdefault(key, {"cases": 0, "captures": 0, "strict": 0, "eventual": 0, "python_wall_seconds": 0.0,
                                                "service_tape_values": set(), "peak_sender_packet_bytes": 0,
                                                "peak_ingress_payload_bytes": 0})
        bucket["cases"] += 1; bucket["captures"] += r.get("capture_count", 0)
        bucket["strict"] += r.get("presented_strict", 0); bucket["eventual"] += r.get("presented_eventual", 0)
        bucket["python_wall_seconds"] += r.get("python_wall_seconds", 0)
        bucket["service_tape_values"].add(str(r.get("service_tape")))
        bucket["peak_sender_packet_bytes"] = max(bucket["peak_sender_packet_bytes"], r.get("peak_sender_packet_bytes", 0))
        bucket["peak_ingress_payload_bytes"] = max(bucket["peak_ingress_payload_bytes"], r.get("peak_ingress_payload_bytes", 0))
    for p in data.get("pairs", []):
        paired.append({"source": p.get("source"), "exact_ui": p.get("exact_ui"),
                       "common_prepared_ids": len(p.get("common_prepared_ids", [])),
                       "same_anchor_and_forced_key_ids": len(p.get("same_anchor_and_forced_key_ids", [])),
                       "same_packet_ids": len(p.get("same_packet_ids", [])),
                       "strict_delta": p.get("strict_delta"), "eventual_delta": p.get("eventual_delta")})
    for b in factor_totals.values(): b["service_tape_values"] = sorted(b["service_tape_values"])
    execution_test_log = ROOT / "experiments/python-game-execution-study/tests.log"
    execution_regressions = _logged_tests(execution_test_log, [
        "test_all_four_paths_keep_same_packets_on_fixed_test_clock",
        "test_optimized_actual_fault_packets_drain_and_recover",
        "test_failed_admission_pays_cost_and_never_sends_or_commits",
        "test_frozen_scheduler_copy_preserves_requested_expiry_guard"])
    return {"case_count": len(cases), "capture_events_summed_across_runs": captures,
            "strict_presentations_summed": strict, "eventual_presentations_summed": eventual,
            "strict_timestamp_rederivation_mismatches": strict_mismatches,
            "runs_with_unresolved_work_at_end": unresolved, "factorial_groups": factor_totals,
            "pairs": paired, "summary_rows": summaries,
            "regression_tests_present_and_logged_passing": execution_regressions,
            "actual_wall_observations_available": all(c.get("result", {}).get("python_wall_seconds") is not None for c in cases) if cases else None,
            "actual_wall_equals_charged_service_observations": actual_wall_service_equality(cases),
            "charged_service_tape_is_actual_measurement": False, "hardware_timing_proven": False,
            "service_scope": data.get("service_scope"), "pairing_scope": data.get("pairing_scope"),
            "memory_scope": data.get("memory_scope"), "transport_scope": data.get("transport_scope"),
            "resolution_scope": data.get("resolution_scope"), "omitted": data.get("omitted")}


def audit_ui_cache(data: dict) -> dict:
    cases = data.get("cases", [])
    rows = [r for c in cases for r in c.get("rows", [])]
    identity = {(c.get("name"), r.get("id")) for c in cases for r in c.get("rows", [])}
    hashes = {r.get("source_rgb_sha256") for r in rows if r.get("source_rgb_sha256")}
    hit_attempts = [a for r in rows for a in r.get("cached_attempts", []) if a.get("candidate_details", {}).get("cache_hit") is True]
    changed_hits = [a for r in rows for a in r.get("cached_attempts", [])
                    if a.get("candidate_details", {}).get("cache_hit") is True and r.get("whole_source_changed") is True]
    equal_packets = [r for r in rows if r.get("baseline_packet_sha256") is not None and r.get("baseline_packet_sha256") == r.get("cached_packet_sha256")]
    accepted = [r for r in rows if r.get("accepted") is True]
    entries = [r.get("cache_entries") for r in rows if isinstance(r.get("cache_entries"), int)]
    persistent = [r.get("persistent_cache_bytes") for r in rows if isinstance(r.get("persistent_cache_bytes"), int)]
    test_log = ROOT / "experiments/python-game-ui-cache-study/tests.log"
    tests = ["test_budget_keeps_lookup_validation_paid_and_can_drop_wrapper",
             "test_changed_background_hits_but_changed_words_miss",
             "test_exact_hit_keeps_full_frame_bytes_and_validation",
             "test_rect_canvas_policy_and_four_entry_bounds",
             "test_reused_payload_cap_fallthrough_and_base_rejection",
             "test_rgb888_difference_inside_same565_word_hits"]
    return {"case_count": len(cases), "paired_source_ids_declared": data.get("paired_source_ids"),
            "row_count": len(rows), "unique_case_frame_ids": len(identity), "unique_rgb_content_hashes": len(hashes),
            "native_manifest_targets_720x480": all((c.get("manifest", {}).get("target_width"), c.get("manifest", {}).get("target_height")) == (720, 480) for c in cases if c.get("manifest", {}).get("target_width") is not None) if cases else None,
            "all_rows_720x480": all((r.get("width"), r.get("height")) == (720, 480) for r in rows) if rows else None,
            "cohort_rows": {k: sum(len(c.get("rows", [])) for c in cases if c.get("cohort") == k) for k in sorted({c.get("cohort") for c in cases})},
            "cache_hit_attempts": len(hit_attempts), "hits_on_changed_whole_source": len(changed_hits),
            "max_entries_observed": max(entries) if entries else None,
            "max_persistent_cache_bytes_observed": max(persistent) if persistent else None,
            "complete_frame_packet_hash_equal_rows": len(equal_packets),
            "all_cached_packets_match_baseline": len(equal_packets) == len(rows) if rows else None,
            "accepted_rows": len(accepted),
            "all_accepted_packet_bytes_fit_case_cap": all(r.get("packet_bytes", 10**99) <= c.get("frame_cap", -1)
                for c in cases for r in c.get("rows", []) if r.get("accepted") is True),
            "all_selected_rgb565_words_exact": all(r.get("selected_rgb565_mismatches") == 0 for r in rows) if rows else None,
            "full_validation_ms_recorded_for_cache_hit_attempts": all(isinstance(a.get("validate_ms"), (int, float)) for a in hit_attempts) if hit_attempts else None,
            "regression_tests_present_and_logged_passing": _logged_tests(test_log, tests),
            "timing_scope": data.get("timing_scope"), "memory_scope": data.get("memory_scope"),
            "protocol_scope": data.get("protocol_scope"), "integration_scope": data.get("integration_scope")}


def audit_credit_window(data: dict) -> dict:
    cases = data.get("cases", [])
    captures = strict = eventual = 0
    unresolved_runs = strict_mismatches = 0
    pools = []
    per_case = []
    busy_packets = busy_feed_costs = 0
    cache_hits = patch_attempts = 0
    for c in cases:
        r = c.get("result", {}); cfg = r.get("config", {})
        captures += r.get("capture_count", 0); strict += r.get("presented_strict", 0); eventual += r.get("presented_eventual", 0)
        end = (r.get("capture_window_ms") or [None, None])[1]
        derived = sum(p.get("at_ms", float("inf")) < end for p in r.get("presented", [])) if end is not None else None
        strict_mismatches += int(derived is not None and derived != r.get("presented_strict"))
        slots = r.get("unresolved_sender_slots") or []
        unresolved = (any(x is not None for x in slots)
            or any(v and any(x is not None for x in v) for v in (r.get("pending_ids"), r.get("unresolved_ingress_frames"), r.get("unresolved_credits")))
            or r.get("waiting_at_end") is not None
            or any(v not in (0, None, False) for v in (r.get("unresolved_cpu") or {}).values()))
        unresolved_runs += int(unresolved)
        busy = [p for p in r.get("packets", []) if p.get("ingress_error") == "GF02 busy"]
        busy_packets += len(busy)
        for p in busy:
            busy_feed_costs += sum(x.get("service_ms", 0) for x in r.get("cpu_services", []) if x.get("id") == p.get("id") and x.get("stage") == "feed")
        hybrid_attempts = [a for p in r.get("packets", []) for a in p.get("hybrid", {}).get("attempts", [])]
        patch_attempts += len(hybrid_attempts)
        cache_hits += sum(a.get("candidate_details", {}).get("cache_hit") is True for a in hybrid_attempts)
        pool = {"case": c.get("source"), "credit_window": c.get("credit_window"), "refresh_period": c.get("refresh_period"),
                "config_sender_slots": cfg.get("sender_slots"), "encoder_credit_window": r.get("encoder_credit_window"),
                "config_credit_window": cfg.get("credit_window"), "receiver_ingress_slots": r.get("receiver_ingress_slots"),
                "framebuffer_role_slots": r.get("framebuffer_role_slots"),
                "peak_sender_slots": r.get("peak_sender_slots"), "peak_credits": r.get("peak_credits"),
                "peak_ingress_slots": r.get("peak_ingress_slots"), "peak_framebuffer_roles": r.get("peak_framebuffer_roles")}
        pool["window_and_factory_agree"] = (pool["credit_window"] == pool["config_sender_slots"] == pool["encoder_credit_window"] == pool["config_credit_window"])
        pool["observed_peaks_within_declared_pools"] = (r.get("peak_sender_slots", 10**9) <= cfg.get("sender_slots", -1)
            and r.get("peak_credits", 10**9) <= cfg.get("credit_window", -1)
            and r.get("peak_ingress_slots", 10**9) <= r.get("receiver_ingress_slots", -1)
            and r.get("peak_framebuffer_roles", 10**9) <= r.get("framebuffer_role_slots", -1))
        pools.append(pool)
        per_case.append({"source": c.get("source"), "credit_window": c.get("credit_window"), "refresh_period": c.get("refresh_period"),
                         "captures": r.get("capture_count"), "prepared": r.get("prepared"), "strict": r.get("presented_strict"),
                         "eventual": r.get("presented_eventual"), "diagnostic_ids_per_second": r.get("metrics", {}).get("steady_fps"),
                         "p_credit_wait_ms": r.get("encoder_admission_wait_ms", {}).get("p_credit_limit"),
                         "patch_attempts": len(hybrid_attempts), "patch_cache_hits": sum(a.get("candidate_details", {}).get("cache_hit") is True for a in hybrid_attempts),
                         "full_ingress_busy_packets": len(busy), "unresolved_work": bool(unresolved)})
    pairs = [{"source": p.get("source"), "a_window": p.get("a_window"), "b_window": p.get("b_window"),
              "a_refresh": p.get("a_refresh"), "b_refresh": p.get("b_refresh"),
              "common_prepared_ids": len(p.get("common_prepared_ids", [])),
              "same_anchor_and_forced_key_ids": len(p.get("same_anchor_and_forced_key_ids", [])),
              "same_packet_ids": len(p.get("same_packet_ids", [])), "strict_delta": p.get("strict_delta"),
              "eventual_delta": p.get("eventual_delta")} for p in data.get("pairs", [])]
    test_log = ROOT / "experiments/python-game-credit-window-study/tests.log"
    tests = ["test_full_cap_reject_still_pays_without_extra_sender_commit",
             "test_invalid_pool_bounds_and_factory_disagreement_fail_before_packets",
             "test_late_ack_during_parse_keeps_reader_and_cannot_install_reference",
             "test_expiry_wins_after_deferred_valid_ack_while_duplicate_reader_drains",
             "test_loss_corruption_duplicate_and_wrong_feedback_drain",
             "test_third_sender_hits_finite_two_ingress_and_recovery_is_paid",
             "test_two_credit_trace_matches_frozen_execution_copy",
             "test_ui_cache_keeps_complete_packets_and_fixed_clock_schedule"]
    result_pins = verify_source_pins([data])
    regression_text = (ROOT / "experiments/python-game-credit-window-study/test_credit_window.py").read_text()
    all_service_tapes_none = all(c.get("result", {}).get("service_tape") is None for c in cases)
    return {"case_count": len(cases), "case_count_declared": data.get("case_count"),
            "capture_events_summed_across_runs": captures, "strict_presentations_summed": strict,
            "eventual_presentations_summed": eventual, "strict_timestamp_rederivation_mismatches": strict_mismatches,
            "prepared_total": sum(c.get("result", {}).get("prepared", 0) for c in cases),
            "decoded_commit_total": sum(len(c.get("result", {}).get("commits", [])) for c in cases),
            "runs_with_unresolved_work_at_end": unresolved_runs,
            "all_window_factory_pairs_agree": all(p["window_and_factory_agree"] for p in pools) if pools else None,
            "all_observed_peaks_fit_configured_pools": all(p["observed_peaks_within_declared_pools"] for p in pools) if pools else None,
            "pools_by_case": pools, "full_ingress_busy_packets_in_main_replays": busy_packets,
            "charged_feed_wall_ms_for_busy_packets": busy_feed_costs,
            "all_main_case_service_tapes_none_actual_wall_mode": all_service_tapes_none,
            "patch_attempts": patch_attempts, "patch_cache_hits": cache_hits,
            "paired_runs": pairs, "per_case": per_case,
            "actual_wall_equals_charged_service_observations": actual_wall_service_equality(cases),
            "source_pins": {k: result_pins[k] for k in ("pin_count", "all_match_and_stable", "missing", "mismatched")},
            "regression_tests_present_and_logged_passing": _logged_tests(test_log, tests),
            "expiry_wins_regression_has_serialized_ack_then_nack_and_zero_ack_promotion_assertion":
                "[f['status'] for f in received],[model.transport.ACK,model.transport.NACK]" in regression_text and "self.assertEqual(calls,[])" in regression_text,
            "positive_ack_after_reader_drain_control_assertion_present": "self.assertTrue(any(f['kind']=='deferred_ack_accepted'" in regression_text,
            "unsupported_gate_config_rejection_in_model": "cfg.controller!='normal'" in (ROOT / "experiments/python-game-credit-window-study/model.py").read_text(),
            "scope": {k: data.get(k) for k in ("policy_scope", "cost_scope", "memory_scope", "comparison_scope", "source_scope", "timing_scope", "full_ingress_scope")},
            "hardware_timing_proven": False, "three_credit_window_is_hardware_default": False}


def audit_pending() -> dict:
    available: dict[str, dict] = {}
    states = {}
    for key, path in INPUTS.items():
        if key in AWAITING_FINALIZATION:
            states[key] = {"path": str(path), "status": "awaiting_finalization"}
            continue
        if path.is_file():
            try:
                available[key] = json.loads(path.read_text())
                states[key] = {"path": str(path), "status": "available"}
            except (OSError, json.JSONDecodeError) as exc:
                states[key] = {"path": str(path), "status": "invalid", "error": str(exc)}
        else:
            states[key] = {"path": str(path), "status": "pending"}
    source_pins = verify_source_pins(list(available.values()))
    source_pins_by_input = {k: verify_source_pins([v]) for k, v in available.items()}
    return {"audit_version": 13, "target": {"canvas": [720, 480], "active_image": [720, 405], "fps": 30},
            "inputs": states,
            "source_pins": source_pins,
            "source_pins_by_input": source_pins_by_input,
            "cache_admission_audit": audit_cache(available["cache_admission"]) if "cache_admission" in available else None,
            "motion_gate_audit": audit_motion(available["motion_gate"]) if "motion_gate" in available else None,
            "execution_audit": audit_execution(available["execution"]) if "execution" in available else None,
            "ui_cache_audit": audit_ui_cache(available["ui_cache"]) if "ui_cache" in available else None,
            "credit_window_audit": audit_credit_window(available["credit_window"]) if "credit_window" in available else None,
            "evidence_gaps": [f"results pending: {v['path']}" if v["status"] == "pending" else
                              f"awaiting finalization: {v['path']}" for v in states.values() if v["status"] in ("pending", "awaiting_finalization")],
            "claims_guard": {"missing_results_mean_success": False, "cache_admission_success_inferred": False,
                             "motion_gate_quality_oracle_is_live_policy": False,
                             "declared_service_is_assumed_equal_without_evidence": False,
                             "physical_or_hardware_timing_proven": False, "packet_payload_equals_complete_packet": False}}


if __name__ == "__main__":
    report = audit_pending()
    OUT.joinpath("audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
