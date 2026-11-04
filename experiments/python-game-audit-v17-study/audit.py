#!/usr/bin/env python3
"""Read-only v17 evidence audit. Inputs remain pending until final signal."""
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
    "paced_gateway": "experiments/python-game-paced-gateway-study",
    "streaming_memory": "experiments/python-game-streaming-memory-study",
    "local_refresh": "experiments/python-game-local-refresh-study",
}
# Set entries only after the parent gives the explicit final-studies-ready signal.
READY_STUDIES: set[str] = {"paced_gateway", "streaming_memory", "local_refresh"}
TARGET = {"canvas": [720, 480], "active_image": [720, 405], "fps": 30}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def replay(directory: Path, command: list[str]) -> dict:
    try:
        run = subprocess.run([sys.executable, *command], cwd=directory, text=True, capture_output=True, timeout=120)
        return {"status": "pass" if run.returncode == 0 else "fail", "returncode": run.returncode,
                "stdout": run.stdout.strip(), "stderr": run.stderr.strip()}
    except Exception as exc:
        return {"status": "fail", "error": f"{type(exc).__name__}: {exc}"}


def audit_paced_gateway(data: dict, directory: Path) -> dict:
    errors = []
    summary = data.get("summary", [])
    cases = data.get("cases", [])
    bounded = bool(cases) and all(
        c["result"].get("peak_packet_credits", 999) <= 6
        and c["result"].get("peak_receiver_mailbox", 999) <= 6
        and c["result"].get("counters", {}).get("mailbox_full", 0) == 0
        and c["result"].get("counters", {}).get("control_mailbox_full", 0) == 0
        for c in cases
    )
    nominal = next((x for x in summary if x.get("workload") == "gm_initial_only" and x.get("profile") == "paced"), {})
    agg8 = next((x for x in summary if x.get("workload") == "gm_initial_only" and x.get("profile") == "aggregate8"), {})
    feedback_blackhole = next((c["result"] for c in cases if c.get("profile") == "feedback_blackhole"), {})
    stress = next((x for x in summary if x.get("workload") == "cap_stress60" and x.get("profile") == "paced"), {})
    framing = data.get("prospective_framing", {})
    if data.get("case_count") != 36 or len(cases) != 36: errors.append("gateway case count is not 36")
    if len(data.get("source_sha256", {})) != 14: errors.append("gateway source pin count is not 14")
    if not bounded: errors.append("gateway mailbox/credit bounds or zero-overflow invariant failed")
    if (nominal.get("admitted"), nominal.get("strict"), nominal.get("eventual"), nominal.get("source_frames")) != (176, 175, 176, 177): errors.append("nominal paced gateway summary mismatch")
    if (agg8.get("admitted"), agg8.get("strict"), agg8.get("eventual"), sum(agg8.get("drops", {}).values())) != (142, 141, 142, 35): errors.append("aggregate8 admission/drop summary mismatch")
    if feedback_blackhole.get("eventual_complete") != 0 or feedback_blackhole.get("all_admitted_packets_issued") is not False or sum(x is not None for x in feedback_blackhole.get("outstanding_credit_slots", [])) != 6: errors.append("blackhole did not retain unresolved credits and stop safely")
    if framing.get("max_udp_datagram_bytes") != 1064 or framing.get("esp_dma_allocation_bytes") != 1065: errors.append("prospective framing/DMA size mismatch")
    stress_mbps = stress.get("data_bytes", 0) / stress.get("admitted", 1) * 8 * 30 / 1_000_000 if stress else None
    if stress and (stress.get("admitted"), stress.get("strict"), stress.get("eventual"), sum(stress.get("drops", {}).values())) != (35, 35, 35, 25): errors.append("maximum-body stress admission/drop summary mismatch")
    if stress_mbps is None or abs(stress_mbps-12.78432) > 1e-6: errors.append("maximum-body stress bandwidth mismatch")
    replayed = replay(directory, ["verify.py"])
    if replayed["status"] != "pass": errors.append("gateway deterministic verifier failed")
    limitations = " ".join(data.get("limitations", []))
    no_qual = all(not c["result"].get("physical_30fps_proven", True) and not c["result"].get("current_firmware_supports_credit_protocol", True) for c in cases)
    no_decode_claim = "not decoder-valid" in limitations and "cannot establish30distinctdisplayedFPS" in limitations
    if not no_decode_claim: errors.append("opaque body-size/presentation limitation is not explicit")
    if not no_qual: errors.append("gateway model promoted to current firmware/physical FPS")
    return {"status": "verified" if not errors else "invalid", "case_count": len(cases), "source_pin_count": len(data.get("source_sha256", {})),
            "bounded_mailbox_zero_overflow": bounded, "nominal_paced": nominal, "aggregate8": agg8,
            "blackhole_retains_six_credits": bool(feedback_blackhole) and sum(x is not None for x in feedback_blackhole.get("outstanding_credit_slots", [])) == 6,
            "stress_paced": stress, "stress_required_mbps_at_30hz": stress_mbps, "framing": framing,
            "opaque_size_only_not_decoder_valid": no_decode_claim, "physical_or_firmware_claims_false": no_qual,
            "deterministic_replay": replayed, "errors": errors}


def audit_local_refresh(data: dict, directory: Path) -> dict:
    errors = []
    cases = data.get("cases", [])
    by_profile = {c.get("profile"): c for c in cases}
    native = [c for c in cases if c.get("source") == "native-regression180"]
    cad_path = directory / "cadence-analysis.json"
    try: cadence = json.loads(cad_path.read_text())
    except (OSError, json.JSONDecodeError): cadence = {}
    profiles = {x.get("profile"): x for x in cadence.get("profiles", [])}
    globalsum = profiles.get("global_refresh30", {})
    localsum = profiles.get("local_refresh30", {})
    repeat = profiles.get("local_refresh30_repeat", {})
    keys = localsum.get("key_ids", [])
    bank1 = localsum.get("key0_pending_bank1_continuity", [])
    ui_exact = bool(native) and all(all(x.get("selected_exact_pixels") == 21120 and x.get("selected_ui_mismatches") == 0 for x in c["result"].get("commits", [])) for c in native)
    if len(cases) != 6 or data.get("case_count") != 6: errors.append("local refresh case count is not six")
    if len(native) != 4 or any(c["manifest"].get("unique_frame_count") != 180 for c in native): errors.append("native regression manifest/count mismatch")
    if sum(c["result"].get("capture_count", 0) for c in cases) != 848: errors.append("local refresh capture count mismatch")
    if len(data.get("source_sha256", {})) != 37: errors.append("local refresh source pin count is not 37")
    if not ui_exact: errors.append("native UI exact-word coverage mismatch")
    if (globalsum.get("strict"), globalsum.get("eventual"), globalsum.get("distinct_input_and_decoded_window_ids")) != (159, 161, 133): errors.append("global refresh strict/eventual/window counts mismatch")
    if (localsum.get("strict"), localsum.get("eventual"), localsum.get("distinct_input_and_decoded_window_ids"), localsum.get("diagnostic_ids_per_second")) != (176, 178, 151, 30.2): errors.append("local refresh strict/eventual/diagnostic counts mismatch")
    if (repeat.get("strict"), repeat.get("eventual"), repeat.get("distinct_input_and_decoded_window_ids")) != (176, 178, 151): errors.append("local repeat summary mismatch")
    if abs(localsum.get("maximum_in_window_gap_ms", 0)-66.6666666667) > 1e-6: errors.append("local maximum presentation gap mismatch")
    if any(abs(a-b)>1e-6 for a,b in ((globalsum.get("maximum_in_window_gap_ms",0),116.6666666667),(localsum.get("maximum_presented_age_ms",0),116.6666666667),(globalsum.get("maximum_presented_age_ms",0),133.3333333333))): errors.append("gap/age evidence mismatch")
    if keys != [0, 30, 60, 90, 120, 150] or len(bank1) != 5 or any(len(x.get("bank1_P_ids", [])) != 2 for x in bank1): errors.append("bank-1 continuity during local key ownership mismatch")
    if cadence.get("local_repeat_same_packet_hashes_and_presented_ids") is not True or cadence.get("local_repeat_same_presented_times") is not False: errors.append("repeat-equivalence/timing distinction mismatch")
    if cadence.get("input_schedule_fps") != 30 or "not>30capture" not in cadence.get("scope", ""): errors.append("diagnostic cadence scope missing")
    if cadence.get("source_quality_delta_on_common_ids") is None or abs(cadence.get("source_quality_delta_on_common_ids") - (-0.01392)) > 0.00002: errors.append("matched-ID quality delta mismatch")
    replayed = replay(directory, ["verify.py"])
    analyzed = replay(directory, ["analyze.py", "--check"])
    if replayed["status"] != "pass": errors.append("local refresh deterministic verifier failed")
    if analyzed["status"] != "pass": errors.append("local refresh bound untimed analysis failed")
    return {"status": "verified" if not errors else "invalid", "case_count": len(cases), "capture_count": sum(c["result"].get("capture_count", 0) for c in cases),
            "source_pin_count": len(data.get("source_sha256", {})), "all_native_ui_words_exact": ui_exact,
            "global": globalsum, "local": localsum, "repeat": repeat, "local_bank1_continuity": bank1,
            "analysis_bound_to_results_and_analyzer": {"results_sha256": cadence.get("results_sha256"), "analyzer_sha256": cadence.get("analyzer_sha256")},
            "deterministic_replay": replayed, "analysis_replay": analyzed,
            "firmware_protocol_scope": "AR03/AF03 v3 experiment; current firmware remains MSV1 JPEG-only",
            "limits": "30.2/5s is phase/catch-up under 30 scheduled IDs/s; timing gaps remain; no physical or native hardware FPS proof",
            "errors": errors}


def audit_streaming_memory(data: dict, directory: Path) -> dict:
    errors = []
    cases = {x.get("name"): x.get("result", {}) for x in data.get("cases", [])}
    phases = data.get("phase_cases", [])
    boundary_path = directory / "epoch-boundaries.json"
    try: boundaries = json.loads(boundary_path.read_text())
    except (OSError, json.JSONDecodeError): boundaries = {}
    bmap = {(x.get("group"), x.get("name")): x.get("result", {}) for x in boundaries.get("rows", [])}
    expected_names = {"nominal_baseline", "nominal_streaming", "fast_baseline", "fast_streaming", "fast_streaming_one_line", "fast_streaming_stall_4lines", "fast_streaming_stall_8lines", "current_2MiB_window"}
    if len(cases) != 8 or set(cases) != expected_names or len(phases) != 4: errors.append("streaming memory case inventory mismatch")
    if len(data.get("source_sha256", {})) != 28: errors.append("streaming memory source pin count is not 28")
    template_scope = any("notvalidAR02packet/referenceidentityreplay" in x for x in data.get("limits", [])) and len(data.get("input_traces", [])) == 3
    if not template_scope: errors.append("streaming memory repeated-template / no-valid-reference-history limit missing")
    expected = {
        "nominal_baseline": (0, 12.0, 12), "nominal_streaming": (0, 20.0, 21),
        "fast_baseline": (0, 26.0, 27), "fast_streaming": (0, 30.0, 30),
        "fast_streaming_one_line": (0, 30.0, 30), "fast_streaming_stall_4lines": (3689, 0.0, 0),
        "fast_streaming_stall_8lines": (0, 30.0, 30),
    }
    for name, (misses, rate, eventual) in expected.items():
        r = cases.get(name, {})
        actual = (r.get("display_line_misses"), r.get("clean_steady_ids_per_second"), r.get("clean_eventual_unique_ids"))
        if actual != (misses, rate, eventual): errors.append(f"streaming memory outcome mismatch: {name}")
        if r and (r.get("decoder_drained") is not True or r.get("live_scanout_reader_requests") != 0 or r.get("live_scanout_fifo_slots") != 0): errors.append(f"streaming memory drain/scanout ownership mismatch: {name}")
    rejected = cases.get("current_2MiB_window", {})
    if rejected.get("status") != "address_window_rejected": errors.append("2 MiB window was not rejected")
    fast = bmap.get(("cases", "fast_streaming"), {})
    strict_start = fast.get("strict_logical_epoch_start_ids", [])
    strict_finish = fast.get("strict_completed_clean_panel_epoch_ids", [])
    eventual = fast.get("complete_clean_epoch_ids", [])
    if len(strict_start) != 29 or len(strict_finish) != 29 or len(eventual) != 30: errors.append("fast streaming strict epoch boundary counts mismatch")
    if len(strict_start) != len(strict_finish) or strict_start != strict_finish: errors.append("early epoch starts incorrectly promoted before clean finish")
    phase_rows = [bmap.get(("phase_cases", x.get("name")), {}) for x in phases]
    if [len(x.get("complete_clean_epoch_ids", [])) for x in phase_rows] != [6, 6, 6, 6]: errors.append("phase clean epoch counts mismatch")
    if boundaries.get("results_sha256") != sha256(directory / "results.json") or boundaries.get("analyzer_sha256") != sha256(directory / "analyze.py"):
        errors.append("epoch boundary analysis is not bound to retained result/analyzer hashes")
    verified = replay(directory, ["verify.py"])
    analyzed = replay(directory, ["analyze.py", "--check"])
    if verified["status"] != "pass": errors.append("streaming memory deterministic verifier failed")
    if analyzed["status"] != "pass": errors.append("streaming memory boundary analysis failed")
    return {"status": "verified" if not errors else "invalid", "case_count": len(cases), "phase_case_count": len(phases),
            "source_pin_count": len(data.get("source_sha256", {})), "main_scenario_summaries": {
                name: {k: cases.get(name, {}).get(k) for k in ("display_line_misses", "strict_presentations", "eventual_presentations", "steady_ids_per_second", "clean_steady_ids_per_second", "clean_eventual_unique_ids", "traffic_bytes", "peak_bounds")}
                for name in sorted(expected_names - {"current_2MiB_window"})},
            "fast_streaming_epoch_boundaries": {"strict_start_count": len(strict_start), "strict_clean_finish_count": len(strict_finish), "eventual_clean_count": len(eventual), "start_ids_equal_clean_finish_ids": strict_start == strict_finish},
            "phase_clean_epoch_counts": [len(x.get("complete_clean_epoch_ids", [])) for x in phase_rows],
            "2MiB_window_rejected": rejected.get("status") == "address_window_rejected",
            "three_native_templates_not_valid_AR02_replay": template_scope,
            "untimed_analysis_hash_binding": {"results_sha256": boundaries.get("results_sha256"), "analyzer_sha256": boundaries.get("analyzer_sha256")},
            "deterministic_replay": verified, "boundary_analysis_replay": analyzed,
            "scope": "Three repeated native coefficient templates do not represent 30 distinct decoded pictures or valid AR03 history; clean scanout and physical memory/FPGA timing remain modeled only.",
            "errors": errors}


def audit_study(key: str, rel_dir: str) -> dict:
    directory = ROOT / rel_dir
    result = {"status": "pending", "path": rel_dir, "artifacts": {}, "source_pins": [], "errors": []}
    if key not in READY_STUDIES:
        result["errors"].append("awaiting explicit final evidence signal")
        return result
    if not directory.is_dir():
        result["errors"].append("study directory missing")
        result["status"] = "invalid"
        return result
    artifact_names = ["README.md", "SCHEMA.md", "results.json", "tests.log", "verify.log", "analysis-verify.log"]
    if key == "streaming_memory": artifact_names.append("epoch-boundaries.json")
    if key == "local_refresh": artifact_names.append("cadence-analysis.json")
    for name in artifact_names:
        path = directory / name
        result["artifacts"][name] = {"present": path.is_file(), "sha256": sha256(path) if path.is_file() else None}
    result["test_log"] = test_log(directory / "tests.log")
    result_path = directory / "results.json"
    if not result_path.is_file():
        result["errors"].append("results.json missing")
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
    pins = data.get("source_sha256", {}) if isinstance(data, dict) else {}
    for raw, expected in sorted(pins.items()):
        path = resolve_pin(raw)
        actual = sha256(path) if path.is_file() else None
        entry = {"path": portable(path), "expected": expected, "actual": actual, "matches": actual == expected}
        result["source_pins"].append(entry)
        if not entry["matches"]:
            result["errors"].append(f"source hash pin missing or mismatched: {entry['path']}")
    result["result_summary"] = {k: data.get(k) for k in ("study", "evidence", "case_count", "frame_count", "event_count", "status") if isinstance(data, dict) and k in data}
    if key == "paced_gateway": result["analysis"] = audit_paced_gateway(data, directory)
    if key == "local_refresh": result["analysis"] = audit_local_refresh(data, directory)
    if key == "streaming_memory": result["analysis"] = audit_streaming_memory(data, directory)
    if result.get("analysis", {}).get("status") == "invalid": result["errors"].extend(result["analysis"].get("errors", []))
    if result["test_log"]["status"] != "pass":
        result["errors"].append("study test log missing or not a passing unittest log")
    result["status"] = "verified" if not result["errors"] else "invalid"
    return result


def load_audit() -> dict:
    results = {key: audit_study(key, path) for key, path in STUDIES.items()}
    status = "verified" if all(item["status"] == "verified" for item in results.values()) else (
        "invalid" if any(item["status"] == "invalid" for item in results.values()) else "pending"
    )
    return {
        "audit": "python-game-v17-evidence-audit",
        "target": TARGET,
        "status": status,
        "final_signal_received": bool(READY_STUDIES) and READY_STUDIES == set(STUDIES),
        "results": results,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="recompute and compare without writing audit.json")
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
