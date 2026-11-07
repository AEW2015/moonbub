#!/usr/bin/env python3
"""Deterministic source and functional-evidence audit for V103 geometry candidates.

This auditor does not run simulators or vendor tools. It checks provenance,
approved function-only edits, pinned focused receipts and traces, and completed
paired-regression receipts. Missing required receipts leave the result PENDING;
available failing evidence produces FAIL.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "6d2ca3ae9abe207215d6130cfb0087fd07928917"
PROFILE = "experiments/python-gamebub-v99/profile.json"
PROFILE_SHA256 = "8e17b24afbefe32ca00b2606ee80a3a70dd06e9050e76d50c9698fd524e735be"
INVENTORY = "experiments/python-gamebub-v100/inventory.json"
OUT = ROOT / "experiments/python-gamebub-v103/source-audit.json"
DOC = ROOT / "docs/cu66-v103/audit.md"
REGRESS = "scripts/cu66-v103/regress.py"

LANES = {
    "admission_fresh": ("admission", "fresh", 24, 52),
    "admission_canonical": ("admission", "canonical", 88, 84),
    "reconstruct_canonical": ("reconstruct", "canonical", 88, 84),
    "combined_canonical": ("combined", "canonical", 88, 84),
}
FOCUSED = {
    "reconstruct": {
        "dir": "experiments/python-gamebub-v103/reconstruct",
        "kind": "reconstruct",
        "domains": 32768,
    },
    "admission": {
        "dir": "experiments/python-gamebub-v103/admission",
        "kind": "admission",
        "domains": None,
    },
}

checks: list[dict[str, Any]] = []
errors: list[str] = []
pending: list[str] = []
inputs: dict[str, str] = {}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record_input(path: str, data: bytes) -> bytes:
    inputs[path] = digest(data)
    return data


def read(path: str) -> bytes:
    return record_input(path, (ROOT / path).read_bytes())


def read_json(path: str) -> Any:
    return json.loads(read(path))


def check(name: str, ok: bool, detail: Any = None) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        errors.append(name)


def need(name: str, detail: Any = None) -> None:
    pending.append(name)
    checks.append({"name": name, "status": "PENDING", "detail": detail})


def git_blob(rev: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rev}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    record_input(f"git/{rev}/{path}", proc.stdout)
    return proc.stdout


def baseline_state() -> tuple[bool, bool]:
    exists = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{BASELINE}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    ancestor = exists and subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", BASELINE, "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    return exists, ancestor


def function_span(src: bytes, name: str) -> tuple[bytes, bytes, bytes]:
    """Return prefix, exact function-through-endfunction span, and suffix."""
    marker = ("function automatic logic" if name in ("quant_cell", "cell_index") else "function")
    starts = []
    cursor = 0
    while True:
        at = src.find(marker.encode(), cursor)
        if at < 0:
            break
        line_end = src.find(b"\n", at)
        if line_end < 0:
            break
        if name.encode() in src[at:line_end]:
            starts.append(at)
        cursor = line_end + 1
    if len(starts) != 1:
        raise ValueError(f"expected one declaration for {name}, found {len(starts)}")
    declaration = starts[0]
    start = src.rfind(b"\n", 0, declaration) + 1
    end_token = b"endfunction"
    end = src.find(end_token, start)
    if end < 0 or src.find(end_token, end + len(end_token)) == -1:
        raise ValueError(f"missing function terminator for {name}")
    end += len(end_token)
    return src[:start], src[start:end], src[end:]


def module_header(src: bytes, module: str) -> bytes:
    start = src.find(("module " + module).encode())
    if start < 0:
        raise ValueError(f"module declaration missing: {module}")
    end = src.find(b");", start)
    if end < 0:
        raise ValueError(f"module header missing terminator: {module}")
    return src[start : end + 2]


def audit_frozen_inputs() -> None:
    exists, ancestor = baseline_state()
    check("baseline_exists_and_is_ancestor", exists and ancestor,
          {"baseline": BASELINE, "exists": exists, "ancestor": ancestor})

    profile = read(PROFILE)
    base_profile = git_blob(BASELINE, PROFILE)
    check("v99_profile_pinned", digest(profile) == PROFILE_SHA256 and base_profile == profile,
          {"sha256": digest(profile), "expected": PROFILE_SHA256, "baseline_blob_equal": base_profile == profile})

    inventory_bytes = read(INVENTORY)
    inv = json.loads(inventory_bytes)
    rows = inv.get("source_files", [])
    mismatches, missing, baseline_diffs = [], [], []
    for row in rows:
        path, expected = row.get("path", ""), row.get("sha256")
        if not path:
            missing.append("<inventory-row-without-path>")
            continue
        try:
            content = read(path)
        except FileNotFoundError:
            missing.append(path)
            continue
        if digest(content) != expected:
            mismatches.append(path)
        if git_blob(BASELINE, path) != content:
            baseline_diffs.append(path)
    check("v100_historical_source_inventory_unchanged", bool(rows) and not mismatches and not missing and not baseline_diffs,
          {"count": len(rows), "hash_mismatches": mismatches, "missing": missing, "baseline_blob_differences": baseline_diffs})

    # V102 source values are the only paired-run controls; ensure they still
    # equal the immutable branch baseline blobs.
    v102_paths = [
        "fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv",
        "fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv",
    ]
    differences = []
    for path in v102_paths:
        content = read(path)
        if git_blob(BASELINE, path) != content:
            differences.append(path)
    check("v102_candidate_baselines_unchanged", not differences, {"paths": v102_paths, "differences": differences})
    read(REGRESS)


def audit_function_candidate(kind: str, source_path: str, baseline_path: str, change_path: str,
                             function: str, module: str, port_manifest: str) -> dict[str, Any]:
    manifest = read_json(change_path)
    source = read(source_path)
    base = read(baseline_path)
    base_blob = git_blob(BASELINE, baseline_path)
    pre, old_func, post = function_span(base, function)
    cpre, new_func, cpost = function_span(source, function)
    old_decl = old_func.splitlines(keepends=True)[0]
    new_decl = new_func.splitlines(keepends=True)[0]
    prefix_ok = pre == cpre
    suffix_ok = post == cpost
    expected_prefix = manifest.get("unchanged_prefix_sha256")
    expected_suffix = manifest.get("unchanged_suffix_sha256")
    if kind == "admission":
        expected_prefix = digest(pre)
        expected_suffix = digest(post)
    transform_ok = prefix_ok and suffix_ok
    module_header_ok = module_header(base, module) == module_header(source, module)
    candidate_pin_ok = digest(source) == manifest.get("candidate_sha256")
    original_pin_ok = digest(base) == manifest.get("original_sha256") and base_blob == base
    check(f"{kind}_source_and_manifest_pins", candidate_pin_ok and original_pin_ok,
          {"candidate_sha256": digest(source), "manifest_candidate_sha256": manifest.get("candidate_sha256"),
           "baseline_sha256": digest(base), "manifest_baseline_sha256": manifest.get("original_sha256"),
           "baseline_git_blob_equal": base_blob == base})
    check(f"{kind}_approved_function_only_edit", transform_ok and old_decl == new_decl
          and digest(pre) == expected_prefix and digest(post) == expected_suffix,
          {"function": function, "old_function_sha256": digest(old_func), "new_function_sha256": digest(new_func),
           "function_declaration_equal": old_decl == new_decl, "prefix_equal": prefix_ok, "suffix_equal": suffix_ok, "prefix_sha256": digest(pre),
           "expected_prefix_sha256": expected_prefix, "suffix_sha256": digest(post), "expected_suffix_sha256": expected_suffix})
    check(f"{kind}_production_header_unchanged", module_header_ok,
          {"module": module, "header_sha256": digest(module_header(source, module))})
    ports = read_json(port_manifest)
    expected_count = ports.get("production_port_count")
    port_rows = ports.get("production_ports", ports.get("ports", []))
    # Header equality is byte-for-byte; manifest inventory count is an
    # independent guard against a malformed/empty interface ledger.
    check(f"{kind}_port_ledger_present", isinstance(expected_count, int) and expected_count > 0
          and isinstance(port_rows, list) and len(port_rows) == expected_count,
          {"manifest": port_manifest, "production_port_count": expected_count, "listed_ports": len(port_rows)})
    return {"candidate": source_path, "baseline": baseline_path, "change_manifest": change_path,
            "function": function, "candidate_sha256": digest(source), "baseline_sha256": digest(base),
            "production_port_count": expected_count}


def expected_admission_tiles() -> list[int]:
    tiles = set(range(8192))
    for bit in range(32):
        for delta in (-181, -180, -179, -91, -90, -89, -2, -1, 0, 1, 2, 44, 45, 46, 89, 90, 91, 179, 180, 181):
            value = (1 << bit) + delta
            if 0 <= value <= 0xFFFFFFFF:
                tiles.add(value)
    tiles.update(0xFFFFFFFF - i for i in range(512))
    for i in range(1024):
        for q in (i, 0xFFFFFFFF // 90 - i):
            for rem in (0, 1, 44, 45, 46, 88, 89):
                value = q * 90 + rem
                if value <= 0xFFFFFFFF:
                    tiles.add(value)
    rng = 103501
    for _ in range(10000):
        rng ^= (rng << 13) & 0xFFFFFFFF
        rng ^= rng >> 17
        rng ^= (rng << 5) & 0xFFFFFFFF
        tiles.add(rng & 0xFFFFFFFF)
    return sorted(tiles)


def audit_trace(receipt: dict[str, Any], attempt_dir: Path, kind: str) -> tuple[bool, dict[str, Any]]:
    trace_meta = receipt.get("trace_replay", {})
    relpath = trace_meta.get("path")
    if not relpath:
        return False, {"reason": "trace path missing"}
    trace_path = attempt_dir / relpath
    raw_gzip = trace_path.read_bytes()
    record_input(str(trace_path.relative_to(ROOT)), raw_gzip)
    if digest(raw_gzip) != trace_meta.get("sha256"):
        return False, {"reason": "compressed trace digest mismatch"}
    raw = gzip.decompress(raw_gzip)
    if digest(raw) != trace_meta.get("raw_sha256"):
        return False, {"reason": "expanded trace digest mismatch"}
    rows = [json.loads(line) for line in raw.splitlines() if line]
    if len(rows) != trace_meta.get("rows"):
        return False, {"reason": "trace row count mismatch", "rows": len(rows)}
    if kind == "reconstruct":
        seen = set()
        for index, row in enumerate(rows):
            p, t = row["plane"], row["tile"]
            expected = (((t // 90) // 2) * 45 + (t % 90) // 2) & 2047 if p == 0 else t & 2047
            if p != index // 8192 or t != index % 8192 or row.get("expected") != expected or row.get("original") != expected or row.get("candidate") != expected:
                return False, {"reason": "independent reconstruction oracle mismatch", "row": row}
            seen.add((p, t))
        complete = len(seen) == 32768 and len(rows) == 32768
    else:
        tiles = expected_admission_tiles()
        tile_set = set(tiles)
        if trace_meta.get("tiles_per_plane") != len(tiles):
            return False, {"reason": "focused receipt tile count differs from independently generated domain", "expected": len(tiles), "actual": trace_meta.get("tiles_per_plane")}
        seen = set()
        for index, row in enumerate(rows):
            p, t = row["plane"], row["tile"]
            expected = ((t // 180) * 45 + (t % 90) // 2) & 0xFFFFFFFF if p == 0 else t
            expected_plane, expected_tile = divmod(index, len(tiles))
            if p != expected_plane or t != tiles[expected_tile] or t not in tile_set or row.get("expected") != expected or row.get("original") != expected or row.get("candidate") != expected:
                return False, {"reason": "independent admission oracle mismatch", "row": row}
            seen.add((p, t))
        complete = seen == {(p, t) for p in range(4) for t in tiles} and len(rows) == 4 * len(tiles)
    return complete, {"status": "PASS" if complete else "FAIL", "rows": len(rows),
                      "unique_pairs": len(seen), "raw_sha256": digest(raw), "gzip_sha256": digest(raw_gzip)}


def audit_focused(kind: str) -> None:
    directory = FOCUSED[kind]["dir"]
    summary_path = f"{directory}/results.json"
    try:
        summary = read_json(summary_path)
    except FileNotFoundError:
        need(f"focused_{kind}_receipt", {"expected": summary_path})
        return
    selected = summary.get("selected_report")
    if not selected:
        selected = f"{directory}/attempts/results.json"
    try:
        receipt = read_json(selected)
    except (FileNotFoundError, IsADirectoryError):
        need(f"focused_{kind}_selected_receipt", {"selected_report": selected})
        return
    attempt_dir = (ROOT / selected).parent
    artifacts = receipt.get("artifacts_sha256", {})
    artifact_mismatches = []
    for rel, expected in artifacts.items():
        p = attempt_dir / rel
        try:
            data = p.read_bytes()
        except FileNotFoundError:
            artifact_mismatches.append({"path": rel, "reason": "missing"})
            continue
        record_input(str(p.relative_to(ROOT)), data)
        if digest(data) != expected:
            artifact_mismatches.append({"path": rel, "reason": "digest"})
    source_mismatches = []
    for source, expected in receipt.get("source_sha256", {}).items():
        try:
            source_data = read(source)
        except FileNotFoundError:
            source_mismatches.append({"path": source, "reason": "missing"})
            continue
        if digest(source_data) != expected:
            source_mismatches.append({"path": source, "reason": "digest"})
    if kind == "reconstruct":
        adapters = [
            ("fpga/experiments/cu66-v103-reconstruct/reconstruct_original.sv",
             "fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv", "reconstruct_original"),
            ("fpga/experiments/cu66-v103-reconstruct/reconstruct_candidate.sv",
             "fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv", "reconstruct_candidate"),
        ]
        probe_extra = (b",\n    input logic [1:0] probe_plane,\n    input logic [12:0] probe_tile,\n"
                       b"    output logic [10:0] probe_cell\n);")
        probe_assign = b"    assign probe_cell=quant_cell(probe_plane,probe_tile);\n"
        module_name = "cu66_reconstruct_stream_v91k"
        probe_function = "quant_cell"
    else:
        adapters = [
            ("fpga/experiments/cu66-v103-admission/admission_original.sv",
             "fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv", "admission_original"),
            ("fpga/experiments/cu66-v103-admission/admission_candidate.sv",
             "fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv", "admission_candidate"),
        ]
        probe_extra = (b",\n    input logic [1:0] probe_plane,\n    input logic [31:0] probe_tile,\n"
                       b"    output logic [31:0] probe_cell\n);")
        probe_assign = b"    assign probe_cell=cell_index(probe_plane,probe_tile);\n"
        module_name = "cs88_admission_v91i2a"
        probe_function = "cell_index"
    adapter_mismatches = []
    for adapter_path, production_path, adapter_module in adapters:
        adapter_data = read(adapter_path)
        production_data = read(production_path)
        try:
            normalized = adapter_data.replace(("module " + adapter_module + " (").encode(),
                                              ("module " + module_name + " (").encode(), 1)
            normalized = normalized.replace(probe_extra, b");", 1).replace(probe_assign, b"", 1)
            if normalized != production_data:
                adapter_mismatches.append(adapter_path)
        except Exception:
            adapter_mismatches.append(adapter_path)
    trace_ok, trace_detail = audit_trace(receipt, attempt_dir, kind)
    baseline_ok = receipt.get("baseline_revision") == BASELINE
    source_ok = (receipt.get("status") == "PASS" and receipt.get("actual_RTL_run") is True
                 and receipt.get("verification_adapters_preserve_complete_production_body") is True
                 and not source_mismatches)
    expected_cases = 32768 if kind == "reconstruct" else 4 * len(expected_admission_tiles())
    focused_ok = (baseline_ok and source_ok and receipt.get("assertions_disabled_or_downgraded") is False
                  and receipt.get("strict_warnings") is True and receipt.get("terminal_verdict", {}).get("status") == "TEST_PASS"
                 and receipt.get("terminal_verdict", {}).get("cases") == expected_cases
                  and receipt.get("clock_edges") == (0 if kind == "reconstruct" else 0)
                 and receipt.get("trace_replay", {}).get("status") == "PASS"
                 and not artifact_mismatches and not adapter_mismatches and trace_ok)
    check(f"focused_{kind}_receipt_and_artifact_pins", focused_ok,
          {"selected_report": selected, "baseline_revision": receipt.get("baseline_revision"),
           "terminal_verdict": receipt.get("terminal_verdict"), "artifact_mismatches": artifact_mismatches,
           "trace": trace_detail, "receipt_status": receipt.get("status"), "strict_warnings": receipt.get("strict_warnings"),
           "source_mismatches": source_mismatches, "adapter_mismatches": adapter_mismatches,
           "assertions_disabled_or_downgraded": receipt.get("assertions_disabled_or_downgraded")})


def audit_lane(name: str, variant: str, mode: str, cases: int, directed: int) -> None:
    path = f"experiments/python-gamebub-v103/regression/{variant}/{mode}/results.json"
    try:
        report = read_json(path)
    except FileNotFoundError:
        need(f"paired_lane_{name}", {"expected": path, "case_profile_runs": cases, "directed_checks": directed})
        return
    selected = report.get("selected_report")
    try:
        attempt = read_json(selected) if selected else report
    except FileNotFoundError:
        need(f"paired_lane_{name}_selected_attempt", {"selected_report": selected})
        return
    if selected:
        read(selected)
    if (variant == "combined" and attempt.get("status") == "FAIL" and not attempt.get("runs")
            and "resource gate: memory PSI full avg10 >= 1" in attempt.get("error", "")):
        need(f"paired_lane_{name}", {"selected_report": selected,
                                      "reason": "retained host resource launch gate; awaiting completed retry"})
        return
    attempt_dir = (ROOT / selected).parent if selected else (ROOT / path).parent
    status_ok = attempt.get("status") == "PASS" and report.get("status") == "PASS"
    counts_ok = attempt.get("case_profile_runs") == cases and attempt.get("directed_checks") == directed
    run_rows = attempt.get("runs", [])
    seeds_ok = [r.get("seed") for r in run_rows] == [103401, 103402]
    equalities_ok = bool(run_rows) and all(
        r.get("equalities", {}).get("stdout") is True and r.get("equalities", {}).get("events") is True
        and (mode != "canonical" or r.get("equalities", {}).get("canonical") is True)
        for r in run_rows)
    terminals_ok = True
    for row in run_rows:
        for side in ("baseline", "candidate"):
            verdict = row.get("variants", {}).get(side, {}).get("verdict", {})
            terminals_ok &= verdict.get("status") == "TEST_PASS"
            terminals_ok &= verdict.get("cases") == (6 if mode == "fresh" else 22)
            terminals_ok &= verdict.get("directed_checks") == (13 if mode == "fresh" else 21)
    compile_commands = [c for c in attempt.get("commands", []) if any("verilator" == str(arg) for arg in c.get("argv", []))
                        and "--build" in c.get("argv", [])]
    strict_compile = len(compile_commands) == 2 and all(
        "--assert" in c["argv"] and "-Wall" in c["argv"] and any("-Werror" in arg for arg in c["argv"])
        and c.get("exit_code") == 0 for c in compile_commands)
    warning_logs_clean = all(
        not (attempt_dir / c.get("log", "")).read_text(errors="replace").__contains__("%Warning-")
        for c in compile_commands)
    strict_ok = attempt.get("assertions_disabled_or_downgraded") is False and strict_compile and warning_logs_clean
    artifact_mismatches = []
    for rel, expected in attempt.get("artifacts_sha256", {}).items():
        artifact = attempt_dir / rel
        try:
            content = artifact.read_bytes()
        except FileNotFoundError:
            artifact_mismatches.append({"path": rel, "reason": "missing"})
            continue
        record_input(f"paired/{name}/artifact/{rel}", content)
        if digest(content) != expected:
            artifact_mismatches.append({"path": rel, "reason": "digest"})
    source_mismatches = []
    for source, expected in attempt.get("source_sha256", {}).items():
        try:
            content = read(source)
        except FileNotFoundError:
            source_mismatches.append({"path": source, "reason": "missing"})
            continue
        if digest(content) != expected:
            source_mismatches.append({"path": source, "reason": "digest"})
    expected_baseline_overrides = {
        "fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv": "fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv",
        "fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv": "fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv",
    }
    baseline_maps_ok = attempt.get("baseline_overrides") == expected_baseline_overrides
    candidate_paths = {c.get("path") for c in attempt.get("candidates", [])}
    expected_candidate_paths = {
        "admission": {"fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv"},
        "reconstruct": {"fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv"},
        "combined": {"fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv",
                     "fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv"},
    }[variant]
    candidate_maps_ok = candidate_paths == expected_candidate_paths
    independent_equalities = []
    per_seed_files_ok = True
    for seed in (103401, 103402):
        suffixes = ["-simulation.jsonl", "-events.jsonl.gz"]
        if mode == "canonical":
            suffixes.append("-canonical.tsv.gz")
        equal_row = {"seed": seed, "files": {}}
        for suffix in suffixes:
            pair_contents = []
            for side in ("baseline", "candidate"):
                file_path = attempt_dir / f"{side}-{seed}{suffix}"
                try:
                    raw_file = file_path.read_bytes()
                    record_input(f"paired/{name}/run/{file_path.name}", raw_file)
                    content = gzip.decompress(raw_file) if suffix.endswith(".gz") else raw_file
                    pair_contents.append(content)
                except FileNotFoundError:
                    pair_contents.append(None)
                except OSError:
                    pair_contents.append(None)
            is_equal = pair_contents[0] is not None and pair_contents[0] == pair_contents[1]
            equal_row["files"][suffix] = is_equal
            per_seed_files_ok &= is_equal
        independent_equalities.append(equal_row)
    check(f"paired_lane_{name}_receipt", status_ok and counts_ok and seeds_ok and equalities_ok and terminals_ok and strict_ok
          and not artifact_mismatches and not source_mismatches and baseline_maps_ok and candidate_maps_ok and per_seed_files_ok,
          {"selected_report": selected, "status": attempt.get("status"), "case_profile_runs": attempt.get("case_profile_runs"),
           "directed_checks": attempt.get("directed_checks"), "seeds": [r.get("seed") for r in run_rows],
           "equalities": [r.get("equalities") for r in run_rows], "strict_compile_commands": len(compile_commands),
           "strict_assertions_wall_werror": strict_compile, "warning_logs_clean": warning_logs_clean,
           "assertions_disabled_or_downgraded": attempt.get("assertions_disabled_or_downgraded"),
           "baseline_overrides_match": baseline_maps_ok, "candidate_paths_match": candidate_maps_ok,
           "independent_file_equalities": independent_equalities, "artifact_mismatches": artifact_mismatches,
           "source_mismatches": source_mismatches})


def audit_stopped_attempts() -> None:
    path = "experiments/python-gamebub-v103/stopped-attempts.json"
    try:
        manifest = read_json(path)
    except FileNotFoundError:
        need("retained_stopped_attempt_classification", {"expected": path})
        return
    rows = manifest.get("attempts", [])
    mismatches = []
    verified = []
    for row in rows:
        receipt_path = row.get("receipt", "")
        try:
            receipt_data = read(receipt_path)
            receipt = json.loads(receipt_data)
        except (FileNotFoundError, json.JSONDecodeError):
            mismatches.append({"receipt": receipt_path, "reason": "missing_or_invalid"})
            continue
        attempt_dir = (ROOT / receipt_path).parent
        receipt_hash_ok = digest(receipt_data) == row.get("sha256")
        artifact_mismatches = []
        for rel, expected in receipt.get("artifacts_sha256", {}).items():
            artifact_path = attempt_dir / rel
            try:
                artifact_data = artifact_path.read_bytes()
            except FileNotFoundError:
                artifact_mismatches.append({"path": rel, "reason": "missing"})
                continue
            record_input(f"stopped_attempt/artifact/{rel}", artifact_data)
            if digest(artifact_data) != expected:
                artifact_mismatches.append({"path": rel, "reason": "digest"})
        source_mismatches = []
        for source, expected in receipt.get("source_sha256", {}).items():
            try:
                source_data = read(source)
            except FileNotFoundError:
                source_mismatches.append({"path": source, "reason": "missing"})
                continue
            if digest(source_data) != expected:
                source_mismatches.append({"path": source, "reason": "digest"})
        completed_commands = [c for c in receipt.get("commands", []) if c.get("exit_code") == 0]
        baseline_cmd = next((c for c in receipt.get("commands", [])
                             if c.get("log") == "baseline-103401-simulation.jsonl"), None)
        baseline_verdict = False
        if baseline_cmd and baseline_cmd.get("exit_code") == 0:
            try:
                verdict_rows = [json.loads(line) for line in (attempt_dir / baseline_cmd["log"]).read_text().splitlines()]
                verdicts = [r for r in verdict_rows if r.get("type") == "verdict"]
                baseline_verdict = (len(verdicts) == 1 and verdicts[0].get("status") == "TEST_PASS"
                                    and verdicts[0].get("seed") == 103401 and verdicts[0].get("cases") == 22
                                    and verdicts[0].get("directed_checks") == 21)
            except (FileNotFoundError, json.JSONDecodeError):
                baseline_verdict = False
        candidate_simulation_started = any(
            c.get("log", "").startswith("candidate-") and "simulation" in c.get("log", "")
            for c in receipt.get("commands", []))
        compile_ok = sum("--build" in c.get("argv", []) and c.get("exit_code") == 0
                         for c in receipt.get("commands", [])) == 2
        reason_ok = (receipt.get("baseline_revision") == BASELINE and receipt.get("variant") == "combined"
                     and receipt.get("mode") == "canonical" and receipt.get("status") == "FAIL"
                     and receipt.get("error_class") == "RuntimeError"
                     and "resource gate: memory PSI full avg10 >= 1" in receipt.get("error", "")
                     and row.get("classification") == "HOST_RESOURCE_LAUNCH_GATE"
                     and row.get("policy_relaxed_for_retry") is False
                     and row.get("sources_modified_for_retry") is False
                     and row.get("RTL_mismatch_reported") is False
                     and not receipt.get("runs") and baseline_verdict and compile_ok and not candidate_simulation_started
                     and row.get("scope", "").find("No paired result completed") >= 0)
        good = receipt_hash_ok and reason_ok and not artifact_mismatches and not source_mismatches
        if not good:
            mismatches.append({"receipt": receipt_path, "sha256_match": receipt_hash_ok,
                               "classification_valid": reason_ok, "artifact_mismatches": artifact_mismatches,
                               "source_mismatches": source_mismatches})
        verified.append({"receipt": receipt_path, "sha256_match": receipt_hash_ok,
                         "classification_valid": reason_ok, "completed_commands": len(completed_commands),
                         "baseline_first_seed_passed": baseline_verdict, "both_compiles_passed": compile_ok,
                         "candidate_simulation_started": candidate_simulation_started})
    check("retained_stopped_attempt_is_resource_gate_not_rtl_failure", manifest.get("schema") == "v103-retained-stopped-attempts-v1"
          and bool(rows) and not mismatches,
          {"attempt_count": len(rows), "verified": verified, "mismatches": mismatches})


def write_doc(result: dict[str, Any]) -> None:
    status = result["status"]
    rows = ["# V103 source and functional evidence audit", "", f"**Status: {status}.**",
            "", "This deterministic audit binds source and receipt inputs by SHA-256. It checks the frozen V99 profile and V100 historical source inventory, V102 source baselines, V103 function-only edits and headers, focused function traces, and paired component regressions. It performs no simulation or vendor flow.",
            "", "## Audit result", "", "| Area | Status |", "|---|---|"]
    for item in result["checks"]:
        rows.append(f"| {item['name']} | {item['status']} |")
    rows += ["", "## Paired regression lanes", "",
             "| Candidate | Mode | Case/profile runs | Directed checks | Result |",
             "|---|---|---:|---:|---|"]
    lane_totals = [0, 0]
    display_names = {"admission": "Admission", "reconstruct": "Reconstruction", "combined": "Combined"}
    for lane_name, (variant, mode, _, _) in LANES.items():
        check_name = f"paired_lane_{lane_name}_receipt"
        item = next((c for c in result["checks"] if c["name"] == check_name), {})
        detail = item.get("detail", {})
        cruns, directed = detail.get("case_profile_runs", 0), detail.get("directed_checks", 0)
        if item.get("status") == "PASS":
            lane_totals[0] += cruns
            lane_totals[1] += directed
        rows.append(f"| {display_names[variant]} | {mode} | {cruns} | {directed} | {item.get('status', 'PENDING')} |")
    rows.append(f"| **Total** |  | **{lane_totals[0]}** | **{lane_totals[1]}** |  |")
    rows += ["", f"Bound input files: **{len(result['input_sha256'])}**.", ""]
    if result["pending"]:
        rows += ["## Pending evidence", "", "The following required receipts are not available yet:", ""]
        rows += [f"- {name}" for name in result["pending"]]
        rows.append("")
    if result["errors"]:
        rows += ["## Failed checks", ""]
        rows += [f"- {name}" for name in result["errors"]]
        rows.append("")
    rows += ["The JSON audit contains the detailed check results and exact SHA-256 pins. A `PASS_EVIDENCE` result qualifies only the audited source and component evidence; it does not claim native implementation timing closure, board integration, or hardware frame rate.", ""]
    DOC.write_text("\n".join(rows))


def main() -> int:
    try:
        audit_frozen_inputs()
        candidates = [
            audit_function_candidate("reconstruct", "fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv",
                                     "fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv",
                                     "fpga/experiments/cu66-v103-reconstruct/change.json", "quant_cell",
                                     "cu66_reconstruct_stream_v91k", "fpga/experiments/cu66-v103-reconstruct/ports.json"),
            audit_function_candidate("admission", "fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv",
                                     "fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv",
                                     "fpga/experiments/cu66-v103-admission/change.json", "cell_index",
                                     "cs88_admission_v91i2a", "fpga/experiments/cu66-v103-admission/ports.json"),
        ]
        for kind in FOCUSED:
            audit_focused(kind)
        for name, (variant, mode, cases, directed) in LANES.items():
            audit_lane(name, variant, mode, cases, directed)
        audit_stopped_attempts()
        status = "FAIL" if errors else ("PENDING" if pending else "PASS_EVIDENCE")
    except Exception as exc:
        errors.append(f"auditor_exception:{type(exc).__name__}:{exc}")
        status = "FAIL"
    result = {
        "schema": "v103-source-functional-audit-v1",
        "status": status,
        "baseline_revision": BASELINE,
        "checks": checks,
        "errors": errors,
        "pending": pending,
        "candidate_sources": locals().get("candidates", []),
        "input_sha256": dict(sorted(inputs.items())),
        "limits": ["No native synthesis, placement, routing, or physical timing audit.",
                   "Paired component evidence is not full-system, board, or hardware qualification."],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_doc(result)
    print(json.dumps({"status": status, "checks": len(checks), "pending": pending, "errors": errors}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
