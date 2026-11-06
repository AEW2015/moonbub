#!/usr/bin/env python3
"""Fail-closed audit of retained V79 monitored system and cohort evidence."""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_ROOT = ROOT / "fpga/experiments/cu66-v79/system"
CAMPAIGN_ROOT = ROOT / "fpga/experiments/cu66-v79/campaign"
PAIRED_PATH = ROOT / "fpga/experiments/cu66-v79/paired-comparison.json"
ANALYSIS_PATH = ROOT / "fpga/experiments/cu66-v79/analysis.json"
QUEUE_BUDGET_PATH = ROOT / "fpga/experiments/cu66-v79/queue-budget.json"
PREFETCH_PATH = ROOT / "fpga/experiments/cu66-v79/prefetch/results.json"
LAYOUT_PATH = ROOT / "fpga/experiments/cu66-v79/layout-study/results.json"
SYSTEM_SCHEMA = "cu79-continuous-monitor-system-v1"
SYSTEM_PASS = "PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY"
CAMPAIGN_SCHEMA = "cu79-history-campaign-v1"
EXPECTED_COHORTS = {0: 119, 1: 119, 2: 119, 3: 100}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc


def safe_file(relpath, label):
    require(isinstance(relpath, str) and not Path(relpath).is_absolute(),
            f"{label}: invalid repository path {relpath!r}")
    path = (ROOT / relpath).resolve()
    require(path.is_relative_to(ROOT.resolve()) and path.is_file(),
            f"{label}: missing/outside-repository file {relpath}")
    return path


def verify_sources(data, label):
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and pins, f"{label}: source_sha256 missing/empty")
    for relpath, expected in pins.items():
        require(re.fullmatch(r"[0-9a-f]{64}", str(expected)) is not None,
                f"{label}: malformed source hash: {relpath}")
        require(sha256(safe_file(relpath, label)) == expected,
                f"{label}: source hash mismatch: {relpath}")
    return len(pins)


def verify_commands(data, label):
    commands = data.get("commands")
    require(isinstance(commands, list) and commands, f"{label}: commands missing/empty")
    logs = {}
    for command in commands:
        require(isinstance(command, dict), f"{label}: malformed command record")
        log_rel = command.get("log")
        require(command.get("exit_code") == 0 and command.get("timed_out", False) is False,
                f"{label}: failed/timed-out command: {command}")
        log = safe_file(log_rel, label)
        require(re.fullmatch(r"[0-9a-f]{64}", str(command.get("sha256"))) is not None
                and sha256(log) == command["sha256"], f"{label}: log hash mismatch: {log_rel}")
        logs[log_rel] = log.read_text(encoding="utf-8", errors="replace")
    return len(commands), logs


def parse_fields(line):
    return {key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)}


def logged(logs, prefix):
    return [parse_fields(line) for body in logs.values() for line in body.splitlines()
            if line.startswith(prefix)]


def audit_system(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == SYSTEM_SCHEMA, f"{label}: schema mismatch")
    require(data.get("status") == SYSTEM_PASS, f"{label}: functional status is not PASS")
    cohort = data.get("cohort")
    count = data.get("requested_frames")
    require(cohort in EXPECTED_COHORTS and isinstance(count, int) and count > 0
            and count <= EXPECTED_COHORTS[cohort], f"{label}: invalid cohort/count")
    frames, timings, deadlines = data.get("frames"), data.get("timings"), data.get("raster_deadlines")
    summary, perf = data.get("summary"), data.get("performance")
    require(isinstance(frames, list) and isinstance(timings, list) and isinstance(deadlines, list)
            and isinstance(summary, dict) and isinstance(perf, dict), f"{label}: records missing")
    require(len(frames) == len(timings) == len(deadlines) == count,
            f"{label}: frame/timing/deadline counts differ from requested source count")
    require(summary.get("cohort") == cohort and summary.get("complete_frames") == count
            and summary.get("distinct_complete_presentations") == count,
            f"{label}: terminal count/cohort mismatch")
    require(summary.get("physical_fps_proven") == 0,
            f"{label}: simulator evidence must not claim physical frame rate")
    require(summary.get("canonical_bytes_per_frame") == 518400
            and summary.get("RGB_DDR_words_written_per_frame") == 0,
            f"{label}: canonical/RGB-write assertion mismatch")
    for key in ("black_lines", "total_underruns", "lcd_memory_errors", "sticky_lcd_error",
                "sticky_memory_error", "sticky_underrun"):
        require(summary.get(key) == 0, f"{label}: health/black-line failure: {key}")
    require(summary.get("raster_deadline_cycles") == 10_000_000
            and summary.get("global_watchdog_cycles", 0) > 0,
            f"{label}: missing bounded raster/global watchdog")
    ids = [f.get("fid") for f in frames]
    require(len(set(ids)) == count and set(ids) == {t.get("fid") for t in timings},
            f"{label}: duplicate or unmatched source frame IDs")
    require(len({f.get("generation") for f in frames}) == count,
            f"{label}: duplicate frame generation")
    clock = data.get("clocks")
    require(isinstance(clock, dict) and clock.get("memory_period_ps") == 10000,
            f"{label}: recorded memory clock missing or unexpected")
    for i, (frame, timing, deadline) in enumerate(zip(frames, timings, deadlines)):
        require(frame.get("fid") == timing.get("fid")
                and frame.get("generation") == timing.get("generation")
                and frame.get("generation") == deadline.get("generation")
                and frame.get("fid") == deadline.get("fid"),
                f"{label}: identity mismatch in row {i}")
        require(timing.get("complete_rasters", 0) > 0,
                f"{label}: no complete correct physical raster for source {i}")
        packet, admission = timing.get("packet_complete_cycle"), timing.get("admission_cycle")
        ready, ack = timing.get("validated_ready_cycle"), timing.get("commit_ack_cycle")
        presented = timing.get("descriptor_presented_cycle")
        require(all(isinstance(x, int) for x in (packet, admission, ready, ack, presented))
                and packet <= admission < ready <= ack,
                f"{label}: invalid packet/admission/validation/ACK order row={i}")
        require(timing.get("queue_cycles") == admission-packet
                and timing.get("validated_decode_model_cycles") == ready-packet
                and frame.get("origin_to_ack_cycles") == ack-packet,
                f"{label}: timing arithmetic mismatch row={i}")
        if data.get("arrival_mode") == "fixed30":
            inferred_release = ack-frame["origin_to_ack_cycles"]
            require(inferred_release == 108+i*100_000_000//30,
                    f"{label}: fixed30 modeled source release schedule mismatch row={i}")
        expected30 = int((ack-packet)*30 <= 100_000_000)
        expected10 = int((ready-packet)*10_000 < 10_000_000_000)
        require(timing.get("met_serial_30fps_budget") == expected30
                and timing.get("met_validated_under10ms") == expected10,
                f"{label}: modeled threshold arithmetic mismatch row={i}")
        require(deadline.get("commit_ack_cycle") == ack
                and deadline.get("due_cycle") == ack+10_000_000
                and deadline.get("bound_cycles") == 10_000_000
                and deadline.get("functional_liveness_only") == 1,
                f"{label}: raster deadline record arithmetic mismatch row={i}")
        end_ps = timing.get("first_complete_raster_end_ps")
        start_ps = timing.get("first_complete_raster_start_ps")
        require(isinstance(start_ps, int) and isinstance(end_ps, int)
                and end_ps > start_ps > 0 and end_ps <= (ack+10_000_000)*10_000,
                f"{label}: complete-raster timing misses ACK deadline row={i}")
        require(frame.get("actual_write_commands", 0)*8 == frame.get("actual_write_bus_beats")
                and frame.get("actual_writes") == frame.get("actual_write_bus_beats")
                and frame.get("underruns") == 0,
                f"{label}: SDRAM write or underrun arithmetic mismatch row={i}")
        base_bins = [frame.get(f"base{base}_tile{tile}_aux{aux}_cycles")
                     for base in range(2) for tile in range(2) for aux in range(2)]
        stage_bins = [frame.get(f"stage{stage}_cycles") for stage in range(16)]
        require(all(isinstance(value, int) and value >= 0 for value in base_bins + stage_bins),
                f"{label}: missing/invalid disjoint profile bins row={i}")
        require(sum(base_bins) == frame.get("cycles") and sum(stage_bins) == frame.get("cycles"),
                f"{label}: profile bins do not partition transaction cycles row={i}")
        require(sum(base_bins[4:]) == sum(stage_bins[5:6]),
                f"{label}: BASE_RUN and base1 occupancy cycle totals differ row={i}")
    require(perf.get("serial_30fps_all_pass") is all(t["met_serial_30fps_budget"] == 1 for t in timings)
            and perf.get("validated_under10ms_all_pass") is all(t["met_validated_under10ms"] == 1 for t in timings),
            f"{label}: performance aggregate mismatch")
    require(perf.get("status") == ("PASS" if perf["serial_30fps_all_pass"]
                                     and perf["validated_under10ms_all_pass"] else "FAIL"),
            f"{label}: performance status does not reflect model thresholds")
    for key, expected in (("validated_model_ms", [t["validated_decode_model_cycles"]*1e-5 for t in timings]),
                          ("origin_to_ack_model_ms", [(t["commit_ack_cycle"]-t["packet_complete_cycle"])*1e-5 for t in timings])):
        values = perf.get(key)
        require(isinstance(values, list) and len(values) == len(expected)
                and all(abs(a-b) < 1e-9 for a, b in zip(values, expected)),
                f"{label}: {key} arithmetic mismatch")
    source_count = verify_sources(data, label)
    command_count, logs = verify_commands(data, label)
    run_logs = [body for name, body in logs.items() if "run" in Path(name).name]
    require(run_logs, f"{label}: execution log missing")
    body = "\n".join(run_logs)
    terminals = re.findall(r"^SYSTEM_PASS (.+)$", body, re.M)
    require(len(terminals) == 1, f"{label}: missing/duplicate terminal SYSTEM_PASS")
    terminal = parse_fields(terminals[0])
    frame_rows = [parse_fields(line) for line in body.splitlines() if line.startswith("SYSTEM_FRAME_PASS ")]
    timing_rows = [parse_fields(line) for line in body.splitlines() if line.startswith("SYSTEM_TIMING ")]
    deadline_rows = [parse_fields(line) for line in body.splitlines() if line.startswith("SYSTEM_RASTER_DEADLINE ")]
    require(len(frame_rows) == len(timing_rows) == len(deadline_rows) == count,
            f"{label}: execution log record counts mismatch")
    for kind, rows, records in (("frame", frame_rows, frames), ("timing", timing_rows, timings),
                                ("deadline", deadline_rows, deadlines)):
        for i, (row, record) in enumerate(zip(rows, records)):
            for key, value in row.items():
                require(record.get(key) == value, f"{label}: logged {kind} {key} differs row={i}")
    for key, value in terminal.items():
        require(summary.get(key) == value, f"{label}: terminal summary {key} differs from JSON")
    return (f"{path.parent.name}: frames={count} source_pins={source_count} command_logs={command_count}; "
            f"functional=PASS; modeled thresholds serial30={sum(t['met_serial_30fps_budget'] for t in timings)}/{count}, "
            f"under10ms={sum(t['met_validated_under10ms'] for t in timings)}/{count}; physical_fps_proven=0")


def audit_campaign(path, systems):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == CAMPAIGN_SCHEMA, f"{label}: schema mismatch")
    require(data.get("status") == "PASS_ALL_REQUESTED_HISTORIES", f"{label}: campaign did not pass")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 4, f"{label}: expected four distinct histories")
    require(data.get("requested_sources") == sum(EXPECTED_COHORTS.values()),
            f"{label}: campaign source count mismatch")
    campaign_pins = verify_sources(data, label)
    seen = set()
    for case in cases:
        cohort = case.get("cohort")
        require(cohort in EXPECTED_COHORTS and cohort not in seen, f"{label}: duplicate/unknown cohort")
        seen.add(cohort)
        require(case.get("requested_sources") == EXPECTED_COHORTS[cohort]
                and case.get("exit_code") == 0 and case.get("error") is None,
                f"{label}: cohort execution failed or source count wrong")
        rel = case.get("log")
        log = safe_file(rel, label)
        require(sha256(log) == case.get("sha256"), f"{label}: cohort log hash mismatch {rel}")
        body = log.read_text(encoding="utf-8", errors="replace")
        require(len(re.findall(r"^V79_SYSTEM_PASS cohort=%d frames=%d mode=fixed30 performance=\w+ wall_seconds=[0-9.]+$" %
                               (cohort, EXPECTED_COHORTS[cohort]), body, re.M)) == 1,
                f"{label}: cohort {cohort} missing its unique terminal marker")
        matches = [s for s in systems if s.get("cohort") == cohort
                   and s.get("requested_frames") == EXPECTED_COHORTS[cohort]
                   and s.get("arrival_mode") == "fixed30"]
        require(len(matches) == 1, f"{label}: cohort {cohort} lacks unique audited system JSON")
    require(seen == set(EXPECTED_COHORTS), f"{label}: one or more cohort histories missing")
    return (f"campaign: four independent immutable cohorts, 457 unique sources, "
            f"source_pins={campaign_pins}; no 60/600-second qualification inferred")


def audit_monitor_unit(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == "cu79-observer-unit-v1" and data.get("status") == "PASS",
            f"{label}: observer unit schema/status mismatch")
    require(data.get("tests") == 9 and data.get("observer_unit_only") is True
            and data.get("hardware_fault_injection") is False,
            f"{label}: observer test scope/count mismatch")
    source_pins = verify_sources(data, label)
    command_count, logs = verify_commands(data, label)
    body = "\n".join(logs.values())
    cases = re.findall(r"^MONITOR_TEST_PASS case=\S+.*$", body, re.M)
    terminal = re.findall(r"^MONITOR_UNIT_PASS tests=9 observer_unit_only=1 hardware_fault_injection=0$",
                          body, re.M)
    require(len(cases) == 9 and len(terminal) == 1,
            f"{label}: observer case/terminal marker count mismatch")
    require(body.count("observer_unit_only=1") == 10
            and "hardware_fault_injection=0" in terminal[0],
            f"{label}: observer unit scope marker mismatch")
    return f"monitor observer unit: cases=9 source_pins={source_pins} command_logs={command_count}; no DUT fault injection"


def close(a, b):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) \
        and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)


def audit_paired_comparison(systems):
    data = read_json(PAIRED_PATH)
    label = str(PAIRED_PATH.relative_to(ROOT))
    require(data.get("schema") == "cu79-v78-paired-comparison-v1"
            and data.get("status") == "PASS_UNCHANGED_PAIRED_TRANSACTIONS",
            f"{label}: schema/status mismatch")
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and len(pins) == 3, f"{label}: expected three paired input pins")
    verify_sources(data, label)
    baseline_rel = "fpga/experiments/cu66-v78/system/frames4-fixed30-tac2/results.json"
    require(baseline_rel in pins, f"{label}: V78 paired baseline was not pinned")
    old = read_json(safe_file(baseline_rel, label))
    candidates = []
    for relpath in pins:
        if relpath.startswith("fpga/experiments/cu66-v79/system/") and relpath.endswith("/results.json"):
            result = read_json(safe_file(relpath, label))
            if result in systems:
                candidates.append(result)
    require(len(candidates) == 1, f"{label}: paired V79 system input is not uniquely audited")
    new = candidates[0]
    require(new.get("cohort") == 0 and new.get("arrival_mode") == old.get("arrival_mode")
            and new.get("tac_ns") == old.get("tac_ns"), f"{label}: pairing configuration mismatch")
    before_frames, after_frames = old.get("frames", []), new.get("frames", [])
    before_timings, after_timings = old.get("timings", []), new.get("timings", [])
    require(len(before_frames) == len(before_timings) and len(after_frames) == len(after_timings)
            and len(after_frames) >= len(before_frames), f"{label}: malformed paired frame counts")
    same_length = len(before_frames) == len(after_frames)
    exact = 0
    changed = []
    for before, after in zip(before_frames, after_frames):
        require(before.keys() <= after.keys(), f"{label}: missing paired frame fields")
        for key, value in before.items():
            require(after[key] == value, f"{label}: transaction field differs fid={before.get('fid')} key={key}")
            exact += 1
    observation_fields = {"native_hud_prepare_wall_ns", "last_correct_pixel_ps", "complete_rasters"}
    for before, after in zip(before_timings, after_timings):
        require(before.keys() <= after.keys(), f"{label}: missing paired timing fields")
        for key, value in before.items():
            if key in observation_fields and (not same_length or key == "native_hud_prepare_wall_ns"):
                if value != after[key]:
                    changed.append(dict(generation=before.get("generation"), field=key,
                                        baseline=value, monitored=after[key]))
            else:
                require(after[key] == value,
                        f"{label}: first-presentation milestone differs fid={before.get('fid')} key={key}")
                exact += 1
    if same_length:
        for key, value in old.get("summary", {}).items():
            require(new.get("summary", {}).get(key) == value,
                    f"{label}: paired terminal summary differs key={key}")
            exact += 1
    require(data.get("sources") == len(before_frames) and data.get("exact_fields") == exact
            and data.get("comparison_mode") == ("complete-paired-run" if same_length else "paired-prefix")
            and data.get("observation_differences") == changed,
            f"{label}: stored paired comparison arithmetic/observations mismatch")
    return f"paired V78/V79: sources={len(before_frames)} exact_fields={exact}; original fields and first presentation preserved"


def stats(values):
    values = sorted(values)
    require(values, "analysis: cannot compute empty statistics")
    return {"min": min(values), "median": __import__("statistics").median(values), "max": max(values)}


def same_value(actual, expected, label):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and actual.keys() == expected.keys(),
                f"{label}: statistic field set differs")
        for key, value in expected.items():
            same_value(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (int, float)):
        require(close(actual, expected), f"{label}: derived value mismatch expected={expected} actual={actual}")
    else:
        require(actual == expected, f"{label}: derived value mismatch")


def audit_analysis(systems):
    data = read_json(ANALYSIS_PATH)
    label = str(ANALYSIS_PATH.relative_to(ROOT))
    require(data.get("schema") == "cu79-finite-history-analysis-v1", f"{label}: schema mismatch")
    pins = data.get("source_sha256")
    require(isinstance(pins, dict), f"{label}: source pins missing")
    verify_sources(data, label)
    candidates = {}
    for relpath in pins:
        result = read_json(safe_file(relpath, label))
        candidates[relpath] = result
    system_paths = {str(path.relative_to(ROOT)) for path in systems}
    require(set(candidates) == system_paths,
            f"{label}: analysis inputs differ from audited system result set")
    expected_runs, expected_failures = [], []
    all_validated, all_delta = [], []
    for relpath, source in sorted(candidates.items()):
        if source.get("status") != SYSTEM_PASS:
            expected_failures.append(dict(path=relpath, failure=source.get("failure")))
            continue
        ts, frames, summary = source["timings"], source["frames"], source["summary"]
        n = len(ts)
        validated = [t["validated_decode_model_cycles"]*1e-5 for t in ts]
        delta = [v for f, v in zip(frames, validated) if not f["key"]]
        transaction_service = [f["cycles"]*1e-5 for f in frames]
        admission_to_validated = [(t["validated_ready_cycle"]-t["admission_cycle"])*1e-5 for t in ts]
        ingress_to_ack = [(t["commit_ack_cycle"]-t["packet_complete_cycle"])*1e-5 for t in ts]
        starts = [t["first_complete_raster_start_ps"] for t in ts]
        ingress = [(t["first_complete_raster_end_ps"]-t["packet_complete_cycle"]*10000)/1e9 for t in ts]
        stage5 = [f["stage5_cycles"]/f["cycles"] for f in frames]
        tile_busy = [(f["base1_tile1_aux0_cycles"]+f["base1_tile1_aux1_cycles"])/f["cycles"] for f in frames]
        row = dict(run=Path(relpath).parent.name, cohort=source["cohort"], sources=n,
            functional="PASS", validated_ms=stats(validated), delta_validated_ms=stats(delta),
            transaction_service_ms=stats(transaction_service),
            admission_to_validated_ms=stats(admission_to_validated),
            ingress_to_commit_ack_ms=stats(ingress_to_ack),
            ingress_to_first_full_raster_end_ms=stats(ingress),
            first_full_raster_start_gap_ms=stats([(b-a)/1e9 for a, b in zip(starts, starts[1:])]),
            finite_first_to_last_source_cadence_fps=(n-1)*1e12/(starts[-1]-starts[0]),
            serial_ack_33ms_passes=sum(t["met_serial_30fps_budget"] for t in ts),
            strict_validated_under10ms_passes=sum(t["met_validated_under10ms"] for t in ts),
            max_release_to_admission_ms=max(t["queue_cycles"] for t in ts)*1e-5,
            max_waiting=summary["max_waiting_released_unadmitted"],
            max_in_service=summary["max_in_service"],
            max_total_released_unacked=summary["max_total_released_unacked"],
            base_run_fraction=stats(stage5), base_run_tile_busy_fraction=stats(tile_busy),
            native_pixels_checked=summary["observed_pixels"], wall_seconds=source["wall_seconds"])
        expected_runs.append(row)
        if n == source["cohort_available_frames"]:
            all_validated.extend(validated)
            all_delta.extend(delta)
    full = [row for row in expected_runs if row["sources"] in (119, 100)]
    same_value(data.get("runs"), expected_runs, f"{label}.runs")
    same_value(data.get("failures"), expected_failures, f"{label}.failures")
    same_value(data.get("full_history_sources"), sum(row["sources"] for row in full), f"{label}.full_history_sources")
    same_value(data.get("full_history_validated_ms"), stats(all_validated) if all_validated else None,
               f"{label}.full_history_validated_ms")
    same_value(data.get("full_history_delta_validated_ms"), stats(all_delta) if all_delta else None,
               f"{label}.full_history_delta_validated_ms")
    return f"derived analysis: runs={len(expected_runs)} failed_runs={len(expected_failures)}; statistics recomputed from pinned source JSON"


def queue_charge(frames):
    events = []
    for frame in frames:
        ident, size = frame["generation"], frame["bytes"]
        require(0 < size <= 49152 and frame["release"] <= frame["admission"] < frame["ack"],
                "queue budget: invalid packet size or release/admission/ACK ordering")
        events.extend(((frame["release"], 0, ident, size),
                       (frame["admission"], 1, ident, size),
                       (frame["ack"], 2, ident, size)))
    waiting, active = {}, {}
    peak_waiting_bytes = peak_owned_bytes = peak_waiting = peak_owned = 0
    for _, kind, ident, size in sorted(events):
        if kind == 0:
            require(ident not in waiting and ident not in active, "queue budget: duplicate release")
            waiting[ident] = size
        elif kind == 1:
            require(waiting.pop(ident, None) == size and ident not in active,
                    "queue budget: admission without uniquely waiting packet")
            active[ident] = size
            require(len(active) <= 1, "queue budget: receiver admits multiple active packets")
        else:
            require(active.pop(ident, None) == size, "queue budget: ACK without active packet")
        waiting_bytes = sum(waiting.values())
        owned_bytes = waiting_bytes+sum(active.values())
        peak_waiting_bytes = max(peak_waiting_bytes, waiting_bytes)
        peak_owned_bytes = max(peak_owned_bytes, owned_bytes)
        peak_waiting = max(peak_waiting, len(waiting))
        peak_owned = max(peak_owned, len(waiting)+len(active))
    require(not waiting and not active, "queue budget: packet ownership not empty at campaign end")
    return dict(max_waiting_packets=peak_waiting, max_waiting_bytes=peak_waiting_bytes,
                max_owned_packets_including_active=peak_owned,
                max_owned_bytes_including_active=peak_owned_bytes,
                fixed_48KiB_slot_pool_bytes=peak_owned*49152,
                budget_bytes_required_without_drops=peak_owned_bytes,
                illustrative_budget_pass={str(size): peak_owned_bytes <= size
                                          for size in (49152, 65536, 131072, 262144)},
                illustrative_fixed_slot_budget_pass={str(size): peak_owned*49152 <= size
                                                      for size in (49152, 65536, 131072, 262144)})


def audit_queue_budget(systems):
    data = read_json(QUEUE_BUDGET_PATH)
    label = str(QUEUE_BUDGET_PATH.relative_to(ROOT))
    require(data.get("schema") == "cu79-immutable-packet-queue-budget-v1"
            and data.get("control_tests") == 1, f"{label}: schema/control mismatch")
    index_rel = "experiments/cu66-native-v69/index.tsv"
    script_rel = "scripts/cu66-v79/queue_budget.py"
    expected_pins = {index_rel, script_rel}
    index_path = safe_file(index_rel, label)
    pools = {}
    for line in index_path.read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        require(len(fields) >= 3, f"{label}: malformed fixture index row")
        cohort, ordinal, relpacket = int(fields[0]), int(fields[1]), fields[2]
        pool = pools.setdefault(cohort, [])
        require(ordinal == len(pool), f"{label}: fixture chronology mismatch cohort={cohort}")
        pool.append(relpacket)
    expected_runs = []
    for path in systems:
        relrun = str(path.relative_to(ROOT))
        expected_pins.add(relrun)
        source = read_json(path)
        if source.get("status") != SYSTEM_PASS:
            expected_runs.append(dict(run=path.parent.name, status="FAIL_SOURCE_CAMPAIGN",
                                      failure=source.get("failure")))
            continue
        cohort = source["cohort"]
        timings = source["timings"]
        packets = pools[cohort][:len(timings)]
        require(len(packets) == len(timings), f"{label}: fixture/timing count mismatch")
        charged = []
        for timing, relpacket in zip(timings, packets):
            packet_rel = f"experiments/cu66-native-v69/{relpacket}"
            packet_path = safe_file(packet_rel, label)
            expected_pins.add(packet_rel)
            charged.append(dict(generation=timing["generation"], bytes=packet_path.stat().st_size,
                                release=timing["packet_complete_cycle"],
                                admission=timing["admission_cycle"], ack=timing["commit_ack_cycle"]))
        result = queue_charge(charged)
        summary = source["summary"]
        require(result["max_waiting_packets"] == summary["max_waiting_released_unadmitted"]
                and result["max_owned_packets_including_active"] == summary["max_total_released_unacked"],
                f"{label}: event-model queue packet counts mismatch {path.parent.name}")
        expected_runs.append(dict(run=path.parent.name, status="PASS_ENDPOINT_QUEUE_ACCOUNTING",
                                  cohort=cohort, sources=len(charged),
                                  packet_bytes_min=min(f["bytes"] for f in charged),
                                  packet_bytes_max=max(f["bytes"] for f in charged), **result))
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and set(pins) == expected_pins,
            f"{label}: source pin set differs from fixture/system inputs")
    verify_sources(data, label)
    same_value(data.get("runs"), expected_runs, f"{label}.runs")
    require(isinstance(data.get("contract"), list) and any("illustrative endpoint reservations" in c for c in data["contract"])
            and any("fixed48KiB slot-pool reservations are reported separately" in c for c in data["contract"])
            and any("No live transport" in c for c in data["contract"]),
            f"{label}: endpoint budget limitations missing")
    return f"queue budget: runs={len(expected_runs)} fixture-byte event replayed through ACK; endpoint reservation model only"


def audit_prefetch():
    data = read_json(PREFETCH_PATH)
    label = str(PREFETCH_PATH.relative_to(ROOT))
    require(data.get("schema") == "cu79-reference-prefetch-prototype-v1"
            and data.get("status") == "PASS_STANDALONE_LOGIC_SIMPLE_BACKEND"
            and isinstance(data.get("attempt"), int) and data["attempt"] >= 5,
            f"{label}: schema/status/final attempt mismatch")
    summary = data.get("summary")
    require(isinstance(summary, dict), f"{label}: summary missing")
    exact_summary = {"cases": 9, "full_replay_tiles": 8100, "hidden_replay_tiles": 8100,
                     "read_commands": 32400, "read_beats": 259200, "logical_reference_bytes": 128,
                     "physical_sdram_model": 0, "system_integration": 0, "speedup_proven": 0}
    require(summary == exact_summary, f"{label}: scope or count summary mismatch")
    resources = data.get("resources")
    require(resources == {"reference_slots": 2, "reference_payload_bits": 1024,
                          "logical_reference_bytes": 128, "slot_identity_control_bits": 184,
                          "candidate_staging_bytes": 0, "physical_read_outstanding_limit": 1},
            f"{label}: resource accounting mismatch")
    source_pins = data.get("source_sha256")
    require(isinstance(source_pins, dict) and len(source_pins) == 4,
            f"{label}: expected module/bench/runner/map source pins")
    verify_sources(data, label)
    attempt_root = PREFETCH_PATH.parent / f"attempt{data['attempt']}"
    archive = read_json(attempt_root / "results.json")
    require(archive == data, f"{label}: final attempt archive differs from published result")
    for relpath, expected in source_pins.items():
        archived = safe_file(str((attempt_root / "source" / relpath).relative_to(ROOT)), label)
        require(sha256(archived) == expected, f"{label}: attempt source snapshot hash mismatch: {relpath}")
    command_count, logs = verify_commands(data, label)
    expected_logs = {f"fpga/experiments/cu66-v79/prefetch/attempt{data['attempt']}/{name}.log"
                     for name in ("version", "build", "binary", "run")}
    require(set(logs) == expected_logs and command_count == 4,
            f"{label}: final attempt command log set mismatch")
    body = logs[f"fpga/experiments/cu66-v79/prefetch/attempt{data['attempt']}/run.log"]
    terminals = re.findall(r"^PREFETCH_PASS (.+)$", body, re.M)
    cases = [line for line in body.splitlines() if line.startswith("PREFETCH_CASE_PASS ")]
    require(len(terminals) == 1 and len(cases) == 9 and data.get("cases") == cases,
            f"{label}: final attempt case/terminal log mismatch")
    logged_summary = parse_fields(terminals[0])
    require(logged_summary == summary, f"{label}: final terminal summary differs from JSON")
    expected_case_names = {"full_replay", "hidden_full_replay", "identity_retirement_held_response",
                           "hidden_early_retire", "abort_all_accepted_offsets",
                           "abort_unaccepted_and_held_response", "memory_faults_lease_reset",
                           "monotonic_epoch", "atomic_fault_edge"}
    names = [re.search(r"case=(\S+)", line).group(1) for line in cases]
    require(set(names) == expected_case_names and len(set(names)) == 9,
            f"{label}: prototype directed case set mismatch")
    case_values = {name: parse_fields(line) for name, line in zip(names, cases)}
    exact_cases = {
        "full_replay": {"tiles": 8100, "read_commands": 32400, "read_beats": 259200,
                        "visible": 8100, "unused": 0, "max_slots": 2,
                        "seed": 2041262477, "simple_backend": 1, "physical_sdram_model": 0},
        "hidden_full_replay": {"tiles": 8100, "unused": 8100, "read_commands": 32400,
                               "read_beats": 259200, "all_plane_first_last_hidden": 1,
                               "seed": 2031236182},
        "identity_retirement_held_response": {"concurrent_lookup_unused": 1,
                                                "wrong_identity_fields": 4,
                                                "stale_retire": 1, "early_retire": 1},
        "abort_all_accepted_offsets": {"offsets": 8, "coincident_beat_offsets": 8,
                                        "missing_beat_hold": 1},
        "abort_unaccepted_and_held_response": {},
        "memory_faults_lease_reset": {"faults": 4, "joint_backend_reset": 1,
                                       "malformed_last_drain_actual8": 1},
        "monotonic_epoch": {"duplicate_stale_rejected": 2, "fresh_recovery": 1},
        "atomic_fault_edge": {"no_new_request_lookup_retire": 1, "held_response_cancelled": 1},
    }
    for name, expected in exact_cases.items():
        actual = case_values[name]
        require(all(actual.get(key) == value for key, value in expected.items()),
                f"{label}: directed case numeric evidence mismatch: {name}")
    require(0 < case_values["full_replay"].get("cycles", 0) < 5_000_000
            and case_values["hidden_early_retire"].get("backpressured_cycles", 0) > 0,
            f"{label}: replay/backpressure cycle observations missing or outside bounds")
    binary_log = logs[f"fpga/experiments/cu66-v79/prefetch/attempt{data['attempt']}/binary.log"]
    digests = re.findall(r"\b([0-9a-f]{64})\b", binary_log)
    require(digests == [data.get("binary_sha256")], f"{label}: binary digest log mismatch")
    limitations = data.get("limitations", [])
    require(any("no actual SDRAM model/controller" in item for item in limitations)
            and any("No latency reduction" in item for item in limitations),
            f"{label}: standalone prototype limitations missing")
    return f"prefetch prototype: attempt={data['attempt']} cases=9 source_pins={len(source_pins)}; standalone simple backend only"


def audit_layout_study():
    data = read_json(LAYOUT_PATH)
    label = str(LAYOUT_PATH.relative_to(ROOT))
    require(data.get("schema") == "cu79-grouped-layout-study-v1"
            and data.get("status") == "PASS_MAPPING_UNCALIBRATED_SERVICE_ONLY",
            f"{label}: schema/status mismatch")
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and len(pins) == 7, f"{label}: expected seven input pins")
    verify_sources(data, label)
    index = safe_file("experiments/cu66-native-v69/index.tsv", label)
    first = index.read_text(encoding="utf-8").splitlines()[0].split("\t")
    require(len(first) >= 4, f"{label}: first YUV fixture reference malformed")
    golden_rel = f"experiments/cu66-native-v69/fixtures/{first[3]}.yuv"
    require(golden_rel in pins and pins[golden_rel] == first[3],
            f"{label}: actual YUV fixture hash is not pinned to content identity")
    mappings = data.get("mappings")
    expected_layouts = [("current_unpadded", None, None), ("group_16x1", 16, 1),
                        ("group_8x2", 8, 2), ("group_4x4", 4, 4),
                        ("group_2x8", 2, 8), ("group_1x16", 1, 16)]
    require(isinstance(mappings, list) and len(mappings) == 6,
            f"{label}: expected six grouped-layout mappings")
    dims = ((90, 60), (45, 30), (45, 30))
    by_name = {mapping.get("layout"): mapping for mapping in mappings}
    require(set(by_name) == {row[0] for row in expected_layouts}, f"{label}: mapping set mismatch")
    restored_hashes = set()
    for name, group_w, group_h in expected_layouts:
        mapping = by_name[name]
        spans = []
        for width, height in dims:
            if group_w is None:
                spans.append(width*height*32)
            else:
                spans.append(((width+group_w-1)//group_w)*((height+group_h-1)//group_h)*512)
        offsets, expected_offset = [], 0
        for span in spans:
            offsets.append(expected_offset)
            expected_offset += span
        require(mapping.get("group_width") == group_w and mapping.get("group_height") == group_h
                and mapping.get("plane_offsets_x16") == offsets
                and mapping.get("plane_spans_x16") == spans,
                f"{label}: mapping geometry mismatch {name}")
        active_bytes, allocated = 518400, sum(spans)*2
        require(mapping.get("allocated_bytes") == allocated
                and mapping.get("active_bytes") == active_bytes
                and mapping.get("padding_bytes") == allocated-active_bytes
                and mapping.get("active_tiles") == 8100
                and mapping.get("padding_tiles") == (allocated-active_bytes)//64,
                f"{label}: mapping byte/tile conservation mismatch {name}")
        require(mapping.get("tests") == "PASS_INJECTIVE_TILES_ALL_WORDS_BYTE_ORDER_PADDING_BANK_AND_HUD_BOUNDS",
                f"{label}: mapping test coverage marker mismatch {name}")
        restored_hashes.add(mapping.get("restored_sha256"))
    require(restored_hashes == {first[3]}, f"{label}: mappings do not all restore the exact retained YUV fixture")
    measures = data.get("measurements")
    require(isinstance(measures, list) and len(measures) == 96,
            f"{label}: expected 96 synthetic mapping/service scenarios")
    streams_expected = {"standalone_display": 35040, "standalone_reference": 31224,
                        "standalone_canonical_write": 32400, "standalone_hud_write": 2640,
                        "standalone_hud_verify": 2640, "fixed_round_robin_all_streams": 103944}
    seen = set()
    for row in measures:
        layout, stream, quantum, refresh = (row.get("layout"), row.get("stream"),
                                              row.get("quantum"), row.get("refresh_period"))
        key = (layout, stream, quantum, refresh)
        require(layout in by_name and stream in streams_expected and refresh in (0, 750)
                and key not in seen, f"{label}: unknown/duplicate service scenario {key}")
        seen.add(key)
        expected_count = streams_expected[stream]
        if stream.startswith("standalone_"):
            require(quantum == expected_count, f"{label}: standalone request quantum mismatch {key}")
        else:
            require(quantum in (4, 8, 16), f"{label}: round-robin quantum mismatch {key}")
        require(row.get("commands") == expected_count and row.get("wire_bytes") == expected_count*16,
                f"{label}: logical wire byte conservation mismatch {key}")
        require(row.get("ACT", -1) >= 0 and row.get("PRE_conflict", -1) >= 0
                and row.get("REF", -1) >= 0 and row.get("row_hits", -1) >= 0
                and row["ACT"]+row["row_hits"] == row["commands"]
                and row["PRE_conflict"] <= row["ACT"]
                and row.get("service_work_cycles", 0) > 0,
                f"{label}: synthetic row-work counters inconsistent {key}")
        require(row.get("REF") == 0 if refresh == 0 else row.get("REF") > 0,
                f"{label}: refresh sensitivity counter mismatch {key}")
        require(row.get("calibration") == "UNCALIBRATED_SYNTHETIC_SERVICE_WORK_NOT_LATENCY",
                f"{label}: service work incorrectly calibrated as latency {key}")
    require(len(seen) == 96, f"{label}: incomplete mapping/service matrix")
    contract = data.get("contract", [])
    require(any("No LCD deadlines" in item for item in contract)
            and any("No hardware gain" in item and "strictunder10ms" in item for item in contract),
            f"{label}: synthetic-only scope limitations missing")
    return "grouped layout study: six mappings and 96 service scenarios; exact fixture restoration, uncalibrated only"


def main():
    reports = []
    monitor_path = SYSTEM_ROOT / "monitor-tests/results.json"
    if monitor_path.is_file():
        reports.append(audit_monitor_unit(monitor_path))
    systems = sorted(SYSTEM_ROOT.glob("cohort*-frames*-*-tac*/results.json"))
    require(systems, "system: no retained V79 results.json")
    reports.extend(audit_system(path) for path in systems)
    campaign_path = CAMPAIGN_ROOT / "results.json"
    if campaign_path.is_file():
        reports.append(audit_campaign(campaign_path, [read_json(path) for path in systems]))
    if PAIRED_PATH.is_file():
        reports.append(audit_paired_comparison([read_json(path) for path in systems]))
    if ANALYSIS_PATH.is_file():
        reports.append(audit_analysis(systems))
    if QUEUE_BUDGET_PATH.is_file():
        reports.append(audit_queue_budget(systems))
    if PREFETCH_PATH.is_file():
        reports.append(audit_prefetch())
    if LAYOUT_PATH.is_file():
        reports.append(audit_layout_study())
    print("V79_EVIDENCE_AUDIT_PASS")
    print("Functional evidence, modeled performance thresholds, and physical qualification remain separate.")
    print("No physical 30 fps, 60/600-second stream, CPU HUD cost, or target timing claim is inferred.")
    for report in reports:
        print(f"- {report}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"V79_EVIDENCE_AUDIT_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
