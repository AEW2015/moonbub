#!/usr/bin/env python3
"""Fail-closed integrity and arithmetic audit for retained V78 evidence."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_ROOT = ROOT / "fpga/experiments/cu66-v78/system"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc


def verify_sources(data, label):
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and pins, f"{label}: source_sha256 is missing/empty")
    for relpath, expected in pins.items():
        require(isinstance(relpath, str) and not Path(relpath).is_absolute(),
                f"{label}: invalid source path {relpath!r}")
        path = (ROOT / relpath).resolve()
        require(path.is_relative_to(ROOT.resolve()), f"{label}: source escapes repository: {relpath}")
        require(path.is_file(), f"{label}: pinned source is missing: {relpath}")
        require(re.fullmatch(r"[0-9a-f]{64}", str(expected)) is not None,
                f"{label}: malformed source hash for {relpath}")
        require(sha256(path) == expected, f"{label}: source hash mismatch: {relpath}")
    return len(pins)


def verify_commands(data, label, terminal_pattern):
    commands = data.get("commands")
    require(isinstance(commands, list) and commands, f"{label}: commands missing")
    run_logs = []
    for command in commands:
        log_rel = command.get("log")
        require(command.get("exit_code") == 0, f"{label}: command failed: {command}")
        require(isinstance(log_rel, str), f"{label}: command log path missing")
        log = (ROOT / log_rel).resolve()
        require(log.is_relative_to(ROOT.resolve()) and log.is_file(),
                f"{label}: command log missing/outside repo: {log_rel}")
        require(re.fullmatch(r"[0-9a-f]{64}", str(command.get("sha256"))) is not None,
                f"{label}: malformed log hash: {log_rel}")
        require(sha256(log) == command["sha256"], f"{label}: log hash mismatch: {log_rel}")
        run_logs.append((log_rel, log.read_text(encoding="utf-8", errors="replace")))
    run_candidates = [(name, body) for name, body in run_logs
                      if "run" in Path(name).name or "SYSTEM_FRAME_PASS" in body
                      or "SCANOUT_PASS" in body or "FRAME_PASS" in body]
    require(run_candidates, f"{label}: no execution log")
    combined = "\n".join(body for _, body in run_candidates)
    require(re.search(terminal_pattern, combined, re.MULTILINE) is not None,
            f"{label}: expected terminal PASS marker absent")
    return len(commands), combined


def logged_key_values(body, prefix):
    rows = []
    for line in body.splitlines():
        if line.startswith(prefix):
            rows.append({key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)})
    return rows


def audit_receiver():
    path = ROOT / "fpga/experiments/cu66-v78/receiver/results.json"
    data = read_json(path)
    label = "receiver"
    require(data.get("schema") == "cu78-receiver-regression-v1", f"{label}: schema mismatch")
    require(data.get("status") == "PASS_ACTUAL_PACKET_BASE_DIRECT_OWNER", f"{label}: not PASS")
    cases = data.get("frame_cases")
    require(isinstance(cases, list) and cases, f"{label}: frame cases absent")
    for i, case in enumerate(cases):
        mode = case.get("mode")
        if mode in (0, 5, 6, 7, 8):
            require(case.get("error") == 0 and case.get("tiles") == 8100
                    and case.get("commits", 0) >= 1,
                    f"{label}: successful frame case did not complete {i}")
        elif mode == 1:
            require(case.get("error", 0) != 0 and case.get("commits") == 0,
                    f"{label}: malformed packet was not rejected {i}")
        elif mode in (2, 3, 4):
            require(case.get("abort_commands", 0) >= 1 and case.get("commits") == 0,
                    f"{label}: injected failure was not aborted {i}")
        else:
            raise ValueError(f"{label}: unknown frame case mode {mode!r}")
    corpus = data.get("actual_corpus_frames")
    require(isinstance(corpus, int) and corpus > 0, f"{label}: corpus identity count missing")
    sources = verify_sources(data, label)
    commands, log = verify_commands(data, label, r"^PASS actual_frames=\d+ .*seed=\d+ clocks=\d+ .*$")
    logged = logged_key_values(log, "FRAME_PASS ")
    require(len(logged) == len(cases), f"{label}: FRAME_PASS log/result count mismatch")
    for i, (row, case) in enumerate(zip(logged, cases)):
        for key in ("fid", "key", "mode", "clocks", "tiles", "error", "commits",
                    "abort_commands", "stale", "validated_checks", "display_guard_checks",
                    "pending_lease_checks", "reference_bank"):
            require(row.get(key) == case.get(key), f"{label}: logged {key} mismatch case={i}")
    return f"receiver cases={len(cases)} corpus_frames={corpus} source_pins={sources} logs={commands}"


def audit_scanout():
    path = ROOT / "fpga/experiments/cu66-v78/scanout/results.json"
    data = read_json(path)
    label = "scanout"
    require(data.get("schema") == "cu78-continuous-scanout-v1", f"{label}: schema mismatch")
    require(data.get("status") == "PASS_EXACT_CONTINUOUS_NATIVE_SCANOUT", f"{label}: not PASS")
    runs = data.get("runs")
    require(isinstance(runs, list) and len(runs) >= 2, f"{label}: expected multiple retained runs")
    for run in runs:
        require(run.get("native_pixels", 0) > 0 and run.get("exact_pixels") == run["native_pixels"],
                f"{label}: non-exact raster run seed={run.get('seed')}")
        require(run.get("underruns") == 0 and run.get("memory_errors") == 0,
                f"{label}: underrun/memory error")
        require(run.get("distinct_sources", 0) >= 2 and run.get("raster_cache_epochs", 0) >= 2,
                f"{label}: source changes or continuous epochs absent")
    sources = verify_sources(data, label)
    commands, log = verify_commands(data, label, r"^SCANOUT_PASS .*underruns=0 memory_errors=0 cycles=\d+$")
    logged = logged_key_values(log, "SCANOUT_PASS ")
    require(len(logged) == len(runs), f"{label}: SCANOUT_PASS log/result count mismatch")
    for row, run in zip(logged, runs):
        for key in run:
            if isinstance(run[key], int):
                require(row.get(key) == run[key], f"{label}: logged {key} mismatch seed={run.get('seed')}")
    return f"scanout runs={len(runs)} exact_pixels/run source_pins={sources} logs={commands}"


def audit_system(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == "cu78-actual-decode-direct-system-v1", f"{label}: schema mismatch")
    require(data.get("status") == "PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY", f"{label}: not PASS")
    frames, timings = data.get("frames"), data.get("timings")
    summary = data.get("summary")
    require(isinstance(frames, list) and frames and isinstance(timings, list) and timings,
            f"{label}: frames/timings absent")
    require(isinstance(summary, dict), f"{label}: summary absent")
    require(summary.get("complete_frames") == len(frames), f"{label}: complete_frames arithmetic mismatch")
    require(summary.get("distinct_complete_presentations") == len(timings),
            f"{label}: presentation/timing count mismatch")
    require(len(timings) == len(frames), f"{label}: timing/frame count mismatch")
    require(summary.get("total_underruns") == sum(f.get("underruns", 0) for f in frames),
            f"{label}: underrun sum mismatch")
    require(summary.get("cycles", 0) >= max(f.get("cycles", 0) for f in frames),
            f"{label}: total cycle count less than a frame's cycle count")
    clocks = data.get("clocks")
    require(isinstance(clocks, dict) and clocks.get("memory_period_ps") == 10000,
            f"{label}: expected recorded 10,000 ps memory clock")
    require(summary.get("canonical_bytes_per_frame") == 518400,
            f"{label}: canonical plane byte count mismatch")
    require(summary.get("RGB_DDR_words_written_per_frame") == 0,
            f"{label}: RGB framebuffer writes reported")
    frame_ids = [(f.get("generation"), f.get("fid")) for f in frames]
    timing_ids = [(t.get("generation"), t.get("fid")) for t in timings]
    require(len(set(frame_ids)) == len(frame_ids) and set(timing_ids) == set(frame_ids),
            f"{label}: duplicate or unmatched source identities")
    require(all(t.get("complete_rasters", 0) > 0 for t in timings),
            f"{label}: no complete correct raster recorded for a presentation")
    for i, (frame, timing) in enumerate(zip(frames, timings)):
        require(frame.get("generation") == timing.get("generation") and frame.get("fid") == timing.get("fid"),
                f"{label}: frame/timing identity mismatch at {i}")
        packet = timing.get("packet_complete_cycle")
        admission = timing.get("admission_cycle")
        ready = timing.get("validated_ready_cycle")
        ack = timing.get("commit_ack_cycle")
        presented = timing.get("descriptor_presented_cycle")
        require(isinstance(packet, int) and isinstance(admission, int) and isinstance(ready, int)
                and isinstance(ack, int) and isinstance(presented, int),
                f"{label}: missing source timing milestones {i}")
        require(packet <= admission < ready <= ack,
                f"{label}: invalid packet/admission/validated/ACK order {i}")
        require(timing.get("validated_decode_model_cycles") == ready - packet,
                f"{label}: validated model cycle arithmetic mismatch {i}")
        require(timing.get("queue_cycles") == admission - packet,
                f"{label}: queue cycle arithmetic mismatch {i}")
        origin_to_ack = ack - packet
        require(frame.get("origin_to_ack_cycles") == origin_to_ack,
                f"{label}: frame origin-to-ACK cycle arithmetic mismatch {i}")
        budget_30 = origin_to_ack * 30 <= 100000000
        budget_10 = timing["validated_decode_model_cycles"] * 10000 < 10000000000
        require(timing.get("met_serial_30fps_budget") == int(budget_30),
                f"{label}: 30-fps modeled threshold flag mismatch {i}")
        require(timing.get("met_validated_under10ms") == int(budget_10),
                f"{label}: under-10-ms modeled threshold flag mismatch {i}")
        if data.get("arrival_mode") == "fixed30":
            expected_release = 108 + i * 100000000 // 30
            require(packet == expected_release, f"{label}: fixed30 source release spacing mismatch {i}")
        require(frame.get("actual_write_commands", 0) * 8 == frame.get("actual_write_bus_beats"),
                f"{label}: write command/beat arithmetic mismatch frame={i}")
        require(frame.get("actual_writes") == frame.get("actual_write_bus_beats"),
                f"{label}: actual write count mismatch frame={i}")
        require(frame.get("underruns") == 0, f"{label}: frame underrun frame={i}")
    perf = data.get("performance")
    require(isinstance(perf, dict), f"{label}: performance verdict absent")
    serial_all = all(t["met_serial_30fps_budget"] == 1 for t in timings)
    under10_all = all(t["met_validated_under10ms"] == 1 for t in timings)
    require(perf.get("serial_30fps_all_pass") is serial_all,
            f"{label}: serial 30-fps aggregate mismatch")
    require(perf.get("validated_under10ms_all_pass") is under10_all,
            f"{label}: under-10-ms aggregate mismatch")
    expected_model_ms = [t["validated_decode_model_cycles"] * 0.00001 for t in timings]
    expected_ack_ms = [(t["commit_ack_cycle"] - t["packet_complete_cycle"]) * 0.00001
                       for t in timings]
    require(len(perf.get("validated_model_ms", [])) == len(expected_model_ms)
            and all(abs(a - b) < 1e-9 for a, b in zip(perf["validated_model_ms"], expected_model_ms)),
            f"{label}: validated model ms arithmetic mismatch")
    require(len(perf.get("origin_to_ack_model_ms", [])) == len(expected_ack_ms)
            and all(abs(a - b) < 1e-9 for a, b in zip(perf["origin_to_ack_model_ms"], expected_ack_ms)),
            f"{label}: origin-to-ACK model ms arithmetic mismatch")
    for timing in timings:
        require(isinstance(timing.get("validated_decode_model_cycles"), int),
                f"{label}: validated decode timing missing")
        require(isinstance(timing.get("met_serial_30fps_budget"), int)
                and isinstance(timing.get("met_validated_under10ms"), int),
                f"{label}: threshold outcomes missing")
    sources = verify_sources(data, label)
    commands, log = verify_commands(data, label, r"^SYSTEM_PASS .*physical_fps_proven=\d+$")
    log_frames, log_timings = logged_key_values(log, "SYSTEM_FRAME_PASS "), logged_key_values(log, "SYSTEM_TIMING ")
    log_summary = logged_key_values(log, "SYSTEM_PASS ")
    require(len(log_frames) == len(frames) and len(log_timings) == len(timings) and len(log_summary) == 1,
            f"{label}: frame/timing/summary log counts mismatch")
    for section, logged_rows, recorded_rows in (("frame", log_frames, frames),
                                                  ("timing", log_timings, timings)):
        for i, (row, recorded) in enumerate(zip(logged_rows, recorded_rows)):
            for key, value in row.items():
                require(recorded.get(key) == value,
                        f"{label}: log/result {section} field {key} mismatch row={i}")
    for key, value in log_summary[0].items():
        require(summary.get(key) == value, f"{label}: log/result summary field {key} mismatch")
    threshold30 = sum(t["met_serial_30fps_budget"] == 1 for t in timings)
    under10 = sum(t["met_validated_under10ms"] == 1 for t in timings)
    return (f"{path.parent.name}: frames={len(frames)} source_pins={sources} logs={commands}; "
            f"functional=PASS; performance observations 30fps={threshold30}/{len(timings)}, "
            f"under10ms={under10}/{len(timings)}, physical_fps_proven={summary.get('physical_fps_proven')}")


def audit_system_fault(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == "cu78-system-fault-v1", f"{label}: schema mismatch")
    require(data.get("status") == "PASS_REJECT_ABORT_RETAIN_AND_RECOVER", f"{label}: not PASS")
    cases, summary = data.get("cases"), data.get("summary")
    require(isinstance(cases, list) and len(cases) == 2, f"{label}: expected two directed cases")
    require(isinstance(summary, dict), f"{label}: summary absent")
    by_kind = {case.get("kind"): case for case in cases}
    require(set(by_kind) == {"bad_crc", "partial_write_abort"}, f"{label}: fault case set mismatch")
    bad_crc, partial = by_kind["bad_crc"], by_kind["partial_write_abort"]
    require(bad_crc.get("physical_write_words") == 0 and bad_crc.get("error", 0) > 0,
            f"{label}: bad CRC did not reject before physical writes")
    require(partial.get("physical_write_words", 0) > 0
            and partial.get("processor_abort_calls", 0) > 0,
            f"{label}: partial write abort was not exercised")
    require(partial.get("canonical_write_words_observed", 0) >= 64
            and partial.get("active_tile_at_abort") == 1,
            f"{label}: partial abort lacks canonical write evidence or active tile")
    require(all(case.get("old_front_full_raster") == 1 for case in cases),
            f"{label}: old front did not complete an exact raster through each fault")
    require(summary.get("rejected") == 2 and summary.get("accepted") == 2,
            f"{label}: rejection/acceptance summary mismatch")
    require(summary.get("no_per_source_reset") == 1,
            f"{label}: recovery without per-source reset not established")
    require(summary.get("underruns") == 0 and summary.get("black_lines") == 0,
            f"{label}: underrun or black-line failure")
    sources = verify_sources(data, label)
    commands, log = verify_commands(data, label, r"^SYSTEM_FAULT_CAMPAIGN_PASS .+$")
    logged = logged_key_values(log, "SYSTEM_FAULT_PASS ")
    require(len(logged) == len(cases), f"{label}: fault log/result count mismatch")
    for row, case in zip(logged, cases):
        for key, value in row.items():
            if key != "kind":
                require(case.get(key) == value, f"{label}: fault log/result {key} mismatch")
    log_summary = logged_key_values(log, "SYSTEM_FAULT_CAMPAIGN_PASS ")
    require(len(log_summary) == 1, f"{label}: fault terminal summary missing/duplicate")
    for key, value in log_summary[0].items():
        require(summary.get(key) == value, f"{label}: fault summary log/result {key} mismatch")
    recovered = logged_key_values(log, "SYSTEM_FRAME_PASS ")
    require(len(recovered) == 2 and recovered[-1].get("processor_commit_calls", 0) >= 2,
            f"{label}: accepted retry after lost COMMIT ACK was not reconciled")
    return (f"faults: directed_cases=2 source_pins={sources} logs={commands}; "
            "functional=PASS for bad-CRC rejection, partial-write abort, retained-front rasters, "
            "and recovered COMMIT ACK only")


def main():
    reports = [audit_receiver(), audit_scanout()]
    system_results = sorted(p for p in SYSTEM_ROOT.glob("*/results.json")
                            if p.parent.name != "faults")
    require(system_results, "system: no retained results.json; at least one actual system proof is required")
    reports.extend(audit_system(path) for path in system_results)
    fault_result = SYSTEM_ROOT / "faults/results.json"
    if fault_result.is_file():
        reports.append(audit_system_fault(fault_result))
    print("V78_EVIDENCE_AUDIT_PASS")
    print("Functional evidence and performance thresholds are reported separately.")
    print("No physical 30 fps or strict under-10-ms claim is inferred from simulation.")
    for report in reports:
        print(f"- {report}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"V78_EVIDENCE_AUDIT_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
