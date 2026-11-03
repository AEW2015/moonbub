#!/usr/bin/env python3
"""Evidence-first standard-library audit for v11 hybrid codec/transport studies."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CAP_BYTES = 49_152


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def pin_audit(pins: dict[str, str]) -> dict:
    rows = []
    for raw, expected in sorted(pins.items()):
        path = Path(raw)
        if not path.is_absolute(): path = ROOT / path
        actual = sha256(path) if path.is_file() else None
        rows.append({"path": str(path), "expected": expected, "actual": actual,
                     "matches": actual == expected if actual is not None else None})
    return {"rows": rows, "missing": [r["path"] for r in rows if r["actual"] is None],
            "mismatched": [r["path"] for r in rows if r["actual"] is not None and not r["matches"]],
            "all_match": bool(rows) and all(r["matches"] is True for r in rows)}


def first(row: dict, *keys: str) -> Any:
    for key in keys:
        if row.get(key) is not None: return row[key]
    return None


def records(data: dict) -> list[dict]:
    result = []
    for key in ("records", "rows", "frames", "decisions", "transactions", "packets", "events"):
        value = data.get(key)
        if isinstance(value, list): result.extend(x for x in value if isinstance(x, dict))
    for group in data.get("cases", []) + data.get("scenes", []):
        if not isinstance(group, dict): continue
        for key in ("records", "rows", "frames", "decisions", "transactions", "packets", "events"):
            value = group.get(key)
            if isinstance(value, list): result.extend(x for x in value if isinstance(x, dict))
    return result


def provenance(row: dict, parent: dict | None = None) -> str:
    parent = parent or {}
    synth = first(row, "synthetic", "is_synthetic")
    if synth is None: synth = first(parent, "synthetic", "is_synthetic")
    if synth is True: return "synthetic"
    if synth is False: return "real_source"
    return "unknown"


def audit_row(row: dict, parent: dict | None = None, cap: int = CAP_BYTES) -> dict:
    parent = parent or {}
    packet = first(row, "whole_packet_bytes", "serialized_packet_bytes", "packet_bytes", "outer_packet_bytes", "bytes")
    attempt_rows = row.get("attempts", row.get("candidates", []))
    attempt_rows = attempt_rows if isinstance(attempt_rows, list) else []
    cost_fields = ("charged_ms", "service_ms", "encode_ms", "validate_ms", "search_ms", "assembly_ms", "loser_cost_ms")
    charged_sum = 0.0
    charged_count = 0
    loser_cost = 0.0
    loser_count = 0
    for attempt in attempt_rows:
        if not isinstance(attempt, dict): continue
        explicit = first(attempt, "charged_ms", "service_ms", "total_cost_ms")
        if explicit is None:
            parts = [attempt.get(k) for k in ("encode_ms", "validate_ms", "search_ms", "assembly_ms")]
            parts = [float(x) for x in parts if isinstance(x, (int, float))]
            explicit = sum(parts) if parts else None
        if explicit is not None:
            charged_sum += float(explicit); charged_count += 1
            selected = first(attempt, "selected", "winner", "chosen")
            rejected = attempt.get("rejected") is True or attempt.get("lost") is True or selected is False
            if rejected: loser_count += 1; loser_cost += float(explicit)
    outer_epoch = first(row, "outer_epoch", "feedback_epoch", "transport_epoch", "epoch")
    outer_frame = first(row, "outer_frame_id", "outer_frame", "feedback_frame_id", "frame_id", "capture_id")
    inner_epoch = first(row, "inner_gm_epoch", "gm_epoch", "inner_epoch", "codec_epoch")
    inner_frame = first(row, "inner_gm_frame_id", "gm_frame_id", "inner_frame_id", "codec_frame_id")
    binding_fields = (outer_epoch, outer_frame, inner_epoch, inner_frame)
    binding_available = all(v is not None for v in binding_fields)
    atomic = first(row, "atomic_reject", "rejected_atomically", "state_unchanged_on_reject")
    status = str(first(row, "status", "decision", "outcome") or "").lower()
    rejected = row.get("rejected") is True or row.get("accepted") is False or status in {"reject", "rejected", "nack", "invalid"}
    wall = first(row, "wall_ms", "actual_wall_ms", "elapsed_ms")
    virtual = first(row, "virtual_service_ms", "charged_service_ms", "service_ms")
    return {"source_id": first(row, "source_id", "source_frame_id", "capture_id", "id"),
            "frame_id": first(row, "frame_id", "capture_id", "id"),
            "input_class": provenance(row, parent), "mode": first(row, "mode", "format", "codec", "profile"),
            "packet_bytes": packet, "cap_bytes": first(row, "frame_cap_bytes", "packet_cap_bytes") or cap,
            "cap_ok": packet <= cap if packet is not None else None,
            "packet_size_components": {k: row.get(k) for k in ("base_bytes", "vector_bytes", "roi_bytes", "skip_metadata_bytes", "header_bytes", "crc_bytes", "feedback_bytes") if row.get(k) is not None},
            "format_vector_roi_skip_overhead": {k: row.get(k) for k in ("vector_bytes", "roi_bytes", "skip_bytes", "skip_metadata_bytes") if row.get(k) is not None},
            "outer_packet_identity": first(row, "outer_packet_sha256", "full_packet_sha256", "packet_sha256"),
            "inner_gm_identity": first(row, "gm_packet_sha256", "inner_packet_sha256", "base_packet_sha256"),
            "outer_epoch": outer_epoch, "outer_frame": outer_frame,
            "inner_gm_epoch": inner_epoch, "inner_gm_frame": inner_frame,
            "outer_inner_binding_checked": binding_available,
            "outer_inner_binding_matches": (outer_epoch == inner_epoch and outer_frame == inner_frame) if binding_available else None,
            "outer_feedback_packet_bytes": first(row, "outer_feedback_packet_bytes", "feedback_packet_bytes", "serialized_feedback_bytes"),
            "atomic_reject_evidence": atomic,
            "rejected": rejected,
            "attempt_count": len(attempt_rows), "attempt_cost_rows": charged_count,
            "attempt_charged_service_ms": charged_sum if charged_count else None,
            "loser_attempt_count": loser_count, "loser_attempt_charged_ms": loser_cost if loser_count else None,
            "actual_wall_ms": wall, "virtual_service_ms": virtual,
            "timing_kind": first(row, "timing_kind", "timing_backend", "backend"),
            "hardware_timing_proven": row.get("hardware_timing_proven") is True}


def audit_study(data: dict, name: str) -> dict:
    cap = first(data, "frame_cap_bytes", "packet_cap_bytes", "cap_bytes") or CAP_BYTES
    rows = []
    for group in data.get("scenes", []) + data.get("cases", []):
        if not isinstance(group, dict): continue
        items = group.get("records", group.get("rows", group.get("frames", group.get("decisions", []))))
        if isinstance(items, list): rows.extend(audit_row(r, group, cap) for r in items if isinstance(r, dict))
    if not rows: rows = [audit_row(r, {}, cap) for r in records(data)]
    source_ids = [(r["source_id"], r["frame_id"]) for r in rows if r["source_id"] is not None and r["frame_id"] is not None]
    unique_pairs = set(source_ids)
    modes = {}
    for row in rows:
        mode = row["mode"] or "unknown"
        m = modes.setdefault(str(mode), {"rows": 0, "over_cap": 0, "rejected": 0,
                                         "charged_attempts": 0, "loser_attempts": 0,
                                         "loser_service_ms": 0.0})
        m["rows"] += 1
        m["over_cap"] += int(row["cap_ok"] is False)
        m["rejected"] += int(row["rejected"])
        m["charged_attempts"] += row["attempt_cost_rows"]
        m["loser_attempts"] += row["loser_attempt_count"]
        m["loser_service_ms"] += float(row["loser_attempt_charged_ms"] or 0)
    binding = [r for r in rows if r["outer_inner_binding_checked"]]
    rejects = [r for r in rows if r["rejected"]]
    deployment = first(data, "deployment_scope", "deploy_scope", "installation_scope", "format_scope")
    timing = first(data, "timing_scope", "service_scope", "scope")
    return {"study": name, "row_count": len(rows), "rows": rows,
            "source_frame_pairs": len(unique_pairs), "duplicate_source_frame_rows": len(source_ids) - len(unique_pairs),
            "distinct_source_ids": len({x[0] for x in source_ids}),
            "packet_cap_bytes": cap,
            "observed_packet_rows": sum(r["packet_bytes"] is not None for r in rows),
            "packet_cap_failures": sum(r["cap_ok"] is False for r in rows),
            "mode_counts": modes,
            "outer_inner_binding_rows_checked": len(binding),
            "outer_inner_binding_rows_match": sum(r["outer_inner_binding_matches"] is True for r in binding),
            "atomic_reject_rows": sum(r["atomic_reject_evidence"] is True for r in rejects),
            "rejected_rows": len(rejects),
            "rejected_rows_with_atomicity_evidence": sum(r["atomic_reject_evidence"] is not None for r in rejects),
            "wall_and_virtual_timing_rows": sum(r["actual_wall_ms"] is not None and r["virtual_service_ms"] is not None for r in rows),
            "hardware_timing_rows": sum(r["hardware_timing_proven"] for r in rows),
            "deployment_scope": deployment, "timing_scope": timing,
            "formats_installed_proven": data.get("installed_support") is True or data.get("hardware_integration") is True}


def _iter_hybrid(data: dict):
    for source in data.get("records", []):
        for policy, result in source.get("policies", {}).items():
            yield source, policy, result


def audit_hybrid(data: dict) -> dict:
    rows = list(_iter_hybrid(data))
    policies = {}
    for _, policy, r in rows:
        m = policies.setdefault(policy, {"decisions": 0, "accepted": 0, "formats": {},
            "over_cap": 0, "selected_pixels": 0, "requested_pixels": 0,
            "zero_selected_rgb565_mismatches": 0, "zero_unselected_base_rgb565_mismatches": 0,
            "attempts": 0, "rejected_attempts": 0, "attempt_candidate_service_ms": 0.0,
            "attempt_encode_validate_ms": 0.0, "rejected_attempt_encode_validate_ms": 0.0,
            "charged_prepare_ms": 0.0, "max_packet_bytes": 0})
        m["decisions"] += 1
        m["accepted"] += int(r.get("accepted") is True)
        fmt = r.get("format") or "unknown"
        m["formats"][fmt] = m["formats"].get(fmt, 0) + 1
        packet = r.get("packet_bytes")
        if packet is not None:
            m["over_cap"] += int(packet > CAP_BYTES)
            m["max_packet_bytes"] = max(m["max_packet_bytes"], packet)
        m["selected_pixels"] += int(r.get("selected_pixels", 0))
        m["requested_pixels"] += int(r.get("requested_pixels", 0))
        m["zero_selected_rgb565_mismatches"] += int(r.get("selected_rgb565_mismatches") == 0)
        m["zero_unselected_base_rgb565_mismatches"] += int(r.get("unselected_base_rgb565_mismatches") == 0)
        m["charged_prepare_ms"] += float(r.get("charged_prepare_ms", 0))
        for a in r.get("attempts", []):
            m["attempts"] += 1
            rejected = a.get("selected_in_output") is False or a.get("fits") is False
            m["rejected_attempts"] += int(rejected)
            attempt_cost = float(a.get("encode_ms", 0)) + float(a.get("validate_ms", 0))
            m["attempt_encode_validate_ms"] += attempt_cost
            if rejected: m["rejected_attempt_encode_validate_ms"] += attempt_cost
            detail = a.get("candidate_details", {})
            m["attempt_candidate_service_ms"] += float(detail.get("all_candidate_service_ms", 0))
    cohorts = {}
    base_rejected_decisions = 0
    base_rejected_sources = set()
    for s in data.get("records", []):
        cohort = s.get("cohort", "unknown")
        cohorts[cohort] = cohorts.get(cohort, 0) + 1
        for policy, result in s.get("policies", {}).items():
            if result.get("reason") == "base_over_cap":
                base_rejected_decisions += 1
                base_rejected_sources.add((s.get("source_rgb_sha256"),s.get("frame_id")))
    for m in policies.values():
        m["selected_to_requested_area_fraction"] = (m["selected_pixels"] / m["requested_pixels"] if m["requested_pixels"] else None)
    return {"source_records": len(data.get("records", [])), "policy_evaluations": len(rows),
        "distinct_source_frames": len({(s.get("source_rgb_sha256"), s.get("frame_id")) for s,_,_ in rows}),
        "cohorts": cohorts, "source_hashes_match": all(s.get("source_rgb_sha256") for s,_,_ in rows),
        "base_overcap_rejected_sources": len(base_rejected_sources),
        "base_overcap_rejected_policy_decisions": base_rejected_decisions,
        "policy_metrics": policies,
        "frame_identity_consistent_across_policies": all(len({r.get("base_packet_sha256") for r in s.get("policies", {}).values()}) == 1 for s in data.get("records", [])),
        "timing_is_offline_service_model": "offline" in data.get("timing_scope", "").lower() or "model" in data.get("timing_scope", "").lower(),
        "not_hardware_timing": True}


def audit_block(data: dict) -> dict:
    scenes = []
    total = 0
    mode_summary = {}
    frame_consistency = True
    for scene in data.get("scenes", []):
        rows = scene.get("records", [])
        total += len(rows)
        by_profile = {}
        ids_by_profile = {}
        for r in rows:
            prof = r.get("profile", "unknown")
            by_profile.setdefault(prof, []).append(r)
            ids_by_profile.setdefault(prof, {})[r.get("id")] = r.get("input_sha256")
        frame_consistency &= len({tuple(sorted(m.items())) for m in ids_by_profile.values()}) <= 1
        prof_out = {}
        for prof, vals in by_profile.items():
            prof_out[prof] = {"decodes": len(vals), "unique_ids": len({r.get("id") for r in vals}),
                "bytes_mean": sum(r.get("bytes", 0) for r in vals)/max(1,len(vals)),
                "cap_fits": sum(r.get("cap_fit") is True for r in vals),
                "active_psnr_mean": sum(r.get("metrics",{}).get("active",{}).get("psnr",0) for r in vals)/max(1,len(vals)),
                "roi_psnr_mean": sum(r.get("metrics",{}).get("roi",{}).get("psnr",0) for r in vals)/max(1,len(vals)),
                "vector_bytes_mean": sum(r.get("vector_bytes",0) for r in vals)/max(1,len(vals))}
            agg = mode_summary.setdefault(prof, {"decodes":0,"bytes_sum":0,"active_psnr_sum":0,"roi_psnr_sum":0,"cap_fits":0,"vector_bytes_sum":0})
            agg["decodes"] += len(vals)
            agg["bytes_sum"] += sum(r.get("bytes",0) for r in vals)
            agg["active_psnr_sum"] += sum(r.get("metrics",{}).get("active",{}).get("psnr",0) for r in vals)
            agg["roi_psnr_sum"] += sum(r.get("metrics",{}).get("roi",{}).get("psnr",0) for r in vals)
            agg["cap_fits"] += sum(r.get("cap_fit") is True for r in vals)
            agg["vector_bytes_sum"] += sum(r.get("vector_bytes",0) for r in vals)
        deltas = {}
        if "gm_zero" in prof_out:
            base=prof_out["gm_zero"]
            for prof, m in prof_out.items():
                deltas[prof]={"mean_bytes_delta_vs_gm_zero":m["bytes_mean"]-base["bytes_mean"],
                    "mean_active_psnr_delta_vs_gm_zero":m["active_psnr_mean"]-base["active_psnr_mean"],
                    "mean_roi_psnr_delta_vs_gm_zero":m["roi_psnr_mean"]-base["roi_psnr_mean"]}
        scenes.append({"name":scene.get("name"),"inputs_per_profile":len(rows)//max(1,len(by_profile)),"profile_metrics":prof_out,"deltas_vs_gm_zero":deltas})
    for k,v in mode_summary.items():
        n=max(1,v.pop("decodes")); v["decodes"]=n
    return {"actual_decode_records": total, "scene_count": len(scenes), "scenes": scenes,
        "profile_pooled_metrics_sums": mode_summary, "frame_id_input_hashes_match_across_profiles": frame_consistency,
        "benchmark_replay_includes_immediate_in_process_ack": True,
        "hardware_or_network_timing_proven": False,
        "motion_codec_general_win_claim_supported": False}


def audit_hybrid_link(data: dict) -> dict:
    cases=[]; input_total=presented=0; strict=eventual=0; packet_sizes=[]; fwd=[]; feedback=[]
    modes={}; actual_decoded_formats={}; prepared_formats={}; service_stages={}; cpu_service_ms=0.0
    peak_slots=peak_ingress=peak_credits=0; drain_runs=0; unresolved_runs=0
    for c in data.get("cases", []):
        r=c.get("result",{}); cfg=r.get("config",{}); metrics=r.get("metrics",{})
        input_total += int(r.get("capture_count",0)); presented += int(metrics.get("presented_count",0))
        strict += int(r.get("presented_strict",0)); eventual += int(r.get("presented_eventual",0))
        pkts=r.get("packets",[]); packet_sizes.extend(p.get("bytes",0) for p in pkts if isinstance(p.get("bytes"),int))
        for commit in r.get("commits",[]):
            fmt=commit.get("format", "unknown"); actual_decoded_formats[fmt]=actual_decoded_formats.get(fmt,0)+1
        for pkt in pkts:
            fmt=pkt.get("hybrid",{}).get("format",pkt.get("selected","GM01")); prepared_formats[fmt]=prepared_formats.get(fmt,0)+1
        fwd.append(int(r.get("forward_ipv4_udp_bytes",0))); feedback.append(int(r.get("feedback_ipv4_udp_bytes",0)))
        for service in r.get("cpu_services",[]):
            stage=service.get("stage","unknown"); service_stages[stage]=service_stages.get(stage,0)+1
            cpu_service_ms += float(service.get("service_ms",0))
        peak_slots=max(peak_slots,int(r.get("peak_sender_slots",0)))
        peak_ingress=max(peak_ingress,int(r.get("peak_ingress_slots",0)))
        peak_credits=max(peak_credits,int(r.get("peak_credits",0)))
        drain_runs += int(r.get("metrics",{}).get("drain_count",0)>0)
        unresolved_runs += int(has_unresolved_work(r))
        mode=str(c.get("mode", "unknown")); agg=modes.setdefault(mode,{"cases":0,"captures":0,"presented":0,"strict":0,"eventual":0,"drops":0,"packet_events":0,"over_cap_packet_events":0})
        agg["cases"]+=1; agg["captures"]+=r.get("capture_count",0); agg["presented"]+=metrics.get("presented_count",0)
        agg["strict"]+=r.get("presented_strict",0); agg["eventual"]+=r.get("presented_eventual",0); agg["drops"]+=len(r.get("drops",[])); agg["packet_events"]+=len(pkts)
        agg["over_cap_packet_events"]+=sum(p.get("bytes",0)>cfg.get("frame_cap",CAP_BYTES) for p in pkts)
        cases.append({"source":c.get("source"),"kind":c.get("kind"),"coded_size":[c.get("coded_width"),c.get("coded_height")],"mode":mode,"controller_policy":cfg.get("policy"),
            "captures":r.get("capture_count"),"presented":metrics.get("presented_count"),"strict_presented":r.get("presented_strict"),
            "eventual_presented":r.get("presented_eventual"),"steady_fps_virtual":metrics.get("steady_fps"),"packet_events":len(pkts),
            "packet_max_bytes":max((p.get("bytes",0) for p in pkts),default=0),"forward_ipv4_udp_bytes":r.get("forward_ipv4_udp_bytes"),
            "feedback_ipv4_udp_bytes":r.get("feedback_ipv4_udp_bytes"),"feedback_protocol_bytes":r.get("feedback_protocol_bytes"),
            "python_wall_seconds":r.get("python_wall_seconds"),"decoder_service":cfg.get("decoder_service"),"fps_assumption":cfg.get("fps")})
    # Capture/presentation metrics are aggregated independently; a presentation can be strict or eventual.
    fb = data.get("functional_outer_feedback", {})
    binding_proven = (fb.get("feedback_binds_outer") is True and fb.get("inner_only_tag_cannot_ack") is True
        and fb.get("outer_epoch") == fb.get("inner_epoch") and fb.get("outer_frame_id") == fb.get("inner_frame_id"))
    return {"case_count":len(cases),"capture_decisions_sum_across_cases":input_total,"presented_sum_across_case_runs":presented,
        "strict_presented_sum_across_case_runs":strict,"eventual_presented_sum_across_case_runs":eventual,
        "metrics_are_summed_over_policy_runs_not_unique_frames":True,"per_mode":modes,"cases":cases,
        "packet_event_count":len(packet_sizes),"packet_event_max_bytes":max(packet_sizes,default=0),
        "packet_event_cap_failures":sum(x>CAP_BYTES for x in packet_sizes),"forward_ipv4_udp_bytes_sum":sum(fwd),
        "feedback_ipv4_udp_bytes_sum":sum(feedback),"functional_outer_feedback":fb,
        "outer_inner_feedback_binding_proven":binding_proven,"decoded_format_counts":actual_decoded_formats,
        "prepared_format_counts":prepared_formats,
        "cpu_service_event_count":sum(service_stages.values()),"cpu_service_ms_sum":cpu_service_ms,
        "cpu_service_stage_counts":service_stages,"peak_sender_slots_across_runs":peak_slots,
        "peak_ingress_slots_across_runs":peak_ingress,"peak_credits_across_runs":peak_credits,
        "runs_with_drain_presentations":drain_runs,"runs_with_unresolved_work_at_end":unresolved_runs,
        "hardware_30fps_proven":False,"timing_scope":data.get("timing_scope"),"format_scope":data.get("format_scope"),
        "new_custom_formats_are_standard_conformant":False}


def has_unresolved_work(result: dict) -> bool:
    """Interpret optional slot entries as occupancy; [None, None] means drained."""
    slots = result.get("unresolved_sender_slots") or []
    if any(slot is not None for slot in slots):
        return True
    for field in ("unresolved_ingress_frames", "unresolved_credits", "pending_ids"):
        values = result.get(field)
        if values and any(value is not None for value in values):
            return True
    if result.get("waiting_at_end") is not None:
        return True
    cpu = result.get("unresolved_cpu") or {}
    if any(value not in (None, 0, False) for value in cpu.values()):
        return True
    return False


def audit_architecture(data: dict) -> dict:
    resource = data.get("resource_inventory", {})
    return {"kind":data.get("kind"),"resource_inventory_is_external_reference_not_fit":True,
        "device":resource.get("device"),"resource_inventory":resource,
        "modeled_sweeps":{k:len(v) if isinstance(v,list) else (1 if isinstance(v,dict) else 0)
            for k,v in data.items() if k.endswith("sweep") or k in {"intra_only","fused_color_output","compound_two_source","three_full_frame_filter_passes","alternate_800x480_display"}},
        "decoder_implementation_or_timing_measured":False,
        "traffic_is_parameter_bound":True}


def audit_bundle() -> dict:
    expected = {"hybrid": ROOT / "experiments/python-game-hybrid-study/results.json",
                "block": ROOT / "experiments/python-game-block-study/results.json",
                "hybrid_link": ROOT / "experiments/python-game-hybrid-link-study/results.json",
                "architecture": ROOT / "experiments/python-game-decoder-architecture-study/results.json"}
    data = {k: json.loads(p.read_text()) for k, p in expected.items() if p.is_file()}
    pins: dict[str, str] = {}
    manifests = {}
    for value in data.values():
        pins.update(value.get("source_sha256", value.get("source_pins", {})))
        groups = value.get("scenes", []) + value.get("cases", []) + value.get("records", [])
        for group in groups:
            m = group.get("manifest", {}) if isinstance(group, dict) else {}
            if m.get("source") and m.get("source_sha256"): manifests[m["source"]] = m["source_sha256"]
    arch_sources = ROOT / "experiments/python-game-decoder-architecture-study/sources.json"
    if arch_sources.is_file():
        for item in json.loads(arch_sources.read_text()).get("local_inputs", []):
            pins[item["path"]] = item["sha256"]
    before, media_before = pin_audit(pins), pin_audit(manifests)
    result = {"inputs_missing": [str(p) for k, p in expected.items() if k not in data],
              "source_pins_before": before, "media_hashes_before": media_before,
              "study_row_summaries": {name: {k:v for k,v in audit_study(value, name).items() if k != "rows"} for name, value in data.items()},
              "independent_rederivations": {name: fn(data[name]) for name, fn in (("hybrid",audit_hybrid),("block",audit_block),("hybrid_link",audit_hybrid_link),("architecture",audit_architecture)) if name in data}}
    refresh_path = ROOT / "experiments/python-game-hybrid-link-study/refresh-results.json"
    if refresh_path.is_file():
        result["initial_key_refresh_probe"] = audit_hybrid_link(json.loads(refresh_path.read_text()))
    else:
        result["initial_key_refresh_probe"] = {"status":"pending","path":str(refresh_path)}
    after, media_after = pin_audit(pins), pin_audit(manifests)
    result["source_pins_after"], result["media_hashes_after"] = after, media_after
    result["source_pins_match_before_and_after"] = before == after and before["all_match"]
    result["media_hashes_match_before_and_after"] = media_before == media_after and media_before["all_match"]
    result["evidence_gaps"] = ["result input missing: " + p for p in result["inputs_missing"]]
    if not pins: result["evidence_gaps"].append("declared source pins unavailable")
    if not manifests: result["evidence_gaps"].append("source media hashes unavailable")
    result["claims_guard"] = {"source_frame_count_is_not_summed_across_formats": True,
                              "full_packet_cap_is_not_inner_payload_cap": True,
                              "modeled_timing_proves_hardware_speed": False,
                              "new_formats_are_installed": False}
    result["remaining_gaps"] = ["No target hardware timing or installed-format support is implied by offline experiments.",
                                "Full live transport, display scanout, and 30 fps presentation require separate evidence."]
    return result


if __name__ == "__main__":
    output = audit_bundle()
    output["audit_date"] = "2026-11-03"
    (OUT / "audit.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
