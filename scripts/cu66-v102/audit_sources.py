#!/usr/bin/env python3
"""Deterministic stdlib source/provenance audit for the isolated V102 candidates.

This checks frozen baseline inputs, candidate source pins, and narrowly approved
text substitutions. It does not launch RTL or vendor tools and does not qualify
functional, synthesis, placement, timing, or physical results.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "6b36a3228804953c50c10db61f620cad5412ecce"
PROFILE = "experiments/python-gamebub-v99/profile.json"
PROFILE_SHA256 = "8e17b24afbefe32ca00b2606ee80a3a70dd06e9050e76d50c9698fd524e735be"
INVENTORY = "experiments/python-gamebub-v100/inventory.json"
MEMORY_CHANGE = "experiments/python-gamebub-v102/memory/change.json"
PREDICATE_CHANGE = "experiments/python-gamebub-v102/predicate/change.json"
OUT = "experiments/python-gamebub-v102/source-audit.json"

checks: list[dict] = []
errors: list[str] = []
inputs: dict[str, str] = {}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read(path: str) -> bytes:
    b = (ROOT / path).read_bytes()
    inputs[path] = sha(b)
    return b

def check(name: str, ok: bool, detail=None) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok: errors.append(name)

def git_blob(rev: str, path: str) -> bytes | None:
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout if p.returncode == 0 else None

def ancestor_exists() -> tuple[bool, bool]:
    exists = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}^{{commit}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    ancestor = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASELINE, "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
    return exists, ancestor

def span_hashes(source: bytes, candidate: bytes, start: bytes, end: bytes) -> tuple[bool, str, str]:
    try:
        si = source.index(start); ei = source.index(end, si + len(start)) + len(end) - 1
        ci = candidate.index(start); ce = candidate.index(end, ci + len(start)) + len(end) - 1
    except ValueError:
        return False, "", ""
    prefix_s, suffix_s = source[:si], source[ei:]
    prefix_c, suffix_c = candidate[:ci], candidate[ce:]
    return prefix_s == prefix_c and suffix_s == suffix_c, sha(prefix_s), sha(suffix_s)

def audit_frozen_inputs() -> None:
    exists, ancestor = ancestor_exists()
    check("baseline_commit_exists_and_is_ancestor", exists and ancestor, {"baseline": BASELINE, "exists": exists, "ancestor_of_head": ancestor})
    profile = read(PROFILE)
    blob = git_blob(BASELINE, PROFILE)
    check("frozen_profile_matches_pinned_baseline_blob", sha(profile) == PROFILE_SHA256 and blob == profile,
          {"path": PROFILE, "sha256": sha(profile), "pinned_sha256": PROFILE_SHA256, "baseline_blob_equal": blob == profile})
    inv = json.loads(read(INVENTORY))
    rows = inv.get("source_files", [])
    mismatches = []
    absent = []
    base_diffs = []
    for row in rows:
        path, expected = row.get("path", ""), row.get("sha256")
        try: data = read(path)
        except FileNotFoundError:
            absent.append(path); continue
        if sha(data) != expected: mismatches.append(path)
        old = git_blob(BASELINE, path)
        if old is None or old != data: base_diffs.append(path)
    check("baseline_v100_rtl_inventory_unchanged", bool(rows) and not mismatches and not absent and not base_diffs,
          {"count": len(rows), "hash_mismatches": mismatches, "missing": absent, "baseline_blob_differences": base_diffs})

def audit_memory() -> dict:
    manifest = json.loads(read(MEMORY_CHANGE))
    original_path, candidate_path = manifest["original"], manifest["candidate"]
    old, new = read(original_path), read(candidate_path)
    expected_old_hash = "9c26be0c1fd8ec996c2bc94a97468b5f29a25b98f97f2a6e80b29be470a8243c"
    original_ok = sha(old) == expected_old_hash and git_blob(BASELINE, original_path) == old and manifest.get("original_sha256") == sha(old)
    check("memory_original_is_baseline_pinned_rtl", original_ok, {"path": original_path, "sha256": sha(old), "manifest_sha256": manifest.get("original_sha256")})
    # Construct the candidate from exact approved operations. No other byte may change.
    old_block = (b"    always_ff @(posedge clk) begin\n"
                 b"        if(stage_write)memory[received[15:0]]<=in_data;\n"
                 b"        replay_rsp_valid<=replay_req&&replay_ready;\n")
    new_block = (b"    // One registered, read-first packet RAM port. Selection retains stage priority.\n"
                 b"    logic memory_read_enable;\n"
                 b"    logic [15:0] memory_read_address;\n"
                 b"    assign memory_read_enable=stage_read_req || (replay_req && replay_ready);\n"
                 b"    assign memory_read_address=stage_read_req ? fetch_addr[15:0] : replay_addr[15:0];\n"
                 b"    always_ff @(posedge clk) begin\n"
                 b"        if(stage_write)memory[received[15:0]]<=in_data;\n"
                 b"        if(memory_read_enable)ram_data<=memory[memory_read_address];\n"
                 b"    end\n\n"
                 b"    always_ff @(posedge clk) begin\n"
                 b"        replay_rsp_valid<=replay_req&&replay_ready;\n")
    expected = old.replace(old_block, new_block, 1)
    expected = expected.replace(b"            ram_data<=memory[fetch_addr[15:0]];\n", b"", 1)
    expected = expected.replace(b"            ram_data<=memory[replay_addr[15:0]];\n", b"", 1)
    # The above exact transform must itself match one instance of each operation.
    transform_ok = old.count(old_block) == 1 and old.count(b"            ram_data<=memory[fetch_addr[15:0]];\n") == 1 and old.count(b"            ram_data<=memory[replay_addr[15:0]];\n") == 1 and new == expected
    header_old = old[:old.index(b");", old.index(b"module cs88_admission_v91i2a")) + 2]
    header_new = new[:new.index(b");", new.index(b"module cs88_admission_v91i2a")) + 2]
    check("memory_candidate_exact_approved_read_template_edit", transform_ok, {"candidate": candidate_path, "candidate_sha256": sha(new), "manifest_sha256": manifest.get("candidate_sha256"), "header_unchanged": header_old == header_new})
    check("memory_public_header_and_ports_unchanged", header_old == header_new, {"header_sha256": sha(header_new)})
    check("memory_manifest_schema_and_baseline", manifest.get("schema") == "v102-memory-change-v1" and manifest.get("baseline") == BASELINE and manifest.get("candidate_sha256") == sha(new), {"schema": manifest.get("schema"), "baseline": manifest.get("baseline"), "manifest_candidate_hash_matches": manifest.get("candidate_sha256") == sha(new)})
    return {"original": original_path, "original_sha256": sha(old), "candidate": candidate_path, "candidate_sha256": sha(new), "exact_edit": transform_ok}

def audit_predicate() -> dict:
    manifest = json.loads(read(PREDICATE_CHANGE))
    old_info, new_info = manifest["original"], manifest["candidate"]
    old_path, new_path = old_info["path"], new_info["path"]
    old, new = read(old_path), read(new_path)
    orig_ok = sha(old) == old_info.get("sha256") and git_blob(BASELINE, old_path) == old
    check("predicate_original_is_baseline_pinned_rtl", orig_ok, {"path": old_path, "sha256": sha(old), "manifest_sha256": old_info.get("sha256")})
    start = b"    function automatic logic safe_hidden(input logic [1:0] p,input logic [12:0] t);\n"
    end = b"    endfunction\n"
    span_ok, prefix_hash, suffix_hash = span_hashes(old, new, start, end)
    hash_ok = prefix_hash == manifest.get("unchanged_prefix_sha256") and suffix_hash == manifest.get("unchanged_suffix_sha256")
    header_end = old.index(b");", old.index(b"module cu66_reconstruct_stream_v91k")) + 2
    header_same = old[:header_end] == new[:header_end]
    check("predicate_only_safe_hidden_function_body_changed", span_ok and hash_ok, {"candidate": new_path, "candidate_sha256": sha(new), "manifest_candidate_sha256": new_info.get("sha256"), "unchanged_prefix_sha256": prefix_hash, "unchanged_suffix_sha256": suffix_hash, "manifest_hashes_match": hash_ok})
    check("predicate_public_header_and_ports_unchanged", header_same, {"header_sha256": sha(new[:header_end]), "clock_or_state_changes": manifest.get("clock_or_state_changes")})
    check("predicate_manifest_schema_and_baseline", manifest.get("schema") == "v102-predicate-change-v1" and manifest.get("baseline_revision") == BASELINE and new_info.get("sha256") == sha(new), {"schema": manifest.get("schema"), "baseline": manifest.get("baseline_revision"), "manifest_candidate_hash_matches": new_info.get("sha256") == sha(new)})
    return {"original": old_path, "original_sha256": sha(old), "candidate": new_path, "candidate_sha256": sha(new), "approved_span_only": span_ok and hash_ok}

def audit_focused_predicate() -> dict:
    summary_path = "experiments/python-gamebub-v102/predicate/results.json"
    summary = json.loads(read(summary_path))
    report_path = summary.get("selected_report", "")
    try:
        report = json.loads(read(report_path))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        report = {}
    report_dir = str(Path(report_path).parent)
    missing, mismatched = [], []
    artifacts = report.get("artifacts_sha256", {})
    for rel, expected in sorted(artifacts.items()):
        try: actual = sha(read(f"{report_dir}/{rel}"))
        except FileNotFoundError:
            missing.append(rel); continue
        if actual != expected: mismatched.append(rel)
    candidate = report.get("candidate", {})
    candidate_path = "fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv"
    current_candidate_sha = sha(read(candidate_path))
    terminal, replay = report.get("terminal_verdict", {}), report.get("trace_replay", {})
    ok = (
        summary.get("schema") == "v102-predicate-focused-rtl-v1"
        and summary.get("status") == "PASS"
        and report.get("schema") == "v102-predicate-focused-rtl-v1"
        and report.get("status") == "PASS"
        and report.get("baseline_revision") == BASELINE
        and candidate.get("path") == candidate_path
        and candidate.get("sha256") == current_candidate_sha
        and report.get("actual_RTL_run") is True
        and report.get("assertions_disabled_or_downgraded") is False
        and report.get("strict_warnings") is True
        and report.get("cases") == 32768
        and report.get("clock_edges") == 0
        and terminal.get("status") == "TEST_PASS"
        and terminal.get("cases") == 32768
        and terminal.get("clock_edges") == 0
        and replay.get("status") == "PASS"
        and replay.get("rows") == 32768
        and report.get("verification_adapters_preserve_complete_production_body") is True
        and len(artifacts) > 0 and not missing and not mismatched
        and report_path.startswith("experiments/python-gamebub-v102/predicate/attempts/")
    )
    check("predicate_focused_actual_rtl_receipt_and_artifact_hashes", ok, {
        "summary": summary_path, "attempt_report": report_path,
        "summary_status": summary.get("status"), "status": report.get("status"),
        "cases": report.get("cases"), "clock_edges": report.get("clock_edges"),
        "trace_replay": {k: replay.get(k) for k in ("status", "rows", "true_counts", "sha256")},
        "artifact_count": len(artifacts), "missing_artifacts": missing, "mismatched_artifacts": mismatched,
    })
    return {"status": "PASS_EVIDENCE" if ok else "FAIL", "summary": summary_path, "attempt_report": report_path, "cases": report.get("cases"), "clock_edges": report.get("clock_edges"), "artifact_count": len(artifacts)}

def audit_focused_memory() -> dict:
    summary_path = "experiments/python-gamebub-v102/memory/probe-results.json"
    summary = json.loads(read(summary_path))
    receipt_path = summary.get("selected_receipt", "")
    try: receipt_bytes = read(receipt_path); receipt = json.loads(receipt_bytes)
    except (FileNotFoundError, OSError, json.JSONDecodeError): receipt_bytes, receipt = b"", {}
    receipt_hash_ok = bool(receipt_bytes) and sha(receipt_bytes) == summary.get("sha256")
    receipt_dir = str(Path(receipt_path).parent)
    artifacts = receipt.get("artifacts_sha256", {})
    missing, mismatched = [], []
    for rel, expected in sorted(artifacts.items()):
        try: actual = sha(read(f"{receipt_dir}/{rel}"))
        except FileNotFoundError:
            missing.append(rel); continue
        if actual != expected: mismatched.append(rel)
    candidate = receipt.get("candidate", {})
    candidate_path = "fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv"
    current_candidate_sha = sha(read(candidate_path))
    compile_cmds = [c for c in receipt.get("commands", []) if "--build" in c.get("argv", [])]
    commands_ok = bool(receipt.get("commands")) and all(c.get("exit_code") == 0 for c in receipt.get("commands", []))
    compile_argv = compile_cmds[-1].get("argv", []) if compile_cmds else []
    strict_compile = bool(compile_cmds) and "--assert" in compile_argv and "-Wall" in compile_argv and "-Werror" in " ".join(compile_argv)
    ok = (
        summary.get("schema") == "v102-memory-probe-selection-v1"
        and summary.get("status") == "PASS_ACTUAL_CLOCKED_RAM_EQUIVALENCE"
        and receipt.get("schema") == "v102-memory-clocked-probe-v1"
        and receipt.get("status") == "PASS_ACTUAL_CLOCKED_RAM_EQUIVALENCE"
        and receipt.get("baseline") == BASELINE
        and candidate.get("path") == candidate_path
        and candidate.get("sha256") == current_candidate_sha
        and receipt.get("source_sha256", {}).get(candidate_path) == current_candidate_sha
        and commands_ok and strict_compile
        and {r.get("seed") for r in receipt.get("runs", [])} == {102401, 102402}
        and all(r.get("status") == "TEST_PASS" and r.get("cases") == 9536 and r.get("clock_edges") == 9537 and r.get("same_address_read_first_collisions") == 32 for r in receipt.get("runs", []))
        and receipt.get("total_cases") == 19072
        and receipt.get("total_clock_edges") == 19074
        and len(artifacts) > 0 and not missing and not mismatched and receipt_hash_ok
        and receipt_path.startswith("experiments/python-gamebub-v102/memory/attempts/")
    )
    check("memory_focused_actual_rtl_receipt_and_artifact_hashes", ok, {
        "summary": summary_path, "selected_receipt": receipt_path,
        "summary_status": summary.get("status"), "receipt_status": receipt.get("status"),
        "receipt_sha256_matches_selection": receipt_hash_ok,
        "all_commands_pass": commands_ok, "strict_assert_compile_flags": strict_compile,
        "run_count": len(receipt.get("runs", [])), "artifact_count": len(artifacts),
        "missing_artifacts": missing, "mismatched_artifacts": mismatched,
    })
    return {"status": "PASS_EVIDENCE" if ok else "FAIL", "summary": summary_path, "selected_receipt": receipt_path, "receipt_status": receipt.get("status"), "run_count": len(receipt.get("runs", [])), "artifact_count": len(artifacts)}

def audit_paired_regression(variant: str, mode: str) -> dict:
    per_seed_cases, per_seed_directed = (6, 13) if mode == "fresh" else (22, 21)
    total_cases, total_directed = per_seed_cases * 4, per_seed_directed * 4
    summary_path = f"experiments/python-gamebub-v102/regression/{variant}/{mode}/results.json"
    if not (ROOT / summary_path).exists():
        return {"status": "PENDING", "summary": summary_path}
    summary = json.loads(read(summary_path))
    report_path = summary.get("selected_report", "")
    try: report = json.loads(read(report_path))
    except (FileNotFoundError, OSError, json.JSONDecodeError): report = {}
    attempt_dir = str(Path(report_path).parent)
    artifacts = report.get("artifacts_sha256", {})
    missing, mismatched = [], []
    for rel, expected in sorted(artifacts.items()):
        try: actual = sha(read(f"{attempt_dir}/{rel}"))
        except FileNotFoundError:
            missing.append(rel); continue
        if actual != expected: mismatched.append(rel)
    expected_candidates = {
        "memory": [("fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv", "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv")],
        "predicate": [("fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv", "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv")],
        "combined": [("fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv", "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv"),
                     ("fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv", "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv")],
    }[variant]
    expected_candidate_rows = [{"original": orig, "path": path, "sha256": sha(read(path))} for path, orig in expected_candidates]
    rows = report.get("runs", [])
    rows_ok = len(rows) == 2 and {r.get("seed") for r in rows} == {102401, 102402}
    for row in rows:
        for name in ("baseline", "candidate"):
            variant_entry = row.get("variants", {}).get(name, {})
            verdict = variant_entry.get("verdict", {})
            rows_ok &= verdict.get("status") == "TEST_PASS" and verdict.get("seed") == row.get("seed") and verdict.get("cases") == per_seed_cases and verdict.get("directed_checks") == per_seed_directed
        rows_ok &= row.get("equalities", {}).get("stdout") is True and row.get("equalities", {}).get("events") is True
        if mode == "canonical": rows_ok &= row.get("equalities", {}).get("canonical") is True
    commands_ok = bool(report.get("commands")) and all(c.get("exit_code") == 0 for c in report["commands"])
    ok = (
        summary.get("schema") == "v102-paired-regression-v1" and summary.get("status") == "PASS"
        and report.get("schema") == "v102-paired-regression-v1" and report.get("status") == "PASS"
        and report.get("mode") == mode and report.get("variant") == variant
        and report.get("baseline_revision") == BASELINE and report.get("seeds") == [102401, 102402]
        and report.get("actual_RTL_run") is True and report.get("assertions_disabled_or_downgraded") is False
        and report.get("case_profile_runs") == total_cases and report.get("directed_checks") == total_directed
        and report.get("exact_same_seed_transcripts_events_cycles") is True and rows_ok and commands_ok
        and report.get("candidates") == expected_candidate_rows
        and all(report.get("source_sha256", {}).get(row["path"]) == row["sha256"] for row in expected_candidate_rows)
        and len(artifacts) > 0 and not missing and not mismatched
        and report_path.startswith(f"experiments/python-gamebub-v102/regression/{variant}/{mode}/attempts/")
    )
    check(f"{variant}_{mode}_paired_component_regression_receipt_and_artifact_hashes", ok, {
        "summary": summary_path, "attempt_report": report_path,
        "status": report.get("status"), "seeds": report.get("seeds"),
        "variant": variant, "mode": mode, "case_profile_runs": report.get("case_profile_runs"), "directed_checks": report.get("directed_checks"),
        "rows_pass": rows_ok, "commands_pass": commands_ok,
        "artifact_count": len(artifacts), "missing_artifacts": missing, "mismatched_artifacts": mismatched,
    })
    return {"status": "PASS_EVIDENCE" if ok else "FAIL", "summary": summary_path, "attempt_report": report_path, "seeds": report.get("seeds"), "case_profile_runs": report.get("case_profile_runs"), "directed_checks": report.get("directed_checks"), "artifact_count": len(artifacts)}

def main() -> int:
    audit_frozen_inputs()
    memory = audit_memory()
    predicate = audit_predicate()
    focused_predicate = audit_focused_predicate()
    focused_memory = audit_focused_memory()
    regressions = {
        "memory_fresh": audit_paired_regression("memory", "fresh"),
        "memory_canonical": audit_paired_regression("memory", "canonical"),
        "predicate_canonical": audit_paired_regression("predicate", "canonical"),
        "combined_canonical": audit_paired_regression("combined", "canonical"),
    }
    result = {"schema": "v102-source-audit-v1", "status": "PASS_EVIDENCE" if not errors else "FAIL", "baseline": BASELINE, "checks": checks, "candidate_sources": {"memory": memory, "predicate": predicate}, "focused_receipts": {"memory": focused_memory, "predicate": focused_predicate}, "integrated_regression_receipts": regressions, "input_sha256": dict(sorted(inputs.items())), "scope_limit": "Source/provenance and lightweight RTL receipt integrity only. Does not establish full system behavior, synthesis mapping, capacity recovery, placement, timing, or physical qualification."}
    target = ROOT / OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{result['status']}: {len(checks)-len(errors)}/{len(checks)} source/provenance checks; report={OUT}")
    return 0 if not errors else 1

if __name__ == "__main__": raise SystemExit(main())
