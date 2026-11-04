#!/usr/bin/env python3
"""Read-only evidence audit scaffold for the v18 Python game studies."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT_PATH = HERE / "audit.json"
STUDIES = {
    "candidate_commit": "experiments/python-game-candidate-commit-study",
    "ar03_trace": "experiments/python-game-ar03-trace-study",
    "joint_admission": "experiments/python-game-joint-admission-study",
}
# Keep empty until the parent explicitly signals that a named study is final.
READY_STUDIES: set[str] = {"candidate_commit", "ar03_trace", "joint_admission"}
TARGET = {"canvas": [720, 480], "active_image": [720, 405], "fps": 30}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def portable(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return "external:" + path.name


def resolve_pin(raw: str) -> Path:
    marker = "/moonbub-30fps-study/"
    if marker in raw:
        return ROOT / Path(raw.split(marker, 1)[1])
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def test_log(path: Path) -> dict:
    if not path.is_file():
        return {"status": "missing", "passed_count": None}
    text = path.read_text(errors="replace")
    match = re.search(r"Ran (\d+) tests?", text)
    passed = match is not None and "OK" in text and "FAILED (" not in text and "ERROR" not in text
    return {"status": "pass" if passed else "invalid", "passed_count": int(match.group(1)) if match else None}


def audit_candidate(data: dict) -> dict:
    errors = []
    rows = data.get("rows", [])
    commits = [r for r in rows if r.get("action") == "commit"]
    discards = [r for r in rows if r.get("action") == "discard"]
    exact_commits = all(r.get("byte_identical_frozen") is True
                        and r.get("decoded_sha256") == r.get("frozen_decoded_sha256")
                        and r.get("selected_words") == 21120 and r.get("selected_word_errors") == 0
                        for r in commits)
    clean_discards = all(r.get("state_before") == r.get("state_after_build") == r.get("state_after")
                         and r.get("readers_after") == 0 for r in discards)
    cap = data.get("cap_rejections", [])
    clean_caps = all(c.get("complete_attempted_bytes", 0) > c.get("cap", 0)
                     and c.get("state_before") == c.get("state_after")
                     and c.get("readers_after") == 0 for c in cap)
    if len(rows) != 48 or data.get("native_decisions") != 48: errors.append("candidate native row/decision count mismatch")
    if len(commits) != 42 or data.get("native_commits") != 42: errors.append("candidate commit count mismatch")
    if len(discards) != 6 or data.get("native_discards") != 6: errors.append("candidate discard count mismatch")
    if not exact_commits or data.get("native_selected_exact_words") != 887040: errors.append("candidate byte/pixel/UI equality mismatch")
    if not clean_discards: errors.append("discard changed semantic state or retained a source reader")
    if len(cap) != 4 or not clean_caps: errors.append("paid cap rejection count/state/lease cleanup mismatch")
    measured = {"total_python_wall_seconds": data.get("total_python_wall_seconds"),
                "discard_build_ms": sum(r.get("build_ms", 0) for r in discards),
                "mean_discard_build_ms": sum(r.get("build_ms", 0) for r in discards) / len(discards) if discards else None,
                "cap_rejection_build_ms": [c.get("build_ms") for c in cap],
                "scope": "Measured Python work; not target CPU cycles or throughput"}
    limits = " ".join(data.get("limits", []))
    if "noFPS" not in limits and "FPS" not in limits: errors.append("candidate throughput limitation absent")
    return {"status": "verified" if not errors else "invalid", "native_candidates": len(rows),
            "commits": len(commits), "discards": len(discards), "cap_rejections": len(cap),
            "all_commits_match_frozen_wire_and_decode": exact_commits,
            "selected_ui_words": data.get("native_selected_exact_words"),
            "discard_state_unchanged_and_leases_released": clean_discards,
            "paid_cap_rejections_state_unchanged_and_leases_released": clean_caps,
            "measured_python_work": measured, "errors": errors}


def audit_trace(data: dict, directory: Path) -> dict:
    errors = []
    counts = data.get("counts", {})
    cohorts = data.get("cohorts", [])
    rows = [r for c in cohorts for r in c.get("rows", [])]
    demand_path = directory / "stripe-demand.json"
    try: demand = json.loads(demand_path.read_text())
    except (OSError, json.JSONDecodeError): demand = {}
    expected = {"cohorts": 3, "frames": 16, "native_frames": 12, "unique_native_acquisitions": 6,
                "gf02_datagrams": 244, "selected_ui_words": 253440, "coefficient_blocks": 97308,
                "objects": 215, "stored_object_bytes": 3466147}
    if counts != expected: errors.append("AR03 trace retained counts mismatch")
    if len(cohorts) != 3 or len(rows) != 16: errors.append("AR03 trace cohort/packet rows mismatch")
    complete_rows = all(isinstance(r.get("ar03"), dict) and isinstance(r.get("af03"), dict)
                        and isinstance(r.get("gf02"), list) and r.get("gf02")
                        and len(r.get("decoded_yuv", [])) == 3 and isinstance(r.get("display_rgb565"), dict)
                        and isinstance(r.get("pre_banks"), dict) and isinstance(r.get("post_banks"), dict)
                        and isinstance(r.get("trace"), dict) for r in rows)
    native_ui = [r for c in cohorts if c.get("name", "").startswith("native-") for r in c.get("rows", [])]
    exact_native_ui_inventory = len(native_ui) == 12 and all(r.get("selected_pixels") == 21120 for r in native_ui)
    if not complete_rows: errors.append("trace rows lack actual packet/GF02/AF03/decoded/reference object references")
    if not exact_native_ui_inventory: errors.append("native UI pixel evidence is not complete per decoded row")
    # Verify each referenced object is a safe relative path with matching stored and raw content hashes.
    import zlib
    refs, bad_refs = [], []
    def walk(value):
        if isinstance(value, dict):
            if {"path", "encoding", "raw_bytes", "raw_sha256", "stored_sha256"} <= value.keys():
                refs.append(value)
            else:
                for child in value.values(): walk(child)
        elif isinstance(value, list):
            for child in value: walk(child)
    walk(cohorts)
    for ref in refs:
        rel = Path(ref["path"])
        if rel.is_absolute() or ".." in rel.parts:
            bad_refs.append(ref["path"]); continue
        path = directory / rel
        if not path.is_file(): bad_refs.append(ref["path"]); continue
        stored = path.read_bytes()
        try: raw = zlib.decompress(stored) if ref["encoding"] == "zlib" else stored
        except zlib.error: raw = b""
        if hashlib.sha256(stored).hexdigest() != ref["stored_sha256"] or len(raw) != ref["raw_bytes"] or hashlib.sha256(raw).hexdigest() != ref["raw_sha256"]:
            bad_refs.append(ref["path"])
    if len({r.get("path") for r in refs}) != counts.get("objects"):
        errors.append("trace unique object inventory does not match manifest count")
    if bad_refs: errors.append(f"trace object refs missing/invalid: {len(bad_refs)}")
    if demand.get("results_sha256") != sha256(directory / "results.json") or demand.get("analyzer_sha256") != sha256(directory / "analyze.py"):
        errors.append("stripe-demand evidence is not hash-bound to current results/analyzer")
    if demand.get("plane_traces") != 48: errors.append("stripe-demand plane trace count mismatch")
    # The current verifier log records parser/lifecycle/negative-case replay; tests.log carries test count.
    verify_text = (directory / "verify.log").read_text(errors="replace") if (directory / "verify.log").is_file() else ""
    analysis_text = (directory / "analysis-verify.log").read_text(errors="replace") if (directory / "analysis-verify.log").is_file() else ""
    if "negative_atomic_rejections\": 53" not in verify_text or '"physical_or_native_30fps_proven": false' not in verify_text:
        errors.append("trace verifier log lacks atomic rejection/non-FPS evidence")
    if not analysis_text.startswith("PASS:"): errors.append("trace stripe-demand analysis verification missing")
    limits = " ".join(data.get("limits", []))
    if "No hardware/native/ISA/physical30fps proof" not in limits or "outside bound" not in limits:
        errors.append("trace hardware/decoder storage limitation missing")
    native = [r for r in demand.get("rows", []) if r.get("cohort") == "native-gm" and r.get("plane") == 0 and r.get("id") == 3]
    peak = max((r.get("peak_stripe_refill_bytes", 0) for r in native), default=0)
    ratio = max((r.get("peak_to_uniform_ratio", 0) for r in native), default=0)
    return {"status": "verified" if not errors else "invalid", "counts": counts,
            "actual_packets_with_ar03_gf02_af03_decoded_references": len(rows),
            "every_row_retains_packet_feedback_decode_and_reference_objects": complete_rows,
            "native_rows_with_exact_ui_pixel_count": len(native_ui) if exact_native_ui_inventory else None,
            "content_addressed_objects_checked": len(refs), "all_objects_valid": not bad_refs,
            "atomic_negative_rejections": 53, "unique_native_acquisitions_are_not_independent_frames": 6,
            "stripe_demand": {"plane_traces": demand.get("plane_traces"), "native_gm_id3_y_peak_refill_bytes": peak,
                              "max_peak_to_uniform_ratio": ratio, "scope": demand.get("scope")},
            "elapsed_python_seconds": data.get("elapsed_python_seconds"),
            "physical_memory_or_30fps_claim": False, "errors": errors}


def audit_joint(data: dict, directory: Path) -> dict:
    errors = []
    cases = data.get("cases", [])
    by_profile = {c.get("profile"): c for c in cases}
    summary = {x.get("profile"): x for x in data.get("summary", [])}
    native = [c for c in cases if c.get("source") == "native-regression"]
    synthetic = [c for c in cases if c.get("source") == "synthetic-fault"]
    if len(cases) != 8 or data.get("case_count") != 8: errors.append("joint case count is not eight")
    if len(data.get("source_sha256", {})) != 49: errors.append("joint source pin count is not 49")
    if len(native) != 6 or any(c.get("result", {}).get("capture_count") != 90 or c.get("manifest", {}).get("unique_frame_count") != 90 for c in native):
        errors.append("joint native cases are not six unique 90-frame captures each")
    if len(synthetic) != 2 or any(c.get("result", {}).get("capture_count") != 48 for c in synthetic): errors.append("joint synthetic fault inventory mismatch")
    if sum(c.get("result", {}).get("capture_count", 0) for c in cases) != 636: errors.append("joint aggregate capture count mismatch")
    profile_names = {"unbudgeted", "admit200", "admit150_batch8", "admit200_link4", "lost_credit_query", "lost_refresh_AF", "forward_loss", "corrupt_AF"}
    if set(by_profile) != profile_names or set(summary) != profile_names: errors.append("joint profile inventory mismatch")
    per_case = []
    for c in cases:
        r = c.get("result", {}); gw = r.get("gateway", {}); wire = gw.get("wire", [])
        data_packets = sum(not w.get("control") for w in wire)
        controls = sum(bool(w.get("control")) for w in wire)
        applied = gw.get("counters", {}).get("credits_applied", 0)
        ack_rows = [f for f in r.get("feedback", []) if f.get("kind") == "ack_applied"]
        af_wires = [f for f in r.get("feedback", []) if f.get("kind") == "wire" and f.get("channel") == "af"]
        credit_wires = [f for f in r.get("feedback", []) if f.get("kind") == "wire" and f.get("channel") == "credit"]
        query_wires = []  # QC18 queries are sent as reserved control datagrams on the forward gateway wire.
        clean = (not r.get("unresolved_ids") and not r.get("unresolved_candidate") and not r.get("unresolved_candidate_readers")
                 and not r.get("unresolved_encoder_pending") and not r.get("unresolved_ingress")
                 and not r.get("unresolved_receiver_readers") and not r.get("unresolved_decode")
                 and all(x is None for x in r.get("unresolved_sender_slots", []))
                 and not gw.get("outstanding_tokens") and not gw.get("control_outstanding"))
        bounded = (gw.get("peak_mailbox", 999) <= 6 and gw.get("peak_tokens", 999) <= 6 and gw.get("peak_control", 999) <= 1
                   and r.get("peak_sender", 999) <= 3 and r.get("peak_ingress", 999) <= 2
                   and r.get("peak_framebuffers", 999) <= 3 and r.get("peak_feedback", 999) <= 4)
        accounting = (data_packets == applied
                      and r.get("forward_ipv4_udp_bytes") == sum(w.get("bytes", 0) for w in wire)
                      and r.get("reverse_ipv4_udp_bytes") == sum(f.get("bytes", 0) for f in r.get("feedback", []) if f.get("kind") == "wire"))
        protocol_lengths = (all(f.get("bytes") == 57 for f in credit_wires)
                            and all(f.get("bytes") == 71 for f in af_wires)
                            and all(f.get("bytes") == 56 for f in query_wires)
                            and all(w.get("bytes") == 56 for w in wire if w.get("control")))
        decoded_ids = {p.get("id") for p in r.get("commits", [])}
        publication_separate = (len(ack_rows) < data_packets
                                and all(f.get("id") in decoded_ids and f.get("at_ms", 0) >= next((p.get("decode_done_ms", 0) for p in r.get("packets", []) if p.get("id") == f.get("id")), float("inf"))
                                        for f in ack_rows))
        rejected = [p for p in r.get("packets", []) if not p.get("committed")]
        rejects_clean = all(not p.get("admitted") and "packet_sha256" not in p and p.get("discard_service_ms", 0) >= 0
                            and not any(w.get("id") == p.get("id") and not w.get("control") for w in wire)
                            and not any(f.get("kind") == "ack_applied" and f.get("id") == p.get("id") for f in r.get("feedback", []))
                            for p in rejected)
        exact_ui = all(x.get("selected_ui_mismatches") == 0 for x in r.get("commits", []))
        if not clean: errors.append(f"{c.get('profile')}: unresolved object/lease/credit state")
        if not bounded: errors.append(f"{c.get('profile')}: finite queue bounds failed")
        if not accounting: errors.append(f"{c.get('profile')}: data datagram/credit/IP-UDP byte accounting mismatch")
        if not protocol_lengths: errors.append(f"{c.get('profile')}: PC18/QC18/AF03 wrapped wire lengths mismatch")
        if not publication_separate: errors.append(f"{c.get('profile')}: AF publication ACK is not separate from packet credits/decode")
        if not rejects_clean: errors.append(f"{c.get('profile')}: candidate discard was sent or acknowledged")
        if not exact_ui: errors.append(f"{c.get('profile')}: decoded UI words mismatch")
        per_case.append({"profile": c.get("profile"), "captures": r.get("capture_count"), "built": len(r.get("packets", [])),
                         "committed": sum(bool(p.get("committed")) for p in r.get("packets", [])), "precommit_rejected": len(rejected),
                         "actual_data_datagrams": data_packets, "consumed_packet_credits": applied, "AF03_publication_acks": len(ack_rows),
                         "packet_credit_records_including_duplicate_reports": len(gw.get("credits", [])),
                         "AF03_wire_records": len(af_wires), "packet_credit_wire_records": len(credit_wires), "query_wire_records": len(query_wires),
                         "control_datagrams": controls, "selected_ui_words": sum(x.get("selected_exact_pixels", 0) for x in r.get("commits", [])),
                         "forward_ipv4_udp_bytes": r.get("forward_ipv4_udp_bytes"), "reverse_ipv4_udp_bytes": r.get("reverse_ipv4_udp_bytes"),
                         "paid_rejected_build_ms": summary.get(c.get("profile"), {}).get("paid_rejected_build_ms"),
                         "diagnostic_ids_per_second": r.get("diagnostic_ids_per_second"),
                         "distinct_decoded_hashes_in_diagnostic_window": summary.get(c.get("profile"), {}).get("distinct_steady_decoded_hashes"),
                         "bounded_and_drained": bounded and clean, "credits_distinct_from_decoded_publication": publication_separate,
                         "wrapped_wire_lengths_valid": protocol_lengths})
    expected = {"unbudgeted": (85, 0), "admit200": (83, 0), "admit150_batch8": (70, 15), "admit200_link4": (58, 21),
                "lost_credit_query": (80, 0), "lost_refresh_AF": (84, 0)}
    for name, values in expected.items():
        s = summary.get(name, {})
        if (s.get("committed"), s.get("precommit_rejected")) != values: errors.append(f"joint profile outcome mismatch: {name}")
    if summary.get("admit200", {}).get("precommit_rejected") != 0: errors.append("admit200 does not retain all built candidates")
    # Avoid treating repeated synthetic outputs as a frame-rate result.
    synthetic_distinct = [summary.get(n, {}).get("distinct_steady_decoded_hashes") for n in ("forward_loss", "corrupt_AF")]
    if synthetic_distinct != [8, 8]: errors.append("synthetic repeated-frame identity scope changed")
    text = " ".join(data.get(k, "") for k in ("wire_scope", "service_scope", "state_scope", "source_scope", "excluded_scope"))
    required_scopes = ("1055byteUDPdatagrammaxwithin1065DMA", "ESP240MHz60%CPU", "consumedcreditnotdecodedpub",
                       "noISA/RFcalibration", "NoESPheap/BRAM/DSPfit")
    if not all(s in text for s in required_scopes): errors.append("joint wire/CPU/hardware scope declarations missing")
    analysis_path = directory / "analysis.json"
    analyzer_path = directory / "analyze.py"
    try: supplemental = json.loads(analysis_path.read_text())
    except (OSError, json.JSONDecodeError): supplemental = {}
    analysis_bound = (supplemental.get("results_sha256") == sha256(directory / "results.json")
                      and supplemental.get("analyzer_sha256") == sha256(analyzer_path)) if analyzer_path.is_file() else False
    if not analysis_bound: errors.append("joint supplemental analysis is not bound to current results/analyzer")
    ingress = {p.get("profile"): p.get("ingress_diagnosis", {}) for p in supplemental.get("profiles", [])}
    busy_rows = {name: ingress.get(name, {}) for name in ("unbudgeted", "admit200", "admit150_batch8", "admit200_link4", "lost_credit_query", "lost_refresh_AF")}
    busy_diagnosis_valid = all(d.get("observed_peak_ingress_slots") == 2
                               and not d.get("busy_ids_without_receiver_nack")
                               and not d.get("nack_ids_without_busy")
                               and "partial-frame occupancy" in d.get("scope", "")
                               and "not proven" in d.get("scope", "")
                               for d in busy_rows.values())
    if not busy_diagnosis_valid: errors.append("joint busy-ingress/NACK evidence or its limitations mismatch")
    try:
        analyzed = subprocess.run([sys.executable, "analyze.py", "--check"], cwd=directory, text=True, capture_output=True, timeout=120)
        analysis_replay = {"status": "pass" if analyzed.returncode == 0 else "fail", "returncode": analyzed.returncode,
                           "stdout": analyzed.stdout.strip(), "stderr": analyzed.stderr.strip()}
    except Exception as exc:
        analysis_replay = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if analysis_replay["status"] != "pass": errors.append("joint supplemental analysis --check failed")
    # Re-run the inexpensive retained-evidence verifier once per audit load (never the benchmark).
    try:
        run = subprocess.run([sys.executable, "verify.py"], cwd=directory, text=True, capture_output=True, timeout=120)
        verifier = {"status": "pass" if run.returncode == 0 else "fail", "returncode": run.returncode,
                    "stdout": run.stdout.strip(), "stderr": run.stderr.strip()}
    except Exception as exc:
        verifier = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if verifier["status"] != "pass": errors.append("joint deterministic retained-evidence verifier failed")
    return {"status": "verified" if not errors else "invalid", "case_count": len(cases), "source_pin_count": len(data.get("source_sha256", {})),
            "capture_count": sum(c.get("result", {}).get("capture_count", 0) for c in cases), "per_case": per_case,
            "summary": summary, "native_wall_seconds": data.get("python_wall_seconds"),
            "python_reference_not_ESP_CPU_or_physical_FPS": True,
            "supplemental_analysis_hash_bound": analysis_bound, "analysis_replay": analysis_replay,
            "busy_ingress_diagnosis": {name: {"rejected_feed_operations": d.get("total_rejected_feed_operations"),
                                               "busy_feed_operations": d.get("busy_feed_operations"),
                                               "affected_owner_ids": d.get("busy_affected_owner_ids"),
                                               "terminal_nack_count": d.get("receiver_nack_count"),
                                               "observed_peak_ingress_slots": d.get("observed_peak_ingress_slots"),
                                               "scope": d.get("scope")}
                                        for name, d in busy_rows.items()},
            "busy_ingress_diagnosis_valid_with_limits": busy_diagnosis_valid,
            "wire_scope": data.get("wire_scope"), "service_scope": data.get("service_scope"),
            "verifier_replay": verifier, "errors": errors}


def audit_study(key: str, rel_dir: str) -> dict:
    directory = ROOT / rel_dir
    result = {"status": "pending", "path": rel_dir, "artifacts": {}, "source_pins": [], "errors": []}
    if key not in READY_STUDIES:
        result["errors"].append("awaiting explicit final evidence signal")
        return result
    if not directory.is_dir():
        result.update(status="invalid")
        result["errors"].append("study directory missing after final signal")
        return result
    for name in ("README.md", "results.json", "tests.log", "run.log", "verify.log"):
        path = directory / name
        result["artifacts"][name] = {"present": path.is_file(), "sha256": sha256(path) if path.is_file() else None}
    result["test_log"] = test_log(directory / "tests.log")
    result_path = directory / "results.json"
    if not result_path.is_file():
        result["errors"].append("results.json missing after final signal")
        result["status"] = "invalid"
        return result
    try:
        data = json.loads(result_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(f"results.json unreadable: {exc}")
        result["status"] = "invalid"
        return result
    result["result_sha256"] = sha256(result_path)
    result["schema"] = {"top_level_type": type(data).__name__, "top_level_keys": sorted(data) if isinstance(data, dict) else []}
    result["result_summary"] = {k: data[k] for k in ("study", "evidence", "case_count", "frame_count", "event_count", "status") if isinstance(data, dict) and k in data}
    pins = data.get("source_sha256", {}) if isinstance(data, dict) else {}
    if not isinstance(pins, dict) or not pins:
        result["errors"].append("source_sha256 map missing or empty")
    else:
        for raw, expected in sorted(pins.items()):
            path = resolve_pin(raw)
            actual = sha256(path) if path.is_file() else None
            entry = {"path": portable(path), "expected": expected, "actual": actual, "matches": actual == expected}
            result["source_pins"].append(entry)
            if not entry["matches"]:
                result["errors"].append(f"source hash pin missing or mismatched: {entry['path']}")
    expected_pins = {"candidate_commit": 42, "ar03_trace": 43}
    expected_pins["joint_admission"] = 49
    if key in expected_pins and len(pins) != expected_pins[key]:
        result["errors"].append(f"source pin count mismatch: expected {expected_pins[key]}, found {len(pins)}")
    if key == "candidate_commit":
        result["analysis"] = audit_candidate(data)
    elif key == "ar03_trace":
        result["analysis"] = audit_trace(data, directory)
    elif key == "joint_admission":
        result["artifacts"]["analysis.json"] = {"present": (directory / "analysis.json").is_file(),
                                                    "sha256": sha256(directory / "analysis.json") if (directory / "analysis.json").is_file() else None}
        result["artifacts"]["analyze.py"] = {"present": (directory / "analyze.py").is_file(),
                                               "sha256": sha256(directory / "analyze.py") if (directory / "analyze.py").is_file() else None}
        result["analysis"] = audit_joint(data, directory)
    else:
        result["analysis"] = {"status": "pending_review", "note": "awaiting final schema-specific checks"}
    if result["analysis"].get("status") == "invalid":
        result["errors"].extend(result["analysis"].get("errors", []))
    if result["test_log"]["status"] != "pass":
        result["errors"].append("study test log missing or not a passing unittest log")
    if key == "candidate_commit" and result["test_log"].get("passed_count") != 13:
        result["errors"].append("candidate study test count is not 13")
    if key == "ar03_trace" and result["test_log"].get("passed_count") != 8:
        result["errors"].append("AR03 trace study test count is not 8")
    if key == "joint_admission" and result["test_log"].get("passed_count") != 16:
        result["errors"].append("joint study test count is not 16")
    result["status"] = "verified" if not result["errors"] and result["analysis"].get("status") == "verified" else (
        "pending" if not result["errors"] else "invalid")
    if result["status"] == "pending": result["errors"].append("final evidence present; semantic audit remains pending")
    return result


def load_audit() -> dict:
    results = {key: audit_study(key, path) for key, path in STUDIES.items()}
    status = "verified" if all(x["status"] == "verified" for x in results.values()) else (
        "invalid" if any(x["status"] == "invalid" for x in results.values()) else "pending")
    return {"audit": "python-game-v18-evidence-audit", "target": TARGET, "status": status,
            "final_signals_received": READY_STUDIES == set(STUDIES), "results": results,
            "scope": ["No hardware, cycle-accuracy, calibrated ESP, or RF claims.",
                      "Dropped or duplicated-template records are not FPS evidence."]}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="recompute without writing audit.json")
    args = parser.parse_args()
    rendered = json.dumps(load_audit(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not AUDIT_PATH.is_file() or AUDIT_PATH.read_text() != rendered:
            print("audit.json differs from recomputed evidence")
            return 1
        print("audit.json matches recomputed evidence")
        return 0
    AUDIT_PATH.write_text(rendered)
    print(rendered, end="")
    return 0 if json.loads(rendered)["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
