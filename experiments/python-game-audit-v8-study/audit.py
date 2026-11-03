#!/usr/bin/env python3
"""Independent, read-only audit for the v8 Python Game Bub experiments."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PACKET_CAP = 49_152


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin_audit(pins: dict[str, str], base: Path = ROOT) -> dict:
    checked, missing, mismatched = [], [], []
    for raw, expected in pins.items():
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        if not path.is_file():
            missing.append(str(path))
            continue
        actual = sha256(path)
        checked.append(str(path))
        if actual != expected:
            mismatched.append({"path": str(path), "expected": expected, "actual": actual})
    return {"checked": checked, "missing": missing, "mismatched": mismatched,
            "all_available_pins_match": not mismatched,
            "all_declared_pins_available_and_match": not missing and not mismatched}


def _num(obj: dict, *keys: str) -> float | None:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _capture_id(record: dict) -> Any:
    for key in ("capture_id", "frame_id", "source_id", "id"):
        if key in record:
            return record[key]
    return None


def audit_record(record: dict) -> dict:
    attempts = record.get("attempts")
    if not isinstance(attempts, list):
        attempts = record.get("candidates") if isinstance(record.get("candidates"), list) else None
    attempt_count = len(attempts) if attempts is not None else None

    # Keep analysis-level calls distinct from the three Y/U/V plane transforms.
    analysis_calls = _num(record, "dct_analysis_calls", "analysis_transform_calls")
    plane_calls = _num(record, "plane_dct_calls", "dct_plane_transforms")
    if analysis_calls is None and isinstance(record.get("transform"), dict):
        analysis_calls = _num(record["transform"], "analysis_calls", "dct_analysis_calls")
        plane_calls = plane_calls if plane_calls is not None else _num(record["transform"], "plane_calls", "plane_dct_transforms")

    charged_attempt_ms = 0.0
    charged_fields_found = False
    if attempts is not None:
        for attempt in attempts:
            if not isinstance(attempt, dict):
                continue
            explicit = _num(attempt, "charged_ms", "total_charged_ms", "service_ms")
            if explicit is not None:
                charged_attempt_ms += explicit
                charged_fields_found = True
            else:
                parts = ["transform_ms", "entropy_ms", "assembly_ms", "selection_ms",
                         "candidate_ms", "encode_ms", "attempt_ms"]
                values = [_num(attempt, field) for field in parts]
                values = [x for x in values if x is not None]
                if values:
                    charged_attempt_ms += sum(values)
                    charged_fields_found = True
    key_commit_ms = _num(record, "key_commit_ms", "keycommit_ms", "commit_ms")
    total = charged_attempt_ms + (key_commit_ms or 0.0) if charged_fields_found or key_commit_ms is not None else None

    # Sizes must describe the complete packet before transport framing. Wire bytes
    # are reported alongside them and never substituted for packet-cap evidence.
    packet_bytes = _num(record, "whole_packet_bytes", "packet_bytes", "actual_packet_bytes", "encoded_packet_bytes")
    wire_bytes = _num(record, "wire_bytes", "transport_bytes", "framed_wire_bytes")
    map_stats = record.get("map_stats", record.get("quality_map_stats"))
    floor = record.get("roi_floor", record.get("priority_floor"))
    metadata = record.get("profile_metadata", record.get("metadata"))
    floor_proven = bool(isinstance(map_stats, dict) and floor is not None and
                        isinstance(metadata, dict) and
                        ("profile" in metadata or "profile_id" in metadata or "profile_version" in metadata) and
                        _num(map_stats, "scale8", "q8", "floor_regions") is not None)
    return {
        "capture_id": _capture_id(record), "attempt_count": attempt_count,
        "attempt_limit_ok": attempt_count is not None and attempt_count <= 2,
        "dct_analysis_calls": analysis_calls, "plane_dct_calls": plane_calls,
        "one_analysis_call_ok": analysis_calls == 1 if analysis_calls is not None else None,
        "plane_transforms_reported_separately": plane_calls is not None,
        "charged_attempt_ms": charged_attempt_ms if charged_fields_found else None,
        "key_commit_ms": key_commit_ms,
        "total_charged_ms_including_key_commit": total,
        "packet_bytes": packet_bytes, "wire_bytes": wire_bytes,
        "whole_packet_cap_ok": packet_bytes <= PACKET_CAP if packet_bytes is not None else None,
        "roi_floor": floor, "map_stats": map_stats,
        "roi_floor_metadata_proven": floor_proven,
        "roi_floor_evidence_status": "proven_by_explicit_map_and_profile_metadata" if floor_proven else "missing_or_incomplete_evidence",
    }


def compare_common_ids(left: dict, right: dict) -> dict:
    """Compare source identity and MSE only for exact shared emitted IDs."""
    lm, rm = left.get("manifest", {}), right.get("manifest", {})
    lrows = left.get("records", left.get("commits", []))
    rrows = right.get("records", right.get("commits", []))
    lmap = {_capture_id(row): row for row in lrows if isinstance(row, dict) and _capture_id(row) is not None}
    rmap = {_capture_id(row): row for row in rrows if isinstance(row, dict) and _capture_id(row) is not None}
    shared = sorted(set(lmap) & set(rmap), key=str)
    mse_pairs = []
    for cid in shared:
        a = _num(lmap[cid], "active_rgb565_mse", "mse", "rgb565_mse")
        b = _num(rmap[cid], "active_rgb565_mse", "mse", "rgb565_mse")
        if a is not None and b is not None:
            mse_pairs.append({"id": cid, "left_mse": a, "right_mse": b, "right_minus_left": b-a})
    lpts, rpts = lm.get("selected_pts", []), rm.get("selected_pts", [])
    lhash, rhash = lm.get("frame_sha256", lm.get("image_sha256", [])), rm.get("frame_sha256", rm.get("image_sha256", []))
    return {"shared_ids": shared, "shared_id_count": len(shared),
            "same_source_sha256": lm.get("source_sha256") == rm.get("source_sha256") if lm.get("source_sha256") and rm.get("source_sha256") else None,
            "same_native_pts": lpts == rpts if lpts and rpts else None,
            "same_frame_hashes": lhash == rhash if lhash and rhash else None,
            "common_id_mse": mse_pairs,
            "mean_right_minus_left_mse": sum(x["right_minus_left"] for x in mse_pairs)/len(mse_pairs) if mse_pairs else None}


def audit_file(path: Path) -> dict:
    data = json.loads(path.read_text())
    records = []
    for case in data.get("cases", []):
        for record in case.get("records", []):
            item = audit_record(record)
            item["case"] = case.get("name")
            records.append(item)
    for record in data.get("records", []):
        records.append(audit_record(record))
    pins = data.get("source_sha256", {})
    if not pins:
        for entry in data.get("cases", []):
            manifest = entry.get("manifest", {})
            if manifest.get("source") and manifest.get("source_sha256"):
                pins[manifest["source"]] = manifest["source_sha256"]
    before = pin_audit(pins)
    # Preserve exact identifiers, including repeats in source content.
    cases = data.get("cases", [])
    manifests = [case.get("manifest", {}) for case in cases]
    comparisons = []
    for i, left in enumerate(cases):
        for right in cases[i + 1:]:
            comparisons.append({"left_case": left.get("name"), "right_case": right.get("name"),
                                **compare_common_ids(left, right)})
    return {"path": str(path), "records": records, "source_pin_audit_before": before,
            "source_manifests": [{"source": m.get("source"), "source_sha256": m.get("source_sha256"),
                                  "selected_pts": m.get("selected_pts", []),
                                  "frame_sha256": m.get("frame_sha256", m.get("image_sha256", []))} for m in manifests],
            "case_comparisons": comparisons,
            "claims_guard": {"mean_service_proves_30fps": False,
                             "immediate_ack_is_physical_drain": False,
                             "reason": "Mean sender timing does not establish 30 distinct presented frames/s; protocol ACK does not establish physical read-drain."}}


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    pos = (len(vals)-1)*q/100
    lo, hi = math.floor(pos), math.ceil(pos)
    return vals[lo] + (vals[hi]-vals[lo])*(pos-lo)


def stats(values: list[float]) -> dict:
    return {"n": len(values), "mean": statistics.mean(values), "p50_linear": percentile(values, 50),
            "p95_linear": percentile(values, 95), "max": max(values)} if values else {"n": 0}


def source_pins(data: dict) -> dict:
    declared = pin_audit(data.get("source_sha256", {}))
    media = []
    for entry in data.get("scenes", []) + data.get("paired_keys", []) + data.get("manifests", []):
        manifest = entry.get("manifest", {})
        raw, expected = manifest.get("source"), manifest.get("source_sha256")
        if raw and expected:
            path = Path(raw)
            actual = sha256(path) if path.is_file() else None
            media.append({"path": raw, "expected": expected, "actual": actual,
                          "matches": actual is not None and actual == expected})
    return {"declared": declared, "media_manifest_pins": media}


def codec_audit(data: dict) -> dict:
    scenes, packet_total = [], 0
    for scene in data.get("scenes", []):
        recs = scene.get("records", [])
        profiles = sorted({r.get("profile") for r in recs})
        groups = {p: {r.get("id"): r for r in recs if r.get("profile") == p} for p in profiles}
        profile_summary, comparisons, transform_checks = {}, [], []
        for profile, by_id in groups.items():
            rows = list(by_id.values())
            sizes = [r["bytes"] for r in rows if isinstance(r.get("bytes"), int)]
            profile_summary[profile] = {
                "record_count": len(rows), "packet_bytes": stats(sizes),
                "whole_packet_cap_fail_ids": [r.get("id") for r in rows if r.get("bytes", 0) > PACKET_CAP],
                "map_bytes": sorted({r.get("map_bytes") for r in rows}),
                "outer_header_crc_bytes": sorted({r.get("outer_header_crc_bytes") for r in rows}),
                "gm01_minus_ma01_byte_deltas": sorted({r["bytes"]-r["uniform_ma01_bytes"] for r in rows
                                                        if isinstance(r.get("bytes"),(int,float)) and isinstance(r.get("uniform_ma01_bytes"),(int,float))})}
            packet_total += len(rows)
            transform_checks.extend({"profile": profile, "id": r.get("id"),
                "analysis_count_cumulative": r.get("analysis_count"),
                "forward_calls_cumulative": r.get("forward_calls_total"),
                "one_analysis_three_plane_calls_per_frame": r.get("analysis_count") == r.get("id", -1)+1 and
                    r.get("forward_calls_total") == 3*(r.get("id", -1)+1)} for r in rows)
        uniform = groups.get("uniform16", {})
        for profile, by_id in groups.items():
            if profile == "uniform16":
                continue
            shared = sorted(set(uniform) & set(by_id))
            same_hash = all(uniform[i].get("input_sha256") == by_id[i].get("input_sha256") for i in shared)
            deltas = {metric: [{"id": i, "delta": by_id[i]["metrics"][metric]["mse"]-uniform[i]["metrics"][metric]["mse"]}
                               for i in shared if metric in uniform[i].get("metrics", {}) and metric in by_id[i].get("metrics", {})]
                      for metric in ("active", "roi", "background")}
            comparisons.append({"profile": profile, "common_id_count": len(shared), "same_source_hashes": same_hash,
                                "common_id_mse_deltas_vs_uniform16": deltas})
        manifest = scene.get("manifest", {})
        frames = manifest.get("frame_sha256", [])
        scenes.append({"name": scene.get("name"), "selected_pts": manifest.get("selected_pts", []),
                       "frame_sha256": frames, "distinct_content_hashes": len(set(frames)),
                       "profile_summary": profile_summary, "transform_counter_checks": transform_checks,
                       "common_id_comparisons": comparisons})
    fmt = data.get("format", {})
    return {"scenes": scenes, "combined_packet_count_recomputed": packet_total,
            "per_profile_transform_totals": {"analysis_calls": packet_total, "forward_plane_calls": packet_total*3,
                "scope": "Each profile is analyzed independently; each analysis performs three Y/U/V plane transforms."},
            "combined_packet_count_declared": data.get("combined_packet_count"),
            "uniform_ma01_pixel_pairs_declared": data.get("uniform_ma01_pixel_pairs"),
            "format": fmt, "map338_plus_outer50_net342": fmt.get("map_bytes_720x480") == 338 and fmt.get("outer_header_crc_bytes") == 50 and fmt.get("uniform_gm01_minus_ma01_bytes_720x480") == 342,
            "regions": data.get("regions"), "policy": data.get("policy"),
            "timing_scope": data.get("timing_scope"), "memory_scope": data.get("memory_scope")}


def rate_audit(data: dict) -> dict:
    decisions, scene_summaries = [], []
    for scene in data.get("scenes", []):
        cases = scene.get("cases", {})
        maps = {}
        for policy, case in cases.items():
            rows = case.get("rows", [])
            maps[policy] = {r.get("id"): r for r in rows}
            for r in rows:
                attempts = r.get("attempts", [])
                # Analysis is charged once; fallback attempt rows should expose 0 for the reused transform.
                components = r.get("map_build_ms", 0.0)+r.get("commit_ms", 0.0)
                components += sum(a.get("analyze_ms", 0.0)+a.get("candidate_ms", 0.0) for a in attempts)
                counts = r.get("verified_selected_scale_counts", r.get("selected_scale_counts", {}))
                decisions.append({"scene": scene.get("name"), "policy": policy, "id": r.get("id"),
                    "input_sha256": r.get("input_sha256"), "accepted": r.get("accepted"), "selected": r.get("selected"),
                    "attempt_count": len(attempts), "attempt_limit_ok": len(attempts) <= 2,
                    "attempt_bytes_are_materialized_candidate_packets": True,
                    "analysis_calls": r.get("analyze_calls"), "forward_plane_calls": r.get("forward_calls"),
                    "one_analysis_three_plane_calls_ok": r.get("analyze_calls") == 1 and r.get("forward_calls") == 3,
                    "attempt_candidate_packet_sizes": [a.get("bytes") for a in attempts],
                    "all_candidate_packets_within_cap": all(a.get("bytes", PACKET_CAP+1) <= r.get("cap_bytes", PACKET_CAP) for a in attempts),
                    "whole_packet_bytes": r.get("bytes"), "wire_bytes": r.get("wire_bytes"),
                    "accepted_packet_within_cap": r.get("bytes", 0) <= r.get("cap_bytes", PACKET_CAP),
                    "charged_component_sum_ms_including_all_attempts_and_commit": components,
                    "recorded_internal_service_ms": r.get("internal_service_ms"),
                    "component_sum_minus_internal_ms": components-r["internal_service_ms"] if isinstance(r.get("internal_service_ms"), (int,float)) else None,
                    "recorded_service_ms": r.get("service_ms"),
                    "verified_roi_scale_min": r.get("verified_roi_scale_min"),
                    "verified_scale8_block_count": counts.get("8") if isinstance(counts, dict) else None,
                    "priority_scale8_verified": policy != "priority" or (r.get("verified_roi_scale_min") == 8 and isinstance(counts,dict) and int(counts.get("8",0)) > 0)})
        common = sorted(set(maps.get("uniform", {})) & set(maps.get("priority", {})))
        mse = {}
        for metric in ("active", "roi", "background"):
            deltas = []
            for i in common:
                u, p = maps["uniform"][i], maps["priority"][i]
                if u.get("input_sha256") != p.get("input_sha256"):
                    continue
                uv = u.get("metrics", {}).get(metric, {}).get("mse")
                pv = p.get("metrics", {}).get(metric, {}).get("mse")
                if isinstance(uv,(int,float)) and isinstance(pv,(int,float)):
                    deltas.append({"id":i,"uniform_mse":uv,"priority_mse":pv,"priority_minus_uniform_mse":pv-uv})
            mse[metric] = {"rows": deltas, "mean_priority_minus_uniform_mse": statistics.mean(x["priority_minus_uniform_mse"] for x in deltas) if deltas else None}
        manifest = scene.get("manifest", {})
        scene_summaries.append({"name":scene.get("name"),"selected_pts":manifest.get("selected_pts",[]),
            "frame_sha256":manifest.get("frame_sha256",[]),"same_source_hashes_across_policies":all(maps["uniform"][i].get("input_sha256")==maps["priority"][i].get("input_sha256") for i in common),
            "common_id_mse":mse,"stored_comparison":scene.get("comparison")})
    paired = []
    for cohort in data.get("paired_keys", []):
        rows = cohort.get("records", [])
        groups = {}
        for selection in ("fallback", "normal"):
            selected = [r for r in rows if r.get("selected") == selection]
            groups[selection] = {"n":len(selected),"two_attempts":sum(r.get("attempts")==2 for r in selected),
                "accepted":sum(r.get("accepted") is True for r in selected),
                "shared_service_ms":stats([r["shared_service_ms"] for r in selected]),
                "naive_service_ms":stats([r["naive_service_ms"] for r in selected]),
                "shared_forward_calls":sorted({r.get("shared_forward_calls") for r in selected})}
        paired.append({"name":cohort.get("name"),"n":len(rows),"groups":groups,
            "input_id_hash_pairs_unique":len({(r.get("repeat"),r.get("source_index"),r.get("input_sha256")) for r in rows})==len(rows),
            "declared_two_attempt_pairs":cohort.get("two_attempt_pairs"),"declared_admitted_pairs":cohort.get("admitted_pairs"),
            "source_scope":cohort.get("source_scope")})
    counts = {"policy_decisions":len(decisions),
        "real_policy_decisions":sum(d["scene"]!="synthetic-noise-to-quiet" for d in decisions),
        "stress_policy_decisions":sum(d["scene"]=="synthetic-noise-to-quiet" for d in decisions),
        "admitted":sum(d["accepted"] is True for d in decisions),"rejected":sum(d["accepted"] is False for d in decisions),
        "attempt_count_histogram":{str(n):sum(d["attempt_count"]==n for d in decisions) for n in sorted({d["attempt_count"] for d in decisions})},
        "all_attempts_at_most_two":all(d["attempt_limit_ok"] for d in decisions),
        "all_rows_one_analysis_three_plane_calls":all(d["one_analysis_three_plane_calls_ok"] for d in decisions),
        "all_admitted_priority_rows_prove_scale8":all(d["priority_scale8_verified"] for d in decisions if d["policy"]=="priority" and d["accepted"])}
    policy_service=[]
    buckets={}
    for d in decisions: buckets.setdefault((d["scene"],d["policy"]),[]).append(d)
    for (scene_name,policy), rows in sorted(buckets.items()):
        policy_service.append({"scene":scene_name,"policy":policy,
            "charged_component_total_ms":sum(d["charged_component_sum_ms_including_all_attempts_and_commit"] for d in rows),
            "charged_component_ms":stats([d["charged_component_sum_ms_including_all_attempts_and_commit"] for d in rows]),
            "internal_service_ms":stats([d["recorded_internal_service_ms"] for d in rows if isinstance(d["recorded_internal_service_ms"],(int,float))]),
            "measured_service_ms":stats([d["recorded_service_ms"] for d in rows if isinstance(d["recorded_service_ms"],(int,float))])})
    return {"caps":{"nominal":data.get("nominal_cap_bytes"),"paired_pressure":data.get("paired_pressure_cap_bytes")},
        "priority_floor":data.get("priority_floor"),"causality":data.get("causality"),"counts":counts,
        "decisions":decisions,"scene_policy_service":policy_service,"scenes":scene_summaries,"paired_key_pressure":paired,
        "timing_scope":data.get("timing_scope"),"load_scope":data.get("load_scope"),"memory_scope":data.get("memory_scope")}


def fixture_audit(path: Path) -> dict:
    data=json.loads(path.read_text()); base=path.parent; file_rows=[]
    for name, meta in data.get("files",{}).items():
        p=base/name; actual=sha256(p) if p.is_file() else None; size=p.stat().st_size if p.is_file() else None
        file_rows.append({"file":name,"matches":p.is_file() and actual==meta.get("sha256") and size==meta.get("bytes"),
                          "expected_bytes":meta.get("bytes"),"actual_bytes":size,"expected_sha256":meta.get("sha256"),"actual_sha256":actual})
    cases=[{"name":c.get("name"),"packet_bytes":c.get("packet_bytes"),"whole_packet_within_cap":c.get("packet_bytes",PACKET_CAP+1)<=data.get("frame_cap",PACKET_CAP),
            "map_bytes":c.get("map_bytes"),"datagrams":c.get("datagrams"),"udp_payload_bytes":c.get("udp_payload_bytes"),
            "ipv4_udp_bytes":c.get("ipv4_udp_bytes"),"chunk_header_bytes":c.get("chunk_header_bytes"),
            "datagram_count_matches_1024_payload_chunks":c.get("datagrams")==math.ceil(c.get("packet_bytes",0)/1024),
            "udp_payload_accounting_matches":c.get("udp_payload_bytes")==c.get("packet_bytes",0)+c.get("datagrams",0)*c.get("chunk_header_bytes",0),
            "ipv4_udp_accounting_matches":c.get("ipv4_udp_bytes")==c.get("udp_payload_bytes",0)+c.get("datagrams",0)*28} for c in data.get("cases",[])]
    test_log=(base.parent/"tests.log").read_text() if (base.parent/"tests.log").is_file() else ""
    replay_log=(base.parent/"replay.log").read_text() if (base.parent/"replay.log").is_file() else ""
    test_line=next((line.strip() for line in test_log.splitlines() if line.strip().startswith("Ran ")),None)
    return {"format":data.get("format"),"frame_cap":data.get("frame_cap"),"two_slot_payload_cap":2*data.get("frame_cap",0),
        "total_datagrams_recomputed":sum(c["datagrams"] for c in cases),"total_datagrams_declared":data.get("total_datagrams"),
        "peak_slot_payload_bytes":data.get("peak_slot_payload_bytes"),"peak_slots":data.get("peak_slots"),
        "all_resources_drained":data.get("all_resources_drained"),"total_forward_plane_calls":data.get("total_forward_plane_calls"),
        "source_pins":pin_audit(data.get("source_sha256",{})),"files":file_rows,"all_fixture_file_hashes_match":all(x["matches"] for x in file_rows),
        "case_datagram_and_wire_accounting_all_match":all(c["datagram_count_matches_1024_payload_chunks"] and c["udp_payload_accounting_matches"] and c["ipv4_udp_accounting_matches"] for c in cases),
        "stored_link_test_log":{"ran_line":test_line,"reports_ok":"\nOK\n" in "\n"+test_log,"tests_log":test_log},
        "stored_replay_log":replay_log,"cases":cases,"scope":data.get("scope")}


def size_audit(exact: dict, gate: dict, prior: dict, prior_result_path: Path) -> dict:
    exact_rows=exact.get("rows",[]); gate_list=gate.get("rows",[])
    row_pairing_matches=len(exact_rows)==len(gate_list) and all(
        (a.get("kind"),a.get("input_sha256"))==(b.get("kind"),b.get("input_sha256"))
        for a,b in zip(exact_rows,gate_list))
    details=[]
    grouped={}
    for index,row in enumerate(exact_rows):
        gr=gate_list[index] if index<len(gate_list) else None
        full={a.get("label"):a for a in row.get("attempts_full",[])}
        pre={a.get("label"):a for a in row.get("attempts_preflight",[])}
        gate_attempts={a.get("label"):a for a in gr.get("attempts_gate",[])} if gr else {}
        pair_pre=[{"label":label,"estimated_bytes":a.get("bytes"),"actual_full_bytes":full.get(label,{}).get("bytes"),
                   "exact_size_match":a.get("bytes")==full.get(label,{}).get("bytes"),
                   "fit_match":a.get("fits")==full.get(label,{}).get("fits"),"serialized":a.get("serialized")}
                  for label,a in pre.items()]
        pair_gate=[{"label":label,"lower_bound_bytes":a.get("lower_bytes"),"actual_full_bytes":full.get(label,{}).get("bytes"),
                    "lower_bound_le_actual":isinstance(a.get("lower_bytes"),int) and a.get("lower_bytes")<=full.get(label,{}).get("bytes",-1),
                    "serialized":a.get("serialized"),"serialized_exact_bytes":a.get("bytes"),
                    "serialized_matches_actual":a.get("bytes")==full.get(label,{}).get("bytes") if a.get("serialized") else None,
                    "provably_rejected":a.get("provably_rejected")}
                   for label,a in gate_attempts.items()]
        selected_actual=next((a.get("label") for a in row.get("attempts_full",[]) if a.get("fits")),None)
        selected_pre=next((a.get("label") for a in row.get("attempts_preflight",[]) if a.get("fits")),None)
        selected_gate=gr.get("selected") if gr else None
        details.append({"kind":row.get("kind"),"input_sha256":row.get("input_sha256"),"cap":row.get("cap"),
            "attempt_count":len(full),"analysis_calls":row.get("analysis_calls"),"forward_plane_calls":row.get("forward_calls"),
            "exact_preflight_attempts":pair_pre,"gate_attempts":pair_gate,
            "all_exact_preflight_sizes_match_actual":len(pair_pre)==len(full) and all(x["exact_size_match"] and x["fit_match"] for x in pair_pre),
            "all_gate_bounds_le_actual":len(pair_gate)==len(full) and all(x["lower_bound_le_actual"] for x in pair_gate),
            "all_gate_emissions_match_actual":all(x["serialized_matches_actual"] is True for x in pair_gate if x["serialized"]),
            "selected_actual_full":selected_actual,"selected_exact_preflight":selected_pre,"selected_gate":selected_gate,
            "selection_matches":row.get("selected")==selected_actual==selected_pre==selected_gate,
            "accepted":row.get("accepted"),"packet_sha256_full":row.get("packet_sha256"),
            "packet_sha256_gate":gr.get("packet_sha256") if gr else None,
            "selected_packet_hash_matches":row.get("packet_sha256")==gr.get("packet_sha256") if gr else None,
            "full_ms":row.get("full_ms"),"exact_preflight_ms":row.get("preflight_ms"),"cheap_gate_ms":gr.get("gate_ms") if gr else None})
        grouped.setdefault(row.get("kind"),[]).append((row,gr))
    summaries={}
    for kind,pairs in grouped.items():
        rows=[x[0] for x in pairs]; gates=[x[1] for x in pairs if x[1] is not None]
        full_mean=statistics.mean(r["full_ms"] for r in rows)
        exact_mean=statistics.mean(r["preflight_ms"] for r in rows)
        gate_mean=statistics.mean(r["gate_ms"] for r in gates)
        summaries[kind]={"n":len(rows),"accepted":sum(r.get("accepted") is True for r in rows),
            "two_attempts":sum(len(r.get("attempts_full",[]))==2 for r in rows),
            "full_ms":stats([r["full_ms"] for r in rows]),"exact_preflight_ms":stats([r["preflight_ms"] for r in rows]),
            "cheap_gate_ms":stats([r["gate_ms"] for r in gates]),
            "exact_preflight_serialized_candidates":sum(a.get("serialized") is True for r in rows for a in r.get("attempts_preflight",[])),
            "cheap_gate_serialized_candidates":sum(a.get("serialized") is True for r in gates for a in r.get("attempts_gate",[])),
            "full_minus_preflight_mean_ms":full_mean-exact_mean,"full_minus_gate_mean_ms":full_mean-gate_mean}
    prior_path=ROOT/"experiments/python-game-size-study/prior-check.json"
    prior_log=(ROOT/"experiments/python-game-size-study/tests.log").read_text()
    benchmark=(ROOT/"experiments/python-game-size-study/benchmark.py").read_text()
    gate_benchmark=(ROOT/"experiments/python-game-size-study/gate_benchmark.py").read_text()
    return {"evidence":exact.get("evidence"),"policy":exact.get("policy"),"timing_scope":exact.get("timing_scope"),
        "memory_scope":exact.get("memory_scope"),"paired_row_order_and_source_ids_match":row_pairing_matches,
        "paired_calls_recomputed":len(details),"paired_calls_declared":exact.get("paired_calls"),
        "groups_recomputed":summaries,"rows":details,
        "all_exact_preflight_sizes_match_actual":all(r["all_exact_preflight_sizes_match_actual"] for r in details),
        "all_gate_lower_bounds_le_actual":all(r["all_gate_bounds_le_actual"] for r in details),
        "all_gate_emitted_sizes_match_actual":all(r["all_gate_emissions_match_actual"] for r in details),
        "all_selections_match":all(r["selection_matches"] for r in details),
        "all_selected_packet_hashes_match_full_vs_gate":all(r["selected_packet_hash_matches"] is True for r in details),
        "rgb_equality":{"per_row_rgb_hash_persisted":False,
            "exact_benchmark_asserts_oracle_rgb_hash_equality":"assert expected==old.encoder.expected_hash(0)==new.encoder.expected_hash(0)" in benchmark,
            "gate_benchmark_asserts_oracle_rgb_hash_equality":"assert expected==old.encoder.expected_hash(0)==new.encoder.expected_hash(0)" in gate_benchmark,
            "scope":"The run code asserts decoded RGB hash equality; result JSON does not store per-row RGB digests."},
        "prior_packet_check":{"source_pins":pin_audit(prior.get("source_sha256",{})),
            "expected_prior_result_sha256":prior.get("prior_result_sha256"),"actual_codec_result_sha256":sha256(prior_result_path),
            "prior_result_hash_matches":prior.get("prior_result_sha256")==sha256(prior_result_path),
            "regenerated_packet_sha_matches":prior.get("regenerated_packet_sha_matches"),
            "exact_plane_length_checks":prior.get("exact_plane_length_checks"),"scope":prior.get("scope")},
        "stored_size_test_log":{"ran":next((x.strip() for x in prior_log.splitlines() if x.strip().startswith("Ran ")),None),
            "reports_ok":"\nOK\n" in "\n"+prior_log,
            "80_family_bound_case_present":"test_eighty_families_lower_never_exceeds_exact" in prior_log,
            "64_positions_and_72_plane_shapes_case_present":"test_all_zigzag_positions_and_existing_72_plane_shapes" in prior_log}}


def main() -> None:
    codec_path=ROOT/"experiments/python-game-codec-study/results.json"
    rate_path=ROOT/"experiments/python-game-rate-study/results.json"
    size_path=ROOT/"experiments/python-game-size-study/results.json"
    gate_path=ROOT/"experiments/python-game-size-study/gate-results.json"
    prior_path=ROOT/"experiments/python-game-size-study/prior-check.json"
    fixture_path=ROOT/"experiments/python-game-link-study/fixtures/manifest.json"
    codec=json.loads(codec_path.read_text()); rate=json.loads(rate_path.read_text()); fixture=json.loads(fixture_path.read_text())
    size=json.loads(size_path.read_text()); gate=json.loads(gate_path.read_text()); prior=json.loads(prior_path.read_text())
    before={"codec":source_pins(codec),"rate":source_pins(rate),"size":source_pins(size),
        "gate":source_pins(gate),"prior_check":source_pins(prior),"fixtures":pin_audit(fixture.get("source_sha256",{}))}
    fixture_before=fixture_audit(fixture_path)
    payload={"scope":"Independent recomputation from stored Python rows and fixture hashes; no media/benchmark reruns.",
        "packet_cap_bytes":PACKET_CAP,"codec":codec_audit(codec),"rate":rate_audit(rate),
        "size_preflight":size_audit(size,gate,prior,codec_path),
        "link_fixtures":fixture_before,"source_pins_before":before}
    after={"codec":source_pins(json.loads(codec_path.read_text())),"rate":source_pins(json.loads(rate_path.read_text())),
        "size":source_pins(json.loads(size_path.read_text())),"gate":source_pins(json.loads(gate_path.read_text())),
        "prior_check":source_pins(json.loads(prior_path.read_text())),
        "fixtures":pin_audit(json.loads(fixture_path.read_text()).get("source_sha256",{}))}
    fixture_after=fixture_audit(fixture_path)
    payload["link_fixture_hashes_after"]=fixture_after["files"]
    payload["all_link_fixture_hashes_match_before_and_after"]=fixture_before["all_fixture_file_hashes_match"] and fixture_after["all_fixture_file_hashes_match"]
    payload["source_pins_after"]=after
    def pin_bundle_ok(bundle):
        declared=bundle.get("declared",bundle)
        media=bundle.get("media_manifest_pins",[])
        return declared.get("all_declared_pins_available_and_match",False) and all(x["matches"] for x in media)
    payload["all_source_pins_match_before_and_after"]=all(pin_bundle_ok(before[k]) and pin_bundle_ok(after[k]) for k in before)
    payload["claims_guard"]={"mean_or_p95_host_service_establishes_30_distinct_presented_fps":False,
        "immediate_decode_ack_establishes_physical_read_drain":False,
        "why":"Stored Python timing and in-process ACK evidence do not exercise live capture, network, target firmware, scanout or physical read-drain."}
    (OUT/"audit.json").write_text(json.dumps(payload,indent=2)+"\n")
    print(f"audited {payload['rate']['counts']['policy_decisions']} policy decisions and {len(payload['size_preflight']['rows'])} size decisions; source pins match={payload['all_source_pins_match_before_and_after']}")


if __name__ == "__main__":
    main()
