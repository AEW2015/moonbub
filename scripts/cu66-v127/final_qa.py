#!/usr/bin/env python3
"""Read-only V127 final QA. Preparation mode cannot report final qualification."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "experiments/python-gamebub-v127"
V126 = ROOT / "experiments/python-gamebub-v126"
V120 = ROOT / "experiments/python-gamebub-v120"
REV2_PATH = AREA / "audit/full-independent-tooling-freeze-revision2.json"
REV2_SHA = "9f71d27f33789381c2962e0b20f3bc21075b16b873a04e553500bce852529606"
V126_ROOT_SHA = "e42e0145e177d65f1499db79195caef8b8abb90fab1e5f235f79913c2056360f"
V126_INDEX_SHA = "7d534c343732bc50786bff874c9b6d536bceaa6298fc5e7f002d98b5216e732f"
OLD_FREEZE_SHA = "1151d4bf76c83548be64aeec3273a9e95724479ed13b77ec4a8abd2d9abb1b44"
FIXTURE_REPAIR_SHA = "4ec030460110233b04518756a51a2ca9202b74e90fb7a27edebaa8374890e3c8"
PLAN_REPAIR_SHA = "b46bad386089720710cd3ccec6bbea28c61b02cf90db67076d3460c228bcf4b5"
ROOT_TOOLING_SHA = "experiments/python-gamebub-v127/orchestration/root-tooling-freeze.json"
EXPECTED_ACTIVE_STAGES = {"focused", "spatial", "peer", "parent"}
EXPECTED_STAGE_STATUSES = {
    "focused": "PASS",
    "peer": "PASS",
    "spatial": "PASS_V127_FINAL_SPATIAL_CANONICAL",
    "parent": "PASS_V127_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION",
}


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load(path: Path):
    return json.loads(path.read_text())


def path_for(raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def pin_result(raw: str, expected: str):
    p = path_for(raw)
    actual = sha(p) if p.is_file() else None
    return {"path": raw, "expected_sha256": expected, "actual_sha256": actual,
            "matches": actual == expected}


def recursive_pins(obj, prefix="root_results"):
    """Validate path/SHA records, excluding historical source-origin maps."""
    found = []

    def visit(v, at, key=""):
        if isinstance(v, dict):
            raw, h = v.get("path"), v.get("sha256")
            if (key not in ("source_origins", "source_sha256") and
                    isinstance(raw, str) and isinstance(h, str) and
                    re.fullmatch(r"[0-9a-f]{64}", h)):
                found.append((at, raw, h))
            for k, child in v.items():
                visit(child, f"{at}.{k}", str(k))
        elif isinstance(v, list):
            for i, child in enumerate(v):
                visit(child, f"{at}[{i}]", key)

    visit(obj, prefix)
    return [{"at": at, **pin_result(raw, h)} for at, raw, h in found]


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])


def markdown_targets(text: str):
    out, in_fence = [], False
    for line in text.splitlines():
        if re.match(r"^\s*(```+|~~~+)", line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    pat = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)|^\s*\[[^\]]+\]:\s*(\S+)", re.M)
    for m in pat.finditer("\n".join(out)):
        value = (m.group(1) or m.group(2) or "").strip()
        yield value[1:-1] if value.startswith("<") and value.endswith(">") else value.split()[0]


def markdown_check(paths):
    rows = []
    for doc in sorted(set(paths)):
        if not doc.is_file():
            rows.append({"document": rel(doc), "error": "missing document"})
            continue
        for target in markdown_targets(doc.read_text(errors="replace")):
            decoded = unquote(target)
            u = urlsplit(decoded)
            if u.scheme or decoded.startswith("//") or decoded.startswith("#") or not u.path:
                continue
            dest = ROOT / u.path.lstrip("/") if u.path.startswith("/") else doc.parent / u.path
            rows.append({"document": rel(doc), "target": target, "resolved": rel(dest), "exists": dest.exists()})
    return rows


def active_stage_closures(index_path: Path):
    """Verify selected index -> selector -> receipt -> source/artifact bytes."""
    rows = []
    if not index_path.is_file():
        return rows
    index = load(index_path)
    stages = index.get("stages", {})
    if not isinstance(stages, dict) or set(stages) != EXPECTED_ACTIVE_STAGES:
        return [{"stage_set_matches": False, "expected_stages": sorted(EXPECTED_ACTIVE_STAGES),
                 "actual_stages": sorted(stages) if isinstance(stages, dict) else None}]
    for name, stage in stages.items():
        selector_path = stage.get("path")
        selector_sha = stage.get("sha256")
        selector_pin = pin_result(selector_path, selector_sha) if selector_path and selector_sha else {"matches": False}
        receipt_meta = stage.get("receipt", {})
        receipt_path = receipt_meta.get("path")
        receipt_pin = pin_result(receipt_path, receipt_meta.get("sha256", "")) if receipt_path else {"matches": False}
        sources, artifacts = [], []
        receipt_status = None
        actual_rtl_run = False
        if receipt_pin.get("matches"):
            receipt = load(path_for(receipt_path))
            receipt_status = receipt.get("status")
            actual_rtl_run = receipt.get("actual_RTL_run") is True
            source_map = receipt.get("source_sha256", {})
            artifact_map = receipt.get("artifact_sha256", receipt.get("artifacts_sha256", {}))
            for raw, expected in source_map.items():
                sources.append(pin_result(raw, expected))
            for raw, expected in artifact_map.items():
                artifacts.append(pin_result(str(Path(receipt_path).parent / raw), expected))
        rows.append({"stage": name, "selector": selector_pin, "receipt": receipt_pin,
                     "receipt_status": receipt_status, "actual_RTL_run": actual_rtl_run,
                     "source_count": len(sources), "artifact_count": len(artifacts),
                     "source_matches": bool(sources) and all(x["matches"] for x in sources),
                     "artifact_matches": bool(artifacts) and all(x["matches"] for x in artifacts),
                     "receipt_qualifies": receipt_status == EXPECTED_STAGE_STATUSES[name] and actual_rtl_run,
                     "source_mismatches": [x for x in sources if not x["matches"]],
                     "artifact_mismatches": [x for x in artifacts if not x["matches"]]})
    return rows


def native_closure(root_obj):
    refs = []
    def visit(v):
        if isinstance(v, dict):
            for k, child in v.items():
                if k == "candidate_native_receipt" and isinstance(child, dict):
                    refs.append(child)
                visit(child)
        elif isinstance(v, list):
            for child in v: visit(child)
    visit(root_obj)
    if len(refs) != 1:
        return {"matches": False, "reason": "expected exactly one selected candidate_native_receipt", "ref_count": len(refs)}
    ref = refs[0]
    rp = pin_result(ref.get("path", ""), ref.get("sha256", ""))
    if not rp["matches"]:
        return {"matches": False, "receipt": rp, "retained_artifacts": []}
    receipt_path = path_for(ref["path"])
    receipt = load(receipt_path)
    retained = receipt.get("retained_artifact_sha256", {})
    checks = [pin_result(str(Path(ref["path"]).parent / raw), h) for raw, h in retained.items()]
    status = receipt.get("status")
    terminal = receipt.get("component_route_finished") is True and status != "RUNNING"
    return {"matches": terminal and bool(retained) and all(x["matches"] for x in checks),
            "status": status, "component_route_finished": receipt.get("component_route_finished"),
            "terminal": terminal,
            "receipt": rp, "retained_count": len(checks),
            "retained_mismatches": [x for x in checks if not x["matches"]]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", action="store_true", help="require completed V127 root results and selected evidence closure")
    ap.add_argument("--root-results", type=Path, default=AREA / "results.json")
    ap.add_argument("--output", type=Path, help="write JSON here; preparation should use /tmp")
    args = ap.parse_args()
    checks = []

    def add(name, passed, details):
        checks.append({"check": name, "pass": bool(passed), "details": details})

    # Include only current V127 product/evidence trees; historical source snapshots
    # are scanned for names/size, never interpreted as current source files.
    scan_roots = [ROOT / "scripts/cu66-v127", ROOT / "docs/cu66-v127",
                  AREA, ROOT / "fpga/experiments/cu66-v127-owner"]
    files = sorted({p for base in scan_roots if base.exists() for p in base.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts})
    py = [p for p in files if p.suffix == ".py"]
    ast_errors = []
    for p in py:
        try: ast.parse(p.read_text(), filename=rel(p))
        except SyntaxError as e: ast_errors.append({"path": rel(p), "error": str(e)})
    add("v127_python_ast", bool(py) and not ast_errors, {"count": len(py), "errors": ast_errors})

    docs = list((ROOT / "docs/cu66-v127").rglob("*.md"))
    for raw in ("README.md", "docs/gamebub-application-specific-codec-plan.md",
                "docs/gamebub-v126-v130-timing-streaming-plan.md",
                "docs/gamebub-v121-v125-spatial-literature-review.md", "docs/timing-review.md"):
        p = ROOT / raw
        if p.is_file(): docs.append(p)
    link_rows = markdown_check(docs)
    broken = [r for r in link_rows if r.get("exists") is False or "error" in r]
    add("v127_and_main_markdown_links", not broken,
        {"document_count": len(set(docs)), "local_link_count": len(link_rows), "broken": broken})

    handoff = load(V120 / "handoff.json")
    commit = handoff["rtl_source_commit"]
    origins = handoff["source_origins"]
    b_rows = []
    for alias, meta in origins.items():
        physical = meta["path"]
        current = sha(ROOT / physical) if (ROOT / physical).is_file() else None
        gitsha = digest_bytes(git_blob(commit, physical))
        b_rows.append({"alias": alias, "path": physical, "expected": meta["sha256"],
                       "current": current, "git": gitsha,
                       "matches": current == gitsha == meta["sha256"]})
    add("qualified_source_B18_physical_and_git", len(b_rows) == 18 and all(x["matches"] for x in b_rows),
        {"commit": commit, "count": len(b_rows), "matched": sum(x["matches"] for x in b_rows),
         "mismatches": [x for x in b_rows if not x["matches"]]})

    protected = load(V120 / "audit/baseline.json").get("protected_files", [])
    marker_rows = []
    for m in protected:
        p = ROOT / m["path"]
        actual = {"sha256": sha(p) if p.is_file() else None,
                  "bytes": p.stat().st_size if p.is_file() else None,
                  "mtime_ns": p.stat().st_mtime_ns if p.is_file() else None}
        expected = {"sha256": m["sha256"], "bytes": m["bytes"], "mtime_ns": m["mtime_ns"]}
        marker_rows.append({"path": m["path"], "matches": actual == expected,
                            "expected": expected, "actual": actual})
    add("V120_protected_marker_metadata", bool(marker_rows) and all(x["matches"] for x in marker_rows),
        {"count": len(marker_rows), "mismatches": [x for x in marker_rows if not x["matches"]]})

    old_root_path = V126 / "results.json"
    old_index_path = V126 / "integration/results.json"
    old_root = load(old_root_path)
    old_index = load(old_index_path)
    old_root_pins = recursive_pins(old_root, "V126_root")
    old_native = native_closure(old_root)
    add("frozen_V126_parent_and_native_closure",
        sha(old_root_path) == V126_ROOT_SHA and sha(old_index_path) == V126_INDEX_SHA and
        old_root.get("functional_proof") == {"path": str(old_index_path.relative_to(ROOT)), "sha256": V126_INDEX_SHA} and
        bool(old_root_pins) and all(x["matches"] for x in old_root_pins) and old_native["matches"],
        {"root_sha256": sha(old_root_path), "index_sha256": sha(old_index_path),
         "root_pin_count": len(old_root_pins), "root_pin_mismatches": [x for x in old_root_pins if not x["matches"]],
         "native_closure": old_native})

    tooling_path = ROOT / ROOT_TOOLING_SHA
    tooling = load(tooling_path)
    maps_ok = all(isinstance(tooling.get(k), dict) and bool(tooling[k]) for k in ("files", "derivations", "core_recipe"))
    tool_pins = {p: sha(ROOT / p) == h for key in ("files", "derivations", "core_recipe")
                 for p, h in tooling.get(key, {}).items()}
    add("V127_root_tooling_freeze_nonempty_and_pinned", maps_ok and len(tooling["files"]) == 7 and
        len(tooling["derivations"]) == 5 and len(tooling["core_recipe"]) == 3 and
        all(tool_pins.values()) and tooling.get("qualification_pending") is True,
        {"freeze_sha256": sha(tooling_path), "counts": {k: len(tooling[k]) for k in ("files", "derivations", "core_recipe")},
         "mismatches": [p for p, ok in tool_pins.items() if not ok]})

    rev = load(REV2_PATH)
    srcmap, focusmap = rev.get("source_sha256", {}), rev.get("focused_input_sha256", {})
    map_checks = [pin_result(p, h) for mp in (srcmap, focusmap) for p, h in mp.items()]
    prev = rev.get("previous_freeze", {})
    repair_checks = []
    for field, expected in (("fixture_repair", FIXTURE_REPAIR_SHA), ("plan_repair", PLAN_REPAIR_SHA),
                            ("retained_failed_attempt", "91bee212647c6bdb08f3ded0d5eb2a871c4f48ca83d73a6d139407bed6babf31")):
        item = rev.get(field, {})
        repair_checks.append({"field": field, **pin_result(item.get("path", ""), item.get("sha256", "")),
                              "expected_sha256": expected, "expected_matches": item.get("sha256") == expected})
    rev_ok = (sha(REV2_PATH) == REV2_SHA and rev.get("schema") == "v127-independent-tooling-freeze-v1" and
              rev.get("status") == "FROZEN_AFTER_VERIFICATION_ONLY_BASELINE_OUTPUT_BINDING_REPAIR" and
              rev.get("actual_RTL_run") is False and rev.get("declared_public_cycle_delta") == 0 and
              rev.get("all_original_oracles_retained") is True and
              rev.get("zero_contract_and_one_syntactic_edit_predicate_exercised") is True and
              rev.get("baseline_self_stream_comparison_counts") == {"spatial": 4, "peer": 2, "parent": 4} and
              bool(srcmap) and bool(focusmap) and len(focusmap) == 61 and all(x["matches"] for x in map_checks) and
              prev.get("sha256") == OLD_FREEZE_SHA and pin_result(prev.get("path", ""), OLD_FREEZE_SHA)["matches"] and
              all(r["expected_matches"] and r["matches"] for r in repair_checks))
    # Retained failed-attempt source bytes are checked against its frozen receipt,
    # independently of later repaired/current production source paths.
    attempt_path = path_for(rev["retained_failed_attempt"]["path"])
    attempt = load(attempt_path)
    attempt_sources = attempt.get("source_sha256", {})
    attempt_artifacts = attempt.get("artifact_sha256", attempt.get("artifacts_sha256", {}))
    # The failed receipt's source map records original logical paths. Its
    # actual retained copies live under attempts/<id>/sources/<logical path>.
    attempt_snapshot_checks = []
    attempt_artifact_checks = []
    for archived, expected in attempt_artifacts.items():
        p = attempt_path.parent / archived
        actual = sha(p) if p.is_file() else None
        attempt_artifact_checks.append({"archived_path": archived, "expected": expected,
                                        "actual": actual, "matches": actual == expected})
    for logical, expected in attempt_sources.items():
        archived = f"sources/{logical}"
        artifact_expected = attempt_artifacts.get(archived)
        p = attempt_path.parent / archived
        actual = sha(p) if p.is_file() else None
        attempt_snapshot_checks.append({"logical_path": logical, "snapshot_path": rel(p),
            "receipt_source_sha256": expected, "artifact_sha256": artifact_expected,
            "actual_sha256": actual,
            "matches": bool(artifact_expected) and actual == expected == artifact_expected})
    before_record_path = AREA / "owner/repair-history/20261110T180823389365Z-baseline-port-binding/preserved-before.json"
    before_record = load(before_record_path)
    before_snapshot_checks = []
    for logical, expected in before_record.get("before_sha256", {}).items():
        archived = attempt_path.parent / "sources" / logical
        actual = sha(archived) if archived.is_file() else None
        before_snapshot_checks.append({"path": logical, "expected": expected, "actual": actual,
                                       "matches": actual == expected})
    # The separately retained verification-plan repair binds its old/new prose.
    plan_dir = AREA / "owner/repair-history/20261110T180828817132Z-plan-output-binding"
    plan_repair = load(plan_dir / "repair.json")
    plan_before = plan_dir / "verification-plan.before.md"
    plan_after = plan_dir / "verification-plan.after.md"
    plan_archive_checks = {
        "before_copy": sha(plan_before) == plan_repair.get("original_sha256"),
        "after_copy": sha(plan_after) == plan_repair.get("candidate_sha256"),
        "current_matches_after": sha(ROOT / plan_repair["path"]) == plan_repair.get("candidate_sha256"),
    }
    repair_after_checks = [pin_result(p, h) for p, h in
                           load(AREA / "owner/repair-history/20261110T180823389365Z-baseline-port-binding/repair.json")["after_sha256"].items()]
    rev_ok = (rev_ok and bool(attempt_snapshot_checks) and all(x["matches"] for x in attempt_snapshot_checks)
              and bool(attempt_artifact_checks) and all(x["matches"] for x in attempt_artifact_checks)
              and bool(before_snapshot_checks) and all(x["matches"] for x in before_snapshot_checks)
              and all(plan_archive_checks.values()) and all(x["matches"] for x in repair_after_checks))
    add("selected_functional_input_freeze_and_repair_history", rev_ok,
        {"revision2_sha256": sha(REV2_PATH), "expected_sha256": REV2_SHA,
         "source_map_count": len(srcmap), "focused_map_count": len(focusmap),
         "map_mismatches": [x for x in map_checks if not x["matches"]],
         "previous_freeze": prev, "repair_checks": repair_checks,
         "failed_attempt_source_count": len(attempt_snapshot_checks),
         "failed_attempt_snapshot_mismatches": [x for x in attempt_snapshot_checks if not x["matches"]],
         "failed_attempt_artifact_count": len(attempt_artifact_checks),
         "failed_attempt_artifact_mismatches": [x for x in attempt_artifact_checks if not x["matches"]],
         "repair_before_snapshot_count": len(before_snapshot_checks),
         "repair_before_snapshot_mismatches": [x for x in before_snapshot_checks if not x["matches"]],
         "repair_after_current_mismatches": [x for x in repair_after_checks if not x["matches"]],
         "plan_repair_archive_checks": plan_archive_checks,
         "historical_sources_compared_to_current": False})

    large = [{"path": rel(p), "bytes": p.stat().st_size} for p in files if p.stat().st_size > 50 * 1024 * 1024]
    add("V127_new_tree_files_over_50MiB", not large, {"count": len(large), "files": large})
    secret_re = re.compile(r"(?i)(secret|credential|password|token|id_rsa|private.?key|\.env|api.?key)")
    secret_names = [rel(p) for p in files if secret_re.search(p.name)]
    add("secret_like_filenames_only", not secret_names,
        {"count": len(secret_names), "filenames": secret_names, "contents_read": False})

    root_path = args.root_results.resolve() if args.root_results.is_absolute() else (ROOT / args.root_results).resolve()
    final_checks, stage_closures, native_check = [], [], {"matches": False, "reason": "final mode not requested"}
    root_obj = None
    if root_path.is_file():
        root_obj = load(root_path)
        final_checks = recursive_pins(root_obj, "V127_root_results")
        final_index = root_obj.get("functional_proof", {})
        index_path = path_for(final_index.get("path", "")) if final_index else AREA / "integration/results.json"
        if index_path.is_file(): stage_closures = active_stage_closures(index_path)
        native_check = native_closure(root_obj)
    root_ok = bool(root_obj and final_checks and all(x["matches"] for x in final_checks))
    stages_ok = (len(stage_closures) == 4 and all(x.get("stage_set_matches", True) and
                  x.get("selector", {}).get("matches") and x.get("receipt", {}).get("matches") and
                  x.get("receipt_qualifies") and x.get("source_matches") and x.get("artifact_matches")
                  for x in stage_closures))
    final_evidence_ok = root_ok and stages_ok and native_check.get("matches") is True
    def final_qualification_predicate(final_mode: bool, evidence_ok: bool) -> bool:
        return bool(evidence_ok) if final_mode else True

    # Predicate-only checks exercise the mode logic without fabricating result files.
    predicate_checks = {
        "final_valid_evidence_can_pass": final_qualification_predicate(True, True),
        "final_invalid_evidence_fails": not final_qualification_predicate(True, False),
        "preparation_does_not_require_final_evidence": final_qualification_predicate(False, False),
    }
    add("final_qualification_predicate_self_checks", all(predicate_checks.values()), predicate_checks)
    add("final_root_recursive_pins_and_selected_evidence_closures",
        final_qualification_predicate(args.final, final_evidence_ok),
        {"required": args.final, "root_results": rel(root_path), "exists": root_path.is_file(),
         "root_status": root_obj.get("status") if root_obj else None,
         "root_pin_count": len(final_checks), "root_pin_mismatches": [x for x in final_checks if not x["matches"]],
         "stage_closure_count": len(stage_closures), "stage_closures": stage_closures,
         "native_closure": native_check})

    # In preparation mode this check is deliberately PASS only as a statement
    # that final qualification has not been asserted.
    add("preparation_never_claims_final_pass", (not args.final) or final_evidence_ok,
        {"final_mode": args.final, "final_qualification_asserted": False if not args.final else final_evidence_ok})
    all_ok = all(c["pass"] for c in checks)
    status = ("PASS_FINAL_READONLY_QA" if all_ok else "FINAL_QA_GAPS") if args.final else (
        "PREPARATION_ONLY" if all_ok else "PREPARATION_GAPS")
    result = {"schema": "v127-final-readonly-qa-v1", "status": status, "final_mode": args.final,
              "script_sha256": sha(Path(__file__)), "root_results": rel(root_path),
              "scope": "Read-only source lineage, freeze/pin closure, selected evidence closure, Python syntax, Markdown links, file sizes and secret-like filenames. No vendor/build jobs; no secret contents read.",
              "checks": checks, "check_count": len(checks), "passed_checks": sum(c["pass"] for c in checks),
              "limitations": ["Preparation mode never reports final PASS and does not require V127 root results.",
                  "Final mode requires root results and recursive path/SHA pins, selected functional stage closures, and selected native retained-artifact closure.",
                  "Historical failed-attempt source snapshots are checked against their own retained receipts, not current repaired source paths.",
                  "This QA does not establish hardware qualification or board performance."]}
    if args.output:
        out = args.output.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.final and not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
