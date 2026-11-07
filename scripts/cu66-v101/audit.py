#!/usr/bin/env python3
"""Independently audit V101 source scope and retained component evidence.

This reader uses only Python's standard library. It never launches simulators,
Vivado, synthesis, or implementation tools. PASS_EVIDENCE describes the bounded
receipts checked here; it is not V101 signoff or complete candidate qualification.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "e8bb1c9cc3cec6775cf128c8fd538a56f022575f"
PROFILE = "experiments/python-gamebub-v99/profile.json"
INVENTORY_PATH = "experiments/python-gamebub-v100/inventory.json"
V100_AUDIT_PATH = "experiments/python-gamebub-v100/audit.json"
PROFILE_SHA256 = "8e17b24afbefe32ca00b2606ee80a3a70dd06e9050e76d50c9698fd524e735be"
ORIGINAL_PATH = "fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv"
CANDIDATE_PATH = "fpga/experiments/cu66-v101-scratch/packed_scratch_v91g2.sv"
CANDIDATE_SHA256 = "ba0f184ae2f1a70b550208fa36535457c5115398a12a5f25ec7707426c5ee142"
OUT_PATH = "experiments/python-gamebub-v101/audit.json"

checks: list[dict] = []
errors: list[str] = []
input_hashes: dict[str, str] = {}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(relative: str) -> bytes:
    data = (ROOT / relative).read_bytes()
    input_hashes[relative] = sha(data)
    return data


def read_json(relative: str):
    return json.loads(read_bytes(relative))


def check(name: str, passed: bool, detail=None) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
    if not passed:
        errors.append(name)


def git_blob(revision: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{revision}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout if proc.returncode == 0 else None


def artifact_audit(attempt_dir: str, declared: dict) -> dict:
    missing, mismatched = [], []
    checked = 0
    for relative, expected in sorted(declared.items()):
        expected_hash = expected.get("sha256") if isinstance(expected, dict) else expected
        path = f"{attempt_dir}/{relative}"
        try:
            actual = sha(read_bytes(path))
        except FileNotFoundError:
            missing.append(relative)
            continue
        checked += 1
        if actual != expected_hash:
            mismatched.append(relative)
    return {"declared": len(declared), "checked": checked, "missing": missing, "mismatched": mismatched}


def selected_attempt(summary_path: str, expected_schema: str, expected_mode: str) -> tuple[dict, str, dict]:
    summary = read_json(summary_path)
    selected = summary.get("selected_report")
    if not selected:
        raise ValueError(f"{summary_path}: missing selected_report")
    report_path = str(Path(selected))
    report = read_json(report_path)
    report_dir = str(Path(report_path).parent)
    declared = report.get("artifacts_sha256", {})
    artifacts = artifact_audit(report_dir, declared)
    basic = (
        summary.get("status") == "PASS"
        and report.get("status") == "PASS"
        and report.get("schema") == expected_schema
        and report.get("mode") == expected_mode
        and report.get("baseline_revision") == BASELINE
        and report_path.startswith(f"experiments/python-gamebub-v101/regression/{expected_mode}/attempts/")
        and artifacts["declared"] == artifacts["checked"]
        and not artifacts["missing"]
        and not artifacts["mismatched"]
    )
    return summary, report_path, {"report": report, "artifacts": artifacts, "basic_ok": basic}


def audit_regression(mode: str) -> dict:
    summary_path = f"experiments/python-gamebub-v101/regression/{mode}/results.json"
    summary, report_path, loaded = selected_attempt(summary_path, "v101-paired-regression-v1", mode)
    report = loaded["report"]
    expected_cases, expected_directed = (6, 13) if mode == "fresh" else (22, 21)
    expected_seeds = report.get("seeds", [])
    runs = report.get("runs", [])
    rows = []
    all_ok = loaded["basic_ok"] and len(expected_seeds) == 2 and len(set(expected_seeds)) == 2 and len(runs) == 2
    compared_source_hashes = []
    source_mismatches = []
    for source_path, expected_hash in sorted(report.get("source_sha256", {}).items()):
        try:
            actual_hash = sha(read_bytes(source_path))
        except FileNotFoundError:
            actual_hash = None
        compared_source_hashes.append(source_path)
        if actual_hash != expected_hash:
            source_mismatches.append(source_path)
    all_ok &= not source_mismatches
    for row in runs:
        seed = row.get("seed")
        variants = row.get("variants", {})
        per_variant = {}
        for name in ("baseline", "candidate"):
            entry = variants.get(name, {})
            verdict = entry.get("verdict", {})
            one_ok = (
                verdict.get("status") == "TEST_PASS"
                and verdict.get("seed") == seed
                and verdict.get("cases") == expected_cases
                and verdict.get("directed_checks") == expected_directed
            )
            per_variant[name] = {
                "status": verdict.get("status"),
                "cases": verdict.get("cases"),
                "directed_checks": verdict.get("directed_checks"),
                "cycle_count": verdict.get("cycles", verdict.get("cycle_count")),
                "pass": one_ok,
            }
            all_ok &= one_ok
        eq = row.get("equalities", {})
        expected_equalities = {"stdout", "events"} | ({"canonical"} if mode == "canonical" else set())
        equality_ok = set(eq) >= expected_equalities and all(eq[k] is True for k in expected_equalities)
        all_ok &= equality_ok
        rows.append({"seed": seed, "variants": per_variant, "equalities": {k: eq.get(k) for k in sorted(expected_equalities)}, "equalities_pass": equality_ok})
    all_ok &= set(expected_seeds) == {row.get("seed") for row in runs}
    all_ok &= report.get("actual_RTL_run") is True
    all_ok &= report.get("assertions_disabled_or_downgraded") is False
    all_ok &= report.get("case_profile_runs") == expected_cases * 4
    all_ok &= report.get("directed_checks") == expected_directed * 4
    all_ok &= report.get("exact_same_seed_transcripts_events_cycles") is True
    check(
        f"{mode}_paired_regression_receipt_and_terminal_tests",
        all_ok,
        {
            "summary": summary_path,
            "attempt_report": report_path,
            "attempt_report_sha256": sha((ROOT / report_path).read_bytes()),
            "status": report.get("status"),
            "seeds": expected_seeds,
            "per_seed_variant_results": rows,
            "case_profile_runs": report.get("case_profile_runs"),
            "directed_checks_total": report.get("directed_checks"),
            "source_hashes_checked": len(compared_source_hashes),
            "source_hash_mismatches": source_mismatches,
            "artifact_hashes": loaded["artifacts"],
            "actual_RTL_run": report.get("actual_RTL_run"),
            "assertions_disabled_or_downgraded": report.get("assertions_disabled_or_downgraded"),
        },
    )
    return {
        "status": "PASS_EVIDENCE" if all_ok else "FAIL",
        "mode": mode,
        "summary": summary_path,
        "attempt_report": report_path,
        "attempt_report_sha256": sha((ROOT / report_path).read_bytes()),
        "seeds": expected_seeds,
        "per_seed_variant_results": rows,
        "case_profile_runs": report.get("case_profile_runs"),
        "directed_checks": report.get("directed_checks"),
        "artifact_audit": loaded["artifacts"],
        "scope_limit": "Paired Verilator behavioral component regression only; no full candidate, formal, mapped-netlist, RGB replay, board, or physical timing qualification.",
    }


def audit_source_scope() -> dict:
    inventory = read_json(INVENTORY_PATH)
    profile_bytes = read_bytes(PROFILE)
    baseline_exists = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).returncode == 0
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASELINE, "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).returncode == 0
    check("v100_baseline_commit_is_in_history", baseline_exists and ancestor, {"baseline": BASELINE, "commit_exists": baseline_exists, "is_ancestor": ancestor})

    profile_blob = git_blob(BASELINE, PROFILE)
    profile_current_hash = sha(profile_bytes)
    profile_ok = profile_blob == profile_bytes and profile_current_hash == PROFILE_SHA256
    check("frozen_research_profile_matches_v100_git_blob", profile_ok, {"path": PROFILE, "sha256": profile_current_hash, "baseline_blob_equal": profile_blob == profile_bytes, "frozen_profile_status": json.loads(profile_bytes).get("status")})

    source_rows = inventory.get("source_files", [])
    source_mismatches, baseline_mismatches, baseline_count = [], [], 0
    for row in source_rows:
        path = row.get("path", "")
        try:
            current = read_bytes(path)
        except FileNotFoundError:
            current = b""
        if not current or sha(current) != row.get("sha256"):
            source_mismatches.append(path)
        blob = git_blob(BASELINE, path)
        if blob is not None:
            baseline_count += 1
            if blob != current:
                baseline_mismatches.append(path)
    inventory_ok = bool(source_rows) and not source_mismatches and not baseline_mismatches and baseline_count == len(source_rows)
    check("all_v100_frozen_source_inventory_files_unchanged", inventory_ok, {"source_count": len(source_rows), "baseline_blobs_compared": baseline_count, "current_hash_mismatches": source_mismatches, "baseline_blob_mismatches": baseline_mismatches})

    original = read_bytes(ORIGINAL_PATH)
    original_blob = git_blob(BASELINE, ORIGINAL_PATH)
    candidate = read_bytes(CANDIDATE_PATH)
    original_hash = sha(original)
    candidate_hash = sha(candidate)
    # Prove that the V101 file differs only inside the approved priority-loop
    # span: the literal marker starts the replacement and the following RAW
    # extraction branch provides a stable, unique suffix boundary.
    old_start = b"                for(integer b=1;b<=3;b=b+1) begin\n"
    new_start = b"                // Fixed DC/band1/band2/band3 priority; preserve final band3 word address.\n"
    suffix = b"            end else if(state==RAW_EXTRACT && raw_mode &&\n"
    try:
        old_i = original.index(old_start)
        new_i = candidate.index(new_start)
        old_suffix_i = original.index(suffix, old_i)
        new_suffix_i = candidate.index(suffix, new_i)
        outside_equal = original[:old_i] == candidate[:new_i] and original[old_suffix_i:] == candidate[new_suffix_i:]
        loop_only = outside_equal and original_blob == original and candidate_hash == CANDIDATE_SHA256
        changed_span = {
            "original_start_line": original[:old_i].count(b"\n") + 1,
            "candidate_start_line": candidate[:new_i].count(b"\n") + 1,
            "original_span_lines": original[old_i:old_suffix_i].count(b"\n"),
            "candidate_span_lines": candidate[new_i:new_suffix_i].count(b"\n"),
            "prefix_and_suffix_byte_identical": outside_equal,
        }
    except ValueError:
        loop_only = False
        changed_span = {"prefix_and_suffix_byte_identical": False, "reason": "approved span anchors missing or ambiguous"}
    check("isolated_scratch_candidate_is_approved_loop_only_change", loop_only, {"original_path": ORIGINAL_PATH, "original_sha256": original_hash, "original_git_blob_equal": original_blob == original, "candidate_path": CANDIDATE_PATH, "candidate_sha256": candidate_hash, "expected_candidate_sha256": CANDIDATE_SHA256, "span": changed_span})

    return {
        "baseline_revision": BASELINE,
        "profile": {"path": PROFILE, "sha256": profile_current_hash, "unchanged_from_baseline": profile_ok},
        "v100_inventory": {"path": INVENTORY_PATH, "sha256": sha((ROOT / INVENTORY_PATH).read_bytes()), "source_files": len(source_rows), "all_source_hashes_and_blobs_match": inventory_ok},
        "approved_candidate": {"original_path": ORIGINAL_PATH, "original_sha256": original_hash, "original_blob_unchanged": original_blob == original, "candidate_path": CANDIDATE_PATH, "candidate_sha256": candidate_hash, "loop_only_change": loop_only, "changed_span": changed_span},
    }


def audit_constraints_ledger(ledger: dict) -> dict:
    path = "experiments/python-gamebub-v101/constraints/ledger.json"
    source_hashes = ledger.get("source_sha256", {})
    recipe_hashes = ledger.get("recipe_sha256", {})
    source_mismatches, source_baseline_mismatches = [], []
    for source, expected in sorted(source_hashes.items()):
        try:
            current = read_bytes(source)
        except FileNotFoundError:
            source_mismatches.append(source)
            continue
        if sha(current) != expected:
            source_mismatches.append(source)
        blob = git_blob(BASELINE, source)
        if blob is None or blob != current:
            source_baseline_mismatches.append(source)
    recipe_mismatches = []
    for recipe, expected in sorted(recipe_hashes.items()):
        try:
            current = read_bytes(recipe)
        except FileNotFoundError:
            recipe_mismatches.append(recipe)
            continue
        if sha(current) != expected:
            recipe_mismatches.append(recipe)

    component = ledger.get("component", {})
    board = ledger.get("board", {})
    gates = ledger.get("gates", {})
    static = {row.get("name"): row for row in ledger.get("static_checks", [])}
    obligations = {row.get("id"): row for row in ledger.get("timing_obligations", [])}
    clock_rows = board.get("clocks", [])
    reset_rows = board.get("resets", [])
    crossing_rows = board.get("crossings", [])
    historical = ledger.get("historical_timing_sources", [])
    hist_paths = {row.get("path") for row in historical}
    flow_hooks = ledger.get("historical_flow_hooks", [])
    flow_hook_ok = bool(flow_hooks) and all(
        row.get("sha256") == sha((ROOT / row.get("path", "__missing__")).read_bytes())
        and (row.get("constraint_source") in hist_paths or str(row.get("constraint_source", "")).startswith("Inherited "))
        for row in flow_hooks
    )
    historical_complete = {
        "fpga/scripts/timing.tcl",
        "fpga/scripts/timing-reviewed.tcl",
    } <= hist_paths

    # Check the actual V101 component XDC and TCL recipe, independent of the
    # producer's summary flags. The OOC file must contain only the comparison
    # clock and no invented board delays, clock groups, false paths, or waivers.
    xdc_rel = "fpga/experiments/cu66-v101-constraints/component.xdc"
    xdc_text = read_bytes(xdc_rel).decode("utf-8", errors="replace")
    xdc_commands = [line.strip() for line in xdc_text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    no_fabricated_xdc = (
        len(xdc_commands) == 1
        and re.search(r"^create_clock\s+-name\s+component_clk\s+-period\s+10\.000\s+\[get_ports clk\]$", xdc_commands[0]) is not None
        and not re.search(r"set_(?:input_delay|output_delay|false_path|clock_groups|clock_uncertainty|disable_timing|max_delay|min_delay)\b", "\n".join(xdc_commands), re.I)
    )
    run_rel = "fpga/experiments/cu66-v101-constraints/run.tcl"
    run_text = read_bytes(run_rel).decode("utf-8", errors="replace")
    reads_xdc = run_text.find("read_xdc")
    synth_pos = run_text.find("synth_design")
    xdc_before_synth = reads_xdc >= 0 and synth_pos > reads_xdc

    source_inventory_ok = (
        ledger.get("schema") == "v101-constraints-source-audit-v1"
        and ledger.get("baseline") == BASELINE
        and ledger.get("status") == "PASS_SOURCE_AUDIT_SIGNOFF_OPEN"
        and not source_mismatches
        and not source_baseline_mismatches
        and not recipe_mismatches
        and gates.get("source_inventory_pass") is True
        and component.get("port_count") == 308
        and component.get("input_port_count") == 37
        and component.get("output_port_count") == 271
        and component.get("clock", {}).get("period_ns") == 10.0
        and component.get("clock", {}).get("achieved") is False
        and len(component.get("sensitivity_events", [])) == 29
        and all(row.get("event_expression") == "posedge clk" for row in component.get("sensitivity_events", []))
        and len(clock_rows) == 7
        and len(reset_rows) == 3
        and len(crossing_rows) == 4
        and historical_complete
        and len(historical) == 8
        and flow_hook_ok
        and ledger.get("historical_SCM_timing_changes") == []
        and len(ledger.get("timing_obligations", [])) == 10
        and all(row.get("pass") is True for row in static.values())
        and static.get("no_invented_external_delays_or_exceptions", {}).get("pass") is True
        and static.get("comparison_clock_loaded_before_synthesis", {}).get("pass") is True
        and no_fabricated_xdc
        and xdc_before_synth
    )

    signoff_open = (
        component.get("external_delays_qualified") is False
        and gates.get("board_IO_delays_qualified") is False
        and gates.get("methodology_DRC_CDC_signoff") is False
        and gates.get("placed_and_routed") is False
        and all(row.get("status", "").startswith("OPEN") for row in ledger.get("timing_obligations", []))
        and "NETLIST_METHOD" in obligations
        and obligations["NETLIST_METHOD"].get("status", "").startswith("OPEN")
        and "OOC_EXTERNAL" in obligations
        and obligations["OOC_EXTERNAL"].get("status") == "OPEN"
    )

    preflight_meta = ledger.get("tool_preflight", {})
    preflight_path = preflight_meta.get("receipt")
    legacy_preflight_ok = False
    preflight = {}
    if preflight_path:
        preflight = read_json(preflight_path)
        preflight_hash = sha((ROOT / preflight_path).read_bytes())
        legacy_preflight_ok = (
            preflight_hash == preflight_meta.get("sha256")
            and preflight_meta.get("part_query_complete") is True
            and preflight_meta.get("status") == "EXACT_PART_UNAVAILABLE"
            and preflight_meta.get("values", {}).get("TARGET_COUNT") == "0"
            and preflight_meta.get("values", {}).get("SERIES7_COUNT") == "0"
            and preflight_meta.get("values", {}).get("VERSION") == "2025.2"
            and preflight.get("status") == "EXACT_PART_UNAVAILABLE"
        )

    selected_meta = ledger.get("selected_2026_preflight", {})
    selected_path = selected_meta.get("receipt") or "experiments/python-gamebub-v101/constraints/2026/results.json"
    selected_query = read_json(selected_path)
    selected_hash = sha((ROOT / selected_path).read_bytes())
    selected_receipt = selected_query.get("selected_receipt", {})
    selected_receipt_obj = read_json(selected_receipt.get("path", "")) if selected_receipt.get("path") else {}
    selected_query_ok = (
        selected_query.get("schema") == "v101-vivado2026-runtime-selection-v1"
        and selected_query.get("status") == "EXACT_TARGET_AVAILABLE"
        and selected_hash == selected_meta.get("sha256")
        and bool(selected_receipt.get("path"))
        and sha((ROOT / selected_receipt["path"]).read_bytes()) == selected_receipt.get("sha256")
        and selected_meta.get("actual_tool_version") == "2026.1"
        and selected_query.get("actual_tool_version") == "2026.1"
        and selected_query.get("exact_target_count") == 1
        and selected_query.get("series7_part_count") == 210
        and selected_query.get("part_query_complete") is True
        and selected_query.get("tool_prerequisite_restored") is True
        and selected_receipt_obj.get("status") == "EXACT_TARGET_AVAILABLE"
        and selected_receipt_obj.get("part_query_complete") is True
        and selected_receipt_obj.get("values", {}).get("TARGET_COUNT") == "1"
        and selected_receipt_obj.get("values", {}).get("SERIES7_COUNT") == "210"
        and selected_receipt_obj.get("values", {}).get("VERSION") == "2026.1"
        and not selected_receipt_obj.get("synthesis_started")
        and not selected_receipt_obj.get("placement_started")
        and not selected_receipt_obj.get("routing_started")
    )
    selected_attempts_ok = True
    for attempt in selected_query.get("attempts", []):
        attempt_path = attempt.get("receipt", "")
        attempt_obj = read_json(attempt_path)
        attempt_hash = sha((ROOT / attempt_path).read_bytes())
        attempt_log_path = str(Path(attempt_path).parent / "query.log")
        attempt_log = read_bytes(attempt_log_path)
        marker = b"V101_QUERY_COMPLETE" in attempt_log
        attempt_ok = (
            attempt_hash == attempt.get("sha256")
            and attempt_obj.get("observed_exit_code") == attempt.get("observed_exit_code")
            and (attempt.get("part_query_complete") is True) == marker
            and (attempt.get("part_query_complete") is True or attempt.get("observed_exit_code") != 0)
            and (not attempt.get("part_query_complete") or attempt_obj.get("status") == "EXACT_TARGET_AVAILABLE")
        )
        selected_attempts_ok &= attempt_ok

    vivado2026_attempts = []
    vivado2026_ok = True
    for receipt_file in sorted((ROOT / "experiments/python-gamebub-v101/constraints/2026").glob("*/receipt.json")):
        receipt_rel = str(receipt_file.relative_to(ROOT))
        receipt = json.loads(read_bytes(receipt_rel))
        log_rel = str(Path(receipt_rel).parent / "query.log")
        try:
            log_bytes = read_bytes(log_rel)
        except FileNotFoundError:
            log_bytes = b""
        log_hash = sha(log_bytes) if log_bytes else None
        no_hardware_flow = not any(receipt.get(key) for key in ["synthesis_started", "placement_started", "routing_started"])
        if receipt.get("status") in ("STARTUP_FAILED", "FINISHED_NEEDS_PARSE"):
            result_ok = (
                receipt.get("schema") == "v101-vivado2026-isolated-query-v1"
                and receipt.get("observed_exit_code") != 0
                and receipt.get("log_sha256") == log_hash
                and no_hardware_flow
            )
        else:
            # Accept only a fully parsed read-only query if a later attempt
            # reaches Tcl; successful launcher startup alone is not a query.
            result_ok = (
                receipt.get("schema") == "v101-vivado2026-isolated-query-v1"
                and receipt.get("part_query_complete") is True
                and receipt.get("observed_exit_code") == 0
                and no_hardware_flow
            )
        vivado2026_ok &= result_ok
        vivado2026_attempts.append({
            "path": receipt_rel,
            "status": receipt.get("status"),
            "tool_installation_host": receipt.get("tool_installation_host"),
            "observed_exit_code": receipt.get("observed_exit_code"),
            "log_sha256": log_hash,
            "no_synthesis_or_implementation_started": no_hardware_flow,
            "license_files_mounted_or_changed": receipt.get("license_files_mounted_or_changed"),
            "verification_pass": result_ok,
        })

    ledger_ok = source_inventory_ok and signoff_open and legacy_preflight_ok and selected_query_ok and selected_attempts_ok and vivado2026_ok
    check(
        "v101_constraints_ledger_coverage_and_truthful_limits",
        ledger_ok,
        {
            "path": path,
            "sha256": sha((ROOT / path).read_bytes()),
            "schema": ledger.get("schema"),
            "status": ledger.get("status"),
            "source_hashes_declared": len(source_hashes),
            "source_hash_mismatches": source_mismatches,
            "source_not_equal_to_v100_git_blob": source_baseline_mismatches,
            "recipe_hashes_declared": len(recipe_hashes),
            "recipe_hash_mismatches": recipe_mismatches,
            "inventory_counts": {"component_ports": component.get("port_count"), "clocked_events": len(component.get("sensitivity_events", [])), "board_clocks": len(clock_rows), "reset_groups": len(reset_rows), "crossings": len(crossing_rows), "historical_timing_sources": len(historical), "timing_obligations": len(obligations)},
            "historical_timing_sources_include_both_timing_tcl_files": historical_complete,
            "historical_flow_hook_count": len(flow_hooks),
            "historical_flow_hooks_hash_and_source_bound": flow_hook_ok,
            "historical_SCM_timing_changes": ledger.get("historical_SCM_timing_changes"),
            "v101_component_xdc_commands": xdc_commands,
            "no_fabricated_component_constraints": no_fabricated_xdc,
            "component_xdc_loaded_before_synthesis": xdc_before_synth,
            "historical_vivado_2025_2_preflight": {"path": preflight_path, "sha256": preflight_meta.get("sha256"), "status": preflight_meta.get("status"), "values": preflight_meta.get("values"), "verified": legacy_preflight_ok},
            "selected_vivado_2026_1_query": {"path": selected_path, "sha256": selected_hash, "status": selected_query.get("status"), "target": selected_query.get("target"), "exact_target_count": selected_query.get("exact_target_count"), "series7_part_count": selected_query.get("series7_part_count"), "part_query_complete": selected_query.get("part_query_complete"), "selected_receipt": selected_receipt, "verified": selected_query_ok, "attempts_verified": selected_attempts_ok},
            "vivado_2026_1_attempts": vivado2026_attempts,
            "vivado_2026_1_attempts_verified": vivado2026_ok,
            "methodology_DRC_CDC_signoff": gates.get("methodology_DRC_CDC_signoff"),
            "board_IO_delays_qualified": gates.get("board_IO_delays_qualified"),
            "exact_part_synthesis": gates.get("exact_part_synthesis"),
        },
    )
    return {
        "status": "PASS_EVIDENCE" if ledger_ok else "FAIL",
        "path": path,
        "sha256": sha((ROOT / path).read_bytes()),
        "schema": ledger.get("schema"),
        "source_file_count": len(source_hashes),
        "recipe_file_count": len(recipe_hashes),
        "board_clocks": len(clock_rows),
        "reset_groups": len(reset_rows),
        "crossings": len(crossing_rows),
        "historical_timing_sources": len(historical),
        "timing_obligations": len(obligations),
        "component_xdc_commands": xdc_commands,
        "historical_vivado_2025_2_preflight": {"path": preflight_path, "status": preflight_meta.get("status"), "values": preflight_meta.get("values"), "verified": legacy_preflight_ok},
        "selected_vivado_2026_1_query": {"path": selected_path, "status": selected_query.get("status"), "target": selected_query.get("target"), "exact_target_count": selected_query.get("exact_target_count"), "series7_part_count": selected_query.get("series7_part_count"), "verified": selected_query_ok},
        "vivado_2026_1_attempts": vivado2026_attempts,
        "vivado_2026_1_part_query_succeeded": any(row.get("status") not in ("STARTUP_FAILED", "FINISHED_NEEDS_PARSE") for row in vivado2026_attempts),
        "methodology_DRC_CDC_signoff": False,
        "board_IO_delays_qualified": False,
        "exact_target_synthesis_or_route": False,
        "scope_limit": "Source/constraint inventory and a separate part-availability query only. This is not Vivado check_timing, methodology, DRC, CDC, exception, implementation, or timing signoff.",
    }


def audit_scratch_probe() -> dict:
    summary_path = "experiments/python-gamebub-v101/scratch/probe-results.json"
    summary = read_json(summary_path)
    receipt_path = summary.get("selected_receipt", "")
    receipt = read_json(receipt_path)
    receipt_hash = sha((ROOT / receipt_path).read_bytes())
    probe_dir = str(Path(receipt_path).parent)
    manifest_path = f"{probe_dir}/artifacts.json"
    manifest = read_json(manifest_path)
    public_ports = read_json(f"{probe_dir}/public-ports.json")
    port_scope_ok = len(public_ports) == 79 and sum(row.get("direction") == "output" for row in public_ports) == 47
    artifact_result = artifact_audit(probe_dir, manifest)
    source_ok = (
        receipt.get("baseline_commit") == BASELINE
        and receipt.get("original", {}).get("path") == ORIGINAL_PATH
        and receipt.get("original", {}).get("sha256") == sha((ROOT / ORIGINAL_PATH).read_bytes())
        and receipt.get("candidate", {}).get("path") == CANDIDATE_PATH
        and receipt.get("candidate", {}).get("sha256") == sha((ROOT / CANDIDATE_PATH).read_bytes())
    )
    verdicts = receipt.get("verdicts", [])
    rows = []
    terminal_ok = len(verdicts) == 2
    for verdict in verdicts:
        seed = verdict.get("seed")
        trace_name = f"probe-seed-{seed}.jsonl.gz"
        trace_manifest = manifest.get(trace_name, {})
        trace_path = ROOT / probe_dir / trace_name
        trace_count = 0
        try:
            import gzip
            with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
                trace_count = sum(1 for _ in stream)
        except OSError:
            pass
        passed = (
            verdict.get("status") == "TEST_PASS"
            and verdict.get("cases") == 21534
            and verdict.get("clock_edges") == 0
            and verdict.get("all_public_outputs_equal") is True
            and verdict.get("internal_cone_equal") is True
            and verdict.get("reference_equal") is True
            and trace_count == 21534
            and trace_manifest.get("records") == trace_count
        )
        terminal_ok &= passed
        rows.append({"seed": seed, "status": verdict.get("status"), "cases": verdict.get("cases"), "clock_edges": verdict.get("clock_edges"), "public_outputs_equal": verdict.get("all_public_outputs_equal"), "internal_cone_equal": verdict.get("internal_cone_equal"), "trace_rows": trace_count, "pass": passed})
    commands_ok = bool(receipt.get("commands")) and all(c.get("exit_code") == 0 for c in receipt["commands"])
    provenance_path = "experiments/python-gamebub-v101/scratch/probe-provenance.json"
    provenance = read_json(provenance_path)
    runner_snapshot_hash = sha(read_bytes(provenance.get("executed_runner_snapshot", "")))
    provenance_ok = (
        provenance.get("status") == "PASS_EXECUTED_SOURCE_SNAPSHOTS_AND_RUNNER_PIN"
        and provenance.get("selected_receipt") == receipt_path
        and provenance.get("selected_receipt_sha256") == receipt_hash
        and provenance.get("executed_runner_sha256") == receipt.get("runner_sha256") == runner_snapshot_hash
        and all(
            row.get("sha256") == sha(read_bytes(row.get("retained_copy", "")))
            for row in provenance.get("compiled_sources", [])
        )
    )
    trace_audit_path = "experiments/python-gamebub-v101/scratch/trace-audit.json"
    trace_audit = read_json(trace_audit_path)
    trace_auditor_path = trace_audit.get("auditor", "")
    trace_auditor_hash = sha(read_bytes(trace_auditor_path)) if trace_auditor_path else None
    trace_audit_ok = (
        trace_audit.get("schema") == "v101-scratch-independent-trace-audit-v1"
        and trace_audit.get("status") == "PASS"
        and trace_audit.get("auditor_sha256") == trace_auditor_hash
        and trace_audit.get("total_replayed_cases") == 43068
        and len(trace_audit.get("seed_checks", [])) == 2
        and all(
            row.get("records_parsed_and_replayed") == 21534
            and row.get("sha256") == manifest.get(Path(row.get("trace", "")).name, {}).get("sha256")
            and row.get("seed") in {101401, 101402}
            for row in trace_audit.get("seed_checks", [])
        )
    )
    ok = (
        summary.get("status") == "PASS_ACTUAL_RTL_PRIORITY_CONE"
        and summary.get("sha256") == receipt_hash
        and receipt.get("schema") == "v101-scratch-priority-probe-v1"
        and receipt.get("status") == "PASS_ACTUAL_RTL_PRIORITY_CONE"
        and source_ok
        and terminal_ok
        and commands_ok
        and port_scope_ok
        and provenance_ok
        and trace_audit_ok
        and artifact_result["declared"] == artifact_result["checked"]
        and not artifact_result["missing"]
        and not artifact_result["mismatched"]
    )
    check(
        "scratch_actual_rtl_priority_probe",
        ok,
        {"summary": summary_path, "receipt": receipt_path, "receipt_sha256": receipt_hash, "source_binding_pass": source_ok, "public_port_count": len(public_ports), "public_output_count": sum(row.get("direction") == "output" for row in public_ports), "public_port_scope_pass": port_scope_ok, "verdicts": rows, "commands_all_pass": commands_ok, "artifact_hashes": artifact_result, "executed_source_and_runner_provenance": {"path": provenance_path, "status": provenance.get("status"), "verified": provenance_ok}, "independent_trace_audit": {"path": trace_audit_path, "auditor": trace_auditor_path, "auditor_hash_verified": trace_audit.get("auditor_sha256") == trace_auditor_hash, "total_replayed_cases": trace_audit.get("total_replayed_cases"), "verified": trace_audit_ok}},
    )
    return {"status": "PASS_EVIDENCE" if ok else "FAIL", "summary": summary_path, "receipt": receipt_path, "receipt_sha256": receipt_hash, "public_port_count": len(public_ports), "public_output_count": sum(row.get("direction") == "output" for row in public_ports), "verdicts": rows, "artifact_audit": artifact_result, "executed_source_and_runner_provenance": {"path": provenance_path, "verified": provenance_ok}, "independent_trace_audit": {"path": trace_audit_path, "total_replayed_cases": trace_audit.get("total_replayed_cases"), "verified": trace_audit_ok}, "scope_limit": receipt.get("scope")}


def audit_scratch_frontend() -> dict:
    summary_path = "experiments/python-gamebub-v101/scratch/frontend-results.json"
    summary = read_json(summary_path)
    receipt_path = summary.get("selected_receipt", "")
    receipt = read_json(receipt_path)
    receipt_hash = sha((ROOT / receipt_path).read_bytes())
    attempt_dir = str(Path(receipt_path).parent)
    artifacts_path = f"{attempt_dir}/artifacts.json"
    manifest = read_json(artifacts_path)
    artifact_result = artifact_audit(attempt_dir, manifest)
    frontend_log = (ROOT / attempt_dir / "frontend.log").read_text(errors="replace")
    diagnosis_link = summary.get("authoritative_diagnosis", {})
    diagnosis_path = diagnosis_link.get("path")
    diagnosis = read_json(diagnosis_path)
    diagnosis_hash = sha((ROOT / diagnosis_path).read_bytes())
    exact_first_fatal_present = diagnosis.get("first_fatal", "") in frontend_log
    commands = receipt.get("commands", [])
    command_codes = [row.get("exit_code") for row in commands]
    candidate_ok = (
        receipt.get("candidate", {}).get("path") == CANDIDATE_PATH
        and receipt.get("candidate", {}).get("sha256") == sha((ROOT / CANDIDATE_PATH).read_bytes())
        and receipt.get("original", {}).get("path") == ORIGINAL_PATH
        and receipt.get("original", {}).get("sha256") == sha((ROOT / ORIGINAL_PATH).read_bytes())
    )
    # The audited outcome is a captured failed scratch-only frontend probe.
    # Treating it as accounted evidence is a pass for the audit; it is never
    # called successful lowering or full-component mapping.
    failure_recorded = (
        summary.get("status") == "FRONTEND_FAILED_OR_LIMITED"
        and summary.get("sha256") == receipt_hash
        and receipt.get("schema") == "v101-scratch-frontend-v1"
        and receipt.get("status") == "FRONTEND_FAILED_OR_LIMITED"
        and diagnosis_hash == diagnosis_link.get("sha256")
        and diagnosis.get("status") == "FAILED_AT_DIFFERENT_ZIGZAG_ITERATOR"
        and diagnosis.get("raw_receipt", {}).get("sha256") == receipt_hash
        and diagnosis.get("frontend_log", {}).get("sha256") == sha((ROOT / attempt_dir / "frontend.log").read_bytes())
        and diagnosis.get("raw_receipt_diagnostic_correction", {}).get("raw_value") is True
        and diagnosis.get("raw_receipt_diagnostic_correction", {}).get("precise_value") is False
        and diagnosis.get("old_priority_iterator_latch_error") is False
        and diagnosis.get("new_function_iterator_latch_error") is True
        and diagnosis.get("additional_RTL_or_IR_workaround_applied") is False
        and exact_first_fatal_present
        and receipt.get("postprocess_mapped_or_routed") is False
        and len(command_codes) >= 4
        and command_codes[:-1] and all(code == 0 for code in command_codes[:-1])
        and command_codes[-1] != 0
    )
    ok = (
        receipt.get("baseline_commit") == BASELINE
        and candidate_ok
        and failure_recorded
        and artifact_result["declared"] == artifact_result["checked"]
        and not artifact_result["missing"]
        and not artifact_result["mismatched"]
    )
    check(
        "scratch_frontend_failure_truthfully_retained",
        ok,
        {"summary": summary_path, "receipt": receipt_path, "receipt_sha256": receipt_hash, "diagnosis": diagnosis_path, "diagnosis_sha256": diagnosis_hash, "observed_failure": diagnosis.get("status"), "command_exit_codes": command_codes, "old_priority_iterator_latch_error": diagnosis.get("old_priority_iterator_latch_error"), "new_function_iterator_latch_error": diagnosis.get("new_function_iterator_latch_error"), "exact_first_fatal_present": exact_first_fatal_present, "postprocess_mapped_or_routed": receipt.get("postprocess_mapped_or_routed"), "candidate_binding_pass": candidate_ok, "artifact_hashes": artifact_result},
    )
    return {
        "status": "PASS_EVIDENCE" if ok else "FAIL",
        "summary": summary_path,
        "receipt": receipt_path,
        "receipt_sha256": receipt_hash,
        "observed_probe_status": receipt.get("status"),
        "diagnosis": diagnosis_path,
        "diagnosis_sha256": diagnosis_hash,
        "observed_failure": diagnosis.get("status"),
        "command_exit_codes": command_codes,
        "old_priority_iterator_latch_error": diagnosis.get("old_priority_iterator_latch_error"),
        "new_function_iterator_latch_error": diagnosis.get("new_function_iterator_latch_error"),
        "postprocess_mapped_or_routed": False,
        "artifact_audit": artifact_result,
        "scope_limit": "Accounted failed scratch-only Yosys process-lowering probe; the historical iterator latch remains and this is not a complete component mapping or timing result.",
    }


def audit_vivado_ooc_build() -> dict:
    selector_path = "experiments/python-gamebub-v101/constraints/2026-build/results.json"
    selector = read_json(selector_path)
    receipt_ref = selector.get("selected_receipt", {})
    receipt_path = receipt_ref.get("path", "")
    receipt = read_json(receipt_path)
    receipt_hash = sha((ROOT / receipt_path).read_bytes())
    attempt_dir = str(Path(receipt_path).parent)
    log_path = f"{attempt_dir}/vivado.log"
    log_bytes = read_bytes(log_path)
    log_hash = sha(log_bytes)
    inputs_path = f"{attempt_dir}/inputs.json"
    inputs = read_json(inputs_path)
    inputs_hash = sha((ROOT / inputs_path).read_bytes())

    artifact_rows, mismatches, missing = [], [], []
    for name, entry in sorted(receipt.get("artifacts", {}).items()):
        external_path = entry.get("external_path")
        try:
            external_bytes = Path(external_path).read_bytes()
            external_hash = sha(external_bytes)
        except (OSError, TypeError):
            external_hash = None
        relative_copy = f"{attempt_dir}/reports/{name}"
        copied_hash = None
        if (ROOT / relative_copy).is_file():
            copied_hash = sha(read_bytes(relative_copy))
        external_good = external_hash == entry.get("sha256") and len(external_bytes) == entry.get("bytes") if external_hash is not None else False
        if copied_hash is not None:
            copied_good = copied_hash == entry.get("sha256")
        else:
            copied_good = False
        # Synth/place/route DCPs intentionally stay in the external build tree.
        # If a downstream clone lacks that tree, the immutable receipt hash is
        # still auditable as a recorded checksum, while the report itself must
        # be retained and rehashed in-repo.
        is_external_dcp = name.endswith(".dcp") and copied_hash is None
        external_checkpoint_only = is_external_dcp and bool(re.fullmatch(r"[0-9a-f]{64}", entry.get("sha256", ""))) and (external_hash is None or external_good)
        good = (external_good and (copied_hash is None or copied_good)) or (copied_good and external_hash is None) or external_checkpoint_only
        if not good:
            mismatches.append(name)
            if external_hash is None and not copied_good and not external_checkpoint_only:
                missing.append(name)
        artifact_rows.append({"name": name, "sha256": entry.get("sha256"), "bytes": entry.get("bytes"), "verification": "external_checkpoint_hash_recorded_optional_recheck" if is_external_dcp else "retained_report_rehashed" if copied_good else "FAIL", "external_hash_verified": False if is_external_dcp else external_good, "copied_report_hash_verified": copied_hash is None or copied_good})

    manifest_path = "fpga/experiments/cu66-v100-baseline/frozen-inputs.json"
    manifest = read_json(manifest_path)
    manifest_hash = sha((ROOT / manifest_path).read_bytes())
    expected_sources = manifest.get("source_sha256", {})
    source_rows = inputs.get("source_sha256", {})
    source_ok = (
        inputs.get("schema") == "v101-prepared-ooc-inputs-v1"
        and inputs.get("scratch_override") is None
        and source_rows == {path: expected_sources[path] for path in source_rows if path in expected_sources}
        and set(source_rows) == set(manifest.get("rtl_sources", []) + manifest.get("include_headers", []))
        and all(sha(read_bytes(path)) == expected for path, expected in source_rows.items())
        and receipt.get("source_snapshot_unchanged") is True
        and receipt.get("source_manifest_sha256") == inputs_hash
        and inputs.get("frozen_manifest_sha256") == manifest_hash
    )
    recipe_ok = all(
        sha(read_bytes(f"{attempt_dir}/recipe-snapshot/{name}")) == expected
        for name, expected in inputs.get("recipe_sha256", {}).items()
        if name != "inputs.tcl"
    ) and all(receipt.get("recipe_snapshots_sha256", {}).get(name) == expected for name, expected in inputs.get("recipe_sha256", {}).items())
    log_ok = receipt.get("log_sha256") == log_hash
    selector_ok = (
        selector.get("schema") == "v101-vivado2026-build-selection-v1"
        and selector.get("status") == "SYNTHESIS_PASSED_PLACEMENT_RESOURCE_BLOCKED"
        and selector.get("selected_receipt", {}).get("sha256") == receipt_hash
        and selector.get("component_route_finished") is False
        and selector.get("placement_started") is False
        and selector.get("routing_started") is False
        and selector.get("synthesis_checkpoint_written") is True
        and receipt.get("schema") == "v101-vivado2026-ooc-build-v1"
        and receipt.get("status") == "TOOL_OR_BUILD_FAILED"
        and receipt.get("observed_exit_code") == 1
        and receipt.get("synthesis_started") is True
        and receipt.get("synthesis_checkpoint_written") is True
        and receipt.get("placement_reports_present") is False
        and receipt.get("routing_checkpoint_written") is False
        and receipt.get("component_route_finished") is False
        and receipt.get("clock_loaded_before_synthesis") is True
        and receipt.get("clock_period_ns") == 10.0
        and receipt.get("part") == "xc7a100tcsg324-1"
    )

    native_ref = selector.get("native_findings", {})
    methodology_ref = selector.get("methodology_violations", {})
    native_path = native_ref.get("path", "")
    method_path = methodology_ref.get("path", "")
    native = read_json(native_path)
    methodology = read_json(method_path)
    native_hash = sha((ROOT / native_path).read_bytes())
    method_hash = sha((ROOT / method_path).read_bytes())
    raw_reports_ok = True
    for report_name, expected in native.get("reports_sha256", {}).items():
        try:
            actual = sha(read_bytes(f"{attempt_dir}/reports/{report_name}"))
        except FileNotFoundError:
            raw_reports_ok = False
            continue
        raw_reports_ok &= actual == expected

    methods = native.get("methodology", {})
    checks = native.get("check_timing", {})
    blocker = native.get("placement_blocker", {})
    timing = native.get("timing", {})
    usage = native.get("utilization", {})
    cdc = native.get("cdc", {})
    methodology_rules = {row.get("rule"): row.get("reported_count") for row in methods.get("rules", [])}
    expected_method_rules = {"RTGT-1": 64, "SYNTH-5": 378, "SYNTH-6": 8, "TIMING-16": 1000, "TIMING-18": 1000, "ULMTCS-2": 1}

    def report_table(path: str) -> dict[str, tuple[str, int]]:
        content = read_bytes(f"{attempt_dir}/reports/{path}").decode("utf-8", errors="replace")
        output = {}
        for line in content.splitlines():
            match = re.match(r"\|\s*([A-Z0-9-]+)\s*\|\s*(Warning|Error|Advisory)\s*\|.*\|\s*(\d+)\s*\|", line)
            if match:
                output[match.group(1)] = (match.group(2), int(match.group(3)))
        return output

    raw_method_rules = report_table("synth-methodology.rpt")
    raw_drc_rules = report_table("synth-drc.rpt")
    raw_check_timing = read_bytes(f"{attempt_dir}/reports/synth-check-timing.rpt").decode("utf-8", errors="replace")
    raw_check_counts = {key: int(value) for key, value in re.findall(r"checking ([a-z_]+) \((\d+)\)", raw_check_timing)}
    raw_cdc = read_bytes(f"{attempt_dir}/reports/synth-cdc.rpt").decode("utf-8", errors="replace")
    raw_report_tables_agree = (
        {key: value[1] for key, value in raw_method_rules.items()} == methodology_rules
        and raw_drc_rules.get("UTLZ-1") == ("Error", 3)
        and raw_check_counts == checks
        and "All paths are Safely Timed." in raw_cdc
    )
    issue_truthful = (
        native.get("schema") == "v101-native-synth-findings-v1"
        and native.get("status") == "SYNTHESIS_PASSED_PLACEMENT_RESOURCE_BLOCKED"
        and methods.get("reported_findings") == 2451
        and methodology_rules == expected_method_rules
        and methods.get("resolved") == 0
        and methods.get("waived") == 0
        and checks.get("no_clock") == 0
        and checks.get("no_input_delay") == 1101
        and checks.get("no_output_delay") == 12885
        and checks.get("unconstrained_internal_endpoints") == 0
        and cdc.get("native_report_exists") is True
        and cdc.get("qualified_clean_whole_board_CDC") is False
        and blocker.get("rule") == "UTLZ-1"
        and blocker.get("DRC_errors") == 3
        and blocker.get("LUTRAM_required") == 22286
        and blocker.get("LUTRAM_compatible_available") == 19000
        and blocker.get("RAMD64E_required") == 19956
        and blocker.get("RAMD64E_compatible_available") == 19000
        and blocker.get("error_downgraded_or_disabled") is False
        and blocker.get("placer_ran") is False
        and blocker.get("route_ran") is False
        and timing.get("timing_closed") is False
        and timing.get("route_Fmax_Hz") is None
        and usage.get("total_LUT") == 74340
        and usage.get("LUTRAM") == 22286
        and usage.get("FF") == 34985
        and usage.get("DSP") == 28
        and raw_report_tables_agree
    )
    method_extract_ok = (
        methodology.get("schema") == "v101-native-methodology-extraction-v1"
        and methodology.get("reported_findings") == methods.get("reported_findings")
        and len(methodology.get("violations", [])) == methods.get("reported_findings")
        and methodology.get("not_necessarily_exhaustive_timing_endpoint_count") is True
    )
    raw_log_blocker = b"ERROR: [DRC UTLZ-1]" in log_bytes and b"Placer not run" in log_bytes
    attempt_rows, attempts_ok = [], True
    for attempt in selector.get("attempts", []):
        path = attempt.get("path", "")
        obj = read_json(path)
        actual_hash = sha((ROOT / path).read_bytes())
        ok = actual_hash == attempt.get("sha256") and obj.get("status") != "RUNNING"
        attempts_ok &= ok
        attempt_rows.append({"path": path, "sha256": actual_hash, "status": obj.get("status"), "exit_code": obj.get("observed_exit_code"), "verified": ok})

    alias_ref = selector.get("user_provided_license_reproduction_alias", {})
    alias_path = alias_ref.get("path", "")
    alias = read_json(alias_path) if alias_path else {}
    alias_hash = sha((ROOT / alias_path).read_bytes()) if alias_path else None
    alias_ok = (
        bool(alias_path)
        and alias_hash == alias_ref.get("sha256")
        and alias.get("schema") == "v101-user-provided-license-path-alias-v1"
        and alias.get("byte_equal_to_legitimate_license_used_for_successful_query_and_build") is True
        and alias.get("license_contents_or_fingerprint_recorded") is False
        and alias.get("original_or_provided_file_modified") is False
        and alias.get("private_copy_removed_after_completed_containers") is True
        and alias.get("build_or_query_repeated_for_alias") is False
        and alias.get("executed_old_copy_argv_preserved") is True
    )

    flat_ref = selector.get("readonly_post_synthesis_analysis", {})
    flat_summary_path = flat_ref.get("path", "")
    flat_summary = read_json(flat_summary_path) if flat_summary_path else {}
    flat_summary_hash = sha((ROOT / flat_summary_path).read_bytes()) if flat_summary_path else None
    flat_receipt_path = flat_summary.get("receipt", {}).get("path", "")
    flat_receipt = read_json(flat_receipt_path) if flat_receipt_path else {}
    flat_receipt_hash = sha((ROOT / flat_receipt_path).read_bytes()) if flat_receipt_path else None
    flat_dir = str(Path(flat_receipt_path).parent) if flat_receipt_path else ""
    flat_log_hash = sha(read_bytes(f"{flat_dir}/analysis.log")) if flat_dir and (ROOT / flat_dir / "analysis.log").is_file() else None
    flat_artifact_hashes_ok = bool(flat_receipt.get("artifacts")) and all(
        sha(read_bytes(f"{flat_dir}/{name}")) == entry.get("sha256")
        and (ROOT / flat_dir / name).stat().st_size == entry.get("bytes")
        for name, entry in flat_receipt.get("artifacts", {}).items()
    )
    flat_analysis_ok = (
        bool(flat_summary_path)
        and flat_summary_hash == flat_ref.get("sha256")
        and flat_summary.get("schema") == "v101-readonly-capacity-dsp-analysis-v1"
        and flat_summary.get("status") == "PASS_READONLY_ANALYSIS"
        and flat_summary.get("checkpoint_mounted_readonly") is True
        and flat_summary.get("synthesis_repeated") is False
        and flat_summary.get("implementation_repeated") is False
        and flat_summary.get("DSP48E1_cells") == 28
        and flat_receipt_hash == flat_summary.get("receipt", {}).get("sha256")
        and flat_receipt.get("observed_exit_code") == 0
        and flat_receipt.get("log_sha256") == flat_log_hash
        and flat_artifact_hashes_ok
        and flat_receipt.get("checkpoint_mounted_readonly") is True
        and flat_receipt.get("synthesis_or_implementation_repeated") is False
        and flat_receipt.get("source_RTL_changed") is False
        and flat_receipt.get("DSP48E1_cells", 28) in (28, None)
        and flat_summary.get("capacity", {}).get("LUT as Memory", {}).get("used") == 22286
        and flat_summary.get("capacity", {}).get("LUT as Memory", {}).get("available") == 19000
        and flat_summary.get("capacity", {}).get("Slice LUTs*", {}).get("util_percent") == 117.26
    )

    ok = (
        selector_ok
        and source_ok
        and recipe_ok
        and log_ok
        and not mismatches
        and not missing
        and raw_reports_ok
        and issue_truthful
        and method_extract_ok
        and raw_log_blocker
        and attempts_ok
        and selector.get("native_findings", {}).get("sha256") == native_hash
        and selector.get("methodology_violations", {}).get("sha256") == method_hash
        and alias_ok
        and flat_analysis_ok
        and selector.get("status") == "SYNTHESIS_PASSED_PLACEMENT_RESOURCE_BLOCKED"
        and selector.get("board_IO_timing_qualified") is False
        and selector.get("hardware_30fps") is False
        and selector.get("complete_validated_decode_under10ms") is False
    )
    check(
        "vivado_2026_ooc_synthesis_and_placement_failure_evidence",
        ok,
        {
            "selector": selector_path,
            "selector_sha256": sha((ROOT / selector_path).read_bytes()),
            "selected_receipt": receipt_path,
            "receipt_sha256": receipt_hash,
            "attempts": attempt_rows,
            "source_snapshot_pass": source_ok,
            "recipe_snapshot_pass": recipe_ok,
            "artifacts": {"declared": len(receipt.get("artifacts", {})), "verified": len(artifact_rows), "mismatches": mismatches, "missing": missing},
            "raw_reports_hash_bound": raw_reports_ok,
            "raw_methodology_rule_counts": {key: list(value) for key, value in raw_method_rules.items()},
            "raw_drc_rule_counts": {key: list(value) for key, value in raw_drc_rules.items()},
            "raw_check_timing_counts": raw_check_counts,
            "raw_cdc_says_all_paths_safely_timed": "All paths are Safely Timed." in raw_cdc,
            "raw_native_reports_reconcile": raw_report_tables_agree,
            "native_findings": {"path": native_path, "sha256": native_hash, "methodology_finding_count": methods.get("reported_findings"), "methodology_rules": methodology_rules, "resolved": methods.get("resolved"), "waived": methods.get("waived"), "check_timing": checks, "cdc_scope": cdc},
            "placement_blocker": blocker,
            "synthesis_utilization": usage,
            "timing": timing,
            "methodology_extract": {"path": method_path, "sha256": method_hash, "violation_count": len(methodology.get("violations", [])), "non_exhaustive_timing_limit_recorded": methodology.get("not_necessarily_exhaustive_timing_endpoint_count")},
            "post_synthesis_readonly_capacity_analysis": {"path": flat_summary_path, "sha256": flat_summary_hash, "receipt": flat_receipt_path, "receipt_sha256": flat_receipt_hash, "analysis_log_sha256": flat_log_hash, "artifact_hashes_verified": flat_artifact_hashes_ok, "DSP48E1_cells": flat_summary.get("DSP48E1_cells"), "verified": flat_analysis_ok},
            "user_provided_license_path_alias": {"path": alias_path, "sha256": alias_hash, "same_bytes_as_used_existing_license": alias.get("byte_equal_to_legitimate_license_used_for_successful_query_and_build"), "no_license_contents_or_fingerprint_logged": alias.get("license_contents_or_fingerprint_recorded") is False, "query_or_build_rerun": alias.get("build_or_query_repeated_for_alias"), "verified": alias_ok},
            "terminal_error_recorded_in_log": raw_log_blocker,
        },
    )
    return {
        "status": "PASS_EVIDENCE" if ok else "FAIL",
        "selector": selector_path,
        "selector_sha256": sha((ROOT / selector_path).read_bytes()),
        "selector_status": selector.get("status"),
        "attempts": attempt_rows,
        "selected_receipt": receipt_path,
        "receipt_sha256": receipt_hash,
        "source_snapshot_unchanged": source_ok,
        "artifact_hashes_verified": len(artifact_rows),
        "artifact_mismatches": mismatches,
        "raw_reports_hash_bound": raw_reports_ok,
        "synthesis_started": receipt.get("synthesis_started"),
        "synthesis_checkpoint_written": receipt.get("synthesis_checkpoint_written"),
        "placement_started": selector.get("placement_started"),
        "routing_started": selector.get("routing_started"),
        "component_route_finished": selector.get("component_route_finished"),
        "synthesis_utilization": usage,
        "synthesis_timing": timing,
        "methodology_findings": methods,
        "check_timing": checks,
        "raw_methodology_rule_counts": {key: list(value) for key, value in raw_method_rules.items()},
        "raw_drc_rule_counts": {key: list(value) for key, value in raw_drc_rules.items()},
        "raw_cdc_report_text": raw_cdc.strip().splitlines()[-1] if raw_cdc.strip() else None,
        "drc_placement_blocker": blocker,
        "cdc": cdc,
        "methodology_violations_path": method_path,
        "methodology_violations_sha256": method_hash,
        "post_synthesis_readonly_capacity_analysis": {"path": flat_summary_path, "sha256": flat_summary_hash, "DSP48E1_cells": flat_summary.get("DSP48E1_cells"), "verified": flat_analysis_ok},
        "user_provided_license_path_alias": {"path": alias_path, "sha256": alias_hash, "same_bytes_as_existing_license": alias.get("byte_equal_to_legitimate_license_used_for_successful_query_and_build"), "contents_or_fingerprint_recorded": alias.get("license_contents_or_fingerprint_recorded"), "verified": alias_ok},
        "scope_limit": "Actual Vivado 2026.1 exact-part component synthesis and native post-synthesis reports. Placement was blocked by UTLZ-1; no place/route, board I/O contract, whole-system integration, Fmax, hardware throughput, or complete decode latency was qualified.",
    }


def main() -> int:
    source_scope = audit_source_scope()
    regressions = {}
    for mode in ("fresh", "canonical"):
        try:
            regressions[mode] = audit_regression(mode)
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
            check(f"{mode}_paired_regression_receipt_and_terminal_tests", False, {"error": type(exc).__name__, "detail": str(exc)})
            regressions[mode] = {"status": "FAIL", "mode": mode, "error": str(exc)}

    # Constraints-ledger validation is filled against its final producer schema
    # once the independent ledger is present. Missing evidence remains an audit
    # error; the audit never turns source inspection into Vivado signoff.
    ledger_path = "experiments/python-gamebub-v101/constraints/ledger.json"
    try:
        ledger = read_json(ledger_path)
        ledger_status = audit_constraints_ledger(ledger)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError, NameError) as exc:
        check("v101_constraints_ledger_coverage_and_truthful_limits", False, {"error": type(exc).__name__, "detail": str(exc)})
        ledger_status = {"status": "FAIL", "path": ledger_path, "error": str(exc)}

    try:
        scratch_probe = audit_scratch_probe()
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        check("scratch_actual_rtl_priority_probe", False, {"error": type(exc).__name__, "detail": str(exc)})
        scratch_probe = {"status": "FAIL", "error": str(exc)}

    try:
        scratch_frontend = audit_scratch_frontend()
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        check("scratch_frontend_failure_truthfully_retained", False, {"error": type(exc).__name__, "detail": str(exc)})
        scratch_frontend = {"status": "FAIL", "error": str(exc)}

    try:
        vivado_ooc = audit_vivado_ooc_build()
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        check("vivado_2026_ooc_synthesis_and_placement_failure_evidence", False, {"error": type(exc).__name__, "detail": str(exc)})
        vivado_ooc = {"status": "FAIL", "error": str(exc)}

    status = "PASS_EVIDENCE" if not errors else "AUDIT_ERRORS"
    result = {
        "schema": "cu66-v101-independent-evidence-audit-v1",
        "status": status,
        "scope_status": status,
        "baseline": source_scope,
        "auditor": {"path": "scripts/cu66-v101/audit.py", "sha256": sha((ROOT / "scripts/cu66-v101/audit.py").read_bytes()), "method": "Python standard library only; direct artifact hashes and read-only git show; no producer imports or FPGA tools"},
        "input_hashes": dict(sorted(input_hashes.items())),
        "source_scope": source_scope,
        "regressions": regressions,
        "constraints_ledger": ledger_status,
        "scratch_priority_probe": scratch_probe,
        "scratch_frontend": scratch_frontend,
        "vivado_ooc_build": vivado_ooc,
        "checks": checks,
        "errors": errors,
        "qualification": {"v101_complete": False, "vivado_methodology_DRC_CDC_signoff": False, "board_IO_timing_qualified": False, "exact_target_tool_available": bool(vivado_ooc.get("selector_status") == "SYNTHESIS_PASSED_PLACEMENT_RESOURCE_BLOCKED" or ("selected_vivado_2026_1_query" in ledger_status and ledger_status["selected_vivado_2026_1_query"].get("verified"))), "exact_target_synthesis": bool(vivado_ooc.get("synthesis_utilization")), "exact_target_placement_and_route": bool(vivado_ooc.get("component_route_finished")), "hardware_30fps": False, "complete_decode_under_10ms": False},
        "open_gates": ["actual board/controller I/O timing requirements and interface contracts", "exact-part placement/route and resource fit after the synthesis UTLZ-1 block", "resolution and review of synthesis methodology/DRC findings, missing I/O delays, CDC and exceptions", "complete selected CS88 top and hardware qualification"],
    }
    output = ROOT / OUT_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(OUT_PATH)
    print(f"status={status} checks={len(checks)} errors={len(errors)}")
    return 0 if status == "PASS_EVIDENCE" else 1


if __name__ == "__main__":
    sys.exit(main())
