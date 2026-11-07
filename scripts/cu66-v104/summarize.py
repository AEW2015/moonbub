#!/usr/bin/env python3
"""Summarize verified V104 cycle-preserving control/DSP experiments."""
import hashlib
import json
from pathlib import Path
from regress import BASELINE_OVERRIDES, OVERRIDES

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v104'
BASELINE = '1d0a702a758787522723ac52ff44a1bf220c39d1'


def obj(path):
    return json.loads(path.read_text())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    source, native = [obj(AREA / n) for n in ('source-audit.json', 'native-audit.json')]
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert source['baseline_revision'] == native['baseline_revision'] == BASELINE
    control, dsp = [obj(AREA / k / 'results.json') for k in ('control', 'dsp')]
    assert control['status'] == dsp['status'] == 'PASS'
    coordinates = obj(AREA / 'admission-coordinate-model.json')
    assert coordinates['status'] == 'PASS'
    for ref in (coordinates['script'], coordinates['source']):
        assert pin(ROOT / ref['path'])['sha256'] == ref['sha256']
    lanes = []
    for variant, mode in [('control', 'canonical'), ('dsp', 'fresh'),
                          ('dsp', 'canonical'), ('combined', 'canonical')]:
        path = AREA / 'regression' / variant / mode / 'results.json'
        result = obj(path)
        assert result['status'] == 'PASS' and result['exact_same_seed_transcripts_events_cycles']
        lanes.append(dict(**pin(path), variant=variant, mode=mode,
                          case_profile_runs=result['case_profile_runs'],
                          directed_checks=result['directed_checks']))
    variants = []
    for a in native['attempts']:
        stages = {}
        for stage, value in a['stages'].items():
            dequant = [row for row in value['DSP_registers'] if '/dequant/' in row['instance']]
            inverse = [row for row in value['DSP_registers'] if '/inverse/' in row['instance']]
            stages[stage] = dict(resources=value['hierarchy'][0], capacity=value['capacity'],
                timing=value['timing'], DRC_reported=value['DRC_reported'],
                methodology_reported=value['methodology_reported'],
                dequant_DSP_count=len(dequant),
                dequant_PREG_enabled=sum(row['PREG'] == '1' for row in dequant),
                dequant_MREG_enabled=sum(row['MREG'] == '1' for row in dequant),
                inverse_DSP_count=len(inverse))
        variants.append(dict(variant=a['variant'], receipt=pin(ROOT / a['path']),
            status=a['status'], stages=stages, routing_legality=a.get('routing_legality'),
            component_internal_timing_target_met=a['component_internal_timing_target_met']))
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
    selection = dict(schema='v104-next-study-source-selection-v1', baseline_revision=BASELINE,
        selected_variant=name,
        selection_rule='Require completed error-free component routing, resource fit on exact target, no unclocked or unconstrained internal endpoints, nonnegative hold/pulse slack, exact workload cycle parity and strictly better routed setup WNS than selected V102. Pipeline state may increase resources; record all costs/headroom. Prefer highest WNS, then lowest LUT/DSP. Otherwise retain V102.',
        source_overrides=overrides,
        source_sha256={path: pin(ROOT / path)['sha256'] for path in overrides.values()},
        selected_receipt=pin(ROOT / receipt), resources=resources, timing=timing,
        resource_delta_from_V102={key: resources[key] - baseline['resources'][key]
            for key in ('total_LUT', 'LUTRAM', 'FF', 'RAMB36', 'RAMB18', 'DSP')},
        native_audit=pin(AREA / 'native-audit.json'),
        scope='Next-study source choice only. No production/hardware or genuine parent-clock/I/O signoff.')
    (AREA / 'selection.json').write_text(json.dumps(selection, indent=2, sort_keys=True) + '\n')
    result = dict(schema='v104-control-dsp-checkpoint-v1', baseline_revision=BASELINE,
        branch='study/gamebub-v104-control-dsp-20261107',
        status='PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN',
        codec_profile_unchanged=True, resolution=[720, 480], packet_cap_bytes=49152,
        cycle_schedule_unchanged_in_selected_tests=True, compression_or_quality_gain_measured=False,
        paired_regression=dict(lanes=lanes,
            total_case_profile_runs=sum(v['case_profile_runs'] for v in lanes),
            total_directed_checks=sum(v['directed_checks'] for v in lanes),
            scope='Baseline/candidate x seeds x profiles, including expected rejects; not distinct displayed frames or hardware FPS.'),
        focused=dict(control=pin(AREA / 'control/results.json'), dsp=pin(AREA / 'dsp/results.json'),
            control_clock_edges=control['clock_edges'], dsp_clock_edges=dsp['clock_edges'],
            total_clock_edges=control['clock_edges'] + dsp['clock_edges'],
            control_terminal_verdict=control['terminal_verdict'],
            dsp_public_samples=dsp['public_samples'], dsp_packed_element_comparisons=dsp['packed_element_comparisons'],
            trace_audits=[pin(AREA / k / 'trace-audit.json') for k in ('control', 'dsp')],
            failed_attempt_ledgers=[pin(AREA / k / 'failed-attempts.json') for k in ('control', 'dsp')],
            scope='Clocked two-state component tests and independent Python replay, not full formal/four-state/mapped-netlist proof.'),
        admission_coordinate_model=dict(receipt=pin(AREA / 'admission-coordinate-model.json'),
            counts=coordinates['counts'], scope=coordinates['limits']),
        native=dict(vendor='Vivado 2026.1 build 6511674', part='xc7a100tcsg324-1',
            comparison_clock_period_ns=10, control=native['V102_control'], variants=variants,
            scope='Single-clock OOC component; parent clock/boundary/I/O contracts unknown. Stage-matched measurements only.'),
        audits=[pin(AREA / n) for n in ('source-audit.json', 'native-audit.json', 'baseline-audit.json')],
        next_study_selection=pin(AREA / 'selection.json'),
        qualification=dict(scope='Selected next-study source only; per-variant outcomes remain separate.',
            component_route_finished=True, routable_nets_all_routed=True,
            component_100MHz_internal_timing_target_met=(chosen['component_internal_timing_target_met'] if chosen else False),
            parent_clock_boundary_IO_qualified=False, methodology_DRC_CDC_signed_off=False,
            complete_custom_path_integrated=False, hardware_30fps_validated=False,
            complete_FPGA_decode_under10ms_validated=False, achieved_Fmax_Hz=None,
            hardware_test_performed=False))
    assert result['paired_regression']['total_case_profile_runs'] == 288
    assert result['paired_regression']['total_directed_checks'] == 304
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V104_SUMMARY', result['status'], 'paired', 288, 'directed', 304, 'selected', name)


if __name__ == '__main__':
    main()
