#!/usr/bin/env python3
"""Select the V106 measured implementation and retain explicit timing gates."""
import hashlib
import json
from pathlib import Path
from bundle_manifest import audited_sha
from regress import ROOT
from campaign import BASELINE, BASELINE_OVERRIDES, LANES, OVERRIDES, DEFERRED_NATIVE, REDIRECTION, REJECTED_FUNCTIONAL

AREA = ROOT / 'experiments/python-gamebub-v106'


def obj(path):
    return json.loads(path.read_text())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def write(name, value):
    (AREA / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    source, native = [obj(AREA / name) for name in ('source-audit.json', 'native-audit.json')]
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert source['baseline_revision'] == native['baseline_revision'] == BASELINE
    for audit in (source, native):
        bindings = audit.get('input_hashes', audit.get('input_sha256'))
        assert bindings
        for name, digest in bindings.items():
            assert audited_sha(name) == digest, ('audited input drift', name)
    paths = obj(AREA / 'path-analysis.json')
    physical = obj(AREA / 'physical-locality.json')
    methodology = obj(AREA / 'methodology-resolution.json')
    assert paths['status'] == 'PASS_EVIDENCE'
    assert paths['native_audit'] == methodology['native_audit'] == pin(AREA / 'native-audit.json')
    assert physical['status'] == 'PASS_EVIDENCE' and physical['native_audit'] == pin(AREA / 'native-audit.json')
    math = obj(AREA / 'math/results.json')
    assert math['status'] == 'PASS' and math['terminal_verdict']['cases'] == 32768
    storage_selection = obj(AREA / 'locality/probe-results.json')
    storage_path = ROOT / storage_selection['selected_receipt']
    storage = obj(storage_path)
    assert storage_selection['status'] == storage['status'] == 'PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE'
    assert pin(storage_path)['sha256'] == storage_selection['sha256']
    composition = obj(AREA / 'composition.json')
    assert composition['status'] == 'PASS' and composition['both_orders_identical']
    assert pin(ROOT / composition['candidate'])['sha256'] == composition['candidate_sha256']
    extra_focused = {}
    for label in ('plan', 'context'):
        probe_path = AREA / label / 'results.json'
        trace_path = AREA / label / 'trace-audit.json'
        probe, trace = obj(probe_path), obj(trace_path)
        assert probe['status'] == trace['status'] == 'PASS'
        assert trace['selected_summary'] == pin(probe_path)
        assert trace['selected_receipt'] == pin(ROOT / trace['selected_receipt']['path'])
        extra_focused[label] = dict(receipt=pin(probe_path), independent_trace=pin(trace_path))
    extra_focused['plan']['prefix_rows'] = obj(AREA / 'plan/trace-audit.json')['prefix_rows']
    extra_focused['plan']['clocked_begin_cases'] = obj(AREA / 'plan/trace-audit.json')['clocked_begin_cases']
    extra_focused['context']['geometry_rows'] = obj(AREA / 'context/trace-audit.json')['rows']
    rice_selection = obj(AREA / 'rice/probe-results.json')
    rice_path = ROOT / rice_selection['selected_receipt']
    rice, rice_trace = obj(rice_path), obj(AREA / 'rice/trace-audit.json')
    assert rice_selection['status'] == rice['status'] == 'PASS_ACTUAL_RICE_CACHE_EQUIVALENCE'
    assert pin(rice_path)['sha256'] == rice_selection['sha256'] == rice_trace['receipt_sha256']
    assert rice_trace['status'] == 'PASS_RICE_CACHE_ALGEBRA_ADAPTERS_AND_CHECKPOINTS'
    extra_focused['rice'] = dict(receipt=pin(rice_path),
        independent_trace=pin(AREA / 'rice/trace-audit.json'),
        clock_edges=sum(row['actual_every_clock_oracle_edges'] for row in rice_trace['runs']),
        raw_historical_traces_sampled=True, actual_oracle_checks_every_clock=True)
    prefix_selection = obj(AREA / 'prefix/probe-results.json')
    prefix_path = ROOT / prefix_selection['selected_receipt']
    prefix, prefix_trace = obj(prefix_path), obj(AREA / 'prefix/trace-audit.json')
    assert prefix_selection['status'] == prefix['status'] == 'PASS_ACTUAL_PREFIX_EQUIVALENCE'
    assert pin(prefix_path)['sha256'] == prefix_selection['sha256'] == prefix_trace['receipt_sha256']
    assert prefix_trace['status'] == 'PASS_PREFIX_MODEL_ADAPTERS_AND_CHECKPOINTS'
    extra_focused['prefix'] = dict(receipt=pin(prefix_path),
        independent_trace=pin(AREA / 'prefix/trace-audit.json'),
        clock_edges=sum(row['actual_every_clock_oracle_edges'] for row in prefix_trace['runs']),
        raw_historical_traces_sampled=True, actual_oracle_checks_every_clock=True)
    telemetry_path, telemetry_trace_path = [AREA / 'telemetry' / name
        for name in ('results.json', 'trace-audit.json')]
    telemetry, telemetry_trace = obj(telemetry_path), obj(telemetry_trace_path)
    assert telemetry['status'] == telemetry_trace['status'] == 'PASS'
    assert telemetry_trace['selected_summary'] == pin(telemetry_path)
    assert telemetry_trace['selected_receipt'] == pin(ROOT / telemetry['selected_report'])
    extra_focused['telemetry'] = dict(receipt=pin(telemetry_path),
        independent_trace=pin(telemetry_trace_path),
        clock_edges=telemetry_trace['prepared_edges'] + telemetry_trace['historical_edges'],
        prepared_cases=telemetry_trace['prepared_cases'],
        counter_words=telemetry_trace['counter_words'], carry_positions=telemetry_trace['carry_positions'],
        raw_historical_traces_sampled=True, actual_oracle_checks_every_clock=True)
    suffix_selection = obj(AREA / 'suffix/probe-results.json')
    suffix_path = ROOT / suffix_selection['selected_receipt']
    suffix, suffix_trace = obj(suffix_path), obj(AREA / 'suffix/trace-audit.json')
    assert suffix_selection['status'] == suffix['status'] == 'PASS_ACTUAL_SUFFIX_EQUIVALENCE'
    assert pin(suffix_path)['sha256'] == suffix_selection['sha256'] == suffix_trace['receipt_sha256']
    assert suffix_trace['status'] == 'PASS_SUFFIX_MODEL_ADAPTERS_AND_CHECKPOINTS'
    extra_focused['suffix'] = dict(receipt=pin(suffix_path),
        independent_trace=pin(AREA / 'suffix/trace-audit.json'),
        clock_edges=sum(row['actual_every_clock_oracle_edges'] for row in suffix_trace['runs']),
        raw_historical_traces_sampled=True, actual_oracle_checks_every_clock=True,
        private_suffix_values_compared_only_when_selected=True)
    idct_path, idct_trace_path = [AREA / 'idct' / name for name in ('results.json', 'trace-audit.json')]
    idct, idct_trace = obj(idct_path), obj(idct_trace_path)
    assert idct['status'] == idct_trace['status'] == 'PASS'
    assert idct_trace['selected_summary'] == pin(idct_path)
    assert idct_trace['selected_receipt'] == pin(ROOT / idct['selected_report'])
    extra_focused['idct'] = dict(receipt=pin(idct_path), independent_trace=pin(idct_trace_path),
        clock_edges=idct_trace['total_clock_edges'], multiply_edges=idct_trace['total_multiply_edges'],
        independent_gold_tiles=idct_trace['independent_integer_gold_tiles'],
        actual_complete_module_cycle_output_product_comparison=True)
    producer_path = AREA / 'producer-cache/results.json'
    producer = obj(producer_path)
    assert producer['status'] == 'PASS_MODEL_AND_EXACT_SOURCE_RECIPES' and not producer['actual_RTL_run']
    assert producer['transition_model_rows'] == 262144 and producer['integrated_RTL_required']
    extra_focused['producer_cache'] = dict(model=pin(producer_path), model_only=True,
        transition_model_rows=producer['transition_model_rows'],
        integrated_live_cache_assertions_in_required_pipeline_lanes=True,
        scope='Inductive finite transition model/source proof; actual whole-producer RTL invariant and public parity checked by the required paired pipeline lanes, not standalone controller reachability proof.')
    for label in ('scratch', 'idct-area'):
        receipt_path, trace_path = [AREA / label / name for name in ('results.json', 'trace-audit.json')]
        receipt, trace = obj(receipt_path), obj(trace_path)
        assert receipt['status'] == trace['status'] == 'PASS'
        assert trace['selected_summary'] == pin(receipt_path)
        assert trace['selected_receipt'] == pin(ROOT / receipt['selected_report'])
        extra_focused[label.replace('-', '_')] = dict(receipt=pin(receipt_path), independent_trace=pin(trace_path),
            clock_edges=trace['total_clock_edges'])
    ingress_selection = obj(AREA / 'ingress/probe-results.json')
    ingress_path = ROOT / ingress_selection['selected_receipt']
    ingress, ingress_trace = obj(ingress_path), obj(AREA / 'ingress/trace-audit.json')
    assert ingress_selection['status'] == ingress['status'] == 'PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE'
    assert ingress_selection.get('qualified_PASS', True)
    assert pin(ingress_path)['sha256'] == ingress_selection['sha256'] == ingress_trace['receipt_sha256']
    assert ingress_trace['status'] == 'PASS_INGRESS_MODEL_ADAPTERS_AND_CHECKPOINTS'
    extra_focused['ingress'] = dict(receipt=pin(ingress_path), independent_trace=pin(AREA / 'ingress/trace-audit.json'),
        clock_edges=ingress_trace['total_clock_edges'], private_replay_values_compared_only_when_live=True)
    suffix24_path = AREA / 'suffix24/results.json'
    suffix24 = obj(suffix24_path)
    assert suffix24['status'] == 'PASS_EXACT_PROJECTION_AND_RECIPES' and not suffix24['actual_RTL_run']
    assert suffix24['integrated_RTL_required']
    extra_focused['suffix24'] = dict(model=pin(suffix24_path), model_only=True,
        integrated_strict_production_lint_and_public_parity_in_required_lanes=True)
    unit_path = AREA / 'idct-area/unit-synthesis-comparison.json'
    unit = obj(unit_path)
    assert unit['status'] == 'UNIT_SYNTHESIS_EVIDENCE_COMPLETE' and unit['all_settings_matched']
    assert unit['selected_receipt'] == pin(ROOT / unit['selected_receipt']['path'])
    extra_focused['idct_area_unit'] = dict(comparison=pin(unit_path), receipt=unit['selected_receipt'],
        scope='Matched standalone synthesis only; no placement, routing or complete-pipeline speed qualification.')
    lanes = []
    for name, mode in LANES:
        path = AREA / 'regression' / name / mode / 'results.json'
        value = obj(path)
        assert value['status'] == 'PASS' and value['exact_same_seed_transcripts_events_cycles']
        lanes.append(dict(**pin(path), variant=name, mode=mode,
                          case_profile_runs=value['case_profile_runs'], directed_checks=value['directed_checks']))
    baseline = native['V105_control']['stages']['route']
    eligible = []
    for name, attempt in native['measured_variants'].items():
        if name in REJECTED_FUNCTIONAL or not all((name, mode) in LANES for mode in ('fresh', 'canonical')):
            continue
        stage = attempt.get('stages', {}).get('route')
        if not stage or not attempt.get('component_route_finished'):
            continue
        timing = stage['timing']
        if (attempt.get('routing_legality', {}).get('reported_zero_errors_and_complete')
                and all(v['used'] <= v['available'] for v in stage['capacity'].values())
                and stage['check_timing'].get('no_clock', -1) == 0
                and stage['check_timing'].get('unconstrained_internal_endpoints', -1) == 0
                and stage['check_timing'].get('loops', -1) == 0
                and timing['WHS_ns'] >= 0 and timing['WPWS_ns'] >= 0
                and timing['hold_failing'] == timing['pulse_failing'] == 0
                and timing['WNS_ns'] > baseline['timing']['WNS_ns']):
            eligible.append((name, attempt))
    if eligible:
        name, chosen = max(eligible, key=lambda item: (
            item[1]['stages']['route']['timing']['WNS_ns'],
            -item[1]['stages']['route']['hierarchy'][0]['total_LUT'],
            -item[1]['stages']['route']['hierarchy'][0]['DSP']))
        resources = chosen['stages']['route']['hierarchy'][0]
        timing, receipt = chosen['stages']['route']['timing'], chosen['path']
    else:
        name, chosen = 'baseline', None
        resources, timing = baseline['resources'], baseline['timing']
        receipt = native['V105_control']['receipt']
    # Fresh-only producer replacement is retained for behavioral reproduction;
    # native build filters source keys against the canonical 17-file closure.
    overrides = {**BASELINE_OVERRIDES, **OVERRIDES.get(name, {})}
    selection = dict(schema='v106-next-study-source-selection-v1', baseline_revision=BASELINE,
        selected_variant=name,
        selection_rule='Require exact paired workload parity; completed error-free routing and target resource fit; no unclocked/unconstrained internal endpoints or loops; nonnegative hold/pulse slack and zero hold/pulse failures. Prefer highest routed setup WNS above V105, then lower LUT/DSP. A negative WNS remains timing failure. A single run is not robustness proof.',
        source_overrides=overrides, source_sha256={p: pin(ROOT / p)['sha256'] for p in overrides.values()},
        selected_receipt=pin(ROOT / receipt), resources=resources, timing=timing,
        resource_delta_from_V105={key: resources[key] - baseline['resources'][key]
            for key in ('total_LUT', 'LUTRAM', 'FF', 'RAMB36', 'RAMB18', 'DSP')},
        setup_WNS_change_from_V105_ns=round(timing['WNS_ns'] - baseline['timing']['WNS_ns'], 3),
        native_audit=pin(AREA / 'native-audit.json'), single_run_gain_is_robustness_proof=False,
        scope='Selected experimental source only; exact parent clock/boundary and whole-device qualification remain separate.')
    write('selection.json', selection)
    variants = []
    for attempt in native['attempts']:
        stages = {}
        for stage, value in attempt.get('stages', {}).items():
            if not {'hierarchy', 'timing', 'capacity'} <= set(value):
                stages[stage] = dict(partial_report_fields=sorted(value))
                continue
            stages[stage] = dict(resources=value['hierarchy'][0], timing=value['timing'],
                capacity=value['capacity'], DRC_reported=value.get('DRC_reported'),
                methodology_reported=value.get('methodology_reported'),
                distributed_RAM_counts=value.get('distributed_RAM_counts'),
                coefficient_named_RAM_cells=sum('coefficients_reg' in row['instance']
                    for row in value.get('distributed_RAM', [])))
        variants.append(dict(variant=attempt['variant'], receipt=pin(ROOT / attempt['path']),
            status=attempt['status'], stages=stages, routing_legality=attempt.get('routing_legality'),
            placement_failure=attempt.get('placement_failure'),
            component_internal_timing_target_met=attempt.get('component_internal_timing_target_met', False)))
    result = dict(schema='v106-timing-locality-checkpoint-v1', baseline_revision=BASELINE,
        branch='study/gamebub-v106-timing-20261107', status='PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN',
        resolution=[720, 480], packet_cap_bytes=49152, codec_profile_unchanged=True,
        cycle_schedule_unchanged_in_selected_tests=True, compression_or_quality_gain_measured=False,
        focused=dict(math=pin(AREA / 'math/results.json'), exhaustive_helper_inputs=32768,
            math_trace=pin(AREA / 'math/trace-audit.json'), storage=pin(storage_path),
            storage_clock_edges=storage['total_clock_edges'], storage_runs=storage['runs'],
            storage_trace=pin(AREA / 'locality/trace-audit.json'),
            **extra_focused,
            scope='Exhaustive binary helper domain and bounded clocked whole-module store tests, including explicitly prepared internal states; not formal/four-state/mapped-netlist proof.'),
        composition=pin(AREA / 'composition.json'),
        paired_regression=dict(lanes=lanes, total_case_profile_runs=sum(x['case_profile_runs'] for x in lanes),
            total_directed_checks=sum(x['directed_checks'] for x in lanes),
            scope='Both implementations × seeds × profiles including expected rejects; not unique displayed frames or hardware FPS.'),
        native=dict(vendor='Vivado2026.1 build6511674', part='xc7a100tcsg324-1', comparison_clock_period_ns=10,
            control=native['V105_control'], variants=variants, deferred_native_variants=DEFERRED_NATIVE,
            rejected_functional_candidates=REJECTED_FUNCTIONAL, campaign_redirection=REDIRECTION),
        setup_cones=pin(AREA / 'path-analysis.json'), methodology_resolution=pin(AREA / 'methodology-resolution.json'),
        physical_locality=pin(AREA / 'physical-locality.json'),
        audits=[pin(AREA / n) for n in ('source-audit.json', 'native-audit.json', 'baseline-audit.json')],
        next_study_selection=pin(AREA / 'selection.json'),
        qualification=dict(component_route_finished=True,
            component_100MHz_internal_timing_target_met=bool(chosen and chosen['component_internal_timing_target_met']),
            parent_clock_boundary_IO_qualified=False, methodology_DRC_CDC_signed_off=False,
            whole_device_memory_service_qualified=False, complete_custom_path_integrated=False,
            hardware_30fps_validated=False, complete_FPGA_decode_under10ms_validated=False,
            achieved_Fmax_Hz=None, hardware_test_performed=False))
    assert result['paired_regression']['total_case_profile_runs'] == 1344
    assert result['paired_regression']['total_directed_checks'] == 1632
    postroute_path = AREA / 'postroute/report-audit.json'
    postroute = obj(postroute_path)
    assert postroute['status'] == 'RETAINED_DIAGNOSTIC_AUDITED'
    assert not postroute['selected_or_promoted']
    assert postroute['parent_checkpoint_unchanged']
    for binding in ('auditor', 'selected_receipt'):
        assert pin(ROOT / postroute[binding]['path']) == postroute[binding]
    result['postroute_diagnostic'] = dict(audit=pin(postroute_path),
        receipt=postroute['selected_receipt'], selected_or_promoted=False,
        before=postroute['before'], after=postroute['after'],
        scope='One separately audited AggressiveExplore post-route probe; excluded from the Default-flow source selection. Setup still fails at the unchanged 10 ns clock.')
    write('summary.json', result)
    print('V106_SUMMARY', name, 'WNS', timing['WNS_ns'],
          'component100MHz', result['qualification']['component_100MHz_internal_timing_target_met'])


if __name__ == '__main__':
    main()
