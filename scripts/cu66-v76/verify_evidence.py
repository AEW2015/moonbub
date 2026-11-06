#!/usr/bin/env python3
"""Read-only integrity, functional-data, and honest performance audit for V76."""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v76"
FAIL = []
REPORT = []


def fail(msg):
    FAIL.append(msg)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(rel):
    path = ROOT / rel
    if not path.is_file():
        fail(f"required evidence missing: {rel}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid JSON {rel}: {exc}")
        return None


def safe(rel):
    p = Path(rel)
    return not p.is_absolute() and ".." not in p.parts


def pins(data, label, field="source_sha256"):
    values = data.get(field)
    if not isinstance(values, dict) or not values:
        fail(f"{label}: {field} missing or empty")
        return
    for name, digest in values.items():
        if not safe(name):
            fail(f"{label}: unsafe {field} path: {name}")
            continue
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{label}: source hash mismatch: {name}")


def commands(data, label, runtime_marker=None):
    cmds = data.get("commands")
    if not isinstance(cmds, list) or not cmds:
        fail(f"{label}: commands missing or empty")
        return
    for i, cmd in enumerate(cmds):
        if not isinstance(cmd, dict) or cmd.get("exit_code") != 0:
            fail(f"{label}: command {i} did not complete successfully")
            continue
        name = cmd.get("log")
        if not isinstance(name, str) or not safe(name):
            fail(f"{label}: command {i} has unsafe/missing log path")
            continue
        path = ROOT / name
        if not path.is_file() or sha(path) != cmd.get("sha256"):
            fail(f"{label}: command log hash mismatch: {name}")
            continue
        content = path.read_text(errors="replace")
        if re.search(r"(^|\s)(FAIL|FATAL)(\s|:|$)", content, re.M):
            fail(f"{label}: failure marker in {name}")
        if runtime_marker and Path(name).name.startswith("run-"):
            if runtime_marker not in content:
                fail(f"{label}: runtime completion marker missing in {name}")
            if runtime_marker == "SERVICE_PASS" and content.count("SERVICE_STRIP ") != 90:
                fail(f"{label}: expected 90 actual strip records in {name}")
            if runtime_marker == "SYSTEM_PASS" and (content.count("SYSTEM_FRAME_PASS ") != 2 or
                    content.count("SYSTEM_TIMING ") != 2):
                fail(f"{label}: incomplete frame/timing runtime records in {name}")


def archive_audit(manifest_rel, archive_rel, expected_count):
    manifest = read(manifest_rel)
    if manifest is None:
        return
    archive = ROOT / archive_rel
    if not archive.is_file() or sha(archive) != manifest.get("archive_sha256"):
        fail(f"{manifest_rel}: archive missing or SHA mismatch")
        return
    try:
        with zipfile.ZipFile(archive) as zf:
            members = {name: hashlib.sha256(zf.read(name)).hexdigest() for name in zf.namelist()}
        if members != manifest.get("files_sha256") or len(members) != expected_count:
            fail(f"{manifest_rel}: archive member inventory/hash mismatch")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        fail(f"{manifest_rel}: archive cannot be read: {exc}")
    if "superseded" not in manifest.get("scope", "").lower():
        fail(f"{manifest_rel}: archived evidence is not labeled superseded")


def baseline():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v76/verify_baseline.py")],
                          cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode:
        fail("frozen V69-V75 baseline verifier failed: " +
             (proc.stdout + proc.stderr).strip().replace("\n", " | "))
    else:
        REPORT.append(proc.stdout.strip())


def phase_audit():
    archive_audit("fpga/experiments/cu66-v76/phases/first-proof/manifest.json",
                  "fpga/experiments/cu66-v76/phases/first-proof/source-and-evidence.zip", 6)
    rel = "fpga/experiments/cu66-v76/phases/results.json"
    d = read(rel)
    if d is None:
        return
    if (d.get("schema"), d.get("status"), d.get("campaign_complete")) != (
            "cu76-phase-replay-v1", "PASS_FUNCTIONAL_EXACT_FRAMEBUFFERS_AND_PHASES", True):
        fail(f"{rel}: phase campaign is incomplete or has unexpected functional status")
    pins(d, rel)
    commands(d, rel, "SYSTEM_PASS")
    offsets = {0, 384171, 768342, 1152513}
    runs = d.get("runs", [])
    expected = {(mode, offset) for mode in ("scalar", "burst") for offset in offsets}
    actual = {(r.get("hud_mode"), r.get("offset_cycles")) for r in runs}
    if len(runs) != 8 or actual != expected:
        fail(f"{rel}: expected one scalar and burst run at each of four phase offsets")
    if d.get("clocks", {}).get("memory_period_ps") != 10000:
        fail(f"{rel}: command-model clock must be explicitly 100 MHz")
    budgets = d.get("budgets", {})
    if (budgets.get("transaction30fps_max_cycles"),
            budgets.get("validated_sub10ms_strict_max_exclusive_cycles")) != (3333333, 1000000):
        fail(f"{rel}: timing budgets differ from documented thresholds")
    functional_ok = True
    budget_outcomes = []
    for run in runs:
        mode = run.get("hud_mode")
        frames, times, summary = run.get("frames", []), run.get("timings", []), run.get("summary", {})
        if len(frames) != 2 or len(times) != 2:
            fail(f"{rel}: {mode}/{run.get('offset_cycles')} lacks two frame/timing records")
            functional_ok = False
            continue
        if {f.get("fid") for f in frames} != {0, 1} or len({f.get("generation") for f in frames}) != 2:
            fail(f"{rel}: frame records do not identify two distinct source IDs/generations")
            functional_ok = False
        if (summary.get("complete_frames"), summary.get("distinct_complete_presentations"),
                summary.get("black_lines"), summary.get("total_underruns"),
                summary.get("physical_fps_proven")) != (2, 2, 0, 0, 0):
            fail(f"{rel}: {mode}/{run.get('offset_cycles')} presentation summary mismatch")
            functional_ok = False
        expected_commands, expected_beats, expected_hud = (
            (83040, 664320, 2640) if mode == "burst" else (101520, 812160, 21120))
        for frame, timing in zip(frames, times):
            if (frame.get("fid"), frame.get("generation")) != (
                    timing.get("fid"), timing.get("generation")):
                fail(f"{rel}: frame/timing identity mismatch")
                functional_ok = False
            if (frame.get("actual_writes"), frame.get("actual_write_commands"),
                    frame.get("actual_write_bus_beats"), frame.get("hud_burst"),
                    frame.get("hud_write_requests"), frame.get("hud_read_requests"),
                    frame.get("painter_read_commands"), frame.get("painter_read_words"),
                    frame.get("painter_write_commands"), frame.get("painter_write_words")) != (
                    664320, expected_commands, expected_beats, int(mode == "burst"),
                    expected_hud, expected_hud, 35040, 280320, 48000, 384000):
                fail(f"{rel}: native memory or HUD accounting mismatch")
                functional_ok = False
        t = times[1]
        off = run.get("offset_cycles")
        if (t.get("fid"), t.get("generation"), t.get("planned_admission_cycle"),
                t.get("admission_cycle"), t.get("packet_complete_cycle", -2) + 1,
                t.get("admission_front_id"), t.get("admission_front_generation")) != (
                1, 2, 20000000 + off, 20000000 + off, 20000000 + off, 0, 1) or \
                t.get("warm_complete_rasters", 0) < 1:
            fail(f"{rel}: fixed-arrival phase/warm-frame identity mismatch")
            functional_ok = False
        order = (t.get("packet_complete_cycle", 0) < t.get("admission_cycle", 0) <
                 t.get("validated_ready_cycle", 0) < t.get("rgb_ready_cycle", 0) <=
                 t.get("commit_ack_cycle", 0))
        validated = t.get("validated_ready_cycle", 0) - t.get("packet_complete_cycle", 0)
        transaction = t.get("commit_ack_cycle", 0) - t.get("packet_complete_cycle", 0)
        if not order or t.get("validated_decode_model_cycles") != validated or \
                t.get("transaction_model_cycles") != transaction:
            fail(f"{rel}: ordered timestamps or derived timing intervals mismatch")
            functional_ok = False
        fps_pass = transaction <= 3333333
        decode_pass = validated < 1000000
        if t.get("met_30fps_transaction_deadline") != int(fps_pass) or \
                t.get("met_sub10ms_validated_deadline") != int(decode_pass):
            fail(f"{rel}: stored budget flags do not match measured cycles")
        budget_outcomes.append((fps_pass, decode_pass))
    declared_failed = any(not a or not b for a, b in budget_outcomes)
    expect_status = "FAIL_30FPS_OR_SUB10MS_BUDGETS" if declared_failed else "PASS_MODELED_BUDGETS_ONLY"
    if d.get("performance_status") != expect_status:
        fail(f"{rel}: performance_status does not match measured 30-fps/10-ms outcomes")
    limits = "".join(d.get("limitations", [])).lower().replace(" ", "")
    if "nophysical30fps" not in limits or "targetsub10ms" not in limits:
        fail(f"{rel}: physical 30 fps limitation missing")
    if functional_ok:
        fps_count = sum(a for a, _ in budget_outcomes)
        decode_count = sum(b for _, b in budget_outcomes)
        REPORT.append(f"{rel}: 8 phase cases functionally audited; 33.333 ms serial transaction PASS={fps_count}/8; strict <10 ms ingress-to-validated PASS={decode_count}/8; performance={d.get('performance_status')}")


def service_audit():
    archive_audit("fpga/experiments/cu66-v76/service/initial-gap-display/manifest.json",
                  "fpga/experiments/cu66-v76/service/initial-gap-display/source-and-evidence.zip", 16)
    archive_audit("fpga/experiments/cu66-v76/service/before-deterministic-cycle/manifest.json",
                  "fpga/experiments/cu66-v76/service/before-deterministic-cycle/source-and-evidence.zip", 31)
    archive_audit("fpga/experiments/cu66-v76/service/before-log-path-separation/manifest.json",
                  "fpga/experiments/cu66-v76/service/before-log-path-separation/source-and-evidence.zip", 38)
    superseded = read("fpga/experiments/cu66-v76/service/crosscheck-initial-metric-difference.json")
    superseded_scope = superseded.get("scope", "").lower().replace(" ", "") if superseded else ""
    if superseded and ("superseded" not in superseded_scope or "racefixed" not in superseded_scope):
        fail("initial cycle-instrumentation comparison is not labeled as superseded")
    rel = "fpga/experiments/cu66-v76/service/results.json"
    d = read(rel)
    if d is None:
        return
    if d.get("schema") != "v76-direct-service-results-v1" or \
            d.get("status") != "PASS_FUNCTIONAL_SERVICE_REPLAY" or d.get("quick") is not False:
        fail(f"{rel}: full multi-condition service replay is not finalized")
    pins(d, rel)
    commands(d, rel, "SERVICE_PASS")
    trace = read("fpga/experiments/cu66-v76/service/trace.json")
    if trace is not None:
        trace_mem = ROOT / "fpga/experiments/cu66-v76/service/trace.mem"
        if (trace.get("schema") != "v76-direct-service-trace-v1" or
                (trace.get("total_bursts"), trace.get("YUV_bursts"),
                 trace.get("HUD_bursts"), trace.get("wire_bytes")) != (35040, 32400, 2640, 560640) or
                not trace_mem.is_file() or sha(trace_mem) != trace.get("trace_sha256")):
            fail(f"{rel}: synthetic direct-service trace inventory or binary hash mismatch")
        if d.get("source_sha256", {}).get("fpga/experiments/cu66-v76/service/trace.json") != sha(
                ROOT / "fpga/experiments/cu66-v76/service/trace.json"):
            fail(f"{rel}: service result is not bound to the retained trace description")
    if d.get("deadline_ps") != 147403024 or d.get("clocks", {}).get("memory_period_ps") != 10000:
        fail(f"{rel}: 147.403024 us deadline or assumed 100 MHz period mismatch")
    if d.get("cache_assumption", {}).get("RTL_implemented") is not False:
        fail(f"{rel}: unimplemented software-cache assumption must remain explicit")
    runs = d.get("runs", [])
    expected = {(tac, route, bg, 0) for tac in (2, 7) for route in (0, 1) for bg in (0, 1, 2)}
    expected |= {(2, 0, 0, 1), (2, 1, 0, 1)}
    actual = {(r.get("tac_ns"), r.get("route"), r.get("background"), r.get("issue_gap"))
              for r in runs}
    if len(runs) != 14 or actual != expected:
        fail(f"{rel}: expected both T_AC settings, routes, three backgrounds, and gap controls")
    all_functional = True
    outcomes = []
    for i, run in enumerate(runs):
        strips = run.get("strips_detail", [])
        if (run.get("strips"), run.get("bursts"), run.get("compared_words"), len(strips)) != (
                90, 35040, 280320, 90):
            fail(f"{rel}: service run {i} strip/burst/word inventory mismatch")
            all_functional = False
        if sum(s.get("bursts", 0) for s in strips) != 35040 or \
                sum(s.get("late_cycles", 0) > 0 for s in strips) != run.get("deadline_misses"):
            fail(f"{rel}: service run {i} strip accounting/deadline count mismatch")
            all_functional = False
        misses = 0
        lateness = []
        max_service = 0
        min_service = None
        origin = strips[0].get("release_cycle", 0) if strips else 0
        for strip_index, s in enumerate(strips):
            service = s.get("end_cycle", 0) - s.get("start_cycle", 0)
            if s.get("service_cycles") != service or s.get("end_cycle", 0) < s.get("start_cycle", 0):
                fail(f"{rel}: service run {i} has invalid strip interval")
                all_functional = False
            expected_release = origin + strip_index * 147403024 // 10000
            expected_deadline = origin + (strip_index + 1) * 147403024 // 10000
            if s.get("release_cycle") != expected_release or s.get("deadline_cycle") != expected_deadline:
                fail(f"{rel}: service run {i} release/deadline schedule differs from absolute 8-row periods")
            late = max(0, s.get("end_cycle", 0) - s.get("deadline_cycle", 0))
            if s.get("late_cycles") != late:
                fail(f"{rel}: service run {i} strip lateness does not match actual response/deadline cycles")
            if late:
                misses += 1
            lateness.append(late)
            max_service = max(max_service, service)
            min_service = service if min_service is None else min(min_service, service)
        if (misses != run.get("deadline_misses") or max_service != run.get("max_service_cycles") or
                min_service != run.get("min_service_cycles") or max(lateness, default=0) != run.get("max_lateness_cycles")):
            fail(f"{rel}: service run {i} aggregate latency/miss fields mismatch strip records")
        if run.get("reference_bank") != 0 or run.get("reads", 0) < 35040 or \
                run.get("cache_hits") != 0 or \
                (run.get("route") == 0 and run.get("cache_misses") != run.get("reads")) or \
                run.get("writes") != run.get("drained_w", -1) * 32 or \
                run.get("write_commands") != run.get("drained_w", -1) * 4 or \
                run.get("write_bus_beats") != run.get("writes") or \
                run.get("drained_w") != run.get("released_w") or \
                run.get("drained_r") != run.get("released_r"):
            fail(f"{rel}: service run {i} memory/background accounting mismatch")
        expected_gap = 2 if run.get("issue_gap") == 1 else 1
        if run.get("background") == 0 and (run.get("min_drain_to_accept"),
                run.get("max_drain_to_accept")) != (expected_gap, expected_gap):
            fail(f"{rel}: service run {i} drain-to-next-accept gap mismatch")
        deadline_pass = all(s.get("end_cycle", 0) <= s.get("deadline_cycle", 0) for s in strips)
        if run.get("deadline_status") != ("PASS" if deadline_pass else "FAIL"):
            fail(f"{rel}: service run {i} deadline verdict mismatch")
        outcomes.append(deadline_pass)
    if all_functional:
        REPORT.append(f"{rel}: 14 controller-model conditions; 147.403024 us strip deadlines PASS={sum(outcomes)} FAIL={len(outcomes)-sum(outcomes)} (functional and timing verdicts separate)")


def lookahead_audit():
    rel = "fpga/experiments/cu66-v76/service/lookahead-results.json"
    d = read(rel)
    if d is None:
        return
    if (d.get("schema"), d.get("status"), d.get("deadline_ps"), d.get("lookahead_strips")) != (
            "v76-service-lookahead-v1", "PASS_FUNCTIONAL_SCHEDULE_REPLAY", 147403024, 1):
        fail(f"{rel}: lookahead schema/status/threshold mismatch")
    pins(d, rel)
    commands(d, rel, "SERVICE_PASS")
    expected = {(2, 1, 1, 0), (2, 0, 1, 0), (7, 1, 1, 0)}
    runs = d.get("runs", [])
    actual = {(r.get("tac_ns"), r.get("route"), r.get("background"), r.get("issue_gap")) for r in runs}
    if len(runs) != 3 or actual != expected:
        fail(f"{rel}: expected the three declared one-strip lookahead schedule cases")
    outcomes = []
    for i, run in enumerate(runs):
        strips = run.get("strips_detail", [])
        if (run.get("lookahead_strips"), run.get("strips"), run.get("bursts"),
                run.get("compared_words"), len(strips)) != (1, 90, 35040, 280320, 90):
            fail(f"{rel}: lookahead run {i} functional service inventory mismatch")
        if sum(s.get("bursts", 0) for s in strips) != 35040 or \
                sum(s.get("late_cycles", 0) > 0 for s in strips) != run.get("deadline_misses"):
            fail(f"{rel}: lookahead run {i} strip/deadline accounting mismatch")
        expected_deadlines = 0
        expected_misses = 0
        lateness = []
        services = []
        for s in strips:
            start = strips[0].get("release_cycle", 0)
            strip = s.get("strip", -1)
            release = start + max(0, strip - 1) * 147403024 // 10000
            deadline = start + (strip + 1) * 147403024 // 10000
            if s.get("release_cycle") != release or s.get("deadline_cycle") != deadline:
                fail(f"{rel}: lookahead run {i} uses an altered or irregular strip deadline")
            service = s.get("end_cycle", 0) - s.get("start_cycle", 0)
            late = max(0, s.get("end_cycle", 0) - deadline)
            if s.get("service_cycles") != service or s.get("late_cycles") != late:
                fail(f"{rel}: lookahead run {i} measured interval/lateness mismatch")
            services.append(service)
            lateness.append(late)
            if late:
                expected_misses += 1
            expected_deadlines += 1
        if (expected_misses != run.get("deadline_misses") or
                max(services, default=0) != run.get("max_service_cycles") or
                min(services, default=0) != run.get("min_service_cycles") or
                max(lateness, default=0) != run.get("max_lateness_cycles")):
            fail(f"{rel}: lookahead run {i} deadline verdict mismatches strip intervals")
        verdict = "PASS" if expected_misses == 0 else "FAIL"
        if run.get("deadline_status") != verdict:
            fail(f"{rel}: lookahead run {i} deadline_status mismatch")
        outcomes.append(verdict)
    if d.get("additional_cache_requirement", "").find("no cacheRTL") < 0:
        fail(f"{rel}: cache/ownership requirement and missing RTL scope not stated")
    if len(outcomes) == 3:
        REPORT.append(f"{rel}: separate lookahead schedule, deadline PASS={outcomes.count('PASS')} FAIL={outcomes.count('FAIL')}; not folded into base 14 runs")


def simulator_crosscheck_audit():
    rel = "fpga/experiments/cu66-v76/service/crosscheck-results.json"
    d = read(rel)
    if d is None:
        return
    if d.get("status") != "PASS_CROSS_SIMULATOR_SERVICE" or \
            d.get("all_summary_counters_identical") is not True:
        fail(f"{rel}: cross-simulator evidence status/counter equality mismatch")
    pins(d, rel)
    commands(d, rel)
    row = d.get("iverilog", {})
    base_rel = "fpga/experiments/cu66-v76/service/results.json"
    base = read(base_rel)
    if base is None:
        return
    reference_log = ROOT / "fpga/experiments/cu66-v76/service/run-tac2-route1-bg1-gap0.log"
    reference_hash = d.get("verilator_reference_sha256")
    if not reference_log.is_file() or reference_hash != sha(reference_log):
        fail(f"{rel}: Verilator reference runtime log hash mismatch")
    ref = next((r for r in base.get("runs", []) if
                (r.get("tac_ns"), r.get("route"), r.get("background"), r.get("issue_gap")) ==
                (2, 1, 1, 0)), None)
    if ref is None:
        fail(f"{rel}: matching Verilator base run unavailable")
    else:
        keys = ("route", "background", "reference_bank", "issue_gap", "min_drain_to_accept",
                "max_drain_to_accept", "first_accept_cycle", "strips", "bursts", "compared_words",
                "measured_cycles", "min_service_cycles", "max_service_cycles", "deadline_misses",
                "max_lateness_cycles", "released_w", "released_r", "complete_w_at_end",
                "complete_r_at_end", "drained_w", "drained_r", "background_read_words", "late_bg_w",
                "late_bg_r", "reads", "writes", "write_commands", "write_bus_beats", "ACT", "PRE",
                "REF", "cache_hits", "cache_misses", "p0_read_wait", "p0_read_service")
        if any(row.get(k) != ref.get(k) for k in keys):
            fail(f"{rel}: Icarus counters disagree with matching Verilator run")
    if (row.get("strips"), row.get("bursts"), row.get("compared_words"),
            row.get("deadline_misses")) != (90, 35040, 280320, 1):
        fail(f"{rel}: cross-simulator service inventory or retained deadline failure mismatch")
    for cmd in d.get("commands", []):
        name = cmd.get("log", "")
        if Path(name).name == "iverilog-paced-lcd.log":
            path = ROOT / name
            log = path.read_text(errors="replace") if path.is_file() else ""
            if log.count("SERVICE_STRIP ") != 90 or "SERVICE_PASS " not in log:
                fail(f"{rel}: Icarus runtime log lacks 90 exact strip comparisons")
    REPORT.append(f"{rel}: Icarus and Verilator LCD-paced summary counters match; the single 147.403 us miss is retained")


def structured_audit():
    rel = "fpga/experiments/cu66-v76/structured/results.json"
    d = read(rel)
    if d is None:
        return
    if (d.get("schema"), d.get("status")) != (
            "cu76-structured-cache-v1", "PASS_PYTHON_CACHE_AND_RENDER_MODEL"):
        fail(f"{rel}: Python cache/render model status mismatch")
    pins(d, rel)
    inputs = d.get("input_sha256", {})
    expected_inputs = {"fpga/experiments/cu66-v76/service/trace.json",
                       "fpga/experiments/cu66-v76/service/trace.mem"}
    if set(inputs) != expected_inputs:
        fail(f"{rel}: structured model input inventory mismatch")
    for name, digest in inputs.items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: structured model input hash mismatch: {name}")
    models = d.get("models", [])
    expected_models = [(0, 1, 2, 14592), (1, 2, 3, 19968), (2, 3, 4, 29184)]
    actual_models = [(m.get("lookahead_strips"), m.get("Y_column_slots"),
                      m.get("HUD_block_columns_per_rectangle"), m.get("cache_data_bytes"))
                     for m in models]
    if len(models) != 3 or actual_models != expected_models:
        fail(f"{rel}: baseline/lookahead column-bank cache capacities mismatch")
    expected_chroma_slots = [2, 2, 3]
    for model, chroma_slots in zip(models, expected_chroma_slots):
        if (model.get("chroma_column_slots_per_plane"), model.get("RGB_words_checked"),
                model.get("cache_sample_checks"), model.get("bursts"),
                model.get("per_strip_miss_sets_equal_independent_LRU_trace")) != (
                chroma_slots, 345600, 1921920, 35040, True):
            fail(f"{rel}: structured model output, sample, or independent miss-set comparison mismatch")
    negative = d.get("negative_probe", {})
    if (negative.get("status"), negative.get("expected_live_column_hazard")) != (
            "EXPECTED_HAZARD_DETECTED", ["HUD", 0, 2, 0, 0, 2]):
        fail(f"{rel}: one-ahead/two-HUD-slot negative alias probe was not detected")
    contract = d.get("early_schedule_contract", {})
    if (contract.get("service_release"), contract.get("cache_ready_deadline_and_consumer_start"),
            contract.get("initial_preroll_periods"), contract.get("max_live_strips"),
            contract.get("requires_model_lookahead_strips"), contract.get("required_data_bytes")) != (
            "strip i at max(0,i-1)*P", "strip i at (i+1)*P", 1, 3, 2, 29184):
        fail(f"{rel}: early-release/consumer timeline and minimum modeled data capacity mismatch")
    under = d.get("underbudget_probes", [])
    expected_under = {("three-live strips with Y slots2", ("YUV", 0, 0, 0, 0, 2)),
                      ("three-live strips with chroma slots2", ("YUV", 1, 4, 0, 0, 2)),
                      ("three-live strips with HUD slots3", ("HUD", 0, 2, 0, 0, 3))}
    actual_under = {(p.get("configuration"), tuple(p.get("expected_live_column_hazard", [])))
                    for p in under if p.get("status") == "EXPECTED_HAZARD_DETECTED"}
    if len(under) != 3 or actual_under != expected_under:
        fail(f"{rel}: three-live-strip underbudget hazard probes incomplete")
    limits = " ".join(d.get("limitations", [])).lower()
    if "not rtl" not in limits or "no target30fps" not in limits:
        fail(f"{rel}: Python-only/no-target qualification limitation missing")
    REPORT.append(f"{rel}: mathematical RGB and miss-set checks audited; Python model only, 3-live-strip 29,184-byte capacity modeled and smaller configurations flagged")


def milestone_audit():
    rel = "fpga/experiments/cu66-v76/service/milestone-budget.json"
    # The producer currently places the derived report at the experiment root.
    rel = "fpga/experiments/cu66-v76/milestone-budget.json"
    d = read(rel)
    if d is None:
        return
    if (d.get("schema"), d.get("status")) != (
            "cu76-milestone-budget-v1", "PASS_DERIVED_BUDGET_ACCOUNTING"):
        fail(f"{rel}: derived milestone schema/status mismatch")
    pins(d, rel)
    inputs = d.get("input_sha256", {})
    if set(inputs) != {"fpga/experiments/cu66-v76/phases/results.json",
                       "fpga/experiments/cu66-v76/service/trace.json"}:
        fail(f"{rel}: milestone input inventory mismatch")
    for name, digest in inputs.items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: input hash mismatch: {name}")
    q = d.get("qualification", {})
    if (q.get("target_source_fps"), q.get("modeled_fixed_arrival_frames"),
            q.get("modeled_fixed_arrival_seconds"), q.get("physical_frames"),
            q.get("physical_seconds"), q.get("validated_max_exclusive_ns"),
            q.get("observed_cases"), q.get("physical30fps_proven"),
            q.get("target_under10ms_proven")) != (30, 1800, 60, 18000, 600, 10000000, 8, False, False):
        fail(f"{rel}: qualification frame counts, time windows, or proof flags mismatch")
    if len(d.get("rows", [])) != 8:
        fail(f"{rel}: expected eight derived phase budget rows")
    for r in d.get("rows", []):
        if r.get("serial_30fps_service_budget_pass") != (
                r.get("transaction_model_ms", 1e99) * 30 <= 1000):
            fail(f"{rel}: serial 30-fps verdict does not follow modeled transaction duration")
        if r.get("validated_under10ms_pass") != (r.get("validated_model_ms", 1e99) < 10):
            fail(f"{rel}: strict sub-10ms verdict does not follow validated interval")
        if r.get("optimistic_overlap_serial_stage_budget_pass") != (
                r.get("optimistic_decode_compose_overlap_period_model_ms", 1e99) * 30 <= 1000):
            fail(f"{rel}: optimistic overlap verdict does not match stage maximum")
    payload = d.get("payload_only_budget", {})
    notes = " ".join(payload.get("notes", [])).lower()
    if "no measured" not in notes or not any("excludes packet" in n.lower() for n in payload.get("notes", [])):
        fail(f"{rel}: raw payload-only arithmetic limitations missing")
    REPORT.append(f"{rel}: eight modeled budget verdicts audited; 1,800/60 s modeled and 18,000/600 s physical campaigns remain unproven")


def main():
    baseline()
    phase_audit()
    service_audit()
    lookahead_audit()
    simulator_crosscheck_audit()
    structured_audit()
    milestone_audit()
    if FAIL:
        print("V76_EVIDENCE_FAIL")
        print("\n".join(" - " + msg for msg in FAIL))
        raise SystemExit(1)
    print("V76_EVIDENCE_INTEGRITY_AND_SCOPE_PASS")
    print("\n".join(REPORT))


if __name__ == "__main__":
    main()
