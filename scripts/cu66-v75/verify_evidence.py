#!/usr/bin/env python3
"""Read-only integrity and scope audit of retained CU66 V75 evidence."""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / "fpga/experiments/cu66-v75"
FAIL = []
REPORT = []


def fail(message):
    FAIL.append(message)


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


def safe_path(rel):
    p = Path(rel)
    return not p.is_absolute() and ".." not in p.parts


def source_pins(data, label):
    pins = data.get("source_sha256")
    if not isinstance(pins, dict) or not pins:
        fail(f"{label}: source_sha256 missing/empty")
        return 0
    for rel, expected in pins.items():
        if not safe_path(rel):
            fail(f"{label}: unsafe source pin {rel}")
            continue
        path = ROOT / rel
        if not path.is_file() or sha(path) != expected:
            fail(f"{label}: source missing/hash mismatch: {rel}")
    return len(pins)


def command_audit(rel, data, require=True):
    commands = data.get("commands")
    if not isinstance(commands, list) or (require and not commands):
        fail(f"{rel}: commands missing/empty")
        return 0
    for i, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            fail(f"{rel} command {i}: malformed")
            continue
        if cmd.get("exit_code") != 0:
            fail(f"{rel} command {i}: exit_code={cmd.get('exit_code')}")
        name = cmd.get("log")
        if not name or not safe_path(name):
            fail(f"{rel} command {i}: unsafe/missing log path")
            continue
        path = ROOT / name
        if not path.is_file():
            path = (ROOT / rel).parent / name
        if not path.is_file() or sha(path) != cmd.get("sha256"):
            fail(f"{rel} command {i}: log missing/hash mismatch: {name}")
            continue
        contents = path.read_text(errors="replace")
        if re.search(r"(^|\s)(FAIL|FATAL)(\s|:|$)", contents, re.M):
            fail(f"{rel} command {i}: FAIL/FATAL marker in {name}")
        argv = cmd.get("argv", [])
        build = "--build" in argv or ("-s" in argv and "yosys" in argv) or "build" in Path(name).name.lower()
        probe = any(tag in Path(name).name.lower() for tag in ("version", "sha256"))
        transform = Path(name).name.lower() in ("sv2v.log", "generic.ys")
        if not build and not probe and not transform:
            markers = ("PASS", "SYSTEM_PASS", "SYSTEM_FRAME_PASS", "CASE_PASS",
                       "V75_FRONTEND_GENERIC_PASS", "V75_ABLATION_PASS")
            if not any(marker in contents for marker in markers):
                fail(f"{rel} command {i}: runtime PASS marker missing in {name}")
    return len(commands)


def audited(rel, expected_status=None, commands=True):
    data = read(rel)
    if data is None:
        return None
    if expected_status and data.get("status") != expected_status:
        fail(f"{rel}: status={data.get('status')!r}, expected {expected_status!r}")
    pins = source_pins(data, rel)
    ncmd = command_audit(rel, data) if commands else 0
    REPORT.append(f"{rel}: pins={pins}, commands={ncmd}")
    return data


def baseline():
    p = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v75/verify_baseline.py")],
                       cwd=ROOT, text=True, capture_output=True, check=False)
    if p.returncode:
        fail("frozen V69-V74 baseline verifier failed: " + (p.stdout + p.stderr).strip().replace("\n", " | "))
    else:
        REPORT.append(p.stdout.strip())
    pins = read("fpga/experiments/cu66-v75/baseline-sources.json")
    if pins:
        for rel in ("fpga/experiments/cu66-v74/memory/cu74_memory_system.sv",
                    "fpga/experiments/cu66-v72/memory/cu72_sdram_controller.sv",
                    "fpga/experiments/cu66-v72/memory/cu72_sdram_model.sv"):
            if rel not in pins.get("source_sha256", {}):
                fail(f"baseline pin missing frozen memory/controller/model file: {rel}")
        REPORT.append("frozen V74 memory system and V72 controller/model source hashes pinned")


def painter():
    rel = "fpga/experiments/cu66-v75/display/results.json"
    data = audited(rel, "PASS")
    if data is None:
        return
    if (data.get("total_rasters"), data.get("total_compared_RGB_words"),
        data.get("total_fault_probes"), data.get("start_rejects")) != (39, 14976000, 20, 30):
        fail(f"{rel}: expected 39 rasters, 14,976,000 RGB words, 20 final fault probes, 30 invalid starts")
    runs = data.get("runs", [])
    if len(runs) != 3 or {r.get("seed") for r in runs} != {0, 7201, 7202}:
        fail(f"{rel}: expected seeds 0, 7201, 7202")
    for run in runs:
        cases = run.get("per_case", [])
        good = [case for case in cases if case.get("mode") == 0]
        if run.get("full_rasters") != 13 or len(good) != 13:
            fail(f"{rel}: seed {run.get('seed')} lacks 13 full rasters")
        expected_faults = 0 if run.get("seed") == 0 else 10
        if run.get("fault_probes") != expected_faults:
            fail(f"{rel}: seed {run.get('seed')} fault probe count mismatch")
        log_name = f"fpga/experiments/cu66-v75/display/run-{run.get('seed')}.log"
        log_path = ROOT / log_name
        if not log_path.is_file():
            fail(f"{rel}: retained native run log missing: {log_name}")
        else:
            log_text = log_path.read_text(errors="replace")
            if f"PASS actual_frames=8 patterns=4 recovery=1 fault_probes={expected_faults} seed={run.get('seed')}" not in log_text or log_text.count("START_REJECT_PASS ") != 10:
                fail(f"{rel}: native seed {run.get('seed')} PASS/fault/reject markers mismatch")
        for case in good:
            if (case.get("read_commands"), case.get("read_words"), case.get("write_commands"),
                case.get("write_words"), case.get("painted"), case.get("error")) != (35040, 280320, 48000, 384000, 345600, 0):
                fail(f"{rel}: native full-raster counter mismatch, seed {run.get('seed')}")
    archived = "fpga/experiments/cu66-v75/display/before-read-stage-probes/manifest.json"
    manifest = read(archived)
    zip_rel = "fpga/experiments/cu66-v75/display/before-read-stage-probes/source-and-evidence.zip"
    if manifest:
        archive = ROOT / zip_rel
        if not archive.is_file() or sha(archive) != manifest.get("archive_sha256"):
            fail(f"{archived}: archive missing/hash mismatch")
        else:
            try:
                with zipfile.ZipFile(archive) as zf:
                    entries = {name: hashlib.sha256(zf.read(name)).hexdigest() for name in zf.namelist()}
                if entries != manifest.get("files_sha256") or len(entries) != 8:
                    fail(f"{archived}: archived superseded 8-file qualification inventory mismatch")
            except (OSError, zipfile.BadZipFile, KeyError) as exc:
                fail(f"{archived}: cannot audit archive: {exc}")
        if "superseded" not in manifest.get("scope", "").lower():
            fail(f"{archived}: old initial qualification not labeled superseded")
        REPORT.append(f"{archived}: superseded archive SHA and all {len(manifest.get('files_sha256', {}))} member hashes verified")


def elaboration():
    rel = "fpga/experiments/cu66-v75/memory/elaboration/results.json"
    data = audited(rel, "PASS_GENERIC_AND_CONVERTED_SIMULATION")
    if data is None:
        return
    if data.get("schema") != "cu75-frontend-memory-inspection-v1":
        fail(f"{rel}: schema mismatch")
    if not data.get("converted_native_case_counters_identical"):
        fail(f"{rel}: converted/native counter parity flag false")
    if data.get("logical_memory_bytes") != 23056 or data.get("statistics", {}).get("num_memories") != 0:
        fail(f"{rel}: generic collected memory inventory mismatch")
    if data.get("statistics", {}).get("num_cells_by_type", {}).get("$mem_v2") != 34:
        fail(f"{rel}: expected 34 generic collected memories")
    # Every retained converted/generic artifact is hash-bound by the result.
    derived = data.get("derived_files_sha256", {})
    expected_names = {"cu75_painter_burst.v", "generic.ys", "stat.json", "netlist.json", "converted-only.vlt"}
    if {Path(name).name for name in derived} != expected_names:
        fail(f"{rel}: incomplete derived-artifact inventory")
    for name, digest in derived.items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: derived artifact missing/hash mismatch: {name}")
    stat = read("fpga/experiments/cu66-v75/memory/elaboration/stat.json")
    if stat is None or stat.get("modules", {}).get("\\cu75_painter_burst") != data.get("statistics"):
        fail(f"{rel}: retained stat.json differs from result statistics")
    net = read("fpga/experiments/cu66-v75/memory/elaboration/netlist.json")
    if net is None:
        return
    module = net.get("modules", {}).get("cu75_painter_burst", {})
    from collections import Counter
    types = Counter(cell.get("type") for cell in module.get("cells", {}).values())
    if len(module.get("cells", {})) != data.get("statistics", {}).get("num_cells") or types.get("$mem_v2") != 34:
        fail(f"{rel}: generic netlist cell/memory inventory disagrees with stats")
    native = read("fpga/experiments/cu66-v75/display/results.json")
    converted = data.get("converted_simulation", [])
    if native is None or len(converted) != 3 or len(native.get("runs", [])) != 3:
        fail(f"{rel}: native/converted seed coverage incomplete")
    else:
        for cv in converted:
            nr = next((r for r in native["runs"] if r.get("seed") == cv.get("seed")), None)
            if nr is None or nr.get("per_case") != cv.get("per_case"):
                fail(f"{rel}: native/converted actual per-case counters differ for seed {cv.get('seed')}")
            expected_faults = 0 if cv.get("seed") == 0 else 10
            run_name = f"fpga/experiments/cu66-v75/memory/elaboration/converted-run-{cv.get('seed')}.log"
            run_path = ROOT / run_name
            if not run_path.is_file():
                fail(f"{rel}: converted run log missing: {run_name}")
            else:
                run_text = run_path.read_text(errors="replace")
                if f"PASS actual_frames=8 patterns=4 recovery=1 fault_probes={expected_faults} seed={cv.get('seed')}" not in run_text or run_text.count("START_REJECT_PASS ") != 10:
                    fail(f"{rel}: converted seed {cv.get('seed')} PASS/fault/reject markers mismatch")
        counts = (sum(len([c for c in r.get("per_case", []) if c.get("mode") == 0]) for r in converted),
                  sum(sum(1 for c in r.get("per_case", []) if 1 <= c.get("mode", 0) <= 10)
                      for r in converted), 30)
        if counts != (39, 20, 30):
            fail(f"{rel}: converted full raster/fault/start-reject totals mismatch: {counts}")
    family = data.get("family_map", {})
    if family.get("status") != "PASS_UNPLACED_FAMILY_MAPPING":
        fail(f"{rel}: expected explicitly unplaced XC7 family map result")
    if len(family.get("files", {})) != 3:
        fail(f"{rel}: expected three family-map derived artifacts")
    for name, digest in family.get("files", {}).items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: family-map artifact hash mismatch: {name}")
    if not any("not exact-device fit/placement/routing/fmax/cdc proof" in str(x).lower()
               for x in data.get("limitations", [])):
        fail(f"{rel}: no-fit/no-Fmax scope limitation missing")


def ooc():
    rel = "fpga/experiments/cu66-v75/build/status.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status"), data.get("exit_code")) != (
        "cu75-exact-target-ooc-preflight-v1", "UNAVAILABLE_EXACT_PART", 2):
        fail(f"{rel}: exact target must remain explicitly unavailable with exit 2")
    sources, pins = data.get("hardware_sources", []), data.get("source_sha256", {})
    if len(sources) != 20 or len(set(sources)) != 20 or set(sources) != set(pins):
        fail(f"{rel}: expected 20 unique hardware source paths with exact SHA pins")
    for name, digest in pins.items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: hardware source hash mismatch: {name}")
    includes = data.get("include_header_sha256", {})
    if not includes:
        fail(f"{rel}: include header pins missing")
    for name, digest in includes.items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: include header hash mismatch: {name}")
    spec = ROOT / data.get("source_spec", "")
    if not spec.is_file() or sha(spec) != data.get("source_spec_sha256"):
        fail(f"{rel}: source specification hash mismatch")
    if data.get("synthesis_started") is not False or data.get("implementation_started") is not False:
        fail(f"{rel}: preflight must prove no synthesis/implementation started")
    if len(data.get("logs_sha256", {})) < 3:
        fail(f"{rel}: expected retained Vivado stdout/OOC/version/hash logs")
    for name, digest in data.get("logs_sha256", {}).items():
        path = ROOT / "fpga/experiments/cu66-v75/build" / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: retained log hash mismatch: {name}")
    REPORT.append(f"{rel}: exact part unavailable, 20 source pins, synthesis/implementation not started")


def system_runs():
    specs = {
        "fpga/experiments/cu66-v75/system/full-strip-scalar/results.json": (2, "scalar", 101520, 812160, 21120, 0),
        "fpga/experiments/cu66-v75/system/full-strip-burst/results.json": (2, "burst", 83040, 664320, 2640, 1),
        "fpga/experiments/cu66-v75/system/history-4-strip-burst/results.json": (4, "burst", 83040, 664320, 2640, 1),
    }
    loaded = {}
    for rel, (n, mode, cmds, beats, hudreq, burstflag) in specs.items():
        d = audited(rel, "PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS")
        if d is None:
            continue
        loaded[mode if n == 2 else "history"] = d
        summary = d.get("summary", {})
        if d.get("hud_mode") != mode or d.get("cadence_status") != "NOT_QUALIFIED":
            fail(f"{rel}: mode/cadence scope mismatch")
        if (summary.get("complete_frames"), summary.get("distinct_complete_presentations")) != (n, n):
            fail(f"{rel}: expected {n} distinct complete presentations")
        if summary.get("black_lines") != 0:
            fail(f"{rel}: final qualification requires black_lines=0")
        if summary.get("total_underruns") != 0 or summary.get("physical_fps_proven") != 0:
            fail(f"{rel}: underrun/cadence result mismatch")
        if (summary.get("canonical_bytes_per_frame"), summary.get("RGB_words_per_frame"),
            summary.get("HUD_functional_readback_words_per_frame")) != (518400, 384000, 21120):
            fail(f"{rel}: canonical/RGB/HUD output totals mismatch")
        frames, timings = d.get("frames", []), d.get("timings", [])
        if len(frames) != n or len(timings) != n:
            fail(f"{rel}: frame/timing records incomplete")
        identities = set()
        for f, t in zip(frames, timings):
            ident = (f.get("fid"), f.get("generation"))
            if ident in identities:
                fail(f"{rel}: duplicate presentation identity {ident}")
            identities.add(ident)
            if (f.get("fid"), f.get("generation")) != (t.get("fid"), t.get("generation")):
                fail(f"{rel}: frame/timing identity mismatch")
            if not (t.get("packet_complete_cycle", 0) <= t.get("admission_cycle", 0) <
                    t.get("validated_ready_cycle", 0) < t.get("rgb_ready_cycle", 0) <= t.get("commit_ack_cycle", 0)):
                fail(f"{rel}: timing event order invalid")
            if (f.get("actual_writes"), f.get("actual_write_commands"), f.get("actual_write_bus_beats"),
                f.get("hud_burst"), f.get("hud_write_requests"), f.get("hud_read_requests"),
                f.get("painter_read_commands"), f.get("painter_read_words"),
                f.get("painter_write_commands"), f.get("painter_write_words")) != (
                    664320, cmds, beats, burstflag, hudreq, hudreq, 35040, 280320, 48000, 384000):
                fail(f"{rel}: native actual memory/HUD/painter counters mismatch")
        if "no physical30fps" not in " ".join(d.get("limitations", [])).lower():
            fail(f"{rel}: physical 30 fps limitation missing")
        if "short history" not in " ".join(d.get("limitations", [])).lower():
            fail(f"{rel}: fixed-arrival qualification limitation missing")
    scalar = loaded.get("scalar")
    burst = loaded.get("burst")
    history = loaded.get("history")
    if scalar and burst:
        if scalar.get("source_sha256") != burst.get("source_sha256"):
            fail("scalar/burst system runs do not have identical source pins")
    if burst and history and burst.get("frames") != history.get("frames", [])[:2]:
        fail("four-presentation burst run does not reproduce the full-strip burst prefix exactly")
    if scalar and "fpga/experiments/cu66-v75/system/tb_system.cpp" in scalar.get("source_sha256", {}):
        tb = ROOT / "fpga/experiments/cu66-v75/system/tb_system.cpp"
        txt = tb.read_text(errors="replace")
        if "full portrait RGB565 memory mismatch" not in txt:
            fail("system TB does not enforce exact full-frame native RGB565 oracle comparison")
        REPORT.append("scalar and burst runs use the same pinned TB and each checks all 480x800 RGB565 words against native oracle")



def control():
    rel = "fpga/experiments/cu66-v75/system/control-results.json"
    data = audited(rel, "PASS")
    if data is None:
        return
    expected = {
        "actual_keys_parsed": 4, "completed_HUD_words": 21130,
        "legacy_denied_writes": 7, "denied_burst_requests": 21,
        "abort_drained": 4, "early_HUD_drain_rejected": 2,
        "accepted_frames": 0, "actual_writes": 21130, "actual_reads": 2642,
        "held_wide_responses": 3, "accepted_payload_mutations": 3,
        "burst_write_commands": 2641, "burst_write_bus_beats": 21128,
        "legacy_clocks": 99261, "burst_clocks": 202339,
    }
    counts = data.get("counts", {})
    for key, value in expected.items():
        if counts.get(key) != value:
            fail(f"{rel}: {key}={counts.get(key)!r}, expected {value}")
    unproven = " ".join(data.get("not_proven", [])).lower()
    for phrase in ("panelcadence30fps", "targetfmax/fit", "fullcanonicalrgboutputs"):
        if phrase not in unproven:
            fail(f"{rel}: missing explicit unproven scope {phrase}")
    REPORT.append(f"{rel}: guarded upload/readback counts verified; accepted_frames=0")


def comparison():
    rel = "fpga/experiments/cu66-v75/system/comparison.json"
    d = read(rel)
    if d is None:
        return
    if d.get("status") != "PASS_EXACT_OUTPUT_ABLATION":
        fail(f"{rel}: status mismatch")
    script = ROOT / "scripts/cu66-v75/compare_system.py"
    if not script.is_file() or sha(script) != d.get("script_sha256"):
        fail(f"{rel}: comparison producer script hash mismatch")
    for name, digest in d.get("input_sha256", {}).items():
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(f"{rel}: input result hash mismatch: {name}")
    if not d.get("new_scalar_burst_source_pins_identical"):
        fail(f"{rel}: scalar/burst identical source-pin declaration missing")
    frames = d.get("frames", [])
    if len(frames) != 2 or {f.get("fid") for f in frames} != {0, 1}:
        fail(f"{rel}: expected matched key and P frame comparisons")
    for f in frames:
        scalar, burst = f.get("v75_scalar", {}), f.get("v75_burst", {})
        if (scalar.get("fid"), scalar.get("generation"), scalar.get("key")) != (
            burst.get("fid"), burst.get("generation"), burst.get("key")):
            fail(f"{rel}: scalar/burst frame identity mismatch")
        if (scalar.get("actual_writes"), burst.get("actual_writes")) != (664320, 664320):
            fail(f"{rel}: scalar/burst active output write counts differ")
        if (scalar.get("actual_write_commands"), scalar.get("actual_write_bus_beats"),
            scalar.get("hud_write_requests"), scalar.get("hud_read_requests")) != (101520, 812160, 21120, 21120):
            fail(f"{rel}: scalar HUD traffic counters mismatch")
        if (burst.get("actual_write_commands"), burst.get("actual_write_bus_beats"),
            burst.get("hud_write_requests"), burst.get("hud_read_requests")) != (83040, 664320, 2640, 2640):
            fail(f"{rel}: burst HUD traffic counters mismatch")
    if len(d.get("history_transaction_model_ms", [])) != 4:
        fail(f"{rel}: four-presentation transaction duration list missing")
    # Report phase effects and avoid interpreting decoder-paced samples as a universal rate.
    limits = " ".join(d.get("limitations", [])).lower()
    if "phase change" not in limits or "not normalized" not in limits or "short decoder-paced" not in limits:
        fail(f"{rel}: phase-change/decoder-paced comparison limitations missing")
    REPORT.append(f"{rel}: two matched frame comparisons; four history transaction durations; timing is model-only and phase-sensitive")


def main():
    baseline()
    painter()
    elaboration()
    ooc()
    system_runs()
    control()
    comparison()
    if FAIL:
        print("V75_EVIDENCE_FAIL")
        print("\n".join(" - " + message for message in FAIL))
        raise SystemExit(1)
    print("V75_EVIDENCE_INTEGRITY_AND_SCOPE_PASS")
    print("\n".join(REPORT))


if __name__ == "__main__":
    main()
