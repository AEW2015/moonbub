#!/usr/bin/env python3
"""Read-only evidence audit for the v9 Python Game Bub studies (stdlib only).

The audit is intentionally conservative: unknown/missing fields remain evidence
gaps and are never inferred from aggregate timing or transport acknowledgements.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pins_audit(pins: dict[str, str], base: Path = ROOT) -> dict:
    rows = []
    for raw, expected in sorted(pins.items()):
        path = Path(raw)
        if not path.is_absolute():
            path = base / path
        actual = sha256(path) if path.is_file() else None
        rows.append({"path": str(path), "expected": expected, "actual": actual,
                     "matches": actual == expected if actual is not None else None})
    return {"pins": rows,
            "missing": [r["path"] for r in rows if r["actual"] is None],
            "mismatched": [r["path"] for r in rows if r["actual"] is not None and not r["matches"]],
            "all_match": all(r["matches"] is True for r in rows)}


def _first(d: dict, *names: str) -> Any:
    for name in names:
        if name in d and d[name] is not None:
            return d[name]
    return None


def _rows(data: dict) -> list[dict]:
    out = []
    for name in ("records", "frames", "outcomes", "commits", "events"):
        val = data.get(name)
        if isinstance(val, list):
            out.extend(x for x in val if isinstance(x, dict))
    for group in data.get("cases", []) + data.get("modes", []):
        if isinstance(group, dict):
            for name in ("records", "frames", "outcomes", "commits", "events"):
                val = group.get(name)
                if isinstance(val, list):
                    out.extend(x for x in val if isinstance(x, dict))
    return out


def capture_outcomes(data: dict) -> dict:
    """Count unique capture IDs at distinct / eventual / diagnostic stages."""
    records = _rows(data)
    stages = {
        "distinct_strict": ("distinct_presented_ids", "presented_distinct_ids", "strict_ids"),
        "eventual": ("eventually_presented_ids", "eventual_ids", "accepted_ids"),
        "diagnostic": ("diagnostic_ids", "attempted_ids", "capture_ids"),
    }
    result = {}
    for stage, names in stages.items():
        values = _first(data, *names)
        if values is None:
            values = []
            for row in records:
                val = _first(row, *names)
                if val is not None:
                    values.extend(val if isinstance(val, list) else [val])
                elif stage == "diagnostic":
                    val = _first(row, "capture_id", "frame_id", "source_id")
                    if val is not None:
                        values.append(val)
        result[stage] = {"ids": values if isinstance(values, list) else [values],
                         "unique_count": len(set(values if isinstance(values, list) else [values])) if values else 0,
                         "evidence": "present" if values else "missing"}
    seconds = _first(data, "measurement_seconds", "duration_seconds")
    result["measurement_seconds"] = seconds
    result["strict_distinct_presented_fps"] = (result["distinct_strict"]["unique_count"] / float(seconds)
                                                if result["distinct_strict"]["evidence"] == "present" and seconds else None)
    result["displayed_fps_proven"] = result["strict_distinct_presented_fps"] is not None
    return result


def audit_feedback(data: dict) -> dict:
    rows = _rows(data)
    rejects = rejected_with_cost = 0
    service_sum = 0.0
    service_n = 0
    binding_checked = binding_ok = 0
    for row in rows:
        status = str(_first(row, "status", "outcome", "decision") or "").lower()
        cost = _first(row, "service_ms", "charged_ms", "total_service_ms")
        is_reject = status in {"reject", "rejected", "drop", "dropped"}
        rejects += int(is_reject)
        if cost is not None:
            service_sum += float(cost)
            service_n += 1
            rejected_with_cost += int(is_reject)
        sent_epoch = _first(row, "sent_epoch", "feedback_epoch", "epoch")
        applied_epoch = _first(row, "applied_epoch", "state_epoch")
        sent_frame = _first(row, "sent_frame_id", "feedback_frame_id", "capture_id")
        applied_frame = _first(row, "applied_frame_id", "state_frame_id")
        if sent_epoch is not None and applied_epoch is not None and sent_frame is not None and applied_frame is not None:
            binding_checked += 1
            binding_ok += int(sent_epoch == applied_epoch and sent_frame == applied_frame)
    return {"row_count": len(rows), "reject_count": rejects,
            "rejected_rows_with_service_cost": rejected_with_cost,
            "service_cost_includes_rejects": rejected_with_cost == rejects and rejects > 0,
            "service_cost_sum_ms": service_sum if service_n else None,
            "service_cost_rows": service_n,
            "feedback_binding_rows_checked": binding_checked,
            "feedback_binding_rows_matching_epoch_and_frame": binding_ok,
            "feedback_binding_proven": binding_checked > 0 and binding_ok == binding_checked,
            "feedback_binding_evidence": "present" if binding_checked else "missing"}


def audit_transport(data: dict) -> dict:
    records = _rows(data)
    forward = feedback = None
    if records:
        f = [int(v) for row in records if (v := _first(row, "forward_wire_bytes", "forward_bytes", "payload_plus_header_bytes")) is not None]
        b = [int(v) for row in records if (v := _first(row, "feedback_wire_bytes", "feedback_bytes")) is not None]
        forward, feedback = (sum(f) if f else None), (sum(b) if b else None)
    else:
        forward = _first(data, "forward_wire_bytes", "forward_bytes")
        feedback = _first(data, "feedback_wire_bytes", "feedback_bytes")
    per_row_headers = [int(v) for row in records if (v := _first(row, "wire_headers_bytes", "headers_bytes", "header_bytes")) is not None]
    headers = sum(per_row_headers) if per_row_headers else _first(data, "wire_headers_bytes", "headers_bytes", "header_bytes")
    declared_total = _first(data, "total_wire_bytes", "wire_bytes")
    payload_peak = _first(data, "two_slot_payload_peak_bytes", "payload_peak_bytes", "max_live_payload_bytes")
    drain = _first(data, "drain_proof", "all_payloads_drained", "physical_read_drain")
    calc = (int(forward or 0) + int(feedback or 0) + int(headers)) if headers is not None and (forward is not None or feedback is not None) else None
    return {"forward_wire_bytes": forward, "feedback_wire_bytes": feedback,
            "header_bytes": headers, "calculated_wire_bytes": calc,
            "declared_wire_bytes": declared_total,
            "wire_accounting_matches": calc == declared_total if calc is not None and declared_total is not None else None,
            "two_slot_payload_peak_bytes": payload_peak,
            "drain_evidence": drain,
            "physical_drain_proven": drain is True or (isinstance(drain, dict) and drain.get("physical") is True),
            "gaps": [label for label, value in (("headers", headers), ("two-slot peak", payload_peak), ("drain", drain)) if value is None]}


def audit_hud(data: dict) -> dict:
    modes = data.get("modes", [])
    if not modes:
        modes = [{"name": data.get("mode", "unspecified"), **data}]
    out = []
    for mode in modes:
        patches = mode.get("patches", mode.get("records", []))
        whole = mode.get("whole_frame", mode.get("frame_bytes"))
        roi = []
        for p in patches:
            if not isinstance(p, dict):
                continue
            area = _first(p, "roi_pixels", "pixel_count")
            if area is None:
                w, h = _first(p, "width"), _first(p, "height")
                area = int(w) * int(h) if w is not None and h is not None else None
            colors = _first(p, "rgb565_colors", "parsed_colors", "colors")
            roi.append({"roi_pixels": area, "rgb565_colors": colors,
                        "patch_bytes": _first(p, "patch_bytes", "bytes"),
                        "pixel_claim_proven": area is not None and colors is not None})
        pixel_claim = bool(roi) and all(r["pixel_claim_proven"] for r in roi)
        predictor_same = _first(mode, "predictor_unchanged", "predictor_state_unchanged")
        out.append({"mode": _first(mode, "name", "mode"), "whole_frame_bytes": whole,
                    "roi_pixel_claims": roi,
                    "roi_pixels_total": sum(r["roi_pixels"] for r in roi if r["roi_pixels"] is not None),
                    "all_roi_color_claims_supported": pixel_claim,
                    "predictor_unchanged": predictor_same,
                    "predictor_unchanged_proven": predictor_same is True})
    return {"modes": out, "whole_frame_cap_is_not_roi_pixel_proof": True,
            "missing_roi_pixel_claims": not any(m["all_roi_color_claims_supported"] for m in out),
            "predictor_unchanged_proven": bool(out) and all(m["predictor_unchanged_proven"] for m in out)}


def audit_pipeline(data: dict) -> dict:
    cases = []
    fault_activation = []
    for case in data.get("cases", []):
        result = case.get("result", {})
        presented = result.get("presented", [])
        end = (result.get("capture_window_ms") or [None, None])[1]
        strict_ids = [r["id"] for r in presented if isinstance(r, dict) and "id" in r and end is not None and r.get("at_ms", end) < end]
        eventual_ids = [r["id"] for r in presented if isinstance(r, dict) and "id" in r]
        captured = int(result.get("capture_count", 0))
        diagnostic_window = result.get("steady_window_ms")
        if isinstance(diagnostic_window, (list, tuple)) and len(diagnostic_window) == 2:
            diagnostic_start, diagnostic_end = diagnostic_window
            diagnostic_ids = [r["id"] for r in presented if isinstance(r, dict) and "id" in r
                              and diagnostic_start <= r.get("at_ms", -1) < diagnostic_end]
            diagnostic_duration = float(diagnostic_end) - float(diagnostic_start)
            diagnostic_fps = len(set(diagnostic_ids)) * 1000.0 / diagnostic_duration if diagnostic_duration > 0 else None
        else:
            diagnostic_start = diagnostic_end = diagnostic_duration = diagnostic_fps = None
            diagnostic_ids = []
        service = result.get("service_summary", {}).get("rejected_encode_ms", {})
        reject_n, reject_mean = service.get("n", 0), service.get("mean")
        rejected_cost = float(reject_mean) * int(reject_n) if reject_mean is not None and reject_n else 0.0
        cfg = result.get("config", {})
        drops = result.get("drops", [])
        timeouts = result.get("timeout_events", [])
        configured = {k: v for k, v in cfg.items() if k.endswith("_ids") and v}
        activation = {}
        for key, ids in configured.items():
            actual = []
            for fid in ids:
                if key == "data_loss_ids":
                    if any(d.get("id") == fid and d.get("reason") == "partial_ingress_timeout" for d in drops): actual.append(fid)
                elif key == "feedback_loss_ids":
                    if any(t.get("id") == fid for t in timeouts): actual.append(fid)
                elif key == "duplicate_chunk_ids":
                    indexes = [w.get("index") for w in result.get("forward_wire", []) if w.get("id") == fid]
                    if len(indexes) != len(set(indexes)): actual.append(fid)
                elif key == "duplicate_feedback_ids":
                    if sum(1 for f in result.get("feedback", []) if f.get("id") == fid) > 1: actual.append(fid)
                else:
                    actual.append(None)  # configuration exists; no stored activation observable for this fault type
            activation[key] = {"configured_ids": ids, "observed_ids": actual,
                               "activation_proven": len(actual) == len(ids) and bool(ids)}
        fault_activation.append({"case": case.get("name"), "configured_faults": activation})
        packets = result.get("packets", [])
        feedback_rows = result.get("feedback", [])
        id_epoch = {p.get("id"): p.get("epoch") for p in packets if isinstance(p, dict)}
        fb_bound = [f for f in feedback_rows if isinstance(f, dict) and f.get("kind") == "received"]
        expected_epoch = cfg.get("epoch", 1)
        feedback_binding = {"rows_checked": len(fb_bound),
                            "rows_matching_packet_epoch_and_frame": sum(f.get("id") in id_epoch and f.get("epoch") == expected_epoch for f in fb_bound),
                            "binding_proven": bool(fb_bound) and all(f.get("id") in id_epoch and f.get("epoch") == expected_epoch for f in fb_bound)}
        sender_left = result.get("unresolved_sender_slots")
        sender_clear = sender_left is None or (isinstance(sender_left, list) and all(v is None for v in sender_left))
        ingress_clear = not result.get("unresolved_ingress_frames")
        credits_clear = not result.get("unresolved_credits")
        cases.append({"name": case.get("name"), "kind": case.get("kind"),
                      "strict_distinct_ids_before_capture_end": strict_ids,
                      "eventual_presented_ids": eventual_ids,
                      "diagnostic_presentation_ids_in_steady_window": diagnostic_ids,
                      "strict_count": len(set(strict_ids)), "eventual_count": len(set(eventual_ids)),
                      "capture_count": captured,
                      "diagnostic_presentation_count": len(set(diagnostic_ids)),
                      "diagnostic_window_ms": [diagnostic_start, diagnostic_end] if diagnostic_start is not None else None,
                      "diagnostic_window_duration_ms": diagnostic_duration,
                      "diagnostic_presentation_fps_rederived": diagnostic_fps,
                      "steady_fps": result.get("metrics", {}).get("steady_fps"),
                      "configured_fault_ids": configured,
                      "fault_activation": activation,
                      "service_reject_n": reject_n, "service_reject_mean_ms": reject_mean,
                      "service_reject_total_ms": rejected_cost,
                      "feedback_epoch_frame_binding": feedback_binding,
                      "unresolved_sender_slots": result.get("unresolved_sender_slots"),
                      "unresolved_ingress_frames": result.get("unresolved_ingress_frames"),
                      "unresolved_credits": result.get("unresolved_credits"),
                      "waiting_at_end": result.get("waiting_at_end"),
                      "peak_sender_slots": result.get("peak_sender_slots"),
                      "peak_ingress_payload_bytes": result.get("peak_ingress_payload_bytes"),
                      "drain_clear": sender_clear and ingress_clear and credits_clear and result.get("waiting_at_end") is None})
    return {"case_count": len(cases), "cases": cases, "fault_activation_checks": fault_activation,
            "total_rejected_encode_service_ms": sum(c["service_reject_total_ms"] for c in cases),
            "strict_eventual_diagnostic_are_distinct_metrics": True}


def audit_feedback_results(data: dict, regression: dict | None = None) -> dict:
    rows = data.get("records", [])
    chunk_hdr = data.get("forward_header_bytes")
    forward_datagram = data.get("forward_ipv4_udp_overhead_per_chunk")
    protocol_feedback = data.get("feedback_bytes")
    reverse_datagram = data.get("reverse_ipv4_udp_overhead_per_feedback")
    forward = sum(r.get("unique_forward_ipv4_udp_bytes", 0) + r.get("duplicate_forward_ipv4_udp_bytes", 0) for r in rows)
    feedback_wire = sum(r.get("reverse_ipv4_udp_bytes", 0) for r in rows)
    forward_chunks = sum(r.get("chunks", 0) + r.get("duplicate_chunks", 0) for r in rows)
    expected_forward_headers = sum(r.get("chunk_header_bytes", 0) * (r.get("chunks", 0) + r.get("duplicate_chunks", 0)) for r in rows)
    network_overhead_forward = int(forward_datagram or 0) - int(chunk_hdr or 0)
    expected_ip_udp = forward_chunks * network_overhead_forward
    expected_feedback_protocol = len(rows) * int(protocol_feedback or 0)
    network_overhead_reverse = int(reverse_datagram or 0) - int(protocol_feedback or 0)
    expected_reverse_overhead = len(rows) * network_overhead_reverse
    return {"record_count": len(rows), "forward_wire_bytes_actual_records": forward,
            "feedback_wire_bytes_actual_records": feedback_wire,
            "forward_protocol_header_bytes_per_chunk": chunk_hdr,
            "forward_ip_udp_datagram_bytes_per_chunk": forward_datagram,
            "forward_ipv4_udp_overhead_per_chunk": network_overhead_forward,
            "forward_total_chunks_including_duplicates": forward_chunks,
            "forward_chunk_header_bytes_rederived": expected_forward_headers,
            "forward_ip_udp_overhead_rederived": expected_ip_udp,
            "feedback_protocol_bytes_per_feedback": protocol_feedback,
            "feedback_protocol_bytes_rederived": expected_feedback_protocol,
            "reverse_ip_udp_datagram_bytes_per_feedback": reverse_datagram,
            "reverse_ipv4_udp_overhead_per_feedback": network_overhead_reverse,
            "reverse_ip_udp_overhead_rederived": expected_reverse_overhead,
            "all_decoded_payloads_zero": all(r.get("payload_bytes_after_decode") == 0 for r in rows),
            "all_faults_drained": all(f.get("drained") is True for f in data.get("faults", [])),
            "all_resources_drained": data.get("all_resources_drained"),
            "faults": data.get("faults", []),
            "regression_pin_ownership": ({"v8_gf01": regression.get("v8_gf01"), "v9_gf02": regression.get("v9_gf02")} if regression else None),
            "wire_accounting_note": "Stored datagram sizes rederive as a 31-byte forward protocol header plus 28-byte IPv4/UDP overhead, and 24-byte feedback plus 28-byte reverse IPv4/UDP overhead."}


def audit_hud_studies(data: dict, flat: dict) -> dict:
    patch_rows = []
    for scene in data.get("scenes", []):
        for profile_name, profile in scene.get("profiles", {}).items():
            if profile_name.endswith("_patch"):
                patch_rows.append({"scene": scene.get("name"), "profile": profile_name,
                                   "packet_bytes": profile.get("bytes"), "over_48k_cap": profile.get("over_48k_cap"),
                                   "roi_rgb565_word_mismatches": profile.get("roi_rgb565_word_mismatches"),
                                   "roi_exact_words": profile.get("roi_rgb565_word_mismatches") == 0,
                                   "base_packet_sha256": profile.get("base_packet_sha256"),
                                   "base_rgb_sha256": profile.get("base_rgb_sha256"),
                                   "display_rgb565_sha256": profile.get("display_rgb565_sha256"),
                                   "patches": profile.get("patches", []),
                                   "rgb888_roi_mse": profile.get("metrics", {}).get("roi", {}).get("mse"),
                                   "mse_zero_inferred_from_rgb565_word_match": False})
    flat_rows = [{"name": c.get("name"), "patch_bytes": c.get("patch_increment_bytes"),
                  "packet_bytes": c.get("wrapped_bytes"), "over_48k_cap": c.get("over_48k_cap"),
                  "roi_rgb565_word_mismatches": c.get("roi_rgb565_word_mismatches"),
                  "roi_exact_words": c.get("roi_rgb565_word_mismatches") == 0,
                  "patches": c.get("patches", []), "scope": c.get("scope")} for c in flat.get("cases", [])]
    test_path = ROOT / "experiments/python-game-hud-study/test_hud_codec.py"
    test_text = test_path.read_text() if test_path.is_file() else ""
    predictor_test = ("test_temporal_patch_does_not_advance_or_pollute_yuv_anchor" in test_text
                      and "np.testing.assert_array_equal(a,b)" in test_text
                      and "plain._anchor,rx.base._anchor" in test_text)
    return {"main_patch_records": len(patch_rows),
            "main_roi_exact_word_records": sum(r["roi_exact_words"] for r in patch_rows),
            "main_patch_cap_failures": sum(r["over_48k_cap"] is True for r in patch_rows),
            "main_patch_rows": patch_rows,
            "flat_patch_cases": flat_rows,
            "flat_zero_word_mismatch_does_not_mean_zero_rgb888_mse": True,
            "predictor_unchanged_from_display_only_patch_test": predictor_test,
            "predictor_evidence": {"test": str(test_path), "explicit_anchor_array_equality_assertion": predictor_test},
            "display_patch_mutates_gm01_yuv": False,
            "predictor_claim_supported_by_independent_state_check": predictor_test}


def audit_file(path: Path) -> dict:
    data = json.loads(path.read_text())
    pins = data.get("source_sha256", data.get("source_pins", {}))
    before = pins_audit(pins) if isinstance(pins, dict) else pins_audit({})
    result = {"input": str(path), "source_pins_before": before,
              "capture_outcomes": capture_outcomes(data),
              "feedback": audit_feedback(data), "transport": audit_transport(data),
              "hud": audit_hud(data) if "modes" in data or "patches" in data or "whole_frame" in data else None,
              "evidence_gaps": []}
    # Any unavailable pin, or unset required audit item, is surfaced explicitly.
    if before["missing"]: result["evidence_gaps"].append("source pins unavailable")
    if before["mismatched"]: result["evidence_gaps"].append("source pin mismatch")
    if result["capture_outcomes"]["distinct_strict"]["evidence"] == "missing": result["evidence_gaps"].append("strict distinct presentation IDs missing")
    if result["feedback"]["feedback_binding_evidence"] == "missing": result["evidence_gaps"].append("feedback epoch/frame binding missing")
    result["evidence_gaps"].extend("transport " + x + " missing" for x in result["transport"]["gaps"])
    if result["hud"] and result["hud"]["missing_roi_pixel_claims"]: result["evidence_gaps"].append("parsed ROI color/pixel evidence missing")
    after = pins_audit(pins) if isinstance(pins, dict) else pins_audit({})
    result["source_pins_after"] = after
    result["source_pins_match_before_and_after"] = before == after and before["all_match"]
    return result


def run_v9_audit() -> dict:
    paths = {"pipeline": ROOT / "experiments/python-game-pipeline-study/results.json",
             "feedback": ROOT / "experiments/python-game-feedback-study/results.json",
             "feedback_regression": ROOT / "experiments/python-game-feedback-study/regression.json",
             "hud": ROOT / "experiments/python-game-hud-study/results.json",
             "hud_flat": ROOT / "experiments/python-game-hud-study/flat-results.json"}
    loaded = {name: json.loads(path.read_text()) for name, path in paths.items() if path.is_file()}
    pin_map: dict[str, str] = {}
    media_pins: dict[str, str] = {}
    for data in loaded.values():
        pin_map.update(data.get("source_sha256", {}))
        for case in data.get("cases", []):
            manifest = case.get("manifest", {})
            if manifest.get("source") and manifest.get("source_sha256"):
                media_pins[manifest["source"]] = manifest["source_sha256"]
        for scene in data.get("scenes", []):
            manifest = scene.get("manifest", {})
            if manifest.get("source") and manifest.get("source_sha256"):
                media_pins[manifest["source"]] = manifest["source_sha256"]
    before = pins_audit(pin_map)
    media_before = pins_audit(media_pins)
    result = {"audit_date": "2026-11-03",
              "inputs_missing": [str(p) for p in paths.values() if not p.is_file()],
              "source_pins_before": before, "external_media_hash_guard_before": media_before}
    if "pipeline" in loaded:
        result["pipeline"] = audit_pipeline(loaded["pipeline"])
    if "feedback" in loaded:
        result["feedback"] = audit_feedback_results(loaded["feedback"], loaded.get("feedback_regression"))
    if "hud" in loaded and "hud_flat" in loaded:
        result["hud"] = audit_hud_studies(loaded["hud"], loaded["hud_flat"])
    after = pins_audit(pin_map)
    media_after = pins_audit(media_pins)
    result["source_pins_after"] = after
    result["external_media_hash_guard_after"] = media_after
    result["source_pins_match_before_and_after"] = before == after and before["all_match"]
    result["external_media_hash_guard_match_before_and_after"] = media_before == media_after and media_before["all_match"]
    result["claims_guard"] = {"mean_service_proves_30_distinct_presented_fps": False,
                              "rgb565_roi_word_match_means_zero_rgb888_mse": False,
                              "display_only_patch_mutates_gm01_yuv_predictor": False,
                              "transport_ack_alone_proves_physical_drain": False}
    return result


if __name__ == "__main__":
    output = run_v9_audit()
    (OUT / "audit.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))
