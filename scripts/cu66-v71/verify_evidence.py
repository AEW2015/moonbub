#!/usr/bin/env python3
"""Read-only integrity and declared-count audit for CU66 v71 evidence."""
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v71'


class AuditError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(relpath):
    path = ROOT / relpath
    if not path.is_file():
        raise AuditError(f'missing required final evidence: {relpath}; run the qualified v71 evidence flow first')
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f'invalid JSON in {relpath}: {exc}') from exc


def require(condition, message):
    if not condition:
        raise AuditError(message)


def check_sources(result, label):
    pins = result.get('source_sha256')
    require(isinstance(pins, dict) and bool(pins), f'{label}: missing source_sha256 map')
    for rel, expected in sorted(pins.items()):
        path = ROOT / rel
        require(path.is_file(), f'{label}: missing pinned source {rel}')
        actual = sha256(path)
        require(actual == expected, f'{label}: source hash mismatch {rel}')
    return len(pins)


def resolve_log(result_path, log_value):
    path = Path(log_value)
    candidates = [path if path.is_absolute() else ROOT / path]
    if not path.is_absolute():
        candidates.append(result_path.parent / path)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def check_commands(result, result_rel, label, terminal_markers=()):
    commands = result.get('commands')
    require(isinstance(commands, list) and bool(commands), f'{label}: missing command records')
    terminal_seen = {marker: False for marker in terminal_markers}
    for i, command in enumerate(commands):
        prefix = f'{label}: command[{i}]'
        require(command.get('exit_code') == 0, f'{prefix} exit_code is not zero')
        log_value = command.get('log')
        expected = command.get('sha256')
        require(isinstance(log_value, str) and isinstance(expected, str),
                f'{prefix} missing log path/hash')
        log = resolve_log(ROOT / result_rel, log_value)
        require(log.is_file(), f'{prefix} log is missing: {log_value}')
        require(sha256(log) == expected, f'{prefix} log hash mismatch: {log_value}')
        content = log.read_text(encoding='utf-8', errors='replace')
        for marker in terminal_seen:
            if marker in content:
                terminal_seen[marker] = True
    for marker, seen in terminal_seen.items():
        require(seen, f'{label}: no qualified command log contains terminal marker {marker}')
    return len(commands)


def check_archive(dirname, label):
    rel = f'fpga/experiments/cu66-v71/system/{dirname}/manifest.json'
    d = load(rel)
    archive_rel = f'fpga/experiments/cu66-v71/system/{dirname}/source-and-evidence.zip'
    archive = ROOT / archive_rel
    require(archive.is_file(), f'initial archive missing: {archive_rel}')
    require(sha256(archive) == d.get('archive_sha256'), 'initial archive ZIP hash mismatch')
    files = d.get('files_sha256')
    require(isinstance(files, dict) and bool(files), 'initial archive manifest has no file pins')
    with ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        for relpath, expected in sorted(files.items()):
            require(relpath in names, f'initial archive is missing pinned member {relpath}')
            actual = hashlib.sha256(bundle.read(relpath)).hexdigest()
            require(actual == expected, f'initial archive member hash mismatch {relpath}')
    scope = d.get('scope', '').lower()
    require('superseded' in scope and 'not final qualification' in scope,
            f'{label} archive is not clearly labeled superseded/nonfinal')
    return len(files)


def check_memory():
    rel = 'fpga/experiments/cu66-v71/memory/results.json'
    d = load(rel)
    require(d.get('schema') == 'cu71-memory-component-results-v1' and d.get('status') == 'PASS',
            'memory: expected PASS cu71-memory-component-results-v1')
    runs = d.get('runs', [])
    require(len(runs) == 28, f'memory: expected 28 runs, got {len(runs)}')
    expected = {(backend, tac, seed, scenario)
                for backend in ('verilator', 'iverilog') for tac in (2, 7)
                for seed in (7101, 7102)
                for scenario in ('continuous', 'bubble', 'bank3-conflict')}
    expected |= {(backend, tac, None, 'reset')
                 for backend in ('verilator', 'iverilog') for tac in (2, 7)}
    keys = {(r.get('backend'), r.get('tac_ns'), r.get('seed'), r.get('scenario')) for r in runs}
    require(keys == expected, 'memory: unexpected/duplicate backend, timing, seed, or scenario matrix')
    for run in runs:
        if run['scenario'] == 'reset':
            require(run.get('probes') == 4 and run.get('hold_clocks') == 32 and run.get('fresh_bursts') == 4 and run.get('fresh_words') == 32, 'memory: reset/held-response probe counts disagree')
            continue
        require(run.get('lcd_bursts', 0) > 0 and run.get('lcd_words', 0) == run['lcd_bursts'] * 8,
                'memory: LCD burst/word accounting is inconsistent')
        require(run.get('checks') == 8143 and run.get('tiles') == 231 and run.get('aux') == 5871 and run.get('aborts') == 43 and run.get('lcd_bursts') == 250 and run.get('lcd_words') == 2000 and run.get('lcd_rejects') == 3, 'memory: functional operation/probe counts disagree')
        require(run.get('max_lcd_streak') == 4 and run.get('lcd_line_max', 999999) <= 1842 and run.get('grace_blocks', 0) > 0 and run.get('silent_wait') == 2, 'memory: tested deadline, grant saturation or finite-grace probe failed')
    for run in runs:
        if run['scenario'] == 'reset':
            needle = f"{run['backend']}-tac{run['tac_ns']}-reset.log"
            marker = 'MEMORY_V71_RESET_PASS '
        else:
            needle = (f"{run['backend']}-tac{run['tac_ns']}-{run['seed']}-"
                      f"{run['scenario']}.log")
            marker = 'MEMORY_V71_PASS '
        matches = [c for c in d.get('commands', []) if needle in c.get('log', '')]
        require(len(matches) == 1, f'memory: expected one qualified runtime log {needle}')
        log = resolve_log(ROOT / rel, matches[0]['log'])
        require(marker in log.read_text(encoding='utf-8', errors='replace'),
                f'memory: terminal pass marker absent from {needle}')
    budget = load('fpga/experiments/cu66-v71/memory/line-budget.json')
    require(budget.get('source_results_sha256') == sha256(ROOT / rel), 'memory line budget: stale result hash')
    require(budget.get('native_line_period_clocks') == 1842.5378, 'memory line budget: changed clock definition')
    for scenario, row in budget.get('scenarios', {}).items():
        selected = [r for r in runs if r.get('scenario') == scenario]
        require(len(selected) == row.get('runs') == 8 and row.get('min_clocks') == min(r['lcd_line_min'] for r in selected) and row.get('max_clocks') == max(r['lcd_line_max'] for r in selected) and row.get('all_within_native_period') is True, 'memory line budget: scenario accounting mismatch')
    require(set(budget.get('scenarios', {})) == {'continuous', 'bubble', 'bank3-conflict'}, 'memory line budget: scenario set mismatch')
    sources = check_sources(d, 'memory')
    commands = check_commands(d, rel, 'memory')
    return f'memory: {len(runs)} runs, {commands} command logs, {sources} source pins'


def check_elaboration():
    rel = 'fpga/experiments/cu66-v71/memory/elaboration-results.json'
    d = load(rel)
    require(d.get('schema') == 'cu71-generic-leaf-elaboration-v1' and d.get('status') == 'PASS',
            'elaboration: expected PASS generic leaf schema')
    runs = d.get('runs', [])
    require(len(runs) == 2 and {r.get('name') for r in runs} == {'v70', 'v71'},
            'elaboration: expected exactly v70 and v71 leaf runs')
    require({r.get('top') for r in runs} == {'cu70_word_bridge', 'cu71_word_bridge'},
            'elaboration: expected matching word-bridge tops')
    for run in runs:
        stats = run.get('statistics', {})
        require(stats.get('num_processes') == 0 and stats.get('num_cells', 0) > 0 and
                run.get('generic_flip_flop_bits', 0) > 0,
                f"elaboration: {run.get('name')} has structural problems or missing statistics")
        files = run.get('files', {})
        require(isinstance(files, dict) and len(files) == 3,
                f"elaboration: {run.get('name')} expected script/stat/netlist file pins")
        for relpath, expected in sorted(files.items()):
            path = ROOT / relpath
            require(path.is_file(), f'elaboration: missing output {relpath}')
            require(sha256(path) == expected, f'elaboration: output hash mismatch {relpath}')
    limitations = ' '.join(d.get('limitations', [])).lower()
    require('no techmap/synth_xilinx run' in limitations and
            'neither fpga lut/ff/bram usage nor timing' in limitations,
            'elaboration: generic-only resource/timing limitations are missing')
    sources = check_sources(d, 'elaboration')
    commands = check_commands(d, rel, 'elaboration', ('Found and reported 0 problems.',))
    return f'elaboration: 2 generic leaf versions, {commands} command logs, {sources} source pins, 6 output hashes'


def check_display():
    rel = 'fpga/experiments/cu66-v71/display/results.json'
    d = load(rel)
    require(d.get('status') == 'PASS', 'display: expected PASS status')
    runs = d.get('runs', [])
    require(len(runs) == 5, f'display: expected 5 runs, got {len(runs)}')
    require(sum(r.get('complete_frames', 0) for r in runs) == 10,
            'display: expected 10 complete raster executions across 5 runs')
    require(sum(r.get('compared_pixels', 0) for r in runs) == 3_840_000,
            'display: expected 3,840,000 compared pixels')
    require(d.get('total_complete_rasters') == 10 and d.get('total_compared_pixels') == 3_840_000,
            'display: aggregate raster/pixel counts disagree')
    require(d.get('control_checks') == 31, 'display: expected 31 independent control checks')
    require(sum(1 for r in runs if r.get('mode') == 'normal') == 3 and
            sum(1 for r in runs if r.get('mode') == '--starve') == 1 and
            sum(1 for r in runs if r.get('mode') == '--faults') == 1,
            'display: unexpected normal/starvation/fault run matrix')
    require(all(r.get('underruns') == 0 and r.get('memory_errors') == 0
                for r in runs if r.get('mode') == 'normal'),
            'display: a normal run has underruns or memory errors')
    sources = check_sources(d, 'display')
    commands = check_commands(d, rel, 'display', ('PASS seed=',))
    return f'display: {len(runs)} runs, {d["control_checks"]} control checks, {commands} command logs, {sources} source pins'


def check_control():
    rel = 'fpga/experiments/cu66-v71/system/control-results.json'
    d = load(rel)
    require(d.get('status') == 'PASS', 'system control: expected PASS status')
    counts = d.get('counts', {})
    require(counts.get('accepted_frames') == 0 and counts.get('actual_keys_parsed') == 2 and
            counts.get('early_HUD_drain_rejected') == 1 and counts.get('completed_HUD_words') == 2 and
            counts.get('denied_writes') == 7 and counts.get('abort_drained') == 2,
            'system control: declared rejection/abort probe counts are inconsistent')
    sources = check_sources(d, 'system control')
    commands = check_commands(d, rel, 'system control', ('SYSTEM_CONTROL_PASS ',))
    return f'system control: {commands} command logs, {sources} source pins'


def check_full_strip():
    rel = 'fpga/experiments/cu66-v71/system/full-strip/results.json'
    d = load(rel)
    require(d.get('status') == 'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS' and d.get('strip') is True,
            'full strip: expected functional PASS strip result')
    frames, timings = d.get('frames', []), d.get('timings', [])
    require(len(frames) == 2 and len(timings) == 2 and d.get('summary', {}).get('complete_frames') == 2,
            'full strip: expected two complete frame records and timings')
    require(len({f.get('fid') for f in frames}) == 2, 'full strip: source frame IDs are not distinct')
    require(d.get('cadence_status') in ('FAIL_UNDERRUNS', 'NOT_QUALIFIED') and
            d.get('summary', {}).get('physical_fps_proven') == 0 and
            d.get('summary', {}).get('distinct_complete_presentations') == 2,
            'full strip: cadence/physical scope status is missing or misreported')
    require('WAIT_RGB=validatedready' in d.get('timing_scope', '') and
            'nativeHUDsoftwareiszero-simtime' in d.get('timing_scope', ''),
            'full strip: validated-ready/native CPU timing scope not recorded')
    qualified_ids = {t.get('fid') for t in timings if t.get('complete_rasters', 0) > 0}
    require(len(qualified_ids) == d.get('summary', {}).get('distinct_complete_presentations'),
            'full strip: complete raster/FID accounting mismatch')
    require(all(t.get('packet_complete_cycle', 0) <= t.get('admission_cycle', 0) <
                t.get('validated_ready_cycle', 0) < t.get('rgb_ready_cycle', 0) <=
                t.get('commit_ack_cycle', 0) for t in timings),
            'full strip: timing phases are not monotonic')
    sources = check_sources(d, 'full strip')
    commands = check_commands(d, rel, 'full strip', ('SYSTEM_PASS ',))
    return f'full strip: 2 frames, {commands} command logs, {sources} source pins'


def check_comparison():
    rel = 'fpga/experiments/cu66-v71/system/comparison.json'
    d = load(rel)
    require(d.get('status') == 'PASS_EXACT_OUTPUT_COMPARISON',
            'comparison: expected PASS_EXACT_OUTPUT_COMPARISON')
    require(len(d.get('frames', [])) == 2, 'comparison: expected 2 key+P frame comparisons')
    old_rel = 'fpga/experiments/cu66-v70/system/full-strip/results.json'
    new_rel = 'fpga/experiments/cu66-v71/system/full-strip/results.json'
    old, new = load(old_rel), load(new_rel)
    require(old.get('status') == new.get('status') == 'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS',
            'comparison: both v70/v71 functional outputs must pass')
    require(old.get('strip') is True and new.get('strip') is True and old.get('clocks') == new.get('clocks'),
            'comparison: expected v70/v71 strip runs on matching model clocks')
    common = old.get('source_sha256', {}).keys() & new.get('source_sha256', {}).keys()
    require(bool(common) and all(old['source_sha256'][p] == new['source_sha256'][p] for p in common),
            'comparison: shared source pins differ')
    for row, a, b in zip(d['frames'], old['frames'], new['frames'], strict=True):
        require((row.get('fid'), int(row.get('key', False)), row.get('v70', {}).get('generation'),
                 row.get('v71', {}).get('generation')) ==
                (a.get('fid'), a.get('key'), a.get('generation'), b.get('generation')) and
                b.get('fid') == a.get('fid'),
                'comparison: key/P frame identity or generation mismatch')
    summary = d.get('summary', {})
    require(summary.get('v70_underruns') == old.get('summary', {}).get('total_underruns') and
            summary.get('v71_underruns') == new.get('summary', {}).get('total_underruns') and
            summary.get('v71_distinct_complete_presentations') ==
            new.get('summary', {}).get('distinct_complete_presentations'),
            'comparison: summary does not match result JSONs')
    inputs = d.get('input_sha256', {})
    for item in (old_rel, new_rel):
        path = ROOT / item
        require(path.is_file(), f'comparison: missing input result {item}')
        require(inputs.get(item) == sha256(path), f'comparison: input result hash mismatch {item}')
    script_rel = 'scripts/cu66-v71/compare_system.py'
    script = ROOT / script_rel
    require(script.is_file() and d.get('script_sha256') == sha256(script),
            f'comparison: missing or changed comparison script {script_rel}')
    limitation_text = ' '.join(d.get('limitations', [])).lower()
    require('30fps' in limitation_text and 'sub10ms' in limitation_text,
            'comparison: physical cadence/latency limitations not recorded')
    return f'comparison: 2 v70/v71 key+P comparisons; {len(common)} shared source pins; input/script hashes match'


def check_ooc_unavailable():
    rel = 'fpga/experiments/cu66-v71/build/status.json'
    d = load(rel)
    require(d.get('status') == 'UNAVAILABLE_EXACT_PART' and d.get('exit_code') == 2 and d.get('target_part') == 'xc7a100tcsg324-1', 'OOC: missing or misreported unavailable-part gate')
    require(d.get('synthesis_started') is False and d.get('implementation_started') is False, 'OOC: unavailable part cannot qualify synthesis/implementation')
    sources = check_sources(d, 'OOC unavailable gate')
    folder = ROOT / rel
    require(sha256(folder.parent / 'ooc_system.tcl') == d.get('script_sha256'), 'OOC: Tcl hash mismatch')
    logs = d.get('logs_sha256', {})
    require(len(logs) == 5, 'OOC: expected five version/executable/flow log hashes')
    for name, expected in logs.items():
        require(sha256(folder.parent / name) == expected, 'OOC: log hash mismatch ' + name)
    require('UNAVAILABLE_EXACT_PART: xc7a100tcsg324-1 is not installed' in (folder.parent / 'vivado-stdout.log').read_text(), 'OOC: missing exact unavailable-part transcript')
    return f'OOC: UNAVAILABLE_EXACT_PART, {sources} source pins and {len(logs)} log hashes; no synthesis'


def main():
    try:
        archived = check_archive('initial-buffered', 'initial buffered')
        elastic = check_archive('elastic-before-grace', 'elastic-before-grace')
        messages = [f'initial archive: {archived} members pinned and labeled superseded',
                    f'elastic archive: {elastic} members pinned and labeled superseded',
                    check_memory(), check_elaboration(), check_display(), check_control(), check_full_strip(), check_comparison(), check_ooc_unavailable()]
        print('V71_EVIDENCE_AUDIT_PASS ' + '; '.join(messages))
        print('Scope: source/log integrity and declared simulation counts only; not physical throughput, target timing/fit, or board proof.')
        return 0
    except (AuditError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f'V71_EVIDENCE_AUDIT_FAIL {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
