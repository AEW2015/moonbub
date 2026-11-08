#!/usr/bin/env python3
"""Select a measured next-study source and summarize the V105 evidence."""
import hashlib
import json
from pathlib import Path
# Resolve this local helper before regress adds the shared V100 tool directory.
from bundle_manifest import audited_sha
from regress import BASELINE, BASELINE_OVERRIDES, LANES, OVERRIDES, ROOT

AREA = ROOT / 'experiments/python-gamebub-v105'


def obj(path):
    return json.loads(path.read_text())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(name, result):
    (AREA / name).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')


def main():
    source, native = [obj(AREA / n) for n in ('source-audit.json', 'native-audit.json')]
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert source['baseline_revision'] == native['baseline_revision'] == BASELINE
    for audit in (source, native):
        inputs = audit.get('input_hashes', audit.get('input_sha256'))
        assert isinstance(inputs, dict) and inputs
        for name, digest in inputs.items():
            assert audited_sha(name) == digest, ('audited input drift', name)
    paths = obj(AREA / 'path-analysis.json')
    assert paths['status'] == 'PASS_EVIDENCE'
    assert paths['native_audit'] == pin(AREA / 'native-audit.json')
    methodology = obj(AREA / 'methodology-resolution.json')
    assert methodology['status'] == 'SIGNOFF_OPEN'
    assert methodology['native_audit'] == pin(AREA / 'native-audit.json')
    admission = obj(AREA / 'admission/results.json')
    assert admission['status'] == admission['trace_replay']['status'] == 'PASS'
    memory_selection = obj(AREA / 'memory/probe-results.json')
    memory = obj(ROOT / memory_selection['selected_receipt'])
    assert memory_selection['status'] == memory['status'] == 'PASS_ACTUAL_CLOCKED_MODE_EQUIVALENCE'
    assert pin(ROOT / memory_selection['selected_receipt'])['sha256'] == memory_selection['sha256']
    memory_trace = obj(AREA / 'memory/trace-audit.json')
    assert memory_trace['status'] == 'PASS_INDEPENDENT_MODE_REPLAY'
    composition = obj(AREA / 'composition.json')
    assert composition['status'] == 'PASS' and composition['both_orders_identical']
    assert pin(ROOT / composition['candidate'])['sha256'] == composition['candidate_sha256']
    lanes = []
    for variant, mode in LANES:
        path = AREA / 'regression' / variant / mode / 'results.json'
        result = obj(path)
        assert result['status'] == 'PASS' and result['exact_same_seed_transcripts_events_cycles']
        lanes.append(dict(**pin(path), variant=variant, mode=mode,
                          case_profile_runs=result['case_profile_runs'],
                          directed_checks=result['directed_checks']))
    variants = []
    for attempt in native['attempts']:
        stages = {}
        for stage, value in attempt.get('stages', {}).items():
            dequant = [row for row in value['DSP_registers'] if '/dequant/' in row['instance']]
            mode_ram = [row for row in value['RAM_configuration'] if '/modes' in row['instance']]
            stages[stage] = dict(resources=value['hierarchy'][0], capacity=value['capacity'],
                timing=value['timing'], DRC_reported=value['DRC_reported'],
                methodology_reported=value['methodology_reported'],
                dequant_DSP_count=len(dequant),
                dequant_PREG_enabled=sum(row['PREG'] == '1' for row in dequant),
                mode_RAM_primitive_rows=mode_ram)
        variants.append(dict(variant=attempt['variant'], receipt=pin(ROOT / attempt['path']),
            status=attempt['status'], stages=stages,
            routing_legality=attempt.get('routing_legality'),
            component_internal_timing_target_met=attempt.get('component_internal_timing_target_met', False)))
    baseline = native['V102_control']['stages']['route']
    eligible = []
    for name, row in native['measured_variants'].items():
        stage = row.get('stages', {}).get('route')
        if not stage or not row.get('component_route_finished'):
            continue
        timing = stage['timing']
        if (row.get('routing_legality', {}).get('reported_zero_errors_and_complete')
                and all(v['used'] <= v['available'] for v in stage['capacity'].values())
                and stage['check_timing'].get('no_clock', -1) == 0
                and stage['check_timing'].get('unconstrained_internal_endpoints', -1) == 0
                and timing['WHS_ns'] >= 0 and timing['WPWS_ns'] >= 0
                and timing['hold_failing'] == 0 and timing['pulse_failing'] == 0
                and timing['WNS_ns'] > baseline['timing']['WNS_ns']):
            eligible.append((name, row))
    if eligible:
        name, chosen = max(eligible, key=lambda item: (
            item[1]['stages']['route']['timing']['WNS_ns'],
            -item[1]['stages']['route']['hierarchy'][0]['total_LUT'],
            -item[1]['stages']['route']['hierarchy'][0]['DSP']))
        resources = chosen['stages']['route']['hierarchy'][0]
        timing, receipt = chosen['stages']['route']['timing'], chosen['path']
    else:
        name, chosen = 'baseline', None
        resources, timing, receipt = baseline['resources'], baseline['timing'], native['V102_control']['receipt']
    overrides = {**BASELINE_OVERRIDES, **OVERRIDES.get(name, {})}
    gain = round(timing['WNS_ns'] - baseline['timing']['WNS_ns'], 3)
    selection = dict(schema='v105-next-study-source-selection-v1', baseline_revision=BASELINE,
        selected_variant=name,
        selection_rule='Require completed error-free component routing, resource fit on exact target, no unclocked or unconstrained internal endpoints, nonnegative hold/pulse slack, exact workload cycle parity and strictly better routed setup WNS than selected V102. Record all costs/headroom. Prefer highest WNS, then lowest LUT/DSP. Otherwise retain V102.',
        source_overrides=overrides,
        source_sha256={path: pin(ROOT / path)['sha256'] for path in overrides.values()},
        selected_receipt=pin(ROOT / receipt), resources=resources, timing=timing,
        resource_delta_from_V102={key: resources[key] - baseline['resources'][key]
            for key in ('total_LUT', 'LUTRAM', 'FF', 'RAMB36', 'RAMB18', 'DSP')},
        setup_WNS_change_from_V102_ns=gain,
        single_run_gain_is_robustness_proof=False,
        native_audit=pin(AREA / 'native-audit.json'),
        scope='Next-study source choice only. No production/hardware or parent-clock/I/O signoff.')
    write('selection.json', selection)
    result = dict(schema='v105-admission-memory-checkpoint-v1', baseline_revision=BASELINE,
        branch='study/gamebub-v105-admission-memory-20261107',
        status='PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN',
        codec_profile_unchanged=True, resolution=[720, 480], packet_cap_bytes=49152,
        cycle_schedule_unchanged_in_selected_tests=True, compression_or_quality_gain_measured=False,
        paired_regression=dict(lanes=lanes,
            total_case_profile_runs=sum(v['case_profile_runs'] for v in lanes),
            total_directed_checks=sum(v['directed_checks'] for v in lanes),
            scope='Baseline/candidate x seeds x profiles including expected rejects; not distinct displayed frames or hardware FPS.'),
        focused=dict(admission=pin(AREA / 'admission/results.json'),
            admission_clock_edges=admission['terminal_verdict']['clock_edges'],
            admission_verdict=admission['terminal_verdict'], admission_trace_replay=admission['trace_replay'],
            memory=pin(ROOT / memory_selection['selected_receipt']),
            memory_clock_edges=memory['total_clock_edges'], memory_cases=memory['total_cases'],
            memory_trace=pin(AREA / 'memory/trace-audit.json'),
            total_clock_edges=admission['terminal_verdict']['clock_edges'] + memory['total_clock_edges'],
            scope='Clocked two-state component tests and independent Python replay; memory probe prepares internal states explicitly. Not formal/four-state/mapped-netlist proof.'),
        composition=pin(AREA / 'composition.json'),
        measured_setup_cones=pin(AREA / 'path-analysis.json'),
        methodology_resolution=pin(AREA / 'methodology-resolution.json'),
        native=dict(vendor='Vivado 2026.1 build 6511674', part='xc7a100tcsg324-1',
            comparison_clock_period_ns=10, control=native['V102_control'], variants=variants,
            scope='Single-clock OOC component; parent clock/boundary/I/O and external-memory service contracts unknown.'),
        audits=[pin(AREA / n) for n in ('source-audit.json', 'native-audit.json', 'baseline-audit.json')],
        next_study_selection=pin(AREA / 'selection.json'),
        qualification=dict(scope='Selected next-study source only; per-variant outcomes remain separate.',
            component_route_finished=bool(chosen['component_route_finished']) if chosen else True,
            component_100MHz_internal_timing_target_met=(chosen['component_internal_timing_target_met'] if chosen else False),
            parent_clock_boundary_IO_qualified=False, methodology_DRC_CDC_signed_off=False,
            complete_custom_path_integrated=False, whole_device_memory_service_qualified=False,
            hardware_30fps_validated=False, complete_FPGA_decode_under10ms_validated=False,
            achieved_Fmax_Hz=None, hardware_test_performed=False))
    assert result['paired_regression']['total_case_profile_runs'] == 512
    assert result['paired_regression']['total_directed_checks'] == 576
    write('summary.json', result)
    print('V105_SUMMARY', result['status'], 'paired', 512, 'directed', 576, 'selected', name)


if __name__ == '__main__':
    main()
