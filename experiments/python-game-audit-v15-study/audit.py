#!/usr/bin/env python3
"""Stdlib-only v15 evidence audit. Reads artifacts; never runs study workloads."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORKSPACE = ROOT.parents[1]
AUDIT_PATH = HERE / "audit.json"


def portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        try:
            return "external:" + path.resolve().relative_to(WORKSPACE.resolve()).as_posix()
        except ValueError:
            return "external:" + path.name


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _test_log_summary(path: Path):
    if not path.is_file():
        return {"status": "missing"}
    text = path.read_text(errors="replace")
    import re
    passed = re.search(r"Ran (\d+) tests?", text)
    failed = re.search(r"FAILED \(([^)]*)\)", text)
    ok = "OK" in text and failed is None
    return {"status": "pass" if ok else "invalid", "passed_count": int(passed.group(1)) if passed else None}


CAP = 49152

def analyze_codec():
    rel = Path("experiments/python-game-unified-codec-study/results.json")
    result_path = ROOT / rel
    if not result_path.is_file():
        return {"status": "pending", "path": rel.as_posix()}
    data = json.loads(result_path.read_text())
    errors = []
    rows = accepted = over_cap = frame_size_mismatch = paid_rejections = rejected_not_over_cap = wrapper_size_mismatch = 0
    analyze_counts, forward_counts = {}, {}
    profile_ids, profile_hashes = [], []
    exact_bound_bad = prune_bound_bad = protected_bad = selected_bad = 0
    bytes_by_case = {}
    for scene in data.get("scenes", []):
        by_profile = {}
        for name, entries in scene.get("profiles", {}).items():
            by_profile[name] = {r["id"]: r["input_sha256"] for r in entries}
            ids = set(by_profile[name])
            profile_ids.append((scene["name"], name, ids))
            profile_hashes.append((scene["name"], name, by_profile[name]))
            case = bytes_by_case.setdefault(scene["name"], {})
            s = scene.get("summary", {}).get(name, {})
            case[name] = {"mean_packet_bytes": s.get("mean_packet_bytes"),
                          "admitted": s.get("admitted"), "rejected": s.get("rejected"),
                          "mean_prepare_ms_all": s.get("mean_prepare_ms_all"),
                          "mean_receive_ms": s.get("mean_receive_ms"),
                          "mean_exact_source_pixels": s.get("mean_exact_source_pixels"),
                          "active_rgb565_mse": s.get("active_rgb565_mse"),
                          "rejected_work_ms": s.get("rejected_work_ms")}
            for r in entries:
                rows += 1
                info = r.get("info", {})
                accepted_flag = bool(r.get("accepted"))
                accepted += int(accepted_flag)
                analyze_counts[r.get("actual_analyze_calls")] = analyze_counts.get(r.get("actual_analyze_calls"), 0) + 1
                forward_counts[r.get("actual_forward_calls")] = forward_counts.get(r.get("actual_forward_calls"), 0) + 1
                if accepted_flag:
                    over_cap += int(r.get("packet_bytes", CAP + 1) > CAP)
                    frame_size_mismatch += int(r.get("packet_bytes") != info.get("bytes"))
                    wrapper_size_mismatch += int(info.get("bytes") != info.get("inner_bytes", 0) + info.get("envelope_bytes", 0) + info.get("patch_bytes", 0))
                else:
                    paid_rejections += int(r.get("prepare_ms", 0) > 0 and info.get("cap_fit") is False)
                    rejected_not_over_cap += int(info.get("bytes", 0) <= CAP)
                delta = r.get("max_yuv_delta_same_reference_gm", 0) or 0
                if name.startswith("exact"):
                    exact_bound_bad += int(delta != 0)
                if name.startswith("prune4"):
                    prune_bound_bad += int(delta > 4)
                protected_bad += int((r.get("protected_gm_rgb565_mismatches", 0) or 0) != 0)
                selected_bad += int((r.get("selected_source_rgb565_mismatches", 0) or 0) != 0)
        if by_profile:
            base = next(iter(by_profile.values()))
            if any(v != base for v in by_profile.values()):
                errors.append(f"profile frame ID or input hash mismatch: {scene['name']}")
    if rows != data.get("decisions") or rows != 1020:
        errors.append(f"decision rows mismatch: {rows}")
    if accepted != 1002:
        errors.append(f"admission count mismatch: {accepted}")
    if over_cap or frame_size_mismatch:
        errors.append(f"accepted complete-frame cap/size failures: {over_cap}/{frame_size_mismatch}")
    if wrapper_size_mismatch:
        errors.append(f"{wrapper_size_mismatch} full-frame sizes do not equal inner plus envelope plus UI patch bytes")
    if rejected_not_over_cap:
        errors.append(f"{rejected_not_over_cap} cap-rejected candidates do not exceed the full-frame cap")
    if paid_rejections != rows - accepted:
        errors.append(f"rejected candidates missing paid cap rejection work: {paid_rejections}/{rows-accepted}")
    if analyze_counts != {1: rows} or forward_counts != {3: rows}:
        errors.append("shared one-analysis/three-forward-transform counts did not hold for every decision")
    if exact_bound_bad or prune_bound_bad or protected_bad or selected_bad:
        errors.append("exact/prune error bound or protected/source RGB565 mismatch")
    companion_rel = Path("experiments/python-game-unified-codec-study/matched-exact.json")
    companion_path = ROOT / companion_rel
    matched = {"status": "pending", "path": companion_rel.as_posix()}
    if companion_path.is_file():
        m = json.loads(companion_path.read_text())
        result_digest = sha256(result_path)
        analysis_path = result_path.parent / "analyze.py"
        analysis_digest = sha256(analysis_path) if analysis_path.is_file() else None
        matched_ok = (m.get("results_sha256") == result_digest and m.get("analysis_sha256") == analysis_digest
                      and all(all(sc.get(k) is True for k in ("source_hashes_identical", "display_rgb_hashes_exact", "base_rgb_hashes_exact", "selected_reference_ids_and_tags_exact", "all_source_quality_metrics_exact")) for sc in m.get("scenes", [])))
        if not matched_ok:
            errors.append("matched exact-reference analysis hash or equality assertions failed")
        matched = {"status": "verified" if matched_ok else "invalid", "path": companion_rel.as_posix(),
                   "source_ids": m.get("source_ids"), "stored_canonical_yuv_tag_observations": m.get("stored_canonical_yuv_tag_observations"),
                   "results_sha256_matches": m.get("results_sha256") == result_digest,
                   "analysis_sha256_matches": m.get("analysis_sha256") == analysis_digest,
                   "scenes": [{"name": sc.get("name"), "matched_ids": len(sc.get("matched_ids", [])),
                               "source_hashes_identical": sc.get("source_hashes_identical"),
                               "display_rgb_hashes_exact": sc.get("display_rgb_hashes_exact"),
                               "base_rgb_hashes_exact": sc.get("base_rgb_hashes_exact"),
                               "selected_reference_ids_and_tags_exact": sc.get("selected_reference_ids_and_tags_exact"),
                               "all_source_quality_metrics_exact": sc.get("all_source_quality_metrics_exact"),
                               "gm_mean_bytes": sc.get("gm_mean_bytes"),
                               "selected_exact_mean_bytes": sc.get("selected_exact_mean_bytes"),
                               "raw_gm_fallbacks": sc.get("raw_gm_fallbacks")} for sc in m.get("scenes", [])]}
    pin_results = []
    for abs_name, expected in data.get("source_sha256", {}).items():
        p = Path(abs_name)
        try:
            actual = sha256(p)
            match = actual == expected
        except OSError:
            actual, match = None, False
        pin_results.append({"path": portable_path(p), "sha256": actual, "expected": expected, "matches": match})
        if not match:
            errors.append(f"codec source pin mismatch/unavailable: {p}")
    media = {}
    for scene in data.get("scenes", []):
        m = scene.get("manifest", {})
        p, expected = Path(m.get("source", "")), m.get("source_sha256")
        key = portable_path(p)
        if not expected or key in media:
            continue
        try:
            before = sha256(p); after = sha256(p)
            media[key] = {"expected": expected, "before": before, "after": after,
                          "matches_manifest": before == expected, "stable_during_audit": before == after}
        except OSError:
            media[key] = {"expected": expected, "before": None, "after": None,
                          "matches_manifest": False, "stable_during_audit": False}
        if not media[key]["matches_manifest"] or not media[key]["stable_during_audit"]:
            errors.append(f"codec external media hash mismatch/unstable: {p}")
    test_log = _test_log_summary(result_path.parent / "tests.log")
    return {"status": "verified" if not errors else "invalid", "path": rel.as_posix(),
            "evidence": data.get("evidence"), "source_ids": data.get("source_ids"),
            "decision_rows": rows, "admitted": accepted, "rejected_with_paid_cap_work": paid_rejections,
            "cap_bytes": CAP, "accepted_full_packet_over_cap": over_cap, "packet_vs_recorded_complete_bytes_mismatch": frame_size_mismatch,
            "inner_plus_envelope_size_mismatches": wrapper_size_mismatch, "cap_rejections_not_over_cap": rejected_not_over_cap,
            "actual_analyze_call_counts": analyze_counts, "actual_forward_call_counts": forward_counts,
            "same_frame_ids_and_input_hashes_across_profiles": not any("profile frame ID or input hash mismatch" in e for e in errors),
            "exact_same_reference_delta_violations": exact_bound_bad, "prune4_over_bound_violations": prune_bound_bad,
            "protected_gm_rgb565_mismatch_rows": protected_bad, "selected_original_rgb565_mismatch_rows": selected_bad,
            "case_profile_summaries": bytes_by_case, "matched_exact_reference": matched,
            "timing_scope": data.get("timing_scope"), "quality_scope": data.get("quality_scope"),
            "reference_scope": data.get("reference_scope"), "memory_scope": data.get("memory_scope"),
            "source_scope": data.get("source_scope"), "deployment_scope": data.get("deployment_scope"),
            "study_regression_test_log": test_log, "source_pins": pin_results,
            "external_media_hashes": media, "errors": errors}




def analyze_cadence_gate(final_signal=False):
    rel = Path("experiments/python-game-cadence-gate-study/results.json")
    result_path = ROOT / rel
    if not result_path.is_file():
        return {"status": "pending", "path": rel.as_posix()}
    data = json.loads(result_path.read_text())
    errors = []
    validation = data.get("validation_scope", {})
    prior_pts, new_pts = validation.get("prior_selected_pts", []), validation.get("new_selected_pts", [])
    disjoint = bool(new_pts and prior_pts and min(new_pts) > max(prior_pts) and validation.get("source_scoped_identities_disjoint"))
    pts_match_manifest = True
    new_case_count = 0
    case_summaries = []
    gate_evaluations = gate_eligible = gate_paid_ms = gate_decision_bad = packet_bad = selected_bad = 0
    decoded_ui_frames = 0
    input_hashes = {}
    profile_index = {}
    for case in data.get("cases", []):
        result = case.get("result", {})
        manifest = case.get("manifest", {})
        if case.get("source", "").endswith("new60-10.04s"):
            new_case_count += 1
            pts_match_manifest &= manifest.get("selected_pts") == new_pts
            pts_match_manifest &= len(set(manifest.get("frame_sha256", []))) == 60
            pts_match_manifest &= manifest.get("source_sha256") == validation.get("new_source_sha256")
        input_hashes.setdefault(case.get("source"), set()).update(manifest.get("frame_sha256", []))
        profile_index[(case.get("source"), case.get("profile"))] = case
        gate_case_evals = gate_case_eligible = 0
        for packet in result.get("packets", []):
            info = packet.get("info", {})
            packet_bad += int(packet.get("bytes", 0) > CAP or packet.get("bytes") != info.get("bytes")
                              or packet.get("bytes") != info.get("inner_bytes", 0)+info.get("envelope_bytes", 0)+info.get("patch_bytes", 0)
                              or not info.get("cap_fit", False))
            gate = info.get("gate")
            if gate and gate.get("evaluated"):
                gate_case_evals += 1; gate_evaluations += 1
                allow = bool(gate.get("planes")) and all(float(plane.get("zero_or_dc_fraction", 0)) >= float(gate.get("threshold", 1.1)) for plane in gate["planes"])
                gate_decision_bad += int(allow != gate.get("allow_sr"))
                gate_case_eligible += int(gate.get("allow_sr"))
                gate_eligible += int(gate.get("allow_sr"))
                gate_paid_ms += float(gate.get("service_ms", 0))
                # SR may only be serialized after the causal sample allows it.
                gate_decision_bad += int(any(x.get("codec") == "SR01" for x in info.get("inner_attempts", [])) and not gate.get("allow_sr"))
        commits = result.get("commits", [])
        for commit in commits:
            if commit.get("selected_exact_pixels", 0):
                decoded_ui_frames += 1
                selected_bad += int(commit.get("selected_exact_pixels") != 21120 or commit.get("selected_ui_mismatches", 0) != 0)
        summary = next((s for s in data.get("summary", []) if s.get("source") == case.get("source") and s.get("profile") == case.get("profile")), {})
        gate_decision_bad += int(summary.get("gate_evaluations", 0) != gate_case_evals)
        gate_decision_bad += int(summary.get("gate_eligible", 0) != gate_case_eligible)
        case_summaries.append({"source": case.get("source"), "profile": case.get("profile"), "mode": case.get("mode"),
            "captures": result.get("capture_count"), "prepared": result.get("prepared"), "decoded": len(commits),
            "strict": result.get("presented_strict"), "eventual": result.get("presented_eventual"),
            "gate_evaluations": gate_case_evals, "gate_eligible": gate_case_eligible,
            "gate_service_ms": summary.get("gate_service_ms"), "inner_formats": summary.get("inner_formats"),
            "forward_ipv4_udp_bytes": result.get("forward_ipv4_udp_bytes"), "mean_frame_bytes": summary.get("mean_frame_bytes"),
            "python_wall_seconds": result.get("python_wall_seconds"), "selected_ui_mismatches": summary.get("selected_ui_mismatches"),
            "active_rgb565_mse_mean": summary.get("active_rgb565_mse_mean")})
    if data.get("case_count") != 9 or len(case_summaries) != 9 or sum(x.get("captures", 0) for x in case_summaries) != 540:
        errors.append("cadence gate cases/capture total mismatch")
    if not disjoint or not pts_match_manifest or new_case_count != 3 or validation.get("new_unique_frame_hashes") != 60 or validation.get("shared_prior_new_hash_count") != 0 or validation.get("new_repeated_hash_count") != 0:
        errors.append("new validation PTS are not disjoint/matched to manifest")
    if gate_decision_bad or packet_bad or selected_bad:
        errors.append(f"gate decisions/packet caps/exact UI mismatches: {gate_decision_bad}/{packet_bad}/{selected_bad}")
    gated_cases = sum(1 for x in case_summaries if x.get("mode") == "gated")
    if gate_evaluations != 174 or gate_eligible != 0 or gated_cases != 3:
        errors.append(f"gate evaluation expectations differ: evals={gate_evaluations}, eligible={gate_eligible}, cases={gated_cases}")
    suite = _test_log_summary(result_path.parent / "tests.log")
    verify_text = (result_path.parent / "verify.log").read_text(errors="replace") if (result_path.parent / "verify.log").is_file() else ""
    verify_pass = verify_text.startswith("PASS:")
    analysis_path = result_path.parent / "analyze.py"
    analysis_json_path = result_path.parent / "gate-analysis.json"
    analysis = json.loads(analysis_json_path.read_text()) if analysis_json_path.is_file() else {}
    analysis_matches = (analysis.get("results_sha256") == sha256(result_path)
                        and analysis.get("analysis_source_sha256") == sha256(analysis_path))
    analysis_check = (result_path.parent / "analysis-verify.log").read_text(errors="replace") if (result_path.parent / "analysis-verify.log").is_file() else ""
    analysis_pass = analysis_check.startswith("PASS:")
    skipped_wins = sum(len(row.get("actual_control_sr_wins_skipped_by_gate", [])) for row in analysis.get("rows", []))
    skipped_bytes = sum(row.get("matched_control_saved_inner_bytes", 0) for row in analysis.get("rows", []))
    matched_control_ids = sum(len(row.get("matched_reference_and_gm_length_ids", [])) for row in analysis.get("rows", []))
    analysis_bad = int(not analysis_matches or not analysis_pass or len(analysis.get("rows", [])) != 3 or skipped_wins != 79 or skipped_bytes != 19400 or matched_control_ids != 174)
    if analysis_bad:
        errors.append("paired actual-control analysis hashes/checks or summarized skipped wins do not match")
    if suite.get("status") != "pass" or suite.get("passed_count") != 15 or not verify_pass:
        errors.append("cadence regression/verification evidence is missing or failing")
    pin_results = []
    for abs_name, expected in data.get("source_sha256", {}).items():
        p = Path(abs_name)
        try:
            actual = sha256(p); match = actual == expected
        except OSError:
            actual, match = None, False
        pin_results.append({"path": portable_path(p), "sha256": actual, "expected": expected, "matches": match})
        if not match:
            errors.append(f"cadence source pin mismatch/unavailable: {p}")
    media = {}
    for case in data.get("cases", []):
        m = case.get("manifest", {}); p = Path(m.get("source", "")); expected = m.get("source_sha256"); key = portable_path(p)
        if not expected or key in media: continue
        try:
            before = sha256(p); after = sha256(p)
            media[key] = {"expected": expected, "before": before, "after": after,
                          "matches_manifest": before == expected, "stable_during_audit": before == after}
        except OSError:
            media[key] = {"expected": expected, "before": None, "after": None,
                          "matches_manifest": False, "stable_during_audit": False}
        if not media[key]["matches_manifest"] or not media[key]["stable_during_audit"]:
            errors.append(f"cadence external media hash mismatch/unstable: {p}")
    copy_origin_path = result_path.parent / "copy-origin.json"
    copy_origin = json.loads(copy_origin_path.read_text()) if copy_origin_path.is_file() else None
    old_hashes_stable = bool(copy_origin)
    if copy_origin:
        for relpath, expected in copy_origin.get("source_sha256", {}).items():
            p = ROOT / relpath
            try: old_hashes_stable &= sha256(p) == expected
            except OSError: old_hashes_stable = False
    if not old_hashes_stable:
        errors.append("frozen original source hashes in copy-origin do not match")
    # The result currently exists, but do not call it final until parent sends the requested final signal.
    status = ("verified" if not errors else "invalid") if final_signal else "available_unreviewed"
    result_by_key = {(x["source"], x["profile"]): x for x in case_summaries}
    new_source = "mass-effect-2600-new60-10.04s"
    new_window = {profile: result_by_key.get((new_source, profile)) for profile in ("gm_ui", "exact_ui", "gated_ui")}
    return {"status": status, "path": rel.as_posix(), "evidence": data.get("evidence"),
        "case_count": len(case_summaries), "capture_events": sum(x.get("captures", 0) for x in case_summaries),
        "total_python_wall_seconds": data.get("total_python_wall_seconds"), "gate_config": data.get("gate_config"),
        "validation_disjoint": disjoint, "prior_max_pts": max(prior_pts) if prior_pts else None,
        "new_min_pts": min(new_pts) if new_pts else None, "new_max_pts": max(new_pts) if new_pts else None,
        "validation_hash_scope": {k:v for k,v in validation.items() if k not in ("prior_selected_pts", "new_selected_pts", "new_selected_times_seconds")},
        "gate_evaluations": gate_evaluations, "gate_eligible": gate_eligible, "gate_service_ms_total": gate_paid_ms,
        "gate_service_ms_per_evaluation": gate_paid_ms/gate_evaluations if gate_evaluations else None,
        "matched_control_comparison": {"analysis_hashes_match": analysis_matches, "analysis_check_pass": analysis_pass,
            "same_reference_and_gm_length_ids": matched_control_ids, "actual_control_sr_wins_skipped": skipped_wins,
            "matched_control_inner_bytes_saved": skipped_bytes,
            "scope": "Measured exact control candidates only; skipped gated SR payload lengths remain unknown"},
        "gate_decision_errors": gate_decision_bad, "packet_size_or_cap_errors": packet_bad,
        "exact_ui_decoded_frames": decoded_ui_frames, "exact_ui_word_mismatch_rows": selected_bad,
        "new_window_profiles": new_window, "case_summaries": case_summaries,
        "gate_scope": data.get("gate_scope"), "timing_scope": data.get("timing_scope"),
        "transport_scope": data.get("transport_scope"), "source_scope": data.get("source_scope"),
        "quality_scope": data.get("quality_scope"), "limits": data.get("limits"),
        "source_pins": pin_results, "external_media_hashes": media, "frozen_original_hashes_stable": old_hashes_stable,
        "study_regression_test_log": suite, "verify_log_pass": verify_pass, "analysis_verify_log_pass": analysis_pass, "errors": errors}


def analyze_stream():
    rel = Path("experiments/python-game-unified-stream-study/results.json")
    result_path = ROOT / rel
    if not result_path.is_file():
        return {"status": "pending", "path": rel.as_posix()}
    data = json.loads(result_path.read_text())
    errors = []
    event_count = prepared = decoded = cap_bad = complete_bad = crc_bad = ref_tag_bad = 0
    resource_bad = drain_bad = work_bad = ui_selected_bad = ack_bad = expiry_publish_bad = 0
    ui_decoded = selected_ui_total = 0
    max_peaks = {"sender": 0, "ingress": 0, "framebuffers": 0, "feedback": 0}
    cases = []
    case_by_key = {}
    input_hashes_by_source = {}
    profile_rows_by_key = {}
    promotion_loss_safe = conflict_expiry_safe = False
    for case in data.get("cases", []):
        result = case.get("result", {})
        event_count += result.get("capture_count", 0)
        prepared += result.get("prepared", 0)
        decoded += len(result.get("commits", []))
        packets = result.get("packets", [])
        commits = {x.get("id"): x for x in result.get("commits", [])}
        manifest_hashes = case.get("manifest", {}).get("frame_sha256", [])
        input_hashes_by_source.setdefault(case.get("source"), set()).update(manifest_hashes)
        profile_rows_by_key[(case.get("source"), case.get("profile"))] = {
            "packet_ids": {x.get("id") for x in packets}, "decoded_ids": set(commits),
            "manifest_hashes": manifest_hashes,
            "unique_decoded_hashes": len({x.get("rgb_sha256") for x in commits.values()})}
        feedback = result.get("feedback", [])
        pubs = {x.get("id"): x for x in result.get("publications", [])}
        for packet in packets:
            size, info = packet.get("bytes", 0), packet.get("info", {})
            cap_bad += int(size > CAP or size != info.get("bytes") or not info.get("cap_fit", False))
            complete_bad += int(size != info.get("inner_bytes", 0) + info.get("envelope_bytes", 0) + info.get("patch_bytes", 0))
            route = packet.get("receiver_route") or {}
            crc_bad += int(packet.get("route_crc") != route.get("body_crc") or route.get("epoch") != result.get("config", {}).get("epoch", 1) or route.get("frame_id") != packet.get("id"))
            ref_bank, ref_id, ref_tag = packet.get("reference_bank"), packet.get("reference_id"), packet.get("reference_tag")
            if ref_bank in (0, 1) and ref_id is not None:
                reference = (packet.get("receiver_banks_before") or {}).get(str(ref_bank))
                ref_tag_bad += int(not reference or reference.get("id") != ref_id or reference.get("tag") != ref_tag)
            if packet.get("decode_started_ms") is not None:
                ref_tag_bad += int(not packet.get("read_pin_at_decode_start"))
                ref_tag_bad += int(packet.get("decode_error") is not None)
            if packet.get("id") in commits:
                cmt = commits[packet["id"]]
                if cmt.get("selected_exact_pixels", 0):
                    ui_decoded += 1
                    selected_ui_total += cmt["selected_exact_pixels"]
                    ui_selected_bad += int(cmt.get("selected_ui_mismatches", 0) != 0 or cmt.get("selected_exact_pixels") != 21120)
        packet_by_id = {p.get("id"): p for p in packets}
        for fbrow in feedback:
            if fbrow.get("kind") == "ack_applied":
                p = packet_by_id.get(fbrow.get("id"))
                if not p or fbrow.get("at_ms", -1) < p.get("decode_done_ms", 1e30):
                    ack_bad += 1
                elif p.get("key") or p.get("promoted"):
                    bank = (fbrow.get("sender_banks") or {}).get(str(p.get("destination_bank")))
                    ack_bad += int(not bank or bank.get("id") != p.get("id"))
            if fbrow.get("kind") == "expired":
                expiry_publish_bad += int(any(x.get("kind") == "ack_applied" and x.get("id") == fbrow.get("id") for x in feedback))
        for work in result.get("work", []):
            try:
                start, done, wall, service = (float(work[k]) for k in ("start_ms", "done_ms", "wall_ms", "service_ms"))
                work_bad += int(min(start, done, wall, service) < 0 or abs((done-start)-wall) > 0.002 or abs(wall-service) > 0.002)
            except (KeyError, TypeError, ValueError):
                work_bad += 1
        unresolved_ok = (not result.get("unresolved_ids") and all(x is None for x in result.get("unresolved_sender_slots", []))
                         and not result.get("unresolved_encoder_pending") and not result.get("unresolved_ingress")
                         and result.get("unresolved_receiver_readers") == 0 and not result.get("unresolved_decode"))
        drain_bad += int(not unresolved_ok)
        sender_final, receiver_final = result.get("sender_banks_final", {}), result.get("receiver_banks_final", {})
        roles_ok = (set(sender_final) == {"0", "1"} and set(receiver_final) == {"0", "1"}
                    and result.get("peak_sender", 99) <= 3 and result.get("peak_ingress", 99) <= 2
                    and result.get("peak_framebuffers", 99) <= 3 and result.get("peak_feedback", 99) <= 4)
        resource_bad += int(not roles_ok)
        for k, field in (("sender", "peak_sender"), ("ingress", "peak_ingress"), ("framebuffers", "peak_framebuffers"), ("feedback", "peak_feedback")):
            max_peaks[k] = max(max_peaks[k], result.get(field, 0))
        case_by_key[(case.get("source"), case.get("profile"))] = case
        cases.append({"source": case.get("source"), "profile": case.get("profile"), "mode": case.get("mode"),
                      "exact_ui": case.get("exact_ui"), "cohort": case.get("manifest", {}).get("cohort"),
                      "captures": result.get("capture_count"), "prepared": result.get("prepared"),
                      "decoded": len(result.get("commits", [])), "strict": result.get("presented_strict"),
                      "eventual": result.get("presented_eventual"), "diagnostic_ids_per_second": result.get("diagnostic_ids_per_second"),
                      "forward_ipv4_udp_bytes": result.get("forward_ipv4_udp_bytes"),
                      "reverse_ipv4_udp_bytes": result.get("reverse_ipv4_udp_bytes"),
                      "python_wall_seconds": result.get("python_wall_seconds"),
                      "selected_ui_pixels_per_decoded": (sum(x.get("selected_exact_pixels", 0) for x in commits.values()) / len(commits)) if commits else 0,
                      "active_rgb565_mse_mean": case.get("result", {}).get("active_rgb565_mse_mean")})
    if data.get("case_count") != len(cases) or len(cases) != 14:
        errors.append(f"expected 14 finite cases, found {len(cases)}")
    if (event_count, prepared, decoded) != (1248, 1154, 1152):
        errors.append(f"finite totals unexpected: captures/prepared/decoded={event_count}/{prepared}/{decoded}")
    if cap_bad or complete_bad or crc_bad or ref_tag_bad:
        errors.append(f"packet/CRC/reference-tag lifecycle failures: {cap_bad}/{complete_bad}/{crc_bad}/{ref_tag_bad}")
    if resource_bad or drain_bad:
        errors.append(f"resource bounds/final drain failures: {resource_bad}/{drain_bad}")
    if work_bad:
        errors.append(f"{work_bad} work rows have invalid or uncharged duration")
    if ack_bad or expiry_publish_bad:
        errors.append(f"staged ACK publication/expiry errors: {ack_bad}/{expiry_publish_bad}")
    if ui_selected_bad:
        errors.append(f"{ui_selected_bad} decoded UI rows violate exact 21,120-word selection")
    # Independent event checks for lost and conflicting promotion feedback.
    loss = case_by_key.get(("synthetic-fault24", "promotion_ack_loss"), {}).get("result", {})
    lost = any(x.get("kind") == "lost" and x.get("id") == 8 for x in loss.get("feedback", []))
    expired = any(x.get("kind") == "expired" and x.get("id") == 8 for x in loss.get("feedback", []))
    fallback = [x for x in loss.get("packets", []) if x.get("id") == 9]
    promotion_loss_safe = lost and expired and bool(fallback) and fallback[0].get("bank0_fallback") and fallback[0].get("reference_id") == 0
    conflict = case_by_key.get(("synthetic-fault24", "conflicting_promotion_feedback"), {}).get("result", {})
    statuses = [x.get("status") for x in conflict.get("feedback", []) if x.get("kind") == "parsed" and x.get("id") == 8]
    conflict_expiry_safe = set(statuses) == {1, 2} and any(x.get("kind") == "expired" and x.get("id") == 8 for x in conflict.get("feedback", []))
    if not promotion_loss_safe or not conflict_expiry_safe:
        errors.append("lost/conflicting promotion feedback did not expire safely")
    suite = _test_log_summary(result_path.parent / "tests.log")
    verify_text = (result_path.parent / "verify.log").read_text(errors="replace") if (result_path.parent / "verify.log").is_file() else ""
    verify_pass = verify_text.startswith("PASS:")
    if suite.get("status") != "pass" or suite.get("passed_count") != 11 or not verify_pass:
        errors.append("stream regression/verify evidence is missing or failing")
    pins = []
    for abs_name, expected in data.get("source_sha256", {}).items():
        p = Path(abs_name)
        try:
            actual = sha256(p); match = actual == expected
        except OSError:
            actual, match = None, False
        pins.append({"path": portable_path(p), "sha256": actual, "expected": expected, "matches": match})
        if not match:
            errors.append(f"stream source pin mismatch/unavailable: {p}")
    media = {}
    for case in data.get("cases", []):
        m = case.get("manifest", {}); p = Path(m.get("source", "")); expected = m.get("source_sha256"); key = portable_path(p)
        if not expected or key in media:
            continue
        try:
            before = sha256(p); after = sha256(p)
            media[key] = {"expected": expected, "before": before, "after": after,
                          "matches_manifest": before == expected, "stable_during_audit": before == after}
        except OSError:
            media[key] = {"expected": expected, "before": None, "after": None,
                          "matches_manifest": False, "stable_during_audit": False}
        if not media[key]["matches_manifest"] or not media[key]["stable_during_audit"]:
            errors.append(f"stream external media hash mismatch/unstable: {p}")
    pair_errors = 0
    pairs = []
    for p in data.get("pairs", []):
        left = profile_rows_by_key.get((p.get("source"), p.get("left_profile")), {})
        right = profile_rows_by_key.get((p.get("source"), p.get("right_profile")), {})
        admitted_common = sorted(left.get("packet_ids", set()) & right.get("packet_ids", set()))
        decoded_common = sorted(left.get("decoded_ids", set()) & right.get("decoded_ids", set()))
        pair_errors += int(admitted_common != p.get("common_admitted_ids", []))
        pair_errors += int(decoded_common != p.get("common_decoded_ids", []))
        pair_errors += int(left.get("manifest_hashes") != right.get("manifest_hashes"))
        pairs.append({"source": p.get("source"), "left_profile": p.get("left_profile"), "right_profile": p.get("right_profile"),
              "common_admitted_ids": len(p.get("common_admitted_ids", [])), "common_decoded_ids": len(p.get("common_decoded_ids", [])),
              "input_hash_manifest_equal": left.get("manifest_hashes") == right.get("manifest_hashes"),
              "same_reference_and_promotion_ids": len(p.get("same_reference_and_promotion_ids", [])),
              "mean_common_decoded_mse_delta": p.get("mean_common_decoded_mse_delta"),
              "strict_delta": p.get("strict_delta"), "eventual_delta": p.get("eventual_delta"), "caveat": p.get("caveat")})
    if pair_errors:
        errors.append(f"{pair_errors} matched-pair ID/input-hash checks failed")
    native_hashes = set().union(*(v for k, v in input_hashes_by_source.items() if not k.startswith("synthetic-")))
    synthetic_hashes = set().union(*(v for k, v in input_hashes_by_source.items() if k.startswith("synthetic-")))
    return {"status": "verified" if not errors else "invalid", "path": rel.as_posix(), "evidence": data.get("evidence"),
            "input_cohorts": {"native_unique_source_hashes": len(native_hashes), "synthetic_unique_source_hashes": len(synthetic_hashes),
                              "unique_input_hashes_by_source": {k: len(v) for k,v in input_hashes_by_source.items()}},
            "unique_decoded_rgb_hashes_by_case": {f"{c['source']}/{c['profile']}": profile_rows_by_key[(c['source'],c['profile'])]["unique_decoded_hashes"] for c in data.get("cases", [])},
            "matched_pair_ID_and_input_hash_errors": pair_errors,
            "case_count": len(cases), "capture_events": event_count, "prepared": prepared, "decoded": decoded,
            "total_python_wall_seconds": data.get("total_python_wall_seconds"), "diagnostic_ids_per_second_caveat": "finite strict schedule window count can exceed 30 during backlog/window phase; it is not a sustained source/input rate",
            "max_resource_peaks": max_peaks, "physical_drains_all_cases": drain_bad == 0,
            "complete_packet_cap_and_crc_reference_binding_errors": {"cap_or_size": cap_bad, "inner_envelope_ui_sum": complete_bad, "outer_route_crc": crc_bad, "stored_reference_tag_or_read_pin": ref_tag_bad},
            "lost_promotion_ack_safe_fallback": promotion_loss_safe, "conflicting_feedback_expires": conflict_expiry_safe,
            "staged_ack_after_decode_errors": ack_bad, "publication_after_expiry_errors": expiry_publish_bad,
            "work_duration_mismatches": work_bad,
            "decoded_ui_frames": ui_decoded, "selected_ui_source_rgb565_pixels": selected_ui_total,
            "selected_ui_mismatch_rows": ui_selected_bad, "resource_peaks": max_peaks,
            "case_summaries": cases, "matched_pair_summaries": pairs,
            "timing_scope": data.get("timing_scope"), "transport_scope": data.get("transport_scope"),
            "source_scope": data.get("source_scope"), "quality_scope": data.get("quality_scope"),
            "comparison_scope": data.get("comparison_scope"), "memory_scope": data.get("memory_scope"),
            "publication_scope": data.get("publication_scope"), "study_regression_test_log": suite,
            "verify_log_pass": verify_pass, "source_pins": pins, "external_media_hashes": media, "errors": errors}


def analyze_ui():
    rel = Path("experiments/python-game-unified-ui-study/results.json")
    result_path = ROOT / rel
    if not result_path.is_file():
        return {"status": "pending", "path": rel.as_posix()}
    results = json.loads(result_path.read_text())
    errors = []
    rows_n = attempts_n = hits_n = changed_hits_n = 0
    distinct_ids, input_hashes = set(), set()
    case_summaries = []
    selected_exact = unselected_exact = selector_equal = display_equal = True
    over_budget = framed_prefix_mismatches = 0
    for case in results.get("cases", []):
        summary = case.get("summary", {})
        case_attempts = case_hits = case_changed_hits = 0
        for row in case.get("rows", []):
            rows_n += 1
            distinct_ids.add((case.get("source"), row.get("id")))
            input_hashes.add(row.get("input_sha256"))
            unc, cached = row.get("uncached", {}), row.get("cached", {})
            selector_equal &= unc.get("selected") == cached.get("selected")
            display_equal &= row.get("uncached_display_sha256") == row.get("cached_display_sha256")
            selected_exact &= row.get("selected_word_mismatches") == 0
            unselected_exact &= row.get("unselected_base_word_mismatches") == 0
            for mode in (unc, cached):
                budget = mode.get("byte_budget")
                for attempt in mode.get("attempts", []):
                    case_attempts += 1
                    attempts_n += 1
                    framed_prefix_mismatches += int(attempt.get("framed_bytes") != attempt.get("patch_bytes", -4) + 4)
                    if attempt.get("fits") and attempt.get("projected_ui_bytes", 0) > budget:
                        over_budget += 1
                for attempt in mode.get("attempts", []):
                    details = attempt.get("candidate_details", {})
                    hit = bool(details.get("cache_hit"))
                    case_hits += int(hit)
                    hits_n += int(hit)
                    case_changed_hits += int(hit and row.get("source_changed"))
                    changed_hits_n += int(hit and row.get("source_changed"))
        case_summaries.append({"source": case.get("source"), "cohort": case.get("cohort"), **summary})
    if results.get("paired_ids") != 160 or rows_n != 160:
        errors.append(f"expected paired IDs/rows 160, got {results.get('paired_ids')}/{rows_n}")
    if not selector_equal:
        errors.append("paired cache variants changed selector output")
    if not display_equal:
        errors.append("paired cache variants changed display RGB565 hash")
    if not selected_exact or not unselected_exact:
        errors.append("selected original or unselected base RGB565 mismatch recorded")
    if over_budget:
        errors.append(f"{over_budget} selected candidates exceed declared UI budget")
    if framed_prefix_mismatches:
        errors.append(f"{framed_prefix_mismatches} patch framing lengths do not include four-byte prefix")
    # Verify code pins and external media hashes without modifying either.
    pin_results = []
    for abs_name, expected in results.get("source_sha256", {}).items():
        p = Path(abs_name)
        try:
            actual = sha256(p)
            match = actual == expected
        except OSError:
            actual, match = None, False
        pin_results.append({"path": portable_path(p), "sha256": actual, "expected": expected, "matches": match})
        if not match:
            errors.append(f"source pin mismatch/unavailable: {p}")
    media = {}
    for case in results.get("cases", []):
        m = case.get("manifest", {})
        p = Path(m.get("source", ""))
        expected = m.get("source_sha256")
        if not expected or str(p) in media:
            continue
        try:
            before = sha256(p)
            after = sha256(p)
            media[portable_path(p)] = {"expected": expected, "before": before, "after": after,
                             "matches_manifest": before == expected, "stable_during_audit": before == after}
        except OSError:
            media[portable_path(p)] = {"expected": expected, "before": None, "after": None,
                             "matches_manifest": False, "stable_during_audit": False}
        if not media[portable_path(p)]["matches_manifest"] or not media[portable_path(p)]["stable_during_audit"]:
            errors.append(f"external media hash mismatch/unstable: {p}")
    return {
        "status": "verified" if not errors else "invalid",
        "path": rel.as_posix(), "evidence": results.get("evidence"),
        "paired_ids": results.get("paired_ids"), "rows": rows_n,
        "unique_case_frame_ids": len(distinct_ids), "unique_input_hashes": len(input_hashes),
        "case_count": len(results.get("cases", [])),
        "per_case_unique_source_hashes": {c.get("source"): c.get("summary", {}).get("unique_source_hashes") for c in results.get("cases", [])},
        "patch_attempts_both_variants": attempts_n, "patch_attempts_per_variant": attempts_n // 2, "cache_hits": hits_n,
        "hits_on_changed_whole_source": changed_hits_n,
        "selected_original_rgb565_exact": selected_exact,
        "unselected_base_rgb565_exact": unselected_exact,
        "cached_and_uncached_selector_output_equal": selector_equal,
        "cached_and_uncached_display_hash_equal": display_equal,
        "over_budget_selected_candidates": over_budget,
        "four_byte_prefix_mismatches": framed_prefix_mismatches,
        "budget_scope": results.get("budget_scope"),
        "timing_scope": results.get("timing_scope"),
        "quality_scope": results.get("quality_scope"),
        "memory_scope": results.get("memory_scope"),
        "source_scope": results.get("source_scope"),
        "integration_scope": results.get("integration_scope"),
        "case_summaries": case_summaries,
        "source_pins": pin_results, "external_media_hashes": media,
        "study_regression_test_log": _test_log_summary(result_path.parent / "tests.log"),
        "errors": errors,
    }


def load_audit():
    data = json.loads(AUDIT_PATH.read_text())
    ui = analyze_ui()
    codec = analyze_codec()
    stream = analyze_stream()
    cadence = analyze_cadence_gate(final_signal=data.get("cadence_gate_final_signal", False))
    data["inputs"]["unified_ui"]["status"] = ui["status"]
    data["inputs"]["unified_codec"]["status"] = codec["status"]
    data["inputs"]["unified_stream"]["status"] = stream["status"]
    data["results"] = {"unified_ui": ui, "unified_codec": codec, "unified_stream": stream, "cadence_gate": cadence}
    data["inputs"]["cadence_gate"]["status"] = cadence["status"]
    # Status reflects all independently audited inputs; file presence alone is not final evidence.
    data["status"] = "verified" if all(x["status"] == "verified" for x in (ui, codec, stream, cadence)) else "pending"
    data["checks"]["ui_exact_selection_or_display_only"] = ui["status"]
    data["checks"]["cadence_gate_matches_fps_priority_exact_policy"] = cadence["status"]
    data["checks"]["source_pins_and_external_media_hash_stability"] = "verified" if all(x["status"] == "verified" for x in (ui, codec, stream)) else "pending"
    for key in ("full_outer_frame_bytes_and_caps", "losing_candidate_paid_work", "shared_forward_transform", "quality_and_prune_bounds_vs_baseline"):
        data["checks"][key] = codec["status"] if key != "quality_and_prune_bounds_vs_baseline" or codec["matched_exact_reference"]["status"] == "verified" else "pending"
    for key in ("outermost_crc_and_stored_tag", "ownership_2bank_3sender_2ingress_3framebuffer", "lost_ack_safe_fallback", "physical_drains", "staged_publication_expiry", "paid_error_work", "finite_measured_host_cost_vs_assumed_link", "matched_ids_unique_inputs_decoded_hashes_real_vs_synthetic"):
        data["checks"][key] = stream["status"]
    return data


def main():
    print(json.dumps(load_audit(), indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
