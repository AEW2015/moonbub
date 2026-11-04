#!/usr/bin/env python3
"""Evidence-first audit scaffold for v14; absent evidence stays unknown."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
INPUTS = {
    "recent_reference": ROOT / "experiments/python-game-recent-reference-study/results.json",
    "skip_residual": ROOT / "experiments/python-game-skip-residual-study/results.json",
    "finite_reference_ownership": ROOT / "experiments/python-game-reference-ownership-study/results.json",
    "overlap_reference": ROOT / "experiments/python-game-overlap-reference-study/results.json",
}
AWAITING_FINALIZATION: set[str] = set()

def complete_packet_bytes(row: dict[str, Any]) -> int | None:
    """Return only declared whole-wire size; never substitute payload length."""
    v = row.get("complete_packet_bytes", row.get("packet_bytes"))
    return v if isinstance(v, int) and not isinstance(v, bool) else None

def identity_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep capture/source identities separate from identical RGB content."""
    identities, rgb_hashes, cohorts = set(), set(), {}
    missing = 0
    for r in rows:
        source, frame = r.get("source_id", r.get("source")), r.get("frame_id", r.get("id"))
        if source is None or frame is None: missing += 1
        else: identities.add((str(source), str(frame)))
        h = r.get("source_rgb_sha256", r.get("rgb_sha256"))
        if isinstance(h, str) and h: rgb_hashes.add(h)
        cohort = str(r.get("cohort", "unknown")); cohorts[cohort] = cohorts.get(cohort, 0) + 1
    return {"rows": len(rows), "unique_source_frames": len(identities), "rows_missing_identity": missing,
            "unique_rgb_content_hashes": len(rgb_hashes) if rgb_hashes else None, "cohort_rows": cohorts}

def explicit_cost(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> dict[str, Any]:
    """Sum explicit paid-work measurements, including attempts later rejected."""
    observed = [next((r[k] for k in keys if isinstance(r.get(k), (int, float)) and not isinstance(r.get(k), bool)), None) for r in rows]
    rejected = [v for r, v in zip(rows, observed) if v is not None and (r.get("accepted") is False or r.get("admitted") is False or r.get("rejected") is True)]
    values = [v for v in observed if v is not None]
    return {"measured_rows": len(values), "sum_ms": sum(values) if values else None,
            "rejected_measured_rows": len(rejected), "rejected_sum_ms": sum(rejected) if rejected else (0 if values else None)}

def ack_promotion_evidence(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Count promotion only when event explicitly binds accepted ACK to a tag."""
    promotions = [e for e in events if e.get("event") in ("promote", "promotion")]
    bound = [e for e in promotions if e.get("ack_status") == "accepted" and e.get("tag") is not None]
    uncertain = [e for e in promotions if e.get("ack_status") in ("lost", "unknown", None)]
    return {"promotion_events": len(promotions), "ack_tag_bound_promotions": len(bound),
            "lost_or_unknown_ack_promotions": len(uncertain),
            "lost_ack_uncertainty": bool(uncertain) if promotions else None,
            "promotion_ack_safety": False if uncertain else (True if promotions and len(bound) == len(promotions) else None),
            "key_bank_fallbacks": sum(e.get("fallback_bank") == 0 and e.get("fallback_kind") == "key" for e in uncertain)}

def timing_separation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare only paired actual host and virtual/service measurements."""
    pairs = [(r.get("host_wall_ms"), r.get("virtual_ms", r.get("declared_service_ms"))) for r in rows]
    known = [(a, b) for a, b in pairs if isinstance(a, (int, float)) and isinstance(b, (int, float))]
    return {"paired_observations": len(known), "host_wall_sum_ms": sum(a for a, _ in known) if known else None,
            "virtual_or_declared_sum_ms": sum(b for _, b in known) if known else None, "hardware_timing_proven": False}

def resolve_pin(raw: str) -> Path:
    marker = "/moonbub-30fps-study/"
    if marker in raw: return ROOT / raw.split(marker, 1)[1]
    p = Path(raw); return p if p.is_absolute() else ROOT / p

def verify_pins(data: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for raw, expected in data.get("source_sha256", {}).items():
        p = resolve_pin(raw)
        actual_before = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        actual_after = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        rows.append({"path": str(p), "expected": expected, "actual_before": actual_before, "actual_after": actual_after,
                     "matches": actual_before == expected if actual_before is not None else None,
                     "stable_during_audit": actual_before == actual_after})
    return {"pin_count": len(rows), "all_match_and_stable": all(x["matches"] is True and x["stable_during_audit"] for x in rows) if rows else None, "rows": rows}


def audit_skip_residual(data: dict[str, Any]) -> dict[str, Any]:
    """Recompute bounded coding, cap, cost and quality evidence from actual rows."""
    cases = data.get("cases", [])
    profiles = sorted({name for c in cases for name in c.get("profiles", {})})
    per_profile = {}
    for name in profiles:
        rows = [r for c in cases for r in c.get("profiles", {}).get(name, [])]
        admitted = [r for r in rows if r.get("accepted") is True]
        rejected = [r for r in rows if r.get("accepted") is False]
        packets = [r.get("packet_bytes") for r in admitted if isinstance(r.get("packet_bytes"), int)]
        caps = [r.get("frame_cap") for r in rows if isinstance(r.get("frame_cap"), int)]
        prune_records = [p for r in rows for p in r.get("pruning", [])]
        bounded = [p for p in prune_records if p.get("checked_blocks", 0) > 0]
        costs = explicit_cost(rows, ("prepare_ms",))
        plane_choices = [p for r in rows for p in r.get("plane_choices", [])]
        max_delta = max((p.get("max_reconstructed_yuv_delta", 0) for p in bounded), default=0)
        max_bound = max((r.get("level", 0) for r in rows), default=0)
        per_profile[name] = {
            "rows": len(rows), "admitted": len(admitted), "rejected": len(rejected),
            "source_ids": len({(c.get("manifest", {}).get("source"), ((c.get("manifest", {}).get("selected_pts") or [])[r.get("id", -1)] if isinstance(r.get("id"), int) and 0 <= r.get("id") < len(c.get("manifest", {}).get("selected_pts", [])) else r.get("id"))) for c in cases for r in c.get("profiles", {}).get(name, [])}),
            "accepted_complete_packet_bytes_recorded": len(packets),
            "accepted_packet_bytes_max": max(packets) if packets else None,
            "accepted_candidate_bytes_equal_complete_packet_bytes": all(r.get("candidate_bytes") == r.get("packet_bytes") for r in admitted),
            "rejected_candidate_bytes_recorded": sum(isinstance(r.get("candidate_bytes"), int) for r in rejected),
            "rejected_candidates_over_frame_cap": sum(isinstance(r.get("candidate_bytes"), int) and r.get("candidate_bytes") > r.get("frame_cap", -1) for r in rejected),
            "frame_cap_min": min(caps) if caps else None,
            "all_admitted_packets_within_per_row_cap": all(r.get("packet_bytes", 10**99) <= r.get("frame_cap", -1) for r in admitted),
            "rejected_rows_with_paid_prepare_ms": sum(isinstance(r.get("prepare_ms"), (int, float)) for r in rejected),
            "explicit_prepare_cost": costs,
            "explicit_stage_costs_ms": {k: explicit_cost(rows, (k,)) for k in ("analyze_ms", "candidate_ms", "commit_ms", "internal_service_ms")},
            "receive_ms_sum_admitted": sum(r["receive_ms"] for r in admitted if isinstance(r.get("receive_ms"), (int, float))) or None,
            "forward_ipv4_udp_bytes_sum_admitted": sum(r["forward_ipv4_udp_bytes"] for r in admitted if isinstance(r.get("forward_ipv4_udp_bytes"), int)) or None,
            "max_observed_pruned_yuv_delta_vs_quantized_gm": max_delta,
            "max_declared_prune_bound": max_bound,
            "pruned_blocks_checked": sum(p.get("checked_blocks", 0) for p in prune_records),
            "prune_eligible_blocks": sum(p.get("eligible", 0) for p in prune_records),
            "all_checked_prune_blocks_within_row_level_bound": all(p.get("max_reconstructed_yuv_delta", 0) <= r.get("level", 0)
                for r in rows for p in r.get("pruning", []) if p.get("checked_blocks", 0) > 0),
            "protected_rgb565_mismatches": sum(r.get("protected_rgb565_mismatches", 0) for r in rows),
            "all_admitted_outputs_match_recorded_quantized_gm_baseline": all(r.get("decoded_rgb_sha256") == r.get("baseline_rgb_sha256") for r in admitted if "baseline_rgb_sha256" in r),
            "mean_source_active_mse": (sum(r.get("metrics", {}).get("active", {}).get("mse", 0) for r in admitted) / len(admitted)) if admitted else None,
            "mean_source_priority_mse": (sum(r.get("metrics", {}).get("priority", {}).get("mse", 0) for r in admitted) / len(admitted)) if admitted else None,
            "plane_mode_counts": {mode: sum(p.get("mode") == mode for p in plane_choices) for mode in ("dense", "split")},
            "zeroed_blocks": sum(p.get("zeroed", 0) for p in prune_records),
            "dc_only_blocks": sum(p.get("dc_only", 0) for p in prune_records),
            "actual_plane_candidate_attempts": sum(p.get("actual_candidates", 0) for p in plane_choices),
            "summary_by_case": {c.get("name"): c.get("summary", {}).get(name) for c in cases},
        }
    cohorts = {}
    seen = set()
    for c in cases:
        cohort = c.get("cohort", "unknown")
        cohorts[cohort] = cohorts.get(cohort, 0) + c.get("manifest", {}).get("frame_count", 0)
        pts = c.get("manifest", {}).get("selected_pts", [])
        for r in c.get("profiles", {}).get("gm", []):
            idx = r.get("id")
            source_frame = pts[idx] if isinstance(idx, int) and 0 <= idx < len(pts) else idx
            seen.add((c.get("manifest", {}).get("source"), source_frame))
    pins = verify_pins(data)
    per_case_deltas = []
    for c in cases:
        summary = c.get("summary", {})
        base = summary.get("gm", {})
        for pname, vals in summary.items():
            if pname == "gm": continue
            base_bytes, profile_bytes = base.get("mean_packet_bytes"), vals.get("mean_packet_bytes")
            per_case_deltas.append({"case": c.get("name"), "cohort": c.get("cohort"), "profile": pname,
                "mean_packet_bytes": profile_bytes,
                "packet_size_delta_vs_gm_pct": ((profile_bytes / base_bytes - 1) * 100) if isinstance(base_bytes, (int, float)) and base_bytes else None,
                "mean_prepare_delta_ms_vs_gm": (vals.get("mean_prepare_ms_all") - base.get("mean_prepare_ms_all")) if isinstance(vals.get("mean_prepare_ms_all"), (int, float)) and isinstance(base.get("mean_prepare_ms_all"), (int, float)) else None,
                "mean_receive_delta_ms_vs_gm": (vals.get("mean_receive_ms") - base.get("mean_receive_ms")) if isinstance(vals.get("mean_receive_ms"), (int, float)) and isinstance(base.get("mean_receive_ms"), (int, float)) else None,
                "mean_full_service_delta_ms_vs_gm": (vals.get("mean_full_service_ms") - base.get("mean_full_service_ms")) if isinstance(vals.get("mean_full_service_ms"), (int, float)) and isinstance(base.get("mean_full_service_ms"), (int, float)) else None})
    external = []
    for c in cases:
        m = c.get("manifest", {})
        raw, expected = m.get("source"), m.get("source_sha256")
        if raw and expected:
            path = Path(raw)
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            external.append({"path": str(path), "expected": expected, "actual": actual, "matches": actual == expected if actual else None})
    return {
        "case_count": len(cases), "declared_source_ids": data.get("source_ids"), "unique_source_frame_keys": len(seen),
        "duplicate_case_rows_of_same_source_frame": sum(len(c.get("profiles", {}).get("gm", [])) for c in cases) - len(seen),
        "declared_decisions": data.get("decisions"), "decisions_recomputed": sum(len(c.get("profiles", {}).get(p, [])) for c in cases for p in profiles),
        "cohort_source_frame_rows": cohorts, "unique_source_rgb_hashes": len({r.get("source_rgb_sha256") for c in cases for r in c.get("profiles", {}).get("gm", []) if r.get("source_rgb_sha256")}),
        "profiles": per_profile, "profile_deltas_vs_gm_by_case": per_case_deltas, "source_pins": pins,
        "external_media_pins": external,
        "all_present_external_media_pins_match": all(x["matches"] is True for x in external) if external else None,
        "format_scope": data.get("format_scope"), "quality_scope": data.get("quality_scope"),
        "timing_scope": data.get("timing_scope"), "ownership_scope": data.get("ownership_scope"),
        "source_scope": data.get("source_scope"), "host_wall_seconds": data.get("wall_seconds"),
        "study_regression_tests": {"log_present": (ROOT / "experiments/python-game-skip-residual-study/tests.log").is_file(),
            "passed_count": (ROOT / "experiments/python-game-skip-residual-study/tests.log").read_text().count(" ... ok"),
            "failure_marker_present": "FAILED" in (ROOT / "experiments/python-game-skip-residual-study/tests.log").read_text()},
        "read_only_verification_log": (json.loads((ROOT / "experiments/python-game-skip-residual-study/verify.log").read_text())
            if (ROOT / "experiments/python-game-skip-residual-study/verify.log").is_file() else None),
        "physical_30fps_proven": False,
    }


def audit_recent_reference(data: dict[str, Any]) -> dict[str, Any]:
    """Audit AR01/AF01 attempts, published bank bindings and paid promotion work."""
    scenes = data.get("scenes", [])
    profiles = sorted({p for sc in scenes for p in sc.get("profiles", {})})
    per_profile = {}
    reference_checks = []
    for pname in profiles:
        rows = [(sc, r) for sc in scenes for r in sc.get("profiles", {}).get(pname, [])]
        accepted = [(sc, r) for sc, r in rows if r.get("accepted") is True]
        rejected = [(sc, r) for sc, r in rows if r.get("accepted") is False]
        promotions = [(sc, r) for sc, r in rows if r.get("promoted") is True]
        enc_infos = [r.get("encoder_info", {}) for _, r in rows]
        rx_infos = [r.get("receiver_info", {}) for _, r in rows]
        total_packet = [r.get("packet_bytes") for _, r in accepted if isinstance(r.get("packet_bytes"), int)]
        caps_ok = all(r.get("packet_bytes", 10**99) <= r.get("cap", -1) for _, r in accepted)
        reject_costs = [r.get("prepare_ms") for _, r in rejected if isinstance(r.get("prepare_ms"), (int, float))]
        prep = [r.get("prepare_ms") for _, r in rows if isinstance(r.get("prepare_ms"), (int, float))]
        recv = [r.get("receive_ms") for _, r in accepted if isinstance(r.get("receive_ms"), (int, float))]
        feedback = [r.get("feedback_ms") for _, r in accepted if isinstance(r.get("feedback_ms"), (int, float))]
        complete = [r.get("complete_service_ms") for _, r in accepted if isinstance(r.get("complete_service_ms"), (int, float))]
        promotion_work = [(r, r.get("encoder_info", {})) for _, r in rows if r.get("promotion_requested") is True]
        prom_costs = [x.get("reconstruction_ms", 0) + x.get("reference_tag_ms", 0) for _, x in promotion_work
                      if isinstance(x.get("reconstruction_ms"), (int, float)) and isinstance(x.get("reference_tag_ms"), (int, float))]
        valid_promoted_bindings = invalid_promoted_bindings = 0
        valid_key_bindings = invalid_key_bindings = 0
        scene_reference_checks = []
        for sc in scenes:
            state: dict[str, Any] = {"0": None, "1": None}
            for r in sc.get("profiles", {}).get(pname, []):
                if r.get("reference_id") is not None and r.get("reference_bank") in (0, 1):
                    bank = str(r.get("reference_bank")); prior = state.get(bank)
                    good = isinstance(prior, dict) and prior.get("frame_id") == r.get("reference_id") and prior.get("tag") == r.get("reference_tag")
                    scene_reference_checks.append(good)
                banks = r.get("acknowledged_banks")
                if not isinstance(banks, dict):
                    continue
                if r.get("promoted") is True:
                    dest = banks.get(str(r.get("destination_bank")))
                    good = (isinstance(dest, dict) and dest.get("frame_id") == r.get("id") and
                            dest.get("tag") == r.get("stored_tag") and r.get("stored_tag") is not None)
                    valid_promoted_bindings += int(good); invalid_promoted_bindings += int(not good)
                elif r.get("key") is True and r.get("accepted") is True:
                    dest = banks.get("0")
                    good = isinstance(dest, dict) and dest.get("frame_id") == r.get("id") and dest.get("tag") == r.get("stored_tag")
                    valid_key_bindings += int(good); invalid_key_bindings += int(not good)
                if r.get("accepted") is True:
                    state = {"0": banks.get("0"), "1": banks.get("1")}
        reference_checks.extend(scene_reference_checks)
        per_profile[pname] = {
            "attempt_rows": len(rows), "accepted": len(accepted), "rejected": len(rejected),
            "accepted_complete_packet_bytes_recorded": len(total_packet), "accepted_packet_bytes_sum": sum(total_packet) if total_packet else None,
            "accepted_packet_bytes_max": max(total_packet) if total_packet else None,
            "outer_envelope_bytes_counts": {str(n): sum(r.get("encoder_info", {}).get("envelope_bytes") == n for _, r in accepted) for n in sorted({r.get("encoder_info", {}).get("envelope_bytes") for _, r in accepted if isinstance(r.get("encoder_info", {}).get("envelope_bytes"), int)})},
            "all_accepted_full_packets_within_cap": caps_ok,
            "rejected_candidate_bytes_recorded": sum(isinstance(r.get("attempted_bytes"), int) for _, r in rejected),
            "rejected_candidates_over_cap": sum(isinstance(r.get("attempted_bytes"), int) and r.get("attempted_bytes") > r.get("cap", -1) for _, r in rejected),
            "rejected_rows_with_paid_prepare_ms": len(reject_costs), "rejected_paid_prepare_ms_sum": sum(reject_costs) if reject_costs else (0 if rejected else None),
            "prepare_ms_sum_all_attempts": sum(prep) if prep else None,
            "receive_ms_sum_accepted": sum(recv) if recv else None, "feedback_ms_sum_accepted": sum(feedback) if feedback else None,
            "complete_service_ms_sum_accepted": sum(complete) if complete else None,
            "promotion_requested_rows": len(promotion_work), "promotion_completed_rows": len(promotions),
            "promotion_reconstruction_and_tag_work_paid_rows": sum(x.get("promotion_reconstruction_paid") is True for _, x in promotion_work),
            "promotion_reconstruction_plus_tag_ms_sum_requested": sum(prom_costs) if prom_costs else None,
            "promotion_reconstruction_ms_sum_requested": sum(x.get("reconstruction_ms", 0) for _, x in promotion_work if isinstance(x.get("reconstruction_ms"), (int, float))) or None,
            "promotion_tag_read_bytes_sum_requested": sum(x.get("tag_read_bytes", 0) for _, x in promotion_work if isinstance(x.get("tag_read_bytes"), int)) or None,
            "promotion_outer_body_equals_complete_packet_bytes": all(r.get("packet_bytes") == r.get("attempted_bytes") == r.get("encoder_info", {}).get("bytes") for _, r in accepted),
            "promoted_bank_frame_tag_bindings_valid": valid_promoted_bindings,
            "promoted_bank_frame_tag_bindings_invalid": invalid_promoted_bindings,
            "key_publication_frame_tag_bindings_valid": valid_key_bindings,
            "key_publication_frame_tag_bindings_invalid": invalid_key_bindings,
            "max_receiver_retained_banks_reported": max((x.get("retained_banks", 0) for x in rx_infos), default=None),
            "max_receiver_retained_reference_array_bytes_reported": max((x.get("retained_reference_array_bytes", 0) for x in rx_infos), default=None),
            "accepted_feedback_drains_report_zero_pending": all(r.get("pending_after_feedback") == 0 for _, r in accepted),
            "accepted_feedback_hash_recorded_rows": sum(bool(r.get("feedback_sha256")) for _, r in accepted),
            "decoded_rgb_hash_matches_expected": sum(r.get("decoded_rgb_sha256") == r.get("expected_rgb_sha256") for _, r in accepted),
            "accepted_rows_with_ack_bank_snapshot": sum(isinstance(r.get("acknowledged_banks"), dict) for _, r in accepted),
            "same_reconstructed_bank_asserted_rows": sum(r.get("same_reconstructed_banks") is True for _, r in rows),
            "summary_from_study": next((sc.get("summary", {}).get(pname) for sc in scenes if pname in sc.get("summary", {})), None),
        }
    scene_summaries = []
    for sc in scenes:
        summary = sc.get("summary", {})
        gm = summary.get("gm_immutable", {})
        imm = summary.get("ar_immutable", {})
        recent = summary.get("ar_recent8", {})
        def mean(v, k): return v.get(k, {}).get("mean") if isinstance(v.get(k), dict) else None
        scene_summaries.append({"scene": sc.get("source"), "cohort": sc.get("cohort"),
            "source_ids": sc.get("manifest", {}).get("frame_count"),
            "source_fps": sc.get("manifest", {}).get("source_fps"),
            "unique_source_rgb_hashes": sc.get("manifest", {}).get("unique_frame_count"),
            "recent_minus_immutable_packet_bytes_mean": mean(recent, "packet_bytes") - mean(imm, "packet_bytes") if mean(recent, "packet_bytes") is not None and mean(imm, "packet_bytes") is not None else None,
            "recent_packet_bytes_delta_vs_immutable_pct": ((mean(recent, "packet_bytes") / mean(imm, "packet_bytes") - 1) * 100) if mean(recent, "packet_bytes") and mean(imm, "packet_bytes") else None,
            "recent_active_psnr": recent.get("regions", {}).get("active", {}).get("psnr"),
            "immutable_active_psnr": imm.get("regions", {}).get("active", {}).get("psnr"),
            "recent_prepare_mean_ms": mean(recent, "prepare_ms_all"), "immutable_prepare_mean_ms": mean(imm, "prepare_ms_all"),
            "recent_receive_mean_ms": mean(recent, "receive_ms"), "immutable_receive_mean_ms": mean(imm, "receive_ms"),
            "recent_complete_service_mean_ms": mean(recent, "complete_service_ms"), "immutable_complete_service_mean_ms": mean(imm, "complete_service_ms"),
            "comparison_rows": len(sc.get("comparisons", [])),
            "gm_inner_equal_and_immutable_pixels_equal": all(x.get("gm_inner_equal") is True and x.get("immutable_pixels_equal") is True for x in sc.get("comparisons", [])) if sc.get("comparisons") else None,
        })
    native_rows = sum(sc.get("manifest", {}).get("frame_count", 0) for sc in scenes if sc.get("cohort") != "synthetic")
    source_pins = verify_pins(data)
    external = []
    for sc in scenes:
        m = sc.get("manifest", {}); raw, expected = m.get("source"), m.get("source_sha256")
        if raw and expected:
            path = Path(raw); actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            external.append({"path": str(path), "expected": expected, "actual": actual, "matches": actual == expected if actual else None})
    test_path = ROOT / "experiments/python-game-recent-reference-study/tests.log"
    test_text = test_path.read_text() if test_path.is_file() else ""
    verify_path = ROOT / "experiments/python-game-recent-reference-study/verify.log"
    verify = json.loads(verify_path.read_text()) if verify_path.is_file() else None
    test_names = {line.split(" ")[0] for line in test_text.splitlines() if line.endswith(" ... ok")}
    return {"scene_count": len(scenes), "declared_native_source_ids": data.get("native_source_ids"),
        "native_manifest_source_ids": native_rows, "attempted_packets_declared": data.get("attempted_packets"),
        "attempt_rows_recomputed": sum(len(sc.get("profiles", {}).get(p, [])) for sc in scenes for p in profiles),
        "decoded_packets_declared": data.get("decoded_packets"),
        "cohort_source_ids": {cohort: sum(sc.get("manifest", {}).get("frame_count", 0) for sc in scenes if sc.get("cohort") == cohort) for cohort in sorted({sc.get("cohort", "unknown") for sc in scenes})},
        "unique_native_source_rgb_hashes": len({r.get("input_sha256") for sc in scenes if sc.get("cohort") != "synthetic" for r in sc.get("profiles", {}).get("gm_immutable", []) if r.get("input_sha256")}),
        "profiles": per_profile, "by_scene": scene_summaries,
        "all_prior_reference_frame_tag_bindings_match_acknowledged_state": all(reference_checks) if reference_checks else None,
        "compared_reference_bindings": len(reference_checks),
        "source_pins": source_pins, "external_media_pins": external,
        "all_present_external_media_pins_match": all(x["matches"] is True for x in external) if external else None,
        "source_regression_tests": {"log_present": test_path.is_file(), "passed_count": test_text.count(" ... ok"), "failure_marker_present": "FAILED" in test_text,
            "named": sorted(test_names),
            "physical_reader_leases_block_overwrite": "test_physical_leases_block_overwrite_and_have_owned_release" in test_names,
            "lost_promotion_ack_disables_bank_and_falls_back_to_key": "test_lost_promotion_ack_disables_old_bank_and_falls_back_to_key" in test_names,
            "feedback_binds_outer_body_session_and_published_reference": "test_feedback_binds_outer_body_session_and_published_reference" in test_names,
            "begin_complete_abort_publication_boundaries": "test_begin_complete_and_abort_hold_reader_without_early_publication" in test_names,
            "cap_rejection_pays_promotion_work_without_commit": "test_cap_rejection_before_state_commit_pays_promotion_work" in test_names},
        "lost_ack_safety_evidence_scope": "Lost-promotion-ACK fallback is a passing isolated regression test; no loss is inferred from benchmark rows.",
        "read_only_verification_log": verify, "total_python_host_wall_seconds": data.get("total_python_wall_seconds"),
        "timing_scope": data.get("timing_scope"), "reference_scope": data.get("reference_scope"),
        "memory_scope": data.get("memory_scope"), "deployment_scope": data.get("deployment_scope"), "physical_30fps_proven": False}


def audit_finite_ownership(data: dict[str, Any]) -> dict[str, Any]:
    """Recompute finite AR01/GF02 case counts, paid work, bounds and fault timing."""
    cases = data.get("cases", [])
    case_rows = []
    all_work = []
    all_media = []
    nacks = []
    expected_input_rows = 0
    for c in cases:
        r = c.get("result", {})
        cfg = r.get("config", {})
        packets, commits, work = r.get("packets", []), r.get("commits", []), r.get("work", [])
        wire, feedback = r.get("wire", []), r.get("feedback", [])
        all_work.extend(work)
        all_media.append({"source": c.get("manifest", {}).get("source"), "sha256": c.get("manifest", {}).get("source_sha256")})
        captures = r.get("capture_count", 0); expected_input_rows += captures
        accepted = [p for p in packets if p.get("admitted") is True]
        rejected = [p for p in packets if p.get("admitted") is False]
        stage_counts = {}
        for w in work: stage_counts[w.get("stage", "unknown")] = stage_counts.get(w.get("stage", "unknown"), 0) + 1
        stage_pairs = [(w.get("wall_ms"), w.get("service_ms")) for w in work
                       if isinstance(w.get("wall_ms"), (int, float)) and isinstance(w.get("service_ms"), (int, float))]
        caps_ok = all(p.get("bytes", 10**99) <= cfg.get("frame_cap", -1) for p in accepted)
        reject_clean = all(not p.get("wire_owned") and not p.get("feed_owned") and not p.get("decode_owned") and
                           not any(w.get("id") == p.get("id") and w.get("stage") in ("packetize", "feed_batch", "decode_begin", "decode_complete") for w in work)
                           for p in rejected)
        strict_derived = sum(p.get("at_ms", 10**99) < r.get("capture_window_ms", [0, -1])[1] for p in r.get("presented", []))
        admitted_bytes = [p.get("bytes") for p in accepted if isinstance(p.get("bytes"), int)]
        for p in packets:
            if p.get("expiry_requested") == "receiver_nack":
                ack_deadline = (p.get("send_started_ms") or 0) + cfg.get("ack_timeout_ms", 0)
                matching = [f for f in feedback if f.get("kind") == "parsed" and f.get("id") == p.get("id") and f.get("status") == 2 and f.get("accepted") is True]
                nacks.append({"case": c.get("profile"), "source": c.get("source"), "id": p.get("id"),
                    "receiver_route_present": p.get("receiver_route") is not None,
                    "accepted_route_nack_parse_times_ms": [f.get("at_ms") for f in matching],
                    "expiry_requested_ms": p.get("expiry_requested_ms"), "ack_timeout_deadline_ms": ack_deadline,
                    "nack_arrived_before_ack_timeout": bool(matching) and all(f.get("at_ms", 10**99) < ack_deadline for f in matching),
                    "released_by": p.get("release_reason")})
        presentation_rows = r.get("presented", [])
        work_sum = sum(w.get("wall_ms", 0) for w in work if isinstance(w.get("wall_ms"), (int, float)))
        service_sum = sum(w.get("service_ms", 0) for w in work if isinstance(w.get("service_ms"), (int, float)))
        case_rows.append({
            "source": c.get("source"), "profile": c.get("profile"),
            "cohort": ("synthetic" if c.get("manifest", {}).get("synthetic") else "heldout_long" if "heldout" in c.get("source", "") else "native_temporal"),
            "captures": captures, "prepared_packets": len(packets), "accepted_packets": len(accepted), "rejected_packets": len(rejected),
            "decoded_commits": len(commits), "presented_eventual_recomputed": len(presentation_rows),
            "presented_strict_recorded": r.get("presented_strict"), "presented_strict_recomputed": strict_derived,
            "strict_presentation_count_matches": strict_derived == r.get("presented_strict"),
            "full_packet_bytes_sum": sum(admitted_bytes) if admitted_bytes else None,
            "all_accepted_packets_within_full_cap": caps_ok, "rejected_work_has_no_wire_or_decode_commit": reject_clean,
            "frame_batched_wire_events": len(wire), "frame_batched_wire_bytes": sum(w.get("bytes", 0) for w in wire),
            "feedback_events_by_kind": {k: sum(f.get("kind") == k for f in feedback) for k in sorted({f.get("kind", "unknown") for f in feedback})},
            "work_stage_counts": stage_counts, "work_wall_ms_sum": work_sum, "work_service_ms_sum": service_sum,
            "work_wall_service_pairs": len(stage_pairs), "work_wall_service_mismatches": sum(a != b for a, b in stage_pairs),
            "unresolved_ids": len(r.get("unresolved_ids", [])), "unresolved_encoder_pending": len(r.get("unresolved_encoder_pending", [])),
            "unresolved_ingress": len(r.get("unresolved_ingress", [])), "unresolved_receiver_readers": r.get("unresolved_receiver_readers"),
            "unresolved_decode": r.get("unresolved_decode"), "unresolved_sender_slots": r.get("unresolved_sender_slots"),
            "resource_peaks": {k: r.get(k) for k in ("peak_sender", "peak_pending", "peak_ingress", "peak_framebuffers", "peak_feedback")},
            "resource_peaks_within_limits": (r.get("peak_sender", 10**9) <= cfg.get("window", -1) and
                r.get("peak_pending", 10**9) <= cfg.get("window", -1) and r.get("peak_ingress", 10**9) <= 2 and
                r.get("peak_framebuffers", 10**9) <= 3 and r.get("peak_feedback", 10**9) <= 4),
            "config": {k: cfg.get(k) for k in ("fps", "width", "height", "frame_cap", "window", "promotion_period", "refresh_period", "link_mbps", "feedback_mbps", "qspi_mbps", "feedback_latency_ms", "drop_first_key_chunk", "drop_first_promotion_ack", "conflict_first_promotion_feedback")},
            "python_wall_seconds": r.get("python_wall_seconds"), "diagnostic_ids_per_second": r.get("diagnostic_ids_per_second"),
        })
    pins = verify_pins(data)
    source_frames = set(); source_hashes = set(); cohorts: dict[str, int] = {}
    for c in cases:
        m = c.get("manifest", {}); cohort = ("synthetic" if m.get("synthetic") else "heldout_long" if "heldout" in c.get("source", "") else "native_temporal")
        cohorts[cohort] = cohorts.get(cohort, 0) + m.get("frame_count", 0)
        pts, hashes = m.get("selected_pts", []), m.get("frame_sha256", [])
        source_name = m.get("source_sha256", m.get("source"))
        for idx, content_hash in enumerate(hashes):
            frame_id = pts[idx] if idx < len(pts) else idx
            source_frames.add((source_name, frame_id))
            if content_hash: source_hashes.add(content_hash)
    media_checks = []
    for c in cases:
        m = c.get("manifest", {}); raw, expected = m.get("source"), m.get("source_sha256")
        if raw and expected:
            p = Path(raw); actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
            media_checks.append({"path": str(p), "expected": expected, "actual": actual, "matches": actual == expected if actual else None})
    test_path = ROOT / "experiments/python-game-reference-ownership-study/tests.log"
    test_text = test_path.read_text() if test_path.is_file() else ""
    test_names = {line.split(" ")[0] for line in test_text.splitlines() if line.endswith(" ... ok")}
    verify_path = ROOT / "experiments/python-game-reference-ownership-study/verify.log"
    verify_text = verify_path.read_text() if verify_path.is_file() else ""
    verify_record = {"present": verify_path.is_file(), "text": verify_text.strip() or None}
    summary = data.get("summary", [])
    # Fault outcomes are joined to model-generated transport and feedback events.
    by_profile = {c.get("profile"): c.get("result", {}) for c in cases}
    dropped_key = by_profile.get("key_chunk_loss", {})
    lost_promo = by_profile.get("promotion_ack_loss", {})
    conflict = by_profile.get("conflicting_promotion_feedback", {})
    key_drop_packets = [p for p in dropped_key.get("packets", []) if p.get("fault_key_chunk_dropped")]
    lost_ack_packets = [p for p in lost_promo.get("packets", []) if p.get("release_reason") == "ack_timeout"]
    conflict_feedback = conflict.get("feedback", [])
    deferred_ack_discarded = sum(f.get("kind") == "ack_discarded_after_expiry" for f in conflict_feedback)
    return {
        "case_count_declared": data.get("case_count"), "case_count_recomputed": len(cases),
        "capture_events_declared_by_case": sum(c.get("result", {}).get("capture_count", 0) for c in cases),
        "capture_cohort_rows": cohorts, "unique_source_frame_identities_across_profiles": len(source_frames),
        "unique_source_rgb_hashes_across_frame_manifests": len(source_hashes),
        "capture_inputs_recomputed": expected_input_rows, "prepared_attempts": sum(len(c.get("result", {}).get("packets", [])) for c in cases),
        "decoded_commits": sum(len(c.get("result", {}).get("commits", [])) for c in cases),
        "source_pins": pins, "external_media_pins": media_checks,
        "all_external_media_pins_match": all(x["matches"] is True for x in media_checks) if media_checks else None,
        "total_python_host_wall_seconds": data.get("total_python_wall_seconds"),
        "case_rows": case_rows, "summary_rows": summary,
        "total_recorded_stage_wall_ms": sum(w.get("wall_ms", 0) for w in all_work if isinstance(w.get("wall_ms"), (int, float))),
        "total_recorded_stage_service_ms": sum(w.get("service_ms", 0) for w in all_work if isinstance(w.get("service_ms"), (int, float))),
        "recorded_stage_timing_pairs": sum(isinstance(w.get("wall_ms"), (int, float)) and isinstance(w.get("service_ms"), (int, float)) for w in all_work),
        "recorded_stage_wall_service_mismatches": sum(w.get("wall_ms") != w.get("service_ms") for w in all_work if isinstance(w.get("wall_ms"), (int, float)) and isinstance(w.get("service_ms"), (int, float))),
        "all_cases_resource_bounded": all(x["resource_peaks_within_limits"] for x in case_rows),
        "all_case_strict_counts_rederived": all(x["strict_presentation_count_matches"] for x in case_rows),
        "all_cases_drained_at_end": all(x["unresolved_ids"] == 0 and x["unresolved_encoder_pending"] == 0 and x["unresolved_ingress"] == 0 and x["unresolved_receiver_readers"] == 0 and x["unresolved_decode"] is False and all(v is None for v in (x["unresolved_sender_slots"] or [])) for x in case_rows),
        "route_nacks": nacks,
        "route_nacks_arrived_before_host_ack_expiry": all(x["receiver_route_present"] and x["nack_arrived_before_ack_timeout"] for x in nacks) if nacks else None,
        "key_chunk_fault_case": {"configured": bool(dropped_key.get("config", {}).get("drop_first_key_chunk")),
            "faulted_packets": len(key_drop_packets), "expiry_reasons": [p.get("release_reason") for p in key_drop_packets],
            "nack_wire_count_for_faulted_frame": sum(f.get("kind") == "wire" and f.get("id") == (key_drop_packets[0].get("id") if key_drop_packets else -1) for f in dropped_key.get("feedback", []))},
        "promotion_ack_loss_case": {"configured": bool(lost_promo.get("config", {}).get("drop_first_promotion_ack")),
            "lost_ack_feedback_events": sum(f.get("kind") == "lost" for f in lost_promo.get("feedback", [])),
            "promotion_released_on_timeout": len(lost_ack_packets), "no_nack_fabricated_for_lost_ack": not any(f.get("kind") == "parsed" and f.get("status") == 2 for f in lost_promo.get("feedback", []))},
        "conflicting_feedback_case": {"configured": bool(conflict.get("config", {}).get("conflict_first_promotion_feedback")),
            "accepted_ack_and_nack_for_same_promotion": any(sum(f.get("kind") == "parsed" and f.get("id") == p.get("id") and f.get("status") == 1 for f in conflict_feedback) > 0 and sum(f.get("kind") == "parsed" and f.get("id") == p.get("id") and f.get("status") == 2 for f in conflict_feedback) > 0 for p in conflict.get("packets", []) if p.get("promoted")),
            "ack_applied_after_conflicting_nack": any(f.get("kind") == "ack_applied" and f.get("id") == p.get("id") for f in conflict_feedback for p in conflict.get("packets", []) if p.get("promoted") and p.get("expiry_requested") == "receiver_nack"),
            "ack_discarded_after_expiry_events": deferred_ack_discarded,
            "expired_promotion_rows": sum(p.get("release_reason") == "receiver_nack" for p in conflict.get("packets", []))},
        "regression_tests": {"log_present": test_path.is_file(), "passed_count": test_text.count(" ... ok"), "failure_marker_present": "FAILED" in test_text,
            "paid_ack_expiry_cannot_publish": "test_timeout_during_paid_ack_work_cannot_publish_future_reference" in test_names,
            "paid_receiver_completion_deadline_aborts_publication": "test_deadline_during_paid_decoder_completion_aborts_publication" in test_names,
            "deferred_ack_expiry_wins": "test_conflicting_feedback_expiry_wins_deferred_ack" in test_names,
            "lost_promotion_ack_falls_back": "test_lost_promotion_ack_does_not_promote_sender_and_falls_back" in test_names,
            "rejected_work_has_no_wire_or_publication": "test_rejected_work_has_no_wire_or_bank_publication" in test_names},
        "read_only_verifier_log": verify_record,
        "timing_scope": data.get("timing_scope"), "transport_scope": data.get("transport_scope"),
        "publication_scope": data.get("publication_scope"), "protocol_scope": data.get("protocol_scope"),
        "memory_scope": data.get("memory_scope"), "source_scope": data.get("source_scope"),
        "selection_scope": data.get("selection_scope"), "hardware_timing_proven": False,
    }


def audit_overlap_reference(data: dict[str, Any]) -> dict[str, Any]:
    """Audit bank-specific overlap, using paired IDs and the actual case event traces."""
    base = audit_finite_ownership(data)
    cases = {(c.get("source"), c.get("profile")): c for c in data.get("cases", [])}
    pairs = []
    for pair in data.get("pairs", []):
        src, control_name, candidate_name = pair.get("source"), pair.get("control"), pair.get("candidate")
        control = cases.get((src, control_name), {}).get("result", {})
        candidate = cases.get((src, candidate_name), {}).get("result", {})
        c_packets = {p.get("id"): p for p in control.get("packets", []) if p.get("admitted") is True}
        n_packets = {p.get("id"): p for p in candidate.get("packets", []) if p.get("admitted") is True}
        common_admitted = set(c_packets) & set(n_packets)
        c_prepared = {p.get("id") for p in control.get("packets", [])}
        n_prepared = {p.get("id") for p in candidate.get("packets", [])}
        c_presented = {p.get("id") for p in control.get("presented", [])}
        n_presented = {p.get("id") for p in candidate.get("presented", [])}
        c_steady = control.get("steady_window_ms") or []
        n_steady = candidate.get("steady_window_ms") or []
        c_steady_count = sum(len(c_steady) == 2 and c_steady[0] <= p.get("at_ms", -1) < c_steady[1] for p in control.get("presented", []))
        n_steady_count = sum(len(n_steady) == 2 and n_steady[0] <= p.get("at_ms", -1) < n_steady[1] for p in candidate.get("presented", []))
        c_body = [p.get("bytes") for p in control.get("packets", []) if p.get("admitted") is True and isinstance(p.get("bytes"), int)]
        n_body = [p.get("bytes") for p in candidate.get("packets", []) if p.get("admitted") is True and isinstance(p.get("bytes"), int)]
        same_choice = {i for i in common_admitted if all(c_packets[i].get(k) == n_packets[i].get(k)
            for k in ("key", "promoted", "reference_bank", "reference_id", "reference_tag", "destination_bank"))}
        exact_hash = all(c_packets[i].get("packet_sha256") == n_packets[i].get("packet_sha256") for i in same_choice)
        c_commits = {r.get("id"): r for r in control.get("commits", [])}
        n_commits = {r.get("id"): r for r in candidate.get("commits", [])}
        common_decoded = set(c_commits) & set(n_commits)
        mse_delta = [n_commits[i].get("active_rgb565_mse", 0) - c_commits[i].get("active_rgb565_mse", 0)
                     for i in common_decoded if isinstance(n_commits[i].get("active_rgb565_mse"), (int, float)) and isinstance(c_commits[i].get("active_rgb565_mse"), (int, float))]
        pairs.append({"source": src, "control": control_name, "candidate": candidate_name,
            "prepared_id_sets_equal": c_prepared == n_prepared, "prepared_ids_missing_from_control": sorted(n_prepared - c_prepared),
            "prepared_ids_missing_from_candidate": sorted(c_prepared - n_prepared),
            "presented_id_sets_equal": c_presented == n_presented,
            "presented_ids_missing_from_control": sorted(n_presented - c_presented),
            "presented_ids_missing_from_candidate": sorted(c_presented - n_presented),
            "steady_window_count_control_recomputed": c_steady_count, "steady_window_count_candidate_recomputed": n_steady_count,
            "steady_window_control_ms": c_steady, "steady_window_candidate_ms": n_steady,
            "mean_complete_body_bytes_control_recomputed": sum(c_body) / len(c_body) if c_body else None,
            "mean_complete_body_bytes_candidate_recomputed": sum(n_body) / len(n_body) if n_body else None,
            "mean_body_bytes_delta_pct_recomputed": ((sum(n_body) / len(n_body)) / (sum(c_body) / len(c_body)) - 1) * 100 if c_body and n_body and sum(c_body) else None,
            "forward_ipv4_udp_bytes_control": control.get("forward_ipv4_udp_bytes"), "forward_ipv4_udp_bytes_candidate": candidate.get("forward_ipv4_udp_bytes"),
            "forward_bytes_delta_pct": ((candidate.get("forward_ipv4_udp_bytes", 0) / control.get("forward_ipv4_udp_bytes", 1)) - 1) * 100 if control.get("forward_ipv4_udp_bytes") else None,
            "common_admitted_ids_recomputed": sorted(common_admitted), "declared_common_admitted_count": len(pair.get("common_admitted_ids", [])),
            "same_reference_and_promotion_choice_ids_recomputed": sorted(same_choice),
            "declared_same_choice_count": len(pair.get("same_reference_and_promotion_ids", [])),
            "same_choice_packet_hashes_exact_recomputed": exact_hash,
            "common_decoded_ids_recomputed": sorted(common_decoded), "declared_common_decoded_count": len(pair.get("common_decoded_ids", [])),
            "common_decoded_active_rgb565_mse_delta_mean_recomputed": sum(mse_delta) / len(mse_delta) if mse_delta else None,
            "declared_common_decoded_active_mse_delta_mean": pair.get("common_decoded_active_mse_delta_mean"),
            "strict_delta_recomputed": candidate.get("presented_strict", 0) - control.get("presented_strict", 0),
            "eventual_delta_recomputed": candidate.get("presented_eventual", 0) - control.get("presented_eventual", 0),
            "caveat": pair.get("caveat")})
    policy_rows = []
    for row in base["case_rows"]:
        c = cases.get((row["source"], row["profile"]), {})
        result = c.get("result", {})
        packets = result.get("packets", [])
        summary = next((s for s in data.get("summary", []) if s.get("source") == row["source"] and s.get("profile") == row["profile"]), {})
        policy_rows.append({"source": row["source"], "profile": row["profile"], "policy": summary.get("policy"),
            "captures": row["captures"], "prepared": row["prepared_packets"], "decoded": row["decoded_commits"],
            "strict": row["presented_strict_recomputed"], "eventual": row["presented_eventual_recomputed"],
            "diagnostic_ids_per_second": summary.get("diagnostic_ids_per_second"),
            "accepted_promotions_reported": summary.get("accepted_promotions"),
            "bank1_references_reported": summary.get("bank1_references"),
            "bank0_fallbacks_recomputed": sum(p.get("admitted") is True and p.get("bank0_fallback") is True for p in packets),
            "bank1_references_recomputed": sum(p.get("admitted") is True and p.get("reference_bank") == 1 for p in packets),
            "key0_during_pending_writer_recomputed": sum(p.get("admitted") is True and p.get("bank0_fallback") is True and p.get("info", {}).get("pending_writers_before", 0) > 0 for p in packets),
            "promotions_with_pending_key0_recomputed": sum(p.get("admitted") is True and p.get("promoted") is True and p.get("info", {}).get("pending_bank0_consumers", 0) > 0 for p in packets),
            "bank0_fallbacks_reported": summary.get("bank0_fallbacks"),
            "key0_during_pending_writer_reported": summary.get("key0_during_pending_writer"),
            "promotions_with_pending_key0_reported": summary.get("promotions_with_pending_key0"),
            "promotion_reconstruction_ms": summary.get("promotion_reconstruction_ms"),
            "reference_tag_ms": summary.get("reference_tag_ms"),
            "forward_ipv4_udp_bytes": summary.get("forward_ipv4_udp_bytes"),
            "mean_packet_bytes": summary.get("mean_packet_bytes"),
            "active_rgb565_mse_mean": summary.get("active_rgb565_mse_mean"),
            "admission_wait_ms": summary.get("admission_wait_ms"), "drops": summary.get("drops")})
    tests = base.get("regression_tests", {})
    verify = base.get("read_only_verifier_log", {})
    test_path = ROOT / "experiments/python-game-overlap-reference-study/tests.log"
    test_text = test_path.read_text() if test_path.is_file() else ""
    test_names = {line.split(" ")[0] for line in test_text.splitlines() if line.endswith(" ... ok")}
    verify_path = ROOT / "experiments/python-game-overlap-reference-study/verify.log"
    verify_text = verify_path.read_text() if verify_path.is_file() else ""
    overlap_tests = {"log_present": test_path.is_file(), "passed_count": test_text.count(" ... ok"), "failure_marker_present": "FAILED" in test_text,
        "bank0_lease_does_not_block_bank1_writer": "test_bank0_leases_do_not_block_bank1_writer_but_bank1_leases_do" in test_names,
        "promotion_overlaps_key0_pending_and_key0_continues": "test_promotion_overlaps_key0_pending_and_key0_continues_before_ack" in test_names,
        "lost_ack_preserves_key0_continuity": "test_lost_promotion_ack_keeps_key0_continuity_and_content_guard" in test_names,
        "serial_policy_fixed_clock_parity": "test_model_serial_fixed_clock_matches_frozen_parent_trace" in test_names,
        "rejected_promotion_keeps_old_bank_and_consumers": "test_rejected_promotion_preserves_existing_bank_and_pending_consumers" in test_names}
    held_key = ("mass-effect-2600-heldout180", "immutable_initial")
    overlap_key = ("mass-effect-2600-heldout180", "overlap_recent16_initial")
    held_control_case, held_overlap_case = cases.get(held_key, {}), cases.get(overlap_key, {})
    held_control, held_overlap = held_control_case.get("result", {}), held_overlap_case.get("result", {})
    prepared_control = sorted(p.get("id") for p in held_control.get("packets", []))
    prepared_overlap = sorted(p.get("id") for p in held_overlap.get("packets", []))
    presented_control = sorted(p.get("id") for p in held_control.get("presented", []))
    presented_overlap = sorted(p.get("id") for p in held_overlap.get("presented", []))
    steady_lo, steady_hi = 500, 5500
    steady_control = [p for p in held_control.get("presented", []) if steady_lo <= p.get("at_ms", -1) < steady_hi]
    steady_overlap = [p for p in held_overlap.get("presented", []) if steady_lo <= p.get("at_ms", -1) < steady_hi]
    manifest_control = held_control_case.get("manifest", {})
    manifest_overlap = held_overlap_case.get("manifest", {})
    native_hashes = manifest_control.get("frame_sha256", [])
    control_commits = {c.get("id"): c for c in held_control.get("commits", [])}
    overlap_commits = {c.get("id"): c for c in held_overlap.get("commits", [])}
    control_body = [p.get("bytes") for p in held_control.get("packets", []) if p.get("admitted") is True]
    overlap_body = [p.get("bytes") for p in held_overlap.get("packets", []) if p.get("admitted") is True]
    control_mean_mse = sum(c.get("active_rgb565_mse", 0) for c in held_control.get("commits", [])) / len(held_control.get("commits", [])) if held_control.get("commits") else None
    overlap_mean_mse = sum(c.get("active_rgb565_mse", 0) for c in held_overlap.get("commits", [])) / len(held_overlap.get("commits", [])) if held_overlap.get("commits") else None
    distinct_source_hashes_steady_control = len({native_hashes[p["id"]] for p in steady_control if p.get("id", -1) < len(native_hashes)})
    distinct_source_hashes_steady_overlap = len({native_hashes[p["id"]] for p in steady_overlap if p.get("id", -1) < len(native_hashes)})
    distinct_decoded_hashes_steady_control = len({control_commits[p["id"]].get("rgb_sha256") for p in steady_control if p.get("id") in control_commits})
    distinct_decoded_hashes_steady_overlap = len({overlap_commits[p["id"]].get("rgb_sha256") for p in steady_overlap if p.get("id") in overlap_commits})
    def mean_int(xs): return sum(xs) / len(xs) if xs else None
    analysis_path = ROOT / "experiments/python-game-overlap-reference-study/analyze.py"
    matched_path = ROOT / "experiments/python-game-overlap-reference-study/matched-delivery.json"
    analysis_hash = hashlib.sha256(analysis_path.read_bytes()).hexdigest() if analysis_path.is_file() else None
    result_path = ROOT / "experiments/python-game-overlap-reference-study/results.json"
    result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest() if result_path.is_file() else None
    matched = json.loads(matched_path.read_text()) if matched_path.is_file() else {}
    analyze_log_path = ROOT / "experiments/python-game-overlap-reference-study/analysis-verify.log"
    analyze_log = analyze_log_path.read_text().strip() if analyze_log_path.is_file() else ""
    heldout_delivery = {
        "control_profile": "immutable_initial", "overlap_profile": "overlap_recent16_initial",
        "prepared_id_sets_equal": prepared_control == prepared_overlap,
        "control_prepared_id_count": len(prepared_control), "overlap_prepared_id_count": len(prepared_overlap),
        "prepared_ids_missing_from_both": sorted((set(range(180)) - set(prepared_control)) & (set(range(180)) - set(prepared_overlap))),
        "prepared_ids_missing_control": sorted(set(range(180)) - set(prepared_control)),
        "prepared_ids_missing_overlap": sorted(set(range(180)) - set(prepared_overlap)),
        "presented_id_sets_equal": presented_control == presented_overlap,
        "control_presented_id_count": len(presented_control), "overlap_presented_id_count": len(presented_overlap),
        "presented_ids_missing_control": sorted(set(range(180)) - set(presented_control)),
        "presented_ids_missing_overlap": sorted(set(range(180)) - set(presented_overlap)),
        "only_drop_id_control": [d.get("id") for d in held_control.get("drops", [])],
        "only_drop_id_overlap": [d.get("id") for d in held_overlap.get("drops", [])],
        "source_frame_hash_manifests_equal": manifest_control.get("frame_sha256") == manifest_overlap.get("frame_sha256"),
        "steady_window_ms": [steady_lo, steady_hi],
        "steady_presented_count_control": len(steady_control), "steady_presented_count_overlap": len(steady_overlap),
        "steady_diagnostic_ids_per_second_control": len(steady_control) / ((steady_hi - steady_lo) / 1000),
        "steady_diagnostic_ids_per_second_overlap": len(steady_overlap) / ((steady_hi - steady_lo) / 1000),
        "steady_unique_native_input_hashes_control": distinct_source_hashes_steady_control,
        "steady_unique_native_input_hashes_overlap": distinct_source_hashes_steady_overlap,
        "steady_unique_decoded_rgb_hashes_control": distinct_decoded_hashes_steady_control,
        "steady_unique_decoded_rgb_hashes_overlap": distinct_decoded_hashes_steady_overlap,
        "mean_complete_ar_body_bytes_control": mean_int(control_body), "mean_complete_ar_body_bytes_overlap": mean_int(overlap_body),
        "complete_body_size_saving_pct": (1 - mean_int(overlap_body) / mean_int(control_body)) * 100 if control_body and overlap_body else None,
        "forward_ipv4_udp_bytes_control": held_control.get("forward_ipv4_udp_bytes"), "forward_ipv4_udp_bytes_overlap": held_overlap.get("forward_ipv4_udp_bytes"),
        "forward_wire_saving_pct": (1 - held_overlap.get("forward_ipv4_udp_bytes", 0) / held_control.get("forward_ipv4_udp_bytes", 1)) * 100 if held_control.get("forward_ipv4_udp_bytes") else None,
        "total_wire_bytes_control": held_control.get("forward_ipv4_udp_bytes", 0) + held_control.get("reverse_ipv4_udp_bytes", 0),
        "total_wire_bytes_overlap": held_overlap.get("forward_ipv4_udp_bytes", 0) + held_overlap.get("reverse_ipv4_udp_bytes", 0),
        "control_active_rgb565_mse_mean": control_mean_mse, "overlap_active_rgb565_mse_mean": overlap_mean_mse,
        "active_rgb565_mse_delta": overlap_mean_mse - control_mean_mse if control_mean_mse is not None and overlap_mean_mse is not None else None,
        "strict_presentations_control_overlap": [held_control.get("presented_strict"), held_overlap.get("presented_strict")],
        "eventual_presentations_control_overlap": [held_control.get("presented_eventual"), held_overlap.get("presented_eventual")],
        "diagnostic_ids_per_second_control_overlap": [held_control.get("diagnostic_ids_per_second"), held_overlap.get("diagnostic_ids_per_second")],
        "max_presented_age_ms_control_overlap": [max((p.get("age_ms", 0) for p in held_control.get("presented", [])), default=None), max((p.get("age_ms", 0) for p in held_overlap.get("presented", [])), default=None)],
        "input_results_hash_matches_matched_analysis": result_hash == matched.get("results_sha256") if result_hash else None,
        "analysis_source_hash_matches_matched_analysis": analysis_hash == matched.get("analysis_sha256") if analysis_hash else None,
        "analyze_check_log_passes": analyze_log.startswith("PASS:"), "analysis_check_log": analyze_log,
        "matched_delivery_artifact_present": bool(matched),
        "cross_study_quality_metric_scope": "Same RGB565-expanded source/decoded metric and identical decoded ID set within this pair; not directly comparable to recent-reference RGB888-source metrics. Not lossless or equal distortion.",
    }
    return {"base_ownership_audit": base, "paired_policy_comparisons": pairs, "policy_rows": policy_rows,
        "pairs_recomputed_match_declared_counts": all(len(p["common_admitted_ids_recomputed"]) == p["declared_common_admitted_count"] and len(p["same_reference_and_promotion_choice_ids_recomputed"]) == p["declared_same_choice_count"] and len(p["common_decoded_ids_recomputed"]) == p["declared_common_decoded_count"] for p in pairs),
        "heldout_initial_immutable_vs_overlap": heldout_delivery,
        "all_same_choice_packet_hashes_exact": all(p["same_choice_packet_hashes_exact_recomputed"] for p in pairs),
        "overlap_tests": overlap_tests, "overlap_verifier_log": {"present": verify_path.is_file(), "text": verify_text.strip() or None},
        "policy_scope": data.get("policy_scope"), "timing_scope": data.get("timing_scope"),
        "transport_scope": data.get("transport_scope"), "quality_scope": data.get("quality_scope"),
        "source_scope": data.get("source_scope"), "memory_scope": data.get("memory_scope"),
        "comparison_scope": data.get("comparison_scope"), "hardware_timing_proven": False}

def audit() -> dict[str, Any]:
    states, loaded = {}, {}
    for key, path in INPUTS.items():
        if key in AWAITING_FINALIZATION:
            states[key] = {"path": str(path), "status": "awaiting_finalization"}
            continue
        if not path.is_file(): states[key] = {"path": str(path), "status": "pending"}; continue
        try: loaded[key] = json.loads(path.read_text()); states[key] = {"path": str(path), "status": "available"}
        except (OSError, json.JSONDecodeError) as e: states[key] = {"path": str(path), "status": "invalid", "error": str(e)}
    studies = {k: None for k in INPUTS}
    if "recent_reference" in loaded:
        studies["recent_reference"] = audit_recent_reference(loaded["recent_reference"])
    if "skip_residual" in loaded:
        studies["skip_residual"] = audit_skip_residual(loaded["skip_residual"])
    if "finite_reference_ownership" in loaded:
        studies["finite_reference_ownership"] = audit_finite_ownership(loaded["finite_reference_ownership"])
    if "overlap_reference" in loaded:
        studies["overlap_reference"] = audit_overlap_reference(loaded["overlap_reference"])
    return {"audit_version": 14, "target": {"canvas": [720, 480], "active_image": [720, 405], "fps": 30},
            "inputs": states, "source_pins_by_input": {k: verify_pins(v) for k, v in loaded.items()},
            "studies": studies,
            "claims_guard": {"missing_results_mean_success": False, "payload_bytes_equal_wire_bytes": False,
                "lost_ack_implies_safe_promotion": False, "oracle_quality_is_live_policy": False,
                "declared_virtual_time_is_host_wall_time": False, "hardware_timing_proven": False}}

if __name__ == "__main__":
    report = audit(); OUT.joinpath("audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
