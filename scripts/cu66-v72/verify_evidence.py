#!/usr/bin/env python3
"""Read-only integrity, count, and scope audit for CU66 v72 evidence."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v72'
FAILURES = []
REPORT = []


def fail(message):
    FAILURES.append(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path, label):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        fail(f'{label}: cannot read valid JSON at {path.relative_to(ROOT)}: {exc}')
        return None


def check_pins(result, label):
    pins = result.get('source_sha256')
    if not isinstance(pins, dict) or not pins:
        fail(f'{label}: missing or empty source_sha256')
        return 0
    for rel, expected in sorted(pins.items()):
        path = ROOT / rel
        if not path.is_file():
            fail(f'{label}: source pin missing: {rel}')
        elif sha(path) != expected:
            fail(f'{label}: stale source pin: {rel}')
    return len(pins)


def log_path(result_path, log_name):
    path = Path(log_name)
    if path.is_absolute():
        return path
    root_relative = ROOT / path
    local_relative = result_path.parent / path
    # Producers use either repository-relative paths or log basenames relative
    # to the result directory. Prefer an existing repository-relative target.
    if root_relative.is_file():
        return root_relative
    return local_relative


def check_commands(result, result_path, label):
    commands = result.get('commands')
    if not isinstance(commands, list) or not commands:
        fail(f'{label}: missing command records')
        return 0
    for index, command in enumerate(commands):
        tag = f'{label} command[{index}]'
        if not isinstance(command, dict):
            fail(f'{tag}: invalid command record')
            continue
        if command.get('exit_code') != 0:
            fail(f'{tag}: exit_code is not zero ({command.get("exit_code")})')
        name = command.get('log')
        if not name:
            fail(f'{tag}: no retained log path')
            continue
        path = log_path(result_path, name)
        if not path.is_file():
            fail(f'{tag}: missing log {name}')
            continue
        if command.get('sha256') != sha(path):
            fail(f'{tag}: log hash mismatch {name}')
            continue
        basename = path.name.lower()
        is_build = 'build' in basename or basename.endswith('.jou')
        if not is_build:
            content = path.read_text(encoding='utf-8', errors='replace')
            if not any(marker in content for marker in (
                    'PASS', 'SYSTEM_PASS', 'MEMORY_V72_PASS',
                    'MEMORY_V72_RESET_PASS', 'MEMORY_V72_CACHE_PASS',
                    'CONTROLLER_V72_PASS', 'CASE_PASS', 'START_REJECT_PASS')):
                fail(f'{tag}: runtime log lacks a terminal PASS marker: {name}')
            if re.search(r'(^|\s)(FAIL|FATAL)(\s|:|$)', content, re.M):
                fail(f'{tag}: runtime log contains FAIL/FATAL: {name}')
    return len(commands)


def audit_result(rel, required_status=None):
    path = ROOT / rel
    data = read_json(path, rel)
    if data is None:
        return None
    status = data.get('status')
    if required_status is not None and status != required_status:
        fail(f'{rel}: status {status!r}, expected {required_status!r}')
    source_count = check_pins(data, rel)
    command_count = check_commands(data, path, rel)
    REPORT.append(f'{rel}: source_pins={source_count}, commands={command_count}')
    return data


def check_controller():
    rel = 'fpga/experiments/cu66-v72/memory/controller/results.json'
    data = audit_result(rel, 'PASS')
    if data is None:
        return
    if data.get('schema') != 'cu72-controller-results-v1':
        fail(f'{rel}: unexpected schema')
    runs = data.get('runs', [])
    expected = {(backend, tac, seed) for backend in ('verilator', 'iverilog')
                for tac in (2, 7) for seed in (7201, 7202)}
    actual = {(r.get('backend'), r.get('tac_ns'), r.get('seed')) for r in runs}
    if len(runs) != 8 or actual != expected:
        fail(f'{rel}: expected 8 backend/tAC/seed runs; got {len(runs)}')
    for row in runs:
        if row.get('checks', 0) <= 0 or row.get('writes') != 195 or row.get('reads') != 212:
            fail(f'{rel}: invalid controller counts: {row}')
        if row.get('reset_probes') != 9 or row.get('reset_edge_probes') != 1 or row.get('mask_cases') != 8:
            fail(f'{rel}: reset/mask coverage mismatch: {row}')


def check_adapters():
    rel = 'fpga/experiments/cu66-v72/memory/adapters/results.json'
    data = audit_result(rel, 'PASS')
    if data is None:
        return
    if data.get('schema') != 'cu72-memory-component-results-v1':
        fail(f'{rel}: unexpected schema')
    runs = data.get('runs', [])
    expected = {(b, t, s, scenario) for b in ('verilator', 'iverilog')
                for t in (2, 7) for s in (7101, 7102)
                for scenario in ('continuous', 'bubble', 'bank3-conflict')}
    expected |= {(b,t,None,'reset') for b in ('verilator','iverilog') for t in (2,7)}
    actual = {(r.get('backend'), r.get('tac_ns'), r.get('seed'), r.get('scenario'))
              for r in runs}
    if len(runs) != 28 or actual != expected:
        fail(f'{rel}: expected 28 main runs (24 scenarios plus 4 resets); got {len(runs)}')
    caches = data.get('cache_runs', [])
    cache_expected = {(b, t) for b in ('verilator', 'iverilog') for t in (2, 7)}
    cache_actual = {(r.get('backend'), r.get('tac_ns')) for r in caches}
    if len(caches) != 4 or cache_actual != cache_expected:
        fail(f'{rel}: expected 4 direct masked-write/cache-alias runs; got {len(caches)}')
    for row in runs:
        if row.get('scenario') == 'reset':
            if row.get('probes') != 4 or row.get('fresh_bursts') != 4 or row.get('fresh_words') != 32:
                fail(f'{rel}: reset recovery counts mismatch: {row}')
        elif (row.get('checks') != 9078 or row.get('tiles') != 237 or
              row.get('aux') != 6751 or row.get('aborts') != 43 or
              row.get('burst_checks') != 23 or row.get('burst_aborts') != 8 or
              row.get('lcd_bursts') != 250 or row.get('lcd_words') != 2000 or
              row.get('lcd_rejects') != 3 or row.get('lcd_line_max', 99999) > 1842):
            fail(f'{rel}: memory scenario count/bound mismatch: {row}')
    for row in caches:
        if row.get('checks') != 19 or row.get('cache_misses') != 1:
            fail(f'{rel}: masked cache alias checks mismatch: {row}')


def check_display():
    rel = 'fpga/experiments/cu66-v72/display/results.json'
    data = audit_result(rel, 'PASS')
    if data is None:
        return
    runs = data.get('runs', [])
    if ({r.get('seed') for r in runs} != {0, 7201, 7202} or len(runs) != 3 or
        data.get('total_rasters') != 39 or
        data.get('total_compared_RGB_words') != 14976000 or
        data.get('total_fault_probes') != 10 or data.get('start_rejects') != 30):
        fail(f'{rel}: expected 3 seeds, 39 rasters, 14,976,000 RGB words, 10 fault probes, 30 rejected starts')
    for row in runs:
        expected_faults = 0 if row.get('seed') == 0 else 5
        if row.get('full_rasters') != 13 or row.get('fault_probes') != expected_faults:
            fail(f'{rel}: painter per-seed counts mismatch: {row}')
        good = [case for case in row.get('per_case', []) if case.get('mode') == 0]
        if len(good) != 13 or any(c.get('write_commands') != 48000 or
                                  c.get('write_words') != 384000 or
                                  c.get('painted') != 345600 for c in good):
            fail(f'{rel}: exact full-raster case counts mismatch for seed {row.get("seed")}')


def check_control():
    rel = 'fpga/experiments/cu66-v72/system/control-results.json'
    data = audit_result(rel, 'PASS')
    if data is None:
        return
    counts = data.get('counts', {})
    expected = {'actual_keys_parsed': 2, 'completed_HUD_words': 2,
                'denied_writes': 7, 'abort_drained': 2,
                'early_HUD_drain_rejected': 1, 'accepted_frames': 0}
    for key, value in expected.items():
        if counts.get(key) != value:
            fail(f'{rel}: {key}={counts.get(key)!r}, expected {value}')
    if not all(any(term in item.lower() for item in data.get('not_proven', []))
               for term in ('cadence', 'fmax')):
        fail(f'{rel}: target cadence/fit limitations are not explicit')


def check_system(rel, frame_count):
    data = audit_result(rel, 'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS')
    if data is None:
        return None
    if data.get('cadence_status') != 'NOT_QUALIFIED' or not data.get('strip'):
        fail(f'{rel}: expected strip run with cadence NOT_QUALIFIED')
    if 'notvalidatedtargetlatency' not in data.get('timing_scope', '').lower():
        fail(f'{rel}: model timing is not explicitly distinguished from target latency')
    limitations = ' '.join(data.get('limitations', [])).lower()
    if 'no physical30fps' not in limitations or 'no targetfmax/fit' not in limitations:
        fail(f'{rel}: physical cadence and target-fit limitations are not explicit')
    frames = data.get('frames', [])
    summary = data.get('summary', {})
    timings=data.get('timings',[])
    if summary.get('distinct_complete_presentations')!=frame_count or len(timings)!=frame_count or len({t.get('fid') for t in timings})!=frame_count or any(t.get('complete_rasters',0)<1 for t in timings):
        fail(f'{rel}: missing distinct complete source raster evidence')
    for frame,t in zip(frames,timings):
        if (frame.get('fid'),frame.get('generation'))!=(t.get('fid'),t.get('generation')) or not(t['packet_complete_cycle']<=t['admission_cycle']<t['validated_ready_cycle']<t['rgb_ready_cycle']<=t['commit_ack_cycle']) or t['validated_decode_model_cycles']!=t['validated_ready_cycle']-t['packet_complete_cycle'] or t['composition_model_cycles']!=t['rgb_ready_cycle']-t['validated_ready_cycle']:
            fail(f'{rel}: source/phase event mismatch')
    if len(frames) != frame_count or summary.get('complete_frames') != frame_count:
        fail(f'{rel}: expected {frame_count} complete frames; found {len(frames)}')
    if summary.get('total_underruns') != 0 or summary.get('physical_fps_proven') != 0:
        fail(f'{rel}: nonzero underruns or physical cadence claim')
    for frame in frames:
        if (frame.get('actual_writes') != 664320 or
            frame.get('actual_write_commands') != 133920 or
            frame.get('actual_write_bus_beats') != 1071360 or
            frame.get('painter_write_commands') != 48000 or
            frame.get('painter_write_words') != 384000):
            fail(f'{rel}: frame write accounting mismatch: {frame.get("fid")}')
    return data


def check_comparison():
    rel = 'fpga/experiments/cu66-v72/system/comparison.json'
    data = read_json(ROOT / rel, rel)
    if data is None:
        return
    if data.get('status') != 'PASS_EXACT_OUTPUT_COMPARISON':
        fail(f'{rel}: missing exact-output comparison PASS')
    source = ROOT / 'fpga/experiments/cu66-v72/system/full-strip/results.json'
    old = ROOT / 'fpga/experiments/cu66-v71/system/full-strip/results.json'
    for path in (source, old):
        key = str(path.relative_to(ROOT))
        if data.get('input_sha256', {}).get(key) != sha(path):
            fail(f'{rel}: stale or missing comparison input hash {key}')
    script = ROOT / 'scripts/cu66-v72/compare_system.py'
    if data.get('script_sha256') != sha(script):
        fail(f'{rel}: stale comparison script hash')
    if len(data.get('frames', [])) != 2 or data.get('summary', {}).get('v72_underruns') != 0:
        fail(f'{rel}: expected two exact-comparison frame records and zero v72 underruns')
    limitations = ' '.join(data.get('limitations', [])).lower()
    if 'physical30fps' not in limitations or 'sub10ms' not in limitations:
        fail(f'{rel}: missing physical 30fps / target sub-10ms limitations')


def check_archive():
    base = AREA / 'system/before-reset-gate'
    manifest_path = base / 'manifest.json'
    archive = base / 'source-and-evidence.zip'
    manifest = read_json(manifest_path, 'superseded before-reset-gate archive')
    if manifest is None:
        return
    if not archive.is_file():
        fail('superseded archive: missing source-and-evidence.zip')
        return
    if sha(archive) != manifest.get('archive_sha256'):
        fail('superseded archive: archive SHA256 mismatch')
        return
    entries = manifest.get('files_sha256', {})
    try:
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            if names != set(entries):
                fail(f'superseded archive: ZIP membership mismatch ({len(names)} vs {len(entries)})')
            for name, expected in entries.items():
                try:
                    actual = hashlib.sha256(zf.read(name)).hexdigest()
                except KeyError:
                    continue
                if actual != expected:
                    fail(f'superseded archive: member hash mismatch {name}')
    except (OSError, zipfile.BadZipFile) as exc:
        fail(f'superseded archive: unreadable ZIP: {exc}')


def check_preflights():
    rel='fpga/experiments/cu66-v72/memory/elaboration/results.json'
    d=read_json(ROOT/rel,rel)
    if d:
        if d.get('status')!='UNAVAILABLE_FRONTEND' or len(d.get('runs',[]))!=3:
            fail('generic preflight: missing unavailable-frontend status')
        check_pins(d,'generic unavailable preflight')
        for c in d.get('commands',[]):
            path=log_path(ROOT/rel,c['log'])
            if not path.is_file() or sha(path)!=c.get('sha256') or c.get('exit_code') not in (0,1):fail('generic preflight log/status mismatch')
        for row in d.get('runs',[]):
            if row.get('status')!='NOT_ELABORATED' or row.get('statistics') is not None or row.get('logical_memories') is not None:fail('generic preflight: unqualified statistics claimed')
            for name,h in row.get('files',{}).items():
                if sha(ROOT/name)!=h:fail('generic preflight: script hash mismatch '+name)
        REPORT.append('generic preflight: UNAVAILABLE_FRONTEND; three leaves not elaborated; no resource claim')
    rel='fpga/experiments/cu66-v72/build/status.json'
    d=read_json(ROOT/rel,rel)
    if d:
        if d.get('status')!='UNAVAILABLE_EXACT_PART' or d.get('exit_code')!=2 or d.get('target_part')!='xc7a100tcsg324-1' or d.get('synthesis_started') is not False or d.get('implementation_started') is not False:fail('OOC preflight: unqualified target status')
        check_pins(d,'OOC unavailable preflight')
        folder=(ROOT/rel).parent
        if sha(folder/'ooc_system.tcl')!=d.get('script_sha256') or sha(ROOT/d['source_spec'])!=d.get('source_spec_sha256'):fail('OOC preflight: source list/Tcl mismatch')
        for name,h in d.get('include_header_sha256',{}).items():
            if sha(ROOT/name)!=h:fail('OOC preflight: include hash mismatch '+name)
        for name,h in d.get('logs_sha256',{}).items():
            if sha(folder/name)!=h:fail('OOC preflight: log hash mismatch '+name)
        REPORT.append('OOC preflight: UNAVAILABLE_EXACT_PART; no synthesis/implementation')


def main():
    # Baseline verifier includes frozen v69/v70/v71 manifests and v71 source pins.
    import subprocess
    baseline = subprocess.run([sys.executable, str(ROOT / 'scripts/cu66-v72/verify_baseline.py')],
                              cwd=ROOT, text=True, capture_output=True, check=False)
    if baseline.returncode:
        fail('frozen baseline audit failed: ' +
             (baseline.stdout + baseline.stderr).strip().replace('\n', ' | '))
    else:
        REPORT.append(baseline.stdout.strip())

    check_controller()
    check_adapters()
    check_display()
    check_control()
    full = check_system('fpga/experiments/cu66-v72/system/full-strip/results.json', 2)
    check_system('fpga/experiments/cu66-v72/system/history-4-strip/results.json', 4)
    check_comparison()
    check_archive()
    check_preflights()

    if FAILURES:
        print('V72_EVIDENCE_AUDIT_FAIL')
        for item in FAILURES:
            print('  ' + item)
        return 1
    print('V72_EVIDENCE_AUDIT_PASS')
    for line in REPORT:
        print('  ' + line)
    print('  functional/model evidence only; no target-fit, physical 30fps, or target sub-10ms verdict')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
