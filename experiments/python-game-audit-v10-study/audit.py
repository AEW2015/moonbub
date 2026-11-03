#!/usr/bin/env python3
"""Independent stdlib audit for selective UI, service accounting, and row-RLE studies."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CAP_BYTES = 49_152


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_pin_audit(pins: dict[str, str], base: Path = ROOT) -> dict:
    rows = []
    for raw, expected in sorted(pins.items()):
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        actual = sha256_file(path) if path.is_file() else None
        rows.append({"path": str(path), "expected": expected, "actual": actual,
                     "matches": actual == expected if actual is not None else None})
    return {"rows": rows, "missing": [r["path"] for r in rows if r["actual"] is None],
            "mismatched": [r["path"] for r in rows if r["actual"] is not None and not r["matches"]],
            "all_match": bool(rows) and all(r["matches"] is True for r in rows)}


def _first(row: dict, *keys: str) -> Any:
    for key in keys:
        if row.get(key) is not None:
            return row[key]
    return None


def _records(data: dict) -> list[dict]:
    result = []
    for key in ("records", "rows", "cases", "frames", "decisions", "samples"):
        val = data.get(key)
        if isinstance(val, list):
            result.extend(r for r in val if isinstance(r, dict))
    return result


def classify_input(row: dict, parent: dict | None = None) -> str:
    """Classify explicit provenance only; never infer real footage from a name."""
    parent = parent or {}
    synthetic = _first(row, "synthetic", "is_synthetic")
    if synthetic is None:
        synthetic = _first(parent, "synthetic", "is_synthetic")
    if synthetic is True:
        return "synthetic"
    if synthetic is False:
        return "real_source"
    source = _first(row, "source", "source_path", "media_path")
    if source is None and isinstance(row.get("manifest"), dict):
        source = row["manifest"].get("source")
    if source:
        return "source_unspecified_synthetic_flag"
    return "provenance_missing"


def _rect(rect: Any) -> tuple[int, int, int, int] | None:
    if isinstance(rect, dict):
        x, y = _first(rect, "x", "left"), _first(rect, "y", "top")
        w, h = _first(rect, "width", "w"), _first(rect, "height", "h")
        if None not in (x, y, w, h): return int(x), int(y), int(w), int(h)
    if isinstance(rect, (list, tuple)) and len(rect) == 4:
        return tuple(int(v) for v in rect)
    return None


def _area_union(rects: list[tuple[int, int, int, int]]) -> int:
    """Exact union area for small declared UI rectangle lists."""
    xs = sorted({x for x, _, w, _ in rects for x in (x, x + w)})
    total = 0
    for left, right in zip(xs, xs[1:]):
        intervals = sorted((y, y + h) for x, y, w, h in rects if x < right and x + w > left)
        covered = 0
        if intervals:
            lo, hi = intervals[0]
            for a, b in intervals[1:]:
                if a > hi:
                    covered += hi - lo
                    lo, hi = a, b
                else:
                    hi = max(hi, b)
            covered += hi - lo
        total += (right - left) * covered
    return total


def roi_coverage(row: dict, parent: dict | None = None) -> dict:
    parent = parent or {}
    declared_raw = _first(row, "declared_roi_rects", "declared_regions", "priority_rects", "all_roi_rects")
    if declared_raw is None:
        declared_raw = _first(parent, "declared_roi_rects", "declared_regions", "priority_rects", "rectangles")
    selected_raw = _first(row, "selected_roi_rects", "selected_regions", "selected_rects", "active_rects")
    if selected_raw is None and isinstance(row.get("selection"), dict):
        selected_raw = _first(row["selection"], "rects", "regions", "selected_rects")
    declared = [_rect(r) for r in declared_raw] if isinstance(declared_raw, list) else []
    selected = [_rect(r) for r in selected_raw] if isinstance(selected_raw, list) else []
    declared = [r for r in declared if r and r[2] > 0 and r[3] > 0]
    selected = [r for r in selected if r and r[2] > 0 and r[3] > 0]
    declared_area, selected_area = _area_union(declared), _area_union(selected)
    # Measure selected pixels inside the union of declared ROIs, avoiding double count.
    covered = 0
    if declared and selected:
        xs = sorted({x for x, _, w, _ in declared + selected for x in (x, x + w)})
        for left, right in zip(xs, xs[1:]):
            dints = [(y, y+h) for x,y,w,h in declared if x < right and x+w > left]
            sints = [(y, y+h) for x,y,w,h in selected if x < right and x+w > left]
            edges = sorted({p for pair in dints + sints for p in pair})
            for top, bottom in zip(edges, edges[1:]):
                d_on = any(a <= top and b >= bottom for a,b in dints)
                s_on = any(a <= top and b >= bottom for a,b in sints)
                if d_on and s_on: covered += (right-left)*(bottom-top)
    return {"declared_roi_pixels": declared_area if declared else None,
            "selected_roi_pixels": selected_area if selected else None,
            "selected_pixels_inside_declared_roi": covered if declared and selected else None,
            "selected_roi_coverage_fraction": covered / declared_area if declared_area else None,
            "evidence": "explicit_rectangles" if declared and selected else "missing_or_incomplete"}


def audit_selective(data: dict) -> dict:
    if isinstance(data.get("scenes"), list):
        cap = int(_first(data, "frame_cap_bytes", "packet_cap_bytes", "cap_bytes") or CAP_BYTES)
        rows = []
        for scene in data["scenes"]:
            declared = data.get("policies", {}).get("broad", {}).get("rectangles")
            requested_broad = _area_union([r for r in (_rect(x) for x in declared or []) if r]) if declared else None
            for policy_name, policy in scene.get("policies", {}).items():
                size = _first(policy, "bytes", "packet_bytes")
                selected_rects = [p.get("rect") for p in policy.get("selected", []) if isinstance(p, dict) and p.get("rect") is not None]
                geom = roi_coverage({"declared_roi_rects": policy.get("rectangles", declared or []),
                                     "selected_roi_rects": selected_rects})
                req = _first(policy, "requested_pixels")
                selected = _first(policy, "selected_pixels")
                fallback = policy.get("format") == "GM01"
                base_hash, packet_hash = policy.get("base_packet_sha256"), policy.get("packet_sha256")
                attempts = policy.get("attempts", [])
                rejected = [a for a in attempts if isinstance(a, dict) and not a.get("selected_in_output", False)]
                rows.append({"scene": scene.get("name"), "policy": policy_name,
                             "input_class": "synthetic" if scene.get("synthetic") is True else "real_source" if scene.get("synthetic") is False else "provenance_missing",
                             "packet_bytes": size, "cap_ok": size <= cap if size is not None else None,
                             "format": policy.get("format"), "accepted": policy.get("accepted"),
                             "requested_pixels": req, "selected_pixels": selected,
                             "selected_requested_fraction_rederived": selected / req if selected is not None and req else None,
                             "selected_common_broad_fraction": policy.get("selected_common_broad_fraction"),
                             "selected_rect_union_pixels": geom["selected_roi_pixels"],
                             "declared_region_pixels": req if req is not None else geom["declared_roi_pixels"],
                             "selected_roi_coverage_fraction": selected / req if selected is not None and req else None,
                             "common_broad_roi_coverage_fraction": selected / requested_broad if selected is not None and requested_broad else None,
                             "selected_rgb565_mismatches": policy.get("selected_rgb565_mismatches"),
                             "unselected_base_rgb565_mismatches": policy.get("unselected_base_rgb565_mismatches"),
                             "fallback_gm01_identity": packet_hash == base_hash if fallback and packet_hash and base_hash else (False if fallback else None),
                             "deadline_hit": policy.get("deadline_hit"), "fallback_reason": policy.get("reason"),
                             "attempt_count": len(attempts), "rejected_attempt_count": len(rejected),
                             "rejected_attempt_service_ms": sum(float(a.get("encode_ms", 0)) + float(a.get("validate_ms", 0)) for a in rejected),
                             "full_service_ms": policy.get("full_service_ms")})
        counts = {"scenes": len(data["scenes"]), "decisions": len(rows),
                  "real_source_decisions": sum(r["input_class"] == "real_source" for r in rows),
                  "synthetic_decisions": sum(r["input_class"] == "synthetic" for r in rows),
                  "cap_fits": sum(r["cap_ok"] is True for r in rows),
                  "deadline_fallbacks": sum(r["deadline_hit"] is True and r["fallback_gm01_identity"] is True for r in rows),
                  "gm01_fallbacks": sum(r["format"] == "GM01" for r in rows),
                  "gh01_outputs": sum(r["format"] == "GH01" for r in rows),
                  "attempts": sum(r["attempt_count"] for r in rows),
                  "rejected_attempts": sum(r["rejected_attempt_count"] for r in rows),
                  "rejected_attempt_service_ms": sum(r["rejected_attempt_service_ms"] for r in rows)}
        temporal = data.get("temporal", {})
        temporal_frames = temporal.get("frames", []) if isinstance(temporal, dict) else []
        temporal_counts = {"frames": len(temporal_frames),
                           "GH01": temporal.get("GH01"), "GM01": temporal.get("GM01"),
                           "fallback_identity_rows": sum(f.get("format") == "GM01" and f.get("packet_sha256") == f.get("base_packet_sha256") for f in temporal_frames)}
        return {"row_count": len(rows), "counts": counts, "rows": rows,
                "temporal": temporal_counts, "packet_cap_bytes": cap,
                "policy_scope": data.get("policy_scope"), "timing_scope": data.get("timing_scope"),
                "deployment_scope": data.get("deploy_scope"),
                "missing_real_synthetic_provenance_count": sum(r["input_class"] == "provenance_missing" for r in rows)}
    rows = []
    cap = _first(data, "frame_cap_bytes", "packet_cap_bytes", "cap_bytes") or CAP_BYTES
    inherited = dict(data)
    for case in _records(data):
        parent = case
        for key in ("declared_roi_rects", "declared_regions", "priority_rects", "all_roi_rects", "rectangles"):
            if key not in parent and key in inherited:
                parent = {**parent, key: inherited[key]}
        items = case.get("records", case.get("frames", case.get("decisions")))
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict): continue
                rows.append(_selective_row(item, parent, cap))
        elif any(k in case for k in ("selected_roi_rects", "selected_regions", "packet_bytes", "fallback")):
            rows.append(_selective_row(case, parent, cap))
    return {"row_count": len(rows), "rows": rows, "packet_cap_bytes": cap,
            "all_observed_packets_within_cap": all(r["cap_ok"] is True for r in rows if r["packet_bytes"] is not None),
            "fallback_identity_checks": [{"id": r["id"], "identity": r["fallback_packet_identity"]} for r in rows],
            "missing_packet_size_rows": sum(r["packet_bytes"] is None for r in rows),
            "missing_real_synthetic_provenance_count": sum(r["input_class"] == "provenance_missing" for r in rows)}


def _selective_row(row: dict, parent: dict, cap: int) -> dict:
    size = _first(row, "packet_bytes", "whole_frame_bytes", "selected_bytes", "bytes")
    fallback = row.get("fallback") if isinstance(row.get("fallback"), dict) else {}
    primary = _first(row, "gm01_fallback_sha256", "fallback_packet_sha256", "fallback_sha256")
    baseline = _first(row, "baseline_gm01_sha256", "actual_gm01_sha256", "gm01_packet_sha256")
    if primary is None: primary = _first(fallback, "packet_sha256", "sha256", "gm01_sha256")
    if baseline is None: baseline = _first(row, "baseline_packet_sha256")
    return {"id": _first(row, "id", "frame_id", "capture_id"),
            "name": _first(row, "name", "case", "profile"),
            "input_class": classify_input(row, parent), "packet_bytes": size,
            "cap_ok": size <= cap if size is not None else None,
            "roi_coverage": roi_coverage(row, parent),
            "fallback_packet_identity": primary == baseline if primary is not None and baseline is not None else None,
            "fallback_sha256": primary, "baseline_gm01_sha256": baseline,
            "rejected": _first(row, "rejected", "admitted") is False or str(_first(row, "status", "decision") or "").lower() in {"reject", "rejected"}}


def audit_service(data: dict) -> dict:
    if isinstance(data.get("cases"), list) and all(isinstance(c.get("result"), dict) for c in data["cases"]):
        cases = []
        for case in data["cases"]:
            result, cfg = case["result"], case["result"].get("config", {})
            cpu = result.get("cpu_services", [])
            resize = result.get("resize_services", [])
            summary = result.get("service_summary", {}).get("rejected_encode_ms", {})
            rmean, rn = summary.get("mean"), int(summary.get("n", 0))
            cases.append({"name": case.get("name"), "kind": case.get("kind"),
                          "charged": case.get("charged"),
                          "transport_cpu_enabled": cfg.get("transport_cpu"), "resize_cpu_enabled": cfg.get("resize_cpu"),
                          "cpu_service_events": len(cpu), "cpu_service_stages": sorted({x.get("stage") for x in cpu}),
                          "cpu_actual_wall_ms": sum(float(x.get("wall_ms", 0)) for x in cpu),
                          "cpu_charged_service_ms": sum(float(x.get("service_ms", 0)) for x in cpu),
                          "resize_service_events": len(resize),
                          "resize_actual_wall_ms": sum(float(x.get("wall_ms", 0)) for x in resize),
                          "resize_charged_service_ms": sum(float(x.get("service_ms", 0)) for x in resize),
                          "rejected_encode_n": rn,
                          "rejected_encode_service_ms": (float(rmean) * rn) if rmean is not None and rn else 0.0,
                          "presented_count": result.get("metrics", {}).get("presented_count"),
                          "steady_fps": result.get("metrics", {}).get("steady_fps"),
                          "unresolved_cpu": result.get("unresolved_cpu"),
                          "all_modeled_cpu_idle_at_end": all(v == 0 for v in (result.get("unresolved_cpu") or {}).values())})
        paired = []
        for pair in data.get("pairs", []):
            paired.append({"name": pair.get("name"),
                           "common_prepared_count": len(pair.get("common_prepared_ids", [])),
                           "common_presented_count": len(pair.get("common_presented_ids", [])),
                           "same_packet_count": len(pair.get("same_packet_ids", [])),
                           "only_zero_cpu_presented_count": len(pair.get("only_zero_cpu_presented", [])),
                           "only_charged_presented_count": len(pair.get("only_charged_presented", [])),
                           "caveat": pair.get("caveat")})
        zero = [c for c in cases if c["charged"] is False]
        charged = [c for c in cases if c["charged"] is True]
        return {"case_count": len(cases), "cases": cases,
                "zero_cpu_case_count": len(zero), "charged_cpu_case_count": len(charged),
                "zero_cpu_actual_wall_ms": sum(c["cpu_actual_wall_ms"] + c["resize_actual_wall_ms"] for c in zero),
                "zero_cpu_charged_service_ms": sum(c["cpu_charged_service_ms"] + c["resize_charged_service_ms"] for c in zero),
                "charged_cpu_service_ms": sum(c["cpu_charged_service_ms"] + c["resize_charged_service_ms"] for c in charged),
                "rejected_encode_service_ms_all_cases": sum(c["rejected_encode_service_ms"] for c in cases),
                "all_model_cpu_queues_drained": all(c["all_modeled_cpu_idle_at_end"] for c in cases),
                "pairs": paired,
                "service_scope": data.get("service_scope"), "acquisition_scope": data.get("acquisition_scope"),
                "timing_scope": data.get("timing_scope"), "memory_scope": data.get("memory_scope"),
                "complete_pipeline_limits": [data.get(k) for k in ("acquisition_scope", "timing_scope", "memory_scope")]}
    rows = _records(data)
    rejected = []
    missing_cost = []
    total = 0.0
    for i, row in enumerate(rows):
        status = str(_first(row, "status", "decision", "outcome") or "").lower()
        is_rejected = row.get("rejected") is True or row.get("admitted") is False or status in {"reject", "rejected", "drop", "dropped"}
        parts = row.get("service_components_ms", row.get("service_components", {}))
        explicit = _first(row, "charged_service_ms", "total_service_ms", "service_ms", "charged_ms")
        vals = ([float(v) for v in parts.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
                if isinstance(parts, dict) else [])
        cost = float(explicit) if explicit is not None else sum(vals) if vals else None
        if cost is None:
            if is_rejected: missing_cost.append(i)
        else:
            total += cost
            if is_rejected: rejected.append({"row": i, "service_ms": cost})
    return {"row_count": len(rows), "rejected_rows_with_cost": rejected,
            "rejected_rows_missing_cost_indexes": missing_cost,
            "all_rejected_work_charged": not missing_cost,
            "service_total_ms_including_rejects": total,
            "service_cost_basis": "row explicit total or sum of explicit component fields"}


def audit_standard_video(data: dict) -> dict:
    cases = data.get("cases", [])
    grouped: dict[str, list[dict]] = {}
    rows = []
    for case in cases:
        name = case.get("source")
        grouped.setdefault(name, []).append(case)
        records = case.get("records", [])
        summary = case.get("summary", {})
        reference = case.get("reference", {})
        record_ids = [r.get("id") for r in records]
        manifest = case.get("manifest", {})
        source_frames = manifest.get("frame_sha256", [])
        native_packets = reference.get("packets", []) if isinstance(reference, dict) else []
        packet_sum = sum(int(p.get("bytes", 0)) for p in native_packets)
        extradata = reference.get("extradata_bytes") if isinstance(reference, dict) else None
        native_rederived = packet_sum + int(extradata or 0)
        coded = summary.get("coded_bytes")
        pooled = {}
        for region in ("active", "roi", "background"):
            errsum = sum(float(r.get("quality", {}).get(region, {}).get("squared_error_sum", 0)) for r in records)
            pixels = sum(int(r.get("quality", {}).get(region, {}).get("pixels", 0)) for r in records)
            mse = errsum / pixels if pixels else None
            pooled[region] = {"squared_error_sum": errsum, "pixels": pixels, "mse_rederived": mse,
                              "psnr_rederived": 10.0 * math.log10(255.0 * 255.0 / mse) if mse and mse > 0 else None,
                              "stored_mse": summary.get("pooled", {}).get(region, {}).get("mse"),
                              "stored_psnr": summary.get("pooled", {}).get(region, {}).get("psnr"),
                              "stored_quality_matches": (abs(mse - summary.get("pooled", {}).get(region, {}).get("mse", float("inf"))) < 1e-9 and
                                                         abs((10.0 * math.log10(255.0 * 255.0 / mse) if mse and mse > 0 else float("inf")) - summary.get("pooled", {}).get(region, {}).get("psnr", float("inf"))) < 1e-9)}
        output_pts = reference.get("output_pts") if isinstance(reference, dict) else None
        pts_ok = output_pts == list(range(60)) if output_pts is not None else None
        rows.append({"source": name, "profile": case.get("profile"), "frame_count": len(records),
                     "manifest_frame_hash_count": len(source_frames),
                     "manifest_unique_rgb_frames": manifest.get("unique_frame_count"),
                     "coded_bytes_records_sum": sum(int(r.get("bytes", 0)) for r in records),
                     "coded_bytes_summary": coded,
                     "native_packet_bytes_sum": packet_sum if native_packets else None,
                     "native_extradata_bytes": extradata,
                     "native_packet_plus_extradata_bytes": native_rederived if native_packets else None,
                     "native_coded_bytes_matches_summary": native_rederived == coded if native_packets else None,
                     "records_sum_matches_summary": sum(int(r.get("bytes", 0)) for r in records) == coded if coded is not None else None,
                     "decoded_ids_exact_0_to_59": record_ids == list(range(60)),
                     "native_decoder_output_pts": output_pts,
                     "native_decoder_pts_exact_0_to_59": pts_ok,
                     "pooled_quality": pooled,
                     "profile_crf_or_quality_parameter": case.get("requested_quality_parameter"),
                     "cross_encoder_quality_parameters_comparable": False})
    manifest_checks = []
    for source, source_cases in grouped.items():
        hashes = [c.get("manifest", {}).get("frame_sha256", []) for c in source_cases]
        manifest_checks.append({"source": source, "profile_count": len(source_cases),
                                "all_manifest_frame_hashes_identical": bool(hashes) and all(h == hashes[0] for h in hashes),
                                "common_frame_hash_count": len(hashes[0]) if hashes else 0,
                                "profile_names": [c.get("profile") for c in source_cases]})
    selected = {}
    desired = {"mass-effect-combat": ("gm_roi8bg16", "libx265_q36", "libsvtav1_q48")}
    by_key = {(r["source"], r["profile"]): r for r in rows}
    for source, profiles in desired.items():
        for profile in profiles:
            row = by_key.get((source, profile))
            if row:
                case = next(c for c in cases if c.get("source") == source and c.get("profile") == profile)
                selected[profile] = {"coded_mbps_at_hypothetical30": case.get("summary", {}).get("coded_mbps_at_hypothetical30"),
                                     "pooled_active_psnr": row["pooled_quality"]["active"]["psnr_rederived"],
                                     "mean_frame_bytes": case.get("summary", {}).get("mean_bytes")}
    rgb_unique = {}
    source_unique_frame_counts = {}
    for source, source_cases in grouped.items():
        rgb_unique[source] = sorted({len({r.get("decoded_rgb565_sha256") for r in c.get("records", [])}) for c in source_cases})
        source_unique_frame_counts[source] = sorted({c.get("manifest", {}).get("unique_frame_count") for c in source_cases})
    return {"profile_count": len(cases), "total_decoded_records": sum(len(c.get("records", [])) for c in cases),
            "native_codec_output_records": sum(len(c.get("records", [])) for c in cases if c.get("reference")),
            "profile_count_by_source": {s: len(cs) for s, cs in grouped.items()},
            "source_manifest_checks": manifest_checks,
            "all_profile_manifests_same_per_source": bool(manifest_checks) and all(x["all_manifest_frame_hashes_identical"] for x in manifest_checks),
            "profiles": rows, "selected_combat_rd_points": selected,
            "distinct_decoded_rgb_counts_by_source_and_profile_range": rgb_unique,
            "manifest_unique_source_rgb_frame_counts": source_unique_frame_counts,
            "quality_scope": data.get("quality_scope"), "rate_scope": data.get("rate_scope"),
            "timing_scope": data.get("timing_scope"),
            "crf_values_are_not_cross_encoder_equal_quality": True,
            "target_hardware_decode_proven": False}


def audit_color_floor(data: dict) -> dict:
    rows = []
    by_source: dict[str, dict] = {}
    for case in data.get("cases", []):
        profile = {"source": case.get("source"), "method": case.get("method"), "distinct_input_rgb_hashes": case.get("distinct_input_rgb_hashes")}
        for region in ("active", "roi", "background"):
            records = case.get("records", [])
            error = sum(float(r.get("quality", {}).get(region, {}).get("squared_error_sum", 0)) for r in records)
            pixels = sum(int(r.get("quality", {}).get(region, {}).get("pixels", 0)) for r in records)
            mse = error / pixels if pixels else None
            psnr = 10 * math.log10(255 * 255 / mse) if mse and mse > 0 else None
            stored = case.get("summary", {}).get("pooled", {}).get(region, {})
            profile[region] = {"mse_rederived": mse, "psnr_rederived": psnr,
                               "stored_mse": stored.get("mse"), "stored_psnr": stored.get("psnr"),
                               "matches_stored": mse is not None and abs(mse - stored.get("mse", float("inf"))) < 1e-9 and abs(psnr - stored.get("psnr", float("inf"))) < 1e-9}
        rows.append(profile)
        by_source.setdefault(case.get("source"), {})[case.get("method")] = profile
    floor_gaps = {}
    for source, methods in by_source.items():
        pyav, gm = methods.get("pyav_yuv420_roundtrip"), methods.get("gm_integer_yuv420_roundtrip")
        floor_gaps[source] = {"pyav_active_psnr": pyav["active"]["psnr_rederived"] if pyav else None,
                              "gm_active_psnr": gm["active"]["psnr_rederived"] if gm else None,
                              "pyav_minus_gm_active_psnr_db": pyav["active"]["psnr_rederived"] - gm["active"]["psnr_rederived"] if pyav and gm else None,
                              "interpretation": "uncompressed conversion floor probe; does not normalize codec RD comparisons"}
    return {"case_count": len(rows), "cases": rows, "active_color_conversion_floor_comparison": floor_gaps,
            "all_pooled_quality_rederived_matches": all(p[r]["matches_stored"] for p in rows for r in ("active", "roi", "background")),
            "scope": data.get("scope"), "coded_stream_comparison": False}


def audit_common_color(data: dict, prior_results: Path) -> dict:
    cases = data.get("cases", [])
    rows = []
    groups: dict[str, list[dict]] = {}
    for case in cases:
        records = case.get("records", [])
        ref = case.get("reference", {})
        packet_sum = sum(int(p.get("bytes", 0)) for p in ref.get("packets", [])) if isinstance(ref, dict) else 0
        extra = int(ref.get("extradata_bytes", 0)) if isinstance(ref, dict) else 0
        native = bool(ref)
        ids = [r.get("id") for r in records]
        grouped = groups.setdefault(case.get("source"), [])
        grouped.append(case)
        quality = {}
        for region in ("active", "roi", "background"):
            err = sum(float(r.get("quality", {}).get(region, {}).get("squared_error_sum", 0)) for r in records)
            pixels = sum(int(r.get("quality", {}).get(region, {}).get("pixels", 0)) for r in records)
            mse = err / pixels if pixels else None
            psnr = 10 * math.log10(255 * 255 / mse) if mse and mse > 0 else None
            stored = case.get("summary", {}).get("pooled", {}).get(region, {})
            quality[region] = {"squared_error_sum": err, "pixels": pixels, "mse_rederived": mse,
                               "psnr_rederived": psnr,
                               "matches_stored": mse is not None and abs(mse-stored.get("mse", float("inf"))) < 1e-9 and abs(psnr-stored.get("psnr", float("inf"))) < 1e-9}
        native_pts = [p.get("pts") for p in ref.get("packets", [])] if native else []
        emitted = [pts for call in ref.get("input_calls", []) for pts in call.get("emitted_pts", [])] if native else []
        rows.append({"source": case.get("source"), "profile": case.get("profile"),
                     "record_count": len(records), "record_ids_exact_0_to_59": ids == list(range(60)),
                     "evidence_origin": case.get("evidence_origin", "new common-color codec run"),
                     "gm_reused_not_new_decode": str(case.get("profile", "")).startswith("gm_") and "reused" in str(case.get("evidence_origin", "")).lower(),
                     "native_encoder": ref.get("requested_options") if isinstance(ref, dict) else None,
                     "native_packet_bytes_plus_extradata": packet_sum + extra if native else None,
                     "record_bytes_sum": sum(int(r.get("bytes", 0)) for r in records),
                     "coded_bytes": case.get("summary", {}).get("coded_bytes"),
                     "native_bytes_match_records": (packet_sum + extra == sum(int(r.get("bytes", 0)) for r in records)) if native else None,
                     "native_bytes_match_summary": (packet_sum + extra == case.get("summary", {}).get("coded_bytes")) if native else None,
                     "native_packet_pts_exact_0_to_59": native_pts == list(range(60)) if native else None,
                     "native_emitted_pts_exact_0_to_59": emitted == list(range(60)) if native else None,
                     "pooled_quality": quality,
                     "scope": case.get("scope")})
    manifest_checks = []
    for source, source_cases in groups.items():
        manifests = [c.get("manifest", {}) for c in source_cases]
        hashes = [m.get("frame_sha256", []) for m in manifests]
        manifest_checks.append({"source": source, "profile_count": len(source_cases),
                                "all_frame_hashes_identical": bool(hashes) and all(h == hashes[0] for h in hashes),
                                "frame_count": len(hashes[0]) if hashes else 0})
    actual_new = sum(r["record_count"] for r in rows if not r["gm_reused_not_new_decode"])
    reused_gm = sum(r["record_count"] for r in rows if r["gm_reused_not_new_decode"])
    prior = sha256_file(prior_results) if prior_results.is_file() else None
    expected_prior = data.get("prior_results_sha256")
    prior_manifest_match = None
    if prior_results.is_file():
        original = json.loads(prior_results.read_text())
        old = {(c.get("source"), c.get("profile")): c.get("manifest", {}).get("frame_sha256") for c in original.get("cases", [])}
        prior_manifest_match = all(old.get((c.get("source"), c.get("profile"))) == c.get("manifest", {}).get("frame_sha256")
                                   for c in cases if (c.get("source"), c.get("profile")) in old)
    rd_points = {}
    desired = {"mass-effect-combat": ("gm_roi8bg16", "libx265_q36", "libsvtav1_q48"),
               "mass-effect-2600": ("gm_roi8bg16", "libx265_q28", "libsvtav1_q38")}
    by_key = {(c.get("source"), c.get("profile")): c for c in cases}
    for source, profiles in desired.items():
        for profile in profiles:
            case = by_key.get((source, profile))
            if case:
                pooled = case.get("summary", {}).get("pooled", {})
                rd_points.setdefault(source, {})[profile] = {"coded_mbps_at_hypothetical30": case.get("summary", {}).get("coded_mbps_at_hypothetical30"),
                                                              "active_psnr": pooled.get("active", {}).get("psnr"),
                                                              "roi_psnr": pooled.get("roi", {}).get("psnr")}
    return {"profile_count": len(cases), "record_rows": rows,
            "new_native_codec_output_records": actual_new,
            "reused_gm_output_records_not_double_counted": reused_gm,
            "manifest_checks": manifest_checks,
            "all_profile_manifests_same_per_source": bool(manifest_checks) and all(m["all_frame_hashes_identical"] for m in manifest_checks),
            "native_packet_plus_extradata_matches_records_and_summaries": all(r["native_bytes_match_records"] is True and r["native_bytes_match_summary"] is True for r in rows if r["native_bytes_match_records"] is not None),
                "native_pts_and_emitted_pts_exact": all(r["native_packet_pts_exact_0_to_59"] and r["native_emitted_pts_exact_0_to_59"] for r in rows if r["native_packet_pts_exact_0_to_59"] is not None),
                "all_pooled_quality_independently_matches": all(q["matches_stored"] for r in rows for q in r["pooled_quality"].values()),
            "prior_original_results_sha256_expected": expected_prior,
            "prior_original_results_sha256_actual": prior,
            "prior_original_results_pin_matches": prior == expected_prior if expected_prior else None,
                "frame_manifests_match_original_profiles": prior_manifest_match,
            "selected_common_color_rd_points": rd_points,
            "scope": data.get("scope"), "timing_scope": data.get("timing_scope")}
    rows = _records(data)
    rejected = []
    missing_cost = []
    total = 0.0
    for i, row in enumerate(rows):
        status = str(_first(row, "status", "decision", "outcome") or "").lower()
        is_rejected = row.get("rejected") is True or row.get("admitted") is False or status in {"reject", "rejected", "drop", "dropped"}
        components = row.get("service_components_ms", row.get("service_components", {}))
        explicit = _first(row, "charged_service_ms", "total_service_ms", "service_ms", "charged_ms")
        if explicit is not None:
            cost = float(explicit)
        elif isinstance(components, dict):
            numeric = [float(v) for v in components.values() if isinstance(v, (int, float)) and not isinstance(v, bool)]
            cost = sum(numeric) if numeric else None
        else:
            cost = None
        if cost is None:
            if is_rejected: missing_cost.append(i)
        else:
            total += cost
            if is_rejected: rejected.append({"row": i, "service_ms": cost})
    backends = {}
    for row in rows:
        backend = _first(row, "timing_backend", "backend", "measurement_kind")
        if backend is not None:
            key = str(backend).lower()
            backends[key] = backends.get(key, 0) + 1
    assumptions = _first(data, "complete_pipeline_assumptions", "pipeline_assumptions", "assumptions")
    scope = _first(data, "pipeline_scope", "scope", "measurement_scope")
    return {"row_count": len(rows), "rejected_rows_with_cost": rejected,
            "rejected_rows_missing_cost_indexes": missing_cost,
            "all_rejected_work_charged": not missing_cost,
            "service_total_ms_including_rejects": total,
            "service_cost_basis": "row explicit total or sum of explicit component fields",
            "timing_rows_by_backend": backends,
            "complete_pipeline_assumptions": assumptions,
            "pipeline_scope": scope,
            "complete_pipeline_evidence": "present" if assumptions is not None or scope is not None else "missing",
            "native_timing_present": any(k in {"native", "hardware", "fpga"} for k in backends),
            "software_timing_present": any(k in {"software", "host", "python", "simulator"} for k in backends)}


def audit_rle(data: dict) -> dict:
    if isinstance(data.get("cases"), list):
        out = []
        min_checks = []
        for case in data["cases"]:
            declared = case.get("rectangles", [])
            declared_rects = [r for r in (_rect(x) for x in declared) if r]
            for profile in case.get("profiles", []):
                patches = profile.get("patches", [])
                selected_pixels = profile.get("selected_region_pixels")
                region_pixels = _area_union(declared_rects) if declared_rects else None
                attempts_checked = 0
                attempts_minimum = 0
                for patch in patches:
                    cand = patch.get("attempts", [])
                    if cand:
                        sizes = [int(x["bytes"]) for x in cand if isinstance(x, dict) and isinstance(x.get("bytes"), int)]
                        chosen = patch.get("chosen_bytes")
                        attempts_checked += 1
                        best_hr01 = min(sizes) if sizes else None
                        hp01 = patch.get("hp01_bytes")
                        best_output = min((v for v in (hp01, best_hr01) if isinstance(v, int)), default=None)
                        attempts_minimum += int(best_output is not None and chosen == best_output and
                                                 ((patch.get("chosen_format") == "HP01" and chosen == hp01) or
                                                  (patch.get("chosen_format") == "HR01" and chosen == best_hr01)))
                min_checks.append({"case": case.get("name"), "profile": profile.get("method"),
                                   "patches_with_candidate_bytes": attempts_checked,
                                   "chosen_minimum_byte_candidates": attempts_minimum,
                                   "all_patches_choose_minimum": attempts_checked == attempts_minimum,
                                   "criterion": "chosen output equals min(HP01 bytes, minimum HR01 candidate bytes)"})
                out.append({"case": case.get("name"), "source_kind": case.get("source_kind"),
                            "method": profile.get("method"),
                            "input_class": "synthetic" if str(case.get("source_kind", "")).startswith("synthetic") else "real_source" if str(case.get("source_kind", "")).startswith("real") else "provenance_missing",
                            "region_set": profile.get("region_set"), "method": profile.get("method"),
                            "packet_bytes": profile.get("packet_bytes"), "base_bytes": profile.get("base_bytes"),
                            "cap_bytes": data.get("cap") if isinstance(data.get("cap"), int) else data.get("cap", {}).get("bytes", CAP_BYTES),
                            "cap_ok": not profile.get("over_cap", False), "over_cap": profile.get("over_cap"),
                            "selected_region_pixels": selected_pixels, "declared_region_union_pixels": region_pixels,
                            "roi_coverage_fraction": selected_pixels / region_pixels if selected_pixels is not None and region_pixels else None,
                            "rgb565_word_mismatches": profile.get("rgb565_word_mismatches"),
                            "rgb565_exact_selected_decoder": profile.get("rgb565_word_mismatches") == 0,
                            "packet_sha256": profile.get("packet_sha256"),
                            "display_rgb565_sha256": profile.get("display_rgb565_sha256"),
                            "patch_count": len(patches), "patches": patches,
                            "charged_prepare_sum_ms": profile.get("charged_prepare_sum_ms"),
                            "receive_ms": profile.get("receive_ms"),
                            "all_candidate_service_ms": sum(float(p.get("all_candidate_service_ms", 0)) for p in patches)})
        grouped_summary = {}
        for row in out:
            key = (row["source_kind"], row["region_set"], row["method"])
            grouped_summary.setdefault(key, []).append(row)
        independent_summary = []
        stored_summary = data.get("summary", {})
        for (source_kind, region_set, method), group in sorted(grouped_summary.items()):
            summary_method = "adaptive_row" if method == "adaptive_row" else "hp01"
            stored = stored_summary.get(f"{source_kind}/{region_set}", {}).get(summary_method, {})
            mean_bytes = sum(float(r["packet_bytes"]) for r in group) / len(group) if group else None
            fit_frames = sum(r["cap_ok"] for r in group)
            independent_summary.append({"source_kind": source_kind, "region_set": region_set, "method": method,
                                        "frames": len(group), "mean_packet_bytes": mean_bytes, "fit_frames": fit_frames,
                                        "mean_bytes_matches_stored": stored.get("mean_packet_bytes") is not None and abs(mean_bytes - stored["mean_packet_bytes"]) < 1e-9,
                                        "fit_count_matches_stored": stored.get("fit_frames") == fit_frames,
                                        "mean_charged_prepare_ms": sum(float(r["charged_prepare_sum_ms"] or 0) for r in group)/len(group),
                                        "mean_receive_ms": sum(float(r["receive_ms"] or 0) for r in group)/len(group)})
        return {"row_count": len(out), "rows": out, "profile_count_declared": data.get("profile_records"),
                "real_precompressed_profiles": sum(r["input_class"] == "real_source" for r in out),
                "synthetic_profiles": sum(r["input_class"] == "synthetic" for r in out),
                "all_four_profile_patch_counts_positive_per_case": all(len(c.get("profiles", [])) == 4 and all(p.get("patches") for p in c["profiles"]) for c in data["cases"]),
                "chosen_minimum_checks": min_checks,
                "all_candidate_bytes_choose_minimum": all(c["all_patches_choose_minimum"] for c in min_checks),
                "independently_rederived_summary": independent_summary,
                "all_rederived_means_and_fit_counts_match_stored": all(x["mean_bytes_matches_stored"] and x["fit_count_matches_stored"] for x in independent_summary),
                "summary": data.get("summary"), "cap": data.get("cap"),
                "format_scope": data.get("format_scope"), "timing_scope": data.get("timing_scope"),
                "memory_scope": data.get("memory_scope"), "quality_scope": data.get("quality_scope")}
    rows = _records(data)
    out = []
    for row in rows:
        actual = _first(row, "packet_bytes", "encoded_bytes", "candidate_bytes", "bytes")
        cap = _first(row, "frame_cap_bytes", "packet_cap_bytes") or CAP_BYTES
        out.append({"name": _first(row, "name", "case", "id"),
                    "input_class": classify_input(row), "packet_bytes": actual,
                    "cap_bytes": cap, "cap_ok": actual <= cap if actual is not None else None,
                    "rle_bytes": _first(row, "rle_bytes", "row_rle_bytes", "compressed_bytes"),
                    "raw_bytes": _first(row, "raw_bytes", "rgb565_raw_bytes", "uncompressed_bytes"),
                    "fallback_packet_sha256": _first(row, "fallback_packet_sha256", "gm01_sha256"),
                    "fallback_identity": _first(row, "fallback_identity", "fallback_packet_identity"),
                    "timing_backend": _first(row, "timing_backend", "backend", "measurement_kind"),
                    "timing_scope": _first(row, "timing_scope", "scope")})
    return {"row_count": len(out), "rows": out,
            "all_observed_packets_within_cap": all(r["cap_ok"] is True for r in out if r["packet_bytes"] is not None),
            "native_timing_rows": sum(str(r["timing_backend"]).lower() in {"native", "hardware", "fpga"} for r in out),
            "software_timing_rows": sum(str(r["timing_backend"]).lower() in {"software", "host", "python", "simulator"} for r in out)}


def audit_bundle() -> dict:
    expected = {"selective": ROOT / "experiments/python-game-selective-study/results.json",
                "service": ROOT / "experiments/python-game-service-study/results.json",
                "row_rle": ROOT / "experiments/python-game-row-study/results.json",
                "standard": ROOT / "experiments/python-game-standard-study/results.json",
                "color_floor": ROOT / "experiments/python-game-standard-study/color-floor.json",
                "common_color": ROOT / "experiments/python-game-standard-study/common-color-results.json"}
    data = {key: json.loads(path.read_text()) for key, path in expected.items() if path.is_file()}
    pins = {}
    media_pins = {}
    for value in data.values():
        pins.update(value.get("source_sha256", value.get("source_pins", {})))
        for scene in value.get("scenes", []) + value.get("cases", []):
            manifest = scene.get("manifest", {})
            if manifest.get("source") and manifest.get("source_sha256"):
                media_pins[manifest["source"]] = manifest["source_sha256"]
    before = source_pin_audit(pins)
    media_before = source_pin_audit(media_pins)
    result = {"inputs_missing": [str(path) for k, path in expected.items() if k not in data],
              "source_pins_before": before, "external_media_hash_guard_before": media_before}
    if "selective" in data: result["selective"] = audit_selective(data["selective"])
    if "service" in data: result["service"] = audit_service(data["service"])
    if "row_rle" in data: result["row_rle"] = audit_rle(data["row_rle"])
    if "standard" in data: result["standard_video"] = audit_standard_video(data["standard"])
    if "color_floor" in data: result["color_floor"] = audit_color_floor(data["color_floor"])
    if "common_color" in data:
        result["common_color"] = audit_common_color(data["common_color"], expected["standard"])
    after = source_pin_audit(pins)
    media_after = source_pin_audit(media_pins)
    result["source_pins_after"] = after
    result["external_media_hash_guard_after"] = media_after
    result["source_pins_match_before_and_after"] = before == after and before["all_match"]
    result["external_media_hash_guard_match_before_and_after"] = media_before == media_after and media_before["all_match"]
    result["claims_guard"] = {"whole_frame_cap_proves_roi_coverage": False,
                              "offline_service_proves_complete_live_pipeline": False,
                              "software_timing_is_native_timing": False,
                              "missing_fields_are_evidence_gaps": True}
    result["accounting"] = {"standard_campaign_decoded_rows": result.get("standard_video", {}).get("total_decoded_records", 0),
                            "common_color_new_native_codec_outputs": result.get("common_color", {}).get("new_native_codec_output_records", 0),
                            "common_color_reused_gm_rows_not_new_decodes": result.get("common_color", {}).get("reused_gm_output_records_not_double_counted", 0),
                            "total_unique_codec_output_rows_across_campaigns": result.get("standard_video", {}).get("total_decoded_records", 0) + result.get("common_color", {}).get("new_native_codec_output_records", 0),
                            "separate_color_floor_conversion_rows": sum(len(c.get("records", [])) for c in data.get("color_floor", {}).get("cases", []))}
    result["remaining_gaps"] = ["No target decoder, real transport, scanout, or physical 30 fps presentation was measured.",
                                "Pipeline and service timing use offline host or virtual-stage assumptions; they do not establish a complete live device pipeline."]
    result["evidence_gaps"] = ["result input missing: " + path for path in result["inputs_missing"]]
    if not pins: result["evidence_gaps"].append("declared source pins missing")
    if not media_pins: result["evidence_gaps"].append("external source manifest hashes missing")
    if before["missing"] or before["mismatched"]: result["evidence_gaps"].append("source pin missing or mismatch")
    if media_before["missing"] or media_before["mismatched"]: result["evidence_gaps"].append("external media hash missing or mismatch")
    if "standard_video" not in result: result["evidence_gaps"].append("standard HEVC/AV1 comparison not supplied")
    if "color_floor" not in result: result["evidence_gaps"].append("color conversion floor probe not supplied")
    if "common_color" not in data: result["evidence_gaps"].append("common-color cross-codec comparison not supplied")
    if result.get("common_color", {}).get("prior_original_results_pin_matches") is False:
        result["evidence_gaps"].append("common-color result does not match pinned original standard results")
    return result


if __name__ == "__main__":
    output = audit_bundle()
    output["audit_date"] = "2026-11-03"
    (OUT / "audit.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
