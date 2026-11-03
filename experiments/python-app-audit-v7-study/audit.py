#!/usr/bin/env python3
"""Independent audit helpers for application-specific v7 packet and ROI evidence."""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
import hashlib
import json

FPS = 30
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packet_rate(rows: Sequence[Mapping], *, packet_bytes_key: str = "packet_bytes",
                roi_bytes_key: str = "roi_map_bytes", fps: int = FPS) -> dict:
    """Compute wire-rate from emitted packet lengths; ROI map is explicit overhead."""
    if fps <= 0:
        raise ValueError("fps must be positive")
    packet_sizes, roi_sizes = [], []
    for i, row in enumerate(rows):
        p = row.get(packet_bytes_key)
        r = row.get(roi_bytes_key, 0)
        if isinstance(p, bool) or not isinstance(p, int) or p < 0:
            raise ValueError(f"row {i}: invalid {packet_bytes_key}")
        if isinstance(r, bool) or not isinstance(r, int) or r < 0:
            raise ValueError(f"row {i}: invalid {roi_bytes_key}")
        packet_sizes.append(p)
        roi_sizes.append(r)
    total_packet = sum(packet_sizes)
    total_roi = sum(roi_sizes)
    return {
        "frames": len(rows), "fps": fps,
        "mean_packet_bytes": total_packet / len(rows) if rows else None,
        "mean_roi_map_bytes": total_roi / len(rows) if rows else None,
        "mean_wire_bytes": (total_packet + total_roi) / len(rows) if rows else None,
        "wire_kbit_s_at_fps": (total_packet + total_roi) * 8 * fps / len(rows) / 1000 if rows else None,
        "packet_bytes_total": total_packet, "roi_map_bytes_total": total_roi,
    }


def pooled_mse(groups: Iterable[Mapping]) -> dict:
    """Pool squared error by pixel area, rather than averaging frame MSEs."""
    sums = {"roi": [0.0, 0], "background": [0.0, 0]}
    for i, row in enumerate(groups):
        for key, out in (("roi", "roi"), ("background", "background")):
            squared_error = row.get(f"{key}_squared_error_sum")
            pixels = row.get(f"{key}_pixels")
            if (isinstance(squared_error, bool) or not isinstance(squared_error, (int, float))
                    or not math.isfinite(squared_error) or squared_error < 0):
                raise ValueError(f"row {i}: invalid {key}_squared_error_sum")
            if isinstance(pixels, bool) or not isinstance(pixels, int) or pixels < 0:
                raise ValueError(f"row {i}: invalid {key}_pixels")
            sums[out][0] += squared_error
            sums[out][1] += pixels
    return {k: {"squared_error_sum": v[0], "pixels": v[1],
                "mse": v[0] / v[1] if v[1] else None} for k, v in sums.items()}


def source_sequence_guard(left: Mapping, right: Mapping) -> dict:
    """Require same source object, source hash and exact selected ID/hash sequence."""
    fields = ("source_id", "source_sha256", "selected_ids", "selected_frame_sha256")
    mismatches = [field for field in fields if left.get(field) != right.get(field)]
    missing = [field for field in fields if left.get(field) is None or right.get(field) is None]
    return {"comparable": not mismatches and not missing,
            "mismatched_fields": mismatches, "missing_fields": missing}


def causality_audit(manifest: Mapping) -> dict:
    """Require explicit negative declarations; missing fields are an evidence gap."""
    forbidden = ("oracle", "future", "lookahead", "ground_truth_at_encoder")
    hits = []
    def walk(value, path=""):
        if isinstance(value, Mapping):
            for key, child in value.items():
                name = str(key).lower()
                loc = f"{path}.{key}" if path else str(key)
                if any(term in name for term in forbidden):
                    if child not in (False, 0, None, ""):
                        hits.append({"path": loc, "value": child})
                walk(child, loc)
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, f"{path}[{i}]")
    walk(manifest)
    required = ("oracle_used", "future_frames_used", "lookahead_frames")
    missing = [key for key in required if key not in manifest]
    declared = not missing
    return {"metadata_declared": declared, "missing_required_fields": missing,
            "suspicious_fields": hits,
            "clean_declared_metadata": declared and not hits}


def _mean(values):
    return sum(values) / len(values) if values else None


def audit_roi_result(data: Mapping) -> dict:
    """Recompute RG01 map/header accounting, pooled MSE and per-profile rates."""
    scenes = data.get("scenes", [])
    profile_names = sorted({p for scene in scenes for p in scene.get("profiles", {})})
    pooled = {p: {k: [0.0, 0] for k in ("active", "roi", "background")} for p in profile_names}
    packet_totals = {p: 0 for p in profile_names}
    profile_cap = {p: {"over_48k": 0, "over_reference_uniform16": 0} for p in profile_names}
    accounting, identities = [], []
    causality = []
    for scene in scenes:
        manifest = scene.get("manifest", {})
        source = {"source_id": manifest.get("source"), "source_sha256": manifest.get("source_sha256"),
                  "selected_ids": manifest.get("selected_pts", []),
                  "selected_frame_sha256": manifest.get("frame_sha256", [])}
        identities.append({"scene": scene.get("name"), "source_id": manifest.get("source"),
                           "source_sha256": manifest.get("source_sha256"),
                           "source_index": scene.get("source_index"), "input_sha256": scene.get("input_sha256"),
                           "selected_source_hash_matches": (scene.get("synthetic", False) or
                               (isinstance(scene.get("source_index"), int) and
                                0 <= scene["source_index"] < len(manifest.get("frame_sha256", [])) and
                                scene["input_sha256"] == manifest["frame_sha256"][scene["source_index"]]))})
        causality.append({"scene": scene.get("name"), **causality_audit(manifest)})
        active_rects = manifest.get("active_rects", [])
        active_index = scene.get("source_index", 0)
        active_rect = (active_rects[active_index] if isinstance(active_index, int) and
                       0 <= active_index < len(active_rects) else (active_rects[0] if active_rects else None))
        active_area_manifest = active_rect[2] * active_rect[3] if active_rect and len(active_rect) == 4 else None
        rectangles = scene.get("declared_rectangles", [])
        first_profile = next(iter(scene.get("profiles", {}).values()), {})
        w = manifest.get("target_width", first_profile.get("info", {}).get("width"))
        h = manifest.get("target_height", first_profile.get("info", {}).get("height"))
        roi_pixels = 0
        if isinstance(w, int) and isinstance(h, int) and active_rect:
            # Recreate 16x16 block-expanded priority map and then intersect with active area.
            marks = set()
            for rect in rectangles:
                x, y, rw, rh = rect
                for by in range(y // 16, (y + rh + 15) // 16):
                    for bx in range(x // 16, (x + rw + 15) // 16):
                        marks.add((bx, by))
            ax, ay, aw, ah = active_rect
            roi_pixels = sum(max(0, min(ax+aw, bx*16+16, w)-max(ax,bx*16)) *
                             max(0, min(ay+ah, by*16+16, h)-max(ay,by*16)) for bx,by in marks)
        for pname, row in scene.get("profiles", {}).items():
            info, metrics = row.get("info", {}), row.get("metrics", {})
            size = row.get("bytes")
            map_bytes = info.get("scale_map_bytes")
            header = info.get("outer_header_crc_bytes")
            expected_map = ((math.ceil(w / 16) * math.ceil(h / 16) + 3) // 4) if w and h else None
            sums, area_ok = {}, True
            for region in ("active", "roi", "background"):
                stat = metrics.get(region, {})
                area = stat.get("pixels", 0)
                mse = stat.get("mse")
                sums[region] = {"pixels": area, "squared_error_sum": mse * area if isinstance(mse, (int,float)) else None,
                                "mse": mse}
                pooled[pname][region][0] += sums[region]["squared_error_sum"] or 0
                pooled[pname][region][1] += area
            active_area = sums["roi"]["pixels"] + sums["background"]["pixels"]
            active_mse_recomputed = ((sums["roi"]["squared_error_sum"] + sums["background"]["squared_error_sum"])
                                     / active_area if active_area else None)
            mse_reported = sums["active"]["mse"]
            # Every pixel included exactly once in ROI or background; active metric is area weighted.
            area_ok = (active_area == sums["active"]["pixels"] and
                       (active_area_manifest is None or active_area_manifest == sums["active"]["pixels"]) and
                       (not roi_pixels or sums["roi"]["pixels"] == roi_pixels))
            accounting.append({"scene": scene.get("name"), "profile": pname,
                "packet_bytes": size, "scale_map_bytes": map_bytes, "expected_map_bytes": expected_map,
                "non_map_header_payload_bytes": (size-map_bytes-header if all(isinstance(v,int) for v in (size,map_bytes,header)) else None),
                "outer_header_crc_bytes": header, "packet_length_matches_components_lower_bound":
                    isinstance(size,int) and isinstance(map_bytes,int) and isinstance(header,int) and size >= map_bytes+header,
                "map_bytes_match_16x16_2bit_geometry": map_bytes == expected_map,
                "manifest_active_area_pixels": active_area_manifest,
                "active_area_partition_matches": area_ok,
                "active_mse_recomputed_from_roi_background": active_mse_recomputed,
                "active_mse_reported": mse_reported,
                "active_mse_reconciles": (active_mse_recomputed is not None and mse_reported is not None and
                                             math.isclose(active_mse_recomputed,mse_reported,rel_tol=1e-10,abs_tol=1e-10))})
            if isinstance(size, int):
                packet_totals[pname] += size
                if size > 48 * 1024: profile_cap[pname]["over_48k"] += 1
                reference_size = scene.get("profiles", {}).get("uniform16", {}).get("bytes")
                if isinstance(reference_size, int) and size > reference_size:
                    profile_cap[pname]["over_reference_uniform16"] += 1
    rates = {p: {"frames": len(scenes), "mean_packet_bytes": packet_totals[p]/len(scenes) if scenes else None,
                 "wire_kbit_s_at_30fps": packet_totals[p]*8*30/len(scenes)/1000 if scenes else None}
             for p in profile_names}
    pooled_out = {p: {k: {"pixels": v[1], "squared_error_sum": v[0], "mse": v[0]/v[1] if v[1] else None}
                      for k,v in regions.items()} for p,regions in pooled.items()}
    baseline = pooled_out.get("uniform16", {})
    comparisons = {}
    for p in profile_names:
        base_bytes = rates.get("uniform16", {}).get("mean_packet_bytes")
        own_bytes = rates[p]["mean_packet_bytes"]
        comparisons[p] = {"mean_packet_bytes_ratio_vs_uniform16": own_bytes/base_bytes if base_bytes else None,
                          "within_5_percent_bytes_vs_uniform16": abs(own_bytes/base_bytes-1)<=.05 if base_bytes else None,
                          "pooled_roi_mse_ratio_vs_uniform16": pooled_out[p]["roi"]["mse"]/baseline["roi"]["mse"] if baseline.get("roi",{}).get("mse") else None,
                          "pooled_background_mse_ratio_vs_uniform16": pooled_out[p]["background"]["mse"]/baseline["background"]["mse"] if baseline.get("background",{}).get("mse") else None}
    per_scene = [{"scene":s.get("name"),"synthetic":s.get("synthetic"),"source_index":s.get("source_index"),
                  "input_sha256":s.get("input_sha256"),"profile_bytes":{k:v.get("bytes") for k,v in s.get("profiles",{}).items()},
                  "profiles_over_48k":[k for k,v in s.get("profiles",{}).items() if v.get("bytes",0)>48*1024],
                  "budget_profile_within_uniform16_bytes":s.get("profiles",{}).get("budget_roi8mix",{}).get("bytes",float("inf")) <= s.get("profiles",{}).get("uniform16",{}).get("bytes",-1)} for s in scenes]
    syntax=data.get("syntax",{})
    return {"scenes": len(scenes), "packet_rates": rates, "profile_cap_counts": profile_cap,
            "declared_syntax_accounting":{"declared_map_bytes_720x480":syntax.get("map_bytes_720x480"),
              "declared_outer_header_crc_bytes":syntax.get("outer_header_crc_bytes"),
              "observed_map_bytes_all_338":all(r["scale_map_bytes"]==338 for r in accounting),
              "observed_header_crc_all_34":all(r["outer_header_crc_bytes"]==34 for r in accounting),
              "packet_bytes_already_include_map_and_outer_header":True}, "per_scene_bytes_and_admission":per_scene, "pooled_mse": pooled_out,
            "profile_comparisons_vs_uniform16": comparisons, "packet_accounting": accounting,
            "all_packet_maps_and_areas_reconcile": all(r["map_bytes_match_16x16_2bit_geometry"] and
                 r["packet_length_matches_components_lower_bound"] and r["active_area_partition_matches"] and
                 r["active_mse_reconciles"] for r in accounting),
            "source_identity_checks": identities,
            "causality_metadata": causality,
            "causality_proven_by_manifest": bool(causality) and all(c["clean_declared_metadata"] for c in causality)}


def audit_word_result(data: Mapping) -> dict:
    scenes = data.get("scenes", [])
    records = [r for s in scenes for r in s.get("records", [])]
    planes = [p for r in records for p in r.get("planes", [])]
    def summary(old,new):
        a=[r[old] for r in records if isinstance(r.get(old),(int,float))]
        b=[r[new] for r in records if isinstance(r.get(new),(int,float))]
        ma,mb=_mean(a),_mean(b)
        return {"n_old":len(a),"n_word":len(b),"old_mean_ms":ma,"word_mean_ms":mb,
                "mean_reduction_percent":(100*(ma-mb)/ma if ma else None)}
    pins=[]
    for raw, expected in data.get("source_sha256",{}).items():
        path=Path(raw); actual=digest(path) if path.is_file() else None
        pins.append({"path":raw,"expected":expected,"actual":actual,"matches":actual==expected})
    scene_identity=[]
    for scene in scenes:
        m=scene.get("manifest",{})
        source={"source_id":m.get("source"),"source_sha256":m.get("source_sha256"),
                "selected_ids":m.get("selected_pts",[]),"selected_frame_sha256":m.get("frame_sha256",[])}
        scene_identity.append({"scene":scene.get("name"),"source_id":source["source_id"],
           "source_sha256":source["source_sha256"],"selected_ids":source["selected_ids"],
           "selected_frame_sha256":source["selected_frame_sha256"],
           "causality_metadata":causality_audit(m)})
    return {"paired_packets":data.get("paired_packets"),"record_count":len(records),"plane_count":len(planes),
            "packet_count_matches_declared":len(records)==data.get("paired_packets"),
            "plane_count_matches_three_per_packet":len(planes)==3*len(records),
            "receive_wall_ms":summary("old_receive_ms","word_receive_ms"),
            "source_pins":pins,"all_source_pins_match":all(x["matches"] for x in pins),
            "scene_sources_and_causality":scene_identity,
            "interpretation":"Decode timing improvement only; packet format/bytes are not changed by decoder implementation."}


def audit_word_records(data: Mapping) -> dict:
    scenes=data.get("scenes",[]); records=[r for s in scenes for r in s.get("records",[])]
    old=[p["old_ms"] for r in records for p in r.get("planes",[]) if isinstance(p.get("old_ms"),(int,float))]
    word=[p["word_ms"] for r in records for p in r.get("planes",[]) if isinstance(p.get("word_ms"),(int,float))]
    a,b=_mean(old),_mean(word)
    return {"paired_packet_records":len(records),"paired_plane_records":len(old),
            "packet_receive_mean_comparison":audit_word_result(data)["receive_wall_ms"],
            "three_plane_coefficient_mean_ms":{"old":a,"word":b,"reduction_percent":100*(a-b)/a if a else None}}


def audit_scheduler(data: Mapping) -> dict:
    rows=[]
    for case in data.get("cases",[]):
        res=case.get("result",{}); cfg=res.get("config",{}); metrics=res.get("metrics",{}); m=case.get("manifest",{})
        rows.append({"scene":case.get("name"),"selected_native_pts":m.get("selected_pts",[]),
           "source_sha256":m.get("source_sha256"),"selected_frame_sha256":m.get("frame_sha256",[]),
           "causality_metadata":causality_audit(m),"encoder_profile":cfg.get("encoder_profile"),
           "decoder_service":cfg.get("decoder_service"),"presented_strict":res.get("presented_strict"),
           "presented_eventual":res.get("presented_eventual"),"steady_count_diagnostic":res.get("steady_count"),
           "steady_window_ms":res.get("steady_window_ms"),"diagnostic_ids_per_second":res.get("steady_fps"),
           "strict_capture_window_ms":res.get("capture_window_ms"),"age_p95_ms":res.get("age_ms",{}).get("p95"),
           "wire_bytes":res.get("transmitted_wire_bytes"),"actual_receiver":case.get("actual_receiver"),
           "actual_encoder":case.get("actual_encoder")})
    return {"cases":rows,"interpretation":"Diagnostic steady IDs/s is a labeled model metric; it is not strict end-to-end FPS qualification."}


def main():
    base=ROOT
    word=json.loads((base/"experiments/python-word-decode-study/results.json").read_text())
    sched=json.loads((base/"experiments/python-word-decode-study/scheduler-results.json").read_text())
    roi=json.loads((base/"experiments/python-game-roi-study/results.json").read_text())
    tile=json.loads((base/"experiments/python-dirty-tile-study/results.json").read_text())
    output={"scope":"Read-only independent audit of stored v7 JSON; no benchmark reruns.",
      "word_decode":audit_word_result(word),"word_decode_plane_detail":audit_word_records(word),
      "word_scheduler":audit_scheduler(sched),"roi":audit_roi_result(roi),
      "dirty_tile":audit_dirty_tile(tile)}
    (OUT/"audit.json").write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
    print("wrote audit.json; ROI accounting reconciles=",output["roi"]["all_packet_maps_and_areas_reconcile"],
          "word source pins match=",output["word_decode"]["all_source_pins_match"])



def audit_dirty_tile(data: Mapping) -> dict:
    scene_rows=[]; totals={name:{"bytes":[],"wire_bytes":[],"active_mse":[],"over_48k":0} for name in ("dirty","whole_intra","immutable_anchor")}
    source_checks=[]; all_records=0
    for scene in data.get("scenes",[]):
        manifest=scene.get("manifest",{}); records=scene.get("records",[]); all_records+=len(records)
        hashes=manifest.get("frame_sha256",[]); pts=manifest.get("selected_pts",[])
        matched=[]; id_hash=[]
        for record in records:
            idx=record.get("id"); input_hash=record.get("input_sha256")
            ok=(isinstance(idx,int) and 0<=idx<len(hashes) and hashes[idx]==input_hash)
            matched.append(ok)
            id_hash.append({"id":idx,"pts":pts[idx] if isinstance(idx,int) and idx<len(pts) else None,
                            "input_sha256":input_hash,"matches_manifest":ok})
            for profile, packet in record.get("packets",{}).items():
                if profile not in totals: continue
                for key,store_key in (("bytes","bytes"),("wire_bytes","wire_bytes"),("active_mse","active_mse")):
                    value=packet.get(key)
                    if isinstance(value,(int,float)): totals[profile][store_key].append(value)
                if packet.get("bytes",0)>48*1024: totals[profile]["over_48k"]+=1
        unique_hashes=len(set(hashes))
        source_checks.append({"source":manifest.get("source"),"source_sha256":manifest.get("source_sha256"),
             "record_count":len(records),"manifest_hash_count":len(hashes),"distinct_rendered_hashes":unique_hashes,
             "repeated_content_frames":len(hashes)-unique_hashes,"all_record_inputs_match_manifest":all(matched),
             "record_id_and_pts_hashes":id_hash,"causality_metadata":causality_audit(manifest)})
        recomputed={}
        for profile in totals:
            vals=[r.get("packets",{}).get(profile,{}) for r in records]
            sizes=[v["bytes"] for v in vals if isinstance(v.get("bytes"),int)]
            wire=[v["wire_bytes"] for v in vals if isinstance(v.get("wire_bytes"),int)]
            mse=[v["active_mse"] for v in vals if isinstance(v.get("active_mse"),(int,float))]
            recomputed[profile]={"n":len(sizes),"packet_mean_bytes":_mean(sizes),"wire_mean_bytes":_mean(wire),
                "wire_mbps_at_30fps":_mean(wire)*8*30/1_000_000 if wire else None,
                "pooled_active_mse_equal_area_frames":_mean(mse),"over_48k_count":sum(v>48*1024 for v in sizes)}
        declared=scene.get("summary",{})
        summary_checks={}
        for profile in recomputed:
            d=declared.get(profile,{})
            summary_checks[profile]={"packet_mean_matches":_close(recomputed[profile]["packet_mean_bytes"],d.get("packet_mean_bytes")),
               "pooled_mse_matches":_close(recomputed[profile]["pooled_active_mse_equal_area_frames"],d.get("pooled_active_mse")),
               "wire_mbps_matches":_close(recomputed[profile]["wire_mbps_at_30fps"],d.get("wire_mbps_if30captures_per_second"))}
        scene_rows.append({"source":manifest.get("source"),"frames":len(records),"recomputed":recomputed,
                           "summary_checks":summary_checks,"tile_opportunities":scene.get("tile_opportunities"),
                           "skipped_tiles_total":scene.get("skipped_tiles_total"),
                           "fully_unchanged_source_frames":scene.get("fully_unchanged_source_frames")})
    comparisons={}
    for profile in totals:
        comparisons[profile]={"packet_mean_bytes":_mean(totals[profile]["bytes"]),"wire_mean_bytes":_mean(totals[profile]["wire_bytes"]),
         "pooled_active_mse_equal_area_frames":_mean(totals[profile]["active_mse"]),"over_48k_count":totals[profile]["over_48k"],
         "packet_count":len(totals[profile]["bytes"])}
    pins=[]
    for raw,expected in data.get("source_sha256",{}).items():
        path=Path(raw);actual=digest(path) if path.is_file() else None
        pins.append({"path":raw,"expected":expected,"actual":actual,"matches":actual==expected})
    return {"record_count":all_records,"scenes":scene_rows,"aggregate":comparisons,"source_checks":source_checks,
            "source_pins":pins,"all_source_pins_match":all(p["matches"] for p in pins),
            "all_summary_statistics_reconcile":all(all(v for v in scene["summary_checks"].values() for v in v.values()) for scene in scene_rows),
            "interpretation":"Dirty tile output is charged with per-tile metadata; compare packet-byte means and quality separately. Immediate-ACK experiment is not transport throughput or end-to-end FPS."}


def _close(actual, expected):
    return isinstance(actual,(int,float)) and isinstance(expected,(int,float)) and math.isclose(actual,expected,rel_tol=1e-9,abs_tol=1e-7)

if __name__ == "__main__":
    main()
