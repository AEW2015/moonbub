#!/usr/bin/env python3
"""Independent V81 retained-system, path-trace and comparison evidence audit."""
import csv
import gzip
import hashlib
import io
import json
import math
import re
import statistics
import sys
import tarfile
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SYSTEM_ROOT=ROOT/'fpga/experiments/cu66-v81/system'
V81_SCHEMA='cu81-integrated-prefetch-system-v1'
PASS='PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY'
EXPECTED_COHORTS={0:119,1:119,2:119,3:100}
MUTABLE_PREFIXES=('fpga/experiments/cu66-v81/','scripts/cu66-v81/')
HASH_RE=re.compile(r'[0-9a-f]{64}')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256(path):
    return sha256_bytes(path.read_bytes())


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc


def safe_repo_file(relpath, label):
    require(isinstance(relpath, str) and not Path(relpath).is_absolute(),
            f"{label}: invalid repository path {relpath!r}")
    path = (ROOT / relpath).resolve()
    require(path.is_relative_to(ROOT.resolve()) and path.is_file(),
            f"{label}: missing/outside-repository file {relpath}")
    return path


def safe_artifact_file(relpath, base, label):
    require(isinstance(relpath, str) and not Path(relpath).is_absolute(),
            f"{label}: invalid artifact path {relpath!r}")
    path = (ROOT / relpath).resolve() if (ROOT / relpath).is_file() else (base / relpath).resolve()
    require(path.is_relative_to(ROOT.resolve()) and path.is_file(),
            f"{label}: missing/outside-repository artifact {relpath}")
    return path


def parse_fields(line):
    return {key: int(value) for key, value in re.findall(r"(\w+)=(-?\d+)", line)}


def histogram_summary(hist):
    if not hist:
        return {"n": 0}
    n = sum(hist.values())
    items = sorted(hist.items())
    def quantile(fraction):
        target = max(1, math.ceil(n*fraction))
        accum = 0
        for value, count in items:
            accum += count
            if accum >= target:
                return value
    total = sum(value*count for value,count in items)
    return {"n": n, "min": items[0][0], "p50_nearest_rank": quantile(.5),
            "p90_nearest_rank": quantile(.9), "p99_nearest_rank": quantile(.99),
            "max": items[-1][0], "sum": total, "mean": total/n,
            "negative": sum(c for v,c in items if v < 0), "zero": hist.get(0,0),
            "positive": sum(c for v,c in items if v > 0)}


def check_pin_map(pins, label, archive=None):
    require(isinstance(pins, dict) and pins, f"{label}: source_sha256 missing/empty")
    archive_files = {}
    if archive is not None:
        try:
            with tarfile.open(archive, "r:gz") as tar:
                for member in tar.getmembers():
                    path = Path(member.name)
                    require(not path.is_absolute() and ".." not in path.parts,
                            f"{label}: unsafe snapshot path {member.name}")
                    if member.isfile():
                        stream = tar.extractfile(member)
                        require(stream is not None, f"{label}: unreadable snapshot member {member.name}")
                        archive_files[str(path)] = sha256_bytes(stream.read())
        except (OSError, tarfile.TarError) as exc:
            raise ValueError(f"{label}: cannot read source snapshot: {exc}") from exc
    for relpath, expected in pins.items():
        require(isinstance(relpath, str) and HASH_RE.fullmatch(str(expected)) is not None,
                f"{label}: malformed source hash: {relpath}")
        if relpath.startswith(MUTABLE_PREFIXES):
            require(archive is not None and archive_files.get(relpath) == expected,
                    f"{label}: mutable V81 source missing/mismatched in archived snapshot: {relpath}")
        else:
            path = safe_repo_file(relpath, label)
            require(sha256(path) == expected, f"{label}: frozen source hash mismatch: {relpath}")
    return len(pins)


def check_snapshot(data, label, base):
    snap = data.get("source_snapshot")
    require(isinstance(snap, dict) and isinstance(snap.get("path"), str),
            f"{label}: source_snapshot missing")
    archive = safe_artifact_file(snap["path"], base, label)
    require(HASH_RE.fullmatch(str(snap.get("sha256"))) is not None
            and sha256(archive) == snap["sha256"], f"{label}: source snapshot hash mismatch")
    return archive


def check_commands(data, label, base):
    commands = data.get("commands")
    require(isinstance(commands, list) and commands, f"{label}: commands missing/empty")
    logs = {}
    for command in commands:
        require(isinstance(command, dict), f"{label}: malformed command record")
        rel = command.get("log")
        require(command.get("exit_code") == 0 and command.get("timed_out") is False,
                f"{label}: failed/timed-out command: {command}")
        path = safe_artifact_file(rel, base, label)
        require(HASH_RE.fullmatch(str(command.get("sha256"))) is not None
                and sha256(path) == command["sha256"], f"{label}: command log hash mismatch: {rel}")
        logs[rel] = path.read_text(encoding="utf-8", errors="replace")
    return logs


def audit_system(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == V81_SCHEMA and data.get("status") == PASS,
            f"{label}: schema/status mismatch")
    cohort, count = data.get("cohort"), data.get("requested_frames")
    require(cohort in EXPECTED_COHORTS and isinstance(count, int) and 0 < count <= EXPECTED_COHORTS[cohort],
            f"{label}: invalid cohort/frame count")
    require(data.get("arrival_mode") in ("fixed30", "paced") and data.get("tac_ns") in (2, 7)
            and data.get("variant") in ("baseline", "prefetch", "overlap", "wide")
            and data.get("prefetch") == {"baseline": 0, "prefetch": 1, "overlap": 2, "wide": 3}[data["variant"]],
            f"{label}: variant/arrival/tAC contract mismatch")
    frames, timings, deadlines = data.get("frames"), data.get("timings"), data.get("raster_deadlines")
    prefetch_rows, command_rows = data.get("prefetch_frames"), data.get("command_frames")
    path_rows = data.get("path_frames")
    summary, perf = data.get("summary"), data.get("performance")
    require(all(isinstance(x, list) for x in (frames, timings, deadlines, prefetch_rows, command_rows, path_rows))
            and isinstance(summary, dict) and isinstance(perf, dict), f"{label}: records missing")
    require(len(frames) == len(timings) == len(deadlines) == len(prefetch_rows) == len(command_rows) == len(path_rows) == count,
            f"{label}: frame/timing/deadline/prefetch/command cardinalities differ")
    require(summary.get("cohort") == cohort and summary.get("complete_frames") == count
            and summary.get("distinct_complete_presentations") == count
            and summary.get("physical_fps_proven") == 0,
            f"{label}: functional summary mismatch or physical rate claim")
    require(summary.get("canonical_bytes_per_frame") == 518400
            and summary.get("RGB_DDR_words_written_per_frame") == 0,
            f"{label}: canonical/RGB-write contract mismatch")
    for key in ("black_lines", "total_underruns", "lcd_memory_errors", "sticky_lcd_error",
                "sticky_memory_error", "sticky_underrun"):
        require(summary.get(key) == 0, f"{label}: health failure: {key}")
    require(summary.get("raster_deadline_cycles") == 10_000_000
            and summary.get("global_watchdog_cycles", 0) > 0,
            f"{label}: bounded raster/global watchdog missing")
    require(isinstance(data.get("clocks"), dict) and data["clocks"].get("memory_period_ps") == 10000,
            f"{label}: unexpected memory clock")
    ids = [x.get("fid") for x in frames]
    gens = [x.get("generation") for x in frames]
    require(len(set(ids)) == count and len(set(gens)) == count,
            f"{label}: duplicate source identity/generation")
    require(set(ids) == {x.get("fid") for x in timings} == {x.get("fid") for x in prefetch_rows}
            == {x.get("fid") for x in command_rows}, f"{label}: source identity rows do not pair")
    require(data.get("trace_source_ordinals", []) == sorted(set(data.get("trace_source_ordinals", [])))
            and all(isinstance(x, int) and 0 <= x < count for x in data.get("trace_source_ordinals", [])),
            f"{label}: selected trace ordinals malformed")

    for i, (frame, timing, deadline, pref, cmd) in enumerate(zip(frames, timings, deadlines,
                                                                  prefetch_rows, command_rows)):
        identity = (frame.get("generation"), frame.get("fid"))
        require(all((item.get("generation"), item.get("fid")) == identity
                    for item in (timing, deadline, pref, cmd)), f"{label}: identity mismatch row {i}")
        packet, admission = timing.get("packet_complete_cycle"), timing.get("admission_cycle")
        ready, ack = timing.get("validated_ready_cycle"), timing.get("commit_ack_cycle")
        require(all(isinstance(x, int) for x in (packet, admission, ready, ack))
                and packet <= admission < ready <= ack, f"{label}: invalid packet/admission/ready/ACK order row={i}")
        require(timing.get("queue_cycles") == admission-packet
                and timing.get("validated_decode_model_cycles") == ready-packet
                and timing.get("post_validated_ack_model_cycles") == ack-ready
                and frame.get("origin_to_ack_cycles") == ack-packet,
                f"{label}: timing arithmetic mismatch row={i}")
        require(data["arrival_mode"]!="fixed30" or packet == 108+i*100_000_000//30,
                f"{label}: fixed30 release schedule mismatch row={i}")
        expected30 = int((ack-packet)*30 <= 100_000_000)
        expected10 = int((ready-packet)*10_000 < 10_000_000_000)
        require(timing.get("met_serial_30fps_budget") == expected30
                and timing.get("met_validated_under10ms") == expected10,
                f"{label}: modeled threshold arithmetic mismatch row={i}")
        require(deadline.get("commit_ack_cycle") == ack
                and deadline.get("due_cycle") == ack+10_000_000
                and deadline.get("bound_cycles") == 10_000_000
                and deadline.get("functional_liveness_only") == 1,
                f"{label}: ACK/raster deadline arithmetic mismatch row={i}")
        start, end = timing.get("first_complete_raster_start_ps"), timing.get("first_complete_raster_end_ps")
        require(timing.get("complete_rasters", 0) > 0 and isinstance(start, int) and isinstance(end, int)
                and 0 < start < end <= (ack+10_000_000)*10_000,
                f"{label}: complete native raster misses functional deadline row={i}")
        require(frame.get("actual_write_commands", 0)*8 == frame.get("actual_write_bus_beats")
                and frame.get("actual_writes") == frame.get("actual_write_bus_beats")
                and frame.get("underruns") == 0,
                f"{label}: SDRAM write beat/underrun arithmetic mismatch row={i}")
        require(frame.get("actual_write_commands") == 35040 and frame.get("actual_write_bus_beats") == 280320,
                f"{label}: canonical and HUD physical write volume mismatch row={i}")
        require(cmd.get("tile_write_requests") == cmd.get("tile_write_done") == 8100,
                f"{label}: canonical tile write retirement count mismatch row={i}")
        if pref.get("new_epoch"):
            require(pref.get("epoch_done_events", 0) == 1
                    and 0 < pref.get("epoch_done_cycle", 0) < timing.get("validated_ready_cycle", 0),
                    f"{label}: prefetch retirement/drain fence does not precede validation row={i}")
        if data["variant"] == "baseline":
            require(pref.get("read_commands") == pref.get("read_beats") == 0
                    and cmd.get("client3_reads") == 0 and cmd.get("prefetch_fill_events") == 0,
                    f"{label}: baseline variant unexpectedly issued prefetch reads")
        elif pref.get("new_epoch"):
            require(pref.get("read_commands") == 32400 and pref.get("read_beats") == 259200
                    and cmd.get("client3_reads") == frame.get("p0_cache_misses") == 32400
                    and frame.get("p0_cache_hits", -1) + frame.get("p0_cache_misses", -1)
                        == frame.get("p0_row_reads") == 32400
                    and cmd.get("client3_writes") == 0 and cmd.get("prefetch_fill_events") == 8100,
                    f"{label}: enabled variant lacks full all-tile actual-read/logical P0 accounting")
        else:
            require(cmd.get("client3_reads") == 0 and cmd.get("client3_writes") == 0
                    and cmd.get("prefetch_fill_events") == 0 and frame.get("p0_cache_hits", 0) == 0
                    and frame.get("p0_cache_misses", 0) == 0 and frame.get("p0_row_reads", 0) == 0,
                    f"{label}: reused/initial frame issued unexpected P0 SDRAM reads")
            if pref.get("epoch_generation", 0) > 0:
                require(pref.get("read_commands") == 32400 and pref.get("read_beats") == 259200
                        and pref.get("tiles_filled") == pref.get("tiles_retired") == 8100
                        and pref.get("epoch_done_events") == 1
                        and 0 < pref.get("epoch_done_cycle", 0) < timing.get("validated_ready_cycle", 0),
                        f"{label}: cached completed prefetch epoch state malformed")
            else:
                require(pref.get("read_commands") == pref.get("read_beats") == 0
                        and pref.get("tiles_filled") == 0 and pref.get("tiles_retired") == 0,
                        f"{label}: initial frame has unexpected prefetch epoch")
        if data["variant"] in ("overlap", "wide"):
            stream = data.get("stream_frames")
            require(isinstance(stream, list) and len(stream) == count,
                    f"{label}: overlap stream observations missing")
            for stream_row in stream:
                require(stream_row.get("generation") in gens and stream_row.get("mode") == data["prefetch"]
                        and all(isinstance(stream_row.get(k), int) and stream_row[k] >= 0
                                for k in ("candidate_wait_cycles", "idle_candidate_wait_cycles", "write_accepts")),
                        f"{label}: malformed overlap stream observation")
        base_bins = [frame.get(f"base{base}_tile{tile}_aux{aux}_cycles")
                     for base in range(2) for tile in range(2) for aux in range(2)]
        stage_bins = [frame.get(f"stage{stage}_cycles") for stage in range(16)]
        require(all(isinstance(x, int) and x >= 0 for x in base_bins+stage_bins)
                and sum(base_bins) == sum(stage_bins) == frame.get("cycles"),
                f"{label}: disjoint profile bins do not partition cycles row={i}")
        require(sum(base_bins[4:]) == sum(stage_bins[5:6]),
                f"{label}: BASE_RUN/base1 occupancy mismatch row={i}")

    for frame, path_row in zip(frames, path_rows):
        expected_blocks=32400 if data['prefetch']==3 and not frame['key'] else 0
        require((path_row.get('generation'),path_row.get('fid'),path_row.get('mode')) == (frame['generation'],frame['fid'],data['prefetch'])
                and path_row.get('ref_first_valid')==(0 if frame['key'] else 7806)
                and path_row.get('backend_write_done')==8100
                and path_row.get('raw_requests')==path_row.get('snapshots')==path_row.get('block_commits')==expected_blocks
                and path_row.get('raw_snapshot_block_instrumented')==int(data['prefetch']==3),
                f'{label}: actual path accounting mismatch')
    prior_epoch=0;prior_pref=None
    for frame,pref in zip(frames,prefetch_rows):
        require(pref.get('enabled')==int(data['prefetch']>0) and pref.get('key')==frame['key']
                and pref.get('busy')==0 and pref.get('fault')==0,
                f'{label}: prefetch enabled/key/health mismatch')
        if data['prefetch'] and not frame['key']:
            require(pref.get('epoch_generation')==frame['generation'] and pref.get('new_epoch')==1
                    and pref.get('read_commands')==32400 and pref.get('read_beats')==259200
                    and pref.get('tiles_filled')==pref.get('tiles_retired')==8100
                    and pref.get('lookups')==7806 and pref.get('unused_retired')==294
                    and pref.get('epoch_done_events')==1 and pref.get('epoch_aborted_events')==0,
                    f'{label}: full prefetch epoch conservation mismatch')
        elif data['prefetch']:
            require(pref.get('epoch_generation')==prior_epoch and pref.get('new_epoch')==0,
                    f'{label}: keyframe changed prefetch epoch identity')
            if prior_pref:
                require(all(pref.get(k)==prior_pref.get(k) for k in ('epoch_generation','read_commands','read_beats','tiles_filled','lookups','tiles_retired','unused_retired','epoch_done_events','epoch_aborted_events','epoch_done_cycle','epoch_aborted_cycle')),
                        f'{label}: keyframe mutated retained epoch diagnostics')
        prior_epoch=pref['epoch_generation'];prior_pref=pref
    expected_serial = all(t.get("met_serial_30fps_budget") == 1 for t in timings)
    expected_strict = all(t.get("met_validated_under10ms") == 1 for t in timings)
    require(perf.get("serial_30fps_all_pass") is expected_serial
            and perf.get("validated_under10ms_all_pass") is expected_strict
            and perf.get("status") == ("PASS" if expected_serial and expected_strict else "FAIL"),
            f"{label}: performance observation aggregation mismatch")
    for key, values in (("validated_model_ms", [t["validated_decode_model_cycles"]*1e-5 for t in timings]),
                        ("origin_to_ack_model_ms", [(t["commit_ack_cycle"]-t["packet_complete_cycle"])*1e-5
                                                     for t in timings])):
        actual = perf.get(key)
        require(isinstance(actual, list) and len(actual) == len(values)
                and all(abs(a-b) < 1e-9 for a, b in zip(actual, values)),
                f"{label}: {key} arithmetic mismatch")
    require(any("No physical 30fps" in item for item in data.get("limitations", [])),
            f"{label}: physical performance limitation missing")

    base = path.parent
    archive = check_snapshot(data, label, base)
    source_count = check_pin_map(data.get("source_sha256"), label, archive)
    require(isinstance(data.get('build_provenance'),dict)
            and data['build_provenance'].get('source_sha256')==data.get('source_sha256'),
            f'{label}: build/run producer pin maps differ')
    check_pin_map(data['build_provenance'].get('source_sha256'),label+' build provenance',archive)
    check_commands(data['build_provenance'],label+' build provenance',base)
    logs = check_commands(data, label, base)
    run_logs = [body for rel, body in logs.items() if Path(rel).name == "run.log"]
    require(len(run_logs) == 1, f"{label}: expected one run log")
    body = run_logs[0]
    require(len(re.findall(r"^SYSTEM_PASS .+$", body, re.M)) == 1,
            f"{label}: unique terminal SYSTEM_PASS missing")
    logged_records = [("SYSTEM_FRAME_PASS ", frames), ("SYSTEM_TIMING ", timings),
                      ("SYSTEM_RASTER_DEADLINE ", deadlines), ("SYSTEM_PREFETCH ", prefetch_rows),
                      ("SYSTEM_COMMANDS ", command_rows), ("SYSTEM_PATH ", path_rows)]
    if data.get("stream_frames") is not None:
        logged_records.append(("SYSTEM_STREAM ", data.get("stream_frames", [])))
    for prefix, records in logged_records:
        rows = [parse_fields(line[len(prefix):]) for line in body.splitlines() if line.startswith(prefix)]
        require(len(rows) == count, f"{label}: {prefix.strip()} log cardinality mismatch")
        for i, (row, record) in enumerate(zip(rows, records)):
            require(all(record.get(k) == v for k, v in row.items()),
                    f"{label}: logged {prefix.strip()} differs from JSON row={i}")
    terminal = parse_fields(re.search(r"^SYSTEM_PASS (.+)$", body, re.M).group(1))
    require(all(summary.get(k) == v for k, v in terminal.items()),
            f"{label}: SYSTEM_PASS summary differs from JSON")
    binary_logs = [body for rel, body in logs.items() if Path(rel).name == "binary.log"]
    binary_check = [body for rel, body in logs.items() if Path(rel).name == "binary-check.log"]
    require(len(binary_check) == 1 and len(binary_logs) <= 1,
            f"{label}: binary hash logs missing/duplicated")
    check_hashes = re.findall(r"\b([0-9a-f]{64})\b", binary_check[0])
    binary_hashes = re.findall(r"\b([0-9a-f]{64})\b", binary_logs[0]) if binary_logs else check_hashes
    require(len(binary_hashes) == len(check_hashes) == 1 and binary_hashes == check_hashes
            and check_hashes[0]==data["build_provenance"].get("binary_sha256"),
            f"{label}: executable hash mismatch between build and run provenance")
    trace_audit = None
    if data.get("trace"):
        selected = data.get("trace_source_ordinals", [])
        require(len(selected) <= min(count, 4), f"{label}: too many selected trace frames")
        trace_audit = audit_trace(data, label, base, frames, timings, prefetch_rows, command_rows, path_rows)
    return {"path": path, "data": data, "source_count": source_count, "command_count": len(logs),
            "trace_audit": trace_audit}


def audit_observer(path):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu81-observer-unit-v1" and d.get("status") == "PASS"
            and d.get("tests") == 9 and d.get("observer_unit_only") is True
            and d.get("hardware_fault_injection") is False,
            f"{label}: observer unit status/scope mismatch")
    base = path.parent
    archive = base / "sources.tar.gz"
    require(archive.is_file() and sha256(archive) == d.get("source_snapshot_sha256"),
            f"{label}: observer snapshot hash mismatch")
    check_pin_map(d.get("source_sha256"), label, archive)
    commands = d.get("commands", [])
    require(commands and all(c.get("exit_code") == 0 and not c.get("timed_out", True) for c in commands),
            f"{label}: observer command status mismatch")
    logs = {}
    for command in commands:
        log = safe_artifact_file(command.get("log"), base, label)
        require(sha256(log) == command.get("sha256"), f"{label}: observer log hash mismatch")
        logs[Path(command["log"]).name] = log.read_text(encoding="utf-8", errors="replace")
    run_log = logs.get("run.log", "")
    cases = re.findall(r"^MONITOR_TEST_PASS case=\S+.*$", run_log, re.M)
    require(len(cases) == 9 and len(re.findall(
        r"^MONITOR_UNIT_PASS tests=9 observer_unit_only=1 hardware_fault_injection=0$", run_log, re.M)) == 1,
        f"{label}: observer case/terminal count mismatch")
    return label


def audit_campaign(path, audited):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu81-independent-history-campaign-v1"
            and d.get("status") == "PASS_ALL_REQUESTED_HISTORIES"
            and d.get("prefetch") == 3 and d.get("requested_sources") == 457,
            f"{label}: campaign schema/status/scope mismatch")
    pins = d.get("source_sha256")
    require(isinstance(pins, dict) and pins, f"{label}: campaign source pins missing")
    for rel, expected in pins.items():
        require(HASH_RE.fullmatch(str(expected)) is not None
                and sha256(safe_repo_file(rel, label)) == expected,
                f"{label}: campaign input source hash mismatch {rel}")
    cases = d.get("cases")
    require(isinstance(cases, list) and len(cases) == 4, f"{label}: expected four campaign cases")
    seen = set()
    for case in cases:
        cohort = case.get("cohort")
        require(cohort in EXPECTED_COHORTS and cohort not in seen
                and case.get("requested_sources") == EXPECTED_COHORTS[cohort]
                and case.get("exit_code") == 0 and case.get("error") is None,
                f"{label}: malformed or unsuccessful cohort case")
        seen.add(cohort)
        log = safe_repo_file(case.get("log"), label)
        require(HASH_RE.fullmatch(str(case.get("sha256"))) is not None
                and sha256(log) == case["sha256"], f"{label}: campaign raw command log hash mismatch")
        lines = [line for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
                 if line.startswith("{")]
        require(lines, f"{label}: command log lacks structured terminal record")
        terminal = json.loads(lines[-1])
        require(terminal == case.get("runner_result") and terminal.get("status") == "V81_SYSTEM_PASS"
                and terminal.get("frames") == EXPECTED_COHORTS[cohort],
                f"{label}: campaign terminal runner record mismatch")
        result_path = safe_repo_file(case.get("results_path"), label)
        require(HASH_RE.fullmatch(str(case.get("results_sha256"))) is not None
                and sha256(result_path) == case["results_sha256"],
                f"{label}: campaign system result hash mismatch")
        matched = [item for item in audited if item["path"] == result_path]
        require(len(matched) == 1 and matched[0]["data"].get("variant") == "wide"
                and matched[0]["data"].get("cohort") == cohort
                and matched[0]["data"].get("requested_frames") == EXPECTED_COHORTS[cohort],
                f"{label}: campaign case lacks its independently audited full-history result")
    require(seen == set(EXPECTED_COHORTS), f"{label}: missing cohort history")
    return f"mode3 campaign: four complete histories, 457 sources; result/log/source bindings verified"


def audit_fault(path):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu81-actual-system-fault-v1"
            and d.get("status") == "PASS_ACTUAL_REJECT_ABORT_RETAIN_AND_RECOVER"
            and d.get("prefetch_mode") == 3 and d.get("observer_unit_only") is False
            and d.get("hardware_fault_injection") is False,
            f"{label}: fault schema/status/scope mismatch")
    base = path.parent
    archive = check_snapshot(d, label, base)
    check_pin_map(d.get("source_sha256"), label, archive)
    check_pin_map(d.get("build_provenance", {}).get("source_sha256"), label+" build provenance", archive)
    logs = check_commands(d, label, base)
    logs_by_name = {Path(rel).name: body for rel, body in logs.items()}
    require(set(logs_by_name) == {"build.log", "binary.log", "binary-check.log", "run.log"},
            f"{label}: fault command log set mismatch")
    binary = re.findall(r"\b([0-9a-f]{64})\b", logs_by_name["binary.log"])
    binary_check = re.findall(r"\b([0-9a-f]{64})\b", logs_by_name["binary-check.log"])
    require(len(binary) == len(binary_check) == 1 and binary == binary_check
            and binary[0] == d.get("build_provenance", {}).get("binary_sha256"),
            f"{label}: fault executable hash mismatch")
    body = logs_by_name["run.log"]
    cases = d.get("cases")
    require(isinstance(cases, list) and [x.get("kind") for x in cases]
            == ["bad_crc", "partial_write_read_accept_abort"],
            f"{label}: fault case set mismatch")
    log_cases = [line for line in body.splitlines() if line.startswith("SYSTEM_FAULT_PASS ")]
    require(len(log_cases) == len(cases), f"{label}: fault case log cardinality mismatch")
    for i, (line, record) in enumerate(zip(log_cases, cases)):
        raw = dict(re.findall(r"(\w+)=([^\s]+)", line[len("SYSTEM_FAULT_PASS "):]))
        parsed = {key: int(value) for key, value in raw.items() if key != "kind"}
        require(raw.get("kind") == record.get("kind")
                and all(record.get(key) == value for key, value in parsed.items()),
                f"{label}: fault case/log mismatch row={i}")
    bad, abort = cases
    require(bad.get("physical_write_words") == bad.get("canonical_write_words_observed") == 0
            and bad.get("actual_prefetch_read_accepts") == 0 and bad.get("error") == 29
            and bad.get("accepted_count") == 1,
            f"{label}: bad CRC rejection evidence mismatch")
    for case in cases:
        require(case.get("wrapper_and_prefetch_drained") == 1
                and case.get("raw_bridge_and_controller_idle_observed") == 1
                and case.get("accepted_reference_unchanged") == 1
                and case.get("accepted_HUD_unchanged") == 1
                and case.get("old_front_full_raster") == 1,
                f"{label}: fault retention/drain/recovery guard failed")
    coincident = d.get("coincident_accepts")
    require(isinstance(coincident, list) and len(coincident) == 1, f"{label}: coincident accepted-read evidence missing")
    read = coincident[0]
    require(read.get('generation')==abort.get('generation')
            and read.get('cycle')==abort.get('abort_cycle') and read.get('cycle',0)>0
            and read.get('address')==abort.get('abort_read_address') and read.get('address',-1)%8==0
            and read.get('client')==3 and read.get('write')==0
            and read.get('canonical_words_before_abort',0)>=64
            and abort.get('canonical_write_words_observed',0)>=read['canonical_words_before_abort']
            and read.get('pending_lookup')==abort.get('pending_lookup_at_abort')
            and d.get('pending_lookup_at_abort') is bool(read.get('pending_lookup')),
            f'{label}: actual accepted-read/abort coincidence mismatch')
    require(abort.get('actual_prefetch_read_accepts',0)>0 and abort.get('read_accept_coincident_abort')==1
            and abort.get('epoch_done_events')==abort.get('epoch_aborted_events')==1
            and abort['abort_cycle']<=abort.get('epoch_done_cycle',-1)==abort.get('epoch_aborted_cycle',-2)
            and abort.get('processor_abort_calls',0)>0,
            f'{label}: partial abort completion/drain evidence mismatch')
    releases = d.get("endpoint_releases")
    require(isinstance(releases, list) and len(releases) == 2
            and [x.get("generation") for x in releases] == [bad.get("generation"), abort.get("generation")]
            and all(x.get("successful_commit") == 0 for x in releases)
            and all(x.get("aborted_endpoint_releases") == i for i, x in enumerate(releases, 1))
            and releases[1].get("cycle") >= abort.get("epoch_done_cycle"),
            f"{label}: endpoint release timing/count mismatch")
    summary = d.get("summary", {})
    expected = {"rejected": 2, "accepted": 2, "attempts": 4, "prefetch_mode": 3,
                "no_per_source_reset": 1, "aborted_endpoint_releases": 2, "underruns": 0,
                "black_lines": 0, "admitted": 4, "endpoint_releases": 4,
                "recovery_commit_calls": 2,
                "observer_unit_only": 0, "hardware_fault_injection": 0, "normal_external_abort": 1}
    require(all(summary.get(k) == v for k, v in expected.items())
            and summary.get("recovery_complete_rasters",0)>0
            and summary.get("clean_lines", 0) > 0 and summary.get("health_observations", 0) > 0,
            f"{label}: aggregate fault campaign summary mismatch")
    terminal = re.findall(r"^SYSTEM_FAULT_CAMPAIGN_PASS (.+)$", body, re.M)
    require(len(terminal) == 1, f"{label}: unique terminal fault marker missing")
    terminal_fields = parse_fields(terminal[0])
    require(all(summary.get(k) == v for k, v in terminal_fields.items()),
            f"{label}: terminal fault marker differs from JSON summary")
    logged_releases = [parse_fields(line.split("SYSTEM_FAULT_ENDPOINT_RELEASE ",1)[1])
                       for line in body.splitlines() if line.startswith("SYSTEM_FAULT_ENDPOINT_RELEASE ")]
    require(logged_releases == releases, f"{label}: endpoint release log differs from records")
    logged_reads = [parse_fields(line.split("SYSTEM_FAULT_ABORT_ACCEPT ",1)[1])
                    for line in body.splitlines() if line.startswith("SYSTEM_FAULT_ABORT_ACCEPT ")]
    require(len(logged_reads) == 1 and all(read.get(k) == v for k, v in logged_reads[0].items()),
            f"{label}: actual abort/read-accept event log mismatch")
    return "actual-system fault: bad-CRC rejection plus coincident accepted client3 read/abort; drained, retained, recovered"


def stat_values(values):
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def near(a, b):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9)


def compare_exact_fields(before, after):
    count=0
    for section in ("frames","timings"):
        require(len(before[section])==len(after[section]),"comparison control row count mismatch")
        for old,new in zip(before[section],after[section]):
            for key,value in old.items():
                if key=="native_hud_prepare_wall_ns": continue
                require(new.get(key)==value,f"comparison control mismatch {section}.{key}")
                count+=1
    for key,value in before["summary"].items():
        if key=="trace_rows":continue
        require(after["summary"].get(key)==value,f"comparison control mismatch summary.{key}")
        count+=1
    return count


def same_values(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual)==set(expected) and all(same_values(actual[k],v) for k,v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual,list) and len(actual)==len(expected) and all(same_values(a,e) for a,e in zip(actual,expected))
    if isinstance(expected,float):
        return near(actual,expected)
    return actual==expected


def audit_trace(data,label,base,frames,timings,prefetch_rows,command_rows,path_rows):
    """Validate exact event identities; raw bus commands keep owner UNKNOWN."""
    meta=data.get('trace');require(isinstance(meta,dict),f'{label}: trace metadata missing')
    path=safe_artifact_file(meta.get('path'),base,label)
    require(sha256(path)==meta.get('sha256'),f'{label}: compressed trace hash mismatch')
    try:raw=gzip.decompress(path.read_bytes())
    except (OSError,EOFError) as exc:raise ValueError(f'{label}: invalid compressed trace: {exc}') from exc
    require(len(raw)==meta.get('raw_bytes') and sha256_bytes(raw)==meta.get('raw_sha256'),f'{label}: raw trace hash/length mismatch')
    selected=data.get('trace_source_ordinals',[])
    require(0<len(selected)<=4,f'{label}: trace selection missing or outside bound')
    gens={frames[n]['generation'] for n in selected}
    bygen={f['generation']:f for f in frames};tm={t['generation']:t for t in timings}
    cmd={r['generation']:r for r in command_rows};paths={r['generation']:r for r in path_rows};prefs={r['generation']:r for r in prefetch_rows}
    tile_names=('ref_first_valid','ref_request','ref_response','tile_write_request','tile_write_done','backend_write_done','prefetch_fill')
    block_names=('prefetch_raw_request','prefetch_snapshot','prefetch_block_commit')
    allowed=set(tile_names)|set(block_names)|{'command','prefetch_epoch_done'}
    events={name:{} for name in tile_names+block_names};counts=Counter();pergen=defaultdict(Counter);actual_commands=Counter();physical_prefetch=Counter();done={}
    reader=csv.DictReader(io.StringIO(raw.decode('utf-8')))
    require(reader.fieldnames==['cycle','ps','frame_generation','event','owner_generation','client','write','address','bank','plane','tile_index'],f'{label}: trace header mismatch')
    row_count=0;previous_command=None;command_gaps={0:Counter(),1:Counter()}
    for row in reader:
        row_count+=1;name=row['event'];require(name in allowed,f'{label}: unexpected event {name}')
        generation=int(row['frame_generation']);cycle=int(row['cycle']);owner=int(row['owner_generation'])
        client=int(row['client']);writing=int(row['write']);address=int(row['address'])
        require(generation in gens and int(row['ps'])==cycle*10000-5000,f'{label}: trace source/cycle identity malformed')
        counts[name]+=1;pergen[generation][name]+=1
        if name=='command':
            require(owner==0 and client in range(4) and writing in (0,1) and address%8==0,f'{label}: raw command owner/address malformed')
            if previous_command is not None:
                previous_cycle,previous_write=previous_command;gap=cycle-previous_cycle
                require(gap>=(16 if previous_write else 18),f'{label}: serialized command predecessor gap below frozen service bound')
                command_gaps[previous_write][gap]+=1
            previous_command=(cycle,writing)
            if tm[generation]['admission_cycle']<=cycle<=tm[generation]['commit_ack_cycle']:
                actual_commands[(generation,client,writing)]+=1
                if client==3 and not writing:physical_prefetch[(generation,address)]+=1
            continue
        require(owner==generation,f'{label}: tagged event owner mismatch {name}')
        if name=='prefetch_epoch_done':
            require(generation not in done,f'{label}: duplicate epoch-done event');done[generation]=cycle;continue
        bank,plane,tile=int(row['bank']),int(row['plane']),int(row['tile_index'])
        require(bank in range(3) and plane in range(3) and 0<=tile<(5400 if plane==0 else 1350),f'{label}: tagged coordinate outside bounds')
        key=(generation,plane,tile)
        if name in block_names:
            base_address=(0x080000,0x480000,0x880000)[bank]+(0,172800,216000)[plane]+tile*32
            require(base_address<=address<base_address+32 and (address-base_address)%8==0,f'{label}: block address disagrees with captured coordinate')
            key+=(int((address-base_address)//8),)
        require(key not in events[name],f'{label}: duplicate tagged event {name} {key}')
        events[name][key]=(cycle,bank,address)
    require(row_count==data['summary'].get('trace_rows') and row_count<=2000000,f'{label}: trace row count/bound mismatch')
    require(dict(counts)==meta.get('event_counts'),f'{label}: trace event counts mismatch')
    coordinates={(p,t) for p in range(3) for t in range(5400 if p==0 else 1350)}
    def hidden(plane,tile):
        x,y=tile%(90 if plane==0 else 45),tile//(90 if plane==0 else 45)
        return (((3<=x<22 and (7<=y<9 or 11<=y<13)) or (21<=x<61 and 45<=y<48) or (21<=x<51 and 49<=y<51)) if plane==0 else (11<=x<30 and y==23))
    reference_coordinates={k for k in coordinates if not hidden(*k)}
    require(len(reference_coordinates)==7806,'Fixed native profile lookup mask arithmetic mismatch')
    derived_frames=[]
    for generation in sorted(gens):
        frame=bygen[generation];key_frame=bool(frame['key']);pref=prefs[generation]
        def keyed(name):return {k[1:]:v for k,v in events[name].items() if k[0]==generation}
        wr,wd,backend=keyed('tile_write_request'),keyed('tile_write_done'),keyed('backend_write_done')
        require(set(wr)==set(wd)==set(backend)==coordinates,f'{label}: canonical/backend event identity coverage incomplete')
        candidate_banks={v[1] for v in wr.values()}|{v[1] for v in wd.values()}|{v[1] for v in backend.values()}
        require(len(candidate_banks)==1,f'{label}: candidate bank inconsistent through backend/retirement')
        candidate_bank=next(iter(candidate_banks))
        require(all(wr[k][0]<backend[k][0]<=wd[k][0]<tm[generation]['validated_ready_cycle'] for k in coordinates),f'{label}: actual backend/retirement/validation ordering violated')
        first,req,rsp=keyed('ref_first_valid'),keyed('ref_request'),keyed('ref_response')
        require(set(first)==set(req)==set(rsp)==(set() if key_frame else reference_coordinates),f'{label}: offered/accepted reference lookup identities differ')
        require(all(first[k][0]<=req[k][0]<rsp[k][0]<=wr[k][0] for k in req),f'{label}: offered/request/response/write causal order violated')
        fills=keyed('prefetch_fill');raw_req=keyed('prefetch_raw_request');snap=keyed('prefetch_snapshot');commit=keyed('prefetch_block_commit')
        expected_block_count=32400 if data['prefetch']==3 and not key_frame else 0
        require(len(raw_req)==len(snap)==len(commit)==expected_block_count,f'{label}: wide block event coverage count mismatch')
        if expected_block_count:
            block_keys={(p,t,b) for p,t in coordinates for b in range(4)}
            require(set(raw_req)==set(snap)==set(commit)==block_keys,f'{label}: wide block identities incomplete')
            require(all(raw_req[k][0]<snap[k][0]<commit[k][0] and raw_req[k][1:]==snap[k][1:]==commit[k][1:] for k in block_keys),f'{label}: captured wide-block identity/order mismatch')
            require(all(commit[(p,t,3)][0]==fills[(p,t)][0] for p,t in coordinates),f'{label}: full tile publication does not match its final block commit')
            for p,t,b in block_keys:
                require(physical_prefetch[(generation,raw_req[(p,t,b)][2])]==1,f'{label}: captured block has no unique context-window physical read address')
        enabled=bool(data['prefetch']) and not key_frame
        require(set(fills)==(coordinates if enabled else set()),f'{label}: prefetch full-tile publication coverage mismatch')
        if enabled:
            ref_banks={v[1] for table in (first,req,rsp,fills,raw_req,snap,commit) for v in table.values()}
            require(len(ref_banks)==1 and candidate_bank not in ref_banks,f'{label}: immutable reference-bank translation mismatch')
            require(done.get(generation)==pref['epoch_done_cycle']<tm[generation]['validated_ready_cycle'],f'{label}: epoch done does not precede validation')
        else:require(generation not in done,f'{label}: non-prefetch source launched epoch')
        metrics=defaultdict(Counter)
        for coordinate in sorted(coordinates):
            metrics['write_accept_to_backend_done'][backend[coordinate][0]-wr[coordinate][0]]+=1
            metrics['backend_done_to_receiver_done'][wd[coordinate][0]-backend[coordinate][0]]+=1
            if coordinate in req:
                metrics['first_offer_to_lookup_accept'][req[coordinate][0]-first[coordinate][0]]+=1
                metrics['lookup_accept_to_response'][rsp[coordinate][0]-req[coordinate][0]]+=1
            if expected_block_count:
                plane,tile=coordinate
                for block in range(4):
                    k=(plane,tile,block)
                    metrics['logical_request_to_bridge_snapshot'][snap[k][0]-raw_req[k][0]]+=1
                    metrics['bridge_snapshot_to_core_commit'][commit[k][0]-snap[k][0]]+=1
                    if block:
                        previous=commit[(plane,tile,block-1)][0]
                        require(previous<raw_req[k][0],f'{label}: next block requested before previous commit')
                        metrics['previous_block_commit_to_next_request'][raw_req[k][0]-previous]+=1
                if coordinate in req:
                    require(fills[coordinate][0]<req[coordinate][0],f'{label}: reference lookup accepted before fill')
                    metrics['fill_to_first_offer'][first[coordinate][0]-fills[coordinate][0]]+=1
        derived_frames.append(dict(generation=generation,fid=frame['fid'],key=frame['key'],metrics_cycles={k:describe_histogram(v) for k,v in metrics.items()}))
        for client in range(4):
            for writing,field in ((0,'reads'),(1,'writes')):
                require(actual_commands[(generation,client,writing)]==cmd[generation][f'client{client}_{field}'],f'{label}: actual command count disagrees with per-source log')
        for name,field in [('ref_request','ref_requests'),('ref_response','ref_responses'),('tile_write_request','tile_write_requests'),('tile_write_done','tile_write_done'),('prefetch_fill','prefetch_fill_events')]:
            require(pergen[generation][name]==cmd[generation][field],f'{label}: accepted trace count disagrees with command records')
        for name,field in [('ref_first_valid','ref_first_valid'),('prefetch_raw_request','raw_requests'),('prefetch_snapshot','snapshots'),('prefetch_block_commit','block_commits'),('backend_write_done','backend_write_done')]:
            require(pergen[generation][name]==paths[generation][field],f'{label}: path trace count disagrees with source records')
    return dict(trace_rows=row_count,event_counts=dict(counts),selected_generations=sorted(gens),derived_frames=derived_frames,
        physical_command_predecessor_gaps=[dict(predecessor_write=bool(w),min_cycles=min(h),observations=sum(h.values()),all_at_least_cycles=16 if w else 18) for w,h in sorted(command_gaps.items())],
        physical_command_ownership='UNKNOWN; tagged block/command address matching is context-window evidence only')


def audit_failure(path,expected_schema):
    """Retain integrity of failures without treating them as qualified PASS runs."""
    d=read_json(path);label=str(path.relative_to(ROOT));base=path.parent
    require(d.get('schema')==expected_schema and d.get('status')=='FAIL_FUNCTIONAL'
            and isinstance(d.get('wall_seconds'),(int,float)) and d['wall_seconds']>0
            and isinstance(d.get('failure'),str) and d['failure'],f'{label}: completed failure lacks terminal reason')
    if d.get('source_snapshot'):
        archive=check_snapshot(d,label,base);check_pin_map(d.get('source_sha256'),label,archive)
    commands=d.get('commands');require(isinstance(commands,list),f'{label}: failed-attempt commands missing')
    for c in commands:
        p=safe_artifact_file(c.get('log'),base,label)
        require(sha256(p)==c.get('sha256') and isinstance(c.get('timed_out'),bool),f'{label}: retained failure log/status identity mismatch')
    return f'retained completed failure: {label}; not a qualified run'


def audit_comparison(path,audited,failed,pending):
    d=read_json(path);label=str(path.relative_to(ROOT))
    require(d.get('schema')=='cu81-selected-simulated-comparison-v1',f'{label}: comparison schema mismatch')
    for rel,pin in d.get('source_sha256',{}).items():
        require(sha256(safe_repo_file(rel,label))==pin,f'{label}: comparison input hash mismatch {rel}')
    require(d.get('source_sha256'),f'{label}: no comparison pins')
    by_config=defaultdict(list)
    for item in audited:
        a=item['data'];by_config[(a['cohort'],a['prefetch'],a['requested_frames'],a['arrival_mode'],a['tac_ns'])].append(item)
    selected={k:max(v,key=lambda a:a['path'].parent.name) for k,v in by_config.items()}
    rows=d.get('selected_runs');require(isinstance(rows,list) and len(rows)==len(selected),f'{label}: selected result cardinality mismatch')
    seen=set()
    for row in rows:
        p=safe_repo_file(row.get('path'),label);item=next((x for x in selected.values() if x['path']==p),None)
        require(item is not None and p not in seen,f'{label}: selection is not unique/latest');seen.add(p)
        a=item['data'];t=a['timings'];v=[x['validated_decode_model_cycles']*1e-5 for x in t]
        starts=[x['first_complete_raster_start_ps'] for x in t]
        expected=dict(cohort=a['cohort'],prefetch=a['prefetch'],sources=len(t),mode=a['arrival_mode'],tac_ns=a['tac_ns'],
          full_history=len(t)==a['cohort_available_frames'],validated_ms=stat_values(v),
          transaction_service_ms=stat_values([x['cycles']*1e-5 for x in a['frames']]),
          ingress_to_first_full_raster_end_ms=stat_values([(x['first_complete_raster_end_ps']-x['packet_complete_cycle']*10000)/1e9 for x in t]),
          finite_first_to_last_source_cadence_fps=(len(t)-1)*1e12/(starts[-1]-starts[0]),
          serial_ack_budget_passes=sum(x['met_serial_30fps_budget'] for x in t),strict_validated_under10ms_passes=sum(x['met_validated_under10ms'] for x in t),
          max_queue_ms=max(x['queue_cycles'] for x in t)*1e-5,native_pixels_checked=a['summary']['observed_pixels'],
          stream_write_accepts=sum(x['write_accepts'] for x in a.get('stream_frames',[])))
        require(all(same_values(row.get(k),value) for k,value in expected.items()),f'{label}: derived selected-run metric mismatch {p}')
    require(sorted(d.get('pending',[]))==sorted(str(p.relative_to(ROOT)) for p in pending),f'{label}: pending checkpoints differ')
    require(sorted(x['path'] for x in d.get('retained_completed_failures',[]))==sorted(str(p.relative_to(ROOT)) for p in failed),f'{label}: retained failure list differs')
    controls=[];pairs=[];histories=[]
    for cohort in (0,3):
        k=(cohort,2,4,'fixed30',2)
        if k in selected:
            olds=sorted((ROOT/f'fpga/experiments/cu66-v80/system/cohort{cohort}-frames4-fixed30-prefetch2-tac2').glob('attempt*/results.json'))
            old_path=olds[-1];old=read_json(old_path);new=selected[k]
            require(old.get('status')==PASS and d['source_sha256'].get(str(old_path.relative_to(ROOT)))==sha256(old_path),f'{label}: frozen mode2 control not pinned/pass')
            controls.append(dict(kind='V80_vs_V81_mode2',cohort=cohort,before=str(old_path.relative_to(ROOT)),after=str(new['path'].relative_to(ROOT)),exact_fields=compare_exact_fields(old,new['data'])))
        keys=[(cohort,mode,4,'fixed30',2) for mode in (2,3)]
        if all(k in selected for k in keys):
            chosen=[selected[k] for k in keys];c,w=[x['data'] for x in chosen]
            require(c['source_sha256']==w['source_sha256'],f'{label}: bounded control and wide producer sources differ')
            values=[]
            for a,b in zip(c['timings'],w['timings']):
                require((a['fid'],a['packet_complete_cycle'])==(b['fid'],b['packet_complete_cycle']),f'{label}: bounded immutable release/identity mismatch')
                values.append(dict(fid=a['fid'],control_validated_ms=a['validated_decode_model_cycles']*1e-5,wide_validated_ms=b['validated_decode_model_cycles']*1e-5,wide_minus_control_ms=(b['validated_decode_model_cycles']-a['validated_decode_model_cycles'])*1e-5))
            pairs.append(dict(cohort=cohort,runs=[str(x['path'].relative_to(ROOT)) for x in chosen],frames=values,same_immutable_releases=True,same_producer_sources=True))
    require(same_values(d.get('control_equivalence'),controls),f'{label}: control equivalence mismatch')
    require(same_values(d.get('bounded_paired_comparisons'),pairs),f'{label}: bounded comparison mismatch')
    for cohort,n in EXPECTED_COHORTS.items():
        k=(cohort,3,n,'fixed30',2)
        if k not in selected:continue
        new=selected[k];old_path=sorted((ROOT/f'fpga/experiments/cu66-v80/system/cohort{cohort}-framesfull-fixed30-prefetch2-tac2').glob('attempt*/results.json'))[-1]
        old=read_json(old_path);require(old.get('status')==PASS and len(old['timings'])==len(new['data']['timings'])==n,f'{label}: full control scope mismatch')
        require(d['source_sha256'].get(str(old_path.relative_to(ROOT)))==sha256(old_path),f'{label}: full control identity unpinned')
        deltas=[]
        for a,b in zip(old['timings'],new['data']['timings']):
            require((a['fid'],a['packet_complete_cycle'])==(b['fid'],b['packet_complete_cycle']),f'{label}: full-history immutable release/identity mismatch')
            deltas.append((b['validated_decode_model_cycles']-a['validated_decode_model_cycles'])*1e-5)
        histories.append(dict(cohort=cohort,sources=n,control=str(old_path.relative_to(ROOT)),wide=str(new['path'].relative_to(ROOT)),validated_delta_ms=stat_values(deltas),improved=sum(x<0 for x in deltas),equal=sum(x==0 for x in deltas),regressed=sum(x>0 for x in deltas)))
    require(same_values(d.get('full_history_comparisons'),histories) and d.get('full_history_sources')==sum(h['sources'] for h in histories),f'{label}: full-history comparison mismatch')
    return f'comparison: {len(rows)} latest runs, {len(controls)} exact V80 mode2 controls, {len(pairs)} bounded pairs and {sum(h["sources"] for h in histories)} full-history sources independently recomputed'



def describe_histogram(hist):
    n=sum(hist.values());items=sorted(hist.items())
    positions=((n-1)//2,n//2);middle=[]
    for position in positions:
        before=0
        for value,count in items:
            if before+count>position:middle.append(value);break
            before+=count
    require(len(middle)==2,'Path metric histogram is empty')
    return dict(samples=n,min=items[0][0],median=sum(middle)/2,max=items[-1][0],exact_histogram={str(k):v for k,v in items})


def audit_path_analysis(path,audited):
    d=read_json(path);label=str(path.relative_to(ROOT))
    require(d.get('schema')=='cu81-authenticated-path-analysis-v1' and d.get('status')=='PASS'
            and d.get('memory_period_ps')==10000
            and d.get('script_sha256')==sha256(ROOT/'scripts/cu66-v81/analyze_path.py'),f'{label}: path analysis schema/script mismatch')
    expected=[]
    for cohort in (0,3):
        for mode in (2,3):
            matches=[x for x in audited if x['data']['cohort']==cohort and x['data']['prefetch']==mode and x['data']['requested_frames']==4 and x['data']['arrival_mode']=='fixed30' and x['data']['tac_ns']==2 and x['trace_audit']]
            require(matches,f'{label}: missing independently audited completed bounded path trace')
            item=max(matches,key=lambda x:x['path'].parent.name);a=item['data'];t=item['trace_audit']
            expected.append(dict(path=str(item['path'].relative_to(ROOT)),results_sha256=sha256(item['path']),mode=mode,cohort=cohort,
                trace_sha256=a['trace']['sha256'],trace_raw_sha256=a['trace']['raw_sha256'],event_counts=t['event_counts'],frames=t['derived_frames']))
    require(same_values(d.get('runs'),expected),f'{label}: path histogram/count/identity derivation mismatch')
    return f'path analysis: four input traces bound; all per-tile and per-block metric histograms independently recomputed'


def audit_interrupted_checkpoints(pending):
    path=ROOT/'fpga/experiments/cu66-v81/interrupted-campaigns/20261106T0420-interruption.json'
    if not path.is_file():return set()
    d=read_json(path);label=str(path.relative_to(ROOT));rows=d.get('attempts',[])
    require(d.get('schema')=='cu81-interrupted-campaign-note-v1' and len(rows)==4,f'{label}: interruption note schema/count mismatch')
    expected={
        0:('20261106T040428626449Z-70f172b0',59),1:('20261106T040428626499Z-519e9702',58),
        2:('20261106T040428626473Z-5e20e2fe',59),3:('20261106T040428626485Z-4d37876f',55)}
    interrupted=set()
    for row in rows:
        p=safe_repo_file(row.get('path'),label);a=read_json(p);cohort=a.get('cohort')
        require(cohort in expected,f'{label}: unexpected interrupted cohort')
        stamp,passes=expected[cohort]
        rel=f'fpga/experiments/cu66-v81/system/cohort{cohort}-framesfull-fixed30-prefetch3-tac2/attempt-{stamp}/results.json'
        require(row['path']==rel and p in pending and p not in interrupted and row.get('qualified') is False
                and row.get('checkpoint_status')==a.get('status')=='FAIL_FUNCTIONAL'
                and row.get('recorded_source_passes')==passes,f'{label}: interrupted checkpoint identity/status mismatch')
        body=(p.parent/'run.log').read_text()
        require(len(re.findall(r'^SYSTEM_FRAME_PASS ',body,re.M))==passes
                and not re.search(r'^SYSTEM_PASS ',body,re.M),f'{label}: interrupted partial log scope mismatch')
        interrupted.add(p)
    return interrupted


def audit_profile_analysis(path,audited):
    d=read_json(path);label=str(path.relative_to(ROOT));pins=d.get('source_sha256',{})
    require(d.get('schema')=='cu81-observed-profile-and-address-reuse-v1' and pins,f'{label}: profile schema/pins missing')
    for rel,pin in pins.items():require(sha256(safe_repo_file(rel,label))==pin,f'{label}: profile input hash mismatch {rel}')
    require('scripts/cu66-v81/analyze_profile.py' in pins,f'{label}: profile analyzer unbound')
    runs=d.get('runs',[]);require(len(runs)==4,f'{label}: expected four bounded profile inputs')
    seen=set()
    for row in runs:
        p=safe_repo_file(row.get('result'),label);matches=[x for x in audited if x['path']==p]
        require(len(matches)==1 and row['result'] in pins,f'{label}: profile input lacks audited result binding')
        item=matches[0];a=item['data'];key=(a['cohort'],a['prefetch']);seen.add(key)
        require((row.get('cohort'),row.get('mode'))==key and a['requested_frames']==4
                and pins.get(a['trace']['path'])==a['trace']['sha256']
                and same_values(row.get('physical_command_predecessor_gaps'),item['trace_audit']['physical_command_predecessor_gaps']),f'{label}: profile command-gap/input scope mismatch')
        require(len(row.get('frames',[]))==4,f'{label}: profile source count mismatch')
        for r,f,t,c in zip(row['frames'],a['frames'],a['timings'],a['command_frames']):
            joint={f'{b}{v}{u}':f[f'base{b}_tile{v}_aux{u}_cycles'] for b in range(2) for v in range(2) for u in range(2)}
            expected=dict(fid=f['fid'],key=f['key'],generation=f['generation'],transaction_cycles=f['cycles'],validated_ms=t['validated_decode_model_cycles']*1e-5,queue_ms=t['queue_cycles']*1e-5,
                receiver_stage_cycles={str(s):f[f'stage{s}_cycles'] for s in range(16)},joint_busy_cycles=joint,per_client_commands=c,
                physical_commands=sum(c[f'client{i}_{rw}'] for i in range(4) for rw in ('reads','writes')),
                base_busy_percent=100*sum(v for k,v in joint.items() if k[0]=='1')/f['cycles'],tile_busy_percent=100*sum(v for k,v in joint.items() if k[1]=='1')/f['cycles'],base_and_tile_busy_percent=100*sum(v for k,v in joint.items() if k[:2]=='11')/f['cycles'],
                p0_read_service_cycles=f['p0_read_service_cycles'],p0_all_service_cycles=f['p0_service_cycles'],p0_read_wait_cycles=f['p0_read_wait_cycles'],p0_read_cache_hits=f['p0_cache_hits'],p0_read_cache_misses=f['p0_cache_misses'])
            require(all(same_values(r.get(k),v) for k,v in expected.items()) and r.get('physical_payload_bytes')==expected['physical_commands']*16,f'{label}: profile source metric mismatch')
    require(seen=={(0,2),(0,3),(3,2),(3,3)},f'{label}: duplicate/missing profile case')
    diagnostics=d.get('readonly_diagnostic_runs',[]);require(len(diagnostics)==2 and {r.get('cohort') for r in diagnostics}=={0,3},f'{label}: expected two completed read-only diagnostic runs')
    for row in diagnostics:
        p=safe_repo_file(row.get('result'),label);item=audit_system(p);a=item['data'];binding=a.get('control_equivalence',{})
        require(row['result'] in pins and row.get('cohort')==a['cohort'] and a['cohort'] in (0,3)
                and row.get('control_equivalence')==binding,f'{label}: diagnostic result binding mismatch')
        control=safe_repo_file(binding.get('path'),label);original=read_json(control)
        require(sha256(control)==binding.get('sha256') and any(x['path']==control for x in audited),f'{label}: diagnostic control not audited/hash bound')
        for name in ('frames','timings'):
            require(len(a[name])==len(original[name])==4 and all({k:v for k,v in x.items() if k!='native_hud_prepare_wall_ns'}=={k:v for k,v in y.items() if k!='native_hud_prepare_wall_ns'} for x,y in zip(a[name],original[name])),f'{label}: read-only diagnostic changed original {name}')
        require(a['summary']=={**original['summary'],'trace_rows':a['summary']['trace_rows']},f'{label}: read-only diagnostic summary changed')
        body=(p.parent/'run.log').read_text();profiles=[parse_fields(x) for x in body.splitlines() if x.startswith('PROFILE_FRAME ')]
        require(profiles==a.get('profile_frames') and len(profiles)==len(row.get('frames',[]))==4,f'{label}: profile raw log/JSON cardinality mismatch')
        for q,f,r in zip(profiles,a['frames'],row['frames']):
            require(q['fid']==f['fid']==r.get('fid') and q['generation']==f['generation']==r.get('generation') and r.get('raw_profile')==q,f'{label}: diagnostic profile row mismatch')
            expected=dict(transaction_cycles=f['cycles'],base_wait_idct_cycles=q['ts5'],inverse_arithmetic_state_cycles=sum(q[f'idct{i}'] for i in range(1,9)),inverse_output_state_cycles=q['idct9'],inverse_output_valid_not_ready_cycles=q['flag5'],write_stage_with_prior_write_pending_cycles=q['flag8'],write_stage_rows_not_ready_cycles=q['flag9'],controller_idle_cycles=q['controller5'],controller_waiting_cycles=q['controller4'],bridge_idle_cycles=q['bridge0'])
            require(all(r.get(k)==v for k,v in expected.items()),f'{label}: diagnostic derived state-count mismatch')
            for prefix,n in (('fs',16),('ts',16),('idct',16),('controller',16),('bridge',8),('hash_fill',8),('hash_core',4),('ts_wp',32),('idct_wp',32)):
                require(sum(q[f'{prefix}{i}'] for i in range(n))==f['cycles'],f'{label}: diagnostic state bins do not partition cycles')
    floor=d.get('conditional_serialized_delta_floor',{})
    expected=dict(physical_reads=35040,physical_writes=35040,min_next_accept_after_read_cycles=18,min_next_accept_after_write_cycles=16,all_but_last_command_lower_bound_cycles=35040*18+35040*16-18,assumed_clock_mhz=100,lower_bound_ms=(35040*18+35040*16-18)*1e-5)
    require(all(same_values(floor.get(k),v) for k,v in expected.items()) and 'not formal proof or physical timing signoff' in floor.get('scope',''),f'{label}: conditional serialized floor arithmetic/scope mismatch')
    return 'profile analysis: four bounded input hashes/gaps and two read-only diagnostic runs bound; 11.91342ms conditional service arithmetic checked (not formal/physical proof)'


def audit_tile_reuse(path):
    d=read_json(path);label=str(path.relative_to(ROOT));base=path.parent
    require(d.get('schema')=='cu81-exact-native-tile-reuse-v1' and d.get('status')=='PASS_EXACT_NATIVE_TILE_EQUALITY_SCREEN'
            and d.get('native_only') is True and d.get('rtl_or_protocol_implemented') is False,f'{label}: native tile-screen scope/status mismatch')
    archive=check_snapshot(d,label,base);check_pin_map(d.get('source_sha256'),label,archive);logs=check_commands(d,label,base)
    byname={Path(k).name:v for k,v in logs.items()};body=byname.get('run.log','')
    require(body.count('TILE_REUSE_NATIVE_PASS ')==1 and 'FAIL' not in body and re.findall(r'\b[0-9a-f]{64}\b',byname.get('binary.log',''))==[d.get('binary_sha256')],f'{label}: native terminal/binary hash mismatch')
    rows=[json.loads(line) for line in body.splitlines() if line.startswith('{')]
    frames_path=safe_repo_file(d.get('frames_path'),label);frames=read_json(frames_path)
    require(sha256(frames_path)==d.get('frames_sha256') and len(rows)==len(frames)==457 and d.get('sources')==457
            and d.get('key_sources')==20 and d.get('delta_sources')==437,f'{label}: native source cardinality/hash mismatch')
    counts=Counter();eligible=0;keys=0
    for row,f in zip(rows,frames):
        cohort=row['cohort'];require(cohort in EXPECTED_COHORTS and row['ordinal']==counts[cohort],f'{label}: native cohort ordering mismatch');counts[cohort]+=1
        require(all(f.get(k)==row[k] for k in ('cohort','ordinal','fid','key','comparable')),f'{label}: native frame identity mismatch')
        total=0;hidden=0;keys+=bool(row['key'])
        require([p['plane'] for p in row['planes']]==[0,1,2],f'{label}: native plane set mismatch')
        for p in row['planes']:
            n=5400 if p['plane']==0 else 1350;mask=bytes.fromhex(p['same_mask_u8_lsb_hex']);same=sum(b.bit_count() for b in mask)
            require(p['tiles']==n and len(mask)==(n+7)//8 and same==p['same_hidden']+p['same_visible']
                    and all(not(mask[i//8]>>(i%8)&1) for i in range(n,len(mask)*8))
                    and (row['comparable'] or same==0),f'{label}: native equality mask/count mismatch')
            total+=same;hidden+=p['same_hidden']
        elidable=0 if row['key'] else total*4;eligible+=0 if row['key'] else total
        require(f.get('same_tiles')==total and f.get('same_hidden')==hidden and f.get('same_visible')==total-hidden
                and f.get('hypothetical_elidable_canonical_BL8_writes')==elidable
                and f.get('hypothetical_remaining_data_BL8_writes')==35040-elidable
                and f.get('metadata_commands_priced') is False and f.get('latency_savings_claimed') is False,f'{label}: native hypothetical arithmetic/scope mismatch')
    h=d.get('hypothetical',{})
    require(dict(counts)==EXPECTED_COHORTS and keys==20 and h.get('eligible_delta_equal_tiles')==eligible
            and h.get('elidable_canonical_BL8_writes')==eligible*4
            and all(h.get(k) is False for k in ('metadata_commands_priced','reference_read_reduction_claimed','latency_savings_claimed')),f'{label}: native aggregate arithmetic/scope mismatch')
    return f'native-only tile reuse: 457 source masks/log/result bindings and {eligible*4} hypothetical elidable BL8 writes checked; no RTL/protocol or latency claim'

def main():
    reports=[];audited=[];failed=[];pending=[];fault_failed=[]
    for name in ('monitor.hpp','monitor_tb.cpp'):
        require((SYSTEM_ROOT/name).read_bytes()==(ROOT/'fpga/experiments/cu66-v79/system'/name).read_bytes(),f'Frozen observer bytes changed: {name}')
    for p in sorted(SYSTEM_ROOT.glob('monitor-tests/attempt*/results.json')):reports.append(audit_observer(p))
    for p in sorted(SYSTEM_ROOT.glob('cohort*/attempt*/results.json')):
        d=read_json(p)
        require(d.get('schema')==V81_SCHEMA,f'{p.relative_to(ROOT)}: unknown system schema')
        if 'wall_seconds' not in d:pending.append(p);continue
        if d.get('status')==PASS:audited.append(audit_system(p))
        else:failed.append(p);reports.append(audit_failure(p,V81_SCHEMA))
    for p in sorted((ROOT/'fpga/experiments/cu66-v81/campaigns').glob('prefetch3-*/results.json')):
        reports.append(audit_campaign(p,audited))
    for p in sorted(SYSTEM_ROOT.glob('faults/attempt*/results.json')):
        d=read_json(p)
        if 'wall_seconds' not in d:continue
        if d.get('status')=='PASS_ACTUAL_REJECT_ABORT_RETAIN_AND_RECOVER':reports.append(audit_fault(p))
        else:fault_failed.append(p);reports.append(audit_failure(p,'cu81-actual-system-fault-v1'))
    path_analysis=ROOT/'fpga/experiments/cu66-v81/path-analysis/results.json'
    if path_analysis.is_file():reports.append(audit_path_analysis(path_analysis,audited))
    profile_analysis=ROOT/'fpga/experiments/cu66-v81/profile-analysis/results.json'
    if profile_analysis.is_file():reports.append(audit_profile_analysis(profile_analysis,audited))
    for p in sorted((ROOT/'fpga/experiments/cu66-v81/tile-reuse').glob('attempt*/results.json')):
        reports.append(audit_tile_reuse(p))
    interrupted=audit_interrupted_checkpoints(pending)
    comparison=ROOT/'fpga/experiments/cu66-v81/comparison.json'
    if comparison.is_file():reports.append(audit_comparison(comparison,audited,failed,pending))
    require(audited,'No completed V81 system PASS evidence exists yet')
    print('V81_EVIDENCE_AUDIT_PASS')
    print('Functional correctness, modeled ACK budget, strict validated latency and physical streaming qualification are separate.')
    print(f'completed_system_pass={len(audited)} retained_system_fail={len(failed)} retained_fault_fail={len(fault_failed)} active_or_unclassified_system_checkpoints={len(pending)-len(interrupted)} interrupted_historical_system_checkpoints={len(interrupted)} total_unqualified_system_checkpoints={len(pending)}')
    for report in reports:print('- '+report)
    for item in audited:
        d=item['data'];t=d['timings'];trace=item['trace_audit']
        print(f'- {item["path"].parent.parent.name}/{item["path"].parent.name}: functional=PASS serial30={sum(x["met_serial_30fps_budget"] for x in t)}/{len(t)} under10={sum(x["met_validated_under10ms"] for x in t)}/{len(t)} trace_rows={trace["trace_rows"] if trace else 0} physical_fps_proven=0')
    for p in pending:print(f'- {"interrupted historical" if p in interrupted else "active or unclassified"} checkpoint is not completed evidence: {p.relative_to(ROOT)}')


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print(f'V81_EVIDENCE_AUDIT_FAIL {exc}',file=sys.stderr);raise SystemExit(1)
