#!/usr/bin/env python3
"""Fail-closed integrity and functional audit for retained V80 evidence."""
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
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM_ROOT = ROOT / "fpga/experiments/cu66-v80/system"
V80_SCHEMA = "cu80-integrated-prefetch-system-v1"
PASS = "PASS_ACTUAL_DECODE_CANONICAL_AND_NATIVE_DISPLAY"
EXPECTED_COHORTS = {0: 119, 1: 119, 2: 119, 3: 100}
EXPECTED_TRACE_EVENTS = {"command", "tile_write_request", "tile_write_done", "prefetch_fill",
                         "ref_request", "ref_response", "prefetch_epoch_done"}
MUTABLE_PREFIXES = ("fpga/experiments/cu66-v80/", "scripts/cu66-v80/")
HASH_RE = re.compile(r"[0-9a-f]{64}")


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
                    f"{label}: mutable V80 source missing/mismatched in archived snapshot: {relpath}")
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


def audit_trace(data, label, base, frames, timings, prefetch_rows, command_rows):
    trace = data.get("trace")
    require(isinstance(trace, dict), f"{label}: trace metadata missing")
    path = safe_artifact_file(trace.get("path"), base, label)
    compressed = path.read_bytes()
    require(HASH_RE.fullmatch(str(trace.get("sha256"))) is not None
            and sha256_bytes(compressed) == trace["sha256"], f"{label}: compressed trace hash mismatch")
    try:
        raw = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise ValueError(f"{label}: invalid gzip trace: {exc}") from exc
    require(len(raw) == trace.get("raw_bytes") and sha256_bytes(raw) == trace.get("raw_sha256"),
            f"{label}: raw trace size/hash mismatch")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
        expected_header = ["cycle", "ps", "frame_generation", "event", "owner_generation",
                           "client", "write", "address", "bank", "plane", "tile_index"]
        require(reader.fieldnames == expected_header, f"{label}: trace header mismatch")
        counts = Counter()
        event_by_gen = {}
        rows = 0
        tile_requests, tile_done = {}, {}
        prefetch_fill = Counter()
        prefetch_done_cycles = {}
        timing_by_gen = {item["generation"]: item for item in timings}
        command_counts, command_gaps = Counter(), {}
        command_previous, global_previous = {}, {}
        for row in reader:
            rows += 1
            event = row["event"]
            counts[event] += 1
            generation = int(row["frame_generation"])
            cycle = int(row["cycle"])
            require(int(row["ps"]) == cycle*10000-5000,
                    f"{label}: trace cycle/ps conversion mismatch")
            event_by_gen.setdefault(generation, Counter())[event] += 1
            owner = int(row["owner_generation"])
            if event in ("tile_write_request", "tile_write_done"):
                index = (int(row["plane"]), int(row["tile_index"]))
                require(owner == generation, f"{label}: tile write ownership mismatch")
                target = tile_requests if event == "tile_write_request" else tile_done
                target.setdefault(generation, []).append((index, cycle))
            if event == "prefetch_fill":
                prefetch_fill[generation] += 1
            if event == "prefetch_epoch_done":
                require(owner == generation and generation not in prefetch_done_cycles,
                        f"{label}: duplicate or misowned prefetch epoch-done event")
                prefetch_done_cycles[generation] = cycle
            if event == "command":
                client, writing = int(row["client"]), int(row["write"])
                require(owner == 0 and client in range(4) and int(row["address"])%8 == 0,
                        f"{label}: raw SDRAM command ownership/address malformed")
                timing = timing_by_gen.get(generation)
                require(timing is not None, f"{label}: command belongs to unknown source generation")
                scopes = ["context_window"]
                if timing["admission_cycle"] <= cycle <= timing["commit_ack_cycle"]:
                    scopes.append("admission_through_ACK")
                for scope in scopes:
                    groups = (f"client{client}_{'write' if writing else 'read'}",
                              f"client{client}_all", "all_clients")
                    for group in groups:
                        key = (generation, scope, group)
                        command_counts[key] += 1
                        previous = command_previous.get(key)
                        if previous is not None:
                            command_gaps.setdefault(key, Counter())[cycle-previous] += 1
                        command_previous[key] = cycle
                    if scope == "admission_through_ACK":
                        previous = global_previous.get(generation)
                        if previous is not None:
                            prev_cycle, prev_client, prev_write = previous
                            group = f"endpoint_pair_{prev_client}{'W' if prev_write else 'R'}_to_{client}{'W' if writing else 'R'}"
                            key = (generation, scope, group)
                            command_gaps.setdefault(key, Counter())[cycle-prev_cycle] += 1
                        global_previous[generation] = (cycle, client, writing)
        require(rows == data.get("summary", {}).get("trace_rows"), f"{label}: trace row count mismatch")
        event_counts = trace.get("event_counts")
        require(isinstance(event_counts, dict) and set(event_counts) <= EXPECTED_TRACE_EVENTS
                and {key: counts[key] for key in EXPECTED_TRACE_EVENTS if counts[key]} == event_counts,
                f"{label}: trace event counts mismatch")
    except (UnicodeDecodeError, csv.Error, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(label):
            raise
        raise ValueError(f"{label}: malformed trace CSV: {exc}") from exc

    pref_by_gen = {item["generation"]: item for item in prefetch_rows}
    command_by_gen = {item["generation"]: item for item in command_rows}
    timing_by_gen = {item["generation"]: item for item in timings}
    data_frames = {item["generation"]: item for item in frames}
    for generation, cmd in command_by_gen.items():
        observed = event_by_gen.get(generation, Counter())
        for event, field in (("ref_request", "ref_requests"), ("ref_response", "ref_responses"),
                             ("tile_write_request", "tile_write_requests"),
                             ("tile_write_done", "tile_write_done"),
                             ("prefetch_fill", "prefetch_fill_events")):
            require(observed[event] == cmd.get(field), f"{label}: per-generation trace event {event} mismatch")
        expected_done_event = pref_by_gen[generation].get("epoch_done_events", 0) if pref_by_gen[generation].get("new_epoch") else 0
        require(observed["prefetch_epoch_done"] == expected_done_event,
                f"{label}: per-generation prefetch epoch event mismatch")
    expected_tiles = ({(0, tile) for tile in range(5400)}
                      | {(plane, tile) for plane in (1, 2) for tile in range(1350)})
    for generation, timing in timing_by_gen.items():
        req = tile_requests.get(generation, [])
        done = tile_done.get(generation, [])
        req_ids, done_ids = [x[0] for x in req], [x[0] for x in done]
        require(len(req_ids) == len(set(req_ids)) == 8100 and set(req_ids) == expected_tiles,
                f"{label}: tile write request ownership/count mismatch")
        require(len(done_ids) == len(set(done_ids)) == 8100 and set(done_ids) == expected_tiles,
                f"{label}: tile write retire ownership/count mismatch")
        req_cycle, done_cycle = dict(req), dict(done)
        require(all(req_cycle[tile] < done_cycle[tile] for tile in expected_tiles),
                f"{label}: tile completion precedes its request")
        require(max(done_cycle.values()) <= timing.get("commit_ack_cycle", -1),
                f"{label}: a tile write retirement occurs after commit ACK")
    for generation, record in pref_by_gen.items():
        if not record.get("new_epoch"):
            continue
        require(generation in timing_by_gen and generation in command_by_gen,
                f"{label}: prefetch epoch lacks matching timing/command row")
        cmd, timing = command_by_gen[generation], timing_by_gen[generation]
        fill_rows = prefetch_fill[generation]
        require(fill_rows == record.get("tiles_filled") == cmd.get("prefetch_fill_events") == 8100,
                f"{label}: actual tile prefetch fill count mismatch")
        frame = next((row for row in data_frames.values() if row.get("generation") == generation), None)
        require(frame is not None and record.get("read_commands") == 32400
                and record.get("read_beats") == 259200
                and cmd.get("client3_reads") == frame.get("p0_cache_misses") == 32400
                and cmd.get("client3_writes") == 0
                and frame.get("p0_cache_hits", -1) + frame.get("p0_cache_misses", -1)
                    == frame.get("p0_row_reads") == 32400,
                f"{label}: all-tile prefetch SDRAM and logical P0 read arithmetic mismatch")
        require(record.get("tiles_retired") == 8100
                and record.get("unused_retired") == 8100-record.get("lookups", -1),
                f"{label}: tile lookup/retirement conservation mismatch")
        require(record.get("epoch_done_events") == 1 and record.get("epoch_aborted_events") == 0
                and 0 < record.get("epoch_done_cycle", 0) < timing.get("validated_ready_cycle", 0)
                and prefetch_done_cycles.get(generation) == record.get("epoch_done_cycle")
                and record.get("busy") == 0 and record.get("fault") == 0,
                f"{label}: prefetch epoch terminal/fence evidence mismatch")
        require(counts["prefetch_epoch_done"] == sum(x.get("epoch_done_events", 0) for x in prefetch_rows),
                f"{label}: epoch-done trace/record mismatch")
        require(cmd.get("ref_requests") == record.get("lookups")
                and cmd.get("ref_responses") == record.get("lookups"),
                f"{label}: reference lookup request/response ownership mismatch")
    expected_groups = []
    for key, count in sorted(command_counts.items()):
        generation, scope, group = key
        expected_groups.append({"generation": generation, "scope": scope, "group": group,
                                "commands": count,
                                "interaccept_cycles": histogram_summary(command_gaps.get(key, Counter()))})
    return {"event_counts": dict(counts), "event_by_generation": event_by_gen,
            "command_groups": expected_groups,
            "command_gap_histograms": command_gaps, "trace_rows": rows}


def audit_system(path):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == V80_SCHEMA and data.get("status") == PASS,
            f"{label}: schema/status mismatch")
    cohort, count = data.get("cohort"), data.get("requested_frames")
    require(cohort in EXPECTED_COHORTS and isinstance(count, int) and 0 < count <= EXPECTED_COHORTS[cohort],
            f"{label}: invalid cohort/frame count")
    require(data.get("arrival_mode") == "fixed30" and data.get("tac_ns") in (2, 7)
            and data.get("variant") in ("baseline", "prefetch", "overlap")
            and data.get("prefetch") == {"baseline": 0, "prefetch": 1, "overlap": 2}[data["variant"]],
            f"{label}: variant/arrival/tAC contract mismatch")
    frames, timings, deadlines = data.get("frames"), data.get("timings"), data.get("raster_deadlines")
    prefetch_rows, command_rows = data.get("prefetch_frames"), data.get("command_frames")
    summary, perf = data.get("summary"), data.get("performance")
    require(all(isinstance(x, list) for x in (frames, timings, deadlines, prefetch_rows, command_rows))
            and isinstance(summary, dict) and isinstance(perf, dict), f"{label}: records missing")
    require(len(frames) == len(timings) == len(deadlines) == len(prefetch_rows) == len(command_rows) == count,
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
        require(packet == 108+i*100_000_000//30,
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
        if data["variant"] == "overlap":
            stream = data.get("stream_frames")
            require(isinstance(stream, list) and len(stream) == count,
                    f"{label}: overlap stream observations missing")
            for stream_row in stream:
                require(stream_row.get("generation") in gens and stream_row.get("mode") == 2
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
    if data.get("build_provenance"):
        check_pin_map(data["build_provenance"].get("source_sha256"), label+" build provenance", archive)
    logs = check_commands(data, label, base)
    run_logs = [body for rel, body in logs.items() if Path(rel).name == "run.log"]
    require(len(run_logs) == 1, f"{label}: expected one run log")
    body = run_logs[0]
    require(len(re.findall(r"^SYSTEM_PASS .+$", body, re.M)) == 1,
            f"{label}: unique terminal SYSTEM_PASS missing")
    logged_records = [("SYSTEM_FRAME_PASS ", frames), ("SYSTEM_TIMING ", timings),
                      ("SYSTEM_RASTER_DEADLINE ", deadlines), ("SYSTEM_PREFETCH ", prefetch_rows),
                      ("SYSTEM_COMMANDS ", command_rows)]
    if data.get("variant") == "overlap":
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
    require(len(binary_hashes) == len(check_hashes) == 1 and binary_hashes == check_hashes,
            f"{label}: executable hash mismatch between build and run provenance")
    trace_audit = None
    if data.get("trace"):
        selected = data.get("trace_source_ordinals", [])
        require(len(selected) <= min(count, 4), f"{label}: too many selected trace frames")
        trace_audit = audit_trace(data, label, base, frames, timings, prefetch_rows, command_rows)
    return {"path": path, "data": data, "source_count": source_count, "command_count": len(logs),
            "trace_audit": trace_audit}


def audit_pair(baseline, prefetch):
    a, b = baseline["data"], prefetch["data"]
    label = f"paired cohort={a['cohort']} frames={a['requested_frames']}"
    require((a["cohort"], a["requested_frames"], a["arrival_mode"], a["tac_ns"])
            == (b["cohort"], b["requested_frames"], b["arrival_mode"], b["tac_ns"]),
            f"{label}: pair dimensions differ")
    require([x["fid"] for x in a["frames"]] == [x["fid"] for x in b["frames"]]
            and [x["generation"] for x in a["frames"]] == [x["generation"] for x in b["frames"]],
            f"{label}: source frame pairing differs")
    require(a["status"] == b["status"] == PASS
            and a["summary"]["complete_frames"] == b["summary"]["complete_frames"] == a["requested_frames"],
            f"{label}: paired runs do not both retain complete functional passes")
    require(all(t.get("complete_rasters", 0) > 0 for t in b["timings"]),
            f"{label}: optimized run lacks complete native raster evidence")
    return label


def audit_observer(path):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu80-observer-unit-v1" and d.get("status") == "PASS"
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


def audit_auxiliary(path, kind):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("status") == "pass", f"{label}: {kind} status is not pass")
    require(d.get("physical_sdram_model") is (kind == "memory")
            and d.get("system_integration") is False and d.get("performance_claim") is False,
            f"{label}: {kind} scope markers mismatch")
    pins = d.get("source_hashes")
    require(isinstance(pins, dict) and pins, f"{label}: source_hashes missing")
    for rel, expected in pins.items():
        require(sha256(safe_repo_file(rel, label)) == expected, f"{label}: source hash mismatch {rel}")
    base = path.parent
    logs = [d.get("log")] if kind == "integration" else [c.get("log") for c in d.get("corners", [])]
    require(logs and all(isinstance(x, str) for x in logs), f"{label}: retained logs missing")
    log_bodies = []
    for rel in logs:
        log = safe_artifact_file(rel, base, label)
        require(log.stat().st_size > 0, f"{label}: empty retained log {rel}")
        log_bodies.append(log.read_text(encoding="utf-8", errors="replace"))
    if kind == "integration":
        cases = re.findall(r"^REFERENCE_PATH_CASE_PASS .+$", log_bodies[0], re.M)
        case_names = [re.search(r"^REFERENCE_PATH_CASE_PASS (\S+)", line).group(1) for line in cases]
        require(d.get("cases") == 7 and len(cases) == 10
                and Counter(case_names) == Counter({"full_tiles=8100": 1,
                    "lookahead_two_entry_ledger=1": 1, "held_reference_cancel=3": 1,
                    "candidate_completion_identity_authentication=4": 4,
                    "raw_error_drain=1": 1, "fault_clear_key_fresh_delta_recovery=1": 1,
                    "invalid_write_request_fields=4": 1})
                and len(re.findall(r"^REFERENCE_PATH_PASS cases=7 physical_sdram_model=0 system_integration=0$",
                                   log_bodies[0], re.M)) == 1,
                f"{label}: integration log case/terminal markers mismatch")
        require(d.get("cases") == 7 and d.get("full_replay") == {
            "tiles": 8100, "lookups": 7806, "unused_retirements": 294,
            "BL8_commands": 32400, "beats": 259200}, f"{label}: directed full replay arithmetic mismatch")
    else:
        require(len(d.get("corners", [])) == 2
                and {c.get("tAC_ns") for c in d["corners"]} == {2, 7}
                and all(c.get("status") == "pass" and c.get("held_stream_beats_checked") == 24
                        for c in d["corners"]), f"{label}: actual-controller corner coverage mismatch")
        for corner, body in zip(d["corners"], log_bodies):
            require(corner.get("physical_commands") == {
                "tile_write": 12, "prefetch_read": 2, "HUD_read": 1, "LCD_read": 1},
                f"{label}: controller physical-command counts mismatch")
            require(len(re.findall(r"^MEMORY_V80_PASS tac=%.1f checks=24 physical_prefetch=2 physical_aux=1 physical_lcd=1 physical_write=12 raw_abort_drains=1 invalid_address_no_command=1 held_stream_stable=1 actual_sdram_model=1$" % corner["tAC_ns"], body, re.M)) == 1,
                    f"{label}: controller run log marker mismatch for tAC={corner['tAC_ns']}")
    return label


def audit_campaign(path, audited):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu80-independent-history-campaign-v1"
            and d.get("status") == "PASS_ALL_REQUESTED_HISTORIES"
            and d.get("prefetch") == 2 and d.get("requested_sources") == 457,
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
        require(terminal == case.get("runner_result") and terminal.get("status") == "V80_SYSTEM_PASS"
                and terminal.get("frames") == EXPECTED_COHORTS[cohort],
                f"{label}: campaign terminal runner record mismatch")
        result_path = safe_repo_file(case.get("results_path"), label)
        require(HASH_RE.fullmatch(str(case.get("results_sha256"))) is not None
                and sha256(result_path) == case["results_sha256"],
                f"{label}: campaign system result hash mismatch")
        matched = [item for item in audited if item["path"] == result_path]
        require(len(matched) == 1 and matched[0]["data"].get("variant") == "overlap"
                and matched[0]["data"].get("cohort") == cohort
                and matched[0]["data"].get("requested_frames") == EXPECTED_COHORTS[cohort],
                f"{label}: campaign case lacks its independently audited full-history result")
    require(seen == set(EXPECTED_COHORTS), f"{label}: missing cohort history")
    return f"mode2 campaign: four complete histories, 457 sources; result/log/source bindings verified"


def audit_system_failure(path):
    d=read_json(path);label=str(path.relative_to(ROOT));base=path.parent
    require(d.get("schema")==V80_SCHEMA and d.get("status")=="FAIL_FUNCTIONAL"
            and isinstance(d.get("wall_seconds"),(int,float)) and d.get("wall_seconds")>0
            and isinstance(d.get("failure"),str) and d.get("failure"),
            f"{label}: completed system failure evidence incomplete")
    archive=check_snapshot(d,label,base)
    check_pin_map(d.get("source_sha256"),label,archive)
    commands=d.get("commands")
    require(isinstance(commands,list) and commands,f"{label}: failed system command records missing")
    failed=[];logs={}
    for command in commands:
        log=safe_artifact_file(command.get("log"),base,label)
        require(HASH_RE.fullmatch(str(command.get("sha256"))) is not None
                and sha256(log)==command["sha256"],f"{label}: failed system log hash mismatch")
        logs[Path(command["log"]).name]=log.read_text(encoding="utf-8",errors="replace")
        if command.get("exit_code")!=0:
            failed.append(command)
        require(not command.get("timed_out",False),f"{label}: retained failure was a timeout")
    require(len(failed)==1 and Path(failed[0]["log"]).name=="run.log"
            and "run.log" in d["failure"] and "SYSTEM_PASS " not in logs.get("run.log",""),
            f"{label}: failed run status/log marker mismatch")
    binary=re.findall(r"\b([0-9a-f]{64})\b",logs.get("binary.log",""))
    check=re.findall(r"\b([0-9a-f]{64})\b",logs.get("binary-check.log",""))
    require(len(binary)==len(check)==1 and binary==check,
            f"{label}: historical failed attempt binary hash mismatch")
    return label


def audit_fault(path):
    d = read_json(path)
    label = str(path.relative_to(ROOT))
    require(d.get("schema") == "cu80-actual-system-fault-v1"
            and d.get("status") == "PASS_ACTUAL_REJECT_ABORT_RETAIN_AND_RECOVER"
            and d.get("prefetch_mode") == 2 and d.get("observer_unit_only") is False
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
    require(read.get("generation") == abort.get("generation")
            and read.get("cycle") == abort.get("abort_cycle") == 4791483
            and read.get("address") == abort.get("abort_read_address") == 542904
            and read.get("client") == 3 and read.get("write") == 0
            and read.get("canonical_words_before_abort") == abort.get("canonical_write_words_observed")-8
            and read.get("pending_lookup") == abort.get("pending_lookup_at_abort") == 0
            and d.get("pending_lookup_at_abort") is False,
            f"{label}: coincident accepted read and abort chronology mismatch")
    require(abort.get("actual_prefetch_read_accepts", 0) > 0
            and abort.get("read_accept_coincident_abort") == 1
            and abort.get("epoch_done_events") == abort.get("epoch_aborted_events") == 1
            and abort.get("epoch_done_cycle") == abort.get("epoch_aborted_cycle") == 4791508
            and abort.get("processor_abort_calls") == 1
            and abort.get("canonical_write_words_observed") == 18592,
            f"{label}: actual partial-write abort accounting mismatch")
    releases = d.get("endpoint_releases")
    require(isinstance(releases, list) and len(releases) == 2
            and [x.get("generation") for x in releases] == [bad.get("generation"), abort.get("generation")]
            and all(x.get("successful_commit") == 0 for x in releases)
            and all(x.get("aborted_endpoint_releases") == i for i, x in enumerate(releases, 1))
            and releases[1].get("cycle") > abort.get("abort_cycle"),
            f"{label}: endpoint release timing/count mismatch")
    summary = d.get("summary", {})
    expected = {"rejected": 2, "accepted": 2, "attempts": 4, "prefetch_mode": 2,
                "no_per_source_reset": 1, "aborted_endpoint_releases": 2, "underruns": 0,
                "black_lines": 0, "admitted": 4, "endpoint_releases": 4,
                "recovery_complete_rasters": 2, "recovery_commit_calls": 2,
                "observer_unit_only": 0, "hardware_fault_injection": 0, "normal_external_abort": 1}
    require(all(summary.get(k) == v for k, v in expected.items())
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


def audit_fault_failure(path):
    d=read_json(path);label=str(path.relative_to(ROOT));base=path.parent
    require(d.get("schema")=="cu80-actual-system-fault-v1" and d.get("status")=="FAIL_FUNCTIONAL"
            and isinstance(d.get("wall_seconds"),(int,float)) and d.get("wall_seconds")>0
            and isinstance(d.get("failure"),str) and d["failure"],
            f"{label}: historical fault failure record incomplete")
    archive=check_snapshot(d,label,base)
    check_pin_map(d.get("source_sha256"),label,archive)
    check_pin_map(d.get("build_provenance",{}).get("source_sha256"),label+" build provenance",archive)
    commands=d.get("commands")
    require(isinstance(commands,list) and len(commands)>=4,f"{label}: failed fault command records missing")
    saw_failure=False
    for c in commands:
        log=safe_artifact_file(c.get("log"),base,label)
        require(HASH_RE.fullmatch(str(c.get("sha256"))) is not None and sha256(log)==c["sha256"],
                f"{label}: historical fault log hash mismatch")
        require(not c.get("timed_out",False),f"{label}: historical fault command timed out unexpectedly")
        if c.get("exit_code")!=0:
            saw_failure=True
            require(Path(c["log"]).name=="run.log" and "run.log" in d["failure"],
                    f"{label}: failed command does not match retained failure reason")
    require(saw_failure,f"{label}: completed failure record has no failed command")
    return label


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


def audit_comparison(path, audited, completed_failures, pending):
    data = read_json(path)
    label = str(path.relative_to(ROOT))
    require(data.get("schema") == "cu80-selected-simulated-comparison-v1",
            f"{label}: comparison schema mismatch")
    pins = data.get("source_sha256")
    require(isinstance(pins, dict) and pins, f"{label}: comparison source pins missing")
    for rel, expected in pins.items():
        require(HASH_RE.fullmatch(str(expected)) is not None
                and sha256(safe_repo_file(rel, label)) == expected,
                f"{label}: comparison input hash mismatch {rel}")

    by_config = {}
    for item in audited:
        d = item["data"]
        key = (d["cohort"], d["prefetch"], d["requested_frames"], d["arrival_mode"], d["tac_ns"])
        by_config.setdefault(key, []).append(item)
    selected = {key: max(rows, key=lambda x: x["path"].parent.name) for key, rows in by_config.items()}
    rows = data.get("selected_runs")
    require(isinstance(rows, list) and len(rows) == len(selected),
            f"{label}: selected-run count differs from latest complete system attempts")
    got = set()
    for row in rows:
        dpath = safe_repo_file(row.get("path"), label)
        item = next((x for x in audited if x["path"] == dpath), None)
        require(item is not None, f"{label}: selected comparison path is not an audited PASS")
        d = item["data"]
        key = (d["cohort"], d["prefetch"], d["requested_frames"], d["arrival_mode"], d["tac_ns"])
        require(key not in got and selected.get(key, {}).get("path") == dpath,
                f"{label}: selected result is duplicated or not latest {key}")
        got.add(key)
        timings, frames = d["timings"], d["frames"]
        v = [t["validated_decode_model_cycles"]*1e-5 for t in timings]
        tx = [f["cycles"]*1e-5 for f in frames]
        ingress = [(t["first_complete_raster_end_ps"]-t["packet_complete_cycle"]*10000)/1e9 for t in timings]
        starts = [t["first_complete_raster_start_ps"] for t in timings]
        cadence = (len(timings)-1)*1e12/(starts[-1]-starts[0]) if len(starts)>1 else None
        expected = {"cohort":d["cohort"],"prefetch":d["prefetch"],"sources":len(timings),
                    "mode":d["arrival_mode"],"tac_ns":d["tac_ns"],
                    "full_history":len(timings)==d["cohort_available_frames"],
                    "validated_ms":stat_values(v),"transaction_service_ms":stat_values(tx),
                    "ingress_to_first_full_raster_end_ms":stat_values(ingress),
                    "serial_ack_budget_passes":sum(t["met_serial_30fps_budget"] for t in timings),
                    "strict_validated_under10ms_passes":sum(t["met_validated_under10ms"] for t in timings),
                    "max_queue_ms":max(t["queue_cycles"] for t in timings)*1e-5,
                    "native_pixels_checked":d["summary"]["observed_pixels"],
                    "stream_write_accepts":sum(x["write_accepts"] for x in d.get("stream_frames",[]))}
        require(row.get("finite_first_to_last_source_cadence_fps") is None if cadence is None
                else near(row.get("finite_first_to_last_source_cadence_fps"), cadence),
                f"{label}: cadence derivation mismatch {key}")
        for field, value in expected.items():
            actual = row.get(field)
            if isinstance(value, dict):
                require(set(actual or {}) == set(value) and all(near(actual[k], value[k]) for k in value),
                        f"{label}: statistic mismatch {key} {field}")
            elif isinstance(value, float):
                require(near(actual, value), f"{label}: derived metric mismatch {key} {field}")
            else:
                require(actual == value, f"{label}: derived metric mismatch {key} {field}")

    expected_pending = sorted(str(p.relative_to(ROOT)) for p in pending)
    require(sorted(data.get("pending", [])) == expected_pending,
            f"{label}: pending checkpoint list mismatch")
    failures = sorted(str(p.relative_to(ROOT)) for p in completed_failures)
    require(sorted(x.get("path") for x in data.get("retained_completed_failures", [])) == failures,
            f"{label}: completed failure list mismatch")

    # Recompute bounded baseline/conservative/overlap comparisons from immutable rows.
    expected_pairs = []
    for cohort in (0, 3):
        keys = [(cohort, mode, 4, "fixed30", 2) for mode in (0, 1, 2)]
        if not all(k in selected for k in keys):
            continue
        chosen = [selected[k] for k in keys]
        base_d, conservative_d, overlap_d = [x["data"] for x in chosen]
        require(conservative_d["source_sha256"] == overlap_d["source_sha256"],
                f"{label}: overlap variant source does not match conservative control")
        paired_rows = []
        for b, c, o in zip(base_d["timings"], conservative_d["timings"], overlap_d["timings"]):
            require(b["fid"] == c["fid"] == o["fid"]
                    and b["packet_complete_cycle"] == c["packet_complete_cycle"] == o["packet_complete_cycle"],
                    f"{label}: paired source identity or release schedule mismatch")
            base_ms = b["validated_decode_model_cycles"]*1e-5
            conservative_ms = c["validated_decode_model_cycles"]*1e-5
            overlap_ms = o["validated_decode_model_cycles"]*1e-5
            paired_rows.append(dict(fid=b["fid"],baseline_validated_ms=base_ms,
                 conservative_validated_ms=conservative_ms,overlap_validated_ms=overlap_ms,
                 overlap_minus_baseline_ms=overlap_ms-base_ms,
                 overlap_minus_conservative_ms=overlap_ms-conservative_ms))
        expected_pairs.append(dict(cohort=cohort,runs=[str(x["path"].relative_to(ROOT)) for x in chosen],
                                   frames=paired_rows,same_immutable_releases=True,
                                   same_source_control_vs_overlap=True))
    actual_pairs = data.get("bounded_paired_comparisons", [])
    require(len(actual_pairs) == len(expected_pairs), f"{label}: bounded pair count mismatch")
    for actual, expected in zip(actual_pairs, expected_pairs):
        require(actual.get("cohort") == expected["cohort"] and actual.get("runs") == expected["runs"]
                and actual.get("same_immutable_releases") is True
                and actual.get("same_source_control_vs_overlap") is True
                and len(actual.get("frames",[])) == len(expected["frames"]),
                f"{label}: bounded pair binding mismatch")
        for a, e in zip(actual["frames"], expected["frames"]):
            require(all((near(a.get(k), v) if isinstance(v,float) else a.get(k)==v) for k,v in e.items()),
                    f"{label}: paired delta arithmetic mismatch")

    expected_controls = []
    legacy_key = (0, 0, 4, "fixed30", 2)
    if legacy_key in selected:
        before_path = ROOT/"fpga/experiments/cu66-v79/system/cohort0-frames4-fixed30-tac2/results.json"
        before = read_json(before_path)
        after_item = selected[legacy_key]
        exact = compare_exact_fields(before, after_item["data"])
        expected_controls.append(dict(kind="V79_vs_V80_legacy", before=str(before_path.relative_to(ROOT)),
                                      after=str(after_item["path"].relative_to(ROOT)), exact_fields=exact))
    for cohort in (0, 3):
        repeat_key = (cohort, 1, 4, "fixed30", 2)
        duplicate = sorted(by_config.get(repeat_key, []), key=lambda x:x["path"].parent.name)
        if len(duplicate) > 1:
            first,last=duplicate[0],duplicate[-1]
            record=dict(kind="original_vs_default_overlap_copy",cohort=cohort,
                        before=str(first["path"].relative_to(ROOT)),after=str(last["path"].relative_to(ROOT)),
                        exact_fields=compare_exact_fields(first["data"],last["data"]))
            if first["data"].get("trace") and last["data"].get("trace"):
                require(first["data"]["trace"].get("raw_sha256")==last["data"]["trace"].get("raw_sha256"),
                        f"{label}: repeated raw trace hash mismatch")
                record["identical_raw_trace_sha256"]=first["data"]["trace"]["raw_sha256"]
            expected_controls.append(record)
    controls=data.get("control_equivalence",[])
    require(len(controls)==len(expected_controls),f"{label}: control-equivalence count mismatch")
    for actual,expected in zip(controls,expected_controls):
        require(all(actual.get(k)==v for k,v in expected.items()),f"{label}: control-equivalence derivation mismatch")

    expected_histories=[]
    for cohort,n in ((0,119),(1,119),(2,119),(3,100)):
        key=(cohort,2,n,"fixed30",2)
        if key not in selected: continue
        new_item=selected[key]; old_path=ROOT/f"fpga/experiments/cu66-v79/system/cohort{cohort}-frames{n}-fixed30-tac2/results.json"
        old=read_json(old_path); new=new_item["data"]
        deltas=[]
        require(len(old["timings"])==len(new["timings"])==n,f"{label}: full history count mismatch")
        for before,after in zip(old["timings"],new["timings"]):
            require(before["fid"]==after["fid"] and before["packet_complete_cycle"]==after["packet_complete_cycle"],
                    f"{label}: full-history source/release pairing mismatch")
            deltas.append((after["validated_decode_model_cycles"]-before["validated_decode_model_cycles"])*1e-5)
        expected_histories.append(dict(cohort=cohort,sources=n,baseline=str(old_path.relative_to(ROOT)),
            overlap=str(new_item["path"].relative_to(ROOT)),validated_delta_ms=stat_values(deltas),
            improved=sum(x<0 for x in deltas),equal=sum(x==0 for x in deltas),regressed=sum(x>0 for x in deltas)))
    actual_histories=data.get("full_history_comparisons",[])
    require(len(actual_histories)==len(expected_histories),f"{label}: full-history comparison count mismatch")
    for actual,expected in zip(actual_histories,expected_histories):
        require(all(actual.get(k)==v for k,v in expected.items() if k!="validated_delta_ms")
                and set(actual.get("validated_delta_ms",{}))=={"min","median","max"}
                and all(near(actual["validated_delta_ms"][k],v) for k,v in expected["validated_delta_ms"].items()),
                f"{label}: full-history delta derivation mismatch")
    require(data.get("full_history_sources")==sum(x["sources"] for x in expected_histories),
            f"{label}: full-history source total mismatch")
    if not pending:
        require(data.get("full_history_sources")==457,
                f"{label}: completed comparison lacks all 457 finite-history sources")
    return f"selected comparison: {len(rows)} latest runs, all metrics/controls/pairs recomputed from pinned source JSON"


def same_values(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual)==set(expected) and all(same_values(actual[k],v) for k,v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual,list) and len(actual)==len(expected) and all(same_values(a,e) for a,e in zip(actual,expected))
    if isinstance(expected,float):
        return near(actual,expected)
    return actual==expected


def audit_trace_analysis(path, audited):
    d=read_json(path); label=str(path.relative_to(ROOT)); base=path.parent
    require(d.get("schema")=="cu80-completed-trace-analysis-v1" and d.get("clock_period_ps")==10000,
            f"{label}: trace-analysis schema/clock mismatch")
    script=ROOT/"scripts/cu66-v80/analyze_trace.py"
    require(sha256(script)==d.get("script_sha256"),f"{label}: trace-analysis script hash mismatch")
    selected=d.get("selected_completed_attempts")
    runs=d.get("runs")
    require(isinstance(selected,list) and isinstance(runs,list) and len(selected)==len(runs)==6,
            f"{label}: selected trace run count mismatch")
    by_name={str(item["path"].parent.relative_to(SYSTEM_ROOT)):item for item in audited}
    by_analysis={}
    total_rows=0;total_tiles=0;total_events=Counter()
    for name,record in zip(selected,runs):
        require(record.get("run")==name and name not in by_analysis,f"{label}: trace-run ordering/identity mismatch")
        result_name="fpga/experiments/cu66-v80/system/"+name+"/results.json"
        result_path=safe_repo_file(result_name,label)
        source=by_name.get(name)
        require(source is not None and source["path"]==result_path and source.get("trace_audit") is not None,
                f"{label}: trace selection is not a complete audited system attempt")
        data=source["data"]; ta=source["trace_audit"]
        require(record.get("status")==PASS and record.get("cohort")==data["cohort"]
                and record.get("mode")==data["prefetch"] and record.get("trace_rows")==ta["trace_rows"]
                and record.get("trace_event_counts")==ta["event_counts"]
                and record.get("trace_raw_sha256_verified")==data["trace"]["raw_sha256"]
                and record.get("producer_source_sha256")==data["source_sha256"],
                f"{label}: trace result differs from its system producer JSON")
        bound=record.get("bound_files_sha256")
        require(isinstance(bound,dict) and bound,f"{label}: bound source/log/trace pins missing")
        for rel,expected in bound.items():
            f=safe_repo_file(rel,label)
            require(HASH_RE.fullmatch(str(expected)) is not None and sha256(f)==expected,
                    f"{label}: trace bound artifact hash mismatch {rel}")
        require(bound.get(data["trace"]["path"])==data["trace"]["sha256"]
                and bound.get(result_name)==sha256(result_path)
                and bound.get(data["source_snapshot"]["path"])==data["source_snapshot"]["sha256"],
                f"{label}: trace output omitted core bound source/result artifacts")
        require(record.get("command_groups")==ta["command_groups"],
                f"{label}: independent raw-trace command gap derivation mismatch")
        for frame in record.get("frames",[]):
            generation=frame.get("generation")
            require(ta["event_by_generation"].get(generation,Counter())==frame.get("events"),
                    f"{label}: per-source trace event counts mismatch generation={generation}")
        by_analysis[name]=record
        total_rows+=ta["trace_rows"]
        total_tiles+=len(data["frames"])*8100
        total_events.update(ta["event_counts"])
    counts=d.get("data_artifact_counts",{})
    require(counts.get("runs")==6 and counts.get("trace_rows")==total_rows
            and counts.get("tile_records")==total_tiles and counts.get("event_totals")==dict(total_events),
            f"{label}: trace-analysis aggregate count mismatch")
    artifacts=d.get("artifact_sha256",{})
    for name,expected in artifacts.items():
        file=safe_artifact_file(name,base,label)
        require(sha256(file)==expected,f"{label}: trace analysis data artifact hash mismatch {name}")

    tiles_path=safe_artifact_file("tiles.csv.gz",base,label)
    try:
        with gzip.open(tiles_path,"rt",newline="") as stream:
            reader=csv.DictReader(stream)
            expected_header=["run","cohort","mode","owner_generation","fid","candidate_bank","reference_bank","plane","tile_index","hidden","fill_cycle_postedge","lookup_accept_cycle_preedge","ref_response_accept_cycle_preedge","write_accept_cycle_preedge","receiver_done_accept_cycle_preedge","previous_ordinal_receiver_done_cycle","first_context_matched_pref_command_cycle","last_context_matched_pref_command_cycle","first_context_matched_write_command_cycle","last_context_matched_write_command_cycle"]
            require(reader.fieldnames==expected_header,f"{label}: tile artifact header mismatch")
            seen=set(); pergen=Counter()
            runmeta={r["run"]:r for r in runs}
            sourced={r["run"]:by_name[r["run"]]["data"] for r in runs}
            for row in reader:
                run=row["run"]; generation=int(row["owner_generation"]); plane=int(row["plane"]); tile=int(row["tile_index"])
                require(run in runmeta and 0<=plane<3 and 0<=tile<(5400 if plane==0 else 1350),
                        f"{label}: tile artifact coordinates out of range")
                key=(run,generation,plane,tile)
                require(key not in seen,f"{label}: duplicate tile analysis record {key}");seen.add(key);pergen[(run,generation)]+=1
                meta=sourced[run]; expected_frame=next((f for f in meta["frames"] if f["generation"]==generation),None)
                require(expected_frame is not None and int(row["fid"])==expected_frame["fid"]
                        and int(row["cohort"])==meta["cohort"] and int(row["mode"])==meta["prefetch"],
                        f"{label}: tile analysis source identity mismatch")
                w=int(row["write_accept_cycle_preedge"]);done=int(row["receiver_done_accept_cycle_preedge"])
                wc0=int(row["first_context_matched_write_command_cycle"]);wcl=int(row["last_context_matched_write_command_cycle"])
                require(w<wc0<=wcl<done and int(row["hidden"]) in (0,1),
                        f"{label}: tile write/physical command chronology mismatch")
                for namecol in ("fill_cycle_postedge","lookup_accept_cycle_preedge","ref_response_accept_cycle_preedge"):
                    if row[namecol]: require(int(row[namecol])>0,f"{label}: malformed optional tile cycle")
                q=row["lookup_accept_cycle_preedge"];resp=row["ref_response_accept_cycle_preedge"];fill=row["fill_cycle_postedge"]
                require((q=="")== (resp==""),f"{label}: unmatched reference lookup/response tile record")
                if q: require(int(q)<int(resp)<=w,f"{label}: tile reference response chronology mismatch")
                if fill and q: require(int(fill)<int(q),f"{label}: prefetch fill is not before accepted lookup")
            require(len(seen)==counts.get("tile_records"),f"{label}: tile record total mismatch")
            for run,record in runmeta.items():
                data=sourced[run]
                for frame in data["frames"]:
                    generation=frame["generation"]
                    require(pergen[(run,generation)]==8100,f"{label}: incomplete per-source tile analysis {run} generation={generation}")
    except (OSError,csv.Error,EOFError) as exc:
        raise ValueError(f"{label}: cannot parse tiles artifact: {exc}") from exc

    hist_path=safe_artifact_file("histograms.csv.gz",base,label)
    histograms={}
    try:
        with gzip.open(hist_path,"rt",newline="") as stream:
            reader=csv.DictReader(stream)
            require(reader.fieldnames==["run","generation","scope","group","delta_cycles","count"],
                    f"{label}: histogram artifact header mismatch")
            for row in reader:
                key=(row["run"],int(row["generation"]),row["scope"],row["group"])
                delta,count=int(row["delta_cycles"]),int(row["count"])
                require(count>0,f"{label}: nonpositive histogram bin count")
                histograms.setdefault(key,Counter())[delta]+=count
    except (OSError,csv.Error,EOFError) as exc:
        raise ValueError(f"{label}: cannot parse histograms artifact: {exc}") from exc
    for name,record in by_analysis.items():
        source=by_name[name]["trace_audit"]
        for (generation,scope,group),expected_hist in source["command_gap_histograms"].items():
            key=(name,generation,scope,group)
            require(histograms.get(key,Counter())==expected_hist,
                    f"{label}: raw trace command gap bins mismatch {key}")
    for run,record in by_analysis.items():
        for group in record["command_groups"]:
            key=(run,group["generation"],group["scope"],group["group"])
            require(histogram_summary(histograms.get(key,Counter()))==group["interaccept_cycles"],
                    f"{label}: command gap histogram summary mismatch {key}")
        for frame in record.get("frames",[]):
            generation=frame["generation"]
            for metric,summary in frame.get("tile_metrics_cycles",{}).items():
                key=(run,generation,"tile_metric",metric)
                require(histogram_summary(histograms.get(key,Counter()))==summary,
                        f"{label}: tile metric histogram mismatch {key}")
            for metric,scope,group in (("same_tile_prefetch_interaccept_cycles","prefetch_coordinate_sequence","same_tile_successive_block_accept"),
                 ("same_tile_prefetch_interaccept_no_intervening_command_cycles","prefetch_coordinate_sequence","same_tile_successive_block_accept_no_intervening_command")):
                key=(run,generation,scope,group)
                require(histogram_summary(histograms.get(key,Counter()))==frame.get(metric),
                        f"{label}: coordinate prefetch gap histogram mismatch {key}")

    pairs=d.get("paired_actual_validated_milestones",[])
    require(len(pairs)==2,f"{label}: expected two paired actual validated milestone reports")
    for pair in pairs:
        cohort=pair["cohort"]; c1=by_analysis[pair["mode1_run"]];c2=by_analysis[pair["mode2_run"]]
        r1=by_name[pair["mode1_run"]]["data"];r2=by_name[pair["mode2_run"]]["data"]
        require(cohort in (0,3) and r1["source_sha256"]==r2["source_sha256"]
                and pair.get("identical_producer_source_pins") is True
                and pair.get("source_pin_count")==len(r1["source_sha256"])
                and pair.get("identical_packet_release_cycles") is True,
                f"{label}: paired trace-control binding mismatch")
        expected=[]
        for a,b in zip(r1["timings"],r2["timings"]):
            require(a["fid"]==b["fid"] and a["packet_complete_cycle"]==b["packet_complete_cycle"],
                    f"{label}: paired mode1/mode2 release mismatch")
            x=a["validated_decode_model_cycles"];y=b["validated_decode_model_cycles"]
            expected.append(dict(fid=a["fid"],generation=a["generation"],mode1_validated_cycles=x,
                                 mode2_minus_mode1_cycles=y-x,mode2_validated_cycles=y))
        require(pair.get("frames")==expected,f"{label}: paired milestone arithmetic mismatch")

    separate=d.get("separate_validation_evidence",[])
    for record in separate:
        file=safe_repo_file(record.get("path"),label)
        require(sha256(file)==record.get("sha256"),f"{label}: separate validation evidence hash mismatch")
        evidence=read_json(file)
        require(record.get("status")==evidence.get("status"),f"{label}: separate validation status mismatch")
    require(any("No first-valid lookup" in x for x in d.get("limits",[]))
            and any("No interaccept-count subtraction" in x for x in d.get("limits",[])),
            f"{label}: trace-analysis interpretation limits missing")
    return f"trace analysis: six bounded traces, {total_tiles} tile rows, command/tile histograms independently recomputed"


def main():
    reports = []
    for path in sorted(SYSTEM_ROOT.glob("monitor-tests/attempt-*/results.json")):
        reports.append(audit_observer(path))
    for kind, path in (("integration", ROOT/"fpga/experiments/cu66-v80/integration/results.json"),
                       ("memory", ROOT/"fpga/experiments/cu66-v80/memory/results.json")):
        if path.is_file():
            reports.append(audit_auxiliary(path, kind))

    audited, pending, finished_failures = [], [], []
    for path in sorted(SYSTEM_ROOT.glob("cohort*-frames*-fixed30-prefetch*-tac*/attempt-*/results.json")):
        data = read_json(path)
        require(data.get("schema") == V80_SCHEMA, f"{path.relative_to(ROOT)}: unknown schema")
        if data.get("status") == PASS:
            audited.append(audit_system(path))
        elif data.get("status") == "FAIL_FUNCTIONAL":
            # A runner may replace this checkpoint while its simulation is active.
            if "wall_seconds" not in data and "failure" not in data:
                pending.append(path)
            else:
                finished_failures.append(path)
                audit_system_failure(path)
        else:
            raise ValueError(f"{path.relative_to(ROOT)}: unrecognized result status {data.get('status')!r}")

    by_key = {}
    for item in audited:
        d = item["data"]
        key = (d["cohort"], d["requested_frames"], d["arrival_mode"], d["tac_ns"], d["variant"])
        by_key.setdefault(key, []).append(item)
    latest = {key: max(rows, key=lambda x: x["path"].parent.name) for key, rows in by_key.items()}
    repeatability_configs = 0
    for key, rows in by_key.items():
        if key[4] != "prefetch" or len(rows) < 2 or key[1] >= EXPECTED_COHORTS[key[0]]:
            continue
        ordered = sorted(rows, key=lambda x: x["path"].parent.name)
        reference = ordered[0]["data"]
        for candidate in ordered[1:]:
            current = candidate["data"]
            for field in ("frames", "timings", "raster_deadlines", "prefetch_frames", "command_frames"):
                left, right = reference.get(field), current.get(field)
                if field == "timings":
                    left = [{k: v for k, v in row.items() if k != "native_hud_prepare_wall_ns"} for row in left]
                    right = [{k: v for k, v in row.items() if k != "native_hud_prepare_wall_ns"} for row in right]
                require(left == right, f"repeatability mismatch for variant1 {key} field={field}")
        repeatability_configs += 1
    if repeatability_configs:
        reports.append(f"variant1 repeatability: {repeatability_configs} sampled configuration(s) retain exact simulation timing and transaction counters")
    pairs = []
    dimensions = {(k[0], k[1], k[2], k[3]) for k in latest
                  if k[1] < EXPECTED_COHORTS.get(k[0], 0)}
    for cohort, count, mode, tac in sorted(dimensions):
        baseline = latest.get((cohort, count, mode, tac, "baseline"))
        prefetch = latest.get((cohort, count, mode, tac, "prefetch"))
        if baseline is None or prefetch is None:
            continue
        require(prefetch["data"].get("trace") is not None,
                f"cohort={cohort} frames={count}: latest all-tile prefetch result lacks its selected event trace")
        pairs.append(audit_pair(baseline, prefetch))
        overlap = latest.get((cohort, count, mode, tac, "overlap"))
        if overlap is not None:
            pairs.append(audit_pair(baseline, overlap))

    # Variant 0 is a V79 behavioral control: the canonical four-frame cohort must
    # preserve V79's original transaction, timing, and first-presentation fields.
    ref = read_json(ROOT/"fpga/experiments/cu66-v79/system/cohort0-frames4-fixed30-tac2/results.json")
    control = latest.get((0, 4, "fixed30", 2, "baseline"))
    require(control is not None, "V80 baseline control: missing four-frame variant0 run")
    if control:
        require([f["fid"] for f in control["data"]["frames"]] == [f["fid"] for f in ref["frames"]],
                "V80 baseline control source identities differ from V79")
        keys = ("fid", "key", "generation", "cycles", "origin_to_ack_cycles", "actual_writes",
                "actual_write_commands", "actual_write_bus_beats", "hud_burst", "hud_write_requests",
                "hud_read_requests", "actual_read_bursts", "ACT", "PRE", "REF", "underruns",
                "processor_commit_calls", "p0_cache_hits", "p0_cache_misses", "p0_row_reads",
                "p0_wait_cycles", "p0_service_cycles", "p1_cache_hits", "p1_cache_misses",
                "p0_read_wait_cycles", "p0_read_service_cycles")
        for i, (left, right) in enumerate(zip(control["data"]["frames"], ref["frames"])):
            require(all(left.get(k) == right.get(k) for k in keys), f"V80 baseline differs from V79 frame {i}")
        for i, (left, right) in enumerate(zip(control["data"]["timings"], ref["timings"])):
            require(all(left.get(k) == right.get(k) for k in right if k != "native_hud_prepare_wall_ns"),
                    f"V80 baseline differs from V79 timing {i}")
        for k, value in ref["summary"].items():
            require(control["data"]["summary"].get(k) == value,
                    f"V80 baseline differs from V79 summary field {k}")
        reports.append("baseline control: four-frame V80 variant0 matches V79 transaction, presentation and summary fields")

    campaigns = sorted((ROOT/"fpga/experiments/cu66-v80/campaigns").glob("prefetch2-*/results.json"))
    for campaign in campaigns:
        reports.append(audit_campaign(campaign, audited))
    faults_root=ROOT/"fpga/experiments/cu66-v80/system/faults"
    fault_path = faults_root/"attempt-20261106T032224482435Z-1b8e74f4/results.json"
    if fault_path.is_file():
        reports.append(audit_fault(fault_path))
    fault_failures=[]
    for failed_path in sorted(faults_root.glob("attempt-*/results.json")):
        if failed_path==fault_path: continue
        if read_json(failed_path).get("status")=="FAIL_FUNCTIONAL":
            fault_failures.append(audit_fault_failure(failed_path))
    if fault_failures:
        reports.append(f"historical actual-system fault-bench failures: {len(fault_failures)} archived snapshots/log sets verified")
    comparison_path = ROOT/"fpga/experiments/cu66-v80/comparison.json"
    if comparison_path.is_file():
        reports.append(audit_comparison(comparison_path, audited, finished_failures, pending))
    trace_analysis_path=ROOT/"fpga/experiments/cu66-v80/trace-analysis/results.json"
    if trace_analysis_path.is_file():
        reports.append(audit_trace_analysis(trace_analysis_path,audited))
    require(audited, "system: no complete V80 PASS results available")
    print("V80_EVIDENCE_AUDIT_PASS")
    print("Functional correctness, modeled 30-fps ACK budget, strict validated-under-10-ms, and physical qualification are separate.")
    print(f"- completed functional PASS runs={len(audited)}; paired configurations={len(pairs)}")
    print(f"- historical completed FAIL attempts={len(finished_failures)}; pending/incomplete checkpoints={len(pending)}")
    for report in reports:
        print(f"- {report}")
    for item in audited:
        d = item["data"]
        t = d["timings"]
        print(f"- {item['path'].parent.parent.name}/{item['path'].parent.name}: "
              f"variant={d['variant']} functional=PASS serial30={sum(x['met_serial_30fps_budget'] for x in t)}/{len(t)} "
              f"under10ms={sum(x['met_validated_under10ms'] for x in t)}/{len(t)} physical_fps_proven=0")
    campaign_dirs = {p.parent for p in campaigns}
    incomplete_campaigns = sorted(p for p in (ROOT/"fpga/experiments/cu66-v80/campaigns").glob("prefetch2-*")
                                  if p.is_dir() and p not in campaign_dirs)
    for path in incomplete_campaigns:
        print(f"- in-progress campaign has no results.json yet: {path.relative_to(ROOT)}")
    for path in finished_failures:
        print(f"- retained historical functional failure: {path.relative_to(ROOT)}")
    for path in pending:
        print(f"- incomplete checkpoint skipped pending process completion: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"V80_EVIDENCE_AUDIT_FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
