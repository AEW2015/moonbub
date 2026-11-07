#!/usr/bin/env python3
"""Independently audit retained V100 inventory and evidence receipts.

This is deliberately a stdlib-only reader. It does not import the physical or
RTL runners and does not launch FPGA, simulator, or synthesis tools.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/python-gamebub-v100/audit.json"
BASELINE = "f403a5f5149de60ebc128ac57911c4912bec0ddf"
INV_PATH = "experiments/python-gamebub-v100/inventory.json"
PROFILE_PATH = "experiments/python-gamebub-v99/profile.json"

checks: list[dict] = []
inputs: dict[str, str] = {}
errors: list[str] = []


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: str) -> bytes:
    p = ROOT / path
    data = p.read_bytes()
    inputs[path] = digest(data)
    return data


def read_json(path: str):
    return json.loads(read_bytes(path))


def check(name: str, passed: bool, detail=None):
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})
    if not passed:
        errors.append(name)


def git_blob(revision: str, path: str) -> bytes | None:
    proc = subprocess.run(["git", "-C", str(ROOT), "show", f"{revision}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout if proc.returncode == 0 else None


def payload(path: str) -> bytes:
    raw = read_bytes(path)
    return gzip.decompress(raw) if path.endswith(".gz") else raw


def verify_artifact_manifest(base: str, manifest: dict) -> dict:
    checked, missing, mismatched = 0, [], []
    for relative, expected in manifest.items():
        path = f"{base}/{relative}"
        expected_hash = expected.get("sha256") if isinstance(expected, dict) else expected
        try:
            actual = digest(read_bytes(path))
        except FileNotFoundError:
            missing.append(relative)
            continue
        checked += 1
        if actual != expected_hash:
            mismatched.append(relative)
    return {"declared": len(manifest), "checked": checked, "missing": missing, "mismatched": mismatched}


inventory = read_json(INV_PATH)
profile_bytes = read_bytes(PROFILE_PATH)
profile = json.loads(profile_bytes)
head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, text=True).stdout.strip()
baseline_exists = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}^{{commit}}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
baseline_is_ancestor = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASELINE, "HEAD"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0
check("frozen_baseline_is_in_checkout_history", baseline_exists and baseline_is_ancestor, {"baseline": BASELINE, "baseline_commit_exists": baseline_exists, "baseline_is_ancestor": baseline_is_ancestor})
profile_hash = digest(profile_bytes)
baseline_profile = git_blob(BASELINE, PROFILE_PATH)
check("frozen_profile_unchanged", baseline_profile == profile_bytes and profile["status"] == "FROZEN_RESEARCH_CANDIDATE_ONLY", {"sha256": profile_hash, "baseline_blob_matches": baseline_profile == profile_bytes, "name": profile.get("name")})
check("inventory_profile_binding", inventory["frozen_profile"]["sha256"] == profile_hash, {"inventory_sha256": inventory["frozen_profile"]["sha256"], "current_sha256": profile_hash})

# Independently recalculate every source and constraint hash in the inventory;
# tracked files must also equal their bytes at the frozen checkout revision.
source_rows = inventory["source_files"]
source_mismatches = []
tracked_baseline_mismatches = []
for row in source_rows:
    path = row["path"]
    current = (ROOT / path).read_bytes() if (ROOT / path).is_file() else b""
    actual = digest(current) if current else None
    if actual != row["sha256"]:
        source_mismatches.append(path)
    baseline_blob = git_blob(BASELINE, path)
    if baseline_blob is not None and baseline_blob != current:
        tracked_baseline_mismatches.append(path)
xdc_mismatches = []
for row in inventory["existing_image"].get("xdc", []):
    path = row["path"]
    current = (ROOT / path).read_bytes() if (ROOT / path).is_file() else b""
    if not current or digest(current) != row["sha256"]:
        xdc_mismatches.append(path)
check("source_inventory_hashes_current", not source_mismatches, {"source_count": len(source_rows), "mismatches": source_mismatches})
check("tracked_baseline_sv_and_support_unchanged", not tracked_baseline_mismatches, {"compared_tracked_sources": len(source_rows) - sum(1 for row in source_rows if git_blob(BASELINE, row["path"]) is None), "mismatches": tracked_baseline_mismatches})
check("constraint_hashes_current", not xdc_mismatches, {"xdc_count": len(inventory["existing_image"].get("xdc", [])), "mismatches": xdc_mismatches})

rtl_summary_path = "experiments/python-gamebub-v100/rtl/results.json"
rtl_attempt_path = "experiments/python-gamebub-v100/rtl/attempts/20261107T193326863575Z-775b4e04/results.json"
rtl_audit_path = "experiments/python-gamebub-v100/rtl/artifact-audit.json"
rtl = read_json(rtl_summary_path)
rtl_attempt = read_json(rtl_attempt_path)
rtl_audit = read_json(rtl_audit_path)
rtl_artifact_audit = verify_artifact_manifest("experiments/python-gamebub-v100/rtl/attempts/20261107T193326863575Z-775b4e04", rtl_attempt.get("artifacts_sha256", {}))
run_checks = []
for row in rtl_attempt.get("runs", []):
    verdict = row.get("terminal_verdict", {})
    run_checks.append({"seed": row.get("seed"), "status": verdict.get("status"), "vectors": verdict.get("vectors"), "cases": verdict.get("cases"), "directed_checks": verdict.get("directed_checks"), "stage_counts": {k: verdict.get(k) for k in ["dense_comparisons", "assembly_comparisons", "dequant_comparisons", "residual_comparisons", "directed_dense_comparisons", "tile_rows"]}})
fresh_ok = (
    rtl.get("status") == "PASS_FRESH_CS88_SIGNED20_DEQUANT_SIGNED24_IDCT_RTL"
    and rtl.get("source_revision") == BASELINE
    and [x.get("seed") for x in run_checks] == [100401, 100402]
    and all(x["status"] == "TEST_PASS" and x["cases"] == 6 and x["directed_checks"] == 13 for x in run_checks)
    and rtl_audit.get("status") == "PASS"
    and rtl_audit.get("attempt_report_sha256") == digest(read_bytes(rtl_attempt_path))
    and rtl_audit.get("terminal_TEST_PASS_seed_count") == 2
    and rtl_artifact_audit["declared"] == 36 and rtl_artifact_audit["checked"] == 36 and not rtl_artifact_audit["missing"] and not rtl_artifact_audit["mismatched"]
)
check("fresh_rtl_seed_and_stage_evidence", fresh_ok, {"report": rtl_attempt_path, "baseline": rtl.get("source_revision"), "runs": run_checks, "artifact_hashes_recomputed": rtl_artifact_audit, "stored_artifact_audit": rtl_audit.get("artifact_hashes_verified"), "golden_report": rtl.get("golden_report")})

converted_summary_path = "experiments/python-gamebub-v100/converted-rtl/verification.json"
converted_report_path = "experiments/python-gamebub-v100/converted-rtl/attempts/20261107T194621466713Z-cb41164d/results.json"
port_path = "experiments/python-gamebub-v100/converted-rtl/port-audit.json"
converted = read_json(converted_summary_path)
converted_report = read_json(converted_report_path)
port_audit = read_json(port_path)
converted_artifact_audit = verify_artifact_manifest("experiments/python-gamebub-v100/converted-rtl/attempts/20261107T194621466713Z-cb41164d", converted_report.get("artifacts_sha256", {}))
arrays = converted_report.get("port_adapter", {}).get("arrays", [])
paired_equalities = []
for seed in [911501, 911502]:
    parts = {}
    for variant in ["original", "converted"]:
        vals = {}
        for suffix in ["simulation.jsonl", "events.jsonl.gz", "canonical.tsv.gz"]:
            path = f"experiments/python-gamebub-v100/converted-rtl/attempts/20261107T194621466713Z-cb41164d/{variant}-seed-{seed}-{suffix}"
            vals[suffix] = digest(payload(path))
        parts[variant] = vals
    paired_equalities.append({"seed": seed, "original_hashes": parts["original"], "converted_hashes": parts["converted"], "all_equal": parts["original"] == parts["converted"]})
converted_ok = (
    converted.get("status") == "PAIRED_RTL_PASS"
    and converted.get("report_sha256") == digest(read_bytes(converted_report_path))
    and converted.get("port_audit_sha256") == digest(read_bytes(port_path))
    and converted_report.get("baseline_revision") == BASELINE
    and converted.get("seeds") == [911501, 911502]
    and converted.get("artifact_hashes_verified") == 53
    and converted_artifact_audit["declared"] == 53 and converted_artifact_audit["checked"] == 53 and not converted_artifact_audit["missing"] and not converted_artifact_audit["mismatched"]
    and converted_report.get("pipeline_directed_checks") == 84
    and converted_report.get("rgb_directed_checks") == 16
    and port_audit.get("ports_compared") == 308
    and port_audit.get("ordered_names_directions_and_total_widths_identical") is True
    and len(arrays) == 9
    and converted_report.get("port_adapter", {}).get("wrapper_contains_only_direct_connections_and_slice_assignments") is True
    and all(row["all_equal"] for row in paired_equalities)
)
check("paired_converted_rtl_artifacts", converted_ok, {"verification_status": converted.get("status"), "report": converted_report_path, "artifact_hashes_recomputed": converted_artifact_audit, "artifact_checks_stored": converted.get("artifact_hashes_verified"), "ports_compared": port_audit.get("ports_compared"), "array_wrappers": len(arrays), "wrapper_only_connections_and_slices": converted_report.get("port_adapter", {}).get("wrapper_contains_only_direct_connections_and_slice_assignments"), "seed_byte_hash_comparisons": paired_equalities, "assertion_policy": converted.get("assertion_policy"), "warnings": converted.get("warnings")})

# Paired simulation caveat is preserved explicitly in the audit.
assertion_limit = converted.get("assertion_policy", "")
warning_limit = converted.get("warnings", {}).get("converted", {})
check("paired_warning_assertion_limits_recorded", "assert" in assertion_limit and "SYNTHESIS" in assertion_limit and bool(warning_limit), {"assertion_policy": assertion_limit, "converted_warning_classes": warning_limit})

# Inspect both retained standard frontend runs. These are generic XC7/Yosys
# frontend evidence, never exact-part Vivado mapping or timing evidence.
mapping_runs = []
for suffix in ["a", "b"]:
    base = f"experiments/python-gamebub-v100/physical/v100-sv2v-baseline-{suffix}"
    conversion = read_json(f"{base}/conversion.json")
    stat = read_json(f"{base}/reports/premap-stat.json")
    memledger = read_json(f"{base}/reports/premap-memory-ledger.json")
    stage_reports = []
    for stage in ["stage1", "stage2"]:
        delta = read_json(f"{base}/reports/{stage}-delta-audit.json")
        cells = delta.get("changed_cells", [])
        stage_ok = delta.get("all_other_text_byte_identical") is True and all(c.get("type") == "$shl" and c.get("before") == 1 and c.get("after") == 0 for c in cells)
        stage_reports.append({"stage": stage, "status": "PASS" if stage_ok else "FAIL", "changed_count": delta.get("changed_count"), "changed_cells": cells, "all_other_text_byte_identical": delta.get("all_other_text_byte_identical"), "before_sha256": delta.get("before_sha256"), "after_sha256": delta.get("after_sha256")})
    mapping_runs.append({"path": base, "conversion_status": conversion.get("status"), "top": conversion.get("top"), "converted_sha256": conversion.get("converted_sha256"), "recipe_sha256": conversion.get("recipe_sha256"), "normalization": conversion.get("normalization"), "stage_deltas": stage_reports, "premap_design": stat.get("design", {}), "premap_memory_ledger_count": len(memledger.get("memories", [])), "artifact_manifest_present": (ROOT / base / "artifacts.json").exists()})
    mapping_path = ROOT / base / "mapping.json"
    mapping_receipt = json.loads(mapping_path.read_bytes()) if mapping_path.is_file() else None
    if mapping_receipt is not None:
        inputs[f"{base}/mapping.json"] = digest(mapping_path.read_bytes())
    manifest_path = ROOT / base / "artifacts.json"
    manifest = json.loads(manifest_path.read_bytes()) if manifest_path.is_file() else {}
    if manifest_path.is_file():
        inputs[f"{base}/artifacts.json"] = digest(manifest_path.read_bytes())
    retained_checked = 0
    retained_mismatches = []
    retained_external_only = []
    for artifact_name, entry in manifest.items():
        artifact_path = ROOT / base / artifact_name
        if artifact_path.is_file():
            retained_checked += 1
            if digest(artifact_path.read_bytes()) != entry.get("sha256"):
                retained_mismatches.append(artifact_name)
        else:
            retained_external_only.append(artifact_name)
    mapping_runs[-1].update({
        "mapping_receipt_status": mapping_receipt.get("status") if mapping_receipt else "PENDING",
        "mapping_command_exit_codes": [c.get("exit_code") for c in mapping_receipt.get("commands", [])] if mapping_receipt else [],
        "mapped_primitive_counts": mapping_receipt.get("mapped_primitive_counts") if mapping_receipt else None,
        "mapped_netlist_sha256": mapping_receipt.get("mapped_netlist_sha256") if mapping_receipt else None,
        "mapping_receipt_sha256": digest(mapping_path.read_bytes()) if mapping_receipt else None,
        "retained_artifact_hashes_checked": retained_checked,
        "retained_artifact_hash_mismatches": retained_mismatches,
        "external_only_artifact_count": len(retained_external_only),
    })
stage_ok_all = all(r["conversion_status"] == "FRONTEND_ELABORATED_PAIRED_RTL_REQUIRED" and all(s["status"] == "PASS" for s in r["stage_deltas"]) for r in mapping_runs)
repeatable_hashes = len({r["converted_sha256"] for r in mapping_runs}) == 1 and len({r["premap_design"].get("num_cells") for r in mapping_runs}) == 1
check("standard_frontend_shift_delta_proofs", stage_ok_all, {"runs": mapping_runs, "repeatable_converted_hash_and_generic_cell_count": repeatable_hashes})
mapping_receipts_seen = [r["mapping_receipt_status"] for r in mapping_runs]
check("generic_mapping_receipts_truthfully_recorded", all(x is not None for x in mapping_receipts_seen), {"statuses": mapping_receipts_seen})
check("generic_mapping_retained_hashes", all(not r["retained_artifact_hash_mismatches"] for r in mapping_runs), {"runs": [{"path": r["path"], "checked": r["retained_artifact_hashes_checked"], "external_only": r["external_only_artifact_count"], "mismatches": r["retained_artifact_hash_mismatches"]} for r in mapping_runs]})
mapped_runs_successful = all("FAIL" not in str(x) and "LIMIT" not in str(x) and x != "PENDING" for x in mapping_receipts_seen)

# Separate cold Yosys mapping exists for the unchanged reconstruction leaf.
# Preserve its stored primitive report and receipts as leaf-only evidence.
yosys_repeat_path = "experiments/python-gamebub-v100/physical/yosys-repeatability.json"
yosys_repeat = read_json(yosys_repeat_path)
leaf_rows = []
for suffix in ["a", "b"]:
    base = f"experiments/python-gamebub-v100/physical/v100-final-yosys-{suffix}"
    receipt = read_json(f"{base}/receipt.json")
    stat = read_json(f"{base}/reports/yosys-cu66_reconstruct_tile-stat.json")
    artifacts = receipt.get("artifacts", {})
    leaf_rows.append({"path": base, "status": receipt.get("status"), "part": receipt.get("part"), "source_manifest_sha256": receipt.get("source_manifest_sha256"), "mapped_netlist_verilog_sha256": artifacts.get("mapped-cu66_reconstruct_tile.v", {}).get("sha256"), "mapped_netlist_json_sha256": artifacts.get("mapped-cu66_reconstruct_tile.json", {}).get("sha256"), "primitive_counts": stat.get("design", {}).get("num_cells_by_type", {}), "mapped_cell_count": stat.get("design", {}).get("num_cells")})
leaf_repeat_ok = len(leaf_rows) == 2 and leaf_rows[0]["mapped_netlist_verilog_sha256"] == leaf_rows[1]["mapped_netlist_verilog_sha256"] and leaf_rows[0]["mapped_netlist_json_sha256"] == leaf_rows[1]["mapped_netlist_json_sha256"] and leaf_rows[0]["primitive_counts"] == leaf_rows[1]["primitive_counts"] and yosys_repeat.get("generic_xc7_leaf_mapping_repeated") is True
check("isolated_yosys_leaf_map_repeatability", leaf_repeat_ok, {"scope": "cu66_reconstruct_tile only; no full pipeline mapping or route", "repeatability_receipt_status": yosys_repeat.get("status"), "repeatability_claim": yosys_repeat.get("generic_xc7_leaf_mapping_repeated"), "runs": leaf_rows})

# Independently reconcile the selected IDCT DSP-inference checkpoint. This is
# an intermediate post-map_dsp report: later fine mapping failed, so the
# primitive count below must not be described as a completed leaf map.
idct_base = "experiments/python-gamebub-v100/physical/v100-solo-idct-b"
idct_receipt = read_json(f"{idct_base}/leaf-receipt.json")
idct_stat = read_json(f"{idct_base}/reports/dsp-stage-stat.json")
idct_summary = read_json(f"{idct_base}/reports/dsp-stage-summary.json")
idct_manifest = read_json(f"{idct_base}/artifacts.json")
idct_manifest_hash_audit = verify_artifact_manifest(idct_base, idct_manifest)
idct_counts = idct_stat.get("design", {}).get("num_cells_by_type", {})
summary_counts = idct_summary.get("cell_type_counts", {})
receipt_counts = idct_receipt.get("dsp_stage", {}).get("cell_type_counts", {})
dsp_rows = idct_summary.get("dsp48e1", [])
parameter_groups = Counter(tuple(sorted(x.get("parameters", {}).items())) for x in dsp_rows)
parameter_distribution = [{"count": count, "parameters": dict(items)} for items, count in sorted(parameter_groups.items())]
raw_report_binding = idct_manifest.get("dsp-stage.json", {}).get("sha256") == idct_summary.get("raw_sha256")
idct_checkpoint_ok = (
    idct_stat.get("invocation", "").endswith("-top cu66_idct8x8 ")
    and idct_stat.get("modules", {}).get("\\cu66_idct8x8", {}).get("num_cells_by_type") == summary_counts
    and summary_counts == receipt_counts
    and idct_receipt.get("dsp_stage", {}).get("canonical_sha256") == idct_summary.get("canonical_sha256")
    and raw_report_binding
    and idct_summary.get("status") == "PARTIAL_DSP_STAGE_ONLY"
    and len(dsp_rows) == summary_counts.get("DSP48E1") == 21
    and all(bool(x.get("parameters")) for x in dsp_rows)
    and idct_receipt.get("full_component_mapped") is False
    and idct_receipt.get("timing_qualified") is False
    and idct_receipt.get("target_part_fit_qualified") is False
    and idct_manifest_hash_audit["checked"] > 0
    and not idct_manifest_hash_audit["mismatched"]
)
check("idct_dsp_checkpoint_report_and_parameters", idct_checkpoint_ok, {"top": "cu66_idct8x8", "stage_status": idct_summary.get("status"), "design_cell_count": idct_stat.get("design", {}).get("num_cells"), "primitive_type_counts": summary_counts, "DSP48E1_parameter_variant_count": len(parameter_distribution), "DSP48E1_parameter_distribution": parameter_distribution, "DSP48E1_cells_with_parameters": len(dsp_rows), "raw_report_sha256_binding": idct_summary.get("raw_sha256"), "summary_sha256": digest((ROOT / f"{idct_base}/reports/dsp-stage-summary.json").read_bytes()), "stat_report_sha256": digest((ROOT / f"{idct_base}/reports/dsp-stage-stat.json").read_bytes()), "receipt_status": idct_receipt.get("status"), "receipt_exit_code": idct_receipt.get("exit_code"), "full_component_mapped": idct_receipt.get("full_component_mapped"), "timing_qualified": idct_receipt.get("timing_qualified"), "target_part_fit_qualified": idct_receipt.get("target_part_fit_qualified"), "artifact_manifest_audit": idct_manifest_hash_audit, "interpretation": "intermediate DSP inference/packing evidence only; not final fine-mapped resources, placed DSP count, fit, route or timing"})

# Verify both selected dequant post-map_dsp attempts independently. Compare
# canonical normalized checkpoint hashes and bound raw-report hashes directly;
# do not infer repeatability from matching summary text alone.
dequant_rows = []
for suffix in ["a", "b"]:
    base = f"experiments/python-gamebub-v100/physical/v100-postdsp-dequant-{suffix}"
    receipt = read_json(f"{base}/leaf-receipt.json")
    stat = read_json(f"{base}/reports/dsp-stage-stat.json")
    summary = read_json(f"{base}/reports/dsp-stage-summary.json")
    manifest = read_json(f"{base}/artifacts.json")
    artifact_audit = verify_artifact_manifest(base, manifest)
    cell_counts = stat.get("design", {}).get("num_cells_by_type", {})
    dsp_cells = summary.get("dsp48e1", [])
    param_groups = Counter(tuple(sorted(x.get("parameters", {}).items())) for x in dsp_cells)
    param_distribution = [{"count": count, "parameters": dict(items)} for items, count in sorted(param_groups.items())]
    dequant_rows.append({"path": base, "top": receipt.get("top"), "status": receipt.get("status"), "exit_code": receipt.get("exit_code"), "full_component_mapped": receipt.get("full_component_mapped"), "target_part_fit_qualified": receipt.get("target_part_fit_qualified"), "timing_qualified": receipt.get("timing_qualified"), "converted_sha256": receipt.get("converted_sha256"), "source_manifest_sha256": receipt.get("original_source_manifest_sha256"), "canonical_sha256": summary.get("canonical_sha256"), "raw_sha256": summary.get("raw_sha256"), "raw_sha256_manifest_binding": manifest.get("dsp-stage.json", {}).get("sha256") == summary.get("raw_sha256"), "summary_sha256": digest((ROOT / f"{base}/reports/dsp-stage-summary.json").read_bytes()), "stat_sha256": digest((ROOT / f"{base}/reports/dsp-stage-stat.json").read_bytes()), "primitive_type_counts": cell_counts, "public_ports_preserved": summary.get("public_ports_preserved"), "exact_ports_preserved": summary.get("exact_port_names_directions_widths_preserved"), "DSP48E1_parameter_distribution": param_distribution, "manifest_hash_audit": artifact_audit})
dequant_repeat_ok = (
    len(dequant_rows) == 2
    and all(row["status"] == "PARTIAL_DSP_STAGE_ONLY" and row["exit_code"] == 0 and row["full_component_mapped"] is False and row["target_part_fit_qualified"] is False and row["timing_qualified"] is False for row in dequant_rows)
    and all(row["raw_sha256_manifest_binding"] and row["manifest_hash_audit"]["checked"] > 0 and not row["manifest_hash_audit"]["mismatched"] for row in dequant_rows)
    and all(row["primitive_type_counts"].get("DSP48E1") == 15 and row["public_ports_preserved"] == 14 and row["exact_ports_preserved"] is True for row in dequant_rows)
    and dequant_rows[0]["canonical_sha256"] == dequant_rows[1]["canonical_sha256"]
    and dequant_rows[0]["raw_sha256"] == dequant_rows[1]["raw_sha256"]
    and dequant_rows[0]["summary_sha256"] == dequant_rows[1]["summary_sha256"]
    and dequant_rows[0]["stat_sha256"] == dequant_rows[1]["stat_sha256"]
    and dequant_rows[0]["converted_sha256"] == dequant_rows[1]["converted_sha256"]
    and dequant_rows[0]["source_manifest_sha256"] == dequant_rows[1]["source_manifest_sha256"]
)
check("dequant_post_dsp_cold_pair_checkpoint_equality", dequant_repeat_ok, {"runs": dequant_rows, "interpretation": "two equivalent Yosys DSP inference/packing checkpoints; not completed leaf maps, final area, placed DSP count, fit, route or timing"})

physical_results_path = "experiments/python-gamebub-v100/physical/results.json"
physical_results = read_json(physical_results_path)
physical_results_hash = digest((ROOT / physical_results_path).read_bytes())
physical_results_ok = (
    physical_results.get("baseline_commit") == BASELINE
    and physical_results.get("top") == "cs88_pipeline_v91k"
    and physical_results.get("status") == "PARTIAL_PHYSICAL_PREREQUISITES_OPEN"
    and physical_results.get("qualification", {}).get("placed_and_routed") is False
    and physical_results.get("qualification", {}).get("exact_target_synthesis") is False
    and physical_results.get("qualification", {}).get("hardware_30fps") is False
    and physical_results.get("arithmetic_diagnostics", {}).get("IDCT", {}).get("partial_post_DSP_checkpoint", {}).get("canonical_sha256") == idct_summary.get("canonical_sha256")
    and physical_results.get("arithmetic_diagnostics", {}).get("dequant_post_DSP_cold_pair", [{}])[0].get("partial_post_DSP_checkpoint", {}).get("raw_sha256") == dequant_rows[0]["raw_sha256"]
    and dequant_repeat_ok
    and idct_checkpoint_ok
)
check("physical_results_summary_reconciles_selected_receipts", physical_results_ok, {"path": physical_results_path, "sha256": physical_results_hash, "status": physical_results.get("status"), "baseline_commit": physical_results.get("baseline_commit"), "qualification": physical_results.get("qualification"), "dequant_pair_raw_sha256": dequant_rows[0]["raw_sha256"], "dequant_pair_canonical_sha256": dequant_rows[0]["canonical_sha256"], "idct_raw_sha256": idct_summary.get("raw_sha256"), "idct_canonical_sha256": idct_summary.get("canonical_sha256")})

# Current exact-target receipt: zero matching part and no synthesis/implementation.
preflight_path = "experiments/python-gamebub-v100/preflight/results.json"
preflight = read_json(preflight_path)
vivado_2026_logs = []
for p in ["experiments/python-gamebub-v100/preflight/vivado-2026-query.log", "experiments/python-gamebub-v100/preflight/vivado-2026-no-preload-query.log"]:
    raw = read_bytes(p)
    vivado_2026_logs.append({"path": p, "sha256": digest(raw), "first_line": raw.decode(errors="replace").splitlines()[0] if raw else "", "root_reported_exit_code": 134, "part_query_result": None, "status": "allocator_or_libudev_crash_before_query"})
exact_receipts = []
for label in ["v100-final-exact-a", "v100-final-exact-b"]:
    base = f"experiments/python-gamebub-v100/physical/{label}"
    receipt = read_json(f"{base}/receipt.json")
    parttext = read_bytes(f"{base}/part-preflight.txt").decode(errors="replace")
    exact_receipts.append({"path": base, "part": receipt.get("part"), "target_count_zero": "target_count=0" in parttext, "series7_count_zero": "series7_count=0" in parttext, "implementation_started": receipt.get("implementation_started"), "board_timing_qualified": receipt.get("board_timing_qualified"), "full_top_qualified": receipt.get("full_top_qualified"), "metrics": receipt.get("metrics")})
exact_unavailable = preflight.get("status") == "EXACT_TARGET_UNAVAILABLE" and preflight.get("exact_target_count") == 0 and preflight.get("all_series7_part_count") == 0 and not preflight.get("synthesis_started") and not preflight.get("placement_started") and not preflight.get("routing_started") and all(x["target_count_zero"] and x["series7_count_zero"] and x["implementation_started"] is False for x in exact_receipts)
check("exact_vivado_target_gate_open", exact_unavailable, {"preflight": {k: preflight.get(k) for k in ["status", "tool_version", "target", "exact_target_count", "all_series7_part_count", "installed_other_parts"]}, "cold_receipts": exact_receipts})

# Full top is not synthesized or routed. Keep one overall evidence status while
# preserving the exact-target route gate as OPEN.
overall = "PASS_EVIDENCE" if not errors else "AUDIT_ERRORS"
result = {
    "schema": "cu66-v100-independent-evidence-audit-v1",
    "status": overall,
    "scope_status": "PASS_EVIDENCE" if not errors else "AUDIT_ERRORS",
    "baseline": {"revision": BASELINE, "revision_is_ancestor": baseline_is_ancestor},
    "auditor": {"path": "scripts/cu66-v100/audit.py", "sha256": digest((ROOT / "scripts/cu66-v100/audit.py").read_bytes()), "method": "Python standard library only; direct reads/hashes and read-only git show; no producer imports or hardware/simulator tools"},
    "input_hashes": dict(sorted(inputs.items())),
    "frozen_profile": {"path": PROFILE_PATH, "sha256": profile_hash, "name": profile.get("name"), "status": profile.get("status"), "unchanged_from_baseline": baseline_profile == profile_bytes},
    "source_inventory": {"path": INV_PATH, "sha256": digest((ROOT / INV_PATH).read_bytes()), "source_file_count": len(source_rows), "xdc_count": len(inventory["existing_image"].get("xdc", [])), "all_hashes_current": not source_mismatches and not xdc_mismatches, "tracked_source_files_equal_baseline": not tracked_baseline_mismatches},
    "fresh_rtl": {"status": "PASS_EVIDENCE" if fresh_ok else "FAIL", "top": rtl.get("top"), "backend": rtl.get("backend"), "source_revision": rtl.get("source_revision"), "runs": run_checks, "artifact_audit": {"status": rtl_audit.get("status"), "attempt_report_sha256": rtl_audit.get("attempt_report_sha256"), "artifact_hashes_verified": rtl_audit.get("artifact_hashes_verified"), "snapshot_baseline_files_verified": rtl_audit.get("unchanged_fpga_source_snapshots_verified_against_git_baseline"), "traces": rtl_audit.get("traces"), "cross_seed_event_keys": rtl_audit.get("cross_seed_semantic_event_keys_compared")}, "scope_limit": "V91j signed dequant/IDCT component; not complete CS88 RTL decode/publication"},
    "paired_converted_rtl": {"status": "PASS_EVIDENCE" if converted_ok else "FAIL", "verification": converted_summary_path, "report": converted_report_path, "report_sha256": digest((ROOT / converted_report_path).read_bytes()), "seeds": converted.get("seeds"), "pipeline_case_runs": converted.get("pipeline_case_runs"), "pipeline_directed_checks": converted.get("pipeline_directed_checks"), "rgb_case_runs": converted.get("rgb_case_runs"), "rgb_directed_checks": converted.get("rgb_directed_checks"), "artifact_hashes_verified": converted.get("artifact_hashes_verified"), "public_ports_compared": port_audit.get("ports_compared"), "array_wrappers": len(arrays), "wrapper_has_only_direct_connections_and_slices": converted_report.get("port_adapter", {}).get("wrapper_contains_only_direct_connections_and_slice_assignments"), "byte_hash_equalities": paired_equalities, "assertion_policy": assertion_limit, "converted_warning_classes": warning_limit, "scope_limit": converted.get("qualification")},
    "generic_xc7_frontend": {"status": "PASS_EVIDENCE_MAPPING_INCOMPLETE" if stage_ok_all and repeatable_hashes and not mapped_runs_successful else "PASS_EVIDENCE" if stage_ok_all and repeatable_hashes else "INCOMPLETE", "cold_runs": mapping_runs, "mapping_receipt_statuses": mapping_receipts_seen, "repeatable_converted_source_and_premap_generic_cells": repeatable_hashes, "premap_generic_design_cells": [r["premap_design"].get("num_cells") for r in mapping_runs], "netlist_port_equivalence": "308-port evidence belongs to paired RTL wrapper audit; mapped-netlist port ledger unavailable without successful full-component map", "mapped_primitive_counts": "full pipeline mapping incomplete; isolated reconstruct leaf counts are recorded separately", "normalized_mapped_netlist_hashes": "full pipeline mapped netlist unavailable", "repeatability": "converted source and generic premap counts repeat; generic full-pipeline mapped netlist repeatability not established", "timing_or_fmax": "not established", "separate_leaf_mapping": {"path": yosys_repeat_path, "status": "PASS_EVIDENCE" if leaf_repeat_ok else "INCOMPLETE", "runs": leaf_rows, "repeatability_summary": yosys_repeat}},
    "idct_dsp_inference_checkpoint": {"audit_status": "PASS_EVIDENCE" if idct_checkpoint_ok else "INCONSISTENT", "path": idct_base, "top": "cu66_idct8x8", "stage": "intermediate post-map_dsp checkpoint; fine mapping did not complete", "design_cell_count_at_checkpoint": idct_stat.get("design", {}).get("num_cells"), "primitive_type_counts": summary_counts, "DSP48E1_parameter_variant_count": len(parameter_distribution), "DSP48E1_parameter_distribution": parameter_distribution, "raw_report_sha256": idct_summary.get("raw_sha256"), "raw_report_hash_bound_by_manifest": raw_report_binding, "stage_summary_sha256": digest((ROOT / f"{idct_base}/reports/dsp-stage-summary.json").read_bytes()), "stage_stat_sha256": digest((ROOT / f"{idct_base}/reports/dsp-stage-stat.json").read_bytes()), "leaf_receipt_status": idct_receipt.get("status"), "leaf_receipt_exit_code": idct_receipt.get("exit_code"), "full_component_mapped": idct_receipt.get("full_component_mapped"), "target_part_fit_qualified": idct_receipt.get("target_part_fit_qualified"), "timing_qualified": idct_receipt.get("timing_qualified"), "scope_limit": "Yosys XC7 DSP inference/packing checkpoint for IDCT only; DSP48E1 count is not a placed device count and 882 cells is not final mapped area"},
    "dequant_dsp_checkpoint_pair": {"audit_status": "PASS_EVIDENCE" if dequant_repeat_ok else "INCONSISTENT", "runs": dequant_rows, "raw_report_hashes_equal": dequant_rows[0]["raw_sha256"] == dequant_rows[1]["raw_sha256"], "canonical_hashes_equal": dequant_rows[0]["canonical_sha256"] == dequant_rows[1]["canonical_sha256"], "dsp48e1_per_run": [r["primitive_type_counts"].get("DSP48E1") for r in dequant_rows], "public_ports_preserved_per_run": [r["public_ports_preserved"] for r in dequant_rows], "scope_limit": "repeated post-map_dsp Yosys component checkpoints only; subsequent fine mapping failed and no placed-device DSP claim"},
    "physical_results_summary": {"path": physical_results_path, "sha256": physical_results_hash, "status": physical_results.get("status"), "baseline_commit": physical_results.get("baseline_commit"), "complete_component_generic_mapping": physical_results.get("complete_component_generic_mapping"), "qualification": physical_results.get("qualification"), "scope_limit": "physical prerequisites summary; exact target, full component fit, route and board gates remain open"},
    "exact_target_route_gate": {"status": "OPEN_UNAVAILABLE", "vivado_status": preflight.get("status"), "tool_version": preflight.get("tool_version"), "target": preflight.get("target"), "exact_target_count": preflight.get("exact_target_count"), "series7_part_count": preflight.get("all_series7_part_count"), "cold_preflight_receipts": exact_receipts, "additional_vivado_probe": {"tool_version": "2026.1", "attempts": vivado_2026_logs, "no_part_count_obtained": True, "acorn_project_modified": False}, "routed": False, "fmax": None},
    "checks": checks,
    "errors": errors,
    "open_gates": ["exact Vivado part availability and actual target route", "final IDCT leaf fine mapping and full V91k component mapping, mapped netlist hashes and mapped port ledger", "full CS88 top-level integration and timing/throughput gates"]
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(OUT.relative_to(ROOT))
print(f"status={overall} checks={len(checks)} errors={len(errors)}")
