#!/usr/bin/env python3
"""Read-only final V126 evidence and documentation QA; --final requires root results."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
V120_BASELINE = ROOT / "experiments/python-gamebub-v120/audit/baseline.json"
V120_HANDOFF = ROOT / "experiments/python-gamebub-v120/handoff.json"
V125_RESULTS = ROOT / "experiments/python-gamebub-v125/results.json"
V125_INDEX = ROOT / "experiments/python-gamebub-v125/integration/results.json"
V126 = ROOT / "experiments/python-gamebub-v126"
DEFAULT_ROOT_RESULTS = V126 / "results.json"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load(path: Path):
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def pin_checks(obj, *, prefix="root_results", allow_external=True):
    """Find every nested {path, sha256} record and verify its file bytes."""
    records = []

    def visit(value, at, parent_key=""):
        if isinstance(value, dict):
            p = value.get("path")
            h = value.get("sha256")
            # Source-origin and source-digest maps describe historical inputs;
            # their copied bytes are checked through the owning receipt closure.
            historical_source = parent_key in ("source_origins", "source_sha256")
            if (not historical_source and isinstance(p, str) and isinstance(h, str) and
                    re.fullmatch(r"[0-9a-f]{64}", h)):
                records.append((at, p, h))
            for key, child in value.items():
                visit(child, at + "." + str(key), str(key))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, f"{at}[{i}]", parent_key)

    visit(obj, prefix)
    results = []
    for at, raw, expected in records:
        p = Path(raw)
        if not p.is_absolute():
            p = ROOT / p
        exists = p.is_file()
        actual = sha(p) if exists else None
        results.append({"at": at, "path": raw, "expected_sha256": expected,
                        "actual_sha256": actual, "matches": exists and actual == expected})
    return results


def closure(path: Path, receipt: dict):
    source_results = []
    for raw, expected in receipt.get("source_sha256", {}).items():
        p = ROOT / raw
        actual = sha(p) if p.is_file() else None
        source_results.append({"path": raw, "expected_sha256": expected,
                               "actual_sha256": actual, "matches": actual == expected})
    artifact_results = []
    artifacts = receipt.get("artifact_sha256", receipt.get("artifacts_sha256", {}))
    for raw, expected in artifacts.items():
        p = path.parent / raw
        actual = sha(p) if p.is_file() else None
        artifact_results.append({"path": raw, "expected_sha256": expected,
                                 "actual_sha256": actual, "matches": actual == expected})
    return {"source_count": len(source_results),
            "source_matches": sum(x["matches"] for x in source_results),
            "artifact_count": len(artifact_results),
            "artifact_matches": sum(x["matches"] for x in artifact_results),
            "all_match": (all(x["matches"] for x in source_results) and
                          all(x["matches"] for x in artifact_results)),
            "mismatches": [x for x in source_results + artifact_results if not x["matches"]]}


def git_blob(commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])


def markdown_link_targets(text: str):
    # Ignore fenced code, which often contains example commands/placeholder paths.
    lines = []
    fenced = False
    fence_re = re.compile(r"^\s*(```+|~~~+)")
    for line in text.splitlines():
        m = fence_re.match(line)
        if m:
            fenced = not fenced
            continue
        if not fenced:
            lines.append(line)
    text = "\n".join(lines)
    pattern = re.compile(r"!?\[[^\]]*\]\((<[^>]+>|[^)]+)\)|^\s*\[[^\]]+\]:\s*(\S+)", re.M)
    for match in pattern.finditer(text):
        target = match.group(1) or match.group(2) or ""
        target = target.strip()
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        else:
            target = target.split()[0] if target else ""
        yield target


def check_markdown(paths):
    rows = []
    for doc in sorted(set(paths)):
        if not doc.is_file():
            rows.append({"document": rel(doc), "error": "missing markdown file"})
            continue
        for target in markdown_link_targets(doc.read_text(errors="replace")):
            decoded = unquote(target)
            parts = urlsplit(decoded)
            if parts.scheme or decoded.startswith("//") or decoded.startswith("#"):
                continue
            raw_path = parts.path
            if not raw_path:
                continue
            if raw_path.startswith("/"):
                dest = ROOT / raw_path.lstrip("/")
            else:
                dest = doc.parent / raw_path
            exists = dest.exists()
            rows.append({"document": rel(doc), "target": target,
                         "resolved": rel(dest), "exists": exists})
    return rows


def v126_new_files():
    roots = [ROOT / "scripts/cu66-v126", ROOT / "docs/cu66-v126",
             ROOT / "experiments/python-gamebub-v126",
             ROOT / "fpga/experiments/cu66-v126-producer"]
    files = []
    for base in roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            files.append(p)
    return sorted(set(files))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--final", action="store_true", help="require final root results and all their pins")
    ap.add_argument("--root-results", type=Path, default=DEFAULT_ROOT_RESULTS)
    ap.add_argument("--output", type=Path, default=V126 / "audit/final-qa.json")
    args = ap.parse_args()
    checks = []

    def add(name, passed, details):
        checks.append({"check": name, "pass": bool(passed), "details": details})

    files = v126_new_files()
    py_files = [p for p in files if p.suffix == ".py"]
    ast_errors = []
    for p in py_files:
        try:
            ast.parse(p.read_text(), filename=rel(p))
        except SyntaxError as exc:
            ast_errors.append({"path": rel(p), "error": str(exc)})
    add("new_v126_python_ast", not ast_errors,
        {"file_count": len(py_files), "errors": ast_errors})

    root_path = args.root_results.resolve() if args.root_results.is_absolute() else (ROOT / args.root_results).resolve()
    docs = list((ROOT / "docs/cu66-v126").rglob("*.md"))
    # Main project documents and any Markdown files explicitly pinned by final root results.
    for p in (ROOT / "docs/gamebub-v126-v130-timing-streaming-plan.md",
              ROOT / "docs/gamebub-v121-v125-spatial-literature-review.md",
              ROOT / "docs/gamebub-application-specific-codec-plan.md",
              ROOT / "docs/timing-review.md", ROOT / "README.md"):
        if p.is_file():
            docs.append(p)
    if root_path.is_file():
        pinned_root_docs = []
        def visit_doc_pins(value):
            if isinstance(value, dict):
                if isinstance(value.get("path"), str) and value["path"].lower().endswith(".md"):
                    target = Path(value["path"])
                    if not target.is_absolute():
                        target = ROOT / target
                    if target.is_file():
                        pinned_root_docs.append(target)
                for child in value.values():
                    visit_doc_pins(child)
            elif isinstance(value, list):
                for child in value:
                    visit_doc_pins(child)
        visit_doc_pins(load(root_path))
        docs.extend(pinned_root_docs)
    links = check_markdown(docs)
    broken = [x for x in links if x.get("exists") is False or "error" in x]
    add("local_markdown_links", not broken,
        {"documents": len(set(docs)), "local_links": len(links), "broken": broken})

    handoff = load(V120_HANDOFF)
    source_commit = handoff["rtl_source_commit"]
    source_rows = []
    for alias, meta in handoff["source_origins"].items():
        physical = meta["path"]
        p = ROOT / physical
        current = sha(p) if p.is_file() else None
        original = git_blob(source_commit, physical)
        git_sha = sha_bytes(original)
        source_rows.append({"alias": alias, "physical_path": physical,
                            "expected_sha256": meta["sha256"], "current_sha256": current,
                            "git_sha256": git_sha,
                            "matches": current == meta["sha256"] == git_sha})
    add("source_B18_physical_and_git_originals", len(source_rows) == 18 and
        all(x["matches"] for x in source_rows),
        {"base_commit": source_commit, "count": len(source_rows),
         "matches": sum(x["matches"] for x in source_rows),
         "mismatches": [x for x in source_rows if not x["matches"]]})

    protected = load(V120_BASELINE)["protected_files"]
    marker_rows = []
    for meta in protected:
        p = ROOT / meta["path"]
        actual = {"sha256": sha(p) if p.is_file() else None,
                  "bytes": p.stat().st_size if p.is_file() else None,
                  "mtime_ns": p.stat().st_mtime_ns if p.is_file() else None}
        expected = {"sha256": meta["sha256"], "bytes": meta["bytes"], "mtime_ns": meta["mtime_ns"]}
        marker_rows.append({"path": meta["path"], "expected": expected,
                            "actual": actual, "matches": actual == expected})
    add("protected_marker_sha_size_mtime", bool(marker_rows) and all(x["matches"] for x in marker_rows),
        {"count": len(marker_rows), "matches": sum(x["matches"] for x in marker_rows),
         "files": marker_rows})

    old_root = load(V125_RESULTS)
    v125_pin_checks = pin_checks(old_root, prefix="V125_results")
    v125_index = load(V125_INDEX)
    v125_origins = v125_index.get("source_origins", {})
    v125_origin_rows = []
    for alias, meta in v125_origins.items():
        p = ROOT / meta["path"]
        actual = sha(p) if p.is_file() else None
        v125_origin_rows.append({"alias": alias, "path": meta["path"],
                                 "expected_sha256": meta["sha256"],
                                 "actual_sha256": actual, "matches": actual == meta["sha256"]})
    candidate_pin = old_root.get("candidate_native_receipt")
    candidate_receipt_path = ROOT / candidate_pin["path"] if candidate_pin else None
    candidate_receipt = load(candidate_receipt_path) if candidate_receipt_path and candidate_receipt_path.is_file() else {}
    v125_closure = closure(candidate_receipt_path, candidate_receipt) if candidate_receipt else {"all_match": False, "mismatches": ["candidate receipt missing"]}
    add("frozen_v125_root_index_and_candidate_closure",
        sha(V125_RESULTS) == "50d28584197078bd6e2292dba71735c8ed55d710866176dc104edee324f8486d" and
        sha(V125_INDEX) == "a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987" and
        old_root.get("status") is not None and v125_index.get("status", "").startswith("PASS") and
        len(v125_origins) == 18 and all(x["matches"] for x in v125_origin_rows) and
        bool(v125_pin_checks) and all(x["matches"] for x in v125_pin_checks) and v125_closure["all_match"],
        {"root_results_sha256": sha(V125_RESULTS), "expected_root_results_sha256": "50d28584197078bd6e2292dba71735c8ed55d710866176dc104edee324f8486d",
         "root_pin_checks": len(v125_pin_checks),
         "root_pin_mismatches": [x for x in v125_pin_checks if not x["matches"]],
         "index_sha256": sha(V125_INDEX), "index_status": v125_index.get("status"),
         "origin_count": len(v125_origins), "origin_mismatches": [x for x in v125_origin_rows if not x["matches"]],
         "candidate_receipt": candidate_pin, "candidate_closure": v125_closure})

    tooling = load(V126 / "orchestration/root-tooling-freeze.json")
    tooling_matches = {p: sha(ROOT / p) == h for p, h in tooling.get("files", {}).items()}
    core_matches = {p: sha(ROOT / p) == h for p, h in tooling.get("core_recipe", {}).items()}
    add("v126_root_tooling_freeze", bool(tooling_matches) and bool(core_matches) and
        tooling.get("core_recipe_reused_byte_exact") is True and
        all(tooling_matches.values()) and all(core_matches.values()),
        {"freeze_sha256": sha(V126 / "orchestration/root-tooling-freeze.json"),
         "file_mismatches": [p for p, ok in tooling_matches.items() if not ok],
         "core_recipe_mismatches": [p for p, ok in core_matches.items() if not ok]})

    rev5_path = V126 / "audit/full-independent-tooling-freeze-revision5.json"
    rev5 = load(rev5_path)
    rev5_maps = [rev5.get("source_sha256", {}), rev5.get("fixture_sha256", {})]
    rev5_bad = [p for mp in rev5_maps for p, h in mp.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    rev5_maps_nonempty = all(bool(mp) for mp in rev5_maps)
    v2supp_path = V126 / "audit/full-independent-tooling-freeze-v2-supplement.json"
    v2supp = load(v2supp_path)
    v2_map = {v2supp["auditor"]["path"]: v2supp["auditor"]["sha256"],
              v2supp["unchanged_original_auditor"]["path"]: v2supp["unchanged_original_auditor"]["sha256"]}
    v2_bad = [p for p, h in v2_map.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    v3der_path = V126 / "audit/full-independent-v3-derivation.json"
    v3der = load(v3der_path)
    v3supp_path = V126 / "audit/full-independent-tooling-freeze-v3-supplement.json"
    v3supp = load(v3supp_path)
    v3supp_pins = [v3supp.get("auditor", {}), v3supp.get("derivation", {}),
                   v3supp.get("integration_index", {}), v3supp.get("preserved_v2_auditor", {}),
                   v3supp.get("previous_supplement", {})]
    v3supp_bad = []
    for pin in v3supp_pins:
        if not pin.get("path") or not pin.get("sha256") or not (ROOT / pin["path"]).is_file() or sha(ROOT / pin["path"]) != pin["sha256"]:
            v3supp_bad.append(pin)
    v3_pair = {v3der["candidate"]["path"]: v3der["candidate"]["sha256"],
               v3der["original"]["path"]: v3der["original"]["sha256"]}
    v3_bad = [p for p, h in v3_pair.items() if not (ROOT / p).is_file() or sha(ROOT / p) != h]
    add("v126_rev5_and_v2_v3_supplements", rev5_maps_nonempty and bool(v2_map) and bool(v3_pair) and
        len(v3supp_pins) == 5 and not v3supp_bad and not rev5_bad and not v2_bad and not v3_bad and
        v3supp.get("actual_RTL_rerun") is False and
        v3supp.get("status") == "FROZEN_V3_EXACT_PRODUCER_INVENTORY_CHECK_MOVE",
        {"rev5_sha256": sha(rev5_path), "rev5_status": rev5.get("status"),
         "rev5_pin_count": sum(len(x) for x in rev5_maps), "rev5_mismatches": rev5_bad,
         "v2_supplement_sha256": sha(v2supp_path), "v2_status": v2supp.get("status"),
         "v2_mismatches": v2_bad, "v3_derivation_sha256": sha(v3der_path),
         "v3_status": v3der.get("status"), "v3_mismatches": v3_bad})

    large = [{"path": rel(p), "bytes": p.stat().st_size} for p in files if p.stat().st_size > 50 * 1024 * 1024]
    add("new_v126_files_over_50MiB", not large, {"count": len(large), "files": large})
    secret_pat = re.compile(r"(?i)(secret|credential|password|token|id_rsa|private.?key|\.env|api.?key)")
    suspicious = [rel(p) for p in files if secret_pat.search(p.name)]
    add("secret_like_filenames_only", not suspicious,
        {"count": len(suspicious), "filenames": suspicious,
         "contents_read": False})

    final_pins = []
    if root_path.is_file():
        root_obj = load(root_path)
        final_pins = pin_checks(root_obj, prefix="V126_root_results")
        # Include the root results file itself and every extant referenced file pin.
        final_checks_ok = bool(final_pins) and all(x["matches"] for x in final_pins)
        final_status = root_obj.get("status")
    else:
        root_obj = None
        final_checks_ok = False
        final_status = None
    final_required = args.final
    add("final_root_results_and_recursive_pins", (not final_required) or
        (root_obj is not None and final_checks_ok),
        {"required": final_required, "root_results_path": rel(root_path),
         "exists": root_path.is_file(), "status": final_status,
         "pin_count": len(final_pins),
         "pin_mismatches": [x for x in final_pins if not x["matches"]]})

    all_ok = all(x["pass"] for x in checks)
    if args.final:
        status = "PASS_FINAL_READONLY_QA" if all_ok else "FINAL_QA_GAPS"
    else:
        status = "PREPARATION_ONLY" if all_ok else "PREPARATION_GAPS"
    result = {
        "schema": "v126-final-readonly-qa-v1",
        "status": status,
        "final_mode": args.final,
        "scope": "Read-only syntax, documentation-link, source lineage, freeze/pin, file-size and filename QA. No RTL/Vivado/Docker jobs; no secret file contents read.",
        "root_results": rel(root_path),
        "checks": checks,
        "check_count": len(checks),
        "passed_checks": sum(x["pass"] for x in checks),
        "limitations": [
            "Preparation mode never reports final PASS and does not require root results.",
            "Final mode requires root results and every recursively discovered path/SHA-256 pin to resolve and match.",
            "Historical failed-attempt source snapshots are validated through retained receipts/closures, not compared to current production inputs.",
            "Filename scanning reports names only; no secret-like file contents are opened.",
            "This review does not establish hardware qualification or board performance.",
        ],
    }
    if args.final:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.final and not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
