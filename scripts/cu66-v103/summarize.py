#!/usr/bin/env python3
"""Summarize verified V103 receipts without inferring hardware performance."""
import hashlib
import json
from pathlib import Path
from regress import BASELINE_OVERRIDES, OVERRIDES

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v103'
BASELINE = '6d2ca3ae9abe207215d6130cfb0087fd07928917'


def obj(path):
    return json.loads(path.read_text())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    source, native = [obj(AREA / n) for n in ('source-audit.json', 'native-audit.json')]
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert source['baseline_revision'] == native['baseline_revision'] == BASELINE
    prefix = obj(AREA / 'parser-prefix-model.json')
    assert prefix['status'] == 'PASS' and prefix['counts']['model_comparisons'] == 1548910
    assert hashlib.sha256((ROOT / prefix['source']).read_bytes()).hexdigest() == prefix['source_sha256']
    assert hashlib.sha256((ROOT / 'scripts/cu66-v103/prefix_model.py').read_bytes()).hexdigest() == prefix['script_sha256']
    lanes = []
    for variant, mode in [('admission', 'fresh'), ('admission', 'canonical'),
                          ('reconstruct', 'canonical'), ('combined', 'canonical')]:
        path = AREA / 'regression' / variant / mode / 'results.json'
        result = obj(path)
        assert result['status'] == 'PASS' and result['exact_same_seed_transcripts_events_cycles']
        lanes.append(dict(**pin(path), variant=variant, mode=mode,
                          case_profile_runs=result['case_profile_runs'],
                          directed_checks=result['directed_checks']))
    variants = []
    for a in native['attempts']:
        variants.append(dict(variant=a['variant'], receipt=pin(ROOT / a['path']),
            status=a['status'],
            stages={stage: dict(resources=v['hierarchy'][0], timing=v['timing'],
                                DRC_reported=v['DRC_reported'],
                                methodology_reported=v['methodology_reported'])
                    for stage, v in a['stages'].items()},
            routing_legality=a.get('routing_legality'),
            component_internal_timing_target_met=a['component_internal_timing_target_met']))
    control = native['V102_control']['stages']['route']
    eligible = []
    for name, row in native['measured_variants'].items():
        stage = row.get('stages', {}).get('route')
        if not stage or not row.get('component_route_finished'):
            continue
        resource, timing = stage['hierarchy'][0], stage['timing']
        if (row.get('routing_legality', {}).get('reported_zero_errors_and_complete')
                and timing['WHS_ns'] >= 0 and timing['WPWS_ns'] >= 0
                and resource['total_LUT'] <= control['resources']['total_LUT']
                and (2 * resource['RAMB36'] + resource['RAMB18']
                     <= 2 * control['resources']['RAMB36'] + control['resources']['RAMB18'])
                and resource['DSP'] <= control['resources']['DSP']
                and timing['WNS_ns'] > control['timing']['WNS_ns']):
            eligible.append((name, row))
    if eligible:
        chosen_name, chosen = max(eligible, key=lambda item: (
            item[1]['stages']['route']['timing']['WNS_ns'],
            -item[1]['stages']['route']['hierarchy'][0]['total_LUT']))
        chosen_resources = chosen['stages']['route']['hierarchy'][0]
        chosen_timing = chosen['stages']['route']['timing']
        chosen_receipt = chosen['path']
    else:
        chosen_name, chosen = 'baseline', None
        chosen_resources, chosen_timing = control['resources'], control['timing']
        chosen_receipt = native['V102_control']['receipt']
    selection = dict(schema='v103-next-study-source-selection-v1',
        baseline_revision=BASELINE, selected_variant=chosen_name,
        selection_rule='Among completed routable candidates with nonnegative hold/pulse slack and no more LUT/weighted BRAM (2*RAMB36+RAMB18)/DSP than V102, require strictly better setup WNS than V102; prefer highest setup WNS then lowest LUT. Otherwise retain V102.',
        source_overrides={**BASELINE_OVERRIDES, **OVERRIDES.get(chosen_name, {})},
        source_sha256={path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
                       for path in {**BASELINE_OVERRIDES, **OVERRIDES.get(chosen_name, {})}.values()},
        selected_receipt=pin(ROOT / chosen_receipt),
        resources=chosen_resources, timing=chosen_timing,
        native_audit=pin(AREA / 'native-audit.json'),
        scope='Next-study source choice only. No production image promotion, hardware qualification or parent-clock/I/O signoff.')
    (AREA / 'selection.json').write_text(json.dumps(selection, indent=2, sort_keys=True) + '\n')
    result = dict(schema='v103-geometry-mapping-checkpoint-v1', baseline_revision=BASELINE,
        branch='study/gamebub-v103-geometry-mapping-20261107',
        status='PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN',
        codec_profile_unchanged=True, resolution=[720, 480], packet_cap_bytes=49152,
        cycle_schedule_unchanged=True, compression_or_quality_gain_measured=False,
        paired_regression=dict(lanes=lanes,
            total_case_profile_runs=sum(v['case_profile_runs'] for v in lanes),
            total_directed_checks=sum(v['directed_checks'] for v in lanes),
            scope='Baseline/candidate x seeds x profiles, including expected rejects; not unique displayed frames or hardware FPS.'),
        focused=dict(reconstruction_combinational_inputs=32768,
            reconstruction_entire_2bit_plane_13bit_tile_domain=True,
            admission_combinational_inputs=130920,
            admission_entire_32bit_tile_domain_exhaustively_simulated=False,
            admission_full_domain_identity='Mathematical derivation with explicit intermediate-width bounds, not machine-checked formal proof.',
            clock_edges=0,
            selected_results=[pin(AREA / k / 'results.json') for k in ('admission', 'reconstruct')],
            independent_trace_replays=[pin(AREA / k / 'trace-audit.json') for k in ('admission', 'reconstruct')]),
        native=dict(vendor='Vivado 2026.1 build 6511674', part='xc7a100tcsg324-1',
            comparison_clock_period_ns=10, control=native['V102_control'], variants=variants,
            scope='Single-clock component OOC. Unknown parent clock/boundary/I/O contracts; stage-matched comparisons only. No board performance claim.'),
        audits=[pin(AREA / n) for n in ('source-audit.json', 'native-audit.json')],
        stopped_attempts=pin(AREA / 'stopped-attempts.json'),
        next_study_selection=pin(AREA / 'selection.json'),
        qualification=dict(component_route_finished=True,
            routable_nets_all_routed=True,
            scope='Selected next-study source only; individual experiment outcomes remain in native.variants.',
            component_100MHz_internal_timing_target_met=(chosen['component_internal_timing_target_met'] if chosen else False),
            parent_clock_boundary_IO_qualified=False, methodology_DRC_CDC_signed_off=False,
            complete_custom_path_integrated=False, hardware_30fps_validated=False,
            complete_FPGA_decode_under10ms_validated=False, achieved_Fmax_Hz=None,
            hardware_test_performed=False),
        parser=dict(RTL_changed=False, review='docs/cu66-v103/parser-mapping-review.md',
            model_receipt=pin(AREA / 'parser-prefix-model.json'),
            Python_model_comparisons=prefix['counts']['model_comparisons'],
            scope='Mapped hierarchy and source inventory plus ranked unmeasured follow-up variants; no parser-specific performance gain.'),
        next_control_architecture='docs/cu66-v103/next-control-architecture.md')
    assert result['paired_regression']['total_case_profile_runs'] == 288
    assert result['paired_regression']['total_directed_checks'] == 304
    (AREA / 'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V103_SUMMARY', result['status'], 'paired', 288, 'directed', 304)


if __name__ == '__main__':
    main()
