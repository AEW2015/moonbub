#!/usr/bin/env python3
"""Independently reconcile current CU66 v70 leaf source/log evidence."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / 'docs/cu66-v70/evidence-audit.json'
OUT_LOG = ROOT / 'docs/cu66-v70/evidence-audit.log'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def choose_hashed_path(rel, expected, local_base=None):
    path = Path(rel)
    candidates = [path] if path.is_absolute() else [ROOT / path]
    if not path.is_absolute() and local_base is not None:
        candidates.append(local_base / path)
        candidates.append(local_base.parent / path)
    for candidate in candidates:
        if candidate.is_file() and sha(candidate) == expected:
            return candidate
    return None


def source_pins(data, local_base):
    claims = []
    for key in ('source_sha256', 'source_sha256_before', 'source_sha256_after'):
        mapping = data.get(key)
        if not isinstance(mapping, dict):
            continue
        for rel, expected in mapping.items():
            actual = choose_hashed_path(rel, expected, local_base)
            claims.append({'path': rel, 'expected': expected,
                           'ok': actual is not None,
                           'resolved': str(actual.relative_to(ROOT)) if actual and ROOT in actual.parents else str(actual) if actual else None})
    if 'source_sha256_before' in data and data.get('source_sha256_before') != data.get('source_sha256_after'):
        claims.append({'path': '<before-after-set>', 'ok': False,
                       'error': 'source pin maps differ'})
    return claims


def verify_result(name, rel_result):
    result_path = ROOT / rel_result
    data = read_json(result_path)
    local_base = result_path.parent
    sources = source_pins(data, local_base)
    logs = []
    commands = data.get('commands', [])
    if not isinstance(commands, list):
        commands = []
    for index, command in enumerate(commands):
        expected = command.get('sha256') or command.get('log_sha256')
        log_rel = command.get('log')
        ok = bool(command.get('exit_code') == 0 and isinstance(command.get('argv'), list)
                  and log_rel and expected and choose_hashed_path(log_rel, expected, local_base))
        logs.append({'index': index, 'path': log_rel, 'ok': ok,
                     'exit_code': command.get('exit_code'), 'expected_sha256': expected})
        script_rel = command.get('script')
        script_hash = command.get('script_sha256')
        if script_rel or script_hash:
            script_ok = bool(script_rel and script_hash and
                             choose_hashed_path(script_rel, script_hash, local_base))
            logs.append({'index': index, 'path': script_rel, 'kind': 'formal_script', 'ok': script_ok,
                         'expected_sha256': script_hash})

    extras = []
    if name == 'control-abi':
        claim = data['test_log']
        path = choose_hashed_path(claim['path'], claim['sha256'], local_base)
        extras.append({'kind': 'test_log', 'path': claim['path'], 'ok': path is not None})
        old = data.get('superseded_initial_run')
        if old:
            path = choose_hashed_path(old['path'], old['sha256'], local_base)
            extras.append({'kind': 'archival_superseded_log', 'path': old['path'], 'ok': path is not None})
    if name == 'formal':
        for run in data.get('runs', []):
            if run.get('witness'):
                path = choose_hashed_path(run['witness'], run.get('witness_sha256', ''), local_base)
                extras.append({'kind': 'reachability_witness', 'path': run['witness'], 'ok': path is not None})
    if name == 'negatives':
        for case in data.get('case_results', []):
            path = choose_hashed_path(case['log'], case['log_sha256'], local_base)
            extras.append({'kind': 'case_log', 'path': case['log'], 'ok': bool(path and case['terminal_pass'])})
        summary = choose_hashed_path(data['summary_log'], data['summary_log_sha256'], local_base)
        extras.append({'kind': 'summary_log', 'path': data['summary_log'], 'ok': summary is not None})
        archived = data.get('preserved_pre_fix_failure')
        if archived:
            path = choose_hashed_path(archived['archive_manifest'], archived['archive_manifest_sha256'], local_base)
            extras.append({'kind': 'pre_fix_archive_manifest', 'path': archived['archive_manifest'], 'ok': path is not None})
        diagnostic = data.get('isolated_asan_diagnostic')
        if diagnostic:
            for path_key, hash_key in (('provenance', 'provenance_sha256'),
                                       ('build_log', 'build_log_sha256'),
                                       ('runtime_log', 'runtime_log_sha256')):
                path = choose_hashed_path(diagnostic[path_key], diagnostic[hash_key], local_base)
                extras.append({'kind': 'private_ASAN_diagnostic', 'path': diagnostic[path_key], 'ok': path is not None})
    if name == 'software-control':
        compat_path = local_base / 'python-compat-results.json'
        compat = read_json(compat_path)
        extras.append({'kind': 'python_compat_result', 'path': str(compat_path.relative_to(ROOT)),
                       'ok': sha(compat_path) == data.get('python_compat_result_sha256')})
        for rel, expected in data.get('examples_sha256', {}).items():
            extras.append({'kind': 'wire_example', 'path': rel,
                           'ok': choose_hashed_path(rel, expected, local_base) is not None})
        codec_path = ROOT / compat.get('python_codec', '')
        extras.append({'kind': 'python_codec', 'path': compat.get('python_codec'),
                       'ok': codec_path.is_file() and sha(codec_path) == compat.get('python_codec_sha256')})
        compat_commands = compat.get('commands', [])
        for index, command in enumerate(compat_commands):
            expected = command.get('log_sha256')
            path = choose_hashed_path(command.get('log', ''), expected, local_base)
            exit_ok = command.get('exit_code') == command.get('expected_exit_code')
            extras.append({'kind': 'python_compat_command', 'index': index,
                           'path': command.get('log'), 'ok': bool(path and exit_ok)})
        for record in compat.get('records', []):
            input_ok = choose_hashed_path(record.get('input', ''), record.get('input_sha256', ''), local_base) is not None
            output_ok = True
            if record.get('valid'):
                output_ok = bool(record.get('output') and record.get('output_sha256') and
                                 choose_hashed_path(record['output'], record['output_sha256'], local_base))
            extras.append({'kind': 'python_compat_input', 'path': record.get('input'), 'ok': input_ok})
            if record.get('valid'):
                extras.append({'kind': 'python_compat_output', 'path': record.get('output'), 'ok': output_ok})

    return {'name': name, 'result': str(result_path.relative_to(ROOT)),
            'result_sha256': sha(result_path), 'declared_status': data.get('status'),
            'scope': data.get('scope'), 'sources': sources, 'commands': logs,
            'extras': extras, 'data': data}


def constants_from_python(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                found[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return found


def add_issue(issues, level, message):
    issues.append({'level': level, 'message': message})


def command_log_text(package, command):
    expected = command.get('sha256') or command.get('log_sha256')
    if not command.get('log') or not expected:
        return ''
    path = choose_hashed_path(command['log'], expected,
                              ROOT / Path(package['result']).parent)
    return path.read_text(encoding='utf-8', errors='replace') if path else ''


def fields_from_line(line):
    fields = {}
    for item in line.split():
        if '=' not in item:
            continue
        key, value = item.split('=', 1)
        try:
            fields[key] = int(value)
        except ValueError:
            fields[key] = value
    return fields


def audit():
    package_paths = {
        'memory': 'fpga/experiments/cu66-v70/memory/results.json',
        'display': 'fpga/experiments/cu66-v70/display/results.json',
        'display-strip-locality': 'fpga/experiments/cu66-v70/display/strip-results.json',
        'display-strip-control': 'fpga/experiments/cu66-v70/display/strip-control-results.json',
        'formal': 'fpga/experiments/cu66-v70/formal/results.json',
        'control-abi': 'fpga/experiments/cu66-v70/control-abi/results/results.json',
        'owner-control': 'fpga/experiments/cu66-v70/owner-control/results.json',
        'system-control': 'fpga/experiments/cu66-v70/system/control-results.json',
        'system-full-direct': 'fpga/experiments/cu66-v70/system/full-direct/results.json',
        'system-full-strip': 'fpga/experiments/cu66-v70/system/full-strip/results.json',
        'negatives': 'fpga/experiments/cu66-v70/negatives/results/results.json',
        'receiver': 'fpga/experiments/cu66-v70/receiver/results.json',
        'software-control': 'fpga/experiments/cu66-v70/software-control/results.json',
    }
    packages = {name: verify_result(name, path) for name, path in package_paths.items()}
    issues = []

    for name, package in packages.items():
        failed_sources = [claim['path'] for claim in package['sources'] if not claim['ok']]
        failed_logs = [claim['path'] for claim in package['commands'] + package['extras'] if not claim['ok']]
        if failed_sources:
            add_issue(issues, 'ERROR', f'{name}: source hash mismatch/missing: {failed_sources[:8]}')
        if failed_logs:
            add_issue(issues, 'ERROR', f'{name}: command/evidence hash mismatch/missing: {failed_logs[:8]}')

    memory = packages['memory']['data']
    memory_map = read_json(ROOT / 'fpga/experiments/cu66-v70/memory/memory-map.json')
    runs = memory.get('runs', [])
    if not (memory.get('status') == 'PASS' and len(runs) == 8 and len(memory.get('commands', [])) == 12
            and memory_map.get('physical_bytes') == 33554432
            and all(r.get('checks') == 3963 and r.get('tiles') == 227 and r.get('aux') == 3695 and r.get('aborts') == 43 for r in runs)):
        add_issue(issues, 'ERROR', 'memory: expected 32 MiB map and eight runs with 3,963 checks/227 tiles/3,695 aux/43 aborts each')
    else:
        for run in runs:
            if run.get('backend') not in ('iverilog', 'verilator') or run.get('cycles') <= 0:
                add_issue(issues, 'ERROR', 'memory: invalid backend or cycle count in run record')
            suffix = '-tac7' if run.get('tac_ns') == 7 else f"-{run['seed']}"
            log_path = ROOT / f"fpga/experiments/cu66-v70/memory/{run['backend']}{suffix}.log"
            expected_marker = (f"MEMORY_PASS seed={run['seed']} checks={run['checks']} "
                              f"tiles={run['tiles']} aux={run['aux']} aborts={run['aborts']} "
                              f"cycles={run['cycles']}")
            if not log_path.is_file() or expected_marker not in log_path.read_text(encoding='utf-8', errors='replace'):
                add_issue(issues, 'ERROR', f"memory: runtime transcript disagrees with run record: {log_path.name}")
    if not any('notvendortimingsignoff' in item for item in memory.get('limitations', [])):
        add_issue(issues, 'WARNING', 'memory: results must remain scoped to the functional command model')

    display = packages['display']['data']
    painter = display.get('painter', [])
    scanout = display.get('scanout', [])
    if not (display.get('status') == 'PASS' and len(painter) == 3 and
            sum(r.get('full_physical_rasters', 0) for r in painter) == 39 and
            all(r.get('full_raster_words') == 384000 and r.get('actual_key_P_frames') == 8 for r in painter) and
            len(scanout) == 4 and sum(r.get('compared_pixels', 0) for r in scanout) == 3072000 and
            all(r.get('complete_frames') == 2 and r.get('descriptors_presented') == 2 and
                r.get('underruns') == r.get('black_lines') for r in scanout)):
        add_issue(issues, 'ERROR', 'display: raster/scanout counts do not reconcile with result expectations')
    elif not any(r.get('starvation') and r.get('underruns') == 1340 and r.get('black_lines') == 1340 for r in scanout):
        add_issue(issues, 'ERROR', 'display: expected separate intentional starvation case is absent')
    locality = packages['display-strip-locality']['data']
    locality_runs = locality.get('runs', [])
    direct_count = sum(r.get('full_rasters', 0) for r in locality_runs if r.get('variant') == 'direct')
    strip_count = sum(r.get('full_rasters', 0) for r in locality_runs if r.get('variant') == 'strip')
    display_runtime_logs = []
    for command in display.get('commands', []):
        argv_text = ' '.join(command.get('argv', []))
        if 'Vcu70_painter' in argv_text or 'Vcu70_scanout' in argv_text:
            text = command_log_text(packages['display'], command)
            if 'Vcu70_painter' in argv_text and '/build/' in argv_text:
                if 'PASS actual_frames=8 patterns=4 recovery=1' not in text:
                    add_issue(issues, 'ERROR', f"display painter runtime lacks complete-run marker: {command.get('log')}")
            if 'Vcu70_scanout' in argv_text and '/build/' in argv_text:
                if 'TEST_PASS_SCANOUT' not in text or not re.search(r'^PASS seed=', text, re.M):
                    add_issue(issues, 'ERROR', f"display scanout runtime lacks terminal marker: {command.get('log')}")
            display_runtime_logs.append(command.get('log'))
    for command in display.get('commands', []):
        if 'control-iverilog.log' in str(command.get('log')) or 'control-verilator.log' in str(command.get('log')):
            if 'TEST_PASS_PAINTER_CONTROL' not in command_log_text(packages['display'], command):
                add_issue(issues, 'ERROR', f"display control runtime lacks terminal marker: {command.get('log')}")

    # Reconcile the previous display-specific auditor's baseline and aggregate counts.
    baseline_doc_path = ROOT / 'fpga/experiments/cu66-v70/display/baseline-files.json'
    baseline_doc = read_json(baseline_doc_path)
    baseline_checks = []
    for rel, expected in baseline_doc.get('files_sha256', {}).items():
        resolved = choose_hashed_path(rel, expected)
        baseline_checks.append({'path': rel, 'ok': resolved is not None})
    display_audit_path = ROOT / 'fpga/experiments/cu66-v70/display/display-audit.json'
    display_audit = read_json(display_audit_path)
    display_verifier_path = ROOT / 'fpga/experiments/cu66-v70/display/verify_display.py'
    declared_display_checks = (len(baseline_doc.get('files_sha256', {})) +
                               len(display.get('source_sha256', {})) +
                               len(locality.get('source_sha256', {})) +
                               len(packages['display-strip-control']['data'].get('source_sha256', {})) +
                               len(display.get('commands', [])) + len(locality.get('commands', [])) +
                               len(packages['display-strip-control']['data'].get('commands', [])))
    if (not all(x['ok'] for x in baseline_checks) or
            display_audit.get('verifier_sha256') != sha(display_verifier_path) or
            display_audit.get('declared_hash_checks') != declared_display_checks or
            display_audit.get('baseline_rasters') != sum(r.get('full_physical_rasters', 0) for r in painter) or
            display_audit.get('comparison_rasters') != direct_count + strip_count or
            display_audit.get('total_painter_words_compared') != (sum(r.get('full_physical_rasters', 0) for r in painter) + direct_count + strip_count) * 384000 or
            display_audit.get('scanout_frames') != sum(r.get('complete_frames', 0) for r in scanout) or
            display_audit.get('scanout_pixels_compared') != sum(r.get('compared_pixels', 0) for r in scanout)):
        add_issue(issues, 'ERROR', 'display audit: baseline pins or aggregate raster/pixel counts do not independently reconcile')

    if not (locality.get('status') == 'PASS' and len(locality_runs) == 4 and direct_count == 26 and strip_count == 26):
        add_issue(issues, 'ERROR', 'display strip locality: expected 26 direct and 26 strip raster runs')
    strip_control = packages['display-strip-control']['data']
    if strip_control.get('status') != 'PASS' or len(strip_control.get('commands', [])) != 4:
        add_issue(issues, 'ERROR', 'display strip-control backend runs are incomplete')
    for command in locality.get('commands', []):
        if 'Vcu70_painter' in ' '.join(command.get('argv', [])) and '/build/' in ' '.join(command.get('argv', [])):
            if 'PASS actual_frames=8 patterns=4 recovery=1' not in command_log_text(packages['display-strip-locality'], command):
                add_issue(issues, 'ERROR', f"display locality runtime lacks terminal marker: {command.get('log')}")
    for command in strip_control.get('commands', []):
        if command.get('argv', []) and command['argv'][0] in ('docker', 'iverilog', 'vvp'):
            if ('final-iverilog.log' in str(command.get('log')) or 'final-verilator.log' in str(command.get('log'))):
                if 'TEST_PASS_STRIP_CONTROL' not in command_log_text(packages['display-strip-control'], command):
                    add_issue(issues, 'ERROR', f"display strip-control runtime lacks terminal marker: {command.get('log')}")

    formal = packages['formal']['data']
    proof_runs = [run for run in formal.get('runs', []) if run.get('kind') == 'proof']
    cover_runs = [run for run in formal.get('runs', []) if run.get('kind') == 'reachability']
    if not (formal.get('status') == 'PASS_BOUNDED' and
            [r.get('solver_steps') for r in proof_runs] == [8, 16, 24] and
            all(r.get('status') == 'PASS_BOUNDED' and r.get('assertions_elaborated') == 16 for r in proof_runs) and
            len(cover_runs) == 5 and all(r.get('status') == 'REACHABLE' for r in cover_runs) and
            'Notaninductiveorunboundedproof' in formal.get('bounds_interpretation', '')):
        add_issue(issues, 'ERROR', 'formal: proof/cover counts or bounded-only disclaimer do not reconcile')
    for command in formal.get('commands', []):
        text = command_log_text(packages['formal'], command)
        if command.get('script', '').startswith('fpga/experiments/cu66-v70/formal/proof-all-'):
            if 'SAT proof finished - no model found: SUCCESS!' not in text:
                add_issue(issues, 'ERROR', f"formal proof log lacks bounded success marker: {command.get('log')}")
        elif command.get('script', '').startswith('fpga/experiments/cu66-v70/formal/reachability-'):
            if 'Dumping SAT model to VCD file' not in text:
                add_issue(issues, 'ERROR', f"formal reachability log lacks a witness dump: {command.get('log')}")

    abi = packages['control-abi']['data']
    constants = constants_from_python(ROOT / 'fpga/experiments/cu66-v70/control-abi/hud_control.py')
    expected_ops = {'PREPARE': 1, 'STATUS': 2, 'READ_CANDIDATE': 3,
                    'ACK_EXTERNAL_WRITE_DRAIN': 4, 'COMMIT': 5, 'ABORT': 6, 'RESET': 7}
    if not (abi.get('status') == 'PASS' and abi.get('tests_passed') == 11 and abi.get('tests_failed') == 0
            and all(constants.get(k) == v for k, v in expected_ops.items())):
        add_issue(issues, 'ERROR', 'control ABI: 11-test claim or authoritative opcode numbering mismatch')
    else:
        abi_log = choose_hashed_path(abi['test_log']['path'], abi['test_log']['sha256'], ROOT / Path(packages['control-abi']['result']).parent)
        if not abi_log or 'Ran 11 tests' not in abi_log.read_text(encoding='utf-8') or '\nOK' not in abi_log.read_text(encoding='utf-8'):
            add_issue(issues, 'ERROR', 'control ABI test log does not independently show 11 passing tests')

    owner = packages['owner-control']['data']
    owner_counts = owner.get('counts', {})
    expected_owner = {'assertions': 618, 'clocks': 561, 'invalid_start_rejections': 13,
                      'watchdog_faults': 1, 'simultaneous_stale_group': 4, 'stale_total': 10,
                      'accepted_frames': 0, 'presented_frames': 0, 'event_sequence': 16,
                      'event_overwrites': 8}
    if not (owner.get('status') == 'PASS' and all(owner_counts.get(k) == v for k, v in expected_owner.items())):
        add_issue(issues, 'ERROR', 'owner-control: expected 618 control assertions and zero accepted/presented frames')
    owner_run = ROOT / 'fpga/experiments/cu66-v70/owner-control/run.log'
    if not owner_run.is_file() or not all(f'{k}={v}' in owner_run.read_text(encoding='utf-8') for k, v in expected_owner.items()):
        add_issue(issues, 'ERROR', 'owner-control run transcript does not match exact assertion/control counts')

    system_control = packages['system-control']['data']
    control_counts = system_control.get('counts', {})
    expected_system_control = {'actual_keys_parsed': 2, 'completed_HUD_words': 2, 'denied_writes': 7,
                               'abort_drained': 2, 'early_HUD_drain_rejected': 1, 'accepted_frames': 0,
                               'actual_writes': 2, 'actual_reads': 2, 'refreshes': 133, 'clocks': 99247}
    if not (system_control.get('status') == 'PASS' and all(control_counts.get(k) == v for k, v in expected_system_control.items())):
        add_issue(issues, 'ERROR', 'system-control: expected two parsed keys, early HUD-drain rejection and no accepted frame')
    system_control_log = ROOT / 'fpga/experiments/cu66-v70/system/control.log'
    if not system_control_log.is_file() or not all(f'{k}={v}' in system_control_log.read_text(encoding='utf-8') for k, v in expected_system_control.items()):
        add_issue(issues, 'ERROR', 'system-control transcript does not match exact command/abort counts')

    system_layouts = {}
    for name, expected_strip in (('system-full-direct', False), ('system-full-strip', True)):
        data = packages[name]['data']
        frames = data.get('frames', [])
        summary = data.get('summary', {})
        if not (data.get('status') == 'PASS_FUNCTIONAL_MEMORY_AND_FRAMEBUFFERS' and
                data.get('cadence_status') == 'FAIL_UNDERRUNS' and data.get('strip') is expected_strip and
                len(frames) == 2 and summary.get('complete_frames') == 2 and
                all(frame.get('actual_writes') == 664320 for frame in frames) and
                frames[0].get('underruns') == 0 and frames[1].get('underruns', 0) > 0 and
                summary.get('physical_fps_proven') == 0 and
                any('nativeHUDsoftwareexecutiontime not simulated' in item for item in data.get('limitations', []))):
            add_issue(issues, 'ERROR', f'{name}: framebuffer/cadence scope or result counters are inconsistent')
        system_layouts[name] = {
            'functional_status': data.get('status'), 'cadence_status': data.get('cadence_status'),
            'strip': data.get('strip'), 'frame_count': len(frames),
            'second_frame_cycles': frames[1].get('cycles') if len(frames) > 1 else None,
            'second_frame_underruns': frames[1].get('underruns') if len(frames) > 1 else None,
            'total_underruns': summary.get('total_underruns'),
            'physical_fps_proven': summary.get('physical_fps_proven'),
        }
    if system_layouts['system-full-direct']['second_frame_cycles'] != 24813942 or system_layouts['system-full-strip']['second_frame_cycles'] != 22984583:
        add_issue(issues, 'ERROR', 'system direct/strip cycle values differ from audited current results')

    negatives = packages['negatives']['data']
    if not (negatives.get('status') == 'PASS' and negatives.get('case_count') == 28 and
            len(negatives.get('case_results', [])) == 28 and
            all(c.get('status') == 'PASS' and c.get('terminal_pass') for c in negatives['case_results']) and
            negatives.get('source_unchanged') and
            negatives.get('source_sha256_before') == negatives.get('source_sha256_after')):
        add_issue(issues, 'ERROR', 'negatives: current 28-case replay or stable source pins did not reconcile')
    for case in negatives.get('case_results', []):
        path = choose_hashed_path(case['log'], case['log_sha256'], ROOT / Path(packages['negatives']['result']).parent)
        text = path.read_text(encoding='utf-8', errors='replace') if path else ''
        mode8 = [fields_from_line(line) for line in text.splitlines() if line.startswith('FRAME_PASS ')]
        if (len(mode8) != 3 or mode8[0].get('mode') != 0 or mode8[1].get('mode') != 8 or
                mode8[1].get('error') == 0 or mode8[1].get('commits') != 0 or
                mode8[2].get('fid') != 24 or not any(line == f"NEGATIVE_CASE_PASS name={case['name']}" for line in text.splitlines())):
            add_issue(issues, 'ERROR', f"negative case transcript does not show seed/reject/recovery sequence: {case.get('name')}")

    receiver = packages['receiver']['data']
    rows = receiver.get('rows', [])
    mode_counts = {}
    for row in rows:
        mode_counts[row.get('mode')] = mode_counts.get(row.get('mode'), 0) + 1
    corpus_rows = [row for row in rows if row.get('mode') == 0]
    fault_rows = [row for row in rows if row.get('mode') != 0]
    terminal_log = choose_hashed_path('seed7001.log', receiver.get('commands', [{}])[-1].get('log_sha256', ''), ROOT / 'fpga/experiments/cu66-v70/receiver')
    terminal_text = terminal_log.read_text(encoding='utf-8', errors='replace') if terminal_log else ''
    if not (receiver.get('status') == 'PASS' and receiver.get('actual_corpus_frames') == 457 and
            len(rows) == 478 and len(corpus_rows) == 471 and len(fault_rows) == 7 and
            all(row.get('tiles') == 8100 and row.get('error') == 0 for row in corpus_rows) and
            {row.get('mode') for row in fault_rows} == set(range(1, 8)) and
            'PASS actual_frames=457 fault_and_control_modes=7 seed=7001' in terminal_text):
        add_issue(issues, 'ERROR', 'receiver: current 457-frame replay, seven modes, or terminal source/log pins do not reconcile')
    receiver_rows_log = terminal_text.splitlines()
    frame_rows_log = [fields_from_line(line) for line in receiver_rows_log if line.startswith('FRAME_PASS ')]
    compare_fields = ('fid', 'key', 'mode', 'clocks', 'tiles', 'error', 'commits', 'abort_commands', 'stale', 'reference_bank')
    if len(frame_rows_log) != len(rows) or any(any(raw.get(k) != row.get(k) for k in compare_fields)
                                                for raw, row in zip(frame_rows_log, rows)):
        add_issue(issues, 'ERROR', 'receiver: structured frame rows do not match the hash-pinned raw seed log')

    software = packages['software-control']['data']
    software_runs = software.get('runs', [])
    expected_endpoint = {'actual_HUD_frames': 457, 'keys': 20, 'commands': 2811,
                         'malformed_no_state_change': 13, 'words_transferred_per_actual_frame': 21120,
                         'commit_retry': True, 'abort_retry': True,
                         'old_abort_does_not_discard_new_candidate': True, 'native_endpoint_only': True}
    if not (software.get('status') == 'PASS' and len(software_runs) == 2 and
            {bool(run.get('sanitized')) for run in software_runs} == {False, True} and
            all(all(run.get(key) == value for key, value in expected_endpoint.items()) for run in software_runs)):
        add_issue(issues, 'ERROR', 'software-control: expected release and sanitized endpoint runs with exact frame/command counters')
    for command in software.get('commands', []):
        if 'test-final-' in str(command.get('log')):
            output = command_log_text(packages['software-control'], command)
            matches = re.findall(r'^TEST_PASS_ENDPOINT (\{.*\})$', output, re.M)
            try:
                parsed = [json.loads(item) for item in matches]
            except json.JSONDecodeError:
                parsed = []
            if len(parsed) != 1 or any(parsed[0].get(k) != v for k, v in expected_endpoint.items()):
                add_issue(issues, 'ERROR', f"software-control: endpoint runtime marker disagrees with summary: {command.get('log')}")
            if re.search(r'AddressSanitizer|runtime error:', output):
                add_issue(issues, 'ERROR', f"software-control: sanitizer/runtime diagnostic in {command.get('log')}")
    compat_path = ROOT / 'fpga/experiments/cu66-v70/software-control/python-compat-results.json'
    compat = read_json(compat_path)
    valid_records = [record for record in compat.get('records', []) if record.get('valid')]
    invalid_records = [record for record in compat.get('records', []) if not record.get('valid')]
    if not (compat.get('status') == 'PASS' and len(compat.get('records', [])) == 32 and
            len(valid_records) == 17 and len(invalid_records) == 15 and len(compat.get('commands', [])) == 32 and
            compat.get('valid_roundtrip_frames') == 17 and compat.get('matching_malformed_rejections') == 15 and
            compat.get('actual_native_response_semantic_checks') == 5 and
            compat.get('actual_READ_HUD_bytes') == 42240 and compat.get('status_payload_bytes') == 72 and
            all(c.get('exit_code') == c.get('expected_exit_code') for c in compat.get('commands', []))):
        add_issue(issues, 'ERROR', 'software-control: Python/native compatibility record counts or response checks do not reconcile')
    compat_log = ROOT / 'fpga/experiments/cu66-v70/software-control/python-compat.log'
    if not compat_log.is_file() or 'PYTHON_CPP_COMPAT_PASS valid_frames=17 malformed_rejections=15 actual_endpoint_response_opcodes=5' not in compat_log.read_text(encoding='utf-8', errors='replace'):
        add_issue(issues, 'ERROR', 'software-control: Python/native compatibility transcript lacks expected terminal marker')

    # Summary transcripts add useful review markers, but those not named by a
    # result command are not independent, hash-bound execution records.
    known_summaries = [
        'fpga/experiments/cu66-v70/memory/regression.log',
        'fpga/experiments/cu66-v70/formal/verify.log',
        'fpga/experiments/cu66-v70/formal/regression.log',
        'fpga/experiments/cu66-v70/display/display-audit.log',
        'fpga/experiments/cu66-v70/owner-control/verify.log',
        'fpga/experiments/cu66-v70/system/control-verify.log',
        'fpga/experiments/cu66-v70/system/verify-direct.log',
        'fpga/experiments/cu66-v70/system/verify-strip.log',
        'fpga/experiments/cu66-v70/receiver/verify-full.log',
        'fpga/experiments/cu66-v70/software-control/verify.log',
    ]
    bound_logs = set()
    for package in packages.values():
        for command in package['data'].get('commands', []):
            if command.get('log'):
                bound_logs.add(command['log'])
    unbound = []
    for rel in known_summaries:
        path = ROOT / rel
        if path.is_file() and rel not in bound_logs:
            unbound.append({'path': rel, 'sha256': sha(path)})
    if unbound:
        add_issue(issues, 'WARNING', 'wrapper summary logs below are not declared as hash-bound command outputs; use bound per-command logs/results as authorities')

    add_issue(issues, 'WARNING', 'system direct and strip both pass framebuffer/readback checks but cadence is FAIL_UNDERRUNS; CPU HUD service time is excluded and physical 30 fps remains unproven')
    add_issue(issues, 'WARNING', 'formal result is bounded to 8/16/24 solver states; it is not an unbounded safety, liveness, CDC, or full-system proof')
    add_issue(issues, 'WARNING', 'memory evidence uses a checked 32 MiB functional command model; it is not electrical timing, board signoff, or target fit evidence')
    add_issue(issues, 'WARNING', 'memory writer qualifies full x16 writes; odd-byte masked/RMW writes remain outside the demonstrated path')
    add_issue(issues, 'WARNING', 'native HC70 encoded endpoint evidence is host-only; the full-system peer remains typed, so end-to-end wire integration is unproven')
    add_issue(issues, 'WARNING', 'per-run tool image digest/version is not embedded in these leaf result records; commands identify the shared container name')

    source_count = sum(len(p['sources']) for p in packages.values())
    command_count = sum(len(p['commands']) for p in packages.values())
    extra_count = sum(len(p['extras']) for p in packages.values())
    result_count = len(packages)
    display_baseline_count = len(baseline_checks)
    display_audit_verifier_count = 1
    unique_source_paths = {item['resolved'] for package in packages.values() for item in package['sources']
                           if item.get('ok') and item.get('resolved')}
    total_claims = (source_count + command_count + extra_count + result_count +
                    display_baseline_count + display_audit_verifier_count)
    integrity_errors = [issue for issue in issues if issue['level'] == 'ERROR']
    report = {
        'schema': 'cu66-v70-independent-evidence-audit-v1',
        'status': 'FAIL' if integrity_errors else 'PASS_WITH_WARNINGS',
        'scope': 'current leaf source/log/result integrity and declared functional counts; receiver included after current 457-frame rerun; archived pre-fix records excluded from current PASS evidence',
        'verifier': str(Path(__file__).resolve().relative_to(ROOT)),
        'verifier_sha256': sha(Path(__file__).resolve()),
        'source_pin_claims_checked': source_count,
        'command_log_and_script_claims_checked': command_count,
        'additional_log_witness_claims_checked': extra_count,
        'unique_resolved_source_paths': len(unique_source_paths),
        'current_result_json_hashes_checked': result_count,
        'display_baseline_file_hashes_checked': display_baseline_count,
        'display_audit_verifier_hashes_checked': display_audit_verifier_count,
        'total_declared_hash_claims_checked': total_claims,
        'display_audit_record_sha256': sha(display_audit_path),
        'display_audit_counts': {
            'declared_hash_checks': display_audit.get('declared_hash_checks'),
            'baseline_rasters': display_audit.get('baseline_rasters'),
            'comparison_rasters': display_audit.get('comparison_rasters'),
            'total_painter_words_compared': display_audit.get('total_painter_words_compared'),
            'scanout_frames': display_audit.get('scanout_frames'),
            'scanout_pixels_compared': display_audit.get('scanout_pixels_compared'),
        },
        'packages': {},
        'system_layouts': system_layouts,
        'unbound_summary_logs': unbound,
        'receiver_status': 'PASS_CURRENT_457_OF_457',
        'issues': issues,
        'limitations': [
            'Full system direct/strip framebuffers pass while both integrated cadence runs fail with underruns.',
            'The full receiver uses transactional RAM and painter/scanout completion models.',
            'The HC70 native endpoint is host-only; the full-system peer is typed and does not prove end-to-end wire integration.',
            'The formal result is bounded and bank-controller scoped.',
            'No result establishes target timing/fit, physical SDRAM behavior, or physical 30 fps.',
        ],
    }
    for name, package in packages.items():
        data = package['data']
        report['packages'][name] = {
            'result': package['result'], 'result_sha256': package['result_sha256'],
            'declared_status': package['declared_status'], 'scope': package['scope'],
            'source_pins': len(package['sources']),
            'source_pins_matching': sum(item['ok'] for item in package['sources']),
            'bound_commands_or_scripts': len(package['commands']),
            'bound_commands_or_scripts_matching': sum(item['ok'] for item in package['commands']),
            'additional_evidence_hashes': len(package['extras']),
            'additional_evidence_hashes_matching': sum(item['ok'] for item in package['extras']),
        }
        if name == 'memory':
            report['packages'][name]['run_count'] = len(data.get('runs', []))
            report['packages'][name]['mapped_bytes'] = memory_map.get('physical_bytes')
            report['packages'][name]['checks_per_run'] = sorted({r.get('checks') for r in data.get('runs', [])})
            report['packages'][name]['physical_words'] = memory_map.get('physical_words')
        elif name == 'display':
            report['packages'][name]['baseline_rasters'] = sum(r.get('full_physical_rasters', 0) for r in data.get('painter', []))
            report['packages'][name]['scanout_pixels'] = sum(r.get('compared_pixels', 0) for r in data.get('scanout', []))
            report['packages'][name]['scanout_runs'] = len(data.get('scanout', []))
            report['packages'][name]['intentional_starvation_underruns'] = sum(r.get('underruns', 0) for r in data.get('scanout', []) if r.get('starvation'))
        elif name == 'display-strip-locality':
            report['packages'][name]['direct_rasters'] = direct_count
            report['packages'][name]['strip_rasters'] = strip_count
        elif name == 'formal':
            report['packages'][name]['proof_bounds'] = [r.get('solver_steps') for r in proof_runs]
            report['packages'][name]['assertions_per_bound'] = [r.get('assertions_elaborated') for r in proof_runs]
            report['packages'][name]['reachability_witnesses'] = len(cover_runs)
        elif name == 'control-abi':
            report['packages'][name]['tests_passed'] = data.get('tests_passed')
            report['packages'][name]['tests_failed'] = data.get('tests_failed')
            report['packages'][name]['opcode_values'] = {key: constants.get(key) for key in expected_ops}
        elif name == 'owner-control':
            report['packages'][name]['counts'] = owner_counts
        elif name == 'system-control':
            report['packages'][name]['counts'] = control_counts
        elif name in ('system-full-direct', 'system-full-strip'):
            report['packages'][name].update(system_layouts[name])
        elif name == 'negatives':
            report['packages'][name]['case_count'] = data.get('case_count')
            report['packages'][name]['failed_cases'] = data.get('failed_cases')
        elif name == 'receiver':
            report['packages'][name]['actual_corpus_frames'] = data.get('actual_corpus_frames')
            report['packages'][name]['rows'] = len(rows)
            report['packages'][name]['normal_corpus_rows'] = len(corpus_rows)
            report['packages'][name]['fault_control_modes'] = sorted(row.get('mode') for row in fault_rows)
            report['packages'][name]['mode_counts'] = {str(k): v for k, v in sorted(mode_counts.items())}
        elif name == 'software-control':
            compat_summary = read_json(ROOT / 'fpga/experiments/cu66-v70/software-control/python-compat-results.json')
            report['packages'][name]['release_and_sanitized_runs'] = len(data.get('runs', []))
            report['packages'][name]['actual_HUD_frames_per_run'] = sorted({r.get('actual_HUD_frames') for r in data.get('runs', [])})
            report['packages'][name]['native_commands_per_run'] = sorted({r.get('commands') for r in data.get('runs', [])})
            report['packages'][name]['python_valid_roundtrips'] = compat_summary.get('valid_roundtrip_frames')
            report['packages'][name]['python_malformed_rejections'] = compat_summary.get('matching_malformed_rejections')
            report['packages'][name]['actual_native_response_checks'] = compat_summary.get('actual_native_response_semantic_checks')
        report['packages'][name]['unique_source_paths'] = len({item['path'] for item in package['sources'] if item['path'] != '<before-after-set>'})

    log_lines = [f"EVIDENCE_AUDIT_{report['status']} total_hash_claims={total_claims} source_claims={source_count} command_logs_scripts={command_count} extra_hashes={extra_count} baseline_files={display_baseline_count}"]
    for name, package in report['packages'].items():
        log_lines.append(f"PACKAGE {name} status={package['declared_status']} source={package['source_pins_matching']}/{package['source_pins']} logs={package['bound_commands_or_scripts_matching']}/{package['bound_commands_or_scripts']} extra={package['additional_evidence_hashes_matching']}/{package['additional_evidence_hashes']}")
    log_lines.append(f"SYSTEM direct_cycles={system_layouts['system-full-direct']['second_frame_cycles']} direct_underruns={system_layouts['system-full-direct']['total_underruns']} strip_cycles={system_layouts['system-full-strip']['second_frame_cycles']} strip_underruns={system_layouts['system-full-strip']['total_underruns']} cadence=FAIL_UNDERRUNS")
    for issue in issues:
        log_lines.append(f"{issue['level']} {issue['message']}")
    log_content = '\n'.join(log_lines) + '\n'
    report['audit_log'] = str(OUT_LOG.relative_to(ROOT))
    report['audit_log_sha256'] = hashlib.sha256(log_content.encode('utf-8')).hexdigest()
    OUT_JSON.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    OUT_LOG.write_text(log_content, encoding='utf-8')
    return report


if __name__ == '__main__':
    result = audit()
    print(f"EVIDENCE_AUDIT_{result['status']} total_hash_claims={result['total_declared_hash_claims_checked']} source_claims={result['source_pin_claims_checked']} command_logs_scripts={result['command_log_and_script_claims_checked']} extra_hashes={result['additional_log_witness_claims_checked']}")
    for issue in result['issues']:
        print(f"{issue['level']} {issue['message']}")
    raise SystemExit(1 if result['status'] == 'FAIL' else 0)
