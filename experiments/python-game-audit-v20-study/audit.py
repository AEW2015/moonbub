#!/usr/bin/env python3
"""Portable, read-only evidence audit for the v20 hardware handoff.

Schema-specific checks are added only after the three handoff artifacts exist.
The audit stays pending until the root agent supplies an explicit readiness
signal; merely finding files never promotes evidence to final.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT_PATH = HERE / "audit.json"
STUDIES = {
    "hardware_kit": "hardware/gamebub-v20",
    "mandatory_hud": "experiments/python-game-mandatory-hud-study",
    "inline_reconstruction": "experiments/python-game-inline-reconstruction-study",
}
# Root must explicitly signal final readiness after evidence and acceptance
# checks are complete. Keep empty while any requested artifact is in flight.
READY_STUDIES: set[str] = {"hardware_kit", "mandatory_hud", "inline_reconstruction"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_log(path: Path) -> dict:
    if not path.is_file():
        return {"status": "missing", "passed_count": None}
    content = path.read_text(errors="replace")
    match = re.search(r"Ran (\d+) tests?", content)
    passed = match is not None and "OK" in content and "FAILED (" not in content and "ERROR" not in content
    return {"status": "pass" if passed else "invalid",
            "passed_count": int(match.group(1)) if match else None}


def run_verifier(directory: Path, script: str) -> dict:
    try:
        run = subprocess.run([sys.executable, script], cwd=directory, text=True,
                             capture_output=True, timeout=180)
        return {"status": "pass" if run.returncode == 0 else "fail",
                "returncode": run.returncode, "stdout": run.stdout.strip(),
                "stderr": run.stderr.strip()}
    except Exception as exc:
        return {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}


def source_pins(data: dict) -> tuple[list[dict], list[str]]:
    pins, errors = [], []
    for raw, expected in sorted(data.get("source_sha256", {}).items()):
        path = Path(raw)
        path = path if path.is_absolute() else ROOT / path
        actual = sha256(path) if path.is_file() else None
        pins.append({"path": raw, "expected": expected, "actual": actual,
                     "matches": actual == expected})
        if actual != expected:
            errors.append(f"source pin mismatch or missing source: {raw}")
    return pins, errors


def study_result(name: str, relative: str) -> dict:
    directory = ROOT / relative
    errors = []
    results_path = directory / "results.json"
    try:
        data = json.loads(results_path.read_text())
    except (OSError, json.JSONDecodeError):
        data = {}
        errors.append("results.json missing or invalid JSON")
    pins, pin_errors = source_pins(data)
    errors.extend(pin_errors)
    log_path = directory / "tests.log"
    tests = test_log(log_path)
    if tests["status"] != "pass":
        errors.append("study tests.log missing or not passing")
    if name == "mandatory_hud" and data:
        if data.get("schema") != "gamebub-mandatory-hud-v1":
            errors.append("unexpected mandatory-HUD schema")
        if data.get("counts") != {"cases": 4, "source_acquisitions": 96,
                                  "frame_decisions": 192, "golden_vectors": 20}:
            errors.append("mandatory-HUD campaign inventory mismatch")
        cases = data.get("cases", [])
        if len(cases) != 4:
            errors.append("mandatory-HUD case inventory mismatch")
        mandatory = [c for c in cases if c.get("policy") == "mandatory"]
        if len(mandatory) != 2 or any(
                len(c.get("rows", [])) != 48 or
                any(not r.get("accepted") or r.get("selected_words") != 21120 or
                    r.get("omitted_rectangles") or r.get("selected_word_errors") != 0 or
                    r.get("packet_bytes", 49153) > 49152 or len(r.get("attempts", [])) > 4 or
                    r.get("state_before") != r.get("state_after_builds") or
                    r.get("readers_after_builds", -1) not in
                    (r.get("readers_before", -1), r.get("readers_before", -1) + 1) or
                    r.get("readers_after") != r.get("readers_before") or
                    r.get("receiver_readers_after") != 0 or
                    (not r.get("accepted") and r.get("state_after") != r.get("state_before")) or
                    any(not a.get("accepted") and a.get("discard_ms", 0) <= 0
                        for a in r.get("attempts", [])) for r in c.get("rows", []))
                for c in mandatory):
            errors.append("mandatory accepted frames do not all meet full-HUD, cap, bounded-attempt, and paid-discard requirements")
        if any(r.get("state_before") != r.get("state_after_builds") or
               r.get("readers_after_builds", -1) not in
               (r.get("readers_before", -1), r.get("readers_before", -1) + 1) or
               r.get("readers_after") != r.get("readers_before") or
               r.get("receiver_readers_after") != 0
               for c in cases for r in c.get("rows", [])):
            errors.append("build attempts changed source identity state or leaked/churned reader leases before commit")
        scope = " ".join(data.get("scope", []) +
                          [c.get("limitation", "") for c in data.get("comparisons", [])]).lower()
        if "background quality" not in scope or "mse" not in scope or "30fps proof" not in scope:
            errors.append("mandatory-HUD quality or hardware timing limitations are not explicit")
    elif name == "inline_reconstruction" and data:
        counts = data.get("counts", {})
        if data.get("schema") != "gamebub-inline-generated-reconstruction-v1":
            errors.append("unexpected inline-reconstruction schema")
        expected = {"packets": 16, "native_decisions": 12,
                    "unique_native_acquisitions": 6, "flat_controls": 4,
                    "blocks": 97308, "residual_samples": 6227712,
                    "reconstructed_samples": 6224472,
                    "selected_ui_words": 253440, "profiles": 5}
        if any(counts.get(k) != v for k, v in expected.items()):
            errors.append("inline reconstruction campaign inventory mismatch")
        if len(data.get("frames", [])) != 16 or len(data.get("cases", [])) != 5:
            errors.append("inline frame/profile inventory mismatch")
        scope = " ".join(str(data.get(k, "")) for k in
                          ("arithmetic_scope", "publication_scope", "memory_scope", "timing_scope", "excluded_scope")).lower()
        for term in ("before external output-bank write", "ordinary p", "physical", "conditional",
                     "hardware30fps proof", "outside"):
            if term not in scope:
                errors.append(f"inline tag/order/finalization/scope statement missing: {term}")
        if any(row.get("selected_ui_word_errors") != 0 or
               row.get("canonical_bytes_hashed") != 4 + 2 * row.get("reconstructed_samples", -1)
               for row in data.get("frames", [])):
            errors.append("inline canonical byte or exact UI accounting mismatch")
        analysis_path, analyzer_path = directory / "analysis.json", directory / "analyze.py"
        try:
            analysis_data = json.loads(analysis_path.read_text())
        except (OSError, json.JSONDecodeError):
            analysis_data = {}
        bound = (analysis_data.get("results_sha256") == sha256(results_path)
                 and analyzer_path.is_file()
                 and analysis_data.get("analyzer_sha256") == sha256(analyzer_path))
        if not bound:
            errors.append("inline service analysis is not bound to frozen results/analyzer hashes")
        if (analysis_data.get("counts") != counts
                or analysis_data.get("actual_generated_frames") != 16
                or analysis_data.get("native_tagger_local_array_bytes_max") != 7200
                or analysis_data.get("every_native_profile_misses_33ms") is not True
                or analysis_data.get("generated_golden_unique_objects") != 9):
            errors.append("inline generated-byte/memory/conditional-clock analysis mismatch")
    elif name == "hardware_kit" and data:
        if data.get("schema") != "gamebub-v20-c11-acceptance-v1":
            errors.append("unexpected C11 acceptance schema")
        if (data.get("blocks"), data.get("exact_residual_samples"), data.get("invalid_input_checks")) != (101667, 6506688, 4):
            errors.append("C11 arithmetic golden inventory or input-guard count mismatch")
        if not data.get("toolchain", {}).get("sanitized"):
            errors.append("C11 acceptance was not run with undefined-behavior sanitizer")
        if "not esp32 execution" not in str(data.get("scope", "")).lower() or "physical30fps" not in str(data.get("scope", "")).lower():
            errors.append("C11 arithmetic result overstates or omits hardware qualification scope")
    verifier = None
    if name in READY_STUDIES:
        script = {"hardware_kit": "verify.py", "mandatory_hud": "verify.py",
                  "inline_reconstruction": "verify.py"}[name]
        verifier = run_verifier(directory, script)
        if verifier["status"] != "pass":
            errors.append("retained deterministic verifier replay failed")
        if name == "mandatory_hud":
            analysis = subprocess.run([sys.executable, "analyze.py", "--check"], cwd=directory,
                                      text=True, capture_output=True, timeout=120)
            verifier["analysis_replay"] = {"status": "pass" if analysis.returncode == 0 else "fail",
                                           "returncode": analysis.returncode,
                                           "stdout": analysis.stdout.strip(), "stderr": analysis.stderr.strip()}
            if analysis.returncode:
                errors.append("mandatory-HUD retained analysis --check failed")
        if name == "inline_reconstruction":
            analysis = subprocess.run([sys.executable, "analyze.py", "--check"], cwd=directory,
                                      text=True, capture_output=True, timeout=120)
            verifier["analysis_replay"] = {"status": "pass" if analysis.returncode == 0 else "fail",
                                           "returncode": analysis.returncode,
                                           "stdout": analysis.stdout.strip(), "stderr": analysis.stderr.strip()}
            if analysis.returncode:
                errors.append("inline retained analysis --check failed")
    status = "pending" if name not in READY_STUDIES else ("verified" if not errors else "invalid")
    return {"status": status, "path": relative, "source_pin_count": len(pins),
            "source_pins": pins, "tests": tests, "verifier_replay": verifier,
            "errors": errors,
            "analysis": analysis_data if name == "inline_reconstruction" and data else None}


def audit_study(name: str, relative: str) -> dict:
    if name not in READY_STUDIES:
        return {"status": "pending", "path": relative,
                "reason": "awaiting explicit final readiness signal"}
    return study_result(name, relative)


def load_audit() -> dict:
    results = {name: audit_study(name, path) for name, path in STUDIES.items()}
    final = READY_STUDIES == set(STUDIES)
    statuses = {result["status"] for result in results.values()}
    status = "verified" if final and statuses == {"verified"} else (
        "invalid" if "invalid" in statuses else "pending")
    return {"audit": "python-game-v20-handoff-audit",
            "status": status,
            "final_signals_received": final,
            "results": results,
            "scope": [
                "Integer golden-vector proof is not fitted RTL or physical 30 fps evidence.",
                "Timed benchmarks are not replayed by this audit.",
                "Full mandatory HUD coverage and inline canonical-tag ordering are required gates.",
            ]}


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
    return 1 if json.loads(rendered)["status"] == "invalid" else 0


if __name__ == "__main__":
    raise SystemExit(main())
