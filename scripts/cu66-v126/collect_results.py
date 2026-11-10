#!/usr/bin/env python3
"""Collect source-bound V126 results after completed qualification and routing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = Path('experiments/python-gamebub-v126')


def read(path):
    return json.loads((ROOT / path).read_text())


def pin(path):
    path = (ROOT / path).resolve()
    return dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def native(path, audit_path):
    record, audit = read(path), read(audit_path)
    assert record['component_route_finished'] and record['source_snapshot_unchanged']
    assert record['recipe_unchanged'] and record['clock_period_ns'] == 8.0
    assert audit['status'] == 'PASS_V126_INDEPENDENT_TERMINAL_EVIDENCE'
    assert audit['receipt'] == pin(path) and not audit['failed_checks'] and not audit['errors']
    return record, audit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-receipt', type=Path, required=True)
    ap.add_argument('--repeat-receipt', type=Path)
    ap.add_argument('--repeat-audit', type=Path)
    a = ap.parse_args()
    index_path = AREA / 'integration/results.json'
    audit_path = AREA / 'audit/full-independent.json'
    functional, fa = read(index_path), read(audit_path)
    assert functional['status'] == 'PASS_V126_PRODUCER_FULL_FUNCTIONAL'
    assert functional['declared_public_cycle_delta'] == 0 and functional['exact_B_public_cycles'] is True
    assert fa['status'] == 'PASS_INDEPENDENT_V126_FULL_FUNCTIONAL_AUDIT'
    assert fa['integration_index_sha256'] == pin(index_path)['sha256']
    assert fa['exact_comparisons'] == dict(spatial_stdout_event_and_canonical_streams=4,
                                         peer_stdout_event_and_canonical_streams=2,
                                         parent_stdout_and_terminal_stream_sets=4)
    previous = read('experiments/python-gamebub-v125/results.json')
    parent = read('experiments/python-gamebub-v125/integration/results.json')
    changed = sorted(k for k, v in functional['source_origins'].items() if v != parent['source_origins'][k])
    assert changed == ['fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv']
    parent_selector = read(functional['stages']['parent']['path'])
    parent_receipt = read(parent_selector['path'])
    assert len(parent_receipt['runs']) == 4
    assert {(r['variant'], r['profile']) for r in parent_receipt['runs']} == {
        ('byte', 0), ('byte', 1), ('row', 0), ('row', 1)}
    parent_profiles = []
    for run in parent_receipt['runs']:
        live = run['live_case']
        fields = ('last_outer_to_commit_cycles', 'first_outer_to_commit_cycles', 'start_to_commit_cycles')
        parent_profiles.append(dict(variant=run['variant'], profile=run['profile'], seed=run['seed'],
                                    cycles={k: live[k] for k in fields},
                                    projected_ms_if_complete_parent_125MHz={k: live[k] / 125000 for k in fields},
                                    physical_SDRAM=False, complete_parent_clock_qualified=False))
    nr, na = native(a.native_receipt, AREA / 'audit/native-independent.json')
    assert nr['source_contract']['source_origins'] == functional['source_origins']
    primary_pass = nr['result']['component_internal_target_pass']
    repeated, repeat_pass = None, False
    if primary_pass:
        assert a.repeat_receipt and a.repeat_audit, 'A positive route requires its separate fresh repeat'
        repeated, ra = native(a.repeat_receipt, a.repeat_audit)
        assert repeated['clean_repeat_of'] == pin(a.native_receipt)
        assert repeated['source_contract'] == nr['source_contract']
        assert repeated['tooling_sha256'] == nr['tooling_sha256']
        assert all(repeated['recipe_sha256'][n] == nr['recipe_sha256'][n]
                   for n in ('run.tcl', 'report.tcl', 'component.xdc'))
        repeat_pass = repeated['result']['component_internal_target_pass']
    else:
        assert not a.repeat_receipt and not a.repeat_audit
    observations = AREA / 'pipeline-observations.json'
    assert read(observations)['status'] == 'PASS_OBSERVATION_INTEGRITY'
    assert read(observations)['candidate']['receipt']['path'].startswith(str(AREA / 'pipeline-inspection/candidate-'))
    query = read(read(observations)['candidate']['receipt']['path'])
    assert query['native_receipt'] == pin(a.native_receipt)
    assert read(AREA / 'orchestration/focused-attempt-history.json')['official_retry_pending'] is False
    before = previous['candidate_result']['timing']
    after = nr['result']['timing']
    refs = {
        'candidate_native_receipt': a.native_receipt,
        'native_independent_audit': AREA / 'audit/native-independent.json',
        'functional_proof': index_path, 'functional_audit': audit_path,
        'functional_auditor_v2': Path('scripts/cu66-v126/audit_functional_v2.py'),
        'selected_functional_auditor_v3': Path('scripts/cu66-v126/audit_functional_v3.py'),
        'functional_auditor_v3_check_placement_repair': AREA / 'audit/full-independent-v3-derivation.json',
        'functional_auditor_v3_review': AREA / 'audit/functional-v3-review.json',
        'functional_auditor_v3_supplement': AREA / 'audit/full-independent-tooling-freeze-v3-supplement.json',
        'native_prelaunch_review': AREA / 'audit/native-preflight-review.json',
        'native_prelaunch_gate': AREA / 'orchestration/native-prelaunch-gate.json',
        'functional_auditor_reporting_repair': AREA / 'audit/full-independent-v2-derivation.json',
        'functional_auditor_v2_review': AREA / 'audit/functional-v2-review.json',
        'functional_auditor_v2_supplement': AREA / 'audit/full-independent-tooling-freeze-v2-supplement.json',
        'focus_selector': AREA / 'producer/results.json',
        'focus_independent_audit': AREA / 'audit/full-independent-focused.json',
        'readonly_pipeline_comparison': observations,
        'baseline_query_review': AREA / 'audit/baseline-query-review.json',
        'python_producer_model': AREA / 'python-model/producer-model.json',
        'model_table_binding_review': AREA / 'audit/producer-model-binding-review.json',
        'retained_attempt_history': AREA / 'orchestration/focused-attempt-history.json',
        'final_focused_tooling_freeze': AREA / 'audit/full-independent-tooling-freeze-revision5.json',
        'root_tooling_freeze': AREA / 'orchestration/root-tooling-freeze.json',
        'qualified_control_B100': Path('experiments/python-gamebub-v120/handoff.json'),
        'previous_V125_results': Path('experiments/python-gamebub-v125/results.json'),
        'report': Path('docs/cu66-v126/README.md'),
        'functional_report': Path('docs/cu66-v126/functional-results.md'),
        'timing_report': Path('docs/cu66-v126/timing-results.md'),
        'next_timing_proposal': Path('docs/cu66-v126/next-timing.md'),
    }
    result = dict(
        schema='v126-producer-successor-pipeline-study-v1',
        status=('COMPONENT_125MHZ_FRESH_REPEAT_QUALIFIED' if primary_pass and repeat_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_REPEAT_FAIL' if primary_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_TARGET_FAIL'),
        base_commit='82ffe3fa16b6df32bb45330a8c47caa31c71751e',
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        candidate_source=pin(Path('fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv')),
        changed_aliases_from_V125=changed, candidate_result=nr['result'],
        baseline_result=previous['candidate_result'],
        timing_delta_from_V125={k: round(after[k] - before[k], 6) for k in after},
        resource_utilization=na['actual_resource_utilization'],
        routed_resources=dict(na['actual_resource_utilization']['route'],
                              CARRY4=na['mapped_inventory']['candidate']['route']['reported_global_CARRY4']),
        mapped_inventory=na['mapped_inventory']['candidate'],
        control_sets=na['actual_control_sets'],
        resource_delta_from_V125=na['resource_delta_from_V125125'],
        control_set_delta_from_V125=na['control_set_delta_from_V125125'],
        fresh_methodology_counts={k: v['count'] for k, v in na['methodology']['candidate']['fresh'].items()},
        independent_native_evidence_checks=len(na['checks']),
        declared_and_measured_public_cycle_delta=0, source_payload_bits_added=24,
        all_original_oracles_retained=True, assertions_disabled_or_downgraded=False,
        full_functional_raw_stream_sets=10, row_parent=previous['row_parent'],
        all_parent_fixture_latency_profiles=parent_profiles,
        candidate_component_125MHz_qualified=bool(primary_pass and repeat_pass),
        positive_same_source_repeat_performed=repeated is not None,
        negative_same_source_rerouted=False,
        qualified_control_original_18_files_unchanged=True,
        full_single_timebase_custom_endpoint_harness_complete=False,
        custom_CU66_profile_negotiation_complete=False,
        ESP32_CPU_WiFi_QSPI_physical_service_calibrated=False,
        whole_parent_routed_clock_qualified=False,
        sustained_hardware_30fps_qualified=False,
        validated_hardware_decode_under10ms_qualified=False,
        hardware_contact=False, board_bitstream_generated=False,
        next_timing_proposal_implemented=False,
        collector=pin(Path('scripts/cu66-v126/collect_results.py')),
        **{key: pin(path) for key, path in refs.items()})
    if repeated:
        result.update(repeat_native_receipt=pin(a.repeat_receipt), repeat_native_audit=pin(a.repeat_audit),
                      repeat_result=repeated['result'])
    (ROOT / AREA / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
