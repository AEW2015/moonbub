#!/usr/bin/env python3
"""Read-only integrity and evidence-scope gate for CU66 v73 artifacts."""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v73"
FAILURES = []
REPORT = []


def fail(message):
    FAILURES.append(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(rel, required=True):
    path = ROOT / rel
    if not path.is_file():
        if required:
            fail(f"PENDING evidence artifact missing: {rel}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(f"{rel}: invalid JSON: {exc}")
        return None


def check_pins(data, label):
    pins = data.get("source_sha256")
    if not isinstance(pins, dict) or not pins:
        fail(f"{label}: source_sha256 is missing or empty")
        return 0
    for rel, expected in sorted(pins.items()):
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            fail(f"{label}: source pin is not repository-relative: {rel}")
            continue
        path = ROOT / rel
        if not path.is_file():
            fail(f"{label}: pinned source missing: {rel}")
        elif sha(path) != expected:
            fail(f"{label}: stale source pin: {rel}")
    return len(pins)


def command_log(result_path, name):
    candidate = ROOT / name
    if candidate.is_file():
        return candidate
    return result_path.parent / name


def check_commands(rel, data):
    result_path = ROOT / rel
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands:
        fail(f"{rel}: missing retained command records")
        return 0
    for index, cmd in enumerate(commands):
        label = f"{rel} command[{index}]"
        if not isinstance(cmd, dict):
            fail(f"{label}: malformed command record")
            continue
        if cmd.get("exit_code") != 0:
            fail(f"{label}: exit_code={cmd.get('exit_code')!r}, expected 0")
        name = cmd.get("log")
        if not name:
            fail(f"{label}: log path missing")
            continue
        path = command_log(result_path, name)
        if not path.is_file():
            fail(f"{label}: retained log missing: {name}")
            continue
        if cmd.get("sha256") != sha(path):
            fail(f"{label}: retained log SHA mismatch: {name}")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"(^|\s)(FAIL|FATAL)(\s|:|$)", content, re.M):
            fail(f"{label}: FAIL/FATAL marker in {name}")
        argv = cmd.get("argv", [])
        is_build = ("--build" in argv or ("iverilog" in argv and "-o" in argv) or
                    ("-s" in argv and "yosys" in argv))
        lower = Path(name).name.lower()
        is_build = is_build or "build" in lower
        is_tool_probe = any(term in lower for term in ("version", "sha256"))
        in_elaboration = "/elaboration/" in rel
        if not is_build and not is_tool_probe and not in_elaboration:
            # Runtime terminal markers emitted by the existing CU66 runners.
            markers = ("PASS", "SYSTEM_PASS", "SYSTEM_CONTROL_PASS", "MEMORY_V73_PASS",
                       "MEMORY_V73_RESET_PASS", "MEMORY_V73_CACHE_PASS",
                       "MEMORY_V73_ROWS_PASS", "CASE_PASS", "PASS_UNPLACED_FAMILY_MAPPING")
            if not any(marker in content for marker in markers):
                fail(f"{label}: runtime log has no retained PASS marker: {name}")
    return len(commands)


def audit_result(rel, expected_status=None, required=True):
    data = read_json(rel, required=required)
    if data is None:
        return None
    if expected_status is not None and data.get("status") != expected_status:
        fail(f"{rel}: status={data.get('status')!r}, expected {expected_status!r}")
    pin_count = check_pins(data, rel)
    command_count = check_commands(rel, data)
    REPORT.append(f"{rel}: source_pins={pin_count}, commands={command_count}")
    return data


def check_baseline():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v73/verify_baseline.py")],
                          cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode:
        fail("frozen baseline audit failed: " + (proc.stdout + proc.stderr).strip().replace("\n", " | "))
    else:
        REPORT.append(proc.stdout.strip())


def check_reference_model():
    rel = "fpga/experiments/cu66-v73/reference-traffic.json"
    data = read_json(rel)
    if data is None:
        return
    if data.get("schema") != "cu66-v73-reference-traffic-v1":
        fail(f"{rel}: unexpected schema")
    scope = data.get("scope", "").lower()
    if "synthetic" not in scope or "not actual cu66 p-request" not in scope or "live-target proof" not in scope:
        fail(f"{rel}: scope must label this as a synthetic trace, not actual P traffic or live-target proof")
    mapping = data.get("mapping", {})
    expected_map = {"base_word": 0x080000, "Y_offset_words": 0, "U_offset_words": 172800,
                    "V_offset_words": 216000, "Y_tiles": 5400, "U_tiles": 1350,
                    "V_tiles": 1350, "total_tiles": 8100, "Y_pitch_words": 360,
                    "chroma_pitch_words": 180, "selected_words_per_row": 4, "bl8_words": 8}
    for key, value in expected_map.items():
        if mapping.get(key) != value:
            fail(f"{rel}: mapping {key}={mapping.get(key)!r}, expected {value}")
    if data.get("placement_checks", {}).get("out_of_bounds") is not False:
        fail(f"{rel}: out-of-bounds check is not false")
    if data.get("placement_checks", {}).get("chroma_row_lowbits") != [0, 4] * 4:
        fail(f"{rel}: chroma half placement does not alternate 0/4")
    expected = {
        "v72_scalar_cache1": dict(word_requests=259200, useful_words=259200, read_bursts=64800,
                                   read_beats=518400, wire_bytes=1036800, useful_bytes=518400,
                                   overfetch_bytes=518400),
        "v73_rowwide_cache8": dict(word_requests=64800, useful_words=259200, read_bursts=32640,
                                   read_beats=261120, wire_bytes=522240, useful_bytes=518400,
                                   overfetch_bytes=3840),
    }
    for label, fields in expected.items():
        row = data.get(label, {})
        if row.get("tile_requests") != 8100 or row.get("row_requests") != 64800:
            fail(f"{rel}: {label} tile/row request totals do not match the all-tiles trace")
        if "API calls" not in row.get("word_requests_semantics", ""):
            fail(f"{rel}: {label} does not define word_requests API-call semantics")
        for key, value in fields.items():
            if row.get(key) != value:
                fail(f"{rel}: {label}.{key}={row.get(key)!r}, expected {value}")
        if row.get("read_beats") != row.get("read_bursts", -1) * 8:
            fail(f"{rel}: {label} beat count is not eight per BL8 burst")
        if row.get("wire_bytes") != row.get("read_beats", -1) * 2:
            fail(f"{rel}: {label} wire-byte count is not two bytes per x16 beat")
    selfcheck = data.get("self_check", {}).get("full_adjacent_tile_pair", {})
    if selfcheck.get("8", {}).get("misses") != 8 or selfcheck.get("8", {}).get("hits") != 8:
        fail(f"{rel}: eight-line wide-row adjacent-pair check mismatch")
    if selfcheck.get("1", {}).get("misses") != 16:
        fail(f"{rel}: one-line scalar adjacent-pair check mismatch")
    check_pins(data, rel)
    REPORT.append(f"{rel}: synthetic 8,100-tile mapping and traffic totals checked")


def check_display():
    rel = "fpga/experiments/cu66-v73/display/results.json"
    data = audit_result(rel, "PASS")
    if data is None:
        return
    runs = data.get("runs", [])
    if ({r.get("seed") for r in runs} != {0, 7201, 7202} or len(runs) != 3 or
            data.get("total_rasters") != 39 or data.get("total_compared_RGB_words") != 14976000 or
            data.get("total_fault_probes") != 10 or data.get("start_rejects") != 30):
        fail(f"{rel}: expected native 39-raster, 14,976,000-word painter totals")
    for row in runs:
        cases = [case for case in row.get("per_case", []) if case.get("mode") == 0]
        if row.get("full_rasters") != 13 or len(cases) != 13:
            fail(f"{rel}: seed {row.get('seed')} lacks 13 exact native raster cases")
        if any(c.get("write_commands") != 48000 or c.get("write_words") != 384000 or
               c.get("painted") != 345600 for c in cases):
            fail(f"{rel}: native painter case accounting mismatch for seed {row.get('seed')}")


def check_memory_results():
    rel = "fpga/experiments/cu66-v73/memory/adapters/results.json"
    data = audit_result(rel, "PASS")
    if data is None:
        return
    if data.get("schema") != "cu73-memory-component-results-v1":
        fail(f"{rel}: unexpected schema")
    runs, caches, rows = data.get("runs", []), data.get("cache_runs", []), data.get("row_runs", [])
    expected_runs = {(b, t, s, scenario) for b in ("verilator", "iverilog") for t in (2, 7)
                     for s in (7101, 7102) for scenario in ("continuous", "bubble", "bank3-conflict")}
    expected_runs |= {(b, t, None, "reset") for b in ("verilator", "iverilog") for t in (2, 7)}
    actual_runs = {(r.get("backend"), r.get("tac_ns"), r.get("seed"), r.get("scenario")) for r in runs}
    if len(runs) != 28 or actual_runs != expected_runs:
        fail(f"{rel}: expected 28 backend/tAC/scenario runs, found {len(runs)}")
    if len(caches) != 4 or {(r.get("backend"), r.get("tac_ns")) for r in caches} != {
            (b, t) for b in ("verilator", "iverilog") for t in (2, 7)}:
        fail(f"{rel}: expected four masked-write/cache-alias runs")
    if len(rows) != 8 or {(r.get("backend"), r.get("tac_ns"), r.get("cache_lines")) for r in rows} != {
            (b, t, lines) for b in ("verilator", "iverilog") for t in (2, 7) for lines in (1, 8)}:
        fail(f"{rel}: expected eight wide-row/cache-width runs")
    for r in runs:
        if r.get("scenario") == "reset":
            if (r.get("probes"), r.get("fresh_bursts"), r.get("fresh_words")) != (4, 4, 32):
                fail(f"{rel}: reset recovery count mismatch")
        elif (r.get("tiles", 0) < 237 or r.get("aborts") != 43 or r.get("burst_checks") != 23 or
              r.get("burst_aborts") != 8 or r.get("lcd_bursts") != 250 or r.get("lcd_words") != 2000 or
              r.get("lcd_rejects") != 3 or r.get("lcd_line_max", 99999) > 1842):
            fail(f"{rel}: memory run bounds/count mismatch: {r}")
    for r in caches:
        if (r.get("checks"), r.get("cache_misses")) != (19, 1):
            fail(f"{rel}: masked-write/cache-alias check mismatch")
    for r in rows:
        if (r.get("first_tile_misses"), r.get("second_tile_misses")) != (8, 0 if r.get("cache_lines") == 8 else 8):
            fail(f"{rel}: row-cache adjacent tile miss check mismatch")


def check_control():
    rel = "fpga/experiments/cu66-v73/system/control-results.json"
    data = audit_result(rel, "PASS")
    if data is None:
        return
    counts = data.get("counts", {})
    expected = {"actual_keys_parsed": 2, "completed_HUD_words": 2, "denied_writes": 7,
                "abort_drained": 2, "early_HUD_drain_rejected": 1, "accepted_frames": 0,
                "actual_writes": 2, "actual_reads": 2, "refreshes": 133, "clocks": 99261}
    for key, value in expected.items():
        if counts.get(key) != value:
            fail(f"{rel}: {key}={counts.get(key)!r}, expected {value}")
    if not any("panelcadence30fps" in x.lower() for x in data.get("not_proven", [])) or not any(
            "targetfmax/fit" in x.lower() for x in data.get("not_proven", [])):
        fail(f"{rel}: cadence and target fit limits must remain explicit")


def check_system(rel, frame_count, cache_lines):
    data = audit_result(rel, "PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS")
    if data is None:
        return
    if data.get("p0_cache_lines") != cache_lines or not data.get("strip"):
        fail(f"{rel}: expected strip=true and P0 cache-lines={cache_lines}")
    if data.get("cadence_status") != "NOT_QUALIFIED":
        fail(f"{rel}: cadence status must remain NOT_QUALIFIED")
    summary = data.get("summary", {})
    frames = data.get("frames", [])
    timings = data.get("timings", [])
    if (len(frames) != frame_count or len(timings) != frame_count or
            summary.get("complete_frames") != frame_count or
            summary.get("distinct_complete_presentations") != frame_count):
        fail(f"{rel}: expected {frame_count} complete source frame records and timings")
    frame_ids = {f.get("fid") for f in frames}
    timing_ids = {t.get("fid") for t in timings}
    if len(frame_ids) != frame_count or frame_ids != timing_ids:
        fail(f"{rel}: source frame IDs are incomplete, duplicated, or do not match timing IDs")
    if summary.get("total_underruns") != 0 or summary.get("physical_fps_proven") != 0:
        fail(f"{rel}: underruns must be zero and physical_fps_proven must remain zero")
    limitations = " ".join(data.get("limitations", [])).lower()
    if "no physical30fps" not in limitations or "no targetfmax/fit" not in limitations:
        fail(f"{rel}: physical 30fps and target-fit limitations must be explicit")
    if "notvalidatedtargetlatency" not in data.get("timing_scope", "").lower():
        fail(f"{rel}: timing scope must distinguish model cycles from target latency")
    if len(frames) != len(timings):
        return
    for frame, timing in zip(frames, timings):
        if (frame.get("fid"), frame.get("generation")) != (timing.get("fid"), timing.get("generation")):
            fail(f"{rel}: frame/timing source identity mismatch")
        if not (timing.get("packet_complete_cycle", 0) <= timing.get("admission_cycle", 0) <
                timing.get("validated_ready_cycle", 0) < timing.get("rgb_ready_cycle", 0) <=
                timing.get("commit_ack_cycle", 0)):
            fail(f"{rel}: source phase events are incomplete or out of order")
        if timing.get("complete_rasters", 0) < 1 or frame.get("underruns") != 0:
            fail(f"{rel}: frame lacks a complete raster or has LCD underruns")
        if (frame.get("actual_writes") != 664320 or frame.get("actual_write_commands") != 133920 or
                frame.get("actual_write_bus_beats") != 1071360 or
                frame.get("painter_write_commands") != 48000 or frame.get("painter_write_words") != 384000):
            fail(f"{rel}: canonical/RGB write accounting mismatch for fid={frame.get('fid')}")
    REPORT.append(f"{rel}: {frame_count} distinct complete source frames, zero LCD underruns, cache={cache_lines}")


def check_elaboration():
    rel = "fpga/experiments/cu66-v73/memory/elaboration/results.json"
    data = audit_result(rel, "PASS_GENERIC_AND_CONVERTED_SIMULATION")
    if data is None:
        return
    if data.get("schema") != "cu73-frontend-memory-inspection-v1":
        fail(f"{rel}: unexpected schema")
    if not data.get("native_v72_v73_case_counters_identical") or not data.get("converted_native_case_counters_identical"):
        fail(f"{rel}: native/converted case counter equality not recorded")
    runs = data.get("runs", [])
    if len(runs) != 2 or {r.get("variant") for r in runs} != {"v72", "v73"} or any(
            r.get("status") != "PASS_GENERIC_STRUCTURE" for r in runs):
        fail(f"{rel}: expected v72/v73 generic structure PASS records")
    converted = data.get("converted_simulation", [])
    if len(converted) != 3 or sum(r.get("full_rasters", 0) for r in converted) != 39 or sum(
            r.get("fault_probes", 0) for r in converted) != 10 or sum(
            r.get("start_rejects", 0) for r in converted) != 30:
        fail(f"{rel}: converted simulation must report 39 rasters, 10 faults, 30 rejected starts")
    families = data.get("family_maps", [])
    family_expected = {"v72": ({"RAMB18E1": 0, "RAMB36E1": 24}, 48),
                       "v73": ({"RAMB18E1": 8, "RAMB36E1": 0}, 8)}
    if len(families) != 2 or {r.get("variant") for r in families} != set(family_expected):
        fail(f"{rel}: expected two xc7 family-mapped results")
    for row in families:
        want_prims, want_eq = family_expected.get(row.get("variant"), ({}, -1))
        if (row.get("status") != "PASS_UNPLACED_FAMILY_MAPPING" or
                row.get("strip_primitives") != want_prims or row.get("strip_18k_equivalents") != want_eq):
            fail(f"{rel}: family-map primitive counts/scope mismatch for {row.get('variant')}")
    if len(data.get("family_maps", [])) == 2:
        if abs(data.get("strip_18k_equivalent_reduction_percent", -999) - 83.3333333333) > 0.001:
            fail(f"{rel}: unexpected strip 18K-equivalent reduction")
    derived = 0
    for row in runs + families:
        for name, expected in row.get("files", {}).items():
            path = ROOT / name
            derived += 1
            if not path.is_file() or sha(path) != expected:
                fail(f"{rel}: stale/missing derived output {name}")
    if derived != 14:
        fail(f"{rel}: expected 14 hash-checked generic/family derived files, found {derived}")
    frontend = data.get("frontend", {})
    if not frontend.get("sha256") or not frontend.get("version"):
        fail(f"{rel}: missing sv2v version/SHA record")
    sha_log = AREA / "memory/elaboration/sv2v-sha256.log"
    if not sha_log.is_file() or frontend.get("sha256") not in sha_log.read_text(errors="replace"):
        fail(f"{rel}: sv2v binary SHA log mismatch")
    version_log = AREA / "memory/elaboration/sv2v-version.log"
    if not version_log.is_file() or frontend.get("version") not in version_log.read_text(errors="replace"):
        fail(f"{rel}: sv2v version log mismatch")
    local_frontend = Path(frontend.get("path", ""))
    if local_frontend.is_file() and sha(local_frontend) != frontend.get("sha256"):
        fail(f"{rel}: locally available sv2v binary SHA mismatch")
    yosys = data.get("yosys", "")
    if not yosys or "Yosys" not in yosys:
        fail(f"{rel}: missing Yosys version record")
    yosys_log = AREA / "memory/elaboration/yosys-version.log"
    if not yosys_log.is_file() or yosys.strip() != yosys_log.read_text(errors="replace").strip():
        fail(f"{rel}: Yosys version log mismatch")
    limitation_text = " ".join(data.get("limitations", [])).lower()
    if ("no exact-device place/route/fmax" not in limitation_text or
            "target30fps" not in limitation_text or "sub10ms" not in limitation_text):
        fail(f"{rel}: unplaced family-map and no-cadence limitations are not explicit")
    separate = read_json("fpga/experiments/cu66-v73/memory/elaboration/family-map-results.json")
    if separate is not None:
        check_pins(separate, "family-map-results.json")
        log_path_value = separate.get("log")
        log_file = ROOT / log_path_value if log_path_value else None
        if separate.get("status") != "PASS_UNPLACED_FAMILY_MAPPING" or separate.get("exit_code") != 0:
            fail("family-map-results.json: missing unplaced mapping PASS")
        if not log_file or not log_file.is_file() or sha(log_file) != separate.get("log_sha256"):
            fail("family-map-results.json: family-map log missing or SHA mismatch")
        for name, expected_hash in separate.get("files", {}).items():
            if not (ROOT / name).is_file() or sha(ROOT / name) != expected_hash:
                fail(f"family-map-results.json: derived output hash mismatch: {name}")
    REPORT.append(f"{rel}: generic+converted evidence and 14 derived hashes; family-map strip = 48 vs 8 18K equivalents (unplaced)")


def check_archive():
    base = AREA / "system/before-cache-index-widths"
    manifest_rel = "fpga/experiments/cu66-v73/system/before-cache-index-widths/manifest.json"
    manifest = read_json(manifest_rel)
    if manifest is None:
        return
    archive = base / "source-and-evidence.zip"
    if not archive.is_file():
        fail("before-cache-index-widths archive missing")
        return
    if sha(archive) != manifest.get("archive_sha256"):
        fail("before-cache-index-widths archive SHA mismatch")
        return
    entries = manifest.get("files_sha256", {})
    if len(entries) != 43:
        fail(f"before-cache-index-widths manifest expected 43 entries; got {len(entries)}")
    try:
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            if names != set(entries):
                fail(f"before-cache-index-widths ZIP membership mismatch: {len(names)} vs {len(entries)}")
            for name, expected in entries.items():
                if hashlib.sha256(zf.read(name)).hexdigest() != expected:
                    fail(f"before-cache-index-widths ZIP member hash mismatch: {name}")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        fail(f"before-cache-index-widths archive unreadable or incomplete: {exc}")
    REPORT.append("before-cache-index-widths: 43 internal archive members verified (superseded evidence)")


def check_comparison():
    rel = "fpga/experiments/cu66-v73/system/comparison.json"
    data = read_json(rel)
    if data is None:
        return
    if data.get("status") != "PASS_EXACT_OUTPUT_COMPARISON":
        fail(f"{rel}: status must be PASS_EXACT_OUTPUT_COMPARISON")
    expected_inputs = (
        "fpga/experiments/cu66-v72/system/full-strip/results.json",
        "fpga/experiments/cu66-v73/system/full-strip-cache1/results.json",
        "fpga/experiments/cu66-v73/system/full-strip/results.json",
    )
    inputs = data.get("input_sha256", {})
    for source in expected_inputs:
        path = ROOT / source
        if not path.is_file():
            fail(f"{rel}: comparison input missing: {source}")
        elif inputs.get(source) != sha(path):
            fail(f"{rel}: stale/missing input hash for {source}")
    script = ROOT / "scripts/cu66-v73/compare_system.py"
    recorded_script = data.get("script_sha256")
    if not script.is_file():
        fail("PENDING comparison producer script missing: scripts/cu66-v73/compare_system.py")
    elif recorded_script != sha(script):
        fail(f"{rel}: stale/missing compare script SHA")
    frames = data.get("frames", [])
    if len(frames) != 2:
        fail(f"{rel}: expected two key/P exact-output comparison frames")
    for frame in frames:
        old = frame.get("v72", {})
        one = frame.get("v73_cache1", {})
        eight = frame.get("v73_cache8", {})
        if (old.get("fid"), old.get("key"), old.get("generation")) != (
                one.get("fid"), one.get("key"), one.get("generation")) or (
                old.get("fid"), old.get("key"), old.get("generation")) != (
                eight.get("fid"), eight.get("key"), eight.get("generation")):
            fail(f"{rel}: v72/cache1/cache8 frame identity mismatch")
        if (one.get("p0_row_reads") != eight.get("p0_row_reads") or
                one.get("p0_cache_hits", 0) + one.get("p0_cache_misses", 0) != one.get("p0_row_reads") or
                eight.get("p0_cache_hits", 0) + eight.get("p0_cache_misses", 0) != eight.get("p0_row_reads")):
            fail(f"{rel}: cache ablation reference-row counters do not reconcile")
        row_reads = eight.get("p0_row_reads", 0)
        if row_reads and eight.get("p0_cache_misses", 0) >= one.get("p0_cache_misses", 0):
            fail(f"{rel}: eight-entry cache does not reduce P0 misses on a row-read frame")
        if row_reads:
            if (frame.get("reference_useful_bytes") != row_reads * 8 or
                    frame.get("cache1_reference_wire_bytes") != one.get("p0_cache_misses", 0) * 16 or
                    frame.get("cache8_reference_wire_bytes") != eight.get("p0_cache_misses", 0) * 16 or
                    frame.get("v72_scalar_ref_requests_inferred") != row_reads * 4):
                fail(f"{rel}: derived row/cache traffic accounting mismatch")
        for result_rel, source in zip(expected_inputs, (old, one, eight)):
            result_path = ROOT / result_rel
            if result_path.is_file():
                try:
                    source_data = json.loads(result_path.read_text(encoding="utf-8"))
                    candidate = next((r for r in source_data.get("frames", [])
                                      if r.get("fid") == old.get("fid")), None)
                    if candidate != source:
                        fail(f"{rel}: comparison frame payload differs from {result_rel}")
                except (OSError, ValueError, json.JSONDecodeError):
                    fail(f"{rel}: cannot reconcile frame payload with {result_rel}")
    if data.get("shared_v72_source_pins", 0) <= 0:
        fail(f"{rel}: no shared frozen-source pin comparison recorded")
    limitations = " ".join(data.get("limitations", [])).lower()
    if "physical30fps" not in limitations or "sub10ms" not in limitations:
        fail(f"{rel}: comparison must state physical 30fps and target sub-10ms limits")


def check_ooc():
    rel="fpga/experiments/cu66-v73/build/status.json"
    d=read_json(rel)
    if d is None:return
    if d.get("status")!="UNAVAILABLE_EXACT_PART" or d.get("exit_code")!=2 or d.get("target_part")!="xc7a100tcsg324-1" or d.get("synthesis_started") is not False or d.get("implementation_started") is not False:
        fail("OOC: unavailable exact part must not claim synthesis/implementation")
    count=check_pins(d,"OOC unavailable preflight")
    folder=ROOT/"fpga/experiments/cu66-v73/build"
    if sha(folder/"ooc_system.tcl")!=d.get("script_sha256") or sha(ROOT/d["source_spec"])!=d.get("source_spec_sha256"):fail("OOC: stale Tcl or source list")
    spec=json.loads((ROOT/d["source_spec"]).read_text())
    expected=[name for name in spec["rtl_sources"]if not name.endswith(("_sim.sv","_model.sv"))]
    if d.get("hardware_sources")!=expected or len(expected)!=21:fail("OOC: hardware source membership differs from staged spec")
    for name,h in d.get("include_header_sha256",{}).items():
        if sha(ROOT/name)!=h:fail("OOC: stale include "+name)
    for name,h in d.get("logs_sha256",{}).items():
        if sha(folder/name)!=h:fail("OOC: stale log "+name)
    if "UNAVAILABLE_EXACT_PART"not in(folder/"vivado-stdout.log").read_text():fail("OOC: unavailable-part transcript absent")
    REPORT.append(f"OOC: UNAVAILABLE_EXACT_PART; {count} source pins, no synthesis/implementation")


def main():
    check_baseline()
    check_reference_model()
    check_display()
    check_memory_results()
    check_control()
    check_system("fpga/experiments/cu66-v73/system/full-strip/results.json", 2, 8)
    check_system("fpga/experiments/cu66-v73/system/full-strip-cache1/results.json", 2, 1)
    check_system("fpga/experiments/cu66-v73/system/history-4-strip/results.json", 4, 8)
    check_elaboration()
    check_archive()
    check_comparison()
    check_ooc()
    if FAILURES:
        print("V73_EVIDENCE_AUDIT_FAIL")
        for item in FAILURES:
            print("  " + item)
        return 1
    print("V73_EVIDENCE_AUDIT_PASS")
    for item in REPORT:
        print("  " + item)
    print("  functional/model evidence only; no target fit/Fmax, physical 30fps, or target sub-10ms verdict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
