#!/usr/bin/env python3
"""Compact independent audit of v5/v6 Python evidence; does not rerun benchmarks."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def percentile(values: Iterable[float], q: float) -> float:
    """NumPy-compatible linear percentile, independently implemented."""
    vals = sorted(float(x) for x in values)
    if not vals:
        raise ValueError("percentile requires values")
    if not 0 <= q <= 100:
        raise ValueError("q must be in [0, 100]")
    pos = (len(vals) - 1) * q / 100
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def overlap_by_id(primary: list[dict], heldout: list[dict], id_key: str, hash_key: str) -> dict:
    """Compare exact IDs and their content hashes; ID set equivalence is explicit."""
    p = {row[id_key]: row[hash_key] for row in primary}
    h = {row[id_key]: row[hash_key] for row in heldout}
    shared = sorted(set(p) & set(h))
    return {
        "primary_count": len(p), "heldout_count": len(h),
        "shared_ids": shared, "shared_id_count": len(shared),
        "shared_id_hash_mismatches": [i for i in shared if p[i] != h[i]],
        "same_id_sets": set(p) == set(h),
        "same_id_hash_mapping": p == h,
        "same_hash_multisets": sorted(p.values()) == sorted(h.values()),
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins(result: dict, base: Path) -> dict:
    checked, missing, mismatched = [], [], []
    for raw, expected in result.get("source_sha256", {}).items():
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        if not path.is_file():
            missing.append(str(path))
            continue
        actual = digest(path)
        checked.append(str(path))
        if actual != expected:
            mismatched.append({"path": str(path), "expected": expected, "actual": actual})
    return {"checked": checked, "missing": missing, "mismatched": mismatched,
            "all_available_pins_match": not mismatched}


def recompute_result(result: dict) -> list[dict]:
    rows = []
    for scene in result.get("scenes", []):
        records = scene.get("records", [])
        def numeric_leaves(value, prefix=""):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield from numeric_leaves(child, f"{prefix}.{key}" if prefix else key)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                yield prefix, float(value)

        fields = sorted({key for record in records for key, _ in numeric_leaves(record)
                         if any(part.endswith("_ms") for part in key.split("."))})
        groups = [("all", records)]
        if records and "kind" in records[0]:
            groups += [(kind, [r for r in records if r.get("kind") == kind])
                       for kind in sorted({r.get("kind") for r in records})]
        stats = {}
        for label, recs in groups:
            for field in fields:
                vals = []
                for record in recs:
                    vals.extend(value for key, value in numeric_leaves(record) if key == field)
                if vals:
                    stats[f"{label}.{field}"] = {
                        "n": len(vals), "median": statistics.median(vals),
                        "p95_linear": percentile(vals, 95),
                    }
        rows.append({"scene": scene.get("name"), "metrics": stats})
    return rows


def recompute_cases(result: dict) -> list[dict]:
    audited = []
    for case in result.get("cases", []):
        r = case.get("result", {})
        packets = r.get("packets", [])
        groups = {"KEY": [p for p in packets if p.get("key")],
                  "P": [p for p in packets if not p.get("key")]}
        service = {}
        for kind, rows in groups.items():
            for field in ("encode_wall_ms", "decode_wall_ms"):
                values = [p[field] for p in rows if isinstance(p.get(field), (int, float))]
                if values:
                    ordered = sorted(values)
                    field_kind = field.removesuffix("_wall_ms")
                    summary_key = f"{kind.lower()}_{field_kind}_ms"
                    recorded = r.get("service_summary", {}).get(summary_key, {})
                    lower_p50 = ordered[(len(ordered) - 1) // 2]
                    nearest_p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
                    service[f"{kind}.{field}"] = {
                        "n": len(values), "median": statistics.median(values),
                        "p95_linear": percentile(values, 95),
                        "p50_lower_order_statistic": lower_p50,
                        "p95_nearest_rank": nearest_p95,
                        "recorded_summary": recorded,
                        "recorded_p50_p95_match": (recorded.get("p50") == lower_p50 and
                                                    recorded.get("p95") == nearest_p95),
                    }
        manifest = case.get("manifest", {})
        pts = manifest.get("selected_pts", [])
        hashes = manifest.get("frame_sha256", [])
        audited.append({
            "case": case.get("name"),
            "encoder_profile": r.get("config", {}).get("encoder_profile"),
            "decoder_service": r.get("config", {}).get("decoder_service"),
            "source_sha256": manifest.get("source_sha256"),
            "native_pts_count": len(pts), "first_pts": pts[0] if pts else None,
            "last_pts": pts[-1] if pts else None,
            "native_pts": pts,
            "native_pts_rendered_hashes": list(zip(pts, hashes)),
            "distinct_rendered_hashes": len(set(hashes)),
            "repeated_content_frames": len(hashes) - len(set(hashes)),
            "service_from_packet_rows": service,
            "service_summary_as_recorded": r.get("service_summary", {}),
            "presentation_counts": {k: r.get(k) for k in
                                     ("capture_count", "presented_strict", "presented_eventual", "steady_count")},
        })
    return audited


def summarize_values(values: list[float]) -> dict:
    return {"n": len(values), "mean": statistics.mean(values),
            "p50_linear": percentile(values, 50), "p95_linear": percentile(values, 95),
            "max": max(values)} if values else {"n": 0}


def recompute_token_entropy(result: dict, budget_ms: float = 1000 / 30) -> dict:
    key_old, key_new, entropy_old, entropy_new = [], [], [], []
    for case in result.get("cases", []):
        for record in case.get("records", []):
            key_old.append(record["prepare_ms"]["previous"])
            key_new.append(record["prepare_ms"]["token"])
            for plane in record.get("entropy_planes", []):
                entropy_old.append(plane["previous"])
                entropy_new.append(plane["token"])
    return {
        "sample_counts": {"whole_keys": len(key_old), "entropy_planes": len(entropy_old)},
        "whole_key_ms": {"previous": summarize_values(key_old), "token": summarize_values(key_new)},
        "entropy_plane_ms": {"previous": summarize_values(entropy_old), "token": summarize_values(entropy_new)},
        "whole_key_over_budget_count": {
            "budget_ms": budget_ms,
            "previous": sum(value > budget_ms for value in key_old),
            "token": sum(value > budget_ms for value in key_new),
        },
    }


def compare_case_ids_and_quality(result: dict) -> list[dict]:
    cases = result.get("cases", [])
    comparisons = []
    pairs = []
    for left_index, left in enumerate(cases):
        for right in cases[left_index + 1:]:
            lr, rr = left.get("result", {}), right.get("result", {})
            if (left.get("name") == right.get("name") and
                    lr.get("config", {}).get("decoder_service") == rr.get("config", {}).get("decoder_service") and
                    lr.get("config", {}).get("encoder_profile") != rr.get("config", {}).get("encoder_profile")):
                pairs.append((left, right))
    for left, right in pairs:
        lr, rr = left["result"], right["result"]
        lm, rm = left.get("manifest", {}), right.get("manifest", {})
        left_presented = {row["id"] for row in lr.get("presented", [])}
        right_presented = {row["id"] for row in rr.get("presented", [])}
        common = left_presented & right_presented
        left_start_end = {row["id"] for row in lr.get("presented", [])
                          if row.get("at_ms", float("inf")) < lr.get("capture_window_ms", [0, 0])[1] - 1e-9}
        right_start_end = {row["id"] for row in rr.get("presented", [])
                           if row.get("at_ms", float("inf")) < rr.get("capture_window_ms", [0, 0])[1] - 1e-9}
        lwindow, rwindow = lr.get("steady_window_ms"), rr.get("steady_window_ms")
        left_steady = {row["id"] for row in lr.get("presented", []) if lwindow and
                       lwindow[0] <= row.get("at_ms", float("inf")) < lwindow[1]}
        right_steady = {row["id"] for row in rr.get("presented", []) if rwindow and
                        rwindow[0] <= row.get("at_ms", float("inf")) < rwindow[1]}
        lq = {row["id"]: row.get("active_rgb565_mse") for row in lr.get("commits", [])}
        rq = {row["id"]: row.get("active_rgb565_mse") for row in rr.get("commits", [])}
        qids = sorted(i for i in common if i in lq and i in rq and
                      isinstance(lq[i], (int, float)) and isinstance(rq[i], (int, float)))
        deltas = [rq[i] - lq[i] for i in qids]
        lpts, rpts = lm.get("selected_pts", []), rm.get("selected_pts", [])
        lhash, rhash = lm.get("frame_sha256", []), rm.get("frame_sha256", [])
        same_source_sequence = (lm.get("source_sha256") == rm.get("source_sha256") and
                                lpts == rpts and lhash == rhash)
        comparisons.append({
            "clip": left.get("name"),
            "decoder_service": lr.get("config", {}).get("decoder_service"),
            "left_profile": lr.get("config", {}).get("encoder_profile"),
            "right_profile": rr.get("config", {}).get("encoder_profile"),
            "left_presented_before_capture_window_end_count": lr.get("presented_strict"),
            "right_presented_before_capture_window_end_count": rr.get("presented_strict"),
            "left_presented_before_capture_window_end_ids": sorted(left_start_end),
            "right_presented_before_capture_window_end_ids": sorted(right_start_end),
            "left_diagnostic_steady_window_ids": sorted(left_steady),
            "right_diagnostic_steady_window_ids": sorted(right_steady),
            "left_eventual_ids": sorted(left_presented),
            "right_eventual_ids": sorted(right_presented),
            "common_eventual_id_count": len(common),
            "same_source_sequence_at_capture_ids": same_source_sequence,
            "left_presented_native_pts": [lpts[i] for i in sorted(left_presented) if i < len(lpts)],
            "right_presented_native_pts": [rpts[i] for i in sorted(right_presented) if i < len(rpts)],
            "common_quality_id_count": len(qids),
            "common_id_active_mse_delta_right_minus_left_mean": statistics.mean(deltas) if deltas else None,
            "common_id_active_mse_delta_right_minus_left_max_abs": max((abs(x) for x in deltas), default=None),
            "diagnostic_window": {"kind": "[start,end)" if lwindow else None, "ms": lwindow,
                                  "left_count": lr.get("steady_count"),
                                  "right_count": rr.get("steady_count")},
        })
    return comparisons


def cohort_audit(path: Path) -> dict:
    data = json.loads(path.read_text())
    pins = data.get("pinned_versions", {})
    pinned_files = {
        "experiments/python-cohort-study/audit.py": pins.get("audit_source_sha256"),
        "experiments/python-codec-study/corpus.py": pins.get("corpus_helper_sha256"),
    }
    pin_audit = []
    for rel, expected in pinned_files.items():
        file = ROOT / rel
        actual = digest(file) if file.is_file() else None
        pin_audit.append({"path": rel, "expected": expected, "actual": actual,
                          "matches": expected is not None and actual == expected})
    windows = data.get("windows", [])
    concise = []
    for w in windows:
        pts = w.get("selected_pts", [])
        hashes = w.get("image_sha256", [])
        concise.append({"clip": w.get("clip"), "role": w.get("role"),
                        "native_pts_count": len(pts), "first_pts": pts[0] if pts else None,
                        "last_pts": pts[-1] if pts else None,
                        "distinct_rendered_hashes": len(set(hashes)),
                        "repeated_content_frames": len(hashes) - len(set(hashes))})
    return {"pinned_source_hashes": pin_audit, "windows": concise,
            "overlap_analysis": data.get("overlap_analysis", [])}


def source_inputs(result: dict) -> list[Path]:
    paths = set()
    for scene in result.get("scenes", []):
        src = scene.get("manifest", {}).get("source")
        if src:
            paths.add(Path(src))
    for case in result.get("cases", []):
        src = case.get("manifest", {}).get("source")
        if src:
            paths.add(Path(src))
    return sorted(paths)


def source_manifest_pins(result: dict) -> list[dict]:
    pins = []
    entries = list(result.get("scenes", [])) + list(result.get("cases", []))
    for entry in entries:
        manifest = entry.get("manifest", {})
        raw = manifest.get("source")
        expected = manifest.get("source_sha256")
        if not raw or not expected:
            continue
        path = Path(raw)
        actual = digest(path) if path.is_file() else None
        pins.append({"path": str(path), "expected": expected, "actual": actual,
                     "matches": actual is not None and actual == expected})
    return pins


def main() -> None:
    result_paths = [ROOT / "experiments/python-fast-entropy-study/results.json",
                    ROOT / "experiments/python-fast-entropy-study/anchor-results.json"]
    for dirname in ("python-key-prepare-study", "python-measured-service-study", "python-arithmetic-study", "python-token-entropy-study"):
        result_paths += sorted((ROOT / "experiments" / dirname).glob("*.json"))
    result_paths += sorted((ROOT / "experiments").glob("python-*-v6-study/*.json"))
    results = {}
    pin_before = {}
    for path in result_paths:
        if path.name in {"audit.json", "test-results.json"}:
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or not ("scenes" in data or "cases" in data):
            continue
        results[str(path.relative_to(ROOT))] = data
        pin_before[str(path)] = verify_pins(data, ROOT)
    cohort = ROOT / "experiments/python-cohort-study/audit.json"
    payload = {
        "scope": "Read-only audit of stored JSON; no benchmark reruns. Percentiles use linear interpolation as in NumPy.",
        "result_files": {},
        "cohort": cohort_audit(cohort),
        "source_hashes_before": {},
        "source_hashes_after": {},
    }
    for rel, data in results.items():
        payload["result_files"][rel] = {
            "evidence": data.get("evidence"),
            "source_pin_audit": pin_before[str(ROOT / rel)],
            "source_manifest_hash_audit": source_manifest_pins(data),
            "recomputed_metrics": recompute_result(data),
            "recomputed_cases": recompute_cases(data),
            "same_source_case_comparisons": compare_case_ids_and_quality(data),
        }
        if "whole_key_over_33_333_ms" in data.get("summary", {}):
            payload["result_files"][rel]["recomputed_token_entropy"] = recompute_token_entropy(data)
    all_sources = set()
    for data in results.values():
        all_sources.update(source_inputs(data))
    for source in sorted(all_sources):
        if source.is_file():
            payload["source_hashes_before"][str(source)] = digest(source)
    for source in sorted(all_sources):
        if source.is_file():
            payload["source_hashes_after"][str(source)] = digest(source)
    payload["source_inputs_unchanged_during_audit"] = payload["source_hashes_before"] == payload["source_hashes_after"]
    for rel, data in results.items():
        payload["result_files"][rel]["source_pin_audit_after"] = verify_pins(data, ROOT)
        payload["result_files"][rel]["source_manifest_hash_audit_after"] = source_manifest_pins(data)
        before = payload["result_files"][rel]
        payload["result_files"][rel]["all_declared_source_pins_stable"] = (
            before["source_pin_audit"]["all_available_pins_match"] and
            before["source_pin_audit_after"]["all_available_pins_match"] and
            all(p["matches"] for p in before["source_manifest_hash_audit"]) and
            all(p["matches"] for p in before["source_manifest_hash_audit_after"]))
    (OUT / "audit.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"audited {len(results)} result JSON files; source inputs unchanged={payload['source_inputs_unchanged_during_audit']}")


if __name__ == "__main__":
    main()
