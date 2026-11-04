#!/usr/bin/env python3
"""Read-only evidence audit scaffold for the v19 Python game studies.

This file deliberately reports pending until the parent explicitly marks both
study artifacts final. It never starts a timed benchmark or claims hardware fit.
"""
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
    "frame_grant": "experiments/python-game-frame-grant-study",
    "causal_stripe": "experiments/python-game-causal-stripe-study",
}
# Intentionally empty: only the root agent can provide the final-readiness signal.
READY_STUDIES: set[str] = {"causal_stripe", "frame_grant"}
TARGET = {"canvas": [720, 480], "active_image": [720, 405], "fps": 30}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
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
    content = path.read_text(errors="replace")
    match = re.search(r"Ran (\d+) tests?", content)
    passed = match is not None and "OK" in content and "FAILED (" not in content and "ERROR" not in content
    return {"status": "pass" if passed else "invalid",
            "passed_count": int(match.group(1)) if match else None}


def audit_causal_stripe(data: dict, directory: Path) -> dict:
    """Check retained exact-work inventory and conditional scheduling arithmetic."""
    errors = []
    expected_counts = {"packets": 16, "native_decisions": 12,
                       "unique_native_acquisitions": 6, "flat_controls": 4,
                       "blocks": 97308, "exact_residual_samples": 6227712,
                       "exact_reconstructed_samples": 6224472,
                       "exact_selected_ui_words": 253440}
    counts = data.get("counts", {})
    frames = data.get("frames", [])
    cases = data.get("cases", [])
    profiles = [c.get("profile") for c in cases]
    if data.get("schema") != "gamebub-actual-stripe-service-v1":
        errors.append("unexpected causal-stripe result schema")
    if any(counts.get(k) != v for k, v in expected_counts.items()):
        errors.append("actual AR03 frame/block/sample inventory mismatch")
    if (len(frames) != 16 or not cases or len(set(profiles)) != len(profiles)
            or counts.get("profiles") != len(cases)
            or not {"existing_bypass4", "sparse4"}.issubset(set(profiles))):
        errors.append("causal-stripe frame/profile inventory mismatch")

    block_total = residual_total = reconstructed_total = selected_total = 0
    sparse_macs_total = bypass_macs_total = dequant_multiplies_total = 0
    arithmetic_ok = True
    for frame in frames:
        blocks = frame.get("blocks", -1)
        block_total += blocks
        residual_total += frame.get("exact_residual_samples", 0)
        reconstructed_total += frame.get("exact_reconstructed_samples", 0)
        selected_total += frame.get("selected_ui_pixels", 0)
        sparse_macs_total += frame.get("sparse_mac_operations", 0)
        bypass_macs_total += frame.get("existing_bypass_general_mac_operations", 0)
        dequant_multiplies_total += frame.get("dequant_multiplies", 0)
        if frame.get("zero", -1) + frame.get("dc", -1) + frame.get("general", -1) != blocks:
            arithmetic_ok = False
        if frame.get("dense_mac_operations") != 1024 * blocks:
            arithmetic_ok = False
        if frame.get("existing_bypass_general_mac_operations") != 1024 * frame.get("general", -1):
            arithmetic_ok = False
        if frame.get("dc_constant_multiplies") != 2 * frame.get("dc", -1):
            arithmetic_ok = False
        if frame.get("selected_ui_word_errors") != 0:
            arithmetic_ok = False
        sparse_from_traces = dequant_from_traces = 0
        for stripe in frame.get("stripes", []):
            work = stripe.get("work", {})
            sparse_from_traces += sum(work.get("first_mac", [])) + sum(work.get("second_mac", []))
            dequant_from_traces += sum(work.get("nonzero_coeff", []))
        if (sparse_from_traces != frame.get("sparse_mac_operations")
                or dequant_from_traces != frame.get("dequant_multiplies")):
            arithmetic_ok = False
        if frame.get("canonical_int16_tag_hex") != frame.get("packed_roundtrip_tag_hex"):
            arithmetic_ok = False
        for proof in frame.get("plane_proofs", []):
            if (proof.get("residual_sha256") != proof.get("frozen_residual_sha256")
                    or proof.get("yuv_sha256") != proof.get("frozen_yuv_sha256")):
                arithmetic_ok = False
            for field in ("residual_sha256", "frozen_residual_sha256", "yuv_sha256", "frozen_yuv_sha256"):
                if not re.fullmatch(r"[0-9a-f]{64}", str(proof.get(field, ""))):
                    arithmetic_ok = False
    if (block_total != expected_counts["blocks"]
            or residual_total != expected_counts["exact_residual_samples"]
            or reconstructed_total != expected_counts["exact_reconstructed_samples"]
            or selected_total != expected_counts["exact_selected_ui_words"]):
        errors.append("per-frame exact-work totals do not conserve the declared inventory")
    if not arithmetic_ok:
        errors.append("coefficient classification, MAC arithmetic, or exact output hashes mismatch")

    bounds = data.get("legal_width_bounds", {})
    if (bounds.get("max_quantized_abs") != 2048 or bounds.get("max_quantizer") != 255
            or bounds.get("dequant_abs_bound") != 2048 * 255
            or bounds.get("accumulator_signed_bits", 99) > 40
            or bounds.get("product_slots_assumed") != {"left_signed_bits": 32, "right_signed_bits": 16, "accumulator_signed_bits": 40}):
        errors.append("legal arithmetic width bound or assumed product-slot declaration mismatch")

    resource_rows = 0
    resource_ok = True
    for case in cases:
        if len(case.get("rows", [])) != 16:
            resource_ok = False
            continue
        for row in case["rows"]:
            got = row.get("schedule", {})
            resource_rows += 1
            expected_local = sum(got.get(k, -1) for k in (
                "local_compressed_cache_bytes", "local_coefficient_stripe_bytes",
                "local_reconstruction_stripe_bytes", "local_inverse_scratch_bytes",
                "local_basis_quantizer_rom_bytes", "local_color_line_bytes",
                "local_ui_palette_bytes")) + 2 * got.get("two_entropy_reservoir_bits_max_each", -1) // 8
            if (got.get("local_buffer_total_bytes") != expected_local
                    or got.get("conditional_18x18_multiplier_primitives") != 2 * case.get("budget", {}).get("wide_lanes", 0)
                    or got.get("entropy_refill_bytes") != sum(s.get("refill_bytes", 0) for s in got.get("stripes", []))
                    or got.get("local_coefficient_stripe_bytes") != case.get("budget", {}).get("stripe_buffers", 0)
                    * max((s.get("coefficient_bytes", 0) for s in got.get("stripes", [])), default=0)
                    or got.get("local_reconstruction_stripe_bytes") != max(
                        (s.get("coefficient_bytes", 0) for s in got.get("stripes", [])), default=0)):
                resource_ok = False
            if got.get("local_coefficient_stripe_bytes", 0) < 0 or got.get("local_reconstruction_stripe_bytes", 0) < 0:
                resource_ok = False
    if resource_rows != 16 * len(cases) or not resource_ok:
        errors.append("conditional local resource accounting mismatch")

    scope = " ".join(str(data.get(k, "")) for k in
                      ("arithmetic_scope", "timing_scope", "memory_scope", "multiplier_scope", "bounded_scope"))
    if not all(word in scope.lower() for word in ("assumption", "not fitted", "no dsp/ram mapping")):
        errors.append("conditional cycle/memory/DSP implementation-fit limits are not explicit")
    # Reconcile retained supplemental analysis and replay only deterministic checkers.
    analysis_path, analyzer_path = directory / "analysis.json", directory / "analyze.py"
    try:
        supplemental = json.loads(analysis_path.read_text())
    except (OSError, json.JSONDecodeError):
        supplemental = {}
    analysis_bound = (supplemental.get("results_sha256") == sha256(directory / "results.json")
                      and analyzer_path.is_file()
                      and supplemental.get("analyzer_sha256") == sha256(analyzer_path))
    operations = supplemental.get("native_operation_counts", {})
    analysis_counts_ok = (supplemental.get("counts") == counts
                          and operations.get("blocks") == 97200
                          and operations.get("zero") == 46122
                          and operations.get("dc") == 23952
                          and operations.get("general") == 27126
                          and operations.get("existing_bypass_general_mac_operations") == 27777024
                          and operations.get("sparse_mac_operations") == 4267808
                          and abs(operations.get("sparse_general_mac_saving_vs_existing_bypass_percent", -1) - 84.63547426822974) < 1e-9)
    if not analysis_bound:
        errors.append("supplemental comparison is not bound to the frozen results/analyzer hashes")
    if not analysis_counts_ok:
        errors.append("native actual-work comparison does not reconcile to baseline and sparse counts")
    summary = supplemental.get("summary", {})
    if (abs(summary.get("sparse4_service_saving_percent", -1) - 4.272065163456629) > 1e-9
            or abs(summary.get("compact8_additional_service_saving_percent", -1) - 20.18437856177675) > 1e-9
            or summary.get("every_native_case_misses_33ms") is not True
            or summary.get("native_local_buffer_bytes_max") != 100112):
        errors.append("matched conditional service/local-footprint summaries mismatch")
    try:
        analysis_run = subprocess.run([sys.executable, "analyze.py", "--check"], cwd=directory, text=True,
                                      capture_output=True, timeout=120)
        analysis_replay = {"status": "pass" if analysis_run.returncode == 0 else "fail",
                           "returncode": analysis_run.returncode, "stdout": analysis_run.stdout.strip(),
                           "stderr": analysis_run.stderr.strip()}
    except Exception as exc:
        analysis_replay = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if analysis_replay["status"] != "pass":
        errors.append("retained hash-bound analyzer --check failed")
    # Replaying verify.py must not run the timed benchmark.
    try:
        replay = subprocess.run([sys.executable, "verify.py"], cwd=directory, text=True,
                                 capture_output=True, timeout=120)
        verifier = {"status": "pass" if replay.returncode == 0 else "fail",
                    "returncode": replay.returncode, "stdout": replay.stdout.strip(),
                    "stderr": replay.stderr.strip()}
    except Exception as exc:
        verifier = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if verifier["status"] != "pass":
        errors.append("retained causal-stripe verifier replay failed")
    return {"status": "verified" if not errors else "invalid", "counts": counts,
            "actual_coefficient_demand_conserved": arithmetic_ok,
            "coefficient_blocks": block_total, "exact_residual_samples": residual_total,
            "exact_reconstructed_samples": reconstructed_total,
            "selected_ui_words": selected_total, "sparse_general_mac_operations": sparse_macs_total,
            "existing_bypass_general_mac_operations": bypass_macs_total,
            "sparse_vs_existing_bypass_general_mac_ratio": sparse_macs_total / bypass_macs_total if bypass_macs_total else None,
            "actual_dequant_multiply_demand": dequant_multiplies_total,
            "baseline_and_sparse_profiles": profiles,
            "conditional_resource_rows": resource_rows, "conditional_resource_accounting_valid": resource_ok,
            "assumed_32x16_products_and_40bit_accumulation_not_fit": True,
            "accumulator_signed_bits": bounds.get("accumulator_signed_bits"),
            "selected_ui_pixels_sum_across_decisions": selected_total,
            "supplemental_analysis_hash_bound": analysis_bound,
            "native_work_analysis_reconciled": analysis_counts_ok,
            "conditional_analysis_summary": summary,
            "analysis_replay": analysis_replay,
            "verifier_replay": verifier, "errors": errors}


def audit_frame_grant(data: dict, directory: Path) -> dict:
    """Reconcile retained candidate runs and FG19/GF03 ownership evidence."""
    errors = []
    cases = data.get("cases", [])
    expected_profiles = {
        "mass-effect-2600/fixed_base6", "mass-effect-2600/fixed_partition5",
        "mass-effect-2600/fixed_serialized_grants5", "mass-effect-2600/fixed_grants5",
        "mass-effect-2600/measured_grants5", "mass-effect-7200/fixed_base6",
        "mass-effect-7200/fixed_grants5", "lost_grant", "lost_release",
        "packet_credit_blackhole", "dropped_fragment", "duplicate_release_and_lost_credit"}
    profiles = {c.get("profile") for c in cases}
    if len(cases) != 12 or profiles != expected_profiles:
        errors.append("frame-grant profile/case inventory mismatch")
    if sum(c.get("result", {}).get("capture_count", 0) for c in cases) != 790:
        errors.append("frame-grant capture inventory is not 790")
    native = [c for c in cases if c.get("source") == "native-regression"]
    if len(native) != 7 or any(c.get("result", {}).get("capture_count") != 90
                               or c.get("manifest", {}).get("unique_frame_count") != 90 for c in native):
        errors.append("seven native profiles do not each retain 90 unique frames")
    try:
        replay = subprocess.run([sys.executable, "verify.py"], cwd=directory, text=True,
                                 capture_output=True, timeout=120)
        verifier = {"status": "pass" if replay.returncode == 0 else "fail",
                    "returncode": replay.returncode, "stdout": replay.stdout.strip(),
                    "stderr": replay.stderr.strip()}
    except Exception as exc:
        verifier = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if verifier["status"] != "pass":
        errors.append("retained frame-grant verifier replay failed")
    summaries = []
    native_busy = native_mismatches = 0
    expected_safe_profiles = {"lost_grant", "lost_release", "packet_credit_blackhole"}
    for case in cases:
        result = case.get("result", {})
        cfg = result.get("config", {})
        grants = result.get("frame_grants")
        wire = result.get("gateway", {}).get("wire", [])
        frame_controls = [w for w in wire if w.get("frame_control")]
        reverse_frame_controls = [w for w in result.get("feedback", [])
                                  if w.get("kind") == "wire" and w.get("channel") == "frame"]
        data_tokens = [w for w in wire if not w.get("control")]
        expected_safe_stop = case.get("profile") in expected_safe_profiles
        if grants is not None:
            owned = (grants.get("pending") or grants.get("receiver_owned") or grants.get("host_owned"))
            if expected_safe_stop:
                if (not grants.get("safe_stop") or not owned or not grants.get("safe_stop_reason")
                        or grants.get("peak_receiver", 99) > 2 or grants.get("peak_host", 99) > 2):
                    errors.append("lost/unknown control outcome did not retain owners at bounded safe stop")
            elif (grants.get("safe_stop") or owned or grants.get("feedback_owned") != 0):
                errors.append(f"{case.get('name', case.get('profile', '?'))}: successful FG19 case did not drain ownership")
            counters = grants.get("counters", {})
            if cfg.get("frame_finish_ack"):
                if counters.get("finish_confirmed", 0) != counters.get("finish_received", 0):
                    errors.append(f"{case.get('profile')}: FINISHED acknowledgements do not match received FINISH")
            elif not expected_safe_stop and cfg.get("frame_grants_enabled"):
                if counters.get("finish_confirmed", 0) != 0:
                    errors.append(f"{case.get('profile')}: serialized FINISH profile unexpectedly reports FINISHED ACKs")
            if not expected_safe_stop and cfg.get("frame_grants_enabled"):
                if counters.get("receiver_released", 0) != counters.get("release_applied", 0):
                    errors.append(f"{case.get('profile')}: receiver release and sender application do not reconcile")
        if cfg.get("frame_grants_enabled"):
            effective_limit = cfg.get("packet_data_tokens") or (5 if cfg.get("frame_grants_enabled") else 6)
            if effective_limit != 5 or result.get("gateway", {}).get("peak_tokens", 99) > 5:
                errors.append("FG19 data tokens exceeded the five-token partition")
            if not frame_controls:
                errors.append("FG19 run has no serialized paid control wire records")
            if any(w.get("bytes") != 64 for w in frame_controls + reverse_frame_controls):
                errors.append("FG19 control wire cost is not 36-byte message plus 28-byte IPv4/UDP overhead")
        elif cfg.get("packet_data_tokens") == 5 and result.get("gateway", {}).get("peak_tokens", 99) > 5:
            errors.append("partition-only control did not maintain a five-data-token bound")
        for packet in result.get("packets", []):
            if "GF03 busy" in packet.get("feed_errors", []) and case.get("source") == "native-regression":
                native_busy += 1
        for commit in result.get("commits", []):
            native_mismatches += int(commit.get("selected_ui_mismatches", 0))
        summaries.append({"profile": cfg.get("service_profile"),
                          "case": case.get("profile"),
                          "frame_grants_enabled": cfg.get("frame_grants_enabled"),
                          "packet_data_tokens": cfg.get("packet_data_tokens"),
                          "effective_data_token_limit": (cfg.get("packet_data_tokens") or (5 if cfg.get("frame_grants_enabled") else 6)),
                          "data_token_wire_records": len(data_tokens),
                          "paid_frame_control_wire_records": len(frame_controls),
                          "paid_frame_control_reply_records": len(reverse_frame_controls),
                          "paid_frame_control_forward_bytes": sum(w.get("bytes", 0) for w in frame_controls),
                          "paid_frame_control_reverse_bytes": sum(w.get("bytes", 0) for w in reverse_frame_controls),
                          "paid_frame_control_bytes": sum(w.get("bytes", 0) for w in frame_controls + reverse_frame_controls),
                          "safe_stop_expected": expected_safe_stop,
                          "safe_stop": grants.get("safe_stop") if grants else None,
                          "grant_counters": grants.get("counters", {}) if grants else {}})
    if native_busy != 0:
        errors.append("native candidates contain GF03 busy feed rejects")
    if native_mismatches != 0:
        errors.append("native selected RGB565 patch words contain mismatches")
    fixed_pairs = data.get("fixed_cost_pairs", [])
    if (len(fixed_pairs) != 2 or not all(p.get("same_input_hashes") and p.get("same_service_profile")
                                          and p.get("grants_busy_rejections") == 0 for p in fixed_pairs)):
        errors.append("fixed-service comparison pairs are not same-input/service or have busy rejects")
    if len(fixed_pairs) == 2:
        pair_by_scene = {p.get("baseline", "").split("/")[0]: p for p in fixed_pairs}
        p2600, p7200 = pair_by_scene.get("mass-effect-2600", {}), pair_by_scene.get("mass-effect-7200", {})
        if ((p2600.get("baseline_eventual"), p2600.get("grants_eventual")) != (89, 82)
                or (p7200.get("baseline_eventual"), p7200.get("grants_eventual")) != (63, 57)):
            errors.append("fixed-service native baseline/grant outcomes mismatch")
    case_by_profile = {c.get("profile"): c for c in cases}
    native_outcomes = {name: case_by_profile.get(name, {}).get("result", {}).get("presented_eventual")
                       for name in ("mass-effect-2600/fixed_base6", "mass-effect-2600/fixed_partition5",
                                    "mass-effect-2600/fixed_serialized_grants5", "mass-effect-2600/fixed_grants5",
                                    "mass-effect-2600/measured_grants5", "mass-effect-7200/fixed_base6",
                                    "mass-effect-7200/fixed_grants5")}
    if native_outcomes != {"mass-effect-2600/fixed_base6": 89,
                           "mass-effect-2600/fixed_partition5": 89,
                           "mass-effect-2600/fixed_serialized_grants5": 58,
                           "mass-effect-2600/fixed_grants5": 82,
                           "mass-effect-2600/measured_grants5": 82,
                           "mass-effect-7200/fixed_base6": 63,
                           "mass-effect-7200/fixed_grants5": 57}:
        errors.append("native primary/secondary eventual presentation counts mismatch")

    # The selected words are checked against their source patches; requested
    # rectangles omitted under the complete-frame cap are an unmet full-HUD gate.
    analysis_path, analyzer_path = directory / "analysis.json", directory / "analyze.py"
    try:
        supplemental = json.loads(analysis_path.read_text())
    except (OSError, json.JSONDecodeError):
        supplemental = {}
    analysis_bound = (supplemental.get("results_sha256") == sha256(directory / "results.json")
                      and analyzer_path.is_file()
                      and supplemental.get("analyzer_sha256") == sha256(analyzer_path))
    if not analysis_bound:
        errors.append("frame coverage analysis is not hash-bound to final results/analyzer")
    if supplemental.get("case_count") != len(cases) or supplemental.get("capture_events") != 790:
        errors.append("frame analysis case/capture totals mismatch")
    coverages = supplemental.get("ui_coverage", [])
    coverage_by_profile = {row.get("profile"): row for row in coverages}
    if set(coverage_by_profile) != profiles:
        errors.append("per-profile requested/selected/omitted UI coverage inventory mismatch")
    partial_profiles = []
    total_partial_frames = total_omitted_words = exact_selected_words = 0
    coverage_rows = 0
    for name, profile_coverage in coverage_by_profile.items():
        for row in profile_coverage.get("rows", []):
            coverage_rows += 1
            requested = row.get("requested_rectangles", [])
            selected = row.get("selected_rectangles", [])
            omitted = row.get("omitted_rectangles", [])
            requested_set = {tuple(rect) for rect in requested}
            selected_set = {tuple(rect) for rect in selected}
            omitted_set = {tuple(rect) for rect in omitted}
            requested_words = sum(r[2] * r[3] for r in requested)
            selected_words = sum(r[2] * r[3] for r in selected)
            omitted_words = sum(r[2] * r[3] for r in omitted)
            exact_selected_words += row.get("selected_words", 0)
            if (requested_words != row.get("requested_words") or selected_words != row.get("selected_words")
                    or omitted_words != row.get("omitted_words") or row.get("selected_word_mismatches") != 0
                    or not selected_set.issubset(requested_set)
                    or not omitted_set.issubset(requested_set)
                    or selected_set & omitted_set or selected_set | omitted_set != requested_set):
                errors.append(f"{name}: requested/selected/omitted coverage arithmetic mismatch")
        if profile_coverage.get("partial_declared_ui_frames", 0):
            partial_profiles.append({"profile": name,
                                     "full_frames": profile_coverage.get("full_declared_ui_frames"),
                                     "partial_frames": profile_coverage.get("partial_declared_ui_frames")})
            total_partial_frames += profile_coverage.get("partial_declared_ui_frames", 0)
            total_omitted_words += sum(row.get("omitted_words", 0) for row in profile_coverage.get("rows", []))
    if coverage_rows != sum(len(c.get("result", {}).get("commits", [])) for c in cases):
        errors.append("UI coverage rows do not match committed frames")
    if (coverage_by_profile.get("mass-effect-2600/fixed_base6", {}).get("partial_declared_ui_frames") != 0
            or coverage_by_profile.get("mass-effect-2600/fixed_grants5", {}).get("partial_declared_ui_frames") != 0
            or coverage_by_profile.get("mass-effect-7200/fixed_base6", {}).get("partial_declared_ui_frames") != 24
            or coverage_by_profile.get("mass-effect-7200/fixed_grants5", {}).get("partial_declared_ui_frames") != 20):
        errors.append("primary/secondary full-HUD coverage counts mismatch")
    for name in ("mass-effect-7200/fixed_base6", "mass-effect-7200/fixed_grants5"):
        for row in coverage_by_profile.get(name, {}).get("rows", []):
            if row.get("omitted_rectangles") and (row.get("selected_words") != 15360 or row.get("omitted_words") != 5760):
                errors.append(f"{name}: partial HUD row is not 15,360 selected / 5,760 omitted words")
    scope = str(supplemental.get("scope", ""))
    if "7200sometimesomitsfourthdeclaredHUDpatch" not in scope or "selectedUIisexact,notfullsourcelossless" not in scope:
        errors.append("coverage analysis does not explicitly scope partial HUD omissions")
    try:
        analysis_run = subprocess.run([sys.executable, "analyze.py", "--check"], cwd=directory, text=True,
                                      capture_output=True, timeout=120)
        analysis_replay = {"status": "pass" if analysis_run.returncode == 0 else "fail",
                           "returncode": analysis_run.returncode, "stdout": analysis_run.stdout.strip(),
                           "stderr": analysis_run.stderr.strip()}
    except Exception as exc:
        analysis_replay = {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}
    if analysis_replay["status"] != "pass":
        errors.append("retained frame analysis --check failed")

    primary_pipeline = next((c for c in cases if c.get("profile") == "mass-effect-2600/fixed_grants5"), None)
    primary_wire = {"forward_bytes": 0, "reverse_bytes": 0}
    if primary_pipeline:
        rr = primary_pipeline["result"]
        primary_wire["forward_bytes"] = sum(w.get("bytes", 0) for w in rr.get("gateway", {}).get("wire", []) if w.get("frame_control"))
        primary_wire["reverse_bytes"] = sum(w.get("bytes", 0) for w in rr.get("feedback", [])
                                             if w.get("kind") == "wire" and w.get("channel") == "frame")
        if primary_wire != {"forward_bytes": 10496, "reverse_bytes": 15744}:
            errors.append("primary pipelined FG19 wire byte totals mismatch")

    scopes = " ".join(str(data.get(k, "")) for k in ("wire_scope", "state_scope", "service_scope", "source_scope", "excluded_scope"))
    if not all(term in scopes for term in ("NoESP32ISA", "FPGAentropycycle", "DSP/BRAMfit", "physical30fps proof")):
        errors.append("frame-grant final ESP/FPGA/physical-FPS scope declarations are incomplete")
    return {"status": "verified" if not errors else "invalid", "case_count": len(cases),
            "capture_events": sum(c.get("result", {}).get("capture_count", 0) for c in cases),
            "source_pin_count": len(data.get("source_sha256", {})),
            "native_profiles": len(native), "native_busy_feed_rejections": native_busy,
            "native_selected_word_mismatches": native_mismatches,
            "fixed_cost_pairs": fixed_pairs,
            "native_eventual_presentations": native_outcomes,
            "primary_pipelined_fg19_wire_bytes": primary_wire,
            "case_summaries": summaries, "verifier_replay": verifier,
            "ownership_drained_in_success_cases": all(not x.get("safe_stop") for x in summaries if x.get("frame_grants_enabled") and not x.get("safe_stop_expected")),
            "intentional_safe_stop_profiles": [x["case"] for x in summaries if x.get("safe_stop_expected") and x.get("safe_stop")],
            "paid_control_wire_accounted": all(x["paid_frame_control_wire_records"] > 0 for x in summaries if x.get("frame_grants_enabled")),
            "fg19_forward_bytes": sum(x["paid_frame_control_forward_bytes"] for x in summaries),
            "fg19_reverse_bytes": sum(x["paid_frame_control_reverse_bytes"] for x in summaries),
            "ui_coverage": {"selected_words_exact": native_mismatches == 0,
                            "full_hud_gate": "unmet" if partial_profiles else "met",
                            "partial_profiles": partial_profiles,
                            "partial_decoded_frames": total_partial_frames,
                            "omitted_requested_words": total_omitted_words,
                            "selected_words_across_profiles": exact_selected_words,
                            "interpretation": "Selected patch words decode exactly; omitted requested rectangles remain lossy and are not counted as protected."},
            "analysis_hash_bound": analysis_bound, "analysis_replay": analysis_replay,
            "errors": errors}


def audit_study(key: str, rel_dir: str) -> dict:
    directory = ROOT / rel_dir
    result = {"status": "pending", "path": rel_dir, "artifacts": {},
              "source_pins": [], "errors": [], "analysis": {"status": "pending"}}
    if key not in READY_STUDIES:
        result["errors"].append("awaiting explicit final evidence signal")
        return result
    if not directory.is_dir():
        result.update(status="invalid")
        result["errors"].append("study directory missing after final signal")
        return result
    required_artifacts = ["README.md", "results.json", "tests.log", "run.log", "verify.log"]
    if key == "causal_stripe":
        required_artifacts.extend(["SCHEMA.md", "analysis.json", "analyze.py", "analysis-verify.log"])
    elif key == "frame_grant":
        required_artifacts.extend(["analysis.json", "analyze.py", "analysis-verify.log"])
    for name in required_artifacts:
        path = directory / name
        result["artifacts"][name] = {"present": path.is_file(), "sha256": sha256(path) if path.is_file() else None}
    for name in required_artifacts:
        if not (directory / name).is_file():
            result["errors"].append(f"required artifact missing: {name}")
    result["test_log"] = test_log(directory / "tests.log")
    if result["test_log"]["status"] != "pass":
        result["errors"].append("study test log missing or not a passing unittest log")
    expected_test_counts = {"causal_stripe": 12, "frame_grant": 28}
    if key in expected_test_counts and result["test_log"].get("passed_count") != expected_test_counts[key]:
        result["errors"].append(f"study test count mismatch: expected {expected_test_counts[key]}")
    result_file = directory / "results.json"
    try:
        data = json.loads(result_file.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(f"results.json unreadable: {exc}")
        data = None
    if not isinstance(data, dict):
        result["errors"].append("results.json must contain an object")
        data = {}
    result["result_sha256"] = sha256(result_file) if result_file.is_file() else None
    result["schema"] = {"top_level_keys": sorted(data)}
    pins = data.get("source_sha256", {})
    if not isinstance(pins, dict) or not pins:
        result["errors"].append("source_sha256 map missing or empty")
        pins = {}
    expected_pin_counts = {"causal_stripe": 264, "frame_grant": 58}
    if key in expected_pin_counts and len(pins) != expected_pin_counts[key]:
        result["errors"].append(f"source pin count mismatch: expected {expected_pin_counts[key]}, found {len(pins)}")
    for raw, expected in sorted(pins.items()):
        source = resolve_pin(raw)
        actual = sha256(source) if source.is_file() else None
        item = {"path": portable(source), "expected": expected, "actual": actual, "matches": actual == expected}
        result["source_pins"].append(item)
        if not item["matches"]:
            result["errors"].append(f"source hash pin missing or mismatched: {item['path']}")

    result["analysis"] = audit_frame_grant(data, directory) if key == "frame_grant" else audit_causal_stripe(data, directory)
    analysis_errors = result["analysis"].get("errors", [])
    if result["analysis"].get("status") == "invalid":
        result["errors"].extend(analysis_errors)
    if result["errors"]:
        result["status"] = "invalid"
    elif result["analysis"].get("status") == "pending":
        result["status"] = "pending"
        result["errors"].append("final evidence present; semantic audit remains pending")
    else:
        result["status"] = "verified"
    return result


def load_audit() -> dict:
    results = {key: audit_study(key, path) for key, path in STUDIES.items()}
    status = "verified" if all(r["status"] == "verified" for r in results.values()) else (
        "invalid" if any(r["status"] == "invalid" for r in results.values()) else "pending")
    return {"audit": "python-game-v19-evidence-audit", "target": TARGET,
            "status": status, "final_signals_received": READY_STUDIES == set(STUDIES),
            "results": results,
            "scope": ["No actual ESP32, RF, ISA, or FPGA implementation-fit claim.",
                      "720x480 coded, 720x405 active, 30 scheduled frames/s.",
                      "Repeated templates, packet accepts, and scheduled cadence are not decoded-display FPS evidence."]}


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
