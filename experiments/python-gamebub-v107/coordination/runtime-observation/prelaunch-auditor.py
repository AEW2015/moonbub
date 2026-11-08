#!/usr/bin/env python3
"""Independent, read-only V107 baseline and evidence checker.

Reads frozen V106 receipts/reports and the real board top, writes the current
V107 audit record. It never launches a vendor flow or edits V106 evidence.
"""
from __future__ import annotations

import hashlib
import gzip
import json
import difflib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/python-gamebub-v107/audit/baseline-audit.json"


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_hash(rel: str) -> str:
    return sha256(ROOT / rel)


def native_timing(data: str) -> dict:
    start = data.index('| Design Timing Summary')
    for line in data[start:].splitlines():
        tokens = line.split()
        if len(tokens) == 12 and all(re.fullmatch(r'-?\d+(?:\.\d+)?', x) for x in tokens):
            names = ['WNS_ns', 'TNS_ns', 'setup_failing', 'setup_total', 'WHS_ns', 'THS_ns',
                     'hold_failing', 'hold_total', 'WPWS_ns', 'TPWS_ns', 'pulse_failing', 'pulse_total']
            return {k: float(v) if '_ns' in k else int(v) for k, v in zip(names, tokens)}
    raise ValueError('no native timing summary row')


def native_routing(data: str) -> dict:
    counts = {}
    for line in data.splitlines():
        match = re.match(r'^\s*(.*?)\s*:\s*([0-9,]+)\s*:', line)
        if match:
            label = re.sub(r'[.#\s]+', ' ', match[1]).strip().lower()
            counts[label] = int(match[2].replace(',', ''))
    get = lambda phrase: [v for k, v in counts.items() if re.search(r'\b' + re.escape(phrase) + r'\b', k)]
    routable, fully, errors = get('routable nets'), get('fully routed nets'), get('routing errors')
    difference = routable[0] - fully[0] if len(routable) == len(fully) == 1 else None
    return {'reported_net_counts': counts, 'derived_unrouted_routable_nets': difference,
            'zero_routing_errors': bool(errors) and all(x == 0 for x in errors),
            'all_routable_nets_routed': difference == 0}


def native_findings(data: str) -> dict:
    rows = {}
    for line in data.splitlines():
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells) == 4 and cells[1] in ('Error', 'Critical Warning', 'Warning', 'Advisory') and cells[3].isdigit():
            rows[cells[0]] = {'severity': cells[1], 'reported': int(cells[3])}
    found = re.search(r'Checks found:\s*(\d+)', data)
    return {'by_rule': rows, 'total_reported': sum(x['reported'] for x in rows.values()),
            'summary_count': int(found[1]) if found else None}


def native_worst_path(data: str) -> dict:
    values = {}
    for label, pattern in {
        'slack_ns': r'^Slack \(VIOLATED\)\s*:\s*(-?\d+\.\d+)ns',
        'source': r'^\s*Source:\s*(.+)$',
        'destination': r'^\s*Destination:\s*(.+)$',
        'data_path_delay_ns': r'^\s*Data Path Delay:\s*(\d+\.\d+)ns',
        'logic_levels': r'^\s*Logic Levels:\s*(\d+)',
    }.items():
        m = re.search(pattern, data, re.M)
        if m:
            value = m[1].strip()
            values[label] = int(value) if label == 'logic_levels' else float(value) if label.endswith('_ns') else value
    return values


def audit_resume(path: Path) -> dict:
    rel = str(path.relative_to(ROOT))
    folder = path.parent
    r = load(rel)
    record = {'receipt': rel, 'status': r.get('status'), 'strategy': r.get('strategy'),
              'pending': r.get('status') == 'RUNNING', 'checks': {}, 'stages': {}}
    try:
        parent_receipt_rel = r['parent_receipt']['path']
        parent_receipt_path = ROOT / parent_receipt_rel
        parent_receipt = json.loads(parent_receipt_path.read_text())
        copied_parent = folder / 'parent-receipt.json'
        copied_inputs = folder / 'parent-inputs.json'
        parent_input_data = copied_inputs.read_bytes()
        checkpoint_hash = parent_receipt['artifacts']['synth.dcp']['sha256']
        checkpoint = r['parent_checkpoint']
        source_records = r['source_sha256']
        snapshots = {
            'resume_route.py': source_records['scripts/cu66-v107/resume_route.py'],
            'run.tcl': source_records['fpga/experiments/cu66-v107-flow/resume.tcl'],
            'report.tcl': source_records['fpga/experiments/cu66-v106-flow/report.tcl'],
        }
        snapshot_results = {}
        for snap, expected in snapshots.items():
            actual = sha256(folder / snap)
            snapshot_results[snap] = {'expected_sha256': expected, 'actual_sha256': actual, 'matches': actual == expected}
        checks = {
            'parent_receipt_copy_matches': sha256(copied_parent) == r['parent_receipt']['sha256'] == sha256(parent_receipt_path),
            'parent_receipt_binds_sixth_attempt': parent_receipt['observed_exit_code'] == 124 and parent_receipt['synthesis_checkpoint_written'],
            'parent_inputs_match_parent_manifest': sha256(copied_inputs) == parent_receipt['source_manifest_sha256'],
            'parent_checkpoint_path_and_hash_match_receipt': checkpoint['path'] == parent_receipt['artifacts']['synth.dcp']['external_path'] and checkpoint['sha256_before'] == checkpoint_hash,
            'parent_checkpoint_was_readonly': checkpoint.get('readonly_mount') is True,
            'retained_snapshots_match_receipt': all(x['matches'] for x in snapshot_results.values()),
            'part_and_period_match_parent': r['part'] == parent_receipt['part'] == 'xc7a100tcsg324-1' and r['clock_period_ns'] == parent_receipt['clock_period_ns'] == 10.0,
            'no_synthesis_rerun_or_clock_exception_edit': r['explicit_synthesis_rerun'] is False and r['clock_or_exception_edits'] is False,
            'flow_is_default_opt_place_route': r['strategy'] == 'Default opt/place/route from preserved synthesis checkpoint',
        }
        if r.get('status') != 'RUNNING':
            checks['parent_checkpoint_hash_after_unchanged'] = (
                checkpoint.get('sha256_after') == checkpoint_hash and checkpoint.get('unchanged') is True
            )
        if 'retained_sha256' in r:
            retained_checks = {}
            for retained_rel, digest in r['retained_sha256'].items():
                fp = folder / retained_rel
                retained_checks[retained_rel] = fp.is_file() and sha256(fp) == digest
            checks['all_terminal_retained_file_hashes_match'] = all(retained_checks.values())
        record['parent'] = {'receipt': parent_receipt_rel, 'receipt_sha256': sha256(parent_receipt_path),
                            'checkpoint_sha256': checkpoint_hash,
                            'checkpoint_before': checkpoint.get('sha256_before'),
                            'checkpoint_after': checkpoint.get('sha256_after'),
                            'checkpoint_actual_bytes_read': False}
        record['snapshots'] = snapshot_results
        record['checks'] = checks
        if not all(checks.values()):
            record['status'] = 'AUDIT_ERROR'
            record['pending'] = False
            record['errors'] = [k for k, v in checks.items() if not v]
            return record

        if r.get('status') == 'RUNNING':
            record['status'] = 'PENDING'
            record['scope'] = 'RUNNING; provenance/checkpoint identity verified; no terminal route verdict.'
            return record

        log_path = folder / 'vivado.log'
        checks['terminal_log_hash_matches'] = log_path.is_file() and bool(r.get('log_sha256')) and sha256(log_path) == r['log_sha256']
        artifacts = r.get('artifacts', {})
        report_dir = folder / 'reports'
        reports = {}
        report_checks = {}
        for name, artifact in artifacts.items():
            copy = report_dir / name
            if copy.is_file():
                digest = sha256(copy)
                report_checks[name] = digest == artifact['sha256'] and copy.stat().st_size == artifact['bytes']
                reports[name] = copy.read_text(errors='replace')
        checks['copied_artifact_hashes_match_receipt'] = all(report_checks.values())
        record['artifact_checks'] = report_checks
        log_text = log_path.read_text(errors='replace') if log_path.is_file() else ''
        route_finished = (
            r.get('status') == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
            and 'V107_COMPONENT_ROUTE_FINISHED' in log_text
            and 'route.dcp' in artifacts
        )
        for stage in ('place', 'route'):
            stage_data = {}
            timing_name = stage + '-timing-summary.rpt'
            if timing_name in reports:
                stage_data['timing'] = native_timing(reports[timing_name])
            clocks_name = stage + '-clocks.rpt'
            if clocks_name in reports:
                clock_data = reports[clocks_name]
                stage_data['clocks'] = [{'name': m[1], 'period_ns': float(m[2]), 'waveform': m[3], 'source': m[4]}
                    for m in re.finditer(r'^([^\s]+)\s+(\d+\.\d+)\s+(\{[^}]+\})\s+\S+\s+(.+)$', clock_data, re.M)]
            check_name = stage + '-check-timing.rpt'
            if check_name in reports:
                stage_data['check_timing'] = {k: int(v) for k, v in re.findall(r'^\s*\d+\. checking (\w+) \((\d+)\)', reports[check_name], re.M)}
            exception_name = stage + '-exceptions.rpt'
            if exception_name in reports:
                exception_data = reports[exception_name]
                stage_data['exceptions'] = {'no_valid_exceptions': 'No valid timing exceptions found.' in exception_data,
                                            'report_sha256': artifacts[exception_name]['sha256']}
            for kind in ('drc', 'methodology', 'cdc'):
                name = stage + '-' + kind + '.rpt'
                if name in reports:
                    if kind == 'cdc':
                        cdc_text = reports[name]
                        stage_data[kind] = {
                            'all_paths_safely_timed_message': 'All paths are Safely Timed.' in cdc_text,
                            'has_unsafe_paths_message': bool(re.search(r'(?i)unsafe path|unsafe CDC', cdc_text)),
                            'report_sha256': artifacts[name]['sha256'],
                            'scope': 'Vivado CDC report for the single-clock resumed OOC checkpoint; not board CDC signoff.'}
                    else:
                        stage_data[kind] = native_findings(reports[name])
            path_name = stage + '-setup-paths.rpt'
            if path_name in reports:
                stage_data['worst_setup_path'] = native_worst_path(reports[path_name])
            if stage == 'route' and 'route-status.rpt' in reports:
                stage_data['routing'] = native_routing(reports['route-status.rpt'])
            record['stages'][stage] = stage_data
        terminal = r.get('status') != 'RUNNING'
        record['pending'] = not terminal
        record['checks'] = checks
        record['terminal_outcome'] = r.get('status')
        record['exit_code'] = r.get('observed_exit_code')
        record['component_route_finished'] = route_finished
        tool_parent = reports.get('tool-parent.txt', '')
        record['tool_parent'] = tool_parent.strip().splitlines() if tool_parent else None
        if terminal:
            checks['tool_parent_report_matches_target'] = (
                'version=2026.1' in tool_parent
                and 'part=xc7a100tcsg324-1' in tool_parent
                and 'clock=component_clk period=10.0' in tool_parent
                and 'Default opt/place/route' in tool_parent
            )
            if record['component_route_finished']:
                checks['route_terminal_has_complete_native_reports'] = (
                    'route' in record['stages']
                    and 'timing' in record['stages']['route']
                    and 'clocks' in record['stages']['route']
                    and 'routing' in record['stages']['route']
                    and 'route.dcp' in artifacts
                    and bool(artifacts['route.dcp'].get('sha256'))
                )
                route_clocks = record['stages'].get('route', {}).get('clocks', [])
                checks['routed_report_keeps_inherited_clock'] = any(
                    c['name'] == 'component_clk' and c['period_ns'] == 10.0 for c in route_clocks
                )
                checks['completed_native_route_status_is_legal'] = (
                    record['stages'].get('route', {}).get('routing', {}).get('zero_routing_errors') is True
                    and record['stages'].get('route', {}).get('routing', {}).get('all_routable_nets_routed') is True
                )
        record['scope'] = ('Terminal OOC checkpoint continuation; report-derived metrics only. Board I/O/CDC/hardware qualification remains open.'
                           if terminal else 'RUNNING; no terminal route verdict.')
        if not all(checks.values()):
            record['status'] = 'AUDIT_ERROR'
            record['pending'] = False
            record['errors'] = [k for k, v in checks.items() if not v]
        elif terminal and not record['component_route_finished']:
            record['status'] = 'TERMINAL_FAILURE_RETAINED'
        elif terminal:
            record['status'] = 'TERMINAL_ROUTE_EVIDENCE_AUDITED'
        else:
            record['status'] = 'PENDING'
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        record.update(status='AUDIT_ERROR', pending=False, errors=[str(exc)])
    return record


def audit_rice_probe() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/rice'
    selection_path = area / 'probe-results.json'
    selection = json.loads(selection_path.read_text())
    receipt_path = ROOT / selection['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    attempt = receipt_path.parent
    audit_path = area / 'audit.json'
    stored_audit = json.loads(audit_path.read_text())
    checks = {
        'selection_receipt_hash_matches': sha256(receipt_path) == selection['sha256'] == stored_audit['receipt_sha256'],
        'selection_and_receipt_pass': selection['status'] == receipt['status'] == 'PASS_ACTUAL_RICE_FIXED_TAP_EQUIVALENCE',
        'frozen_audit_passes': stored_audit['status'] == 'PASS_FROZEN_ACTUAL_RTL_AUDIT',
        'candidate_hash_matches_selection_and_current_source': (
            receipt['candidate']['sha256'] == stored_audit['candidate_sha256'] ==
            file_hash(receipt['candidate']['path'])
        ),
    }
    artifact_results = {}
    for rel, digest in receipt['artifacts_sha256'].items():
        fp = attempt / rel
        actual = sha256(fp) if fp.is_file() else None
        artifact_results[rel] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
    checks['all_attempt_artifacts_match_receipt'] = all(x['matches'] for x in artifact_results.values())
    source_results = {rel: {'expected': digest, 'actual': file_hash(rel), 'matches': file_hash(rel) == digest}
                      for rel, digest in receipt['source_sha256'].items()}
    checks['all_current_sources_match_receipt'] = all(x['matches'] for x in source_results.values())
    run_rows = []
    logs_clean = True
    warnings = []
    for run in receipt['runs']:
        log_path = attempt / f"seed-{run['seed']}.log"
        rows = [json.loads(x) for x in log_path.read_text().splitlines() if x.strip()]
        verdicts = [x for x in rows if x.get('type') == 'verdict']
        summaries = [x for x in rows if 'historical_clocks' in x and 'parameter_cases' in x]
        good = (
            len(verdicts) == 1 and verdicts[0] == run['historical_verdict']
            and verdicts[0]['cases'] == 1520 and verdicts[0]['configurations'] == 8
            and verdicts[0]['directed_checks'] == 104 and verdicts[0]['requests_per_configuration'] == 173061
            and len(summaries) == 1 and summaries[0]['seed'] == run['seed']
            and summaries[0]['historical_clocks'] == run['historical_clocks']
            and summaries[0]['parameter_cases'] == run['parameter_cases'] == 6096
            and summaries[0]['prepared_clocks'] == run['prepared_clocks'] == 189105
        )
        run_rows.append({'seed': run['seed'], 'historical_cases': verdicts[0]['cases'] if verdicts else None,
                         'configurations': verdicts[0]['configurations'] if verdicts else None,
                         'directed_checks': verdicts[0]['directed_checks'] if verdicts else None,
                         'historical_clocks': run['historical_clocks'], 'pass': good})
    checks['both_seed_verdicts_and_counts_match'] = len(run_rows) == 2 and all(x['pass'] for x in run_rows)
    checked_logs = ['compile.log', 'binary.log', 'seed-107401.log', 'seed-107402.log', 'tool.log']
    for name in checked_logs:
        content = (attempt / name).read_text(errors='replace')
        if re.search(r'(?i)(?:%Warning-|\bwarning:|\bwaiver\b|TEST_FAIL|assertion failed)', content):
            logs_clean = False
            warnings.append({'file': name, 'matches': re.findall(r'(?i).{0,80}(?:%Warning-|\bwarning:|\bwaiver\b|TEST_FAIL|assertion failed).{0,100}', content)[:10]})
    checks['no_runtime_warning_failure_or_waiver_text'] = logs_clean
    # Verilator's compiler recipe contains only the declared filename-warning exclusion;
    # the audit and runtime logs show no functional warning/assertion suppression.
    result = {
        'status': 'PASS_ACTUAL_RICE_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
        'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha256(receipt_path),
        'candidate_sha256': receipt['candidate']['sha256'], 'total_clock_edges': receipt['total_clock_edges'],
        'runs': run_rows, 'historical_cases_per_seed': 1520, 'configurations_per_seed': 8,
        'directed_checks_per_seed': 104, 'requests_per_configuration': 173061,
        'parameter_cases_per_seed': 6096, 'prepared_clocks_per_seed': 189105,
        'artifacts_checked': len(artifact_results), 'sources_checked': len(source_results),
        'artifact_results': artifact_results, 'source_results': source_results,
        'checks': checks, 'warning_matches': warnings,
        'compile_warning_policy': 'Verilator --assert -Wall; receipt includes -Wno-DECLFILENAME only; no runtime warnings, test failures, or waiver text found.',
        'scope': 'Two-state clocked RTL probe and source/artifact evidence only; not mapped-netlist, timing, metastability, or hardware qualification.'
    }
    return result


def audit_cdc_selection() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/cdc'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    receipt_path = ROOT / selection['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    attempt = receipt_path.parent
    checks = {
        'selection_receipt_hash_matches': sha256(receipt_path) == selection['sha256'],
        'behavioral_selection_passes': selection['status'] == receipt['status'] == 'PASS_BEHAVIORAL_CDC_FABRIC',
        'actual_rtl_run_is_recorded': receipt['actual_RTL_run'] is True,
        'scope_excludes_metastability_and_hardware': all(x in receipt['scope'] for x in ('metastability', 'hardware', 'actual board parent adapters')),
        'strict_warning_policy_is_declared': receipt['strict_warning_policy'] == 'Verilator -Wall --assert; C++ -Wall -Wextra -Werror; no suppression',
    }
    artifact_results = {}
    for rel, digest in receipt['artifacts_sha256'].items():
        fp = attempt / rel
        actual = sha256(fp) if fp.is_file() else None
        artifact_results[rel] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
    checks['all_attempt_artifacts_match_receipt'] = all(x['matches'] for x in artifact_results.values())
    source_results = {}
    for rel, digest in receipt['source_sha256'].items():
        live = ROOT / rel
        snapshot = attempt / 'sources' / rel
        live_hash = sha256(live) if live.is_file() else None
        snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
        source_results[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                               'matches': live_hash == digest and snapshot_hash == digest}
    checks['all_live_and_snapshot_sources_match_receipt'] = all(x['matches'] for x in source_results.values())
    inventory_path = area / 'inventory.json'
    inventory = json.loads(inventory_path.read_text())
    inventory_sources = {rel: {'expected': digest, 'actual': file_hash(rel), 'matches': file_hash(rel) == digest}
                         for rel, digest in inventory['source_sha256'].items()}
    checks['inventory_sources_still_match'] = inventory['status'] == 'REVIEWED_SOURCE_NOT_BOARD_SIGNOFF' and all(
        x['matches'] for x in inventory_sources.values())
    compile_text = (attempt / 'compile.log').read_text(errors='replace')
    compile_warnings = re.findall(r'(?im)^.*(?:%Warning-|\bwarning:|Waiver).*$', compile_text)
    checks['compile_has_no_verilator_warnings'] = '%Warning-' not in compile_text and not re.search(r'(?im)^.*\bwarning:.*$', compile_text)
    pass_logs = {}
    count_rows = []
    verdict_count = True
    for run in receipt['runs']:
        seed = run['seed']
        log = (attempt / f'{seed}.log').read_text(errors='replace')
        matches = re.findall(rf'^TEST_PASS_CDC seed={seed} edges=(\d+) reset_epochs=(\d+) ticks=(\d+)$', log, re.M)
        lines = [json.loads(x) for x in log.splitlines() if x.startswith('{')]
        totals = {key: sum(int(row[key]) for row in lines)
                  for key in ('accepted', 'delivered', 'reset_discarded') if lines and all(key in row for row in lines)}
        expected = run['replay']
        good = (
            len(matches) == 1 and expected['status'] == 'PASS'
            and int(matches[0][0]) == 45809 and int(matches[0][1]) == 6 and int(matches[0][2]) == 120000
            and len(lines) == 5
            and totals == {k: expected[k] for k in ('accepted', 'delivered', 'reset_discarded')}
            and expected['accepted'] == expected['delivered'] + expected['reset_discarded']
        )
        pass_logs[str(seed)] = {'pass_line_count': len(matches), 'channel_rows': len(lines), 'totals': totals,
                                'receipt_replay': expected, 'pass': good}
        count_rows.append(good)
    checks['all_three_seed_verdicts_and_channel_counts_match'] = len(count_rows) == 3 and all(count_rows)
    checked_logs = ['compile.log', '107001.log', '107002.log', '107003.log']
    runtime_warning_lines = []
    for name in checked_logs:
        content = (attempt / name).read_text(errors='replace')
        runtime_warning_lines += [{'file': name, 'line': line.strip()} for line in content.splitlines()
                                  if re.search(r'(?i)(?:%Warning-|\bwarning:|TEST_FAIL|assertion failed|waiver)', line)]
    checks['no_runtime_warning_failure_or_waiver_lines'] = not runtime_warning_lines
    result = {
        'status': 'PASS_BEHAVIORAL_CDC_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
        'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha256(receipt_path),
        'mode': receipt['mode'], 'seeds': pass_logs, 'artifacts_checked': len(artifact_results),
        'sources_checked': len(source_results), 'artifact_results': artifact_results,
        'source_results': source_results, 'compile_warning_matches': compile_warnings,
        'inventory': str(inventory_path.relative_to(ROOT)), 'inventory_sources': inventory_sources,
        'runtime_warning_failure_waiver_lines': runtime_warning_lines, 'checks': checks,
        'scope': receipt['scope'] + ' Behavioral simulation does not establish metastability performance or hardware CDC signoff.'
    }
    return result


def audit_matrix() -> dict:
    base_required = [('aligned', 'fresh'), ('aligned', 'canonical'),
                     ('closure-aligned', 'fresh'), ('closure-aligned', 'canonical')]
    quant_required = [('quant-aligned', 'fresh'), ('quant-aligned', 'canonical')]
    required = base_required + quant_required
    lanes = []
    for variant, mode in required:
        area_name = 'quant-regression' if variant == 'quant-aligned' else 'regression'
        lane_dir = ROOT / 'experiments/python-gamebub-v107' / area_name / variant / mode
        attempts = sorted(p for p in (lane_dir / 'attempts').glob('*') if p.is_dir()) if (lane_dir / 'attempts').exists() else []
        if not attempts:
            lanes.append({'variant': variant, 'mode': mode, 'status': 'PENDING', 'results': None, 'attempts': []})
            continue
        audited_attempts = []
        for attempt in attempts:
            path = attempt / 'results.json'
            if not path.is_file():
                audited_attempts.append({'path': str(attempt.relative_to(ROOT)), 'status': 'PENDING', 'results': None})
                continue
            report = json.loads(path.read_text())
            artifacts = {}
            for rel, digest in report.get('artifacts_sha256', {}).items():
                fp = attempt / rel
                actual = sha256(fp) if fp.is_file() else None
                artifacts[rel] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
            sources = {}
            for rel, digest in report.get('source_sha256', {}).items():
                live, snapshot = ROOT / rel, attempt / 'sources' / rel
                live_hash = sha256(live) if live.is_file() else None
                snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
                sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                                'matches': live_hash == digest and snapshot_hash == digest}
            verdicts = []
            for run in report.get('runs', []):
                for impl, run_record in run.get('variants', {}).items():
                    verdict = run_record.get('verdict', {})
                    expected_cases, expected_directed = (6, 13) if mode == 'fresh' else (22, 21)
                    verdicts.append({'seed': run.get('seed'), 'implementation': impl,
                                     'status': verdict.get('status'), 'cases': verdict.get('cases'),
                                     'directed_checks': verdict.get('directed_checks'),
                                     'pass': verdict.get('status') == 'TEST_PASS' and verdict.get('cases') == expected_cases
                                             and verdict.get('directed_checks') == expected_directed})
            terminal = report.get('status') in ('PASS', 'FAIL')
            hashes_ok = all(x['matches'] for x in artifacts.values()) and all(x['matches'] for x in sources.values())
            expected_profile, expected_directed = (24, 52) if mode == 'fresh' else (88, 84)
            expected_seeds = [107501, 107502] if variant == 'quant-aligned' else [107401, 107402]
            passed = (report.get('status') == 'PASS' and report.get('actual_RTL_run') is True
                      and report.get('assertions_disabled_or_downgraded') is False
                      and report.get('case_profile_runs') == expected_profile
                      and report.get('directed_checks') == expected_directed
                      and report.get('exact_same_seed_transcripts_events_cycles') is True
                      and report.get('seeds') == expected_seeds
                      and hashes_ok and len(verdicts) == 4 and all(x['pass'] for x in verdicts)
                      and all(all(v is True for v in row.get('equalities', {}).values()) for row in report.get('runs', [])))
            audited_attempts.append({'path': str(attempt.relative_to(ROOT)),
                'status': 'PASS' if passed else 'TERMINAL_FAILURE_RETAINED' if terminal else 'PENDING',
                'results': str(path.relative_to(ROOT)), 'results_sha256': sha256(path),
                'terminal_report_status': report.get('status'), 'error': report.get('error'),
                'case_profile_runs': report.get('case_profile_runs'), 'directed_checks': report.get('directed_checks'),
                'seeds': report.get('seeds'), 'exact_same_seed_transcripts_events_cycles': report.get('exact_same_seed_transcripts_events_cycles'),
                'actual_RTL_run': report.get('actual_RTL_run'), 'artifacts_checked': len(artifacts),
                'sources_checked': len(sources), 'artifact_hashes_match': all(x['matches'] for x in artifacts.values()),
                'source_hashes_match': all(x['matches'] for x in sources.values()), 'verdicts': verdicts,
                'artifact_results': artifacts, 'source_results': sources})
        latest = audited_attempts[-1]
        if latest['status'] == 'PASS': lane_status = 'PASS'
        elif latest['status'] == 'TERMINAL_FAILURE_RETAINED': lane_status = 'TERMINAL_FAILURE_RETAINED'
        else: lane_status = 'PENDING'
        lanes.append({'variant': variant, 'mode': mode, 'status': lane_status,
                      'results': latest.get('results'), 'results_sha256': latest.get('results_sha256'),
                      'attempts': audited_attempts})
    base_complete = all(next(x for x in lanes if (x['variant'], x['mode']) == key)['status'] == 'PASS' for key in base_required)
    quant_complete = all(next(x for x in lanes if (x['variant'], x['mode']) == key)['status'] == 'PASS' for key in quant_required)
    complete = base_complete and quant_complete
    errors = any(x['status'] == 'TERMINAL_FAILURE_RETAINED' for x in lanes)
    quant_lanes = [x for x in lanes if x['variant'] == 'quant-aligned']
    quant_reports = [json.loads((ROOT / x['results']).read_text()) for x in quant_lanes if x.get('results') and (ROOT / x['results']).is_file()]
    quant_profiles = sum(x.get('case_profile_runs', 0) for x in quant_reports)
    quant_directed = sum(x.get('directed_checks', 0) for x in quant_reports)
    quant_pair_seed_match = len(quant_reports) == 2 and quant_reports[0].get('seeds') == quant_reports[1].get('seeds') == [107501, 107502]
    quant_pair_exact = len(quant_reports) == 2 and all(x.get('exact_same_seed_transcripts_events_cycles') is True for x in quant_reports)
    if quant_complete:
        quant_complete = quant_profiles == 112 and quant_directed == 136 and quant_pair_seed_match and quant_pair_exact
        complete = base_complete and quant_complete
        status = 'PASS_ALL_SIX_PIPELINE_LANES' if complete else 'AUDIT_ERROR'
    status = ('PASS_ALL_SIX_PIPELINE_LANES' if complete else
              'PASS_BASE_FOUR_LANES_QUANT_PAIR_PENDING' if base_complete else
              'TERMINAL_FAILURE_RETAINED' if errors else 'PENDING_REQUIRED_LANES')
    return {'status': status, 'base_four_lane_status': 'PASS' if base_complete else 'PENDING_OR_FAILED',
            'quant_pair_status': 'PASS' if quant_complete else 'PENDING_OR_FAILED',
            'orchestrator': 'scripts/cu66-v107/run_matrix.py',
            'orchestrator_sha256': file_hash('scripts/cu66-v107/run_matrix.py'),
            'lane_runner': 'scripts/cu66-v107/regress.py',
            'lane_runner_sha256': file_hash('scripts/cu66-v107/regress.py'),
            'required_lanes': lanes, 'base_four_lane_complete': base_complete,
            'quant_pair_complete': quant_complete, 'complete': complete,
            'quant_pair_case_profile_runs': quant_profiles, 'quant_pair_directed_checks': quant_directed,
            'quant_pair_same_seeds': quant_pair_seed_match, 'quant_pair_exact_seed_transcripts': quant_pair_exact,
            'total_six_lane_case_profile_runs': sum(x.get('case_profile_runs', 0) or 0 for lane in lanes for x in lane.get('attempts', []) if x.get('status') == 'PASS'),
            'total_six_lane_directed_checks': sum(x.get('directed_checks', 0) or 0 for lane in lanes for x in lane.get('attempts', []) if x.get('status') == 'PASS'),
            'scope': 'All four aligned/closure-aligned and both quant-aligned fresh/canonical lanes must have hash-matched terminal PASS reports. Component RTL evidence only.'}


def audit_quant_focus() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/quant'
    selected_path = area / 'results.json'
    selected = json.loads(selected_path.read_text())
    audit_path = area / 'audit.json'
    audit = json.loads(audit_path.read_text())
    selected_report_path = ROOT / selected['selected_report']
    report = json.loads(selected_report_path.read_text())
    candidate_path = audit['candidate']['path']
    checks = {
        'selected_receipt_hash_matches_frozen_audit': sha256(selected_report_path) == audit['selected_receipt_sha256'] == audit['attempts'][-1]['sha256'],
        'selected_candidate_hash_matches_current_source': report['candidate']['sha256'] == audit['candidate']['sha256'] == file_hash(candidate_path),
        'selected_result_is_pass': selected['status'] == 'PASS' and report['status'] == 'PASS' and audit['status'] == 'PASS_QUANT_RETAINED_ARTIFACT_AUDIT',
        'actual_rtl_assertions_enabled': report['actual_RTL_run'] is True and report['assertions_disabled_or_downgraded'] is False,
        'original_full_module_coverage_floor_met': report['complete_production_body_preserved_by_adapters'] is True,
    }
    attempt_rows = []
    warning_lines = []
    for item in audit['attempts']:
        path = ROOT / item['receipt']
        attempt_report = json.loads(path.read_text())
        artifacts = {rel: {'expected': digest,
                           'actual': sha256(path.parent / rel) if (path.parent / rel).is_file() else None,
                           'matches': (path.parent / rel).is_file() and sha256(path.parent / rel) == digest}
                     for rel, digest in attempt_report.get('artifacts_sha256', {}).items()}
        sources = {}
        for rel, digest in attempt_report.get('source_sha256', {}).items():
            live = ROOT / rel
            snapshot = path.parent / 'sources' / rel
            live_hash = sha256(live) if live.is_file() else None
            snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
            sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                            'snapshot_matches': snapshot_hash == digest, 'current_matches': live_hash == digest}
        artifact_ok = all(x['matches'] for x in artifacts.values())
        source_snapshot_ok = all(x['snapshot_matches'] for x in sources.values())
        source_current_ok = all(x['current_matches'] for x in sources.values())
        for logfile in ('compile.log', 'verilator.log', 'compiler.log'):
            fp = path.parent / logfile
            if fp.is_file():
                contents = fp.read_text(errors='replace')
                warning_lines.extend([{'file': str(fp.relative_to(ROOT)), 'line': line.strip()}
                                      for line in contents.splitlines()
                                      if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver)', line)])
        run_verdicts = []
        for run in attempt_report.get('runs', []):
            v = run.get('terminal_verdict', {})
            run_verdicts.append({'seed': run.get('seed'), 'status': v.get('status'), 'cases': v.get('cases'),
                                 'directed_checks': v.get('directed_checks'), 'clock_edges': v.get('clock_edges'),
                                 'independent_trace_replay': run.get('trace_replay', {}).get('status'),
                                 'packet_run_oracle': run.get('quant_replay', {}).get('status')})
        attempt_rows.append({'receipt': item['receipt'], 'sha256': sha256(path), 'reported_status': attempt_report.get('status'),
                             'error': attempt_report.get('error'), 'actual_RTL_run': attempt_report.get('actual_RTL_run'),
                             'artifact_hashes_match': artifact_ok, 'source_snapshots_match': source_snapshot_ok,
                             'current_sources_match': source_current_ok,
                             'artifacts_checked': len(artifacts), 'sources_checked': len(sources),
                             'runs': run_verdicts, 'artifact_results': artifacts, 'source_results': sources})
    checks['all_attempt_snapshots_and_artifact_hashes_match'] = all(
        x['artifact_hashes_match'] and x['source_snapshots_match'] for x in attempt_rows)
    checks['selected_attempt_sources_match_current_tree'] = attempt_rows[-1]['current_sources_match']
    checks['selected_two_seed_counts_and_independent_oracles_match'] = (
        len(report['runs']) == 2 and all(x['status'] == 'TEST_PASS' and x['cases'] == 86 and x['directed_checks'] == 35
            and x['independent_trace_replay'] == 'PASS' and x['packet_run_oracle'] == 'PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE'
            for attempt in attempt_rows if attempt['reported_status'] == 'PASS' for x in attempt['runs'])
    )
    checks['no_focused_compile_warning_or_waiver_text'] = not warning_lines
    return {'status': 'PASS_QUANT_FOCUS_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
            'selection': str(selected_path.relative_to(ROOT)), 'selection_sha256': sha256(selected_path),
            'audit': str(audit_path.relative_to(ROOT)), 'audit_sha256': sha256(audit_path),
            'selected_report': str(selected_report_path.relative_to(ROOT)), 'selected_report_sha256': sha256(selected_report_path),
            'candidate': {'path': candidate_path, 'sha256': report['candidate']['sha256']},
            'selected_actual_clock_edges': audit['selected_actual_clock_edges'],
            'selected_runs': attempt_rows[-1]['runs'], 'attempts': attempt_rows,
            'warning_matches': warning_lines, 'checks': checks,
            'scope': 'Clocked behavioral full production module through adapters with independent trace/packet replay; no physical timing or hardware qualification.'}


def audit_value_check() -> dict:
    selection_path = ROOT / 'experiments/python-gamebub-v107/value-check/results.json'
    selection = json.loads(selection_path.read_text())
    receipt_path = ROOT / selection['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    attempt = receipt_path.parent
    artifacts = {rel: {'expected': digest, 'actual': sha256(attempt / rel) if (attempt / rel).is_file() else None,
                       'matches': (attempt / rel).is_file() and sha256(attempt / rel) == digest}
                 for rel, digest in receipt['artifacts_sha256'].items()}
    sources = {}
    for rel, digest in receipt['source_sha256'].items():
        live, snapshot = ROOT / rel, attempt / 'sources' / rel
        live_hash = sha256(live) if live.is_file() else None
        snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
        sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                        'matches': live_hash == digest and snapshot_hash == digest}
    simulation = json.loads((attempt / 'simulation.json').read_text())
    compile_text = (attempt / 'compile.log').read_text(errors='replace')
    warning_matches = [line for line in compile_text.splitlines()
                       if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line)]
    checks = {
        'selected_receipt_path_and_status_match_selection': (
            str(receipt_path.relative_to(ROOT)) == selection['selected_receipt']
            and selection['status'] == receipt['status']
        ),
        'selection_receipt_pass': receipt['status'] == 'PASS_EXACT_RANGE_RECODE' and selection['status'] == receipt['status'],
        'actual_expression_rtl_run': receipt['actual_expression_RTL_run'] is True,
        'full_module_run_explicitly_false': receipt['full_module_RTL_run'] is False,
        'literal_and_model_counts_match': receipt['verdict'] == simulation and simulation == {'status': 'TEST_PASS', 'vectors': 262144}
                                              and receipt['model_binary_values'] == 65536,
        'candidate_hash_matches_current_source': receipt['candidate']['sha256'] == file_hash(receipt['candidate']['path']),
        'all_artifact_hashes_match': all(x['matches'] for x in artifacts.values()),
        'all_current_and_snapshot_sources_match': all(x['matches'] for x in sources.values()),
        'no_compile_warning_failure_or_waiver_text': not warning_matches,
        'all_commands_succeeded': all(x['exit_code'] == 0 for x in receipt['commands']),
    }
    return {'status': 'PASS_VALUE_EXPRESSION_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
            'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
            'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha256(receipt_path),
            'candidate': receipt['candidate'], 'rtl_expression_vectors': receipt['verdict']['vectors'],
            'model_binary_values': receipt['model_binary_values'], 'full_module_RTL_run': receipt['full_module_RTL_run'],
            'artifacts_checked': len(artifacts), 'sources_checked': len(sources),
            'artifact_results': artifacts, 'source_results': sources,
            'warning_matches': warning_matches, 'checks': checks,
            'scope': 'Two-state expression-level RTL proof only; the full module was explicitly not run.'}


def audit_value_check_selection() -> dict:
    return audit_value_check()


def audit_header_focus() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/header'
    selection_path = area / 'results.json'
    audit_path = area / 'audit.json'
    selection = json.loads(selection_path.read_text())
    frozen = json.loads(audit_path.read_text())
    receipt_path = ROOT / selection['selected_report']
    report = json.loads(receipt_path.read_text())
    attempt = receipt_path.parent
    artifacts = {rel: {'expected': digest, 'actual': sha256(attempt / rel) if (attempt / rel).is_file() else None,
                       'matches': (attempt / rel).is_file() and sha256(attempt / rel) == digest}
                 for rel, digest in report['artifacts_sha256'].items()}
    sources = {}
    for rel, digest in report['source_sha256'].items():
        live, snapshot = ROOT / rel, attempt / 'sources' / rel
        live_hash = sha256(live) if live.is_file() else None
        snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
        sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                        'matches': live_hash == digest and snapshot_hash == digest}
    warnings = []
    for name in ('verilator.log', 'compiler.log', 'compile.log', 'binary.log', 'simulation-107701.jsonl', 'simulation-107702.jsonl'):
        fp = attempt / name
        if fp.is_file():
            warnings += [{'file': name, 'line': line.strip()} for line in fp.read_text(errors='replace').splitlines()
                         if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line)]
    run_checks = []
    for run in report.get('runs', []):
        v = run.get('terminal_verdict', {})
        run_checks.append({'seed': run.get('seed'), 'status': v.get('status'), 'cases': v.get('cases'),
            'directed_checks': v.get('directed_checks'), 'trace_replay': run.get('trace_replay', {}).get('status'),
            'quant_replay': run.get('quant_replay', {}).get('status'),
            'pass': v.get('status') == 'TEST_PASS' and v.get('cases') == 86 and v.get('directed_checks') == 44
                and run.get('trace_replay', {}).get('status') == 'PASS'
                and run.get('quant_replay', {}).get('status') == 'PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE'})
    checks = {
        'selection_and_frozen_audit_point_to_report': selection.get('status') == 'PASS'
            and frozen.get('status') == 'PASS_FROZEN_ACTUAL_HEADER_AUDIT'
            and selection.get('selected_report') == frozen.get('selected_receipt')
            and sha256(receipt_path) == frozen.get('selected_receipt_sha256')
            and sha256(receipt_path) == frozen.get('attempts', [{}])[-1].get('sha256'),
        'actual_rtl_strict_warning_and_adapter_claims': report.get('actual_RTL_run') is True
            and report.get('assertions_disabled_or_downgraded') is False and report.get('strict_warnings') is True
            and report.get('complete_production_body_preserved_by_adapters') is True,
        'candidate_hash_matches_current_source': report['candidate']['frozen_after_focused_PASS'] is True
            and report['candidate']['sha256'] == file_hash(report['candidate']['path']) == frozen['candidate']['sha256'],
        'both_seed_verdicts_and_independent_oracles_pass': len(run_checks) == 2 and all(x['pass'] for x in run_checks)
            and report.get('terminal_verdict', {}).get('status') == 'TEST_PASS',
        'all_artifact_and_source_snapshot_hashes_match': all(x['matches'] for x in artifacts.values())
            and all(x['matches'] for x in sources.values()),
        'no_warning_failure_or_waiver_text': not warnings,
        'native_and_parent_qualification_remain_separate': 'remain separate' in frozen.get('scope', ''),
    }
    return {'status': 'PASS_HEADER_FOCUS_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
        'audit': str(audit_path.relative_to(ROOT)), 'audit_sha256': sha256(audit_path),
        'selected_report': str(receipt_path.relative_to(ROOT)), 'selected_report_sha256': sha256(receipt_path),
        'candidate': report['candidate'], 'actual_clock_edges': frozen['actual_clock_edges'],
        'runs': run_checks, 'artifacts_checked': len(artifacts), 'sources_checked': len(sources),
        'artifacts': artifacts, 'sources': sources, 'warning_matches': warnings,
        'full_pipeline_integrated': False, 'checks': checks,
        'scope': frozen['scope'] + ' No timing, full pipeline, hardware FPS, or sub-10ms claim.'}


def audit_header_pipeline() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/header-pipeline'
    attempts = []
    dirs = sorted(p for p in (area / 'attempts').glob('*') if p.is_dir()) if (area / 'attempts').exists() else []
    for folder in dirs:
        receipt_path = folder / 'receipt.json'
        if not receipt_path.is_file():
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PENDING',
                             'retained_inputs': sorted(p.name for p in folder.iterdir() if p.is_file())})
            continue
        receipt = json.loads(receipt_path.read_text())
        artifacts = {rel: {'expected': digest, 'actual': sha256(folder / rel) if (folder / rel).is_file() else None,
                           'matches': (folder / rel).is_file() and sha256(folder / rel) == digest}
                     for rel, digest in receipt.get('artifact_sha256', {}).items()}
        sources = {rel: {'expected': digest,
            'live': sha256(ROOT / rel) if (ROOT / rel).is_file() else None,
            'snapshot': sha256(folder / 'sources' / rel) if (folder / 'sources' / rel).is_file() else None}
            for rel, digest in receipt.get('source_sha256', {}).items()}
        for row in sources.values():
            row['matches'] = row['live'] == row['snapshot'] == row['expected']
        runs = []
        for run in receipt.get('runs', []):
            seed = run.get('seed')
            baseline = ROOT / receipt['baseline_reference']['path']
            baseline_report = json.loads(baseline.read_text())
            baseline_run = next((x for x in baseline_report['runs'] if x['seed'] == seed), {})
            baseline_attempt = baseline.parent
            stdout_path = folder / f'candidate-{seed}-simulation.jsonl'
            candidate_stdout_equal = (stdout_path.is_file() and
                sha256(stdout_path) == sha256(baseline_attempt / f'candidate-{seed}-simulation.jsonl'))
            stream_checks = {}
            for key in ('events', 'canonical_actual'):
                item = run.get('artifacts', {}).get(key, {})
                reference = item.get('reference', {})
                reference_path = ROOT / reference.get('path', '')
                current_path = folder / item.get('path', '')
                try:
                    raw_current = gzip.decompress(current_path.read_bytes())
                    raw_reference = gzip.decompress(reference_path.read_bytes())
                    raw_hash = hashlib.sha256(raw_current).hexdigest()
                    stream_checks[key] = (raw_current == raw_reference and raw_hash == item.get('raw_sha256')
                        and sha256(current_path) == item.get('sha256') == reference.get('sha256'))
                except (OSError, EOFError):
                    stream_checks[key] = False
            runs.append({'seed': seed, 'verdict': run.get('verdict', {}).get('status'),
                'case_profiles': run.get('verdict', {}).get('cases'), 'directed_checks': run.get('verdict', {}).get('directed_checks'),
                'exact_stdout_vs_retained_elastic': candidate_stdout_equal, 'stream_checks': stream_checks,
                'pass': (run.get('verdict', {}).get('status') == 'TEST_PASS'
                    and run.get('verdict', {}).get('cases') == 22 and run.get('verdict', {}).get('directed_checks') == 21
                    and run.get('exact_stdout_events_cycles_and_canonical') is True and candidate_stdout_equal
                    and all(stream_checks.values()))})
        warnings = []
        for name in ('compile.log', 'binary.log', *(f'candidate-{s}-simulation.jsonl' for s in receipt.get('seeds', []))):
            fp = folder / name
            if fp.is_file():
                warnings.extend({'file': name, 'line': line.strip()} for line in fp.read_text(errors='replace').splitlines()
                    if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
        report_path = area / 'results.json'
        selection = json.loads(report_path.read_text()) if report_path.is_file() else {}
        pointer_ok = (selection.get('status') == 'PASS_EXACT_HEADER_CANONICAL'
            and selection.get('selected_receipt') == str(receipt_path.relative_to(ROOT))
            and receipt.get('status') == 'PASS_EXACT_HEADER_CANONICAL'
            and all(selection.get(k) == receipt.get(k) for k in ('runs', 'source_sha256', 'artifact_sha256', 'seeds')))
        checks = {
            'actual_candidate_run_exact_reused_control': receipt.get('actual_RTL_run') is True
                and receipt.get('baseline_recompiled_or_rerun') is False and receipt.get('baseline_reused_actual_RTL') is True
                and receipt.get('newly_executed_candidate_case_profiles') == 44
                and receipt.get('newly_executed_candidate_directed_checks') == 42,
            'two_same_seed_exact_stdout_and_streams': len(runs) == 2 and all(x['pass'] for x in runs)
                and receipt.get('seeds') == [107601, 107602],
            'source_and_artifact_hashes_match': all(x['matches'] for x in artifacts.values())
                and all(x['matches'] for x in sources.values()),
            'all_commands_succeeded_and_no_warning_waiver': all(x.get('exit_code') == 0 for x in receipt.get('commands', []))
                and not warnings,
            'selection_points_to_audited_pass': pointer_ok,
            'no_hardware_or_timing_qualification_claim': receipt.get('hardware_contact') is False
                and receipt.get('full_frame_publication') is False
                and any('no timing' in x.lower() for x in receipt.get('limits', [])),
        }
        passed = receipt.get('status') == 'PASS_EXACT_HEADER_CANONICAL' and all(checks.values())
        attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PASS' if passed else 'AUDIT_ERROR' if not all(checks.values()) and receipt.get('status') == 'PASS_EXACT_HEADER_CANONICAL' else 'TERMINAL_FAILURE_RETAINED',
            'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha256(receipt_path), 'runs': runs,
            'artifacts_checked': len(artifacts), 'sources_checked': len(sources), 'artifacts': artifacts,
            'sources': sources, 'warning_matches': warnings, 'checks': checks})
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text()) if selection_path.is_file() else None
    state = 'PENDING_HEADER_PIPELINE' if not selection or not attempts or attempts[-1]['status'] == 'PENDING' else attempts[-1]['status']
    return {'status': state,
        'selection': str(selection_path.relative_to(ROOT)) if selection else None,
        'selection_sha256': sha256(selection_path) if selection else None,
        'attempts': attempts, 'scope': 'Fresh header candidate comparison against retained same-seed elastic streams; reused control runs are not counted as fresh. No timing or hardware qualification.'}


def audit_selected_attempt(selection_path: Path) -> dict:
    selection = json.loads(selection_path.read_text())
    selected = selection.get('selected_report')
    if not selected:
        return {'status': selection.get('status'), 'checks': {'selected_report_present': False}}
    report_path = ROOT / selected
    report = json.loads(report_path.read_text())
    folder = report_path.parent
    artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                 for rel, digest in report.get('artifacts_sha256', {}).items()}
    sources = {rel: (folder / 'sources' / rel).is_file() and sha256(folder / 'sources' / rel) == digest
               for rel, digest in report.get('source_sha256', {}).items()}
    verdicts = [x.get('terminal_verdict', x.get('verdict', x)) for x in report.get('runs', [])]
    checks = {
        'actual_rtl_run': report.get('actual_RTL_run') is True,
        'artifact_hashes_match': bool(artifacts) and all(artifacts.values()),
        'source_snapshot_hashes_match': bool(sources) and all(sources.values()),
        'seed_verdicts_pass': bool(verdicts) and all(x.get('status') == 'TEST_PASS' for x in verdicts),
        'strict_warnings_enabled': report.get('strict_warnings') is True or any(
            '-Wall' in str(arg) and '-Werror' in str(arg)
            for command in report.get('commands', []) for arg in command.get('argv', [])),
        'candidate_or_all_source_hashes_match_live': (
            file_hash(report['candidate']['path']) == report.get('candidate', {}).get('sha256')
            if report.get('candidate', {}).get('path') else
            bool(report.get('source_sha256')) and all(file_hash(rel) == digest for rel, digest in report.get('source_sha256', {}).items())),
    }
    warnings = []
    for name in ('compile.log', 'binary.log', 'compiler.log', 'verilator.log',
                 *(x for x in folder.glob('*simulation.jsonl') if x.is_file())):
        fp = folder / name if isinstance(name, str) else name
        if fp.is_file():
            warnings.extend({'file': fp.name, 'line': line.strip()} for line in fp.read_text(errors='replace').splitlines()
                if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
    checks['no_runtime_warnings_or_waivers'] = not warnings
    return {'status': 'PASS' if report.get('status') == 'PASS' and all(checks.values()) else 'RETAINED_NONPASS',
            'selected_report': selected, 'result_status': report.get('status'), 'checks': checks,
            'source_hash_checks': sources, 'artifact_hash_checks': artifacts, 'seed_verdicts': verdicts,
            'warning_matches': warnings}


def audit_scale() -> dict:
    base = ROOT / 'experiments/python-gamebub-v107/scale'
    behavioral = audit_selected_attempt(base / 'results.json')
    unit_selection = json.loads((base / 'unit/results.json').read_text())
    unit_path = ROOT / unit_selection['selected_receipt']
    unit = json.loads(unit_path.read_text())
    unit_dir = unit_path.parent
    unit_files = {rel: (unit_dir / rel).is_file() and sha256(unit_dir / rel) == digest
                  for rel, digest in unit.get('retained_sha256', {}).items()}
    modes = (unit_dir / 'reports/ram-modes.tsv').read_text().splitlines()
    mapped_text = (unit_dir / 'reports/mapped.v').read_text(errors='replace')
    unit_log = (unit_dir / 'reports/xsim.log').read_text(errors='replace')
    unit_warnings, unit_environment_advisories = [], []
    for name in ('reports/xvlog.log', 'reports/xelab.log', 'reports/xsim.log'):
        fp = unit_dir / name
        if fp.is_file():
            for line in fp.read_text(errors='replace').splitlines():
                if not re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line):
                    continue
                item = {'file': name, 'line': line.strip()}
                (unit_environment_advisories if '[XSIM 43-3431]' in line else unit_warnings).append(item)
    match = re.search(r'TEST_PASS_SCALE_UNIT clocks=(\d+) old_data_collisions=(\d+) distinct_dual_writes=(\d+) same_address_priority=(\d+) held_outputs=(\d+)', unit_log)
    unit_checks = {
        'receipt_hash_matches_selection': sha256(unit_path) == unit_selection['sha256'],
        'all_retained_file_hashes_match': bool(unit_files) and all(unit_files.values()),
        'current_source_matches': file_hash(unit['source']['path']) == unit['source']['sha256'],
        'mapped_actual_unisim_no_sdf': unit.get('mode') == 'post-synthesis functional mapped actual UNISIM, no SDF'
            and unit.get('actual_native_parameters_and_models') is True,
        'no_timing_relaxation_or_collision_waiver': unit.get('no_clock_relaxation') is True
            and unit.get('no_collision_warning_disable') is True,
        'terminal_mapped_sim_pass': unit.get('status') == 'PASS_MAPPED_UNISIM_SCALE_COLLISIONS'
            and unit.get('exit_code') == 0 and match is not None,
        'no_mapped_unit_runtime_warning_or_waiver': not unit_warnings,
        'physical_ram_modes_are_read_first_both_ports': any(
            row.split('\t')[:9] == ['words_reg', 'RAMB18E1', 'TDP', '9', '9', '9', '9', 'READ_FIRST', 'READ_FIRST']
            for row in modes[1:]),
        'b_output_hold_logic_is_in_mapped_rtl_netlist': 'b_q[0]_INST_0' in mapped_text
            and 'b_q[1]_INST_0' in mapped_text and mapped_text.count('LUT3 #(') >= 2
            and 'WRITE_MODE_B("READ_FIRST")' in mapped_text,
    }
    unit_metrics = ({'clocks': int(match[1]), 'old_data_collisions': int(match[2]), 'distinct_dual_writes': int(match[3]),
                     'same_address_priority': int(match[4]), 'held_outputs': int(match[5])} if match else None)

    probe_selection = json.loads((base / 'lookup-probe/results.json').read_text())
    probe_path = ROOT / probe_selection['selected_receipt']
    probe = json.loads(probe_path.read_text())
    probe_dir = probe_path.parent
    probe_files = {rel: (probe_dir / rel).is_file() and sha256(probe_dir / rel) == digest
                   for rel, digest in probe.get('retained_sha256', {}).items()}
    parents = sorted((ROOT / 'experiments/python-gamebub-v107/native').glob('*/receipt.json'))
    parent_matches = [str(p.relative_to(ROOT)) for p in parents if sha256(p) == probe.get('parent_receipt_sha256')]
    clocks = re.findall(r'^\s*(\S+)\s+(\d+\.\d+)\s+\{[^}]+\}',
                        (probe_dir / 'reports/clocks.rpt').read_text(), re.M)
    endpoint_rows = [x.split('\t') for x in (probe_dir / 'reports/endpoints.tsv').read_text().splitlines()[1:]]
    paths = {}
    for kind in ('mode', 'scale'):
        rows = (probe_dir / f'reports/lookup-{kind}-paths.tsv').read_text().splitlines()[1:]
        paths[kind] = [{'startpoint': x[0], 'endpoint': x[1], 'slack_ns': float(x[2]),
                        'datapath_delay_ns': float(x[3]), 'logic_levels': int(x[4])} for x in (r.split('\t') for r in rows)]
    probe_checks = {
        'selection_receipt_hash_matches': sha256(probe_path) == probe_selection['sha256'],
        'all_retained_file_hashes_match': bool(probe_files) and all(probe_files.values()),
        'read_only_checkpoint_unchanged': probe.get('checkpoint_readonly') is True
            and probe.get('checkpoint_sha256_before') == probe.get('checkpoint_sha256_after'),
        'parent_receipt_hash_resolves_once': len(parent_matches) == 1,
        'no_rtl_clock_or_exception_edits': probe.get('no_RTL_or_clock_or_exception_edits') is True,
        'probe_terminal_pass': probe.get('status') == 'PASS_READONLY_TIMING_EXTRACTION' and probe.get('exit_code') == 0,
        'only_inherited_10ns_clock': clocks == [('component_clk', '10.000')],
        'four_expected_register_endpoints': sum(r[0] == 'mode' for r in endpoint_rows) == 2
            and sum(r[0] == 'scale' for r in endpoint_rows) == 2,
        'both_lookup_cones_have_negative_slack': all(len(paths[k]) == 2 and all(p['slack_ns'] < 0 for p in paths[k]) for k in paths),
    }
    errors = [k for k, v in {**unit_checks, **probe_checks}.items() if not v]
    if behavioral['status'] != 'PASS':
        errors.append('scale_behavioral_evidence_not_pass')
    return {
        'status': 'PASS_SCALE_BEHAVIOR_AND_DIAGNOSTICS' if not errors else 'AUDIT_ERROR',
        'behavioral': behavioral,
        'mapped_unit': {'receipt': str(unit_path.relative_to(ROOT)), 'checks': unit_checks,
                        'retained_hash_checks': unit_files, 'terminal_metrics': unit_metrics,
                        'warning_matches': unit_warnings,
                        'tool_environment_advisories': unit_environment_advisories,
                        'physical_ram_modes': modes,
                        'scope': 'Post-synthesis mapped actual UNISIM functional simulation, no SDF; unit timing only.'},
        'readonly_lookup_probe': {'receipt': str(probe_path.relative_to(ROOT)), 'checks': probe_checks,
                                  'parent_receipt_matches': parent_matches, 'paths': paths,
                                  'scope': 'Read-only extraction from retained elastic route checkpoint; not a routed SCALE variant.'},
        'semantic_note': 'RAMB18E1 uses READ_FIRST on both physical ports. B-output hold behavior is RTL hold logic; it is not a NO_CHANGE primitive-mode setting.',
        'full_scale_pipeline_canonical_and_native': 'DEFERRED', 'errors': errors,
    }


def audit_tables() -> dict:
    base = ROOT / 'experiments/python-gamebub-v107/tables'
    focus = audit_selected_attempt(base / 'results.json')
    pipeline = audit_tables_pipeline()
    focus_history = []
    for result_path in sorted((base / 'attempts').glob('*/results.json')):
        report = json.loads(result_path.read_text())
        folder = result_path.parent
        artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                     for rel, digest in report.get('artifacts_sha256', {}).items()}
        sources = {rel: (folder / 'sources' / rel).is_file() and sha256(folder / 'sources' / rel) == digest
                   for rel, digest in report.get('source_sha256', {}).items()}
        command_codes = [x.get('exit_code') for x in report.get('commands', [])]
        sim = (folder / 'simulation-107701.jsonl').read_text(errors='replace') if (folder / 'simulation-107701.jsonl').is_file() else ''
        assertion_failure = any(x not in (0, None) for x in command_codes) and '%Fatal:' in sim and 'Assertion failed' in sim
        status = 'PASS' if report.get('status') == 'PASS' and report.get('actual_RTL_run') is True else (
            'EXECUTED_RTL_ASSERTION_FAILURE' if assertion_failure else 'TERMINAL_FAILURE_RETAINED')
        focus_history.append({'report': str(result_path.relative_to(ROOT)), 'sha256': sha256(result_path),
                              'status': status, 'runner_actual_RTL_run_flag': report.get('actual_RTL_run'),
                              'command_exit_codes': command_codes, 'assertion_failure_in_original_fixture': assertion_failure,
                              'error': report.get('error'), 'artifact_hashes_match': bool(artifacts) and all(artifacts.values()),
                              'source_snapshots_match': bool(sources) and all(sources.values()),
                              'artifacts_checked': len(artifacts), 'sources_checked': len(sources)})
    select = json.loads((base / 'unit/results.json').read_text())
    receipt_path = ROOT / select['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    folder = receipt_path.parent
    retained = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                for rel, digest in receipt.get('retained_sha256', {}).items()}
    unit_log = (folder / 'reports/xsim.log').read_text(errors='replace') if (folder / 'reports/xsim.log').is_file() else ''
    unit_warnings, unit_environment_advisories = [], []
    for name in ('reports/xvlog.log', 'reports/xelab.log', 'reports/xsim.log'):
        fp = folder / name
        if fp.is_file():
            for line in fp.read_text(errors='replace').splitlines():
                if not re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line):
                    continue
                item = {'file': name, 'line': line.strip()}
                (unit_environment_advisories if '[XSIM 43-3431]' in line else unit_warnings).append(item)
    modes_path = folder / 'reports/ram-modes.tsv'
    mode_rows = modes_path.read_text().splitlines() if modes_path.is_file() else []
    mapped_text = (folder / 'reports/mapped.v').read_text(errors='replace') if (folder / 'reports/mapped.v').is_file() else ''
    expected_table_modes = (
        'modes/words_reg\tRAMB18E1\tTDP\t2\t2\t2\t2\tREAD_FIRST\tWRITE_FIRST' in '\n'.join(mode_rows)
        and 'scales/words_reg\tRAMB18E1\tTDP\t9\t9\t9\t9\tREAD_FIRST\tREAD_FIRST' in '\n'.join(mode_rows)
    )
    unit_ok = (sha256(receipt_path) == select['sha256'] and bool(retained) and all(retained.values())
               and receipt.get('status') == 'PASS_MAPPED_UNISIM_TABLES_COLLISIONS'
               and receipt.get('actual_native_parameters_and_models') is True and 'TEST_PASS_TABLES_UNIT' in unit_log
               and expected_table_modes and 'b_q[0]_INST_0' in mapped_text and 'b_q[1]_INST_0' in mapped_text
               and not unit_warnings)
    status = 'PASS_TABLES_PIPELINE_AUDITED' if unit_ok and focus['status'] == 'PASS' and pipeline['status'] == 'PASS' else 'PENDING_TABLES_FULL_EVIDENCE'
    return {'status': status,
            'selected_behavioral': focus,
            'focus_attempt_history': focus_history,
            'mapped_unit': {'receipt': str(receipt_path.relative_to(ROOT)), 'status': receipt.get('status'),
                            'checks': retained, 'all_retained_hashes_match': bool(retained) and all(retained.values()),
                            'receipt_hash_matches': sha256(receipt_path) == select['sha256'],
                            'terminal_mapped_sim_pass': 'TEST_PASS_TABLES_UNIT' in unit_log,
                            'scale_output_hold_mux_present': 'b_q[0]_INST_0' in mapped_text and 'b_q[1]_INST_0' in mapped_text,
                            'warning_matches': unit_warnings,
                            'tool_environment_advisories': unit_environment_advisories,
                            'expected_physical_ram_modes': expected_table_modes, 'ram_modes': mode_rows,
                            'scope': 'Mapped actual UNISIM unit evidence only; not full pipeline or routed timing.'},
            'full_pipeline': pipeline,
            'scope': 'TABLES combines scale and mode RAM changes; native route remains required.'}


def audit_payload_reset() -> dict:
    base = ROOT / 'experiments/python-gamebub-v107'
    domain = {}
    for label in ('payload-reset', 'idct-reset'):
        area = base / label
        selection_path = area / 'results.json'
        focus = audit_selected_attempt(selection_path)
        selection = json.loads(selection_path.read_text())
        report_path = ROOT / selection['selected_report']
        report = json.loads(report_path.read_text())
        audit_path = area / 'audit.json'
        independent = json.loads(audit_path.read_text())
        source_field = 'fpga/experiments/cu66-v107-payload-reset/cu66_dequant.sv' if label == 'payload-reset' else 'fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv'
        selected_candidate = report.get('candidate', {})
        commands_ok = bool(report.get('commands')) and all(x.get('exit_code') == 0 for x in report['commands'])
        runs = report.get('runs', [])
        run_checks = []
        for run in runs:
            if label == 'payload-reset':
                run_checks.append(run.get('status') == 'TEST_PASS' and run.get('accepted') == 6716
                    and run.get('retired') == 6686 and run.get('discarded') == 30
                    and run.get('kill_edges') == 253 and run.get('owned_input_noise_edges', 0) > 0)
            else:
                verdict = run.get('verdict', {})
                replay = run.get('trace_replay', {})
                run_checks.append(verdict.get('status') == 'TEST_PASS' and verdict.get('states') == 1023
                    and verdict.get('abort_state_mask') == 1023 and verdict.get('tiles') == 4303
                    and verdict.get('completed_tiles') == 4333 and replay.get('status') == 'PASS')
        focus_checks = {
            'focus_candidate_source_is_exact': selected_candidate.get('path') == source_field
                and selected_candidate.get('sha256') == report.get('source_sha256', {}).get(source_field)
                and file_hash(source_field) == selected_candidate.get('sha256'),
            'actual_rtl_and_all_commands_succeeded': report.get('actual_RTL_run') is True and commands_ok,
            'all_run_verdicts_and_domain_counts_pass': len(runs) == (3 if label == 'payload-reset' else 2)
                and all(run_checks),
            'full_public_outputs_compared': (report.get('full_public_outputs_compared_including_invalid') is True
                if label == 'payload-reset' else report.get('assertions_disabled_or_downgraded') is False),
            'domain_independent_audit_binds_selected_report': independent.get('selected_report', independent.get('selected_receipt')) == selection['selected_report']
                and independent.get('status', '').startswith('PASS')
                and independent.get('source_sha256') in (selected_candidate.get('sha256'), report.get('source_sha256', {}).get(source_field)),
        }
        independent_hash_ok = independent.get('receipt_sha256') == sha256(report_path) if label == 'idct-reset' else (
            independent.get('authoritative_native_query') is not None)
        focus_checks['independent_audit_hash_link_is_valid'] = independent_hash_ok
        domain[label] = {'status': 'PASS' if focus['status'] == 'PASS' and all(focus_checks.values()) else 'AUDIT_ERROR',
                         'selection': str(selection_path.relative_to(ROOT)), 'selected_report': selection['selected_report'],
                         'focus': focus, 'independent_audit': str(audit_path.relative_to(ROOT)),
                         'checks': focus_checks, 'run_counts': runs}

    # Payload reset's standalone mapped unit and follow-up exact fan-in query.
    p_area = base / 'payload-reset/native'
    p_select = json.loads((p_area / 'results.json').read_text())
    p_receipt_path = ROOT / p_select['selected_receipt']
    p_receipt = json.loads(p_receipt_path.read_text())
    p_dir = p_receipt_path.parent
    p_artifacts = {rel: (p_dir / rel).is_file() and sha256(p_dir / rel) == digest
                   for rel, digest in p_receipt.get('artifacts_sha256', {}).items()}
    p_focus_report_path = ROOT / p_receipt.get('focus_report', '')
    p_focus = json.loads(p_focus_report_path.read_text()) if p_focus_report_path.is_file() else {}
    p_source_checks = {rel: file_hash(rel) == digest for rel, digest in p_receipt.get('source_sha256', {}).items()}
    p_metrics = p_receipt.get('metrics', {})
    p_native_ok = (p_select.get('status') == 'PASS_MEASURED_PRIVATE_RESET_AND_INPUT_CONTROL_REMOVAL'
        and sha256(p_receipt_path) == p_select.get('sha256')
        and p_receipt.get('status') == 'PASS_MEASURED_PRIVATE_RESET_AND_INPUT_CONTROL_REMOVAL'
        and p_receipt.get('exit_code') == 0 and p_receipt.get('source_unchanged') is True
        and p_receipt.get('no_parent_timing_claim') is True
        and p_focus_report_path.is_file() and p_receipt.get('focus_report') == domain['payload-reset']['selected_report']
        and p_receipt.get('candidate_sha256') == p_focus.get('candidate', {}).get('sha256')
        and bool(p_artifacts) and all(p_artifacts.values()) and bool(p_source_checks) and all(p_source_checks.values())
        and p_metrics.get('candidate', {}).get('payload_cells') == 1027
        and p_metrics.get('candidate', {}).get('payload_grounded_reset') == 1027
        and p_metrics.get('candidate', {}).get('payload_reset_port_fanin') == 0
        and p_metrics.get('candidate', {}).get('payload_ce_port_fanin') == 0
        and p_metrics.get('candidate', {}).get('reset_port_fanin') == ['']
        and p_metrics.get('candidate', {}).get('ce_port_fanin') == ['']
        and p_metrics.get('original', {}).get('payload_grounded_reset') == 0)
    p_query_select = json.loads((p_area / 'query-results.json').read_text())
    p_query_path = ROOT / p_query_select['selected_receipt']
    p_query = json.loads(p_query_path.read_text())
    p_query_dir = p_query_path.parent
    p_query_artifacts = {rel: (p_query_dir / rel).is_file() and sha256(p_query_dir / rel) == digest
                         for rel, digest in p_query.get('artifacts_sha256', {}).items()}
    query_metrics = p_query.get('metrics', {})
    p_query_ok = (p_query_select.get('status') == 'PASS_EXACT_MAPPED_PAYLOAD_RESET_AND_CE_FANIN'
        and sha256(p_query_path) == p_query_select.get('sha256')
        and p_query.get('status') == 'PASS_EXACT_MAPPED_PAYLOAD_RESET_AND_CE_FANIN'
        and p_query.get('exit_code') == 0 and p_query.get('candidate_sha256') == p_receipt.get('candidate_sha256')
        and p_query.get('prior_receipt') == str(p_receipt_path.relative_to(ROOT))
        and p_query.get('prior_receipt_sha256') == sha256(p_receipt_path)
        and p_query.get('dcp_sha256_before') == p_query.get('dcp_sha256_after')
        and bool(p_query_artifacts) and all(p_query_artifacts.values())
        and query_metrics.get('candidate', {}).get('cells') == 1027
        and query_metrics.get('candidate', {}).get('ground_reset') == 1027
        and query_metrics.get('candidate', {}).get('reset_ports') == ['']
        and query_metrics.get('candidate', {}).get('ce_ports') == ['']
        and query_metrics.get('original', {}).get('ground_reset') == 0
        and query_metrics.get('original', {}).get('reset_ports') == ['abort_i rst']
        and query_metrics.get('original', {}).get('ce_ports') == ['abort_i in_valid rst'])

    # IDCT native mapping is pending while RUNNING; check its source/focus identity now.
    i_area = base / 'idct-reset/native'
    i_select_path = i_area / 'results.json'
    i_select = json.loads(i_select_path.read_text()) if i_select_path.is_file() else None
    i_receipt_path = ROOT / i_select['selected_receipt'] if i_select else None
    i_receipt = json.loads(i_receipt_path.read_text()) if i_receipt_path and i_receipt_path.is_file() else {}
    i_sources = {rel: file_hash(rel) == digest for rel, digest in i_receipt.get('source_sha256', {}).items()}
    i_dir = i_receipt_path.parent if i_receipt_path else None
    i_artifacts = {rel: (i_dir / rel).is_file() and sha256(i_dir / rel) == digest
                   for rel, digest in i_receipt.get('artifacts_sha256', {}).items()} if i_dir else {}
    i_focus_path = ROOT / i_receipt.get('focus_report', '') if i_receipt.get('focus_report') else None
    i_focus_sha_ok = i_focus_path is not None and i_focus_path.is_file() and sha256(i_focus_path) == i_receipt.get('focus_report_sha256')
    i_native_pending = i_receipt.get('status') == 'RUNNING'
    i_running_identity_ok = (i_focus_sha_ok and i_receipt.get('no_parent_timing_claim') is True
        and i_receipt.get('synthetic_unit_clock_ns') == 10
        and all(i_sources.values()) and bool(i_sources)
        and i_receipt.get('candidate_sha256') == json.loads((base/'idct-reset/results.json').read_text()).get('candidate', {}).get('sha256'))
    i_selection_ok = bool(i_select and i_receipt_path and sha256(i_receipt_path) == i_select.get('sha256')
        and i_select.get('status') == i_receipt.get('status'))
    i_metrics = i_receipt.get('metrics', {})
    i_native_ok = (i_selection_ok and i_running_identity_ok and i_receipt.get('status') == 'PASS_MEASURED_PRIVATE_RESET_AND_INPUT_CONTROL_REMOVAL'
        and i_receipt.get('exit_code') == 0 and i_receipt.get('source_unchanged') is True
        and bool(i_artifacts) and all(i_artifacts.values())
        and i_metrics.get('candidate', {}).get('payload_cells') == 1280
        and i_metrics.get('candidate', {}).get('payload_grounded_reset') == 1280
        and i_metrics.get('candidate', {}).get('payload_reset_port_fanin') == 0
        and i_metrics.get('candidate', {}).get('payload_ce_port_fanin') == 0
        and i_metrics.get('candidate', {}).get('reset_port_fanin') == ['']
        and i_metrics.get('candidate', {}).get('ce_port_fanin') == ['']
        and i_metrics.get('original', {}).get('payload_grounded_reset') == 0
        and i_metrics.get('original', {}).get('payload_reset_port_fanin') == 1280
        and i_metrics.get('original', {}).get('payload_ce_port_fanin') == 1280
        and i_metrics.get('original', {}).get('reset_port_fanin') == ['abort_frame rst']
        and i_metrics.get('original', {}).get('ce_port_fanin') == ['abort_frame in_valid rst'])

    pipeline = audit_tables_pipeline('payload-pipeline', 'PASS_EXACT_PAYLOAD_CANONICAL',
                                     'PENDING_PAYLOAD_FULL_EVIDENCE', 'payload-reset')
    proof_pass = all(x['status'] == 'PASS' for x in domain.values()) and p_native_ok and p_query_ok and i_native_ok
    pending = i_native_pending and i_running_identity_ok
    status = 'PASS_PAYLOAD_RESET_COMPONENT_PROOFS' if proof_pass else 'PENDING_PAYLOAD_RESET_COMPONENT_PROOFS' if pending else 'AUDIT_ERROR'
    return {'status': status, 'focus_proofs': domain,
        'dequant_native': {'receipt': str(p_receipt_path.relative_to(ROOT)), 'status': p_receipt.get('status'),
            'checks': {'selection_receipt_hash': sha256(p_receipt_path) == p_select.get('sha256'),
                       'source_hashes_match_current': bool(p_source_checks) and all(p_source_checks.values()),
                       'retained_artifact_hashes_match': bool(p_artifacts) and all(p_artifacts.values()),
                       'private_reset_and_ce_removed_metrics_match': p_native_ok}, 'metrics': p_metrics},
        'dequant_mapped_query': {'receipt': str(p_query_path.relative_to(ROOT)), 'status': p_query.get('status'),
            'checks': {'selection_receipt_hash': sha256(p_query_path) == p_query_select.get('sha256'),
                       'prior_receipt_and_checkpoint_unchanged': p_query_ok,
                       'retained_artifact_hashes_match': bool(p_query_artifacts) and all(p_query_artifacts.values())},
            'metrics': query_metrics, 'correction': p_query.get('correction')},
        'idct_native': {'receipt': str(i_receipt_path.relative_to(ROOT)) if i_receipt_path else None,
            'status': i_receipt.get('status'), 'pending': i_native_pending,
            'selection_hash_matches': i_selection_ok, 'artifact_checks': i_artifacts,
            'source_checks': i_sources, 'focus_report_sha256_matches': i_focus_sha_ok,
            'source/focus_identity_checks_pass': i_running_identity_ok, 'terminal_metrics': i_metrics,
            'terminal_mapping_pass': i_native_ok,
            'scope': 'Single-unit synthetic 10 ns component inference only; no parent-route timing or hardware CDC claim.'},
        'full_payload_pipeline': pipeline,
        'scope': 'Reset/CE control changes only; independent proof at finite component-cycle scope. No CDC metastability, full-parent timing, or hardware claim.'}


def audit_guard_dsp() -> dict:
    base = ROOT / 'experiments/python-gamebub-v107/guard-dsp'
    selection_path = base / 'results.json'
    selection = json.loads(selection_path.read_text())
    report_path = ROOT / selection['selected_report']
    report = json.loads(report_path.read_text())
    folder = report_path.parent
    run = json.loads((folder / 'run.json').read_text())
    artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                 for rel, digest in report.get('artifacts_sha256', {}).items()}
    sources = {rel: {'snapshot': (folder / 'sources' / rel).is_file()
                     and sha256(folder / 'sources' / rel) == digest,
                     'live': (ROOT / rel).is_file() and file_hash(rel) == digest}
               for rel, digest in report.get('source_sha256', {}).items()}
    audit_path = base / 'audit.json'
    domain_audit = json.loads(audit_path.read_text())
    attribution_path = base / 'attribution/receipt.json'
    attribution = json.loads(attribution_path.read_text())
    table_receipts = []
    for path in sorted((ROOT / 'experiments/python-gamebub-v107/native').glob('*/receipt.json')):
        inputs_path = path.parent / 'inputs.json'
        if inputs_path.is_file() and json.loads(inputs_path.read_text()).get('variant') == 'tables':
            table_receipts.append(path)
    table_receipt_path = table_receipts[0] if len(table_receipts) == 1 else None
    table_receipt_sha = sha256(table_receipt_path) if table_receipt_path else None
    attr_files = {rel: (base / 'attribution' / rel).is_file()
                  and sha256(base / 'attribution' / rel) == digest
                  for rel, digest in attribution.get('artifacts_sha256', {}).items()}
    attribution_ok = (attribution.get('status') == 'PASS_EXACT_MAPPED_CONSTANT43_ATTRIBUTION'
        and attribution.get('read_only') is True and table_receipt_sha is not None
        and attribution.get('parent_receipt_sha256') == table_receipt_sha
        and attribution.get('checkpoint_sha256_before') == attribution.get('checkpoint_sha256_after')
        and attribution.get('source_sha256') == report.get('source_sha256', {}).get(attribution.get('source'))
        and attribution.get('primitive') == 'DSP48E1'
        and attribution.get('registers') == {'AREG': 1, 'BREG': 0, 'MREG': 0, 'PREG': 0}
        and attribution.get('B_constant') == 43 and attribution.get('A_nonconstant_bits') == 17
        and attribution.get('A_high_bits_grounded') == 13
        and bool(attr_files) and all(attr_files.values()))
    probe_selection_path = base / 'route-probe/results.json'
    probe_selection = json.loads(probe_selection_path.read_text())
    probe_path = ROOT / probe_selection['selected_receipt']
    probe = json.loads(probe_path.read_text())
    probe_dir = probe_path.parent
    probe_files = {rel: (probe_dir / rel).is_file() and sha256(probe_dir / rel) == digest
                   for rel, digest in probe.get('retained_sha256', {}).items()}
    clocks = re.findall(r'^\s*(\S+)\s+(\d+\.\d+)\s+\{[^}]+\}',
        (probe_dir / 'reports/clocks.rpt').read_text(), re.M)
    dsp_rows = [[c.strip() for c in row.split('\t')] for row in
                (probe_dir / 'reports/dsp-paths.tsv').read_text().splitlines()[1:]]
    probe_ok = (probe_selection.get('status') == 'PASS_READONLY_TIMING_EXTRACTION'
        and sha256(probe_path) == probe_selection.get('sha256')
        and probe.get('status') == 'PASS_READONLY_TIMING_EXTRACTION' and probe.get('exit_code') == 0
        and table_receipt_sha is not None and probe.get('parent_receipt_sha256') == table_receipt_sha
        and probe.get('checkpoint_readonly') is True
        and probe.get('checkpoint_sha256_before') == probe.get('checkpoint_sha256_after')
        and probe.get('no_RTL_or_clock_or_exception_edits') is True
        and bool(probe_files) and all(probe_files.values()) and clocks == [('component_clk', '10.000')]
        and len(dsp_rows) >= 1 and all(float(x[2]) < 0 for x in dsp_rows)
        and any(float(x[2]) == -2.497 and float(x[3]) == 12.208 and int(x[4]) == 11 for x in dsp_rows))
    focus_ok = (selection.get('status') == 'PASS' and report.get('status') == 'PASS'
        and report.get('actual_RTL_run') is True and run.get('status') == 'TEST_PASS'
        and run.get('seed') == 107943 and run.get('rows') == 1179648
        and run.get('all17bit_operands_per_product') == 131072 and run.get('count_cases_per_operand') == 9
        and run.get('high32_scratch_counts') == 458581
        and bool(artifacts) and all(artifacts.values()) and bool(sources)
        and all(x['snapshot'] and x['live'] for x in sources.values())
        and all(x.get('exit_code') == 0 for x in report.get('commands', [])))
    independent_ok = (domain_audit.get('status') == 'PASS_EXTRACTED_EXPRESSION_SOURCE_RECIPES_AND_ROUTED_MOTIVATION'
        and domain_audit.get('full_module_or_new_native_mapping_claim') is False
        and domain_audit.get('actual_RTL_expression_rows') == 1179648
        and domain_audit.get('all17bit_operands_per_product') == 131072
        and domain_audit.get('full32_count_cases_per_operand') == 9
        and domain_audit.get('routed_original_DSP_worst_slack_ns') == -2.497
        and domain_audit.get('attribution_receipt_sha256') == sha256(attribution_path)
        and domain_audit.get('routed_probe_receipt_sha256') == sha256(probe_path))
    pipeline = audit_tables_pipeline('guard-pipeline', 'PASS_EXACT_GUARD_CANONICAL',
                                     'PENDING_GUARD_FULL_EVIDENCE', 'payload/reset/control-guard')
    focus_record = {'status': 'PASS' if focus_ok and independent_ok and attribution_ok and probe_ok else 'AUDIT_ERROR',
        'selected_report': str(report_path.relative_to(ROOT)), 'run': run,
        'checks': {'focus_source_and_artifact_hashes_match': focus_ok,
            'expression_audit_explicitly_limits_full_module_claim': independent_ok,
            'mapped_constant43_attribution_matches_tables_checkpoint': attribution_ok,
            'readonly_routed_probe_matches_tables_checkpoint': probe_ok},
        'source_checks': sources, 'artifact_checks': artifacts,
        'attribution_receipt': str(attribution_path.relative_to(ROOT)),
        'route_probe_receipt': str(probe_path.relative_to(ROOT)),
        'probe_paths': [{'source': x[0], 'endpoint': x[1], 'slack_ns': float(x[2]),
                         'datapath_delay_ns': float(x[3]), 'logic_levels': int(x[4])} for x in dsp_rows]}
    return {'status': 'PASS_GUARD_DSP_FOCUS_AUDITED' if focus_record['status'] == 'PASS' else 'AUDIT_ERROR',
            'focus': focus_record, 'full_pipeline': pipeline,
            'scope': 'Isolated exact 32-bit guard-expression proof plus read-only DSP path attribution/probe. Not full-module mapping/timing; full candidate and native route are separate gates.'}


def audit_meta_flags() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/meta-flags'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    report_path = ROOT / selection['selected_report']
    report = json.loads(report_path.read_text())
    folder = report_path.parent
    audit_path = area / 'audit.json'
    audit = json.loads(audit_path.read_text())
    artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                 for rel, digest in report.get('artifacts_sha256', {}).items()}
    sources = {rel: {'snapshot': (folder / 'sources' / rel).is_file()
                     and sha256(folder / 'sources' / rel) == digest,
                     'current': (ROOT / rel).is_file() and file_hash(rel) == digest}
               for rel, digest in report.get('source_sha256', {}).items()}
    stages, inverses = report.get('stage_runs', []), report.get('inverse_runs', [])
    logs = sorted(folder.glob('*.log'))
    warnings = [{'file': fp.name, 'line': line.strip()}
                for fp in logs for line in fp.read_text(errors='replace').splitlines()
                if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line)]
    commands_ok = bool(report.get('commands')) and all(x.get('exit_code') == 0 for x in report['commands'])
    stage_pass = (len(stages) == 2 and [x.get('seed') for x in stages] == [108001, 108002]
        and all(x.get('status') == 'TEST_PASS' for x in stages)
        and sum(x.get('edges', 0) for x in stages) == 67715579
        and stages[0].get('metadata_cases') == 67108864 and stages[0].get('helper_cases') == 32768
        and stages[0].get('domain_cases') == 262144)
    inverse_pass = (len(inverses) == 2 and [x.get('seed') for x in inverses] == [108001, 108002]
        and all(x.get('status') == 'TEST_PASS' for x in inverses)
        and sum(x.get('prepared_clocks', 0) + x.get('historical_clocks', 0) for x in inverses) == 41697
        and all(x.get('word_count') == 128 and x.get('concurrent_math_cases') == 51
                and x.get('late_same_edge_write_fail_cases') == 2 for x in inverses))
    selection_ok = (selection.get('status') == 'PASS' and selection.get('actual_RTL_run') is True
        and selection.get('selected_report_sha256') == sha256(report_path)
        and audit.get('status') == 'PASS' and audit.get('receipt_sha256') == sha256(report_path)
        and audit.get('stage_edges') == 67715579 and audit.get('inverse_edges') == 41697
        and audit.get('source_files_checked') == len(sources) and audit.get('artifacts_checked') > 0)
    checks = {'selector_and_independent_audit_bind_report': selection_ok,
        'source_snapshots_and_live_sources_match': bool(sources) and all(x['snapshot'] and x['current'] for x in sources.values()),
        'retained_artifacts_match': bool(artifacts) and all(artifacts.values()),
        'actual_stage_edge_and_domain_tests_pass': stage_pass,
        'actual_inverse_and_historical_comparison_pass': inverse_pass,
        'strict_assertions_warnings_and_commands': report.get('strict_warnings') is True
            and report.get('warning_suppression') is False and report.get('assertions_disabled_or_downgraded') is False
            and report.get('added_public_cycles') == 0 and commands_ok and not warnings}
    pipeline = audit_tables_pipeline('meta-pipeline', 'PASS_EXACT_META_CANONICAL',
                                     'PENDING_META_FULL_EVIDENCE', 'META')
    return {'status': 'PASS_META_FLAGS_UNIT_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'selected_report': str(report_path.relative_to(ROOT)), 'checks': checks,
        'stage_runs': stages, 'inverse_runs': inverses, 'source_checks': sources,
        'artifact_checks': artifacts, 'warning_matches': warnings, 'full_pipeline': pipeline,
        'scope': 'Standalone meta-flag stage and inverse behavioral proofs plus an independent full-pipeline canonical gate. No native mapping or hardware timing claim.'}


def _audit_focus_hashes(folder: Path, report: dict, artifact_field: str = 'artifacts_sha256') -> dict:
    artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                 for rel, digest in report.get(artifact_field, {}).items()}
    sources = {rel: {'snapshot': (folder / 'sources' / rel).is_file()
                     and sha256(folder / 'sources' / rel) == digest,
                     'current': (ROOT / rel).is_file() and file_hash(rel) == digest}
               for rel, digest in report.get('source_sha256', {}).items()}
    return {'artifacts': artifacts, 'sources': sources}


def audit_prefix_qualification() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/plan-prefix'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    report_rel = selection.get('selected_report')
    report_path = ROOT / report_rel if report_rel else None
    report = json.loads(report_path.read_text()) if report_path and report_path.is_file() else {}
    folder = report_path.parent if report_path else area
    hashes = _audit_focus_hashes(folder, report)
    independent_path = area / 'audit.json'
    independent = json.loads(independent_path.read_text())
    artifacts_ok = bool(hashes['artifacts']) and all(hashes['artifacts'].values())
    sources_ok = bool(hashes['sources']) and all(x['snapshot'] and x['current'] for x in hashes['sources'].values())
    commands = report.get('commands', [])
    negative_rows = report.get('negative_owner_contract_rejections', [])
    expected_pairs = {(mode, index) for mode in (1, 2) for index in (33, 37, 41)}
    expected_by_pair = {(int(row.get('mode', -1)), int(row.get('index', -1))): row for row in negative_rows}
    command_outcomes = []
    observed_negative = {}
    for command in commands:
        argv = command.get('argv', [])
        pair = None
        try:
            pair = (int(argv[-2]), int(argv[-1]))
        except (ValueError, TypeError, IndexError):
            pass
        if pair in expected_pairs:
            observed_negative[pair] = command.get('exit_code')
            command_outcomes.append({'negative_pair': list(pair), 'exit_code': command.get('exit_code'),
                                     'no_stop_reason': command.get('stop_reason') in (None, '')})
        else:
            command_outcomes.append({'negative_pair': None, 'exit_code': command.get('exit_code'),
                                     'no_stop_reason': command.get('stop_reason') in (None, '')})
    negative_checks = {}
    for pair in sorted(expected_pairs):
        row = expected_by_pair.get(pair, {})
        log_path = folder / row.get('log', '')
        text = log_path.read_text(errors='replace') if log_path.is_file() else ''
        negative_checks[f'{pair[0]}:{pair[1]}'] = (
            row.get('status') == 'PASS_EXPECTED_ASSERTION_REJECTION'
            and row.get('capture_enable') is False and row.get('post_rejection_recovery_claim') is False
            and observed_negative.get(pair) == 134
            and 'EXPECTED_ASSERTION_ARMED' in text and 'capture_enable":false' in text
            and 'Assertion failed' in text and 'stale staging response' in text
        )
    normal_log_warnings = []
    for log in sorted(folder.glob('*.log')):
        if log.name.startswith('capture-negative-'):
            continue
        normal_log_warnings.extend({'file': log.name, 'line': line.strip()}
            for line in log.read_text(errors='replace').splitlines()
            if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
    math = report.get('math', {})
    capture_runs = report.get('capture_runs', [])
    runs = report.get('runs', [])
    run_checks = (len(runs) == 4 and {(x.get('sync_staging'), x.get('seed')) for x in runs}
        == {(sync, seed) for sync in (0, 1) for seed in (108041, 108042)}
        and all(x.get('historical', {}).get('status') == 'TEST_PASS'
                and x.get('pair', {}).get('status') == 'TEST_PASS'
                and x.get('historical', {}).get('case_rows') == 40
                and x.get('historical', {}).get('packets') == 20
                and x.get('pair', {}).get('public_cycle_edges', 0) > 0 for x in runs))
    capture_checks = (len(capture_runs) == 2 and all(x.get('status') == 'TEST_PASS'
        and x.get('seed') in (108041, 108042) and x.get('actual_raw_packets') == 4
        and x.get('positive_prepared_cases') == 1728 and x.get('high32_metadata_owners') == 128
        and x.get('capture_edge_abort_restarts') == 3 and x.get('held_metadata_edges') == 2244
        for x in capture_runs))
    continuation = report.get('bounded_compile_continuation', {})
    prior_path = ROOT / continuation.get('prior_receipt', '') if continuation.get('prior_receipt') else None
    prior = json.loads(prior_path.read_text()) if prior_path and prior_path.is_file() else {}
    prior_hash_checks = _audit_focus_hashes(prior_path.parent, prior) if prior else {'artifacts': {}, 'sources': {}}
    prior_expected_timeout = (prior.get('status') == 'FAIL' and prior.get('actual_RTL_run') is False
        and prior.get('commands', [])[-1].get('exit_code') == 124
        and prior.get('commands', [])[-1].get('timeout_seconds') == 300
        and bool(prior.get('artifacts_sha256')) and all(prior_hash_checks['artifacts'].values()))
    prior_source_equal = all(report.get('source_sha256', {}).get(rel) == digest
        for rel, digest in prior.get('source_sha256', {}).items()
        if rel != 'scripts/cu66-v107/plan_prefix/qualify.py')
    generated_before = continuation.get('generated_before', {})
    continuation_ok = (bool(prior_path and prior_path.is_file())
        and continuation.get('prior_receipt_sha256') == sha256(prior_path)
        and continuation.get('prior_timeout_seconds') == 300
        and continuation.get('unchanged_RTL_and_fixture') is True
        and bool(generated_before) and prior_expected_timeout and prior_source_equal
        and bool(prior_hash_checks['sources'])
        and all(x['snapshot'] for x in prior_hash_checks['sources'].values())
        and all(x['current'] for rel, x in prior_hash_checks['sources'].items()
                if rel != 'scripts/cu66-v107/plan_prefix/qualify.py'))
    prior_attempts = []
    attempts_dir = area / 'attempts'
    for attempt_dir in sorted(p for p in attempts_dir.glob('*') if p.is_dir()) if attempts_dir.exists() else []:
        result_path = attempt_dir / 'results.json'
        if not result_path.is_file():
            prior_attempts.append({'path': str(attempt_dir.relative_to(ROOT)), 'status': 'PENDING'})
            continue
        prior_report = json.loads(result_path.read_text())
        ph = _audit_focus_hashes(attempt_dir, prior_report)
        last = prior_report.get('commands', [])[-1] if prior_report.get('commands') else {}
        if prior_report.get('status') == 'FAIL' and prior_report.get('actual_RTL_run') is False and last.get('exit_code') == 124:
            attempt_status = 'RETAINED_INITIAL_COMPILE_TIMEOUT_NO_RTL'
        elif prior_report.get('status') == 'PASS' and result_path == report_path:
            attempt_status = 'SELECTED_PASS'
        else:
            attempt_status = 'RETAINED_NONPASS'
        prior_attempts.append({'path': str(attempt_dir.relative_to(ROOT)), 'receipt': str(result_path.relative_to(ROOT)),
            'status': attempt_status, 'receipt_sha256': sha256(result_path),
            'artifact_hashes_match': bool(ph['artifacts']) and all(ph['artifacts'].values()),
            'source_snapshot_and_current_hashes_match': bool(ph['sources']) and all(x['snapshot'] and x['current'] for x in ph['sources'].values()),
            'actual_RTL_run': prior_report.get('actual_RTL_run'), 'terminal_report_status': prior_report.get('status'),
            'last_command_exit_code': last.get('exit_code'), 'last_command_timeout_seconds': last.get('timeout_seconds')})
    selection_ok = bool(report_path and report_path.is_file() and selection.get('status') == 'PASS'
        and report.get('status') == 'PASS' and report.get('actual_RTL_run') is True
        and sha256(report_path) == independent.get('receipt_sha256')
        and independent.get('receipt') == str(report_path.relative_to(ROOT))
        and independent.get('status') == 'PASS_ACTUAL_CAPTURE_OWNERSHIP_AND_ALL_FOUR_BODY_PUBLIC_PAIRS')
    checks = {
        'selected_report_and_independent_audit_hash_bind': selection_ok,
        'all_current_source_and_snapshot_hashes_match': sources_ok,
        'all_selected_artifact_hashes_match': artifacts_ok,
        'math_actual_rtl_pass_and_counts': math.get('status') == 'TEST_PASS'
            and math.get('rows') == 108000 and math.get('edges') == 1296000 and math.get('held_edges') == 432000,
        'positive_capture_runs_and_four_controller_pairs_pass': capture_checks and run_checks,
        'six_stale_epoch_rejections_are_expected_and_separate': len(negative_rows) == 6
            and set(expected_by_pair) == expected_pairs and set(observed_negative) == expected_pairs
            and all(negative_checks.values()),
        'strict_nonnegative_compile_runtime_logs': report.get('strict_warnings') is True
            and all(x.get('exit_code') == 0 or tuple(x.get('negative_pair') or ()) in expected_pairs
                    and x.get('exit_code') == 134 for x in command_outcomes)
            and not normal_log_warnings,
        'initial_compile_timeout_retained_and_bounded_same_build_continuation': continuation_ok,
    }
    pending = any(x['status'] == 'PENDING' for x in prior_attempts)
    return {'status': 'PASS_PREFIX_QUALIFICATION_AUDITED' if all(checks.values()) else
            'PENDING_PREFIX_QUALIFICATION' if pending and not report else 'AUDIT_ERROR',
        'selected_report': report_rel, 'selected_report_sha256': sha256(report_path) if report_path and report_path.is_file() else None,
        'checks': checks, 'negative_rejection_checks': negative_checks,
        'command_outcomes': command_outcomes, 'math': math,
        'capture_runs': capture_runs, 'controller_pairs': runs,
        'compile_attempt_history': prior_attempts,
        'bounded_compile_continuation': {'prior_receipt': continuation.get('prior_receipt'),
            'prior_receipt_sha256': continuation.get('prior_receipt_sha256'), 'generated_before_count': len(generated_before),
            'prior_initial_timeout_verified': prior_expected_timeout, 'unchanged_sources_except_runner': prior_source_equal,
            'same_build_recorded': continuation.get('unchanged_RTL_and_fixture') is True},
        'source_checks': hashes['sources'], 'artifact_checks': hashes['artifacts'],
        'warning_matches': normal_log_warnings,
        'scope': 'Actual prefix-focused RTL/math and four-controller public-cycle qualification; expected stale-epoch subprocess assertion rejections are separately identified. No full pixel canonical, native or timing claim.'}


def audit_count_threshold() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/count-threshold'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    arithmetic_path = area / 'arithmetic-review.json'
    arithmetic = json.loads(arithmetic_path.read_text())
    preparation_path = area / 'preparation.json'
    preparation = json.loads(preparation_path.read_text())
    prep_source_checks = {rel: (ROOT / rel).is_file() and file_hash(rel) == digest
                          for rel, digest in preparation.get('source_sha256', {}).items()}
    achecks = arithmetic.get('checks', {})
    arithmetic_ok = (arithmetic.get('schema') == 'v107-count-threshold-arithmetic-review-v1'
        and arithmetic.get('status') == 'PASS_INTEGER_MODEL_CHECKS'
        and arithmetic.get('scope', '').startswith('Unsigned integer model only;')
        and achecks.get('assertions_failed') == 0
        and achecks.get('random_arithmetic_checks') == 300000
        and achecks.get('random_predicate_checks') == 300000
        and achecks.get('boundary_arithmetic_and_predicate_checks') == 1179645
        and achecks.get('underflowing_bd_minus_1_cases_skipped') == 3
        and achecks.get('constants_M') == {'5': 858993459, '15': 286331153, '43': 99882960})
    preparation_ok = (preparation.get('status') == 'PASS_PREPARATION_MODEL_NOT_RTL'
        and preparation.get('actual_RTL_run') is False
        and preparation.get('full_u17_block_domain_per_divisor') == 131072
        and preparation.get('integer_boundary_predicate_cases') == 1966080
        and preparation.get('random_full_u32_predicate_cases') == 300000
        and bool(prep_source_checks) and all(prep_source_checks.values()))
    attempts = []
    attempts_dir = area / 'attempts'
    for folder in sorted(p for p in attempts_dir.glob('*') if p.is_dir()) if attempts_dir.exists() else []:
        result_path = folder / 'results.json'
        if not result_path.is_file():
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PENDING', 'classification': 'PENDING'})
            continue
        report = json.loads(result_path.read_text())
        hashes = _audit_focus_hashes(folder, report)
        commands = report.get('commands', [])
        last = commands[-1] if commands else {}
        compile_log = folder / 'math-compile.log'
        compile_text = compile_log.read_text(errors='replace') if compile_log.is_file() else ''
        if report.get('status') == 'PASS' and report.get('actual_RTL_run') is True:
            classification = 'SELECTED_PASS'
        elif report.get('actual_RTL_run') is False and last.get('exit_code') == 1 and 'Exiting due to 5 warning(s)' in compile_text:
            classification = 'RETAINED_STRICT_COMPILE_WARNING_FAILURE_NO_RTL'
        elif report.get('status') == 'FAIL' and report.get('actual_RTL_run') is False:
            classification = 'RETAINED_INITIAL_COMPILE_FAILURE_NO_RTL'
        else:
            classification = 'RETAINED_NONPASS'
        expected_rejections = report.get('negative_owner_contract_rejections', [])
        expected_pairs = {(mode, index) for mode in (1, 2) for index in (33, 37, 41)}
        rejection_map = {(int(x.get('mode', -1)), int(x.get('index', -1))): x for x in expected_rejections}
        negative_checks = {}
        for pair in expected_pairs:
            row = rejection_map.get(pair, {})
            log = folder / row.get('log', '')
            text = log.read_text(errors='replace') if log.is_file() else ''
            negative_checks[f'{pair[0]}:{pair[1]}'] = (row.get('status') == 'PASS_EXPECTED_ASSERTION_REJECTION'
                and row.get('capture_enable') is False and row.get('post_rejection_recovery_claim') is False
                and 'EXPECTED_ASSERTION_ARMED' in text and 'capture_enable":false' in text
                and 'Assertion failed' in text and 'stale staging response' in text)
        nonnegative_logs = []
        for log in sorted(folder.glob('*.log')):
            if log.name.startswith('capture-negative-'):
                continue
            nonnegative_logs.extend({'file': log.name, 'line': line.strip()}
                for line in log.read_text(errors='replace').splitlines()
                if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
        cmd_neg_pairs = {}
        for c in commands:
            argv = c.get('argv', [])
            try: pair = (int(argv[-2]), int(argv[-1]))
            except (ValueError, TypeError, IndexError): pair = None
            if pair in expected_pairs:
                cmd_neg_pairs[pair] = c.get('exit_code') == 134 and c.get('stop_reason') in (None, '')
        math_runs = report.get('math_runs', [])
        captures = report.get('capture_runs', [])
        run_pairs = report.get('runs', [])
        focused_checks = (report.get('status') == 'PASS' and report.get('actual_RTL_run') is True
            and report.get('strict_warnings') is True and len(math_runs) == 2
            and [x.get('seed') for x in math_runs] == [109101, 109102]
            and all(x.get('status') == 'TEST_PASS' and x.get('full_u17_boundary_cases') == 1966080
                and x.get('random_u32_cases') == 300000 and x.get('post_capture_edges') == 8 for x in math_runs)
            and len(captures) == 2 and all(x.get('status') == 'TEST_PASS' and x.get('actual_raw_packets') == 7
                and x.get('positive_prepared_cases') == 1728 and x.get('high32_metadata_owners') == 128
                and x.get('capture_edge_abort_restarts') == 3 and x.get('held_metadata_edges') == 2295
                and x.get('commit_abort_retries') == 3 for x in captures)
            and len(run_pairs) == 4 and {(x.get('sync_staging'), x.get('seed')) for x in run_pairs}
                == {(sync, seed) for sync in (0, 1) for seed in (109101, 109102)}
            and all(x.get('pair', {}).get('status') == 'TEST_PASS'
                and x.get('historical', {}).get('status') == 'TEST_PASS' for x in run_pairs)
            and set(rejection_map) == expected_pairs and all(negative_checks.values())
            and set(cmd_neg_pairs) == expected_pairs and all(cmd_neg_pairs.values())
            and all(c.get('exit_code') == 0 for c in commands if not (
                len(c.get('argv', [])) >= 2 and (lambda pair: pair in expected_pairs)(
                    (int(c['argv'][-2]), int(c['argv'][-1])) if c['argv'][-2].isdigit() and c['argv'][-1].isdigit() else (-1,-1))))
            and not nonnegative_logs and bool(hashes['artifacts']) and all(hashes['artifacts'].values())
            and bool(hashes['sources']) and all(x['snapshot'] and x['current'] for x in hashes['sources'].values()))
        attempts.append({'path': str(folder.relative_to(ROOT)), 'receipt': str(result_path.relative_to(ROOT)),
            'receipt_sha256': sha256(result_path), 'classification': classification,
            'status': 'PASS' if focused_checks else 'TERMINAL_FAILURE_RETAINED',
            'actual_RTL_run': report.get('actual_RTL_run'), 'terminal_report_status': report.get('status'),
            'last_command_exit_code': last.get('exit_code'), 'strict_compile_warning_seen': 'Exiting due to 5 warning(s)' in compile_text,
            'artifact_hashes_match': bool(hashes['artifacts']) and all(hashes['artifacts'].values()),
            'source_snapshot_and_current_hashes_match': bool(hashes['sources']) and all(x['snapshot'] and x['current'] for x in hashes['sources'].values()),
            'math_runs': math_runs, 'capture_runs': captures, 'expected_negative_checks': negative_checks,
            'warning_matches': nonnegative_logs})
    selected = selection.get('selected_report')
    selected_path = ROOT / selected if selected else None
    selected_report = json.loads(selected_path.read_text()) if selected_path and selected_path.is_file() else {}
    selected_row = next((x for x in attempts if x.get('receipt') == selected), None)
    selected_hash_ok = bool(selected_path and selected_path.is_file()
        and selection.get('selected_report_sha256') == sha256(selected_path)
        and selected_row and selected_row.get('status') == 'PASS'
        and selection.get('status') == 'PASS' and selected_report.get('status') == 'PASS')
    current_incomplete = any(x['status'] == 'PENDING' for x in attempts)
    native_unit_record = audit_count_threshold_native_unit()
    checks = {'arithmetic_model_and_full_u17_preparation_pass': arithmetic_ok and preparation_ok,
        'selected_actual_rtl_attempt_and_hashes_pass': selected_hash_ok,
        'retained_compile_failures_are_classified_not_counted_as_rtl_pass': all(
            x['classification'] == 'RETAINED_STRICT_COMPILE_WARNING_FAILURE_NO_RTL'
            for x in attempts if x['classification'].startswith('RETAINED_'))}
    return {'status': 'PASS_COUNT_THRESHOLD_QUALIFICATION_AUDITED' if all(checks.values()) and not current_incomplete
            else 'PENDING_COUNT_THRESHOLD_QUALIFICATION' if current_incomplete or not selected_hash_ok and selection.get('status') != 'PASS'
            else 'AUDIT_ERROR',
        'selected_report': selected, 'selected_report_sha256': sha256(selected_path) if selected_path and selected_path.is_file() else None,
        'checks': checks, 'arithmetic_review': {'path': str(arithmetic_path.relative_to(ROOT)),
            'sha256': sha256(arithmetic_path), 'status': arithmetic.get('status'), 'checks': achecks,
            'scope': arithmetic.get('scope')},
        'preparation': {'path': str(preparation_path.relative_to(ROOT)), 'status': preparation.get('status'),
            'actual_RTL_run': preparation.get('actual_RTL_run'), 'source_checks': prep_source_checks,
            'scope': preparation.get('limits')},
        'attempts': attempts, 'native_unit': native_unit_record,
        'scope': 'Unsigned integer model, count-threshold focused RTL qualification and retained compiler-attempt history. Full integration and native timing are separate gates.'}


def audit_count_threshold_native_unit() -> dict:
    """Audit the extracted arithmetic mapping without treating it as decoder timing."""
    area = ROOT / 'experiments/python-gamebub-v107/count-threshold/native-unit'
    selection_path = area / 'results.json'
    index_path = area / 'evidence-index.json'
    audit_path = area / 'audit.json'
    attribution_path = area / 'connectivity-attribution.json'
    if not selection_path.is_file():
        return {'status': 'PENDING_COUNT_THRESHOLD_NATIVE_UNIT', 'checks': {'selection_present': False},
            'scope': 'No extracted arithmetic unit receipt is selected yet.'}
    selection = json.loads(selection_path.read_text())
    receipt_rel = selection.get('selected_receipt')
    receipt_path = ROOT / receipt_rel if receipt_rel else None
    index = json.loads(index_path.read_text()) if index_path.is_file() else {}
    audit = json.loads(audit_path.read_text()) if audit_path.is_file() else {}
    attribution = json.loads(attribution_path.read_text()) if attribution_path.is_file() else {}
    if not receipt_path or not receipt_path.is_file():
        return {'status': 'PENDING_COUNT_THRESHOLD_NATIVE_UNIT', 'selection': selection,
            'checks': {'selected_receipt_present': False},
            'scope': 'Selected extraction receipt is not yet retained.'}
    receipt = json.loads(receipt_path.read_text())
    folder = receipt_path.parent
    metrics = receipt.get('metrics', {})
    artifacts = receipt.get('artifacts', {})
    source_hashes = receipt.get('source_sha256', {})
    retained = receipt.get('retained_sha256', {})
    retained_results = {rel: folder.joinpath(rel).is_file() and sha256(folder / rel) == digest
                        for rel, digest in retained.items()}
    portable_index = index.get('portable_files', {})
    portable_results = {}
    for indexed_rel, digest in portable_index.items():
        # The evidence index keys are rooted at the unit output folder and carry
        # the attempt timestamp as their first path component.
        rel = indexed_rel.split('/', 1)[1] if '/' in indexed_rel else indexed_rel
        fp = folder / rel
        artifact_key = rel.removeprefix('reports/')
        artifact = artifacts.get(artifact_key, {}) if rel.startswith('reports/') else {}
        portable_results[indexed_rel] = (fp.is_file() and sha256(fp) == digest
            and (not artifact or fp.stat().st_size == artifact.get('bytes')))
    source_results = {}
    for rel, digest in source_hashes.items():
        snapshot = folder / 'sources' / rel
        source_results[rel] = {'snapshot_matches': snapshot.is_file() and sha256(snapshot) == digest,
                               'current_matches': (ROOT / rel).is_file() and sha256(ROOT / rel) == digest}
    try:
        settings = (folder / 'reports/settings.tsv').read_text()
        clocks = (folder / 'reports/clocks.rpt').read_text()
        check_timing = (folder / 'reports/check-timing.rpt').read_text()
        timing = (folder / 'reports/timing.rpt').read_text()
        dsp_rows = (folder / 'reports/dsp-registers.tsv').read_text().splitlines()
        srl_rows = (folder / 'reports/srls.tsv').read_text().splitlines()[1:]
    except OSError:
        settings = clocks = check_timing = timing = ''
        dsp_rows = []
        srl_rows = []
    dsp_configs = []
    if dsp_rows:
        header = dsp_rows[0].split('\t')
        indexes = {name: header.index(name) for name in ('primitive', 'AREG', 'BREG', 'MREG', 'PREG')}
        for line in dsp_rows[1:]:
            fields = line.split('\t')
            if len(fields) >= len(header) and fields[indexes['primitive']] == 'DSP48E1':
                dsp_configs.append(tuple(int(fields[indexes[name]]) for name in ('AREG', 'BREG', 'MREG', 'PREG')))
    settings_ok = ('part\txc7a100tcsg324-1' in settings and 'mode\tout_of_context' in settings
                   and 'directive\tDefault' in settings and 'clock_period_ns\t10.000' in settings)
    timing_match = re.search(r'^\s*Setup\s*:\s+(\d+)\s+Failing Endpoints,\s+Worst Slack\s+(-?\d+\.\d+)ns', timing, re.M)
    hold_match = re.search(r'^\s*Hold\s*:\s+(\d+)\s+Failing Endpoints,\s+Worst Slack\s+(-?\d+\.\d+)ns', timing, re.M)
    pulse_match = re.search(r'^\s*(?:Pulse Width|PW)\s*:\s+(\d+)\s+Failing Endpoints,\s+Worst Slack\s+(-?\d+\.\d+)ns', timing, re.M)
    timing_summary = {'setup_failing_endpoints': int(timing_match[1]), 'setup_worst_slack_ns': float(timing_match[2])} if timing_match else {}
    if hold_match:
        timing_summary.update({'hold_failing_endpoints': int(hold_match[1]), 'hold_worst_slack_ns': float(hold_match[2])})
    if pulse_match:
        timing_summary.update({'pulse_failing_endpoints': int(pulse_match[1]), 'pulse_worst_slack_ns': float(pulse_match[2])})
    checks = {
        'selected_receipt_is_hash_bound_terminal_extraction': selection.get('status') == 'PASS_MEASURED_EXTRACTED_UNIT_MAPPING'
            and selection.get('sha256') == sha256(receipt_path)
            and index.get('receipt_sha256') == sha256(receipt_path)
            and receipt.get('status') == 'PASS_MEASURED_EXTRACTED_UNIT_MAPPING'
            and receipt.get('schema') == 'v107-frozen-extracted-threshold-native-unit-v1'
            and receipt.get('exit_code') == 0 and receipt.get('source_unchanged') is True
            and receipt.get('source_unmodified') is True,
        'all_retained_and_portable_artifact_hashes_match': bool(retained_results) and all(retained_results.values())
            and bool(portable_results) and all(portable_results.values())
            and index.get('separate_qualified_files', {}).get('audit.json') == sha256(audit_path)
            and index.get('separate_qualified_files', {}).get('connectivity-attribution.json') == sha256(attribution_path)
            and audit.get('connectivity_attribution_sha256') == sha256(attribution_path),
        'source_snapshot_and_current_sources_match_receipt': bool(source_results)
            and all(x['snapshot_matches'] and x['current_matches'] for x in source_results.values()),
        'device_ooc_default_and_synthetic_10ns_constraints_are_reported': settings_ok
            and 'threshold_unit_clk  10.000' in clocks
            and 'checking no_clock (0)' in check_timing
            and 'checking unconstrained_internal_endpoints (0)' in check_timing,
        'timing_is_synthesis_only_and_not_routed': bool(timing_match) and bool(hold_match) and bool(pulse_match)
            and 'Design State : Synthesized' in timing and receipt.get('part') == 'xc7a100tcsg324-1'
            and receipt.get('synthetic_clock_ns') == 10,
        'connectivity_overlay_corrects_seven_reset_mask_false_data_ff': (
            attribution.get('status') == 'PASS_CONNECTIVITY_QUALIFIED_RESET_MASK_ATTRIBUTION'
            and attribution.get('raw_receipt_sha256') == sha256(receipt_path)
            and len(attribution.get('raw_name_heuristic_misclassified_FFs', [])) == 7
            and metrics.get('data_FFs') == 476
            and attribution.get('qualified_data_FFs') == 469
            and attribution.get('qualified_data_reset_GND') == 469
            and attribution.get('qualified_control_FFs') == 16
            and attribution.get('DSP_reset_pins_grounded') == 160
            and attribution.get('SRL16E') == 124 and attribution.get('all_SRL_CE_VCC') is True
            and attribution.get('all_data_CE_input_port_fanin_empty') is True
            and attribution.get('data_SRLs') == 121),
        'raw_DSP_mapping_is_preserved_and_open_pipelining_is_visible': (
            metrics.get('DSP48E1') == 16 and len(dsp_configs) == 16
            and sum(1 for cfg in dsp_configs if cfg[3] == 1) == 14
            and sum(1 for cfg in dsp_configs if cfg[2] == 0 and cfg[3] == 0) == 2
            and len(metrics.get('DSPs_with_neither_MREG_nor_PREG', [])) == 2
            and audit.get('status') == 'PASS_NATIVE_EVIDENCE_AND_CONTROL_ATTRIBUTION_WITH_OPEN_DSP_PIPELINING'),
    }
    status = 'PASS_COUNT_THRESHOLD_NATIVE_UNIT_AUDITED' if all(checks.values()) else 'AUDIT_ERROR'
    return {'status': status, 'selection': str(selection_path.relative_to(ROOT)),
        'selection_sha256': sha256(selection_path), 'receipt': str(receipt_path.relative_to(ROOT)),
        'receipt_sha256': sha256(receipt_path), 'audit': str(audit_path.relative_to(ROOT)),
        'connectivity_attribution': str(attribution_path.relative_to(ROOT)),
        'checks': checks, 'source_checks': source_results,
        'retained_artifact_checks': retained_results, 'portable_artifact_checks': portable_results,
        'synthesis_only_timing': timing_summary,
        'raw_mapping': {'data_FFs': metrics.get('data_FFs'), 'control_FFs': metrics.get('control_FFs'),
            'DSP48E1': metrics.get('DSP48E1'), 'SRLs': metrics.get('SRLs'),
            'DSP_register_configs': metrics.get('DSP_register_configs'),
            'DSPs_with_neither_MREG_nor_PREG': metrics.get('DSPs_with_neither_MREG_nor_PREG')},
        'qualified_connectivity_overlay': {'data_FFs': attribution.get('qualified_data_FFs'),
            'data_reset_GND': attribution.get('qualified_data_reset_GND'),
            'control_FFs': attribution.get('qualified_control_FFs'),
            'reset_mask_false_data_FFs': len(attribution.get('raw_name_heuristic_misclassified_FFs', [])),
            'SRL16E': attribution.get('SRL16E'), 'DSP_reset_pins_grounded': attribution.get('DSP_reset_pins_grounded')},
        'scope': 'Extracted arithmetic-only unit mapped in a synthetic OOC wrapper with 10 ns constraint. Timing figures are synthesis-only; this is not the whole ingress/decoder, routed timing, board clock, or hardware qualification.'}


def audit_threshold_native_activation(prefix_record: dict, count_record: dict,
                                      threshold_pipeline_record: dict, meta_record: dict) -> dict:
    activation_path = ROOT / 'experiments/python-gamebub-v107/coordination/threshold-native-activation.json'
    policy_path = ROOT / 'experiments/python-gamebub-v107/study-policy.json'
    if not activation_path.is_file():
        return {'status': 'PREPARED_NOT_ACTIVATED', 'activation_record': None,
            'checks': {'activation_record_present': False},
            'scope': 'Threshold native remains unactivated; no vendor run is inferred or authorized by this audit.'}
    activation = json.loads(activation_path.read_text())
    policy = json.loads(policy_path.read_text())
    canonical_path = ROOT / 'experiments/python-gamebub-v107/threshold-pipeline/results.json'
    canonical = json.loads(canonical_path.read_text()) if canonical_path.is_file() else {}
    unit_rel = activation.get('unit_qualification')
    unit_path = ROOT / unit_rel if unit_rel else None
    unit = json.loads(unit_path.read_text()) if unit_path and unit_path.is_file() else {}
    parent_rel = activation.get('parent_receipt')
    parent_path = ROOT / parent_rel if parent_rel else None
    parent = json.loads(parent_path.read_text()) if parent_path and parent_path.is_file() else {}
    setup_rel = activation.get('parent_setup_report')
    setup_path = ROOT / setup_rel if setup_rel else None
    setup_hash = sha256(setup_path) if setup_path and setup_path.is_file() else None
    native_variants = []
    native_root = ROOT / 'experiments/python-gamebub-v107/native'
    for receipt_path in sorted(native_root.glob('*/receipt.json')) if native_root.exists() else []:
        inputs_path = receipt_path.parent / 'inputs.json'
        if inputs_path.is_file():
            native_variants.append((json.loads(inputs_path.read_text()).get('variant'), receipt_path))
    parent_worst = None
    if parent_path:
        parent_attempt = next((p for p in native_root.glob('*/receipt.json') if p == parent_path), None)
        if parent_attempt:
            parent_folder = parent_attempt.parent
            setup_report = parent_folder / 'reports/route-setup-paths.rpt'
            parent_worst = setup_report.is_file() and setup_report == setup_path
    meta_native = next((p for v, p in native_variants if v == 'meta'), None)
    parent_route_summary = {}
    if meta_native:
        meta_folder = meta_native.parent
        summary_path = meta_folder / 'reports/route-timing-summary.rpt'
        # The retained parent receipt's structured run fields are the portable source for metrics.
        meta_receipt = json.loads(meta_native.read_text())
        parent_route_summary = meta_receipt.get('route_summary', {})
    checks = {
        'activation_schema_and_explicit_eighth_source_limit': activation.get('schema') == 'v107-eighth-source-activation-v1'
            and activation.get('source_limit') == 8 and policy.get('threshold_native_activation') == activation
            and policy.get('max_heavy_jobs') == 2 and policy.get('max_native_seconds') == 3600,
        'current_count_threshold_canonical_pass_is_hash_bound': (
            threshold_pipeline_record.get('status') == 'PASS'
            and activation.get('canonical_qualification') == str(canonical_path.relative_to(ROOT))
            and activation.get('canonical_sha256') == sha256(canonical_path)
            and canonical.get('status') == 'PASS_EXACT_THRESHOLD_CANONICAL' and canonical.get('actual_RTL_run') is True),
        'prefix_and_count_threshold_actual_proofs_pass': prefix_record.get('status') == 'PASS_PREFIX_QUALIFICATION_AUDITED'
            and count_record.get('status') == 'PASS_COUNT_THRESHOLD_QUALIFICATION_AUDITED',
        'meta_focused_and_canonical_evidence_in_scope': meta_record.get('status') == 'PASS_META_FLAGS_UNIT_AUDITED'
            and meta_record.get('full_pipeline', {}).get('status') == 'PASS',
        'unit_receipt_path_and_hash_bind': bool(unit_path and unit_path.is_file())
            and activation.get('unit_sha256') == sha256(unit_path)
            and unit_path == ROOT / count_record.get('native_unit', {}).get('receipt', '')
            and count_record.get('native_unit', {}).get('status') == 'PASS_COUNT_THRESHOLD_NATIVE_UNIT_AUDITED'
            and unit.get('status') == 'PASS_MEASURED_EXTRACTED_UNIT_MAPPING' and unit.get('exit_code') == 0,
        'measured_META_parent_receipt_and_setup_report_bind': bool(parent_path and parent_path.is_file())
            and parent.get('status') == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
            and activation.get('parent_receipt_sha256') == sha256(parent_path)
            and parent_worst is True and activation.get('parent_setup_report_sha256') == setup_hash
            and meta_native == parent_path,
        'decision_timestamp_and_no_hardware_contact': activation.get('decision_utc') is not None
            and activation.get('hardware_contact') is False,
    }
    return {'status': 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'activation_record': str(activation_path.relative_to(ROOT)), 'activation_sha256': sha256(activation_path),
        'source_limit': activation.get('source_limit'),
        'unit_qualification': unit_rel, 'unit_sha256': sha256(unit_path) if unit_path and unit_path.is_file() else None,
        'parent_receipt': parent_rel, 'parent_receipt_sha256': sha256(parent_path) if parent_path and parent_path.is_file() else None,
        'parent_setup_report': setup_rel, 'parent_setup_report_sha256': setup_hash,
        'checks': checks,
        'scope': 'Explicit eighth native trial activation gate. Requires current focused/canonical proofs, unit receipt, exact measured META parent route provenance, source limit 8, and matching study policy.'}


def audit_threshold_runtime_activation(threshold_activation_record: dict) -> dict:
    """Independent preflight for one strategy-only attempt on the same source set."""
    activation_path = ROOT / 'experiments/python-gamebub-v107/coordination/threshold-runtime-activation.json'
    policy_path = ROOT / 'experiments/python-gamebub-v107/study-policy.json'
    if not activation_path.is_file():
        return {'status': 'PREPARED_NOT_ACTIVATED', 'activation_record': None,
                'checks': {'activation_record_present': False},
                'scope': 'No alternate threshold strategy is activated.'}
    activation = json.loads(activation_path.read_text())
    if activation.get('enabled') is not True:
        return {'status': 'PREPARED_NOT_ACTIVATED', 'activation_record': str(activation_path.relative_to(ROOT)),
                'activation_sha256': sha256(activation_path), 'checks': {'runtime_strategy_enabled': False},
                'scope': 'Runtime strategy is prepared but disabled; no alternate strategy attempt is authorized.'}
    policy = json.loads(policy_path.read_text())
    preflight_rel = activation.get('prepared_preflight')
    preflight_path = ROOT / preflight_rel if preflight_rel else None
    preflight = json.loads(preflight_path.read_text()) if preflight_path and preflight_path.is_file() else {}
    default_inputs_path = ROOT / activation.get('default_inputs', '')
    default_inputs = json.loads(default_inputs_path.read_text()) if default_inputs_path.is_file() else {}
    canonical_path = ROOT / activation.get('canonical_qualification', '')
    canonical = json.loads(canonical_path.read_text()) if canonical_path.is_file() else {}
    observation_path = ROOT / activation.get('observation_record', '')
    observation = json.loads(observation_path.read_text()) if observation_path.is_file() else {}
    observation_folder = observation_path.parent
    copy_results = {}
    for copy_key, hash_key in (
        ('default_inputs_snapshot_path', 'default_inputs_snapshot_sha256'),
        ('default_receipt_snapshot_path', 'default_receipt_snapshot_sha256'),
        ('default_log_prefix_path', 'default_log_prefix_sha256'),
        ('default_memory_snapshot_path', 'default_memory_snapshot_sha256'),
    ):
        rel = observation.get(copy_key)
        expected = observation.get(hash_key)
        fp = ROOT / rel if rel else None
        copy_results[copy_key] = bool(fp and fp.is_file() and expected == sha256(fp))
    snap_inputs_path = ROOT / observation.get('default_inputs_snapshot_path', '')
    snap_receipt_path = ROOT / observation.get('default_receipt_snapshot_path', '')
    snap_log_path = ROOT / observation.get('default_log_prefix_path', '')
    snap_memory_path = ROOT / observation.get('default_memory_snapshot_path', '')
    snapshot_inputs = json.loads(snap_inputs_path.read_text()) if snap_inputs_path.is_file() else {}
    snapshot_receipt = json.loads(snap_receipt_path.read_text()) if snap_receipt_path.is_file() else {}
    memory_rows = []
    if snap_memory_path.is_file():
        memory_rows = [json.loads(line) for line in snap_memory_path.read_text().splitlines() if line.strip()]
    preflight_folder = preflight_path.parent if preflight_path else ROOT
    default_run_path = ROOT / preflight.get('flow_before', '')
    runtime_run_path = ROOT / preflight.get('flow_after', '')
    diff_path = preflight_folder / 'flow.diff'
    default_run = default_run_path.read_text() if default_run_path.is_file() else ''
    runtime_run = runtime_run_path.read_text() if runtime_run_path.is_file() else ''
    expected_default_synth = 'synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default'
    expected_runtime_synth = expected_default_synth.removesuffix('Default') + 'RuntimeOptimized'
    one_line_diff = (default_run.count(expected_default_synth) == 1
        and runtime_run == default_run.replace(expected_default_synth, expected_runtime_synth, 1)
        and preflight.get('exact_one_line_flow_diff') == ''.join(difflib.unified_diff(
            default_run.splitlines(True), runtime_run.splitlines(True),
            fromfile='Default/run.tcl', tofile='RuntimeOptimized/run.tcl'))
        and diff_path.is_file() and diff_path.read_text() == preflight.get('exact_one_line_flow_diff'))
    runtime_flow_root = ROOT / 'fpga/experiments/cu66-v107-threshold-runtime-flow'
    runtime_xdc_path = runtime_flow_root / 'component.xdc'
    runtime_xdc = runtime_xdc_path.read_text() if runtime_xdc_path.is_file() else ''
    frozen_flow_checks = {}
    for name, digest in preflight.get('preserved_flow_sha256', {}).items():
        fp = runtime_flow_root / name
        frozen_flow_checks[name] = fp.is_file() and sha256(fp) == digest
    default_folder = ROOT / observation.get('default_attempt_path', '')
    default_recipe = default_folder / 'recipe-snapshot'
    default_recipe_hashes = {name: sha256(default_recipe / name) if (default_recipe / name).is_file() else None
        for name in ('run.tcl', 'report.tcl', 'component.xdc')}
    prepared_recipe_checks = {
        'run.tcl': one_line_diff and preflight.get('prepared_recipe_sha256', {}).get('run.tcl') == sha256(runtime_run_path) if runtime_run_path.is_file() else False,
        'report.tcl': preflight.get('prepared_recipe_sha256', {}).get('report.tcl') == preflight.get('preserved_flow_sha256', {}).get('report.tcl'),
        'component.xdc': preflight.get('prepared_recipe_sha256', {}).get('component.xdc') == preflight.get('preserved_flow_sha256', {}).get('component.xdc'),
        'inputs.tcl_digest_well_formed': bool(re.fullmatch(r'[0-9a-f]{64}', preflight.get('prepared_recipe_sha256', {}).get('inputs.tcl', ''))),
    }
    source_map = activation.get('source_sha256', {})
    origins = activation.get('source_origins', {})
    canonical_source_map = {v.get('path'): v.get('sha256') for v in origins.values()}
    current_origin_hashes = {alias: (ROOT / row.get('path', '')).is_file()
        and sha256(ROOT / row['path']) == row.get('sha256') for alias, row in origins.items()}
    default_source_snapshots = {alias: (default_folder / 'source-snapshot' / alias).is_file()
        and sha256(default_folder / 'source-snapshot' / alias) == digest for alias, digest in source_map.items()}
    expected_prep_dir = preflight_folder
    prepared_inputs_copy = expected_prep_dir / 'prepared-inputs.json'
    default_inputs_copy = expected_prep_dir / 'default-inputs.json'
    prepared_inputs = json.loads(prepared_inputs_copy.read_text()) if prepared_inputs_copy.is_file() else {}
    copied_default_inputs = json.loads(default_inputs_copy.read_text()) if default_inputs_copy.is_file() else {}
    threshold_base_ok = threshold_activation_record.get('status') == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED'
    checks = {
        'enabled_policy_mirror_and_one_attempt_limits': activation.get('schema') == 'v107-threshold-runtime-activation-v1'
            and activation.get('enabled') is True and policy.get('threshold_runtime_activation') == activation
            and activation.get('variant') == 'threshold-runtime'
            and (activation.get('source_limit'), activation.get('native_attempt_limit'), activation.get('alternate_strategy_limit')) == (8, 9, 1)
            and (activation.get('native_attempt_ordinal'), activation.get('source_set_ordinal')) == (9, 8)
            and activation.get('heavy_slot_granted') is True and activation.get('hardware_contact') is False,
        'strategy_and_resources_are_fixed': activation.get('strategy') == {'synth': 'RuntimeOptimized', 'opt': 'Default', 'place': 'Default', 'route': 'Default'}
            and activation.get('clock_period_ns') == 10 and activation.get('max_threads') == 2
            and activation.get('memory_limit_bytes') == 8589934592 and activation.get('cpus') == 2
            and activation.get('timeout_seconds') == 3600,
        'preflight_hash_and_current_canonical_bind': bool(preflight_path and preflight_path.is_file())
            and activation.get('prepared_preflight_sha256') == sha256(preflight_path)
            and preflight.get('schema') == 'v107-threshold-runtime-preflight-v1'
            and preflight.get('status') == 'PREPARED_NOT_ACTIVATED' and preflight.get('actual_native_run') is False
            and preflight.get('canonical_qualification') == activation.get('canonical_qualification')
            and activation.get('canonical_sha256') == sha256(canonical_path)
            and canonical.get('status') == 'PASS_EXACT_THRESHOLD_CANONICAL'
            and canonical.get('actual_RTL_run') is True and threshold_base_ok,
        'source8_same18_files_and_current_origins': len(source_map) == len(origins) == 18
            and sum(x.endswith(('.sv', '.v')) for x in source_map) == 17
            and source_map == default_inputs.get('source_sha256') == preflight.get('source_sha256')
            and origins == default_inputs.get('source_origins') == preflight.get('source_origins')
            and source_map == prepared_inputs.get('source_sha256')
            and origins == prepared_inputs.get('source_origins')
            and canonical_source_map == {p: canonical.get('source_sha256', {}).get(p) for p in canonical_source_map}
            and bool(current_origin_hashes) and all(current_origin_hashes.values())
            and bool(default_source_snapshots) and all(default_source_snapshots.values())
            and preflight.get('source_maps_identical_to_Default8') is True
            and preflight.get('source_set_ordinal') == 8 and preflight.get('new_RTL_sources') == 0,
        'immutable_Default8_inputs_and_prepared_copy_match': default_inputs_path.is_file()
            and activation.get('default_inputs_sha256') == sha256(default_inputs_path)
            and observation.get('default_inputs_path') == activation.get('default_inputs')
            and observation.get('default_inputs_sha256') == activation.get('default_inputs_sha256')
            and all(copy_results.values()) and copied_default_inputs == default_inputs == snapshot_inputs
            and prepared_inputs_copy.is_file() and preflight.get('prepared_inputs_sha256') == sha256(prepared_inputs_copy),
        'observation_is_immutable_running_NoDCP_snapshot': observation.get('schema') == 'v107-runtime-strategy-observation-v1'
            and observation.get('default_status_at_capture') == 'RUNNING'
            and observation.get('default_attempt_path') == str(default_folder.relative_to(ROOT))
            and snapshot_receipt.get('status') == 'RUNNING'
            and observation.get('route_checkpoint_present_at_capture') is False
            and observation.get('synthesis_checkpoint_present_at_capture') is False
            and snap_log_path.is_file() and snap_log_path.stat().st_size == observation.get('default_log_prefix_bytes')
            and len(memory_rows) > 0
            and memory_rows[-1].get('elapsed_seconds') == observation.get('last_resource_sample', {}).get('elapsed_seconds')
            and observation.get('observed_elapsed_seconds') == observation.get('last_resource_sample', {}).get('elapsed_seconds'),
        'only_synthesis_directive_changes_and_other_flow_recipe_hashes_match': one_line_diff
            and default_recipe_hashes.get('run.tcl') == preflight.get('flow_before_sha256')
            and default_recipe_hashes.get('report.tcl') == preflight.get('preserved_flow_sha256', {}).get('report.tcl')
            and default_recipe_hashes.get('component.xdc') == preflight.get('preserved_flow_sha256', {}).get('component.xdc')
            and all(frozen_flow_checks.values()) and all(prepared_recipe_checks.values())
            and preflight.get('new_clock_or_exception_edits') == 0
            and 'synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive RuntimeOptimized' in runtime_run
            and all(f'{cmd}_design -directive Default' in runtime_run for cmd in ('opt', 'place', 'route'))
            and 'create_clock -name component_clk -period 10.000 [get_ports clk]' in runtime_xdc
            and not re.search(r'(?m)^\s*set_(?:input_delay|output_delay|false_path|multicycle_path|clock_groups)\b', runtime_xdc),
        'runtime_activation_decision_is_explicit': bool(activation.get('decision_utc'))
            and bool(activation.get('reason')) and bool(observation.get('captured_at_utc')),
    }
    return {'status': 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
        'activation_record': str(activation_path.relative_to(ROOT)), 'activation_sha256': sha256(activation_path),
        'prepared_preflight': preflight_rel, 'prepared_preflight_sha256': sha256(preflight_path) if preflight_path and preflight_path.is_file() else None,
        'observation_record': str(observation_path.relative_to(ROOT)) if observation_path.is_file() else None,
        'observation_sha256': sha256(observation_path) if observation_path.is_file() else None,
        'default_inputs': activation.get('default_inputs'), 'default_inputs_sha256': activation.get('default_inputs_sha256'),
        'source_file_count': len(source_map), 'rtl_file_count': sum(x.endswith(('.sv', '.v')) for x in source_map),
        'limits': {'source_limit': activation.get('source_limit'), 'native_attempt_limit': activation.get('native_attempt_limit'),
                   'alternate_strategy_limit': activation.get('alternate_strategy_limit')},
        'checks': checks, 'observation_copy_checks': copy_results, 'default_recipe_hashes': default_recipe_hashes,
        'prepared_recipe_checks': prepared_recipe_checks, 'source_origin_checks': current_origin_hashes,
        'default_source_snapshot_checks': default_source_snapshots,
        'scope': 'One strategy-only native attempt on the same qualified 18-file source set. RuntimeOptimized synthesis with Default opt/place/route and inherited 10 ns OOC constraints. Preflight evidence does not imply a QoR result.'}


def audit_tables_pipeline(area_name: str = 'tables-pipeline', pass_status: str = 'PASS_EXACT_TABLES_CANONICAL',
                          pending_status: str = 'PENDING_TABLES_FULL_EVIDENCE', label: str = 'TABLES') -> dict:
    area = ROOT / f'experiments/python-gamebub-v107/{area_name}'
    attempts = []
    dirs = sorted(p for p in (area / 'attempts').glob('*') if p.is_dir()) if (area / 'attempts').exists() else []
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text()) if selection_path.is_file() else None
    for folder in dirs:
        result_path = folder / 'receipt.json'
        if not result_path.is_file():
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PENDING'})
            continue
        report = json.loads(result_path.read_text())
        artifacts = {rel: (folder / rel).is_file() and sha256(folder / rel) == digest
                     for rel, digest in report.get('artifact_sha256', {}).items()}
        source_rows = {}
        for rel, digest in report.get('source_sha256', {}).items():
            snap = folder / 'sources' / rel
            live = ROOT / rel
            source_rows[rel] = {'snapshot_matches': snap.is_file() and sha256(snap) == digest,
                                'current_matches': live.is_file() and sha256(live) == digest}
        baseline_path = ROOT / report.get('baseline_reference', {}).get('path', '')
        baseline = json.loads(baseline_path.read_text()) if baseline_path.is_file() else {}
        baseline_folder = baseline_path.parent
        run_results = []
        warnings = []
        for run in report.get('runs', []):
            seed = run.get('seed')
            old_stdout = baseline_folder / f'candidate-{seed}-simulation.jsonl'
            new_stdout = folder / f'candidate-{seed}-simulation.jsonl'
            streams = {}
            old_run = next((x for x in baseline.get('runs', []) if x.get('seed') == seed), {})
            for key in ('events', 'canonical_actual'):
                item = run.get('artifacts', {}).get(key, {})
                ref = item.get('reference', {})
                old_item = old_run.get('variants', {}).get('candidate', {}).get(key, {})
                target = folder / item.get('path', '')
                reference = ROOT / ref.get('path', '')
                try:
                    raw = gzip.decompress(target.read_bytes())
                    raw_ref = gzip.decompress(reference.read_bytes())
                    streams[key] = (raw == raw_ref and hashlib.sha256(raw).hexdigest() == item.get('raw_sha256')
                        and sha256(target) == item.get('sha256') == ref.get('sha256')
                        and ref.get('path') == str((baseline_folder / old_item.get('path', '')).relative_to(ROOT))
                        and ref.get('sha256') == old_item.get('sha256'))
                except (OSError, EOFError):
                    streams[key] = False
            exact_stdout = new_stdout.is_file() and old_stdout.is_file() and sha256(new_stdout) == sha256(old_stdout)
            verdict = run.get('verdict', {})
            passed = (verdict.get('status') == 'TEST_PASS' and verdict.get('cases') == 22
                and verdict.get('directed_checks') == 21 and run.get('exact_stdout_events_cycles_and_canonical') is True
                and exact_stdout and all(streams.values()))
            run_results.append({'seed': seed, 'status': verdict.get('status'), 'case_profiles': verdict.get('cases'),
                                'directed_checks': verdict.get('directed_checks'), 'exact_stdout': exact_stdout,
                                'streams': streams, 'pass': passed})
        for name in ('compile.log', 'binary.log', *(f'candidate-{s}-simulation.jsonl' for s in report.get('seeds', []))):
            fp = folder / name
            if fp.is_file():
                warnings.extend({'file': name, 'line': line.strip()} for line in fp.read_text(errors='replace').splitlines()
                    if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
        commands_ok = all(c.get('exit_code') == 0 for c in report.get('commands', [])) and bool(report.get('commands'))
        passed = (report.get('status') == pass_status and report.get('actual_RTL_run') is True
            and report.get('baseline_recompiled_or_rerun') is False and report.get('baseline_reused_actual_RTL') is True
            and report.get('newly_executed_candidate_case_profiles') == 44
            and report.get('newly_executed_candidate_directed_checks') == 42
            and report.get('lossless_compile_packaging', {}).get('concatenation_equal') is True
            and report.get('lossless_compile_packaging', {}).get('filename_warning_disabled') is False
            and len(run_results) == 2 and all(x['pass'] for x in run_results)
            and all(x['snapshot_matches'] and x['current_matches'] for x in source_rows.values())
            and bool(artifacts) and all(artifacts.values()) and commands_ok and not warnings)
        attempts.append({'path': str(folder.relative_to(ROOT)), 'receipt': str(result_path.relative_to(ROOT)),
                         'status': 'PASS' if passed else 'TERMINAL_FAILURE_RETAINED',
                         'results_sha256': sha256(result_path), 'source_checks': source_rows,
                         'artifact_checks': artifacts, 'runs': run_results, 'commands_ok': commands_ok,
                         'warning_matches': warnings, 'terminal_status': report.get('status'),
                         'actual_RTL_run': report.get('actual_RTL_run')})
    selected = selection.get('selected_receipt') if selection else None
    chosen = next((x for x in attempts if x.get('receipt') == selected), None)
    pointer_ok = bool(selection and chosen and chosen['status'] == 'PASS'
        and selection.get('status') == pass_status)
    pending = not selection or any(x['status'] == 'PENDING' for x in attempts)
    status = pending_status if pending else 'PASS' if pointer_ok else 'AUDIT_ERROR' if selection and selection.get('status') == pass_status else 'TERMINAL_FAILURE_RETAINED'
    return {'status': status, 'selection': str(selection_path.relative_to(ROOT)) if selection else None,
            'selection_sha256': sha256(selection_path) if selection else None, 'selected_report': selected,
            'selection_points_to_audited_pass': pointer_ok, 'attempts': attempts,
            'scope': f'Fresh {label} candidate compared byte-for-byte and cycle-for-cycle against retained actual elastic candidate streams; reused controls are not recounted. No timing claim.'}


def audit_elastic_unit() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/elastic'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    receipt_path = ROOT / selection['selected_receipt']
    receipt = json.loads(receipt_path.read_text())
    audit_path = area / 'audit.json'
    audit = json.loads(audit_path.read_text())
    attempt = receipt_path.parent
    artifact_results = {}
    for rel, digest in receipt['artifact_sha256'].items():
        fp = attempt / rel
        actual = sha256(fp) if fp.is_file() else None
        artifact_results[rel] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
    source_results = {}
    for rel, digest in receipt['source_sha256'].items():
        live, snapshot = ROOT / rel, attempt / 'sources' / rel
        live_hash = sha256(live) if live.is_file() else None
        snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
        source_results[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                               'matches': live_hash == digest and snapshot_hash == digest}
    logs = [attempt / f"seed-{r['seed']}.log" for r in receipt['runs']]
    runtime_matches = []
    for fp in logs:
        text = fp.read_text(errors='replace')
        runtime_matches.extend([{'file': str(fp.relative_to(ROOT)), 'line': line.strip()} for line in text.splitlines()
                                if re.search(r'(?i)(?:warning|TEST_FAIL|assertion failed|waiver)', line)])
    checks = {
        'selection_receipt_and_audit_hashes_match': sha256(receipt_path) == selection['receipt_sha256'] == audit['receipt_sha256'],
        'unit_and_audit_pass': selection['status'] == receipt['status'] == 'PASS_ACTUAL_ELASTIC_UNIT' and audit['status'] == 'PASS_FROZEN_ELASTIC_UNIT_AUDIT',
        'actual_rtl_assertions_enabled': receipt['assertions_disabled_or_downgraded'] is False,
        'warning_suppression_is_false': receipt['warning_suppression'] is False and audit['warning_suppression'] is False,
        'source_and_artifact_hashes_match': all(x['matches'] for x in artifact_results.values()) and all(x['matches'] for x in source_results.values()),
        'three_seed_counts_match': len(receipt['runs']) == 3 and all(x['status'] == 'TEST_PASS' for x in receipt['runs'])
            and receipt['actual_clock_edges'] == 508800
            and sum(x['pushes'] for x in receipt['runs']) == 288502
            and sum(x['pops'] for x in receipt['runs']) == 288460
            and sum(x['discarded'] for x in receipt['runs']) == 42,
        'no_runtime_warning_failure_assertion_or_waiver_text': not runtime_matches,
        'complete_pipeline_not_claimed': audit['complete_pipeline_compile_or_simulation'] is False,
    }
    return {'status': 'PASS_ELASTIC_UNIT_AUDITED' if all(checks.values()) else 'AUDIT_ERROR',
            'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
            'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha256(receipt_path),
            'audit': str(audit_path.relative_to(ROOT)), 'audit_sha256': sha256(audit_path),
            'actual_clock_edges': receipt['actual_clock_edges'], 'seeds': receipt['runs'],
            'pushes': sum(x['pushes'] for x in receipt['runs']), 'pops': sum(x['pops'] for x in receipt['runs']),
            'discarded': sum(x['discarded'] for x in receipt['runs']),
            'artifacts_checked': len(artifact_results), 'sources_checked': len(source_results),
            'artifact_results': artifact_results, 'source_results': source_results,
            'runtime_warning_matches': runtime_matches, 'complete_pipeline_integrated': False,
            'checks': checks, 'scope': receipt['limits'][0] + ' No full pipeline, routed timing, or hardware qualification.'}


def audit_cdc_native() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/cdc-native'
    selection_path = area / 'results.json'
    selection = json.loads(selection_path.read_text())
    selected_path = ROOT / selection['selected_receipt']
    selected = json.loads(selected_path.read_text())
    portable_path = area / 'native-audit.json'
    portable = json.loads(portable_path.read_text())
    attempt_results = []
    for receipt_path in sorted(area.glob('*/receipt.json')):
        receipt = json.loads(receipt_path.read_text())
        folder = receipt_path.parent
        input_path = folder / 'inputs.json'
        inputs = json.loads(input_path.read_text())
        snapshot_hashes = {}
        for name, digest in inputs['snapshot_sha256'].items():
            fp = folder / 'snapshot' / name
            actual = sha256(fp) if fp.is_file() else None
            snapshot_hashes[name] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
        retained_hashes = {rel: {'expected': digest, 'actual': sha256(folder / rel) if (folder / rel).is_file() else None,
                                'matches': (folder / rel).is_file() and sha256(folder / rel) == digest}
                           for rel, digest in receipt.get('retained_sha256', {}).items()}
        origin_hashes = {}
        for name, source in inputs['source_origins'].items():
            live = ROOT / source['path']
            snap = folder / 'snapshot' / name
            live_hash = sha256(live) if live.is_file() else None
            snapshot_hash = sha256(snap) if snap.is_file() else None
            origin_hashes[name] = {'expected': source['sha256'], 'live': live_hash, 'snapshot': snapshot_hash,
                                   'snapshot_matches': snapshot_hash == source['sha256'],
                                   'current_matches': live_hash == source['sha256']}
        attempt_results.append({'attempt': folder.name, 'status': receipt['status'], 'exit_code': receipt['observed_exit_code'],
            'receipt_sha256': sha256(receipt_path), 'input_manifest_matches': sha256(input_path) == receipt['input_manifest_sha256'],
            'snapshots_match': all(x['matches'] for x in snapshot_hashes.values()),
            'retained_artifacts_match': all(x['matches'] for x in retained_hashes.values()),
            'source_snapshots_match': all(x['snapshot_matches'] for x in origin_hashes.values()),
            'current_sources_match': all(x['current_matches'] for x in origin_hashes.values()),
            'snapshot_results': snapshot_hashes, 'artifact_results': retained_hashes, 'source_results': origin_hashes})
    route = portable['route_timing']
    checks = {
        'selection_receipt_hash_matches': sha256(selected_path) == selection['sha256'] == portable['source_receipt_sha256'],
        'portable_audit_passes_with_open_findings': portable['status'] == 'PASS_EVIDENCE_WITH_OPEN_CDC_AND_RESET_FINDINGS',
        'selected_native_route_review_required': selection['status'] == selected['status'] == 'MAPPED_CDC_UNIT_ROUTE_FINISHED_REVIEW_REQUIRED',
        'all_attempt_hashes_and_snapshots_match': len(attempt_results) == 4 and all(
            all(x[k] for k in ('input_manifest_matches', 'snapshots_match', 'retained_artifacts_match', 'source_snapshots_match')) for x in attempt_results),
        'selected_attempt_sources_match_current_tree': bool(attempt_results) and attempt_results[-1]['current_sources_match'],
        'route_setup_hold_pulse_metrics_are_reported': route['WNS_ns'] == 2.025 and route['WHS_ns'] == 0.097 and route['WPWS_ns'] == 2.0,
        'route_is_legal_and_complete': portable['routed_nets'] == 240 and portable['routing_errors'] == 0,
        'board_qualification_remains_false': selected['actual_board_clock_or_IO_qualified'] is False,
        'no_waivers_added': portable['waivers_added'] is False,
        'open_CDC11_and_CDC6_are_preserved': portable['cdc']['CDC-11']['count'] == 8 and portable['cdc']['CDC-6']['count'] == 10,
    }
    return {'status': 'PASS_CDC_NATIVE_EVIDENCE_WITH_OPEN_FINDINGS' if all(checks.values()) else 'AUDIT_ERROR',
            'selection': str(selection_path.relative_to(ROOT)), 'selection_sha256': sha256(selection_path),
            'receipt': str(selected_path.relative_to(ROOT)), 'receipt_sha256': sha256(selected_path),
            'portable_audit': str(portable_path.relative_to(ROOT)), 'portable_audit_sha256': sha256(portable_path),
            'attempts': attempt_results, 'route_timing': route,
            'gray_bounds': portable['gray_applied_checks'], 'bus_skew': portable['bus_skew'],
            'CDC_findings': portable['cdc'], 'methodology_findings': portable['methodology'],
            'open_findings': portable['open_findings'], 'waivers_added': portable['waivers_added'],
            'checks': checks, 'scope': portable['scope'] + '; synthetic unit clocks only, no board CDC/timing/hardware signoff.'}


def audit_cdc_sync() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/cdc-sync'
    selection_path = area / 'results.json'
    behavioral_audit_path = area / 'audit.json'
    native_area = area / 'native'
    native_selection_path = native_area / 'results.json'
    native_audit_path = native_area / 'native-audit.json'
    selection = json.loads(selection_path.read_text())
    behavioral_audit = json.loads(behavioral_audit_path.read_text())
    native_selection = json.loads(native_selection_path.read_text())
    native_audit = json.loads(native_audit_path.read_text())
    behavior_receipt_path = ROOT / selection['selected_receipt']
    behavior = json.loads(behavior_receipt_path.read_text())
    behavior_attempt = behavior_receipt_path.parent
    behavior_artifacts = {rel: {'expected': digest, 'actual': sha256(behavior_attempt / rel) if (behavior_attempt / rel).is_file() else None,
                                'matches': (behavior_attempt / rel).is_file() and sha256(behavior_attempt / rel) == digest}
                          for rel, digest in behavior['artifacts_sha256'].items()}
    behavior_sources = {}
    for rel, digest in behavior['source_sha256'].items():
        live = ROOT / rel
        snapshot = behavior_attempt / 'sources' / rel
        live_hash = sha256(live) if live.is_file() else None
        snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
        behavior_sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                                 'matches': live_hash == digest and snapshot_hash == digest}
    behavior_logs = []
    for name in ('compile.log', 'version.log', '107001.log', '107002.log', '107003.log'):
        content = (behavior_attempt / name).read_text(errors='replace')
        behavior_logs.extend({'file': name, 'line': line.strip()} for line in content.splitlines()
            if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
    totals = behavioral_audit['totals']
    capacity = behavioral_audit['capacity']
    rate = behavioral_audit['rate']
    checks = {
        'behavioral_selector_receipt_hash_matches': sha256(behavior_receipt_path) == selection['sha256'] == behavioral_audit['behavioral_receipt_sha256'],
        'behavioral_receipt_and_independent_audit_pass': selection['status'] == behavior['status'] == 'PASS_BEHAVIORAL_SYNC_BRAM_CONTROL'
            and behavioral_audit['status'] == 'PASS_BEHAVIOR_CAPACITY_AND_MEASURED_HALF_RATE',
        'behavioral_source_and_artifact_hashes_match': all(x['matches'] for x in behavior_artifacts.values())
            and all(x['matches'] for x in behavior_sources.values()),
        'behavioral_three_seed_capacity_conservation': len(behavioral_audit['seeds']) == 3
            and totals == {'accepted': 45243, 'delivered': 44702, 'reset_discarded': 541}
            and totals['accepted'] == totals['delivered'] + totals['reset_discarded']
            and capacity['all_five_channels_all_three_seeds_reached'] is True
            and capacity['reserved_RAM_slots'] == 8 and capacity['output_slots'] == 1 and capacity['observed_max'] == 9,
        'behavioral_equal_clock_rate_scope_and_no_waivers': len(rate) == 5
            and all(x['accepted'] == x['delivered'] == 10000 and x['accepted_words_per_clock_steady'] == 0.5
                and x['delivered_words_per_clock'] == 0.5 and x['min_latency_equal_test_clocks'] == 6
                and x['max_latency_equal_test_clocks'] == 13 for x in rate)
            and behavioral_audit['waivers_added'] is False and behavioral_audit['board_or_complete_parent_qualified'] is False,
        'behavioral_logs_have_no_warning_failure_or_waiver_text': not behavior_logs,
        'native_selector_receipt_audit_hashes_match': sha256(ROOT / native_selection['selected_receipt']) == native_selection['sha256']
            == native_audit['source_receipt_sha256'] and native_audit['source_receipt'] == native_selection['selected_receipt'],
        'native_review_required_route_complete': native_selection['status'] == 'MAPPED_CDC_UNIT_ROUTE_FINISHED_REVIEW_REQUIRED'
            and native_audit['status'] == 'PASS_TARGETED_REPAIR_WITH_PARENT_TIMING_OPEN',
        'native_input_manifest_snapshot_and_retained_hashes_match': False,
        'native_targeted_route_metrics_and_open_scope': False,
        'native_no_waivers_and_board_unqualified': native_audit['waivers_added'] is False
            and native_audit['RTL_changes_after_behavioral_PASS'] is False
            and native_audit['scope'] == 'Synthetic isolated fabric unit only; not parent timing/CDC/hardware signoff',
    }
    native_receipt_path = ROOT / native_selection['selected_receipt']
    native_receipt = json.loads(native_receipt_path.read_text())
    native_attempt = native_receipt_path.parent
    native_inputs_path = native_attempt / 'inputs.json'
    native_inputs = json.loads(native_inputs_path.read_text())
    native_snapshots = {}
    for name, digest in native_inputs['snapshot_sha256'].items():
        source_origin = native_inputs['source_origins'].get(name)
        origin_actual = file_hash(source_origin['path']) if source_origin else None
        native_snapshots[name] = {'expected': digest,
            'actual': sha256(native_attempt / 'snapshot' / name) if (native_attempt / 'snapshot' / name).is_file() else None,
            'origin': source_origin.get('sha256') if source_origin else None,
            'origin_actual': origin_actual}
    native_retained = {rel: {'expected': digest,
        'actual': sha256(native_attempt / rel) if (native_attempt / rel).is_file() else None,
        'matches': (native_attempt / rel).is_file() and sha256(native_attempt / rel) == digest}
        for rel, digest in native_receipt['retained_sha256'].items()}
    checks['native_input_manifest_snapshot_and_retained_hashes_match'] = (
        sha256(native_inputs_path) == native_receipt['input_manifest_sha256']
        and native_receipt['source_snapshot_unchanged'] is True
        and all(x['actual'] == x['expected'] and (x['origin'] is None or x['expected'] == x['origin'] == x['origin_actual'])
                for x in native_snapshots.values())
        and all(x['matches'] for x in native_retained.values()))
    reports = {name: native_attempt / 'reports' / name for name in native_receipt['artifacts']
               if (native_attempt / 'reports' / name).is_file()}
    timing = native_timing(reports['route-timing-summary.rpt'].read_text(errors='replace'))
    route_status_text = reports['route-status.rpt'].read_text(errors='replace')
    check_text = reports['route-check-timing.rpt'].read_text(errors='replace')
    check_counts = {k: int(v) for k, v in re.findall(r'checking (\w+) \((\d+)\)', check_text)}
    cdc_text = reports['route-cdc.rpt'].read_text(errors='replace')
    cdc_counts = {k: int(v) for k, v in re.findall(r'^(CDC-\d+)\s+(?:Info|Warning|Critical)\s+(\d+)\s', cdc_text, re.M)}
    route_metrics_ok = (timing['WNS_ns'] == 2.078 and timing['WHS_ns'] == 0.027 and timing['WPWS_ns'] == 2.0
        and timing['setup_failing'] == timing['hold_failing'] == timing['pulse_failing'] == 0
        and all(check_counts.get(k) == 0 for k in ('no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops', 'multiple_clock'))
        and check_counts.get('no_input_delay') == check_counts.get('no_output_delay') == 279
        and re.search(r'fully routed nets\.+\s*:\s*568', route_status_text)
        and re.search(r'nets with routing errors\.+\s*:\s*0', route_status_text)
        and cdc_counts == {'CDC-3': 10, 'CDC-6': 10}
        and native_audit['drc_displayed'] == {'CFGBVS-1': 1}
        and native_audit['methodology'] == {'LUTAR-1': 1, 'SYNTH-4': 7, 'SYNTH-6': 7, 'TIMING-18': 558})
    checks['native_targeted_route_metrics_and_open_scope'] = route_metrics_ok
    result = {'status': 'PASS_CDC_SYNC_WITH_PARENT_FINDINGS_OPEN' if all(checks.values()) else 'AUDIT_ERROR',
        'behavioral_audit': str(behavioral_audit_path.relative_to(ROOT)),
        'behavioral_audit_sha256': sha256(behavioral_audit_path), 'behavioral_receipt': str(behavior_receipt_path.relative_to(ROOT)),
        'behavioral_receipt_sha256': sha256(behavior_receipt_path), 'behavioral_artifacts': behavior_artifacts,
        'behavioral_sources': behavior_sources, 'behavioral_warning_matches': behavior_logs,
        'behavioral_totals': totals, 'capacity': capacity, 'rate': rate,
        'native_audit': str(native_audit_path.relative_to(ROOT)), 'native_audit_sha256': sha256(native_audit_path),
        'native_receipt': str(native_receipt_path.relative_to(ROOT)), 'native_receipt_sha256': sha256(native_receipt_path),
        'native_snapshots': native_snapshots, 'native_retained_artifacts': native_retained,
        'route_timing': timing, 'route_check_timing': check_counts, 'route_cdc': cdc_counts,
        'native_routed_nets': native_audit['routed_nets'], 'native_drc': native_audit['drc_displayed'],
        'native_methodology': native_audit['methodology'], 'resources': native_audit['resources'],
        'open_findings': native_audit['open_findings'], 'waivers_added': native_audit['waivers_added'],
        'checks': checks, 'scope': native_audit['scope'] + '; measured rates use equal synthetic clocks, not board clocks or LCD service.'}
    return result


def audit_elastic_seed(folder: Path, run: dict) -> dict:
    seed = run['seed']
    checks = {}
    semantics = []
    try:
        case_path = folder / 'inputs/cases.tsv'
        good_ids = {parts[0] for parts in (line.split() for line in case_path.read_text().splitlines())
                    if len(parts) >= 2 and int(parts[1]) == 0}
        grouped = {}
        for implementation in ('baseline', 'candidate'):
            variant = run['variants'][implementation]
            verdict = variant['verdict']
            checks[implementation + '_verdict'] = (verdict['status'] == 'TEST_PASS' and verdict['seed'] == seed
                and verdict['cases'] == 22 and verdict['directed_checks'] == 21)
            events = variant['events']
            event_path = folder / events['path']
            compressed = event_path.read_bytes()
            raw = gzip.decompress(compressed)
            checks[implementation + '_event_compressed_sha256'] = sha256(event_path) == events['sha256']
            checks[implementation + '_event_raw_sha256'] = hashlib.sha256(raw).hexdigest() == events['raw_sha256']
            streams = {}
            for line in raw.splitlines():
                if not line:
                    continue
                event = json.loads(line)
                if event.get('id') not in good_ids:
                    continue
                key = (event['id'], event.get('memory_profile'), event['type'], event.get('stage'))
                semantic = {k: v for k, v in event.items() if k not in ('cycle', 'first_cycle', 'last_cycle')}
                streams.setdefault(key, []).append(semantic)
            grouped[implementation] = streams
            canonical = variant['canonical_actual']
            canonical_path = folder / canonical['path']
            canonical_raw = gzip.decompress(canonical_path.read_bytes())
            checks[implementation + '_canonical_raw_sha256'] = hashlib.sha256(canonical_raw).hexdigest() == canonical['raw_sha256']
            grouped[implementation]['__canonical_raw__'] = canonical_raw

        base, candidate = grouped['baseline'], grouped['candidate']
        checks['canonical_raw_bytes_equal'] = base.pop('__canonical_raw__') == candidate.pop('__canonical_raw__')
        same_keys = base.keys() == candidate.keys()
        if same_keys:
            for key, expected in sorted(base.items(), key=lambda item: str(item[0])):
                actual = candidate[key]
                digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                semantics.append({'stream': list(key), 'events': len(actual), 'sha256': digest, 'equal': expected == actual})
        reported = run.get('semantic_streams', {})
        checks['independent_ordered_good_frame_streams'] = (same_keys and len(semantics) == 52
            and all(x['equal'] for x in semantics) and reported.get('status') == 'PASS_ORDERED_SEMANTIC_STREAMS'
            and [{k: x[k] for k in ('stream', 'events', 'sha256')} for x in semantics] == reported.get('streams'))

        simulation = {}
        for implementation in ('baseline', 'candidate'):
            sim_path = folder / f'{implementation}-{seed}-simulation.jsonl'
            rows = [json.loads(line) for line in sim_path.read_text().splitlines() if line.strip()]
            simulation[implementation] = {(row['id'], row['memory_profile']): row for row in rows if row.get('type') == 'case'}
        b_rows, c_rows = simulation['baseline'], simulation['candidate']
        profile_ok = b_rows.keys() == c_rows.keys() and len(c_rows) == 22
        for key, c in c_rows.items():
            b = b_rows[key]
            row_ok = b['error'] == c['error'] and c['status'] == 'PASS'
            if c['error'] == 0:
                row_ok &= all(b[field] == c[field] for field in ('coefficients', 'core_starts', 'refill_bytes', 'child_epochs', 'frame_epoch'))
                e = c['elastic']
                row_ok &= e['accepted'] == e['delivered'] == c['coefficients'] and e['discarded'] == 0 and e['final_occupied'] == 0
            else:
                e = c['elastic']
                row_ok &= e['accepted'] == e['delivered'] + e['discarded'] and e['final_occupied'] == 0
            profile_ok &= bool(row_ok)
        stored = run.get('case_latency', [])
        stored_ok = len(stored) == 22
        for item in stored:
            key = (item['id'], item['memory_profile'])
            b, c = b_rows[key], c_rows[key]
            stored_ok &= (item['baseline_cycles'] == b['cycles'] and item['candidate_cycles'] == c['cycles']
                and item['delta_cycles'] == c['cycles'] - b['cycles'] and item['elastic'] == c['elastic'])
        checks['independent_case_goldens_and_conservation'] = bool(profile_ok and stored_ok)
        checks['canonical_equality_flag'] = run.get('equalities', {}).get('canonical') is True
        v = run['variants']['candidate']['verdict']
        checks['aggregate_candidate_conservation'] = v['elastic_total_up'] == v['elastic_total_down'] + v['elastic_total_discard']
    except (OSError, EOFError, KeyError, ValueError, json.JSONDecodeError) as exc:
        checks['independent_replay_completed'] = False
        return {'seed': seed, 'checks': checks, 'semantic_streams': semantics, 'error': str(exc)}
    return {'seed': seed, 'checks': checks, 'semantic_streams': semantics, 'cases_checked': len(run.get('case_latency', [])),
            'candidate_counts': {k: run['variants']['candidate']['verdict'].get(k)
                                 for k in ('elastic_total_up', 'elastic_total_down', 'elastic_total_discard')}}


def audit_elastic_pipeline() -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/elastic-pipeline'
    attempt_dirs = sorted(p for p in (area / 'attempts').glob('*') if p.is_dir()) if (area / 'attempts').exists() else []
    attempts = []
    for folder in attempt_dirs:
        result_path = folder / 'results.json'
        if not result_path.is_file():
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PENDING', 'results': None,
                             'logs_present': sorted(p.name for p in folder.glob('*log'))})
            continue
        report = json.loads(result_path.read_text())
        artifacts = {rel: {'expected': digest, 'actual': sha256(folder / rel) if (folder / rel).is_file() else None,
                           'matches': (folder / rel).is_file() and sha256(folder / rel) == digest}
                     for rel, digest in report.get('artifacts_sha256', {}).items()}
        sources = {}
        for rel, digest in report.get('source_sha256', {}).items():
            live = ROOT / rel
            snapshot = folder / 'sources' / rel
            live_hash = sha256(live) if live.is_file() else None
            snapshot_hash = sha256(snapshot) if snapshot.is_file() else None
            sources[rel] = {'expected': digest, 'live': live_hash, 'snapshot': snapshot_hash,
                            'snapshot_matches': snapshot_hash == digest, 'current_matches': live_hash == digest}
        seed_results = [audit_elastic_seed(folder, run) for run in report.get('runs', [])]
        warning_matches = []
        logs = ('verilator.log', 'compiler.log', 'compile-baseline.log', 'compile-candidate.log',
                'binary-baseline.log', 'binary-candidate.log')
        for name in logs:
            fp = folder / name
            if fp.is_file():
                warning_matches.extend({'file': name, 'line': line.strip()} for line in fp.read_text(errors='replace').splitlines()
                    if re.search(r'(?i)(?:%Warning-|\bwarning:|waiver|TEST_FAIL|assertion failed)', line))
        commands_ok = len(report.get('commands', [])) >= 10 and all(x.get('exit_code') == 0 for x in report.get('commands', []))
        passed = (report.get('status') == 'PASS' and report.get('actual_RTL_run') is True
                  and report.get('assertions_disabled_or_downgraded') is False
                  and report.get('mode') == 'canonical' and report.get('variant') == 'elastic'
                  and report.get('seeds') == [107601, 107602]
                  and report.get('case_profile_runs') == 88 and report.get('directed_checks') == 84
                  and report.get('ordered_good_frame_semantic_streams_equal') is True
                  and report.get('exact_same_seed_canonical_bytes') is True
                  and all(x['matches'] for x in artifacts.values())
                  and all(x['snapshot_matches'] for x in sources.values())
                  and all(x['current_matches'] for x in sources.values())
                  and len(seed_results) == 2 and all(all(v is True for v in x['checks'].values()) for x in seed_results)
                  and commands_ok and not warning_matches)
        attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'PASS' if passed else 'TERMINAL_FAILURE_RETAINED',
                         'results': str(result_path.relative_to(ROOT)), 'results_sha256': sha256(result_path),
                         'terminal_report_status': report.get('status'), 'actual_RTL_run': report.get('actual_RTL_run'),
                         'error': report.get('error'), 'artifacts_checked': len(artifacts), 'sources_checked': len(sources),
                         'artifacts_match': all(x['matches'] for x in artifacts.values()),
                         'source_snapshots_match': all(x['snapshot_matches'] for x in sources.values()),
                         'sources_match_current': all(x['current_matches'] for x in sources.values()),
                         'source_results': sources, 'runs': seed_results, 'commands_ok': commands_ok,
                         'warning_matches': warning_matches})
    latest = attempts[-1] if attempts else {'status': 'PENDING'}
    selected_area = area / 'results.json'
    selection = json.loads(selected_area.read_text()) if selected_area.is_file() else None
    any_pending = latest['status'] == 'PENDING'
    pointer = selection.get('selected_report') if selection else None
    pointed_attempt = next((x for x in attempts if x.get('results') == pointer), None)
    pointed = json.loads((ROOT / pointer).read_text()) if pointer and (ROOT / pointer).is_file() else {}
    pointer_ok = bool(selection and pointed_attempt and pointed_attempt['status'] == 'PASS' and selection.get('status') == 'PASS'
        and all(selection.get(k) == pointed.get(k) for k in ('status', 'actual_RTL_run', 'source_sha256', 'runs', 'case_profile_runs', 'directed_checks')))
    status = ('PENDING_ELASTIC_FULL_PIPELINE' if any_pending else
              'AUDIT_ERROR' if latest['status'] == 'PASS' and not pointer_ok else latest['status'])
    return {'status': status,
            'selection': str(selected_area.relative_to(ROOT)) if selection else None,
            'selection_sha256': sha256(selected_area) if selection else None,
            'selected_report_pointer': pointer, 'selected_report_sha256': sha256(ROOT / pointer) if pointer and (ROOT / pointer).is_file() else None,
            'selection_points_to_audited_pass': pointer_ok,
            'attempts': attempts,
            'scope': 'Latency-aware full canonical pipeline comparison with independent ordered-stream replay and per-case conservation/golden audit; no physical timing or hardware qualification.'}


def audit_native_builds(matrix_record: dict, elastic_pipeline_record: dict, header_pipeline_record: dict,
                        tables_record: dict, payload_record: dict, guard_record: dict, meta_record: dict,
                        prefix_record: dict, count_record: dict, threshold_pipeline_record: dict,
                        threshold_activation_record: dict,
                        threshold_runtime_activation_record: dict) -> dict:
    area = ROOT / 'experiments/python-gamebub-v107/native'
    attempts = []
    for receipt_path in sorted(area.glob('*/receipt.json')) if area.exists() else []:
        folder = receipt_path.parent
        receipt = json.loads(receipt_path.read_text())
        checks = {}
        try:
            inputs_path = folder / 'inputs.json'
            inputs = json.loads(inputs_path.read_text())
            source_pins = inputs['source_sha256']
            origins = inputs['source_origins']
            variant = inputs['variant']
            expected_sources, expected_rtl = ((18, 17) if ('tables' in variant or 'payload' in variant or 'guard' in variant or 'meta' in variant or 'threshold' in variant) else
                (18, 17) if ('elastic' in variant or 'header' in variant) else (17, 16))
            snapshots = {}
            for rel, digest in source_pins.items():
                fp = folder / 'source-snapshot' / rel
                actual = sha256(fp) if fp.is_file() else None
                origin = origins.get(rel, {})
                origin_path = ROOT / origin['path'] if origin.get('path') else None
                origin_actual = sha256(origin_path) if origin_path and origin_path.is_file() else None
                snapshots[rel] = {'expected': digest, 'actual': actual,
                                  'origin_expected': origin.get('sha256'), 'origin_actual': origin_actual,
                                  'snapshot_matches': actual == digest,
                                  'origin_matches': origin_actual == origin.get('sha256') == digest}
            recipes = {}
            recipe_expected = inputs['recipe_sha256']
            for name, digest in recipe_expected.items():
                fp = folder / 'recipe-snapshot' / name
                actual = sha256(fp) if fp.is_file() else None
                recipes[name] = {'expected': digest, 'actual': actual, 'matches': actual == digest}
            input_hash = sha256(inputs_path)
            source_snapshot_receipt = receipt.get('retained_source_snapshot_sha256', {})
            source_mount = receipt.get('source_snapshot_readonly_mount') is True
            checks.update({
                'receipt_binds_native_input_manifest': receipt.get('source_manifest_sha256') == input_hash,
                'source_snapshot_cardinality_matches_variant': len(source_pins) == expected_sources
                    and len([x for x in source_pins if x.endswith(('.sv', '.v'))]) == expected_rtl,
                'receipt_source_snapshot_map_matches_inputs': source_snapshot_receipt == source_pins,
                'retained_source_snapshots_match_manifest': all(x['snapshot_matches'] for x in snapshots.values()),
                'runner_source_snapshot_unchanged_flag': (receipt.get('source_snapshot_unchanged') is True
                    if receipt.get('status') != 'RUNNING' else receipt.get('source_snapshot_unchanged') in (None, True)),
                'input_source_origins_match_manifest': all(x['origin_matches'] for x in snapshots.values()),
                'readonly_source_snapshot_mount_recorded': source_mount,
                'retained_recipe_snapshots_match_manifest': bool(recipes) and all(x['matches'] for x in recipes.values()),
                'target_and_ooc_clock_recorded': receipt.get('part') == 'xc7a100tcsg324-1'
                    and receipt.get('clock_period_ns') == 10.0 and receipt.get('top') == 'cs88_pipeline_v91k',
                'default_two_thread_flow_recorded': receipt.get('max_threads') == 2
                    and inputs.get('constraints', '').startswith('Same V101 10ns OOC comparison clock'),
                'vivado_maps_readonly_source_snapshot': any(
                    isinstance(arg, str) and '/snapshot,readonly' in arg
                    for arg in receipt.get('command', [])),
                'no_board_or_hardware_qualification_claim': receipt.get('board_IO_timing_qualified') is False
                    and receipt.get('full_custom_top_qualified') is False and receipt.get('hardware_30fps') is False,
            })
            behavioral_preflight = {'status': 'NOT_APPLICABLE', 'checks': {}}
            header_scheduling_cancelled = False
            if 'quant' in variant:
                quant_results = {}
                quant_checks = {}
                lanes_by_key = {(x['variant'], x['mode']): x for x in matrix_record.get('required_lanes', [])}
                quant_source_maps = []
                for mode, expected_profile, expected_directed in (('fresh', 24, 52), ('canonical', 88, 84)):
                    lane = lanes_by_key.get(('quant-aligned', mode), {})
                    result_path = ROOT / lane['results'] if lane.get('results') else None
                    report = json.loads(result_path.read_text()) if result_path and result_path.is_file() else {}
                    source_map = report.get('source_sha256', {})
                    required_override_paths = set(inputs.get('source_overrides', {}).values())
                    override_matches = all(source_map.get(path) == next((v['sha256'] for v in origins.values()
                        if v['path'] == path), None) for path in required_override_paths)
                    origin_matches = override_matches and all(
                        source_map[path] == digest for path, digest in source_map.items()
                        if path in {v['path'] for v in origins.values()})
                    quant_source_maps.append(source_map)
                    quant_results[mode] = {'results': lane.get('results'), 'status': report.get('status'),
                        'case_profile_runs': report.get('case_profile_runs'), 'directed_checks': report.get('directed_checks'),
                        'seeds': report.get('seeds'), 'exact_same_seed_transcripts_events_cycles': report.get('exact_same_seed_transcripts_events_cycles'),
                        'native_source_origins_match_pair': origin_matches}
                    quant_checks[mode] = (lane.get('status') == 'PASS' and report.get('status') == 'PASS'
                        and report.get('actual_RTL_run') is True and report.get('assertions_disabled_or_downgraded') is False
                        and report.get('case_profile_runs') == expected_profile and report.get('directed_checks') == expected_directed
                        and report.get('seeds') == [107501, 107502]
                        and report.get('exact_same_seed_transcripts_events_cycles') is True and origin_matches)
                if len(quant_source_maps) == 2:
                    shared = set(quant_source_maps[0]) & set(quant_source_maps[1])
                    pair_source_match = all(quant_source_maps[0][path] == quant_source_maps[1][path] for path in shared)
                    quant_checks['fresh_and_canonical_sources_match'] = pair_source_match
                behavioral_preflight = {'status': 'PASS' if all(quant_checks.values()) else 'PENDING_OR_FAILED',
                                        'checks': quant_checks, 'runs': quant_results}
                checks['native_source_map_matches_qualified_quant_pair'] = behavioral_preflight['status'] == 'PASS'
            elif 'header' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                header_ok = (header_pipeline_record.get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/header-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_HEADER_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and inputs.get('header_zero_extra_cycles_relative_to_elastic') is True
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if header_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches}
                checks['native_source_map_matches_qualified_header_pipeline'] = header_ok
            elif 'tables' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                tables_ok = (tables_record.get('full_pipeline', {}).get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/tables-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_TABLES_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and inputs.get('header_and_tables_zero_extra_cycles_relative_to_elastic') is True
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if tables_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches}
                checks['native_source_map_matches_qualified_tables_pipeline'] = tables_ok
            elif 'payload' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                payload_ok = (payload_record.get('status') == 'PASS_PAYLOAD_RESET_COMPONENT_PROOFS'
                    and payload_record.get('full_payload_pipeline', {}).get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/payload-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_PAYLOAD_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and inputs.get('header_and_tables_zero_extra_cycles_relative_to_elastic') is True
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if payload_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches,
                    'reset_component_proofs_pass': payload_record.get('status') == 'PASS_PAYLOAD_RESET_COMPONENT_PROOFS'}
                checks['native_source_map_matches_qualified_payload_pipeline'] = payload_ok
            elif 'guard' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                guard_ok = (guard_record.get('status') == 'PASS_GUARD_DSP_FOCUS_AUDITED'
                    and guard_record.get('full_pipeline', {}).get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/guard-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_GUARD_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and inputs.get('header_and_tables_zero_extra_cycles_relative_to_elastic') is True
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if guard_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches,
                    'guard_expression_proof_pass': guard_record.get('status') == 'PASS_GUARD_DSP_FOCUS_AUDITED'}
                checks['native_source_map_matches_qualified_guard_pipeline'] = guard_ok
            elif 'meta' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                meta_ok = (meta_record.get('status') == 'PASS_META_FLAGS_UNIT_AUDITED'
                    and meta_record.get('full_pipeline', {}).get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/meta-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_META_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if meta_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches,
                    'meta_unit_proofs_pass': meta_record.get('status') == 'PASS_META_FLAGS_UNIT_AUDITED'}
                checks['native_source_map_matches_qualified_meta_pipeline'] = meta_ok
            elif 'threshold' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                activation_path = ROOT / 'experiments/python-gamebub-v107/coordination/threshold-native-activation.json'
                activation_ok = (threshold_activation_record.get('status') == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED'
                    and activation_path.is_file() and qualification.get('activation_path') == str(activation_path.relative_to(ROOT))
                    and qualification.get('activation_sha256') == sha256(activation_path))
                unit_rel = threshold_activation_record.get('unit_qualification')
                unit_path = ROOT / unit_rel if unit_rel else None
                threshold_unit_path = qualification.get('threshold_native_unit_path')
                threshold_unit_file = ROOT / threshold_unit_path if threshold_unit_path else None
                tables_unit_path = ROOT / 'experiments/python-gamebub-v107/tables/unit/20261108T051111105011Z/receipt.json'
                mapped_unit_hash_ok = (tables_unit_path.is_file()
                    and qualification.get('mapped_unit_path') == str(tables_unit_path.relative_to(ROOT))
                    and qualification.get('mapped_unit_sha256') == sha256(tables_unit_path))
                threshold_unit_hash_ok = (bool(unit_path and unit_path.is_file())
                    and unit_path == threshold_unit_file
                    and qualification.get('threshold_native_unit_sha256') == sha256(unit_path)
                    and count_record.get('native_unit', {}).get('status') == 'PASS_COUNT_THRESHOLD_NATIVE_UNIT_AUDITED'
                    and count_record.get('native_unit', {}).get('receipt') == unit_rel
                    and threshold_activation_record.get('unit_sha256') == sha256(unit_path))
                threshold_ok = (activation_ok and mapped_unit_hash_ok and threshold_unit_hash_ok
                    and prefix_record.get('status') == 'PASS_PREFIX_QUALIFICATION_AUDITED'
                    and count_record.get('status') == 'PASS_COUNT_THRESHOLD_QUALIFICATION_AUDITED'
                    and threshold_pipeline_record.get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/threshold-pipeline/results.json'
                    and full_report.get('status') == 'PASS_EXACT_THRESHOLD_CANONICAL'
                    and full_report.get('actual_RTL_run') is True
                    and full_report.get('baseline_recompiled_or_rerun') is False
                    and full_report.get('newly_executed_candidate_case_profiles') == 44
                    and full_report.get('newly_executed_candidate_directed_checks') == 42
                    and origin_matches and sha256(full_report_path) == qualification.get('sha256'))
                runtime_variant = variant == 'threshold-runtime'
                runtime_flow_ok = True
                runtime_inputs_ok = True
                if runtime_variant:
                    runtime_inputs = threshold_runtime_activation_record.get('default_inputs')
                    default_inputs_path = ROOT / runtime_inputs if runtime_inputs else None
                    default_inputs = json.loads(default_inputs_path.read_text()) if default_inputs_path and default_inputs_path.is_file() else {}
                    runtime_inputs_ok = (threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED'
                        and inputs.get('strategy') == {'synth': 'RuntimeOptimized', 'opt': 'Default', 'place': 'Default', 'route': 'Default'}
                        and inputs.get('runtime_activation_required') is True
                        and inputs.get('source_set_ordinal') == 8 and inputs.get('native_attempt_ordinal') == 9
                        and inputs.get('source_sha256') == default_inputs.get('source_sha256') == source_pins
                        and inputs.get('source_origins') == default_inputs.get('source_origins') == origins)
                    runtime_preflight_path = ROOT / threshold_runtime_activation_record.get('prepared_preflight', '')
                    runtime_preflight = json.loads(runtime_preflight_path.read_text()) if runtime_preflight_path.is_file() else {}
                    recipe_run = folder / 'recipe-snapshot/run.tcl'
                    recipe_report = folder / 'recipe-snapshot/report.tcl'
                    recipe_xdc = folder / 'recipe-snapshot/component.xdc'
                    runtime_flow_ok = (recipe_run.is_file() and recipe_report.is_file() and recipe_xdc.is_file()
                        and sha256(recipe_run) == runtime_preflight.get('flow_after_sha256')
                        and sha256(recipe_report) == runtime_preflight.get('preserved_flow_sha256', {}).get('report.tcl')
                        and sha256(recipe_xdc) == runtime_preflight.get('preserved_flow_sha256', {}).get('component.xdc'))
                behavioral_preflight = {'status': 'PASS' if threshold_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches, 'activation_pass': activation_ok,
                    'mapped_tables_unit_hash_matches_builder_qualification': mapped_unit_hash_ok,
                    'threshold_arithmetic_unit_hash_matches_activation': threshold_unit_hash_ok,
                    'runtime_activation_pass': (threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED'
                        if runtime_variant else None),
                    'runtime_source_inputs_match_Default8': runtime_inputs_ok if runtime_variant else None,
                    'runtime_recipe_matches_preflight': runtime_flow_ok if runtime_variant else None}
                checks['native_source_map_matches_threshold_canonical_and_activation'] = threshold_ok
                if runtime_variant:
                    checks['runtime_attempt_is_one_same_source_strategy_trial'] = runtime_inputs_ok and runtime_flow_ok
            elif 'elastic' in variant:
                qualification = inputs.get('behavioral_qualification') or {}
                qualification_path = qualification.get('path')
                full_report_path = ROOT / qualification_path if qualification_path else None
                full_report = json.loads(full_report_path.read_text()) if full_report_path and full_report_path.is_file() else {}
                origin_matches = all(full_report.get('source_sha256', {}).get(source['path']) == source['sha256']
                                     for source in origins.values())
                elastic_ok = (elastic_pipeline_record.get('status') == 'PASS'
                    and qualification_path == 'experiments/python-gamebub-v107/elastic-pipeline/results.json'
                    and full_report.get('status') == 'PASS' and full_report.get('actual_RTL_run') is True
                    and len(full_report.get('runs', [])) == 2 and origin_matches
                    and sha256(full_report_path) == qualification.get('sha256'))
                behavioral_preflight = {'status': 'PASS' if elastic_ok else 'PENDING_OR_FAILED',
                    'path': qualification_path, 'sha256': qualification.get('sha256'),
                    'actual_sha256': sha256(full_report_path) if full_report_path and full_report_path.is_file() else None,
                    'source_origins_match_qualification': origin_matches}
                checks['native_source_map_matches_qualified_elastic_pipeline'] = elastic_ok
            if ('header' in variant or 'guard' in variant) and receipt.get('status') == 'TOOL_OR_BUILD_FAILED' and receipt.get('observed_exit_code') == 143:
                cancel_kind = 'guard' if 'guard' in variant else 'header'
                cancellation_path = ROOT / f'experiments/python-gamebub-v107/coordination/{cancel_kind}-scheduling-cancellation.json'
                policy_path = ROOT / 'experiments/python-gamebub-v107/study-policy.json'
                cancellation = json.loads(cancellation_path.read_text())
                policy = json.loads(policy_path.read_text())
                policy_key = f'{cancel_kind}_scheduling_redirection'
                cancellation_ok = (
                    cancellation.get('schema') == f'v107-{cancel_kind}-scheduling-cancellation-v1'
                    and cancellation.get('receipt') == str(receipt_path.relative_to(ROOT))
                    and cancellation.get('terminal_receipt_sha256') == sha256(receipt_path)
                    and cancellation.get('terminal_observed_exit_code') == receipt.get('observed_exit_code') == 143
                    and cancellation.get('terminal_status') == receipt.get('status') == 'TOOL_OR_BUILD_FAILED'
                    and cancellation.get('terminal_wall_seconds') == receipt.get('wall_seconds')
                    and cancellation.get('timeout_seconds_not_reached') == receipt.get('timeout_seconds') == 3600
                    and cancellation.get('synthesis_checkpoint_written') is False
                    and cancellation.get('routing_checkpoint_written') is False
                    and cancellation.get('retained_source_unchanged') is True
                    and cancellation.get('decision_utc') is not None
                    and policy.get('max_heavy_jobs') == 2
                    and policy.get(policy_key, {}).get('receipt') == str(receipt_path.relative_to(ROOT))
                    and policy.get(policy_key, {}).get('maximum_watchdog_unchanged_seconds') == 3600
                )
                checks[f'{cancel_kind}_scheduling_cancellation_record_matches_terminal_receipt'] = cancellation_ok
                checks[f'{cancel_kind}_cancelled_before_checkpoint_not_timing_result'] = (
                    'not a tool timeout' in cancellation.get('reason', '').lower()
                    and receipt.get('synthesis_checkpoint_written') is False
                    and receipt.get('component_route_finished') is False
                )
                header_scheduling_cancelled = cancellation_ok and checks[f'{cancel_kind}_cancelled_before_checkpoint_not_timing_result']
            recipe_paths = {name: (folder / 'recipe-snapshot' / name).read_text(errors='replace')
                            for name in recipes if (folder / 'recipe-snapshot' / name).is_file()}
            xdc = recipe_paths.get('component.xdc', '')
            checks['inherited_single_10ns_clock_no_io_delays_or_exceptions'] = (
                'create_clock -name component_clk -period 10.000 [get_ports clk]' in xdc
                and not re.search(r'(?m)^\s*set_(?:input_delay|output_delay|false_path|multicycle_path|clock_groups)\b', xdc)
            )
            run_tcl = recipe_paths.get('run.tcl', '')
            synth_directive = '-directive RuntimeOptimized' if variant == 'threshold-runtime' else '-directive Default'
            checks['native_tcl_uses_qualified_synth_and_default_opt_place_route'] = (
                'synth_design' in run_tcl and synth_directive in run_tcl
                and all(f'{command}_design -directive Default' in run_tcl for command in ('opt', 'place', 'route')))
            if variant == 'threshold-runtime':
                default_run = ROOT / 'experiments/python-gamebub-v107/native/20261108T073857407909Z/recipe-snapshot/run.tcl'
                runtime_run = folder / 'recipe-snapshot/run.tcl'
                old_directive = ' -directive Default'
                new_directive = ' -directive RuntimeOptimized'
                checks['runtime_recipe_diff_is_only_synth_directive'] = (
                    default_run.is_file() and runtime_run.is_file()
                    and old_directive in default_run.read_text()
                    and default_run.read_text().count(old_directive) == 1
                    and runtime_run.read_text() == default_run.read_text().replace(old_directive, new_directive, 1))
            artifact_results = {}
            reports = {}
            for name, artifact in receipt.get('artifacts', {}).items():
                copied = folder / 'reports' / name
                textual = Path(name).suffix in ('.rpt', '.txt', '.json', '.xdc', '.tsv')
                if textual:
                    actual = sha256(copied) if copied.is_file() else None
                    artifact_results[name] = {'expected': artifact['sha256'], 'actual': actual,
                                              'matches': actual == artifact['sha256'] and copied.stat().st_size == artifact['bytes'] if copied.is_file() else False}
                    if copied.is_file():
                        reports[name] = copied.read_text(errors='replace')
            report_hashes_ok = all(x['matches'] for x in artifact_results.values())
            checks['all_copied_textual_native_artifacts_match_receipt'] = report_hashes_ok
            log_path = folder / 'vivado.log'
            checks['terminal_log_hash_matches_receipt'] = (bool(receipt.get('log_sha256')) and log_path.is_file()
                and sha256(log_path) == receipt['log_sha256']) if receipt.get('status') != 'RUNNING' else log_path.is_file()
            required = ('route-timing-summary.rpt', 'route-clocks.rpt', 'route-check-timing.rpt',
                        'route-setup-paths.rpt', 'route-status.rpt', 'route-exceptions.rpt',
                        'route-methodology.rpt', 'route-drc.rpt', 'route-cdc.rpt')
            route_complete = receipt.get('status') == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
            if route_complete:
                log_text = log_path.read_text(errors='replace') if log_path.is_file() else ''
                checks['route_finish_marker_and_zero_exit_code'] = receipt.get('observed_exit_code') == 0 \
                    and 'V107_COMPONENT_ROUTE_FINISHED' in log_text
                checks['required_routed_native_reports_retained'] = all(x in reports for x in required)
                timing = native_timing(reports['route-timing-summary.rpt']) if required[0] in reports else {}
                clocks = [{'name': m[1], 'period_ns': float(m[2]), 'waveform': m[3], 'source': m[4]}
                          for m in re.finditer(r'^([^\s]+)\s+(\d+\.\d+)\s+(\{[^}]+\})\s+\S+\s+(.+)$', reports.get('route-clocks.rpt', ''), re.M)]
                check_timing = {k: int(v) for k, v in re.findall(
                    r'^\s*\d+\. checking ([\w]+) \((\d+)\)', reports.get('route-check-timing.rpt', ''), re.M)}
                exceptions = reports.get('route-exceptions.rpt', '')
                routing = native_routing(reports.get('route-status.rpt', ''))
                checks['only_inherited_component_clock_present'] = len(clocks) == 1 and clocks[0]['name'] == 'component_clk' and clocks[0]['period_ns'] == 10.0
                checks['setup_hold_pulse_all_pass'] = timing.get('WNS_ns', -1) >= 0 and timing.get('setup_failing', 1) == 0 \
                    and timing.get('WHS_ns', -1) >= 0 and timing.get('hold_failing', 1) == 0 \
                    and timing.get('WPWS_ns', -1) >= 0 and timing.get('pulse_failing', 1) == 0
                checks['no_clock_unconstrained_internal_or_timing_loop'] = all(
                    check_timing.get(k) == 0 for k in ('no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops'))
                checks['no_valid_timing_exceptions_reported'] = 'No valid timing exceptions found.' in exceptions
                checks['routing_complete_and_error_free'] = routing.get('zero_routing_errors') is True and routing.get('all_routable_nets_routed') is True
                timing_record = {'summary': timing, 'clocks': clocks, 'check_timing': check_timing,
                                 'exceptions_no_valid_exceptions': 'No valid timing exceptions found.' in exceptions,
                                 'routing': routing,
                                 'worst_setup_path': native_worst_path(reports.get('route-setup-paths.rpt', '')),
                                 'drc': native_findings(reports.get('route-drc.rpt', '')),
                                 'methodology': native_findings(reports.get('route-methodology.rpt', '')),
                                 'cdc_sha256': receipt.get('artifacts', {}).get('route-cdc.rpt', {}).get('sha256')}
            else:
                timing_record = None
                checks['terminal_route_status_claims_match_receipt'] = (
                    receipt.get('component_route_finished') is False if receipt.get('status') != 'RUNNING'
                    else receipt.get('component_route_finished') in (None, False)
                )
            quality_checks = {'setup_hold_pulse_all_pass', 'no_clock_unconstrained_internal_or_timing_loop',
                              'routing_complete_and_error_free'}
            integrity_ok = all(value for key, value in checks.items() if key not in quality_checks)
            qualified = route_complete and integrity_ok and all(checks.get(k) is True for k in quality_checks)
            if not integrity_ok:
                attempt_status = 'AUDIT_ERROR'
            elif receipt.get('status') == 'RUNNING':
                attempt_status = 'PENDING'
            elif route_complete and qualified:
                attempt_status = 'PASS_COMPONENT_OOC_TIMING'
            elif route_complete:
                attempt_status = 'TERMINAL_ROUTE_NO_TIMING_PASS'
            elif header_scheduling_cancelled:
                attempt_status = 'SCHEDULING_CANCELLATION_RETAINED'
            else:
                attempt_status = 'TERMINAL_ROUTE_INCOMPLETE'
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': attempt_status,
                'variant': variant, 'receipt_sha256': sha256(receipt_path), 'input_sha256': input_hash,
                'source_count': len(source_pins), 'rtl_count': sum(x.endswith(('.sv', '.v')) for x in source_pins),
                'sources': snapshots, 'recipes': recipes, 'behavioral_preflight': behavioral_preflight,
                'artifact_hashes_match': report_hashes_ok,
                'artifact_results': artifact_results, 'route': timing_record, 'checks': checks,
                'scope': 'OOC component evidence only. Even nonnegative route timing does not qualify board I/O, CDC, reset integration, hardware, or decode latency.'})
        except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
            attempts.append({'path': str(folder.relative_to(ROOT)), 'status': 'AUDIT_ERROR', 'errors': [str(exc)], 'checks': checks})
    attempt_variants = sorted(x.get('variant') for x in attempts if x.get('variant'))
    variants = sorted(set('threshold' if x == 'threshold-runtime' else x for x in attempt_variants))
    source_limit = (threshold_activation_record.get('source_limit')
                    if threshold_activation_record.get('status') == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED'
                    else 7)
    source_cap_ok = len(variants) <= source_limit and (
        'threshold' not in variants or threshold_activation_record.get('status') == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED')
    runtime_attempts = attempt_variants.count('threshold-runtime')
    attempt_limit = (9 if threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED'
                     else (8 if threshold_activation_record.get('status') == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED' else 7))
    alternate_limit = (1 if threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED' else 0)
    attempt_cap_ok = len(attempts) <= attempt_limit and runtime_attempts <= alternate_limit and (
        runtime_attempts == 0 or threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED')
    if not source_cap_ok or not attempt_cap_ok:
        status = 'AUDIT_ERROR'
    elif not attempts:
        status = 'PENDING_NATIVE_BUILDS'
    elif any(x['status'] == 'AUDIT_ERROR' for x in attempts):
        status = 'AUDIT_ERROR'
    elif any(x['status'] == 'PENDING' for x in attempts):
        status = 'PENDING_NATIVE_BUILDS'
    elif any(x['status'] == 'PASS_COMPONENT_OOC_TIMING' for x in attempts):
        status = 'NATIVE_ROUTE_AUDITED_COMPONENT_ONLY'
    else:
        status = 'TERMINAL_NATIVE_EVIDENCE_RETAINED_NO_TIMING_PASS'
    return {'status': status, 'attempts': attempts, 'native_trial_variants': variants,
            'native_trial_variants_raw': attempt_variants,
            'native_trial_variant_count': len(variants), 'source_trial_limit': source_limit,
            'source_trial_cap_check': source_cap_ok,
            'native_attempt_count': len(attempts), 'native_attempt_limit': attempt_limit,
            'alternate_strategy_attempt_count': runtime_attempts, 'alternate_strategy_attempt_limit': alternate_limit,
            'native_attempt_cap_check': attempt_cap_ok,
            'scope': 'Audits receipt-bound retained source snapshots and native reports; component OOC result cannot establish board or hardware qualification.'}


def main() -> None:
    audit_rel = "experiments/python-gamebub-v106/native-audit.json"
    route_rel = "experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt"
    selected_receipt_rel = "experiments/python-gamebub-v106/native/20261108T013032873883Z/receipt.json"
    postroute_rel = "experiments/python-gamebub-v106/postroute/report-audit.json"
    sixth_rel = "experiments/python-gamebub-v106/native/20261108T025230842632Z/receipt.json"
    plan_rel = "docs/gamebub-v91-v110-development-plan.md"
    top_rel = "fpga/rtl/moonshine_top.sv"
    xdc_rel = "fpga/experiments/cu66-v106-flow/component.xdc"
    board_sources = [
        top_rel,
        "fpga/rtl/moonshine_bus_cdc.sv",
        "fpga/rtl/moonshine_memory.sv",
        "fpga/rtl/moonshine_lcd.sv",
        "fpga/rtl/esp32_overlay.sv",
    ]

    audit = load(audit_rel)
    selected = audit["measured_variants"]["closure"]
    selected_receipt = load(selected_receipt_rel)
    postroute = load(postroute_rel)
    sixth = load(sixth_rel)
    selected_route = selected["stages"]["route"]["timing"]
    report_hash = file_hash(route_rel)
    receipt_report_hash = selected_receipt["artifacts"]["route-setup-paths.rpt"]["sha256"]
    native_route_hash = audit["campaign_redirection"]["closure_route_evidence_sha256"]
    external_dcp = Path(sixth["artifacts"]["synth.dcp"]["external_path"])
    actual_dcp_hash = sha256(external_dcp) if external_dcp.is_file() else None
    expected_dcp_hash = sixth["artifacts"]["synth.dcp"]["sha256"]

    checks = {
        "selected_closure_is_completed_route": (
            selected["component_route_finished"] is True
            and selected_receipt["component_route_finished"] is True
            and selected_receipt["part"] == "xc7a100tcsg324-1"
            and selected_receipt["clock_period_ns"] == 10.0
        ),
        "selected_route_report_hash_agrees": (
            report_hash == receipt_report_hash == native_route_hash
        ),
        "selected_route_timing_remains_failing": (
            selected_route["WNS_ns"] == -4.034
            and selected_route["setup_failing"] == 44630
            and selected_route["setup_total"] == 106218
            and selected_route["WHS_ns"] >= 0
            and selected_route["WPWS_ns"] >= 0
        ),
        "separate_postroute_diagnostic_has_same_setup_failures": (
            postroute["before"]["timing"]["setup_failing_endpoints"] == 44630
            and postroute["after"]["timing"]["setup_failing_endpoints"] == 44630
            and postroute["selected_or_promoted"] is False
        ),
        "sixth_native_attempt_timed_out_before_placement": (
            sixth["status"] == "TOOL_OR_BUILD_FAILED"
            and sixth["observed_exit_code"] == 124
            and sixth["synthesis_checkpoint_written"] is True
            and sixth["placement_reports_present"] is False
            and sixth["component_route_finished"] is False
        ),
        "sixth_synthesis_checkpoint_exists_and_matches_receipt": (
            actual_dcp_hash is not None and actual_dcp_hash == expected_dcp_hash
        ),
        "ooc_recipe_is_one_clock_only": (
            "create_clock -name component_clk -period 10.000 [get_ports clk]" in (ROOT / xdc_rel).read_text()
            and "No external I/O" in (ROOT / xdc_rel).read_text()
        ),
    }
    if not all(checks.values()):
        failed = [name for name, ok in checks.items() if not ok]
        raise SystemExit("baseline evidence check failed: " + ", ".join(failed))

    top = (ROOT / top_rel).read_text()
    clocks = [
        {"name": "clk_50mhz", "role": "board input/base clock", "source": "moonshine_top port"},
        {"name": "clk200", "role": "service/QSPI endpoint and overlay system domain", "source": "service PLL output 0, BUFG"},
        {"name": "clk100", "role": "core/memory controller domain", "source": "service PLL output 1, BUFG"},
        {"name": "read_clk100", "role": "memory read domain, phase shifted", "source": "service PLL output 2 (279-degree phase), BUFG"},
        {"name": "pclk", "role": "LCD/pixel and overlay output domain", "source": "separate panel MMCM output, BUFG"},
    ]
    assert all(token in top for token in ("raw200", "raw100", "raw_read100", "279.0", "pclk", "rst200", "rst100", "rstpixel"))

    input_paths = [
        plan_rel,
        "docs/cu66-v106/baseline-audit.md",
        "docs/cu66-v106/remaining-timing-plan.md",
        audit_rel,
        selected_receipt_rel,
        route_rel,
        postroute_rel,
        sixth_rel,
        xdc_rel,
        top_rel,
    ]
    result = {
        "schema": "v107-baseline-independent-audit-v1",
        "status": "PASS_BASELINE_EVIDENCE",
        "scope": "Read-only V106 baseline and V107 interface/clock inventory. No vendor flow, board test, or V106 mutation.",
        "target": {"part": "xc7a100tcsg324-1", "ooc_clock_period_ns": 10.0, "top": "cs88_pipeline_v91k"},
        "selected_v106": {
            "variant": "closure",
            "receipt": selected_receipt_rel,
            "route_report": route_rel,
            "route_report_sha256": report_hash,
            "route_dcp_sha256_recorded": selected_receipt["artifacts"]["route.dcp"]["sha256"],
            "wns_ns": selected_route["WNS_ns"],
            "setup_failing_endpoints": selected_route["setup_failing"],
            "setup_total_endpoints": selected_route["setup_total"],
            "hold_slack_ns": selected_route["WHS_ns"],
            "pulse_slack_ns": selected_route["WPWS_ns"],
            "component_timing_target_met": selected["component_internal_timing_target_met"],
            "board_io_timing_qualified": selected["board_IO_timing_qualified"],
        },
        "separate_postroute_diagnostic": {
            "report_audit": postroute_rel,
            "wns_ns": postroute["after"]["timing"]["WNS_ns"],
            "setup_failing_endpoints": postroute["after"]["timing"]["setup_failing_endpoints"],
            "selected_or_promoted": postroute["selected_or_promoted"],
            "scope": "Separate strategy diagnostic on the selected checkpoint; it does not change source selection or close setup timing.",
        },
        "sixth_attempt": {
            "receipt": sixth_rel,
            "status": sixth["status"],
            "exit_code": sixth["observed_exit_code"],
            "elapsed_seconds": sixth["wall_seconds"],
            "placement_reports_present": sixth["placement_reports_present"],
            "routing_checkpoint_written": sixth["routing_checkpoint_written"],
            "synth_dcp_external_path": str(external_dcp),
            "synth_dcp_sha256_receipt": expected_dcp_hash,
            "synth_dcp_sha256_actual": actual_dcp_hash,
            "route_result": None,
        },
        "actual_board_top": {
            "source": top_rel,
            "related_sources": board_sources[1:],
            "clocks": clocks,
            "reset_release": "Four-stage shift registers per clk200, clk100 and pclk; asynchronous assert on corresponding PLL LOCKED falling edge, deassertion shifts synchronously in each local domain.",
            "interfaces": ["50 MHz input", "external MCU QSPI pins", "buttons", "SDRAM pins", "LCD pixel/sync outputs"],
            "cross_domain_boundaries_to_inventory": [
                "external mcu_spi_clk/data into clk200 QSPI endpoint",
                "clk200 SPI-side to clk100 core-side moonshine_bus_cdc bridge",
                "clk100 core/memory to phase-shifted read_clk100 line-memory interface",
                "clk100 memory-side to pclk LCD line request/data interface",
                "clk200 overlay writes and pclk overlay pixel stream",
                "clk200 SPI-side overflow Gray counter to clk100 synchronizer/consumer",
            ],
            "qualification_gap": "V106 OOC component XDC contains one 10 ns clk constraint only; it has no board port delays, generated-clock relationships, CDC exceptions, reset recovery/removal budget, or full-top interface constraints.",
        },
        "checks": checks,
        "input_sha256": {rel: file_hash(rel) for rel in input_paths},
    }
    result["auditor"] = {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha256(Path(__file__))}
    result["input_sha256"][result["auditor"]["path"]] = result["auditor"]["sha256"]
    resume_records = []
    for receipt_path in sorted((ROOT / "experiments/python-gamebub-v107/resume").glob("*/receipt.json")):
        rec = audit_resume(receipt_path)
        resume_records.append(rec)
        for rel in [str(receipt_path.relative_to(ROOT)),
                    str((receipt_path.parent / "parent-receipt.json").relative_to(ROOT)),
                    str((receipt_path.parent / "parent-inputs.json").relative_to(ROOT))]:
            if (ROOT / rel).is_file():
                result["input_sha256"][rel] = file_hash(rel)
        for snap in ("resume_route.py", "run.tcl", "report.tcl", "vivado.log"):
            candidate = receipt_path.parent / snap
            if candidate.is_file():
                result["input_sha256"][str(candidate.relative_to(ROOT))] = sha256(candidate)
        for report in sorted((receipt_path.parent / "reports").glob("*")) if (receipt_path.parent / "reports").exists() else []:
            if report.is_file():
                result["input_sha256"][str(report.relative_to(ROOT))] = sha256(report)
    result["resume_attempts"] = resume_records
    try:
        rice_record = audit_rice_probe()
        cdc_record = audit_cdc_selection()
        matrix_record = audit_matrix()
        quant_focus_record = audit_quant_focus()
        value_record = audit_value_check_selection()
        elastic_unit_record = audit_elastic_unit()
        cdc_native_record = audit_cdc_native()
        cdc_sync_record = audit_cdc_sync()
        elastic_pipeline_record = audit_elastic_pipeline()
        header_focus_record = audit_header_focus()
        header_pipeline_record = audit_header_pipeline()
        scale_record = audit_scale()
        tables_record = audit_tables()
        payload_record = audit_payload_reset()
        guard_record = audit_guard_dsp()
        meta_record = audit_meta_flags()
        prefix_record = audit_prefix_qualification()
        count_threshold_record = audit_count_threshold()
        threshold_pipeline_record = audit_tables_pipeline('threshold-pipeline',
            'PASS_EXACT_THRESHOLD_CANONICAL', 'PENDING_THRESHOLD_FULL_EVIDENCE', 'COUNT-THRESHOLD')
        threshold_activation_record = audit_threshold_native_activation(prefix_record, count_threshold_record,
            threshold_pipeline_record, meta_record)
        threshold_runtime_activation_record = audit_threshold_runtime_activation(threshold_activation_record)
        native_build_record = audit_native_builds(matrix_record, elastic_pipeline_record, header_pipeline_record,
            tables_record, payload_record, guard_record, meta_record, prefix_record, count_threshold_record,
            threshold_pipeline_record, threshold_activation_record, threshold_runtime_activation_record)
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        rice_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        cdc_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        matrix_record = {'status': 'PENDING_REQUIRED_LANES', 'complete': False, 'required_lanes': []}
        quant_focus_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        value_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        elastic_unit_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        cdc_native_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        cdc_sync_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        elastic_pipeline_record = {'status': 'PENDING_ELASTIC_FULL_PIPELINE', 'attempts': []}
        header_focus_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        header_pipeline_record = {'status': 'PENDING_HEADER_PIPELINE', 'attempts': []}
        native_build_record = {'status': 'AUDIT_ERROR', 'attempts': [], 'errors': [str(exc)]}
        scale_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        tables_record = {'status': 'PENDING_TABLES_FULL_EVIDENCE', 'errors': [str(exc)]}
        payload_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)],
                          'full_payload_pipeline': {'status': 'PENDING_PAYLOAD_FULL_EVIDENCE'}}
        guard_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)],
                        'full_pipeline': {'status': 'PENDING_GUARD_FULL_EVIDENCE'}}
        meta_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)],
                       'full_pipeline': {'status': 'PENDING_META_FULL_EVIDENCE'}}
        prefix_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        count_threshold_record = {'status': 'AUDIT_ERROR', 'errors': [str(exc)]}
        threshold_pipeline_record = {'status': 'PENDING_THRESHOLD_FULL_EVIDENCE', 'attempts': []}
        threshold_activation_record = {'status': 'PREPARED_NOT_ACTIVATED', 'checks': {}}
        threshold_runtime_activation_record = {'status': 'PREPARED_NOT_ACTIVATED', 'checks': {}}
    result['rice_probe'] = rice_record
    result['cdc_selection'] = cdc_record
    result['required_pipeline_matrix'] = matrix_record
    result['quant_focus'] = quant_focus_record
    result['value_expression'] = value_record
    result['elastic_unit'] = elastic_unit_record
    result['cdc_native'] = cdc_native_record
    result['cdc_sync'] = cdc_sync_record
    result['elastic_full_pipeline'] = elastic_pipeline_record
    result['header_focus'] = header_focus_record
    result['header_pipeline'] = header_pipeline_record
    result['native_builds'] = native_build_record
    result['scale_ram'] = scale_record
    result['tables_ram'] = tables_record
    result['payload_reset'] = payload_record
    result['guard_dsp'] = guard_record
    result['meta_flags'] = meta_record
    result['prefix_qualification'] = prefix_record
    result['count_threshold'] = count_threshold_record
    result['threshold_full_pipeline'] = threshold_pipeline_record
    result['threshold_native_activation'] = threshold_activation_record
    result['threshold_runtime_activation'] = threshold_runtime_activation_record
    evidence_inputs = [
        'experiments/python-gamebub-v107/rice/probe-results.json',
        'experiments/python-gamebub-v107/rice/audit.json',
        'experiments/python-gamebub-v107/cdc/results.json',
        'experiments/python-gamebub-v107/cdc/inventory.json',
        'experiments/python-gamebub-v107/quant/results.json',
        'experiments/python-gamebub-v107/quant/audit.json',
        'experiments/python-gamebub-v107/value-check/results.json',
        'scripts/cu66-v107/run_matrix.py',
        'scripts/cu66-v107/regress.py',
        'scripts/cu66-v107/quant_regress.py',
        'experiments/python-gamebub-v107/elastic/results.json',
        'experiments/python-gamebub-v107/elastic/audit.json',
        'experiments/python-gamebub-v107/cdc-native/results.json',
        'experiments/python-gamebub-v107/cdc-native/native-audit.json',
        'experiments/python-gamebub-v107/cdc-sync/results.json',
        'experiments/python-gamebub-v107/cdc-sync/audit.json',
        'experiments/python-gamebub-v107/cdc-sync/native/results.json',
        'experiments/python-gamebub-v107/cdc-sync/native/native-audit.json',
        'experiments/python-gamebub-v107/header/results.json',
        'experiments/python-gamebub-v107/header/audit.json',
        'experiments/python-gamebub-v107/header-pipeline/results.json',
        'scripts/cu66-v107/header_pipeline.py',
        'scripts/cu66-v107/header.py',
        'scripts/cu66-v107/elastic_pipeline.py',
        'scripts/cu66-v107/quant_build.py',
        'scripts/cu66-v107/elastic_build.py',
        'scripts/cu66-v107/tables_pipeline.py',
        'scripts/cu66-v107/tables_build.py',
        'experiments/python-gamebub-v107/guard-dsp/results.json',
        'experiments/python-gamebub-v107/guard-dsp/audit.json',
        'experiments/python-gamebub-v107/guard-dsp/attribution/receipt.json',
        'experiments/python-gamebub-v107/guard-dsp/route-probe/results.json',
        'experiments/python-gamebub-v107/guard-pipeline/results.json',
        'experiments/python-gamebub-v107/meta-flags/results.json',
        'experiments/python-gamebub-v107/meta-flags/audit.json',
        'experiments/python-gamebub-v107/meta-pipeline/results.json',
        'experiments/python-gamebub-v107/plan-prefix/results.json',
        'experiments/python-gamebub-v107/plan-prefix/audit.json',
        'experiments/python-gamebub-v107/count-threshold/results.json',
        'experiments/python-gamebub-v107/count-threshold/preparation.json',
        'experiments/python-gamebub-v107/count-threshold/arithmetic-review.json',
        'experiments/python-gamebub-v107/count-threshold/native-unit/results.json',
        'experiments/python-gamebub-v107/count-threshold/native-unit/evidence-index.json',
        'experiments/python-gamebub-v107/count-threshold/native-unit/audit.json',
        'experiments/python-gamebub-v107/count-threshold/native-unit/connectivity-attribution.json',
        'experiments/python-gamebub-v107/threshold-pipeline/results.json',
        'experiments/python-gamebub-v107/coordination/threshold-native-activation.json',
        'experiments/python-gamebub-v107/coordination/threshold-dispatch.json',
        'experiments/python-gamebub-v107/coordination/threshold-runtime-activation.json',
        'experiments/python-gamebub-v107/coordination/threshold-runtime-pre-native-audit.json',
        'experiments/python-gamebub-v107/coordination/threshold-runtime-dispatch.json',
        'experiments/python-gamebub-v107/coordination/meta-native-activation.json',
        'experiments/python-gamebub-v107/study-policy.json',
        'scripts/cu66-v107/guard_dsp.py',
        'scripts/cu66-v107/guard_dsp/audit.py',
        'scripts/cu66-v107/guard_dsp/attribution.py',
        'scripts/cu66-v107/guard_dsp/route_probe.py',
        'scripts/cu66-v107/guard_pipeline.py',
        'scripts/cu66-v107/guard_build.py',
        'scripts/cu66-v107/meta_flags.py',
        'scripts/cu66-v107/meta_flags/verification.py',
        'scripts/cu66-v107/meta_pipeline.py',
        'scripts/cu66-v107/meta_build.py',
        'scripts/cu66-v107/plan_prefix.py',
        'scripts/cu66-v107/plan_prefix/audit.py',
        'scripts/cu66-v107/plan_prefix/qualify.py',
        'scripts/cu66-v107/count_threshold.py',
        'scripts/cu66-v107/count_threshold/qualify.py',
        'scripts/cu66-v107/count_threshold/verification.py',
        'scripts/cu66-v107/count_threshold/model.py',
        'scripts/cu66-v107/threshold_pipeline.py',
        'scripts/cu66-v107/threshold_build.py',
        'fpga/experiments/cu66-v107-flow/run_vivado2026.py',
        'experiments/python-gamebub-v107/scale/results.json',
        'experiments/python-gamebub-v107/scale/unit/results.json',
        'experiments/python-gamebub-v107/scale/lookup-probe/results.json',
        'experiments/python-gamebub-v107/tables/results.json',
        'experiments/python-gamebub-v107/tables/unit/results.json',
        'experiments/python-gamebub-v107/tables-pipeline/results.json',
        'experiments/python-gamebub-v107/coordination/header-scheduling-cancellation.json',
        'experiments/python-gamebub-v107/coordination/guard-scheduling-cancellation.json',
        'experiments/python-gamebub-v107/study-policy.json',
        'experiments/python-gamebub-v107/payload-reset/results.json',
        'experiments/python-gamebub-v107/payload-reset/audit.json',
        'experiments/python-gamebub-v107/payload-reset/native/results.json',
        'experiments/python-gamebub-v107/payload-reset/native/query-results.json',
        'experiments/python-gamebub-v107/idct-reset/results.json',
        'experiments/python-gamebub-v107/idct-reset/audit.json',
        'experiments/python-gamebub-v107/idct-reset/native/results.json',
        'experiments/python-gamebub-v107/payload-pipeline/results.json',
        'scripts/cu66-v107/payload_pipeline.py',
        'scripts/cu66-v107/payload_build.py',
        'scripts/cu66-v107/payload_reset.py',
        'scripts/cu66-v107/payload_reset/native.py',
        'scripts/cu66-v107/idct_reset.py',
        'scripts/cu66-v107/idct_reset/native.py',
        'scripts/cu66-v107/tables_pipeline.py',
        'scripts/cu66-v107/tables_build.py',
        'fpga/experiments/cu66-v107-scale/cs88_admission_v91i2a.sv',
        'fpga/experiments/cu66-v107-tables/cs88_admission_v91i2a.sv',
    ]
    for rel in evidence_inputs:
        if (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    threshold_unit_dir = ROOT / 'experiments/python-gamebub-v107/count-threshold/native-unit'
    if threshold_unit_dir.is_dir():
        for candidate in sorted(p for p in threshold_unit_dir.rglob('*') if p.is_file()):
            result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for record in (rice_record, cdc_record, elastic_unit_record, cdc_native_record, cdc_sync_record, header_focus_record):
        for key in ('receipt', 'selection'):
            rel = record.get(key)
            if rel and (ROOT / rel).is_file():
                result['input_sha256'][rel] = file_hash(rel)
    for rel in [quant_focus_record.get('selected_report'), value_record.get('receipt')]:
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    for attempt in quant_focus_record.get('attempts', []):
        rel = attempt.get('receipt')
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    for lane in matrix_record['required_lanes']:
        rel = lane.get('results')
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    for record in (cdc_native_record, elastic_unit_record):
        for key in ('portable_audit', 'audit'):
            rel = record.get(key)
            if rel and (ROOT / rel).is_file():
                result['input_sha256'][rel] = file_hash(rel)
    for attempt in elastic_pipeline_record.get('attempts', []):
        rel = attempt.get('results')
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    for attempt in native_build_record.get('attempts', []):
        folder = ROOT / attempt['path']
        if folder.is_dir():
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for attempt in header_pipeline_record.get('attempts', []):
        folder = ROOT / attempt['path']
        if folder.is_dir():
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for attempt in tables_record.get('full_pipeline', {}).get('attempts', []):
        folder = ROOT / attempt['path']
        if folder.is_dir():
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for attempt in payload_record.get('full_payload_pipeline', {}).get('attempts', []):
        folder = ROOT / attempt['path']
        if folder.is_dir():
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for attempt in guard_record.get('full_pipeline', {}).get('attempts', []):
        folder = ROOT / attempt['path']
        if folder.is_dir():
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for label in ('guard-dsp', 'guard-pipeline'):
        area = ROOT / f'experiments/python-gamebub-v107/{label}'
        for candidate in sorted(p for p in area.rglob('*') if p.is_file()):
            if label == 'guard-dsp' or 'attempts' in candidate.parts:
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for label in ('meta-flags', 'meta-pipeline'):
        area = ROOT / f'experiments/python-gamebub-v107/{label}'
        for candidate in sorted(p for p in area.rglob('*') if p.is_file()):
            if label == 'meta-flags' or 'attempts' in candidate.parts:
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for label in ('plan-prefix', 'count-threshold', 'threshold-pipeline', 'threshold-runtime'):
        area = ROOT / f'experiments/python-gamebub-v107/{label}'
        for candidate in sorted(p for p in area.rglob('*') if p.is_file()):
            result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for attempt in tables_record.get('focus_attempt_history', []):
        rel = attempt.get('report')
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
            folder = (ROOT / rel).parent
            for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for label in ('payload-reset', 'idct-reset'):
        area = ROOT / f'experiments/python-gamebub-v107/{label}'
        for candidate in sorted(p for p in area.rglob('*') if p.is_file()):
            if 'native' in candidate.parts or 'attempts' in candidate.parts:
                result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    for key in ('behavioral_receipt', 'native_receipt'):
        rel = cdc_sync_record.get(key)
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
    for record, result_key in ((scale_record, 'behavioral'), (tables_record, 'selected_behavioral')):
        rel = record.get(result_key, {}).get('selected_report')
        if rel and (ROOT / rel).is_file():
            result['input_sha256'][rel] = file_hash(rel)
        for key in ('mapped_unit', 'readonly_lookup_probe'):
            rel = record.get(key, {}).get('receipt')
            if rel and (ROOT / rel).is_file():
                result['input_sha256'][rel] = file_hash(rel)
                folder = (ROOT / rel).parent
                for candidate in sorted(p for p in folder.rglob('*') if p.is_file()):
                    result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    observation_dir = ROOT / 'experiments/python-gamebub-v107/coordination/runtime-observation'
    if observation_dir.is_dir():
        for candidate in sorted(p for p in observation_dir.rglob('*') if p.is_file()):
            result['input_sha256'][str(candidate.relative_to(ROOT))] = sha256(candidate)
    if (any(x["status"] == "AUDIT_ERROR" for x in resume_records)
        or any(x['status'] == 'AUDIT_ERROR' for x in (rice_record, cdc_record, quant_focus_record, value_record,
                                                       elastic_unit_record, cdc_native_record, cdc_sync_record, header_focus_record))
        or native_build_record['status'] == 'AUDIT_ERROR'
        or scale_record['status'] == 'AUDIT_ERROR'
        or tables_record['status'] == 'AUDIT_ERROR'
        or payload_record['status'] == 'AUDIT_ERROR'
        or guard_record['status'] == 'AUDIT_ERROR'
        or meta_record['status'] == 'AUDIT_ERROR'
        or prefix_record['status'] == 'AUDIT_ERROR'
        or count_threshold_record['status'] == 'AUDIT_ERROR'
        or threshold_activation_record['status'] == 'AUDIT_ERROR'
        or threshold_runtime_activation_record['status'] == 'AUDIT_ERROR'):
        result["status"] = "AUDIT_ERRORS"
    elif (any(x["pending"] for x in resume_records) or not matrix_record['complete']
          or elastic_pipeline_record['status'] == 'PENDING_ELASTIC_FULL_PIPELINE'
          or native_build_record['status'] == 'PENDING_NATIVE_BUILDS'
          or header_pipeline_record['status'] == 'PENDING_HEADER_PIPELINE'
          or tables_record['status'] == 'PENDING_TABLES_FULL_EVIDENCE'
          or payload_record['status'] == 'PENDING_PAYLOAD_RESET_COMPONENT_PROOFS'
          or payload_record.get('full_payload_pipeline', {}).get('status') == 'PENDING_PAYLOAD_FULL_EVIDENCE'
          or guard_record.get('full_pipeline', {}).get('status') == 'PENDING_GUARD_FULL_EVIDENCE'
          or meta_record.get('full_pipeline', {}).get('status') == 'PENDING_META_FULL_EVIDENCE'
          or prefix_record['status'] == 'PENDING_PREFIX_QUALIFICATION'
          or count_threshold_record['status'] == 'PENDING_COUNT_THRESHOLD_QUALIFICATION'
          or threshold_pipeline_record['status'] == 'PENDING_THRESHOLD_FULL_EVIDENCE'
          or (threshold_activation_record['status'] == 'PASS_THRESHOLD_NATIVE_ACTIVATION_AUDITED'
              and any(a.get('variant') == 'threshold' and a.get('status') == 'PENDING'
                      for a in native_build_record.get('attempts', [])))
          or (threshold_runtime_activation_record.get('status') == 'PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED'
              and any(a.get('variant') == 'threshold-runtime' and a.get('status') == 'PENDING'
                      for a in native_build_record.get('attempts', [])))):
        result["status"] = "PENDING_REQUIRED_EVIDENCE"
    elif native_build_record['status'] == 'TERMINAL_NATIVE_EVIDENCE_RETAINED_NO_TIMING_PASS':
        result['status'] = 'TERMINAL_NATIVE_EVIDENCE_RETAINED_NO_TIMING_PASS'
    elif any(x["status"] == "TERMINAL_FAILURE_RETAINED" for x in resume_records):
        result["status"] = "TERMINAL_FAILURE_RETAINED_PENDING_OTHER_EVIDENCE" if not matrix_record['complete'] else "TERMINAL_FAILURE_RETAINED"
    elif any((rice_record['status'] != 'PASS_ACTUAL_RICE_AUDITED',
              cdc_record['status'] != 'PASS_BEHAVIORAL_CDC_AUDITED',
              quant_focus_record['status'] != 'PASS_QUANT_FOCUS_AUDITED',
              value_record['status'] != 'PASS_VALUE_EXPRESSION_AUDITED')):
        result['status'] = 'AUDIT_ERRORS'
    else:
        result['status'] = 'PASS_V107_REQUIRED_EVIDENCE'
    threshold_native_pending = any(
        a.get('variant') == 'threshold' and a.get('status') == 'PENDING'
        for a in native_build_record.get('attempts', []))
    threshold_runtime_pending = any(
        a.get('variant') == 'threshold-runtime' and a.get('status') == 'PENDING'
        for a in native_build_record.get('attempts', []))
    result['audit_phase'] = ('INTERIM_PENDING_THRESHOLD_RUNTIME_ROUTE' if threshold_runtime_pending else
                             'INTERIM_PENDING_THRESHOLD_NATIVE_ROUTE' if threshold_native_pending
                             else 'TERMINAL_EVIDENCE_READOUT')
    if threshold_runtime_activation_record.get('activation_record'):
        pre_native_path = ROOT / 'experiments/python-gamebub-v107/coordination/threshold-runtime-pre-native-audit.json'
        pre_native = {'schema': 'v107-threshold-runtime-pre-native-audit-v1',
            'status': threshold_runtime_activation_record.get('status'),
            'activation_record': threshold_runtime_activation_record.get('activation_record'),
            'activation_sha256': threshold_runtime_activation_record.get('activation_sha256'),
            'prepared_preflight': threshold_runtime_activation_record.get('prepared_preflight'),
            'prepared_preflight_sha256': threshold_runtime_activation_record.get('prepared_preflight_sha256'),
            'checks': threshold_runtime_activation_record.get('checks', {}),
            'auditor': 'scripts/cu66-v107/audit.py', 'auditor_sha256': sha256(Path(__file__).resolve()),
            'native_job_launched_by_auditor': False,
            'scope': threshold_runtime_activation_record.get('scope')}
        pre_native_path.write_text(json.dumps(pre_native, indent=2, sort_keys=True) + '\n')
        result['input_sha256'][str(pre_native_path.relative_to(ROOT))] = sha256(pre_native_path)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks,
                      "resume_attempts": [{"receipt": x["receipt"], "status": x["status"], "pending": x["pending"], "errors": x.get("errors", [])} for x in resume_records],
                      "rice_probe": rice_record['status'], "cdc_selection": cdc_record['status'],
                      "quant_focus": quant_focus_record['status'], "value_expression": value_record['status'],
                      "elastic_unit": elastic_unit_record['status'], "cdc_native": cdc_native_record['status'],
                      "cdc_sync": cdc_sync_record['status'],
                      "elastic_pipeline": elastic_pipeline_record['status'],
                      "header_focus": header_focus_record['status'],
                      "header_pipeline": header_pipeline_record['status'],
                      "native_builds": native_build_record['status'],
                      "scale_ram": scale_record['status'], "tables_ram": tables_record['status'],
                      "payload_reset": payload_record['status'],
                      "guard_dsp": guard_record['status'],
                      "guard_pipeline": guard_record.get('full_pipeline', {}).get('status'),
                      "meta_flags": meta_record['status'],
                      "meta_pipeline": meta_record.get('full_pipeline', {}).get('status'),
                      "prefix_qualification": prefix_record['status'],
                      "count_threshold": count_threshold_record['status'],
                      "threshold_pipeline": threshold_pipeline_record['status'],
                      "threshold_native_activation": threshold_activation_record['status'],
                      "threshold_runtime_activation": threshold_runtime_activation_record['status'],
                      "matrix": matrix_record['status'],
                      "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
