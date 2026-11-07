#!/usr/bin/env python3
"""Audit retained V104 native variants without vendor tools or external DCPs.

PASS_EVIDENCE verifies recorded inputs/reports and terminal outcomes, including
honest failures. It does not mean a design fits, closes timing, or runs at FPS.
"""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v104'
BASELINE = '1d0a702a758787522723ac52ff44a1bf220c39d1'
MEMORY = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
RECONSTRUCT = 'fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv'
BASELINE_OVERRIDES = {
    MEMORY: 'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv',
    RECONSTRUCT: 'fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv',
}
OVERRIDES = {
    'dsp': {'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv': 'fpga/experiments/cu66-v104-dsp/cu66_dequant.sv'},
    'control': {RECONSTRUCT: 'fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv'},
}
OVERRIDES['combined'] = {**OVERRIDES['dsp'], **OVERRIDES['control']}
INPUTS, CHECKS, ERRORS = {}, [], []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    path = Path(path)
    if path.is_absolute():
        path = path.relative_to(ROOT)
    data = (ROOT / path).read_bytes()
    INPUTS[str(path)] = sha(data)
    return data


def obj(path):
    return json.loads(read(path))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob(path):
    return subprocess.check_output(['git', '-C', str(ROOT), 'show', BASELINE + ':' + str(path)])


def hierarchy(data):
    result = []
    for line in data.splitlines():
        fields = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(fields) == 10 and all(re.fullmatch(r'\d+', v) for v in fields[2:]):
            keys = ['total_LUT', 'logic_LUT', 'LUTRAM', 'SRL', 'FF', 'RAMB36', 'RAMB18', 'DSP']
            result.append(dict(instance=fields[0], module=fields[1], **dict(zip(keys, map(int, fields[2:])))))
    require(result and result[0]['instance'] == 'cs88_pipeline_v91k', 'missing hierarchical top row')
    return result


def capacity(data):
    wanted = {'Slice LUTs*', 'LUT as Logic', 'LUT as Memory', 'Slice Registers', 'Block RAM Tile', 'DSPs'}
    result = {}
    for line in data.splitlines():
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if cells[0] == 'Slice LUTs':
            cells[0] = 'Slice LUTs*'  # Native post-place tables omit the synthesis footnote marker.
        if len(cells) >= 6 and cells[0] in wanted:
            used = float(cells[1])
            result[cells[0]] = dict(used=int(used) if used.is_integer() else used, available=int(cells[-2]), util_percent=float(cells[-1]))
    require(set(result) == wanted, 'incomplete native flat capacity table')
    return result


def timing(data):
    start = data.index('| Design Timing Summary')
    for line in data[start:].splitlines():
        tokens = line.split()
        if len(tokens) == 12 and all(re.fullmatch(r'-?\d+(?:\.\d+)?', x) for x in tokens):
            names = ['WNS_ns', 'TNS_ns', 'setup_failing', 'setup_total', 'WHS_ns', 'THS_ns',
                     'hold_failing', 'hold_total', 'WPWS_ns', 'TPWS_ns', 'pulse_failing', 'pulse_total']
            return {k: float(v) if '_ns' in k else int(v) for k, v in zip(names, tokens)}
    raise ValueError('no design timing row')


def routing_legality(data):
    counts = {}
    for line in data.splitlines():
        match = re.match(r'^\s*(.*?)\s*:\s*([0-9,]+)\s*:', line)
        if match:
            label = re.sub(r'[.#\s]+', ' ', match[1]).strip().lower()
            counts[label] = int(match[2].replace(',', ''))
    find = lambda phrase: [v for k, v in counts.items() if re.search(r'\b' + re.escape(phrase) + r'\b', k)]
    errors, unrouted = find('routing errors'), find('unrouted')
    routable, fully = find('routable nets'), find('fully routed nets')
    difference = routable[0] - fully[0] if len(routable) == len(fully) == 1 else None
    require(difference is None or difference >= 0, 'inconsistent native route-status counts')
    literal = [line.strip() for line in data.splitlines() if re.search(r'(?:design|all nets).*(?:is|are|been).*fully routed', line, re.I)]
    error_free = bool(errors) and all(value == 0 for value in errors)
    complete = (difference is None or difference == 0) and all(value == 0 for value in unrouted) and (bool(unrouted) or difference == 0)
    return dict(reported_net_counts=counts, derived_unrouted_routable_nets=difference,
                literal_fully_routed_messages=literal,
                reported_zero_errors_and_complete=bool(error_free and complete),
                scope='Native route-status counts only; OOC routing legality is not board or methodology signoff.')


def finding_summary(data):
    rows = {}
    for line in data.splitlines():
        cells = [x.strip() for x in line.strip().strip('|').split('|')]
        if len(cells) == 4 and cells[1] in ('Error', 'Critical Warning', 'Warning', 'Advisory') and cells[3].isdigit():
            rows[cells[0]] = dict(severity=cells[1], reported=int(cells[3]))
    found = re.search(r'Checks found:\s*(\d+)', data)
    total = sum(row['reported'] for row in rows.values())
    require(found is None or total == int(found[1]), 'reported finding summary rows/count differ')
    return dict(by_rule=rows, total_reported=total,
                errors_reported=sum(row['reported'] for row in rows.values() if row['severity'] == 'Error'),
                per_rule_enumeration_limits_verified=False)


def pin_reference(reference):
    path = reference['path']
    data = read(path)
    require(sha(data) == reference['sha256'], 'reference changed: ' + path)
    return json.loads(data)


def baseline():
    selector = 'experiments/python-gamebub-v102/native-audit.json'
    data = read(selector)
    require(data == blob(selector), 'published V102 audit changed')
    selected = json.loads(data)
    require(selected['status'] == 'PASS_EVIDENCE', 'V102 evidence audit not passed')
    for name, digest in selected['input_hashes'].items():
        value = read(name)
        require(sha(value) == digest and value == blob(name), 'V102 bound input changed: ' + name)
    controls = [a for a in selected['attempts'] if a['variant'] == 'combined' and a['terminal']]
    require(len(controls) == 1, 'ambiguous V102 combined baseline')
    control = controls[0]
    stages = control['stages']
    require(control['component_route_finished'] and control['routing_legality']['reported_zero_errors_and_complete'], 'V102 route baseline missing')
    require(stages['synth']['hierarchy'][0]['total_LUT'] == 49040 and stages['route']['timing']['WNS_ns'] == -13.976, 'wrong V102 control')
    return dict(selector=selector, receipt=control['path'],
                synthesis=stages['synth']['hierarchy'][0],
                capacity=stages['synth']['capacity'], timing=stages['synth']['timing'],
                stages={k: dict(resources=v['hierarchy'][0], timing=v['timing']) for k,v in stages.items()},
                routing_legality=control['routing_legality'],
                source_top_public_port_names=308,
                scope='Published V102 combined component baseline; matched synthesis and route stage comparisons, parent boundary/clock and hardware gates open.')


def audit_attempt(path, frozen):
    folder = path.parent
    receipt = obj(path)
    inputs = obj(folder / 'inputs.json')
    variant = inputs['variant']
    require(variant in OVERRIDES or variant == 'baseline', 'unexpected variant ' + variant)
    require(inputs['baseline_revision'] == BASELINE, 'wrong source baseline')
    expected_overrides = {**BASELINE_OVERRIDES, **OVERRIDES.get(variant, {})}
    require(inputs['source_overrides'] == expected_overrides, 'unapproved override map')
    require(inputs['baseline_overrides'] == BASELINE_OVERRIDES, 'baseline source map changed')
    require(isinstance(inputs['synth_only'], bool), 'invalid native phase flag')
    require(variant != 'combined' or inputs['synth_only'] is False, 'combined experiment requires full implementation')
    source_names = set(frozen['rtl_sources'] + frozen['include_headers'])
    require(len(source_names) == 17, 'expected frozen 17-file source closure')
    require(set(inputs['source_origins']) == set(inputs['source_sha256']) == source_names, 'source closure differs')
    for name in source_names:
        original_data = read(name)
        require(original_data == blob(name), 'historical source changed: ' + name)
        origin = inputs['source_origins'][name]
        baseline_path = BASELINE_OVERRIDES.get(name, name)
        require(read(baseline_path) == blob(baseline_path), 'V102 baseline source changed')
        expected_path = expected_overrides.get(name, name)
        require(origin['path'] == expected_path, 'unexpected origin: ' + name)
        require(sha(read(expected_path)) == origin['sha256'] == inputs['source_sha256'][name], 'origin hash mismatch: ' + name)
    require(inputs['frozen_manifest'] == 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json', 'wrong frozen manifest')
    require(inputs['frozen_manifest_sha256'] == sha(read(inputs['frozen_manifest'])), 'frozen manifest changed')
    require(receipt['source_manifest_sha256'] == sha(read(folder / 'inputs.json')), 'prepared manifest hash differs')
    require(receipt['runner_sha256'] == sha(read(folder / 'run_vivado2026.py')), 'executed runner differs')
    require(receipt['part'] == 'xc7a100tcsg324-1' and receipt['clock_period_ns'] == 10.0, 'part/clock differs')
    require(receipt['clock_loaded_before_synthesis'] is True and receipt['max_threads'] == 2, 'flow controls differ')
    require(receipt['memory_limit_bytes'] == 8 * 1024**3, 'native memory limit changed')
    require(receipt['resource_before']['MemAvailable_bytes'] >= 8 * 1024**3 and receipt['resource_before']['PSI_full_avg10'] < 1, 'launch resource gate failed')
    require(set(receipt['recipe_snapshots_sha256']) == {'run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl'}, 'incomplete recipe snapshot set')
    for name, digest in receipt['recipe_snapshots_sha256'].items():
        require(sha(read(folder / 'recipe-snapshot' / name)) == digest == inputs['recipe_sha256'][name], 'recipe hash mismatch: ' + name)
    xdc = read(folder / 'recipe-snapshot/component.xdc').decode()
    active = '\n'.join(s for s in xdc.splitlines() if not s.lstrip().startswith('#'))
    require(active.strip() == 'create_clock -name component_clk -period 10.000 [get_ports clk]', 'comparison constraints changed')
    run_tcl = read(folder / 'recipe-snapshot/run.tcl').decode()
    require(run_tcl.index('read_xdc $constraint_file') < run_tcl.index('\nsynth_design '), 'clock loaded too late')
    active_run = {line.strip() for line in run_tcl.splitlines() if not line.lstrip().startswith('#')}
    expected_flow = {'set_param general.maxThreads 2', 'set_property verilog_define SYNTHESIS [current_fileset]',
        'synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default',
        'opt_design -directive Default', 'place_design -directive Default', 'route_design -directive Default'}
    require(expected_flow <= active_run, 'matched native flow settings changed')
    require(not re.search(r'phys_opt_design|set_false_path|set_clock_groups|create_waiver|disableLUTOverUtilError| -retiming', '\n'.join(active_run)), 'unmatched physical override or exception')
    initial = dict(path=str(path.relative_to(ROOT)), variant=variant, status=receipt['status'],
                   inputs_sha256=sha(read(folder / 'inputs.json')), source_origins=inputs['source_origins'],
                   source_files=len(source_names), synth_only=inputs['synth_only'])
    if receipt['status'] == 'RUNNING':
        return {**initial, 'terminal': False, 'scope': 'RUNNING; no final artifact or performance verdict'}
    require(receipt['status'] in {'SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN', 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN', 'TOOL_OR_BUILD_FAILED', 'STOPPED_RESOURCE_OR_TIME_GATE'}, 'unknown terminal outcome')
    log = read(folder / 'vivado.log').decode(errors='replace')
    require(sha(read(folder / 'vivado.log')) == receipt['log_sha256'], 'native transcript changed')
    require(receipt['source_snapshot_unchanged'] is True, 'prepared source changed during execution')
    version_verified = 'Vivado v2026.1' in log and 'SW Build 6511674' in log
    if receipt['synthesis_started']:
        require(version_verified, 'vendor version differs from baseline')
    require(isinstance(receipt['observed_exit_code'], int) and bool(log.strip()), 'terminal job lacks exit code/transcript')
    require(not receipt['hardware_contact'] and not receipt['bitstream_generated'] and not receipt['board_IO_timing_qualified'], 'unsupported hardware qualification')
    reports, external = {}, []
    retained_names = {p.name for p in (folder / 'reports').iterdir() if p.is_file()}
    require(retained_names <= set(receipt['artifacts']), 'unbound retained report copy')
    for name, artifact in receipt['artifacts'].items():
        require(re.fullmatch(r'[0-9a-f]{64}', artifact['sha256']) and artifact['bytes'] > 0, 'invalid artifact checksum')
        copy = folder / 'reports' / name
        if copy.exists():
            data = read(copy)
            require(sha(data) == artifact['sha256'] and len(data) == artifact['bytes'], 'native report changed: ' + name)
            reports[name] = data.decode(errors='replace')
        else:
            require(name.endswith('.dcp') or artifact['bytes'] >= 8 * 1024**2, 'missing retained report: ' + name)
            external.append(dict(name=name, sha256=artifact['sha256'], bytes=artifact['bytes'], verification='Checksum recorded; unbundled output not required'))
    if 'part-query.txt' in reports:
        require('version=2026.1' in reports['part-query.txt'] and 'part=xc7a100tcsg324-1 count=1' in reports['part-query.txt'], 'actual native part query differs')
    result = {**initial, 'terminal': True, 'exit_code': receipt['observed_exit_code'], 'copied_reports_verified': len(reports),
              'vendor_version_verified_from_log': version_verified,
              'unbundled_artifact_policy': 'Retained copies verified; external DCP/license files never read or required.',
              'external_outputs': external, 'synthesis_checkpoint_written': receipt['synthesis_checkpoint_written'],
              'placement_reports_present': receipt['placement_reports_present'], 'component_route_finished': receipt['component_route_finished'],
              'native_build_source_snapshot_unchanged': receipt['source_snapshot_unchanged'], 'stages': {},
              'hardware_30fps': False, 'complete_validated_decode_under10ms': False, 'board_IO_timing_qualified': False}
    for stage in ('synth', 'place', 'route'):
        measured = {}
        if stage + '-utilization.rpt' in reports:
            resource_report = reports[stage + '-utilization.rpt']
            require(re.search(r'\| Device\s*:\s*xc7a100tcsg324-1\s*$', resource_report, re.M), 'native resource report device differs')
            measured['hierarchy'] = hierarchy(resource_report)
        if stage + '-capacity.rpt' in reports:
            measured['capacity'] = capacity(reports[stage + '-capacity.rpt'])
        if stage + '-timing-summary.rpt' in reports:
            summary = reports[stage + '-timing-summary.rpt']
            measured['timing'] = timing(summary)
            clock = re.search(r'^component_clk\s+\{[^}]+\}\s+(\d+\.\d+)\s+', summary, re.M)
            require(clock is not None and float(clock[1]) == 10.0, 'native report clock differs from target')
        for label, suffix in [('RAM_configuration', '-ram-config.tsv'), ('DSP_registers', '-dsp-registers.tsv')]:
            if stage + suffix in reports:
                measured[label] = list(csv.DictReader(reports[stage + suffix].splitlines(), delimiter='\t'))
        if 'capacity' in measured:
            measured['synthesized_capacity_within_reported_limits'] = all(row['used'] <= row['available'] for row in measured['capacity'].values())
        if 'hierarchy' in measured and 'capacity' in measured:
            require(measured['hierarchy'][0]['total_LUT'] == measured['capacity']['Slice LUTs*']['used'], 'resource table discrepancy')
            require(measured['hierarchy'][0]['DSP'] == measured['capacity']['DSPs']['used'], 'DSP table discrepancy')
        if 'DSP_registers' in measured and 'hierarchy' in measured:
            require(len(measured['DSP_registers']) == measured['hierarchy'][0]['DSP'], 'DSP primitive ledger discrepancy')
            require(all(row.get('primitive') == 'DSP48E1' for row in measured['DSP_registers']), 'invalid DSP TSV structure')
        if 'RAM_configuration' in measured and 'hierarchy' in measured:
            ram = measured['RAM_configuration']
            require(all('RAM_MODE' in row and row.get('REF_NAME') in ('RAMB36E1', 'RAMB18E1') for row in ram), 'invalid RAM TSV structure')
            require(sum(row['REF_NAME'] == 'RAMB36E1' for row in ram) == measured['hierarchy'][0]['RAMB36'], 'RAMB36 ledger discrepancy')
            require(sum(row['REF_NAME'] == 'RAMB18E1' for row in ram) == measured['hierarchy'][0]['RAMB18'], 'RAMB18 ledger discrepancy')
        for label, suffix in [('DRC_reported', '-drc.rpt'), ('methodology_reported', '-methodology.rpt')]:
            if stage + suffix in reports:
                measured[label] = finding_summary(reports[stage + suffix])
        if stage + '-check-timing.rpt' in reports:
            measured['check_timing'] = {name: int(value) for name, value in re.findall(r'^\s*\d+\. checking (\w+) \((\d+)\)', reports[stage + '-check-timing.rpt'], re.M)}
        if measured:
            measured['scope'] = 'Synthesized estimate; no placed/routed speed' if stage == 'synth' else 'Placed estimate; route not implied' if stage == 'place' else 'Routed OOC component only; board I/O/full-system gates remain open'
            result['stages'][stage] = measured
    require(receipt['status'] != 'SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN' or receipt.get('synthesis_only_finished'), 'synth success lacks terminal flag')
    require(receipt['status'] != 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' or receipt['component_route_finished'], 'route success lacks terminal flag')
    completed_stages = ('synth', 'place', 'route') if receipt['component_route_finished'] else ('synth',) if receipt.get('synthesis_only_finished') else ()
    for stage in completed_stages:
        require(all(stage + suffix in reports for suffix in ('-utilization.rpt', '-capacity.rpt', '-timing-summary.rpt', '-ram-config.tsv', '-dsp-registers.tsv')), 'completed stage lacks required reports: ' + stage)
    if receipt['component_route_finished']:
        require(receipt['observed_exit_code'] == 0 and 'route-status.rpt' in reports, 'route success lacks exit/report evidence')
    if receipt.get('synthesis_only_finished'):
        require(inputs['synth_only'] is True and receipt['observed_exit_code'] == 0 and 'V104_SYNTH_ONLY_FINISHED' in log, 'synth-only terminal mismatch')
    if receipt['component_route_finished']:
        require(inputs['synth_only'] is False and receipt['routing_checkpoint_written'] and 'V104_COMPONENT_ROUTE_FINISHED' in log and 'route' in result['stages'], 'route terminal mismatch')
    result['route_Fmax_Hz'] = None
    route_timing = result['stages'].get('route', {}).get('timing', {})
    result['component_internal_timing_target_met'] = bool(receipt['component_route_finished'] and all(route_timing.get(k, -1) >= 0 for k in ('WNS_ns', 'WHS_ns', 'WPWS_ns')) and all(route_timing.get(k, -1) == 0 for k in ('setup_failing', 'hold_failing', 'pulse_failing')))
    if 'route-status.rpt' in reports:
        result['routing_legality'] = routing_legality(reports['route-status.rpt'])
    result['methodology_DRC_CDC_signoff'] = False
    return result


def main():
    reference = None
    attempts = []
    try:
        reference = baseline()
        frozen_path = 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'
        require(read(frozen_path) == blob(frozen_path), 'historical source closure manifest changed')
        frozen = obj(frozen_path)
        CHECKS.append(dict(name='V102_reference_reports_and_frozen_control', status='PASS'))
        for path in sorted((AREA / 'native').glob('*/receipt.json')):
            try:
                row = audit_attempt(path, frozen)
                synth = row.get('stages', {}).get('synth', {})
                if synth.get('hierarchy'):
                    current, control = synth['hierarchy'][0], reference['synthesis']
                    row['synthesized_change_from_V102'] = {
                        'counts': {key: current[key] - control[key] for key in ('total_LUT', 'logic_LUT', 'LUTRAM', 'FF', 'RAMB36', 'RAMB18', 'DSP')},
                        'total_LUT_percent': round(100 * (current['total_LUT'] - control['total_LUT']) / control['total_LUT'], 3),
                        'WNS_change_ns': round(synth['timing']['WNS_ns'] - reference['timing']['WNS_ns'], 3) if 'timing' in synth else None,
                        'scope': 'Synthesis-stage counts/estimates only, same target/tool/10ns comparison clock; not hardware speed or full-system throughput.'}
                attempts.append(row)
                CHECKS.append(dict(name='native_attempt:' + path.parent.name, status='PASS' if row['terminal'] else 'PENDING'))
            except (KeyError, ValueError, FileNotFoundError, subprocess.CalledProcessError) as error:
                ERRORS.append(dict(path=str(path.relative_to(ROOT)), error=str(error)))
                CHECKS.append(dict(name='native_attempt:' + path.parent.name, status='FAIL'))
    except (KeyError, ValueError, FileNotFoundError, subprocess.CalledProcessError) as error:
        ERRORS.append(dict(path='baseline', error=str(error)))
    selected = {}
    for variant in OVERRIDES:
        rows = [row for row in attempts if row['variant'] == variant]
        selected[variant] = rows[-1] if rows else {'variant': variant, 'terminal': False, 'status': 'MISSING'}
    pending = [variant for variant, row in selected.items() if not row['terminal']]
    status = 'AUDIT_ERRORS' if ERRORS else 'PENDING' if pending else 'PASS_EVIDENCE'
    result = dict(schema='v104-native-evidence-audit-v1', status=status, baseline_revision=BASELINE,
                  auditor=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha(Path(__file__).read_bytes())),
                  input_hashes=dict(sorted(INPUTS.items())), checks=CHECKS, errors=ERRORS,
                  V102_control=reference, attempts=attempts, measured_variants=selected, pending_variants=pending,
                  scope='Retained provenance/native reports only; failed tool outcomes remain failures. No external DCP/license requirement, hardware FPS, full custom top or complete decode latency qualification.')
    (AREA / 'native-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V104_NATIVE_AUDIT', status, 'checks', len(CHECKS), 'errors', len(ERRORS), 'pending', pending)
    return 1 if ERRORS else 0


if __name__ == '__main__':
    raise SystemExit(main())
