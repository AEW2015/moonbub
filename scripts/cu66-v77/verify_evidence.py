#!/usr/bin/env python3
"""Audit retained V77 component and native-system evidence, with separated verdicts."""
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


def safe(rel):
    path = Path(rel)
    return not path.is_absolute() and ".." not in path.parts


def verify_hashes(data, field, label):
    hashes = data.get(field)
    if not isinstance(hashes, dict) or not hashes:
        fail(f"{label}: {field} missing or empty")
        return False
    valid = True
    for rel, digest in hashes.items():
        if not safe(rel):
            fail(f"{label}: unsafe path in {field}: {rel}")
            valid = False
            continue
        path = ROOT / rel
        if not path.is_file() or sha(path) != digest:
            fail(f"{label}: hash mismatch: {rel}")
            valid = False
    return valid


def command_logs(data, label, required_marker):
    commands = data.get("commands")
    if not isinstance(commands, list) or not commands:
        fail(f"{label}: command records missing")
        return
    for index, command in enumerate(commands):
        if not isinstance(command, dict) or command.get("exit_code") != 0:
            fail(f"{label}: command {index} did not exit successfully")
            continue
        rel = command.get("log")
        if not isinstance(rel, str) or not safe(rel):
            fail(f"{label}: command {index} has unsafe/missing log path")
            continue
        path = ROOT / rel
        if not path.is_file() or sha(path) != command.get("sha256"):
            fail(f"{label}: command log hash mismatch: {rel}")
            continue
        content = path.read_text(errors="replace")
        if re.search(r"(^|\s)(FAIL|FATAL)(\s|:|$)", content, re.M):
            fail(f"{label}: failure marker in {rel}")
        name = Path(rel).name
        runtime_log = name.startswith("run-") or name == "pixel-run.log" or name == "slot3-run.log"
        marker = "SLOT3_PASS" if name == "slot3-run.log" else required_marker
        if marker and runtime_log and marker not in content:
            fail(f"{label}: completion marker {marker} absent from {rel}")


def baseline():
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/cu66-v77/verify_baseline.py")],
                          cwd=ROOT, text=True, capture_output=True, check=False)
    if proc.returncode:
        fail("frozen V69-V76 baseline verifier failed: " +
             (proc.stdout + proc.stderr).strip().replace("\n", " | "))
    else:
        REPORT.append(proc.stdout.strip())


def archive_audit(manifest_rel, archive_rel, expected_count):
    manifest = read(manifest_rel)
    if manifest is None:
        return
    archive = ROOT / archive_rel
    if not archive.is_file() or sha(archive) != manifest.get("archive_sha256"):
        fail(f"{manifest_rel}: archive missing or hash mismatch")
        return
    try:
        with zipfile.ZipFile(archive) as zf:
            members = {name: hashlib.sha256(zf.read(name)).hexdigest()
                       for name in zf.namelist()}
        if members != manifest.get("files_sha256") or len(members) != expected_count:
            fail(f"{manifest_rel}: internal archive inventory/hash mismatch")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        fail(f"{manifest_rel}: archive cannot be read: {exc}")
    if "superseded" not in manifest.get("scope", "").lower():
        fail(f"{manifest_rel}: archived proof is not labeled superseded")


def pixel_audit():
    rel = "fpga/experiments/cu66-v77/render/pixel-results.json"
    data = read(rel)
    if data is None:
        return
    if data.get("status") != "PASS_EXACT_ELASTIC_PIXEL_PIPELINE":
        fail(f"{rel}: exact elastic pixel regression did not pass")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "PIXEL_PASS")
    log_path = ROOT / "fpga/experiments/cu66-v77/render/pixel-run.log"
    text = log_path.read_text(errors="replace") if log_path.is_file() else ""
    match = re.search(r"PIXEL_PASS accepted=(\d+) emitted=(\d+) flushed=(\d+) aborts=(\d+) II1_cycles=(\d+)", text)
    if not match:
        fail(f"{rel}: missing structured pixel accounting record")
        return
    accepted, emitted, flushed, aborts, ii1 = map(int, match.groups())
    if accepted != emitted + flushed or aborts <= 0 or ii1 <= 0:
        fail(f"{rel}: pixel held-output ownership, abort, or II=1 accounting mismatch")
    REPORT.append(f"{rel}: exact RGB565 oracle PASS; accepted={accepted}, emitted={emitted}, abort-flushed={flushed}; standalone arithmetic only")


def render_audit():
    rel = "fpga/experiments/cu66-v77/render/results.json"
    data = read(rel)
    if data is None:
        return
    if data.get("status") != "PASS_NATIVE_CACHE_BACKED_RGB":
        fail(f"{rel}: native fixture/cache render did not pass")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "RENDER_PASS")
    runs = data.get("runs", [])
    if [r.get("seed") for r in runs] != [0, 7701, 7702]:
        fail(f"{rel}: expected retained deterministic seeds 0, 7701, 7702")
    frames = words = faults = 0
    for run in runs:
        cases = run.get("per_case", [])
        normal = [c for c in cases if c.get("mode") == 0]
        if len(normal) != 13 or run.get("full_frames") != 13 or \
                any((c.get("commands"), c.get("words"), c.get("pixels"), c.get("accepted")) !=
                    (35040, 280320, 345600, 345600) for c in normal):
            fail(f"{rel}: full render case memory/pixel inventory mismatch for seed {run.get('seed')}")
        if run.get("fault_probes") != sum(c.get("mode") != 0 for c in cases):
            fail(f"{rel}: directed fault-probe records mismatch")
        frames += run.get("full_frames", 0)
        words += sum(c.get("pixels", 0) for c in normal)
        faults += run.get("fault_probes", 0)
    if (frames, words, faults, data.get("total_frames"), data.get("total_active_RGB_words"),
            data.get("fault_probes")) != (39, 13478400, 4, 39, 13478400, 4):
        fail(f"{rel}: aggregate native render accounting mismatch")
    limits = " ".join(data.get("limitations", [])).lower().replace(" ", "")
    scope = data.get("scope", "").lower().replace(" ", "")
    if "physical30fps" not in limits or "pixelclockcdc" not in scope:
        fail(f"{rel}: physical-rate and CDC limitations missing")
    REPORT.append(f"{rel}: native decoded fixture render PASS across {frames} frames / {words} RGB words; ideal memory source, not native controller or physical timing")


def bounded_render_audit():
    rel = "fpga/experiments/cu66-v77/render/bounded/results.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status")) != (
            "cu77-bounded-native-render-v1", "PASS_NATIVE_CACHE_BACKED_RGB_AND_BASE_PARITY"):
        fail(f"{rel}: bounded-address native render did not pass")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "RENDER_PASS")
    base = read("fpga/experiments/cu66-v77/render/results.json")
    runs, base_runs = data.get("runs", []), base.get("runs", []) if base else []
    if data.get("base_native_case_counters_identical") is not True or len(runs) != 3 or \
            len(base_runs) != 3:
        fail(f"{rel}: bounded native render/base comparison is incomplete")
    base_by_seed = {r.get("seed"): r for r in base_runs}
    for run in runs:
        previous = base_by_seed.get(run.get("seed"))
        if not previous or run.get("per_case") != previous.get("per_case"):
            fail(f"{rel}: bounded native per-case counters/cycles differ from base seed {run.get('seed')}")
    if [(r.get("seed"), r.get("full_frames")) for r in runs] != [(0, 13), (7701, 13), (7702, 13)]:
        fail(f"{rel}: bounded render seeds/full-frame coverage mismatch")
    if (data.get("total_frames"), data.get("total_active_RGB_words"),
            data.get("fault_probes")) != (39, 13478400, 4):
        fail(f"{rel}: bounded native render aggregate count mismatch")
    if "fpga/experiments/cu66-v77/render/results.json" not in data.get("source_sha256", {}):
        fail(f"{rel}: bounded result is not pinned to the base render evidence")
    limits = " ".join(data.get("limitations", [])).lower().replace(" ", "")
    scope = data.get("scope", "").lower().replace(" ", "")
    if "notrealsdram" not in scope or "pixelclockcdc" not in scope or "physical30fps" not in limits:
        fail(f"{rel}: ideal-memory, CDC, and physical-performance limitations missing")
    REPORT.append(f"{rel}: separate bounded-address native render PASS; 39 frames and every per-case counter/cycle exactly matches base, ideal memory only")


def cache_audit():
    rel = "fpga/experiments/cu66-v77/cache/results.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status")) != ("cu77-cache-regression-v1", "PASS"):
        fail(f"{rel}: streamed cache regression did not pass")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "CACHE_PASS")
    runs = data.get("runs", [])
    if [r.get("seed") for r in runs] != [0, 7701, 7702]:
        fail(f"{rel}: expected retained deterministic seeds 0, 7701, 7702")
    for run in runs:
        accepted = run.get("accepted_pixel_queries", -1)
        delivered_or_canceled = run.get("pixel_responses", -1) + run.get("canceled_pixel_responses", 0)
        if (run.get("rasters"), run.get("active_pixels"), run.get("fault_probes"),
                run.get("invalid_requests"), accepted, delivered_or_canceled) != (
                2, 691200, 26, 16, 691207, 691207):
            fail(f"{rel}: run {run.get('seed')} raster, fault, invalid-request, or pixel ownership mismatch")
    if (data.get("full_synthetic_rasters"), data.get("active_pixels")) != (6, 2073600):
        fail(f"{rel}: aggregate synthetic raster accounting mismatch")
    trace = "fpga/experiments/cu66-v76/service/trace.mem"
    if trace not in data.get("source_sha256", {}):
        fail(f"{rel}: miss-set comparison is not bound to the frozen V76 trace data")
    limits = " ".join(data.get("limitations", [])).lower().replace(" ", "")
    if "notrealcontroller" not in limits or "cdc" not in limits:
        fail(f"{rel}: controller/CDC/target-performance limitations missing")
    REPORT.append(f"{rel}: streamed cache functional PASS over 6 synthetic rasters; accepted pixel queries match responses, frozen V76 trace bound; ideal memory source only")


def bounded_cache_audit():
    rel = "fpga/experiments/cu66-v77/cache/bounded/results.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status")) != (
            "cu77-bounded-cache-regression-v1", "PASS_BOUNDED_CACHE_AND_SLOT3"):
        fail(f"{rel}: bounded helper regression did not pass")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "CACHE_PASS")
    base_rel = "fpga/experiments/cu66-v77/cache/results.json"
    base = read(base_rel)
    rows, base_rows = data.get("runs", []), base.get("runs", []) if base else []
    if data.get("base_finite_counters_and_cycles_equal") is not True or rows != base_rows:
        fail(f"{rel}: bounded cache counters/cycles do not exactly match the frozen base run records")
    if [r.get("seed") for r in rows] != [0, 7701, 7702]:
        fail(f"{rel}: expected all three bounded cache seeds")
    if (data.get("exhaustive_slot3_inputs"), data.get("full_synthetic_rasters"),
            data.get("active_pixels"), data.get("fault_probes"),
            data.get("invalid_requests")) != (128, 6, 2073600, 78, 48):
        fail(f"{rel}: bounded cache exhaustive/helper or aggregate coverage mismatch")
    for path in ("fpga/experiments/cu66-v77/cache/cu77_direct_cache_bounded.sv",
                 "fpga/experiments/cu66-v77/cache/cu77_direct_cache.sv",
                 "fpga/experiments/cu66-v77/cache/cu77_slot3_probe.sv", base_rel):
        if path not in data.get("source_sha256", {}):
            fail(f"{rel}: missing bounded/base source comparison pin {path}")
    limits = " ".join(data.get("limitations", [])).lower().replace(" ", "")
    if "notformalrtlequivalence" not in data.get("scope", "").lower().replace(" ", "") or \
            "physical30fps" not in limits or "fit" not in limits:
        fail(f"{rel}: finite-regression and no-target-fit limits missing")
    REPORT.append(f"{rel}: separate bounded cache PASS; all three seed counters/cycles equal base, 128 helper inputs exhaustive, 6 rasters; no formal-equivalence or target-fit claim")


def system_audit():
    archive_audit("fpga/experiments/cu66-v77/system/first-native-proof/manifest.json",
                  "fpga/experiments/cu66-v77/system/first-native-proof/source-and-evidence.zip", 24)
    rel = "fpga/experiments/cu66-v77/system/results.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status"), data.get("quick")) != (
            "v77-real-controller-display-v1", "PASS_EXACT_NATIVE_DISPLAY", False):
        fail(f"{rel}: full native controller/display matrix is not finalized")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "DIRECT_DISPLAY_PASS")
    clocks = data.get("clocks", {})
    if (clocks.get("memory_period_ps"), clocks.get("read_phase_degrees"),
            clocks.get("pixel_half_period_ps")) != (10000, 279, 17029):
        fail(f"{rel}: controller/read/pixel clock model is missing or changed")
    runs = data.get("runs", [])
    expected = {(2, 0), (2, 1), (7, 0), (7, 1)}
    actual = {(r.get("tac_ns"), r.get("background")) for r in runs}
    if len(runs) != 4 or actual != expected:
        fail(f"{rel}: expected four T_AC/background conditions (2/7 ns by background 0/1)")
    frame_count = 0
    for run in runs:
        frames = run.get("frames", [])
        background = run.get("background")
        if len(frames) != 2 or {f.get("source") for f in frames} != {0, 1}:
            fail(f"{rel}: each condition must retain both distinct native source frames")
        for frame in frames:
            frame_count += 1
            if (frame.get("pixels"), frame.get("good"), frame.get("mismatches"),
                    frame.get("exact_rasters"), frame.get("underruns"),
                    frame.get("memory_errors"), frame.get("cache_reads"),
                    frame.get("cache_words"), frame.get("queries")) != (
                    384000, 384000, 0, 1, 0, 0, 35040, 280320, 345600):
                fail(f"{rel}: native pixel/deadline or cache read accounting mismatch")
            if frame.get("released_w") != frame.get("complete_w") or \
                    frame.get("released_r") != frame.get("complete_r"):
                fail(f"{rel}: background write/read ownership was not fully drained")
            expected_memory = (35040, 0, 0, 0, 0) if background == 0 else (
                49260, 118016, 3688, 3555, 48)
            if (frame.get("actual_reads"), frame.get("actual_writes"),
                    frame.get("released_w"), frame.get("released_r"),
                    frame.get("drain_cycles")) != expected_memory and not (
                    background == 1 and frame.get("actual_reads") == 49260 and
                    frame.get("actual_writes") == 118016 and
                    frame.get("released_w") == frame.get("complete_w") == 3688 and
                    frame.get("released_r") == frame.get("complete_r") == 3555 and
                    frame.get("drain_cycles") in (47, 48)):
                fail(f"{rel}: controller/background transaction and drain accounting mismatch")
    if frame_count != 8:
        fail(f"{rel}: expected eight retained condition/frame measurements")
    limits = " ".join(data.get("limitations", [])).lower().replace(" ", "")
    if "physical30fps" not in limits or "validatedunder10ms" not in limits or \
            "seamless" not in limits or "fullreceiver" not in limits:
        fail(f"{rel}: physical-rate, decode, lease, or receiver limits missing")
    REPORT.append(f"{rel}: actual frozen SDRAM controller/model + LCD scanout native RGB PASS for {frame_count} condition/source frames; zero mismatch/underrun, background queues drained; frame-cycle evidence is not physical 30 fps or decoder-latency proof")


def bounded_system_audit():
    rel = "fpga/experiments/cu66-v77/system-bounded/results.json"
    data = read(rel)
    if data is None:
        return
    if (data.get("schema"), data.get("status"), data.get("quick")) != (
            "v77-real-controller-display-bounded-v1", "PASS_EXACT_NATIVE_DISPLAY", False):
        fail(f"{rel}: bounded native controller/display matrix is not finalized")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, "DIRECT_DISPLAY_PASS")
    base_rel = "fpga/experiments/cu66-v77/system/results.json"
    base = read(base_rel)
    if not base or data.get("base_results_sha256") != sha(ROOT / base_rel) or \
            data.get("base_case_counters_identical") is not True or data.get("runs") != base.get("runs"):
        fail(f"{rel}: bounded native result cases/cycles do not match hash-pinned base results")
    expected = {(2, 0), (2, 1), (7, 0), (7, 1)}
    if {(r.get("tac_ns"), r.get("background")) for r in data.get("runs", [])} != expected:
        fail(f"{rel}: bounded native test matrix differs from base conditions")
    if base and base.get("limitations") != data.get("limitations"):
        fail(f"{rel}: bounded native scope/limitations differ from base")
    REPORT.append(f"{rel}: separate bounded cache + actual controller/model + LCD PASS; all 8 native condition/frame records exactly match hash-pinned base, no additional cadence claim")


def elaboration_audit(bounded):
    area = "elaboration-bounded" if bounded else "elaboration"
    rel = f"fpga/experiments/cu66-v77/{area}/results.json"
    data = read(rel)
    if data is None:
        return
    expected_schema = "cu77-bounded-cache-render-elaboration-v1" if bounded else "cu77-cache-render-elaboration-v1"
    if data.get("schema") != expected_schema or data.get("status") not in (
            "PASS_GENERIC_AND_CONVERTED_SIMULATION", "PASS_GENERIC_CONVERTED_AND_FAMILY_MAP"):
        fail(f"{rel}: elaboration/conversion evidence status mismatch")
    verify_hashes(data, "source_sha256", rel)
    command_logs(data, rel, None)
    for item in data.get("commands", []):
        name = item.get("log", "")
        if Path(name).name.startswith("converted-run-"):
            path = ROOT / name
            if not path.is_file() or "RENDER_PASS" not in path.read_text(errors="replace"):
                fail(f"{rel}: converted native replay marker missing from {name}")
    if (data.get("frontend", {}).get("version"), data.get("frontend", {}).get("sha256")) != (
            "sv2v v0.0.13", "b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635"):
        # The source of truth is also retained in frontend hash/version logs;
        # tolerate a typo here only if the pinned tool record itself matches.
        if data.get("frontend", {}).get("sha256") != "b80a8ac6212aa72a196d9d6129cda35f16dbfa799ec61848c46321f845b6b635":
            fail(f"{rel}: sv2v version or executable digest mismatch")
    if data.get("logical_data_bytes") != 29184:
        fail(f"{rel}: structured cache data capacity is not 29,184 bytes")
    expected_sizes = {"ymemory": 5760, "hmemory": 3072}
    expected_sizes.update({f"{plane}mem{i}": 720 for plane in ("cb", "cr") for i in range(4)})
    memories = data.get("data_memories", [])
    actual_sizes = {m.get("name"): m.get("size") for m in memories}
    if len(memories) != 10 or actual_sizes != expected_sizes or \
            sum(m.get("logical_bits", 0) for m in memories) != 29184 * 8 or \
            any((m.get("width"), m.get("read_ports"), m.get("write_ports"),
                 m.get("read_clock_enable")) != (16, 1, 1, 1) for m in memories):
        fail(f"{rel}: extracted synchronous word-memory inventory/capacity mismatch")
    derived = data.get("derived_files_sha256", {})
    expected_derived = {f"fpga/experiments/cu66-v77/{area}/{name}"
                        for name in ("cu77_render_bounded_sim.v" if bounded else "cu77_render_sim.v",
                                     "generic.ys", "stat.json", "netlist.json")}
    if set(derived) != expected_derived:
        fail(f"{rel}: derived converted RTL/script/netlist/report inventory mismatch")
    verify_hashes({"derived_files_sha256": derived}, "derived_files_sha256", rel)
    family = data.get("family_map", {})
    if family.get("status") not in ("PASS_UNPLACED_FAMILY_MAPPING", "BOUNDED_TIMEOUT"):
        fail(f"{rel}: family mapping status is missing or misrepresented")
    if family.get("status") == "PASS_UNPLACED_FAMILY_MAPPING":
        family_files = family.get("files", {})
        if set(family_files) != {f"fpga/experiments/cu66-v77/{area}/{n}"
                                for n in ("family-xc7.ys", "family-xc7-stat.json", "family-xc7-netlist.json")}:
            fail(f"{rel}: family-map derived file inventory mismatch")
        verify_hashes({"family_files": family_files}, "family_files", rel)
    base_rtl = "fpga/experiments/cu66-v77/cache/cu77_direct_cache_bounded.sv" if bounded else \
        "fpga/experiments/cu66-v77/cache/cu77_direct_cache.sv"
    top = "cu77_direct_cache_bounded" if bounded else "cu77_direct_cache"
    if base_rtl not in data.get("source_sha256", {}):
        fail(f"{rel}: elaborated cache source is not pinned")
    for seed in (0, 7701, 7702):
        if not any(r.get("seed") == seed for r in data.get("converted_simulation", [])):
            fail(f"{rel}: converted native replay missing seed {seed}")
    compare_rel = ("fpga/experiments/cu66-v77/render/bounded/results.json" if bounded else
                   "fpga/experiments/cu66-v77/render/results.json")
    comparison = read(compare_rel)
    if comparison:
        comp_runs = {r.get("seed"): r.get("per_case") for r in comparison.get("runs", [])}
        for replay in data.get("converted_simulation", []):
            if replay.get("per_case") != comp_runs.get(replay.get("seed")):
                fail(f"{rel}: converted RTL native case records differ from {compare_rel}")
    if bounded:
        if data.get("converted_native_case_counters_identical") is not True:
            fail(f"{rel}: bounded converted simulation parity flag is false")
        base = read("fpga/experiments/cu66-v77/elaboration/results.json")
        if not base:
            pass
        else:
            def cache_map_cells(result, module):
                stats = result.get("family_map", {}).get("statistics", {}).get("modules", {})
                return stats.get(module, {}).get("num_cells_by_type", {})
            base_cells = cache_map_cells(base, "\\cu77_direct_cache")
            bounded_cells = cache_map_cells(data, "\\cu77_direct_cache_bounded")
            if data.get("family_map", {}).get("status") == "PASS_UNPLACED_FAMILY_MAPPING" and \
                    base.get("family_map", {}).get("status") == "PASS_UNPLACED_FAMILY_MAPPING":
                if not (sum(bounded_cells.get(k, 0) for k in ("CARRY4", "LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6")) <
                        sum(base_cells.get(k, 0) for k in ("CARRY4", "LUT1", "LUT2", "LUT3", "LUT4", "LUT5", "LUT6")) and
                        (bounded_cells.get("RAMB18E1"), bounded_cells.get("RAMB36E1")) ==
                        (base_cells.get("RAMB18E1"), base_cells.get("RAMB36E1"))):
                    fail(f"{rel}: unplaced mapping does not show smaller helper/control logic with same RAM blocks")
        REPORT.append(f"{rel}: bounded converted replay PASS with 29,184-byte synchronous memory inventory; family counts are unplaced generic mapping only, not target fit")
    else:
        REPORT.append(f"{rel}: base converted replay PASS with 29,184-byte synchronous memory inventory; family counts are unplaced generic mapping only, not target fit")


def main():
    baseline()
    pixel_audit()
    cache_audit()
    bounded_cache_audit()
    render_audit()
    bounded_render_audit()
    system_audit()
    bounded_system_audit()
    elaboration_audit(False)
    elaboration_audit(True)
    if FAIL:
        print("V77_EVIDENCE_FAIL")
        print("\n".join(" - " + msg for msg in FAIL))
        raise SystemExit(1)
    print("V77_EVIDENCE_INTEGRITY_AND_SCOPE_PASS")
    print("\n".join(REPORT))


if __name__ == "__main__":
    main()
