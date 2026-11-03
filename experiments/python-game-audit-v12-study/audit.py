#!/usr/bin/env python3
"""Small evidence-first audit helpers for rate/motion, refresh, and sparse studies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_pins(pins: dict[str, str]) -> dict:
    rows = []
    for raw, expected in sorted(pins.items()):
        path = Path(raw)
        marker = '/moonbub-30fps-study/'
        if marker in str(path):
            path = ROOT / str(path).split(marker, 1)[1]
        elif not path.is_absolute():
            path = ROOT / path
        actual = sha256(path) if path.is_file() else None
        rows.append({"path": str(path), "expected": expected, "actual": actual,
                     "matches": actual == expected if actual is not None else None})
    return {"rows": rows, "all_match": bool(rows) and all(r["matches"] is True for r in rows),
            "missing": [r["path"] for r in rows if r["actual"] is None],
            "mismatched": [r["path"] for r in rows if r["actual"] is not None and not r["matches"]]}


def packet_accounting(row: dict) -> dict:
    """Report captured complete bytes and component sums without inventing absent fields."""
    packet_bytes = row.get("packet_bytes", row.get("coded_packet_bytes"))
    components = {k: row[k] for k in ("payload_bytes", "header_bytes", "crc_bytes", "skip_bytes", "metadata_bytes")
                  if isinstance(row.get(k), (int, float))}
    component_sum = sum(components.values()) if components else None
    return {"complete_packet_bytes": packet_bytes, "components": components,
            "component_sum_bytes": component_sum,
            "component_sum_matches_packet": component_sum == packet_bytes if component_sum is not None and packet_bytes is not None else None,
            "headers_and_crc_recorded": "header_bytes" in components and "crc_bytes" in components}


def identity_counts(rows: list[dict]) -> dict:
    ids = [(r.get("source_id", r.get("input_id")), r.get("frame_id")) for r in rows]
    complete = [(s, f) for s, f in ids if s is not None and f is not None]
    return {"rows": len(rows), "identified_source_frames": len(set(complete)),
            "duplicate_source_frame_rows": len(complete) - len(set(complete)),
            "unidentified_rows": len(rows) - len(complete),
            "cohort_counts": {str(k): sum(r.get("cohort") == k for r in rows)
                              for k in sorted({r.get("cohort") for r in rows if r.get("cohort") is not None})}}


def candidate_cost(rows: list[dict]) -> dict:
    """Sum explicit encode/search work for winners and losers; preserve missing evidence."""
    count = loser_count = measured = 0
    total_ms = loser_ms = 0.0
    for row in rows:
        for a in row.get("attempts", []):
            count += 1
            parts = [a.get(k) for k in ("encode_ms", "search_ms", "validate_ms")]
            stages = a.get("stages", {})
            explicit = a.get("candidate_total_ms", stages.get("candidate_total_ms"))
            has_cost = isinstance(explicit, (int,float)) or any(isinstance(x, (int,float)) for x in parts)
            cost = float(explicit) if isinstance(explicit, (int,float)) else sum(float(x) for x in parts if isinstance(x, (int,float)))
            if not has_cost:
                continue
            measured += 1
            total_ms += cost
            loser = a.get("selected") is False or a.get("winner") is False or a.get("rejected") is True
            loser |= a.get("fits") is False
            if loser:
                loser_count += 1
                loser_ms += cost
    return {"attempt_count": count, "attempts_with_explicit_cost": measured,
            "explicit_attempt_service_ms": total_ms if measured else None,
            "loser_attempt_count": loser_count,
            "loser_explicit_service_ms": loser_ms if loser_count else (0.0 if measured else None)}


def skip_compatibility(row: dict) -> dict:
    """Check only explicit equality evidence for skipped coefficients/pixels."""
    coeff = row.get("zero_coefficients_equal")
    pixels = row.get("reconstructed_pixels_equal")
    if coeff is None and "source_coefficients" in row and "decoded_coefficients" in row:
        coeff = row["source_coefficients"] == row["decoded_coefficients"]
    if pixels is None and "source_pixels" in row and "reconstructed_pixels" in row:
        pixels = row["source_pixels"] == row["reconstructed_pixels"]
    return {"zero_coefficients_equal": coeff, "reconstructed_pixels_equal": pixels,
            "bit_exact_skip_proven": coeff is True and pixels is True}


def timing_evidence(row: dict) -> dict:
    return {"measured_wall_ms": row.get("wall_ms", row.get("actual_wall_ms")),
            "declared_service_ms": row.get("declared_service_ms", row.get("service_ms")),
            "physical_timing_proven": row.get("physical_timing_proven") is True or row.get("hardware_timing_proven") is True,
            "timing_classes_separate": True}


def audit_sparse(data: dict) -> dict:
    rows = []
    frame_hashes = set()
    source_frame_hashes = set()
    outputs_exact = True
    packet_identity_unchanged = True
    block_totals = {k: 0 for k in ("blocks", "zero", "dc_only", "general_inverse", "bypass_blocks", "baseline_inverse_blocks")}
    resolution_ok = True
    timings = {k: [] for k in ("core_baseline_ms", "core_fast_ms")}
    receive_times = {k: [] for k in ("gm_baseline", "gm_fast", "hg_baseline", "hg_fast")}
    per_source = []
    for case in data.get("cases", []):
        manifest = case.get("manifest", {})
        resolution_ok &= (manifest.get("target_width"), manifest.get("target_height")) == (720, 480)
        case_rows = case.get("rows", [])
        exact_case = 0
        local_blocks = {k: 0 for k in block_totals}
        for row in case_rows:
            rows.append(row)
            if row.get("input_sha256"):
                frame_hashes.add((case.get("source"), row.get("id")))
                source_frame_hashes.add(row["input_sha256"])
            exact = (row.get("baseline_gm_rgb_sha256") == row.get("fast_gm_rgb_sha256")
                and row.get("baseline_hg_rgb_sha256") == row.get("fast_hg_rgb_sha256")
                and row.get("baseline_reconstructed_yuv_sha256") == row.get("fast_reconstructed_yuv_sha256")
                and row.get("all_pixels_and_yuv_exact") is True
                and row.get("selected_rgb565_mismatches") == 0)
            outputs_exact &= exact
            exact_case += int(exact)
            packet_identity_unchanged &= (row.get("gm_packet_bytes") is not None and row.get("hybrid_packet_bytes") is not None
                and row.get("gm_packet_sha256") is not None and row.get("hybrid_packet_sha256") is not None)
            for p in row.get("inverse_blocks", []):
                for key in local_blocks:
                    local_blocks[key] += int(p.get(key, 0))
            for key in timings:
                if isinstance(row.get(key), (int, float)): timings[key].append(float(row[key]))
            for key in receive_times:
                value = row.get("whole_receive_ms", {}).get(key)
                if isinstance(value, (int, float)): receive_times[key].append(float(value))
        per_source.append({"source": case.get("source"), "rows": len(case_rows), "exact_output_rows": exact_case,
                           "block_counts": local_blocks, "target_size": [manifest.get("target_width"),manifest.get("target_height")]})
        for key in block_totals: block_totals[key] += local_blocks[key]
    means = lambda m: {k: (sum(v)/len(v) if v else None) for k,v in m.items()}
    identity = identity_counts([{"source_id":r.get("input_sha256"),"frame_id":r.get("id"),"cohort":r.get("cohort")} for r in rows])
    return {"case_count":len(data.get("cases",[])),"row_count":len(rows),"source_frame_count_declared":data.get("source_frames"),
        "whole_decoder_calls_declared":data.get("whole_decoder_calls"),"core_reconstruction_calls_declared":data.get("core_reconstruction_calls"),
        "unique_source_frame_records":identity["identified_source_frames"],"unique_rgb_content_hashes":len(source_frame_hashes),
        "duplicate_source_frame_rows":identity["duplicate_source_frame_rows"],
        "per_source":per_source,"primary_resolution_720x480_all_cases":resolution_ok,
        "all_baseline_fast_yuv_rgb_and_rgb565_checks_exact":outputs_exact,"exact_output_rows":sum(x["exact_output_rows"] for x in per_source),
        "block_counts":block_totals,"block_count_partition_consistent":block_totals["zero"]+block_totals["dc_only"]+block_totals["general_inverse"]==block_totals["blocks"],
        "bypass_count_matches_zero_plus_dc":block_totals["bypass_blocks"]==block_totals["zero"]+block_totals["dc_only"],
        "packet_sizes_and_hashes_recorded":packet_identity_unchanged,"packet_byte_savings_claimed":False,
        "core_wall_ms_means":means(timings),"whole_receive_wall_ms_means":means(receive_times),
        "physical_timing_proven":False,"scope":data.get("scope"),"timing_scope":data.get("timing_scope"),
        "memory_scope":data.get("memory_scope"),"deployment_scope":data.get("deployment_scope")}


def audit_rate_motion(data: dict) -> dict:
    rows_by_profile = {}
    scene_summary=[]
    all_source_pairs=set()
    content_hashes=set()
    cohorts={}
    accepted=0
    packet_rows=0
    packet_bytes_mismatches=0
    reference_match=0
    packet_control_match=0
    comparison_rows=0
    distortion_diff_rows=0
    for scene in data.get("scenes", []):
        cohort=scene.get("cohort","unknown")
        for profile, rows in scene.get("profiles",{}).items():
            rows_by_profile.setdefault(profile,[]).extend(rows)
            for row in rows:
                cohorts[cohort]=cohorts.get(cohort,0)+int(profile=="gm_zero")
                all_source_pairs.add((scene.get("name"),row.get("source_index"),row.get("frame_id")))
                if row.get("source_rgb_sha256"): content_hashes.add(row["source_rgb_sha256"])
                accepted += int(row.get("accepted") is True) if profile=="actual_rate" else 0
                if profile=="actual_rate" and row.get("packet_bytes") is not None:
                    packet_rows+=1
                    packet_bytes_mismatches+=int(row.get("inner_bytes",0)+row.get("outer_header_crc_bytes",0)!=row.get("packet_bytes"))
        comparisons=scene.get("comparisons",[])
        for comp in comparisons:
            comparison_rows+=1
            reference_match+=int(comp.get("same_canonical_reference") is True)
            packet_control_match+=int(comp.get("candidate_packets_match_controls") is True)
            distortion_diff_rows+=int(comp.get("gm_active_mse") is not None and comp.get("bm_active_mse") is not None and comp["gm_active_mse"]!=comp["bm_active_mse"])
        scene_summary.append({"name":scene.get("name"),"cohort":cohort,"source_ids":len(scene.get("indices",[])),
            "comparison_rows":len(comparisons),"same_reference_rows":sum(c.get("same_canonical_reference") is True for c in comparisons),
            "candidate_packet_control_match_rows":sum(c.get("candidate_packets_match_controls") is True for c in comparisons),
            "summary":scene.get("summary",{})})
    profile_metrics={}
    for profile, rows in rows_by_profile.items():
        attempts=[a for r in rows for a in r.get("attempts",[])]
        costs=candidate_cost(rows)
        profile_metrics[profile]={"decision_rows":len(rows),"accepted":sum(r.get("accepted") is True for r in rows),
            "rejected":sum(r.get("accepted") is False for r in rows),"selected_modes":{},
            "attempt_count":len(attempts),"losing_candidate_count":costs["loser_attempt_count"],
            "all_explicit_candidate_ms":costs["explicit_attempt_service_ms"],
            "losing_candidate_ms":costs["loser_explicit_service_ms"],
            "mean_complete_packet_bytes":(sum(r.get("packet_bytes",0) for r in rows if r.get("packet_bytes") is not None)/max(1,sum(r.get("packet_bytes") is not None for r in rows))),
            "max_complete_packet_bytes":max((r.get("packet_bytes",0) for r in rows if r.get("packet_bytes") is not None),default=None),
            **packet_fit_counts(rows),
            "mean_prepare_wall_ms":(sum(r.get("prepare_ms",0) for r in rows)/max(1,sum(r.get("prepare_ms") is not None for r in rows))),
            "mean_receive_wall_ms":(sum(r.get("receive_ms",0) for r in rows)/max(1,sum(r.get("receive_ms") is not None for r in rows))),
            "mean_full_service_wall_ms":(sum(r.get("full_service_ms",0) for r in rows)/max(1,sum(r.get("full_service_ms") is not None for r in rows)))}
        for r in rows:
            mode=r.get("selected_mode") or "none"
            profile_metrics[profile]["selected_modes"][mode]=profile_metrics[profile]["selected_modes"].get(mode,0)+1
    return {"decision_rows":sum(len(v) for v in rows_by_profile.values()),"source_frame_decisions":len(all_source_pairs),
        "distinct_rgb_content_hashes":len(content_hashes),"source_frame_decisions_by_cohort":cohorts,"scenes":scene_summary,
        "profile_metrics":profile_metrics,"actual_rate_admitted":accepted,
        "comparison_rows":comparison_rows,"same_canonical_reference_rows":reference_match,
        "candidate_packets_match_control_rows":packet_control_match,"gm_bm_active_mse_diff_rows":distortion_diff_rows,
        "actual_rate_packet_rows":packet_rows,"complete_packet_vs_inner_plus_header_crc_mismatches":packet_bytes_mismatches,
        "shadow_candidate_or_future_oracle_claimed":False,"future_frames":data.get("policy",{}).get("future_frames"),
        "quality_oracle_for_selection":data.get("policy",{}).get("quality_oracle_for_selection"),
        "timing_scope":data.get("timing_scope"),"physical_timing_proven":False,
        "strict_eventual_presentation_counts_available":False}


def packet_fit_counts(rows: list[dict]) -> dict:
    """Keep decision rejection distinct from any over-cap candidate attempt."""
    return {"actual_decision_rejections":sum(r.get("accepted") is False for r in rows),
        "decisions_with_cap_failed_candidates":sum(any(a.get("fits") is False for a in r.get("attempts",[])) for r in rows),
        "over_cap_candidate_attempts":sum(a.get("fits") is False for r in rows for a in r.get("attempts",[]))}


def audit_memo(data: dict) -> dict:
    rows=[]; source_frames=set(); content_hashes=set(); cohorts={}; cases=[]; packet_hash_matches=0
    baseline_calls=memo_calls=0; cap_fits=0; cache_hits=0; baseline_prepare=memo_prepare=memo_service=0.0
    for case in data.get("cases",[]):
        manifest=case.get("manifest",{}); case_rows=case.get("rows",[])
        cohort="synthetic" if str(manifest.get("source", "")).startswith("synthetic:") or case.get("source", "").startswith("synthetic") else "real_source"
        cohorts[cohort]=cohorts.get(cohort,0)+len(case_rows)
        unique_hashes=set()
        for row in case_rows:
            rows.append(row); source_frames.add((case.get("source"),row.get("id")))
            h=row.get("input_sha256")
            if h:content_hashes.add(h);unique_hashes.add(h)
            packet_hash_matches+=int(row.get("baseline_packet_sha256") is not None and row.get("baseline_packet_sha256")==row.get("memo_packet_sha256"))
            cap_fits+=int(row.get("cap_fit") is True)
            cache_hits+=int(row.get("memo",{}).get("hit") is True)
            baseline_calls+=int(row.get("baseline_forward_calls",0));memo_calls+=int(row.get("memo_forward_calls",0))
            baseline_prepare+=float(row.get("baseline_prepare_ms",0));memo_prepare+=float(row.get("memo_prepare_ms",0))
            memo_service+=float(row.get("memo",{}).get("service_ms",0))
        cases.append({"source":case.get("source"),"source_cohort":cohort,"rows":len(case_rows),
                      "unique_input_hashes":len(unique_hashes),"key_period":case.get("key_period"),
                      "summary":case.get("summary",{}).get("all",{})})
    return {"case_count":len(cases),"paired_source_ids_declared":data.get("paired_source_ids"),
        "paired_frame_rows":len(rows),"unique_source_frame_pairs":len(source_frames),"unique_input_content_hashes":len(content_hashes),
        "cohort_frame_rows":cohorts,"cases":cases,"baseline_memo_packet_hash_matches":packet_hash_matches,
        "all_bitstreams_unchanged":packet_hash_matches==len(rows),"packet_byte_savings_claimed":False,
        "cap_fit_rows":cap_fits,"cap_fail_rows":len(rows)-cap_fits,
        "baseline_forward_calls":baseline_calls,"memo_forward_calls":memo_calls,
        "forward_call_reduction":baseline_calls-memo_calls,
        "memo_hits":cache_hits,"baseline_prepare_wall_ms_sum":baseline_prepare,
        "memo_prepare_wall_ms_sum":memo_prepare,"memo_service_wall_ms_sum":memo_service,
        "service_is_host_observed_not_hardware":True,"physical_timing_proven":False,
        "memo_scope_examples":sorted({str(r.get("memo",{}).get("scope")) for r in rows if r.get("memo",{}).get("scope")}),
        "scope":data.get("scope"),"timing_scope":data.get("timing_scope"),"memory_scope":data.get("memory_scope"),
        "comparison_scope":data.get("comparison_scope")}


def audit_refresh(data: dict) -> dict:
    rows=[]; captures=strict=eventual=0; unique_frames=set(); unique_hashes={}; cohort_frames={}
    pairing={}; pair_mismatches=0; admitted_packets=cap_failures=0; packet_max=0; nominal_gm_frames={}
    strict_mismatches=0; unresolved=0; by_policy={}; service={"encode_wall_ms":0.0,"encode_service_ms":0.0,"decode_wall_ms":0.0,"decode_service_ms":0.0}
    for case in data.get("cases",[]):
        r=case.get("result",{}); m=case.get("manifest",{}); cfg=r.get("config",{})
        captures += int(r.get("capture_count",0))
        eventual += int(r.get("presented_eventual",0)); strict += int(r.get("presented_strict",0))
        end=(r.get("capture_window_ms") or [None,None])[1]
        derived_strict=sum(p.get("at_ms",float("inf"))<end for p in r.get("presented",[])) if end is not None else None
        strict_mismatches += int(derived_strict is not None and derived_strict != r.get("presented_strict"))
        unresolved += int(has_unresolved_state(r))
        source=case.get("source","unknown")
        cohort="synthetic" if source.startswith("synthetic") else "real_source"
        hlist=m.get("frame_sha256",[]); pts=m.get("selected_pts",[])
        for i,h in enumerate(hlist):
            pt=pts[i] if i<len(pts) else i
            unique_frames.add((source,pt)); unique_hashes.setdefault(source,set()).add(h)
            cohort_frames.setdefault(cohort,set()).add((source,pt))
        if case.get("mode") == "gm_only" and case.get("service_scale")==1.0:
            nominal_gm_frames.setdefault(cohort,set()).update((source,pts[i] if i<len(pts) else i) for i in range(len(hlist)))
        key=(source,case.get("mode"),case.get("service_scale"))
        identity=(case.get("table_source_clip"),r.get("service_tape",{}).get("table_sha256"),tuple(hlist))
        if key in pairing and pairing[key]!=identity: pair_mismatches+=1
        pairing[key]=identity
        packets=r.get("packets",[])
        for p in packets:
            if p.get("admitted"):
                admitted_packets+=1; packet_max=max(packet_max,int(p.get("bytes",0)))
                cap_failures+=int(p.get("bytes",0)>cfg.get("frame_cap",49152))
        summary=next((s for s in data.get("summary",[]) if (s.get("source"),s.get("mode"),s.get("policy"),s.get("scale"))==(source,case.get("mode"),case.get("policy"),case.get("service_scale"))),{})
        aggregate=by_policy.setdefault(f"{source}/{case.get('mode')}/{case.get('policy')}/scale={case.get('service_scale')}",
            {"cases":0,"captures":0,"strict":0,"eventual":0,"prepared":0,"presented_rows":0,
             "actual_encode_wall_ms":0.0,"charged_encode_service_ms":0.0,"actual_decode_wall_ms":0.0,"charged_decode_service_ms":0.0,
             "encode_calls_over_declared":0,"decode_calls_over_declared":0})
        aggregate["cases"]+=1;aggregate["captures"]+=r.get("capture_count",0)
        aggregate["strict"]+=r.get("presented_strict",0);aggregate["eventual"]+=r.get("presented_eventual",0)
        aggregate["prepared"]+=r.get("prepared",0);aggregate["presented_rows"]+=len(r.get("presented",[]))
        for field in ("actual_encode_wall_ms","charged_encode_service_ms","actual_decode_wall_ms","charged_decode_service_ms","encode_calls_observed_above_declared_service","decode_calls_observed_above_declared_service"):
            target={"actual_encode_wall_ms":"actual_encode_wall_ms","charged_encode_service_ms":"charged_encode_service_ms",
                    "actual_decode_wall_ms":"actual_decode_wall_ms","charged_decode_service_ms":"charged_decode_service_ms",
                    "encode_calls_observed_above_declared_service":"encode_calls_over_declared","decode_calls_observed_above_declared_service":"decode_calls_over_declared"}[field]
            aggregate[target]+=summary.get(field,0)
        rows.append({"source":source,"cohort":cohort,"mode":case.get("mode"),"refresh_policy":case.get("policy"),
            "service_scale":case.get("service_scale"),"captures":r.get("capture_count"),"strict_presentations":r.get("presented_strict"),
            "eventual_presentations":r.get("presented_eventual"),"prepared":r.get("prepared"),
            "declared_service_tape":r.get("service_tape"),"strict_derived_from_timestamps":derived_strict,
            "unresolved_work":has_unresolved_state(r)})
    # late-ACK proof is from pinned implementation + regression test, not the main 17 replay cases.
    test_path=ROOT/"experiments/python-game-refresh-study/test_refresh.py"
    model_path=ROOT/"experiments/python-game-refresh-study/model.py"
    log_path=ROOT/"experiments/python-game-refresh-study/tests.log"
    test_text=test_path.read_text() if test_path.is_file() else ""
    model_text=model_path.read_text() if model_path.is_file() else ""
    test_log=log_path.read_text() if log_path.is_file() else ""
    late_ack_case="test_timeout_during_parse_pays_reader_drain_and_rejects_late_ack" in test_text
    timeout_case="test_ack_after_timeout_cannot_install_key_reference" in test_text
    stale_guard="and not r.get('expire_requested')" in model_text
    null_anchor_assert="sender_anchor_after'] is None" in test_text
    late_test_logged=late_ack_case and any("test_timeout_during_parse_pays_reader_drain_and_rejects_late_ack" in line and line.rstrip().endswith("ok") for line in test_log.splitlines())
    timeout_test_logged=timeout_case and any("test_ack_after_timeout_cannot_install_key_reference" in line and line.rstrip().endswith("ok") for line in test_log.splitlines())
    return {"case_count":len(rows),"capture_events_summed_across_runs":captures,"strict_presentations_summed":strict,
        "eventual_presentations_summed":eventual,"presentations_rederived_strict_timestamp_mismatches":strict_mismatches,
        "unique_source_frame_ids_across_clips":len(unique_frames),"unique_content_hashes_by_source":{k:len(v) for k,v in unique_hashes.items()},
        "source_frame_decisions_by_cohort":{k:len(v) for k,v in cohort_frames.items()},
        "unique_source_frames_in_nominal_scale_gm_only":{k:len(v) for k,v in nominal_gm_frames.items()},
        "pairing_identity_group_count":len(pairing),"pairing_identity_mismatches":pair_mismatches,
        "admitted_complete_packets":admitted_packets,"max_complete_packet_bytes":packet_max,"frame_cap_failures":cap_failures,
        "runs_with_unresolved_work_at_end":unresolved,"per_case":rows,"per_policy_run":by_policy,
        "timing_evidence":{"actual_wall_sums_and_declared_tape_summaries":True,"physical_timing_proven":False,
            "service_tape_provenance":sorted({str(c.get("result",{}).get("service_tape",{}).get("provenance")) for c in data.get("cases",[])}),
            "calls_observed_above_declared_encode_or_decode_service":sum(v["encode_calls_over_declared"]+v["decode_calls_over_declared"] for v in by_policy.values()),
            "actual_encode_wall_ms_sum":sum(v["actual_encode_wall_ms"] for v in by_policy.values()),
            "charged_encode_service_ms_sum":sum(v["charged_encode_service_ms"] for v in by_policy.values()),
            "actual_decode_wall_ms_sum":sum(v["actual_decode_wall_ms"] for v in by_policy.values()),
            "charged_decode_service_ms_sum":sum(v["charged_decode_service_ms"] for v in by_policy.values())},
        "late_ack_state_evidence":{"expiry_guard_in_pinned_model":stale_guard,"late_ack_after_timeout_test_present":timeout_case,
            "late_ack_during_parse_reader_drain_test_present":late_ack_case,"late_ack_tests_recorded_passing":timeout_test_logged and late_test_logged,
            "asserts_sender_anchor_not_installed":null_anchor_assert},
        "scope":data.get("source_scope"),"omitted":data.get("omitted"),"physical_30fps_proven":False}


def has_unresolved_state(result: dict) -> bool:
    slots=result.get("unresolved_sender_slots") or []
    if any(x is not None for x in slots): return True
    for field in ("unresolved_ingress_frames","unresolved_credits","pending_ids"):
        values=result.get(field)
        if values and any(x is not None for x in values): return True
    if result.get("waiting_at_end") is not None: return True
    return any(v not in (None,0,False) for v in (result.get("unresolved_cpu") or {}).values())


def audit_pending() -> dict:
    inputs = {
        "rate_motion": ROOT / "experiments/python-game-rate-motion-study/results.json",
        "refresh": ROOT / "experiments/python-game-refresh-study/results.json",
        "sparse": ROOT / "experiments/python-game-sparse-study/results.json",
        "memo": ROOT / "experiments/python-game-memo-study/results.json",
    }
    available = {k: json.loads(p.read_text()) for k,p in inputs.items() if p.is_file()}
    source_pins = {}
    manifests = {}
    for data in available.values():
        source_pins.update(data.get("source_sha256", {}))
        for case in data.get("cases", []) + data.get("scenes", []):
            m=case.get("manifest", {})
            if m.get("source") and m.get("source_sha256"):
                manifests[m["source"]]=m["source_sha256"]
    pins_before, media_before = verify_pins(source_pins), verify_pins(manifests)
    pins_after, media_after = verify_pins(source_pins), verify_pins(manifests)
    return {"audit_date": "2026-11-03", "inputs": {k: {"path": str(p), "status": "available" if p.is_file() else "pending"}
                                                       for k,p in inputs.items()},
            "source_pins_before":pins_before,"source_pins_after":pins_after,
            "source_pins_stable_and_matching":pins_before==pins_after and pins_before["all_match"],
            "media_hashes_before":media_before,"media_hashes_after":media_after,
            "media_hashes_stable_and_matching":media_before==media_after and media_before["all_match"],
            "sparse_audit":audit_sparse(available["sparse"]) if "sparse" in available else None,
            "rate_motion_audit":audit_rate_motion(available["rate_motion"]) if "rate_motion" in available else None,
            "refresh_audit":audit_refresh(available["refresh"]) if "refresh" in available else None,
            "memo_audit":audit_memo(available["memo"]) if "memo" in available else None,
            "evidence_gaps": [f"results pending: {p}" for k,p in inputs.items() if k not in available],
            "claims_guard": {"offline_data_proves_physical_timing": False,
                             "measured_wall_equals_declared_service": False,
                             "result_rows_equal_unique_input_frames": False,
                             "sparse_decoder_change_saves_packet_bytes": False}}


if __name__ == "__main__":
    OUT.joinpath("audit.json").write_text(json.dumps(audit_pending(), indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit_pending(), indent=2, sort_keys=True))
