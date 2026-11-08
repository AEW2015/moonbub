#!/usr/bin/env python3
"""Read-only provenance and signoff audit for the CU66 V108 study.

This initial mode audits the immutable selected V107 routed baseline.  The
matrix mode will audit retained V108 evidence without invoking Vivado or
modifying run artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
SELECTION = Path("experiments/python-gamebub-v107/selection.json")
BASELINE_RECEIPT = Path(
    "experiments/python-gamebub-v107/native/20261108T081254078678Z/receipt.json"
)
BASELINE_INPUTS = Path(
    "experiments/python-gamebub-v107/native/20261108T081254078678Z/inputs.json"
)
BASELINE_REPORT_DIR = Path(
    "experiments/python-gamebub-v107/native/20261108T081254078678Z/reports"
)
BASELINE_ROUTE_TIMING = BASELINE_REPORT_DIR / "route-timing-summary.rpt"
BASELINE_ROUTE_STATUS = BASELINE_REPORT_DIR / "route-status.rpt"
BASELINE_XDC = Path(
    "experiments/python-gamebub-v107/native/20261108T081254078678Z/recipe-snapshot/component.xdc"
)
V108_AREA = Path("experiments/python-gamebub-v108")
V108_MATRIX = V108_AREA / "native-matrix.json"
V108_POLICY = V108_AREA / "study-policy.json"
V108_FLOW = Path("fpga/experiments/cu66-v108-flow")
PREPARED_TRIALS = {
    "m0": Path("experiments/python-gamebub-v108/prepared/v108-m0-checkpoint-20261108T091025360164Z-1c4aa7/preflight.json"),
    "m1": Path("experiments/python-gamebub-v108/prepared/v108-m1-checkpoint-20261108T091025420549Z-b4573b/preflight.json"),
    "m2": Path("experiments/python-gamebub-v108/prepared/v108-m2-checkpoint-20261108T091500758277Z-dfb719/preflight.json"),
}
GRANTS = {
    "m0": Path("experiments/python-gamebub-v108/coordination/m0-grant.json"),
    "m1": Path("experiments/python-gamebub-v108/coordination/m1-grant.json"),
    "m2": Path("experiments/python-gamebub-v108/coordination/m2-grant.json"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def active_native_dispatches() -> list[str]:
    """Return dispatched native jobs not proven terminal by completion+receipt."""
    coordination = REPO / V108_AREA / "coordination"
    completions: dict[str, dict[str, Any]] = {}
    for path in coordination.glob("native-completion-*.json"):
        entry = load_json(path)
        completions[entry.get("dispatch", "")] = entry
    receipts = []
    for path in (REPO / V108_AREA / "native").glob("*/receipt.json"):
        try:
            receipts.append((path, load_json(path)))
        except (OSError, json.JSONDecodeError):
            continue
    active: list[str] = []
    for path in coordination.glob("native-dispatch-*.json"):
        record = load_json(path)
        path_rel = path.relative_to(REPO).as_posix()
        completion = completions.get(path_rel)
        dispatch_hash = sha256(path)
        matched_receipt = next((receipt for _, receipt in receipts
                                if receipt.get("predispatch", {}).get("path") == path_rel and
                                receipt.get("predispatch", {}).get("sha256") == dispatch_hash), None)
        terminal_completion = bool(
            completion and completion.get("schema") == "v108-native-dispatch-completion-v1" and
            completion.get("dispatch_sha256") == dispatch_hash and
            isinstance(completion.get("runner_exit_code"), int)
        )
        terminal_receipt = bool(matched_receipt and matched_receipt.get("status") != "RUNNING")
        if not (terminal_completion and terminal_receipt):
            active.append(record.get("trial_id", path_rel))
    return sorted(active)


def baseline_audit() -> dict[str, Any]:
    selection = load_json(REPO / SELECTION)
    inputs = load_json(REPO / BASELINE_INPUTS)
    receipt = load_json(REPO / BASELINE_RECEIPT)
    report_path = REPO / BASELINE_ROUTE_TIMING
    route_status_path = REPO / BASELINE_ROUTE_STATUS
    report = report_path.read_text(errors="replace")
    route_status = route_status_path.read_text(errors="replace")
    issues: list[str] = []

    source_origins = selection.get("source_origins", {})
    source_hashes = selection.get("source_sha256", {})
    if len(source_origins) != 18 or selection.get("closure_files") != 18:
        issues.append("selected source closure is not exactly 18 files")
    if set(source_origins) != set(source_hashes):
        issues.append("source_origins and source_sha256 keys differ")
    if inputs.get("source_origins") != source_origins:
        issues.append("selected source origins differ from the retained run inputs")
    if inputs.get("source_sha256") != source_hashes:
        issues.append("selected source hashes differ from the retained run inputs")
    if receipt.get("retained_source_snapshot_sha256") != source_hashes:
        issues.append("retained source snapshot hashes differ from selection.json")

    audited_sources = []
    for logical, origin in sorted(source_origins.items()):
        actual = origin["path"]
        expected_hash = origin["sha256"]
        if source_hashes.get(logical) != expected_hash:
            issues.append(f"selection hash disagreement for {logical}")
        for source_path, label in ((Path(actual), "actual"),
                                   (Path("experiments/python-gamebub-v107/native/20261108T081254078678Z/source-snapshot") / logical, "snapshot")):
            full = REPO / source_path
            if not full.is_file():
                issues.append(f"missing {label} source for {logical}: {source_path}")
                continue
            actual_hash = sha256(full)
            if actual_hash != expected_hash:
                issues.append(f"{label} source hash mismatch for {logical}: {source_path}")
        audited_sources.append({"logical_path": logical, "actual_path": actual,
                                "sha256": expected_hash})

    # The selected IDCT path is intentionally a V107 reset implementation
    # derived from the V106 area implementation, not the original V69 file.
    idct = source_origins.get("fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv", {})
    if idct.get("path") != "fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv":
        issues.append("selected IDCT actual source is not the V107 reset-derived file")

    receipt_path = REPO / BASELINE_RECEIPT
    receipt_hash = sha256(receipt_path)
    if receipt_hash != selection.get("receipt_sha256"):
        issues.append("selected receipt SHA-256 disagrees with selection.json")
    if receipt.get("clock_period_ns") != 10.0 or selection.get("clock_period_ns") != 10.0:
        issues.append("baseline fixed clock is not 10 ns")
    if not receipt.get("component_route_finished"):
        issues.append("baseline route did not finish")
    if not receipt.get("clock_loaded_before_synthesis"):
        issues.append("baseline clock was not loaded before synthesis")
    if receipt.get("max_threads") != 2 or receipt.get("memory_limit_bytes") != 8 * 1024**3:
        issues.append("baseline resource receipt is not 2 threads / 8 GiB")
    if receipt.get("hardware_30fps") or receipt.get("complete_validated_decode_under10ms"):
        issues.append("baseline receipt claims a hardware or decode qualification")

    for name, expected in receipt.get("recipe_snapshots_sha256", {}).items():
        recipe = REPO / BASELINE_REPORT_DIR.parent / "recipe-snapshot" / name
        if not recipe.is_file() or sha256(recipe) != expected:
            issues.append(f"baseline recipe snapshot hash mismatch: {name}")
    xdc_hash = sha256(REPO / BASELINE_XDC)
    if receipt.get("recipe_snapshots_sha256", {}).get("component.xdc") != xdc_hash:
        issues.append("baseline constraint snapshot does not match receipt")
    for name, expected in (("route-timing-summary.rpt", None), ("route-status.rpt", None)):
        artifact = receipt.get("artifacts", {}).get(name)
        path = REPO / BASELINE_REPORT_DIR / name
        if not artifact or not path.is_file() or sha256(path) != artifact.get("sha256"):
            issues.append(f"retained report artifact hash mismatch: {name}")

    # Parse individual fields from the detailed summary, avoiding a derived Fmax.
    summary = re.search(
        r"^\s*(-?\d+\.\d+)\s+-?\d+\.\d+\s+(\d+)\s+\d+\s+(-?\d+\.\d+)\s+-?\d+\.\d+\s+(\d+)\s+\d+\s+(-?\d+\.\d+)\s+-?\d+\.\d+\s+(\d+)",
        report, flags=re.MULTILINE)
    if not summary:
        issues.append("could not parse setup/hold/pulse summary row")
        metrics = {}
    else:
        metrics = {
            "wns_ns": float(summary.group(1)),
            "setup_failing_endpoints": int(summary.group(2)),
            "whs_ns": float(summary.group(3)),
            "hold_failing_endpoints": int(summary.group(4)),
            "wpws_ns": float(summary.group(5)),
            "pulse_width_failing_endpoints": int(summary.group(6)),
        }
    expected_metrics = {
        "wns_ns": -2.333, "setup_failing_endpoints": 21433,
        "whs_ns": 0.096, "hold_failing_endpoints": 0,
        "wpws_ns": 3.750, "pulse_width_failing_endpoints": 0,
    }
    if metrics != expected_metrics:
        issues.append(f"baseline routed timing does not match expected metrics: {metrics}")
    for timing_check in ("no_clock", "unconstrained_internal_endpoints", "loops"):
        if not re.search(rf"checking {timing_check} \(0\)", report):
            issues.append(f"baseline timing check {timing_check} is absent or nonzero")

    def count(label: str) -> int | None:
        m = re.search(rf"# of {re.escape(label)}\.*\s*:\s*(\d+)", route_status)
        return int(m.group(1)) if m else None

    routable = count("routable nets")
    fully_routed = count("fully routed nets")
    routing_errors = count("nets with routing errors")
    if routable != fully_routed or routing_errors != 0:
        issues.append("baseline has incomplete routing or routing errors")

    return {
        "schema": "cu66-v108-baseline-audit-v1",
        "source": "V107 selected routed frontier",
        "selection_path": SELECTION.as_posix(),
        "receipt_path": BASELINE_RECEIPT.as_posix(),
        "receipt_sha256": receipt_hash,
        "baseline_commit": inputs.get("baseline_revision"),
        "fixed_clock_period_ns": 10.0,
        "device": receipt.get("part"),
        "top": receipt.get("top"),
        "route_finished": bool(receipt.get("component_route_finished")),
        "vivado_version": "2026.1",
        "source_count": len(audited_sources),
        "source_files": audited_sources,
        "source_sha256_map": {item["logical_path"]: item["sha256"] for item in audited_sources},
        "constraint_sha256": xdc_hash,
        "timing": metrics,
        "timing_check_counts": {k: 0 for k in ("no_clock", "unconstrained_internal_endpoints", "loops")},
        "routing": {"routable_nets": routable, "fully_routed_nets": fully_routed,
                    "routing_errors": routing_errors},
        "resource_limits": {"threads": receipt.get("max_threads"),
                             "memory_limit_bytes": receipt.get("memory_limit_bytes")},
        "derived_fmax_mhz": None,
        "hardware_30fps": False,
        "complete_validated_decode_under10ms": False,
        "audit_pass": not issues,
        "issues": issues,
    }


def preflight_audit(trial_id: str) -> dict[str, Any]:
    """Independently verify a prepared checkpoint run and its active grant."""
    errors: list[str] = []

    def require(condition: bool, reason: str) -> None:
        if not condition:
            errors.append(reason)

    preflight_rel = PREPARED_TRIALS[trial_id]
    grant_rel = GRANTS[trial_id]
    preflight_path = REPO / preflight_rel
    grant_path = REPO / grant_rel
    pre = load_json(preflight_path)
    grant = load_json(grant_path)
    matrix_path = REPO / V108_MATRIX
    policy_path = REPO / V108_POLICY
    matrix = load_json(matrix_path)
    policy = load_json(policy_path)
    preflight_sha = sha256(preflight_path)
    grant_sha = sha256(grant_path)
    matrix_sha = sha256(matrix_path)
    policy_sha = sha256(policy_path)
    trial = next((x for x in matrix.get("trials", []) if x.get("id") == trial_id), None)
    contract = matrix.get("source_contract", {})

    require(pre.get("schema") == "v108-native-preflight-v1", "unexpected preflight schema")
    require(pre.get("status") == "PREPARED_NOT_RUN" and pre.get("actual_native_run") is False,
            "preflight is not a prepared, unrun trial")
    require(pre.get("trial_id") == trial_id and pre.get("start_mode") == "checkpoint",
            "preflight trial identity or start mode is wrong")
    require(trial is not None and matrix.get("schema") == "v108-frozen-implementation-matrix-v1",
            "frozen matrix is missing this trial or has an unexpected schema")
    require(pre.get("native_matrix_path") == V108_MATRIX.as_posix() and
            pre.get("native_matrix_sha256") == matrix_sha == policy.get("native_matrix_sha256"),
            "preflight/policy matrix binding mismatch")
    require(policy.get("native_matrix_path") == V108_MATRIX.as_posix(), "policy matrix path mismatch")
    require(pre.get("source_contract") == contract, "preflight source contract differs from frozen matrix")
    require(pre.get("source_sha256") == contract.get("source_sha256") and
            pre.get("source_origins") == contract.get("source_origins"),
            "preflight source map differs from frozen matrix")
    require(len(contract.get("source_sha256", {})) == 18 and
            contract.get("closure_files") == 18 and contract.get("RTL_files") == 17,
            "frozen source closure is not 17 RTL files plus one header")
    require(pre.get("clock_period_ns") == matrix.get("clock_period_ns") ==
            policy.get("clock_period_ns") == 10.0, "clock is not fixed at 10 ns")
    require(pre.get("part") == matrix.get("part") == policy.get("part") == "xc7a100tcsg324-1",
            "device part does not match frozen policy")
    require(pre.get("limits") == {
                "timeout_seconds": policy.get("native_timeout_seconds"),
                "max_threads": policy.get("native_max_threads"),
                "cpus": policy.get("native_cpus"),
                "memory_limit_bytes": policy.get("native_memory_limit_bytes"),
                "memory_swap_limit_bytes": policy.get("native_memory_swap_limit_bytes"),
            }, "preflight resource limits differ from policy")
    require(pre.get("limits", {}).get("timeout_seconds") == 2400 and
            pre.get("limits", {}).get("max_threads") == 2 and
            pre.get("limits", {}).get("cpus") == 2 and
            pre.get("limits", {}).get("memory_limit_bytes") == 8 * 1024**3 and
            pre.get("limits", {}).get("memory_swap_limit_bytes") == 8 * 1024**3,
            "preflight does not use the approved 2400 s / 2 CPU / 8 GiB cap")
    require(policy.get("max_heavy_jobs") == matrix.get("max_heavy_jobs") == 2 and
            policy.get("max_native_initial_trials") == matrix.get("initial_trial_limit") == 6 and
            policy.get("max_native_clean_repeats") == matrix.get("planned_clean_repeat_limit") == 1,
            "policy trial caps or global heavy-job cap disagree with frozen matrix")
    require(len(matrix.get("trials", [])) == 6 and
            [x.get("id") for x in matrix.get("trials", [])] == [f"m{i}" for i in range(6)],
            "matrix is not the frozen six-trial proposal")
    require(trial is not None and pre.get("directives") == {
                k: trial.get(k) for k in ("opt", "place", "phys_opt", "phys_opt_stage", "route")
            }, "trial directives differ from its matrix row")

    # Re-derive each frozen input hash from the corresponding immutable source.
    bindings = (
        ("selection_path", "selection_sha256"),
        ("parent_receipt", "parent_receipt_sha256"),
        ("parent_inputs", "parent_inputs_sha256"),
        ("canonical_qualification", "canonical_sha256"),
        ("clock_constraints", "clock_constraints_sha256"),
    )
    for path_key, hash_key in bindings:
        source = REPO / contract.get(path_key, "")
        require(source.is_file() and sha256(source) == contract.get(hash_key),
                f"frozen source contract hash mismatch: {path_key}")

    selection = load_json(REPO / contract.get("selection_path", ""))
    parent_receipt = load_json(REPO / contract.get("parent_receipt", ""))
    parent_inputs = load_json(REPO / contract.get("parent_inputs", ""))
    canonical = load_json(REPO / contract.get("canonical_qualification", ""))
    require(selection.get("source_origins") == contract.get("source_origins"),
            "frozen source origins differ from selected V107 mapping")
    require(selection.get("source_sha256") == contract.get("source_sha256"),
            "frozen source hashes differ from selected V107 mapping")
    require(parent_inputs.get("source_origins") == contract.get("source_origins") and
            parent_inputs.get("source_sha256") == contract.get("source_sha256"),
            "parent run input source map differs from frozen contract")
    require(parent_receipt.get("clock_loaded_before_synthesis") is True and
            contract.get("parent_clock_loaded_before_synthesis") is True,
            "parent clock was not proven loaded before synthesis")
    require(parent_receipt.get("routing_checkpoint_written") is True and
            parent_receipt.get("source_snapshot_unchanged") is True,
            "parent route/source snapshot qualification is missing")
    require(canonical.get("status") == "PASS_EXACT_THRESHOLD_CANONICAL" and
            canonical.get("actual_RTL_run") is True,
            "selected source set lacks canonical RTL qualification")

    actual_source_map = {v["path"]: v["sha256"] for v in contract.get("source_origins", {}).values()}
    canonical_source_map = {k: v for k, v in canonical.get("source_sha256", {}).items()
                            if Path(k).suffix in (".sv", ".svh")}
    require(len(actual_source_map) == 18 and actual_source_map == canonical_source_map,
            "selected source aliases differ from canonical qualified actual files")
    for alias, entry in contract.get("source_origins", {}).items():
        actual = REPO / entry["path"]
        require(actual.is_file() and sha256(actual) == entry["sha256"] ==
                contract["source_sha256"].get(alias), f"source hash mismatch: {alias}")

    checkpoint = contract.get("synthesis_checkpoint", {})
    dcp = Path(checkpoint.get("external_path", ""))
    require(dcp.is_file() and sha256(dcp) == checkpoint.get("sha256") ==
            pre.get("parent_checkpoint_sha256_before"),
            "parent SYNTH checkpoint hash does not match the immutable V107 DCP")
    require(dcp.is_file() and dcp.stat().st_size == checkpoint.get("bytes"),
            "parent SYNTH checkpoint size does not match matrix contract")

    build = Path(pre.get("prepared_build", ""))
    require(build.is_dir(), "external prepared build directory is missing")
    prepared_inputs_path = build / "inputs.json"
    require(prepared_inputs_path.is_file() and sha256(prepared_inputs_path) ==
            pre.get("prepared_inputs_sha256"), "prepared inputs hash mismatch")
    if prepared_inputs_path.is_file():
        prepared_inputs = load_json(prepared_inputs_path)
        require(prepared_inputs.get("trial_id") == trial_id and
                prepared_inputs.get("start_mode") == "checkpoint" and
                prepared_inputs.get("synthesis_executed") is False and
                prepared_inputs.get("synthesis_strategy") == "RuntimeOptimized",
                "prepared inputs do not describe a checkpoint-start, no-new-synthesis run")
        require(prepared_inputs.get("source_sha256") == contract.get("source_sha256") and
                prepared_inputs.get("source_origins") == contract.get("source_origins") and
                prepared_inputs.get("native_matrix_sha256") == matrix_sha,
                "prepared inputs source or matrix identity mismatch")
        require(prepared_inputs.get("directives") == pre.get("directives") and
                prepared_inputs.get("recipe_sha256") == pre.get("recipe_sha256"),
                "prepared inputs directives/recipe hash differ from preflight")
        for source_path, expected in prepared_inputs.get("source_sha256", {}).items():
            snap = build / "snapshot" / source_path
            require(snap.is_file() and sha256(snap) == expected,
                    f"prepared external source snapshot mismatch: {source_path}")

    for name, expected in pre.get("recipe_sha256", {}).items():
        external = build / name
        prepared = REPO / V108_AREA / "prepared" / build.name / name
        flow_source = REPO / V108_FLOW / name if name != "inputs.tcl" else None
        require(external.is_file() and sha256(external) == expected,
                f"external prepared recipe hash mismatch: {name}")
        require(prepared.is_file() and sha256(prepared) == expected,
                f"retained prepared recipe hash mismatch: {name}")
        if flow_source is not None:
            require(flow_source.is_file() and sha256(flow_source) == expected,
                    f"current flow recipe differs from prepared {name}")
    require(pre.get("source_contract", {}).get("clock_constraints_sha256") ==
            pre.get("recipe_sha256", {}).get("component.xdc"),
            "prepared constraints do not match frozen contract")

    # Ensure preparation tools and parser evidence are still the files/hashes audited.
    for relpath, expected in pre.get("tooling_sha256", {}).items():
        tool = REPO / relpath
        require(tool.is_file() and sha256(tool) == expected,
                f"prepared tooling hash mismatch: {relpath}")
    parser = pre.get("parser_self_test", {})
    require(parser.get("status") == "PASS_EXISTING_NATIVE_REPORT_PARSER" and
            parser.get("observed", {}).get("clock_10ns") is True and
            parser.get("observed", {}).get("component_internal_100MHz_pass") is False,
            "native report parser evidence or 100 MHz baseline status is invalid")
    for relpath, expected in parser.get("reports", {}).items():
        report_file = REPO / relpath
        require(report_file.is_file() and sha256(report_file) == expected,
                f"parser baseline report hash mismatch: {relpath}")

    # Count only immutable dispatches still lacking both a terminal completion
    # record and terminal receipt. Historical enabled grants do not consume a slot.
    active_jobs = active_native_dispatches()
    global_cap = policy.get("max_heavy_jobs")
    require(isinstance(global_cap, int) and len(active_jobs) + 1 <= global_cap,
            "the current active dispatches plus this grant exceed the global heavy-job cap")
    require(grant.get("enabled") is True and grant.get("heavy_slot_granted") is True and
            grant.get("trial_id") == trial_id and grant.get("start_mode") == "checkpoint" and
            grant.get("max_global_heavy_jobs") == 2 and
            grant.get("native_matrix_sha256") == matrix_sha,
            "trial grant is not enabled for this exact matrix/trial")
    require(grant.get("preflight") == preflight_rel.as_posix() and
            grant.get("preflight_sha256") == preflight_sha,
            "grant does not bind the exact preflight file")

    return {
        "schema": "v108-native-preflight-audit-v1",
        "status": "PASS_V108_NATIVE_PREFLIGHT_AUDIT" if not errors else "FAIL_V108_NATIVE_PREFLIGHT_AUDIT",
        "trial_id": trial_id,
        "preflight": preflight_rel.as_posix(),
        "preflight_sha256": preflight_sha,
        "grant": grant_rel.as_posix(),
        "grant_sha256": grant_sha,
        "policy_sha256": policy_sha,
        "native_matrix_path": V108_MATRIX.as_posix(),
        "native_matrix_sha256": matrix_sha,
        "source_count": len(contract.get("source_sha256", {})),
        "parent_synthesis_checkpoint_sha256": checkpoint.get("sha256"),
        "parent_synthesis_checkpoint_bytes": checkpoint.get("bytes"),
        "fixed_clock_period_ns": pre.get("clock_period_ns"),
        "constraint_sha256": contract.get("clock_constraints_sha256"),
        "directives": pre.get("directives"),
        "global_heavy_job_cap": policy.get("max_heavy_jobs"),
        "active_native_dispatches_before_grant": active_jobs,
        "active_native_dispatch_count_before_grant": len(active_jobs),
        "active_native_dispatch_count_with_grant": len(active_jobs) + 1,
        "audit_errors": errors,
    }


def receipt_audit(trial_id: str) -> dict[str, Any]:
    """Audit one terminal native receipt and its copied evidence, read-only."""
    errors: list[str] = []

    def require(condition: bool, reason: str) -> None:
        if not condition:
            errors.append(reason)

    receipts = []
    for receipt_path in (REPO / V108_AREA / "native").glob("*/receipt.json"):
        candidate = load_json(receipt_path)
        if candidate.get("trial_id") == trial_id:
            receipts.append((receipt_path, candidate))
    require(len(receipts) == 1, f"expected exactly one retained receipt for {trial_id}, found {len(receipts)}")
    if len(receipts) != 1:
        return {"schema": "v108-native-receipt-audit-v1", "status": "FAIL_V108_NATIVE_RECEIPT_AUDIT",
                "trial_id": trial_id, "audit_errors": errors}
    receipt_path, receipt = receipts[0]
    output_dir = receipt_path.parent
    inputs_path = output_dir / "inputs.json"
    inputs = load_json(inputs_path) if inputs_path.is_file() else {}
    predispatch_path = output_dir / "predispatch.json"
    dispatch = load_json(predispatch_path) if predispatch_path.is_file() else {}
    dispatch_path = REPO / dispatch.get("independent_audit", "")
    gate = load_json(dispatch_path) if dispatch_path.is_file() else {}
    matrix_path = REPO / V108_MATRIX
    matrix = load_json(matrix_path)
    matrix_sha = sha256(matrix_path)
    policy_path = REPO / V108_POLICY
    policy_sha = sha256(policy_path)
    row = next((x for x in matrix.get("trials", []) if x.get("id") == trial_id), None)

    require(receipt.get("schema") == "v108-native-implementation-trial-v1", "unexpected receipt schema")
    require(receipt.get("status") in ("COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN", "STOPPED_RESOURCE_OR_TIME_GATE", "TOOL_OR_BUILD_FAILED", "ROUTE_FINISHED_REPORT_PARSE_FAILED"),
            "receipt has no recognized terminal status")
    require(receipt.get("trial_id") == trial_id and inputs.get("trial_id") == trial_id,
            "receipt/input trial identity mismatch")
    require(receipt.get("status") != "RUNNING", "trial is still running; terminal audit is premature")
    require(receipt.get("native_matrix_path") == V108_MATRIX.as_posix() and
            receipt.get("native_matrix_sha256") == matrix_sha and
            inputs.get("native_matrix_sha256") == matrix_sha and
            dispatch.get("native_matrix_sha256") == matrix_sha,
            "receipt/input/dispatch matrix binding mismatch")
    require(row is not None and receipt.get("directives") == inputs.get("directives") == {
                k: row.get(k) for k in ("opt", "place", "phys_opt", "phys_opt_stage", "route")
            }, "receipt directives differ from frozen matrix row")
    contract = matrix.get("source_contract", {})
    require(receipt.get("source_contract") == inputs.get("source_contract") == contract,
            "receipt source contract differs from frozen matrix")
    require(receipt.get("source_sha256") == inputs.get("source_sha256") == contract.get("source_sha256") and
            receipt.get("source_origins") == inputs.get("source_origins") == contract.get("source_origins"),
            "receipt source hashes/origins differ from frozen source contract")
    require(receipt.get("part") == matrix.get("part") == "xc7a100tcsg324-1" and
            receipt.get("top") == matrix.get("top") and
            receipt.get("clock_period_ns") == matrix.get("clock_period_ns") == 10.0,
            "receipt part/top/fixed clock differs from matrix")
    require(receipt.get("start_mode") == "checkpoint" and receipt.get("synthesis_executed") is False and
            receipt.get("synthesis_checkpoint_generated_in_this_run") is False,
            "matrix run synthesized anew instead of starting from the frozen parent checkpoint")
    require(receipt.get("clock_inherited_from_parent_checkpoint") is True and
            receipt.get("parent_clock_loaded_before_synthesis") is True,
            "fixed clock inheritance from the parent SYNTH checkpoint is not proven")

    # Verify the copied immutable dispatch, launch gate, and associated grant bindings.
    expected_dispatch_hash = receipt.get("predispatch", {}).get("sha256")
    require(predispatch_path.is_file() and sha256(predispatch_path) == expected_dispatch_hash,
            "retained predispatch JSON hash differs from receipt")
    require(dispatch.get("status") == "DISPATCHED_TO_RUNNER" and dispatch.get("trial_id") == trial_id and
            dispatch.get("start_mode") == "checkpoint", "predispatch identity/status mismatch")
    for key in ("preflight", "preflight_sha256", "grant", "grant_sha256", "policy", "policy_sha256",
                "independent_audit", "independent_audit_sha256", "native_matrix_sha256"):
        require(receipt.get("predispatch", {}).get("record", {}).get(key) == dispatch.get(key),
                f"receipt nested dispatch differs from copied dispatch: {key}")
    audit_path = REPO / dispatch.get("independent_audit", "")
    require(audit_path.is_file() and sha256(audit_path) == dispatch.get("independent_audit_sha256"),
            "the prelaunch audit gate file/hash no longer matches dispatch")
    require(gate.get("status") == "PASS_V108_NATIVE_PREFLIGHT_AUDIT" and
            gate.get("preflight_sha256") == dispatch.get("preflight_sha256") and
            gate.get("grant_sha256") == dispatch.get("grant_sha256") and
            gate.get("policy_sha256") == dispatch.get("policy_sha256"),
            "predispatch does not bind a passing immutable audit gate")

    prepared_inputs_hash = receipt.get("source_manifest_sha256")
    require(inputs_path.is_file() and sha256(inputs_path) == prepared_inputs_hash,
            "retained input manifest hash differs from receipt")
    require(receipt.get("source_snapshot_readonly_mount") is True and
            receipt.get("source_snapshot_unchanged") is True,
            "run source snapshot was not read-only/unchanged")
    require(receipt.get("parent_synthesis_checkpoint") == contract.get("synthesis_checkpoint"),
            "receipt parent checkpoint differs from frozen source contract")
    dcp = Path(contract.get("synthesis_checkpoint", {}).get("external_path", ""))
    expected_dcp = contract.get("synthesis_checkpoint", {}).get("sha256")
    require(receipt.get("parent_checkpoint_sha256_before") == expected_dcp and
            dcp.is_file() and sha256(dcp) == expected_dcp,
            "parent SYNTH checkpoint identity/hash mismatch before run")
    require(receipt.get("parent_checkpoint_sha256_after") == expected_dcp,
            "parent SYNTH checkpoint changed during the run")

    # Hash each retained source and recipe copy rather than trusting summary fields.
    for name, expected in contract.get("source_sha256", {}).items():
        copied_source = output_dir / "source-snapshot" / name
        require(copied_source.is_file() and sha256(copied_source) == expected,
                f"retained route source hash mismatch: {name}")
    for name, expected in inputs.get("recipe_sha256", {}).items():
        copied_recipe = output_dir / "recipe-snapshot" / name
        require(copied_recipe.is_file() and sha256(copied_recipe) == expected and
                receipt.get("recipe_sha256", {}).get(name) == expected,
                f"retained route recipe hash mismatch: {name}")
    require(inputs.get("recipe_sha256", {}).get("component.xdc") == contract.get("clock_constraints_sha256"),
            "retained XDC is not the frozen matrix clock constraint")

    # Check resources, monitoring history, and terminal reason against policy.
    require(policy_path.is_file(), "study policy file is missing")
    policy = load_json(policy_path)
    require(receipt.get("cpus") == policy.get("native_cpus") == 2 and
            receipt.get("max_threads") == policy.get("native_max_threads") == 2 and
            receipt.get("memory_limit_bytes") == policy.get("native_memory_limit_bytes") == 8 * 1024**3 and
            receipt.get("memory_swap_limit_bytes") == policy.get("native_memory_swap_limit_bytes") == 8 * 1024**3 and
            receipt.get("timeout_seconds") == policy.get("native_timeout_seconds") == 2400,
            "run resource limits differ from approved policy")
    require(receipt.get("observed_exit_code") == 0 and receipt.get("monitor_stop_reason") is None,
            "native run had a nonzero exit or resource/time stop")
    samples = receipt.get("memory_samples", [])
    require(bool(samples), "terminal receipt has no resource samples")
    for sample in samples:
        require(sample.get("MemAvailable_bytes", 0) >= 4 * 1024**3 and
                sample.get("PSI_full_avg10", 100) < 5,
                "resource samples crossed the hard-stop threshold")
    resource_before = receipt.get("resource_before", {})
    require(resource_before.get("MemAvailable_bytes", 0) >= 8 * 1024**3 and
            resource_before.get("PSI_full_avg10", 100) < 1,
            "run launch resource gate was not met")

    # Verify every retained output file and compare native parsing from its copy.
    retained = receipt.get("retained_artifact_sha256", {})
    require(bool(retained), "receipt has no retained artifact checksum manifest")
    for relpath, expected in retained.items():
        artifact = output_dir / relpath
        require(artifact.is_file() and sha256(artifact) == expected,
                f"retained artifact hash mismatch: {relpath}")
    result = receipt.get("result")
    if receipt.get("component_route_finished"):
        require(receipt.get("status") == "COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN" and
                receipt.get("observed_exit_code") == 0 and result is not None,
                "route completion status/result fields disagree")
        runner_copy = output_dir / "run_native.py"
        runner_hash = retained.get("run_native.py")
        require(runner_copy.is_file() and sha256(runner_copy) == runner_hash == receipt.get("runner_sha256"),
                "retained native parser/runner hash mismatch")
        if runner_copy.is_file():
            spec = importlib.util.spec_from_file_location("v108_retained_runner", runner_copy)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                reparsed = module.parse_reports(output_dir / "reports")
                require(reparsed == result, "independent reparse differs from receipt result")
            except Exception as exc:
                errors.append(f"retained native reports could not be reparsed: {exc!r}")
        # Keep a completed route with a negative setup slack as a valid failed
        # timing observation; this audit never elevates the design to a pass.
        require(result.get("clock_10ns") is True, "native timing reports do not prove the fixed 10 ns clock")
        timing = result.get("timing", {})
        checks = result.get("check_timing", {})
        routing = result.get("routing", {})
        require(all(checks.get(k) == 0 for k in
                    ("no_clock", "unconstrained_internal_endpoints", "loops", "latch_loops")),
                "native timing checks report missing clocks, unconstrained internals, or loops")
        require(routing.get("all_routable_nets_routed") is True and
                routing.get("zero_routing_errors") is True and
                routing.get("fully_routed_nets") == routing.get("routable_nets"),
                "completed route has unrouted nets or routing errors")
        require(receipt.get("component_route_finished") is True and
                receipt.get("hardware_30fps") is False and
                receipt.get("complete_validated_decode_under10ms") is False and
                receipt.get("full_custom_top_qualified") is False and
                receipt.get("board_IO_timing_qualified") is False,
                "component run claims a hardware/full-top qualification")
    else:
        require(not result, "non-route terminal run unexpectedly contains route results")

    return {
        "schema": "v108-native-receipt-audit-v1",
        "status": "PASS_V108_NATIVE_RECEIPT_AUDIT" if not errors else "FAIL_V108_NATIVE_RECEIPT_AUDIT",
        "trial_id": trial_id,
        "receipt": receipt_path.relative_to(REPO).as_posix(),
        "receipt_sha256": sha256(receipt_path),
        "native_matrix_sha256": matrix_sha,
        "audit_basis": "Independent provenance/resource/report audit; timing qualification reported separately.",
        "terminal_run_status": receipt.get("status"),
        "component_route_finished": receipt.get("component_route_finished", False),
        "fixed_clock_period_ns": receipt.get("clock_period_ns"),
        "timing": result.get("timing") if result else None,
        "component_internal_100MHz_pass": result.get("component_internal_100MHz_pass") if result else False,
        "hardware_30fps": receipt.get("hardware_30fps"),
        "complete_validated_decode_under10ms": receipt.get("complete_validated_decode_under10ms"),
        "audit_errors": errors,
    }
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="write audit JSON to this path")
    parser.add_argument("--preflight", choices=sorted(PREPARED_TRIALS),
                        help="independently audit one prepared V108 trial and grant")
    parser.add_argument("--receipt", choices=[f"m{i}" for i in range(6)],
                        help="independently audit one terminal V108 native receipt")
    args = parser.parse_args()
    if args.preflight and args.receipt:
        parser.error("choose either --preflight or --receipt")
    result = (preflight_audit(args.preflight) if args.preflight else
              receipt_audit(args.receipt) if args.receipt else baseline_audit())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    passed = (result.get("status") == "PASS_V108_NATIVE_PREFLIGHT_AUDIT"
              if args.preflight else
              result.get("status") == "PASS_V108_NATIVE_RECEIPT_AUDIT" if args.receipt else
              result.get("audit_pass", False))
    if args.output:
        if not passed:
            sys.stdout.write(payload)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.preflight or args.receipt:
            # The launch gate is immutable dispatch evidence. Refuse to replace
            # a launch gate or completion record if the audit is rerun.
            with args.output.open("x") as f:
                f.write(payload)
        else:
            args.output.write_text(payload)
    else:
        sys.stdout.write(payload)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
