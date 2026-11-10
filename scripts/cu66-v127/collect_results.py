#!/usr/bin/env python3
"""Collect V127 only after complete functional, native and query evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = Path('experiments/python-gamebub-v127')
CHANGES = {
    'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv',
    'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv',
    'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv',
}


def read(path):
    return json.loads((ROOT / path).read_text())


def pin(path):
    p = (ROOT / path).resolve()
    return dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def native(path, audit_path):
    n, a = read(path), read(audit_path)
    assert n['component_route_finished'] and n['source_snapshot_unchanged']
    assert n['recipe_unchanged'] and n['clock_period_ns'] == 8.0
    assert a['status'] == 'PASS_V127_INDEPENDENT_TERMINAL_EVIDENCE'
    assert a['receipt'] == pin(path) and not a['failed_checks'] and not a['errors']
    assert a['design_timing_pass'] == n['result']['component_internal_target_pass']
    return n, a


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-receipt', type=Path, required=True)
    ap.add_argument('--repeat-receipt', type=Path)
    ap.add_argument('--repeat-audit', type=Path)
    ap.add_argument('--functional-auditor', type=Path, default=Path('scripts/cu66-v127/audit_functional.py'))
    ap.add_argument('--functional-freeze', type=Path,
                    default=AREA / 'audit/full-independent-tooling-freeze-revision2.json')
    ap.add_argument('--functional-freeze-sha256',
                    default='9f71d27f33789381c2962e0b20f3bc21075b16b873a04e553500bce852529606')
    args = ap.parse_args()
    index_path, audit_path = AREA / 'integration/results.json', AREA / 'audit/full-independent.json'
    f, fa, freeze = read(index_path), read(audit_path), read(args.functional_freeze)
    assert f['schema'] == 'v127-owner-functional-composition-v1'
    assert f['status'] == 'PASS_V127_OWNER_FULL_FUNCTIONAL'
    assert f['declared_public_cycle_delta'] == 0 and f['exact_B_public_cycles'] is True
    assert f['all_original_oracles_retained'] and not f['assertions_disabled_or_downgraded']
    assert fa['status'] == 'PASS_INDEPENDENT_V127_FULL_FUNCTIONAL_AUDIT'
    assert fa['integration_index_sha256'] == pin(index_path)['sha256']
    assert fa['source_B_count'] == 18 and fa['source_B_hashes_match_handoff'] is True
    assert fa['exact_comparisons'] == dict(spatial_stdout_event_and_canonical_streams=4,
                                         peer_stdout_event_and_canonical_streams=2,
                                         parent_stdout_and_terminal_stream_sets=4)
    assert pin(args.functional_freeze)['sha256'] == args.functional_freeze_sha256
    assert freeze['schema'] == 'v127-independent-tooling-freeze-v1'
    assert freeze['status'].startswith('FROZEN') and freeze['actual_RTL_run'] is False
    assert freeze['declared_public_cycle_delta'] == 0 and freeze['all_original_oracles_retained'] is True
    assert freeze['zero_contract_and_one_syntactic_edit_predicate_exercised'] is True
    assert freeze['baseline_self_stream_comparison_counts'] == dict(spatial=4, peer=2, parent=4)
    assert freeze['source_sha256'] and freeze['focused_input_sha256']
    for mapping in (freeze['source_sha256'], freeze['focused_input_sha256']):
        assert all(pin(path)['sha256'] == digest for path, digest in mapping.items())
    assert freeze['source_sha256'][pin(args.functional_auditor)['path']] == pin(args.functional_auditor)['sha256']
    old_path = Path('experiments/python-gamebub-v126/results.json')
    assert pin(old_path)['sha256'] == 'e42e0145e177d65f1499db79195caef8b8abb90fab1e5f235f79913c2056360f'
    old, parent = read(old_path), read('experiments/python-gamebub-v126/integration/results.json')
    assert pin('experiments/python-gamebub-v126/integration/results.json') == old['functional_proof']
    assert set(f['stages']) == {'focused', 'spatial', 'peer', 'parent'}
    for meta in f['stages'].values():
        assert pin(meta['path'])['sha256'] == meta['sha256']
        assert pin(meta['receipt']['path']) == meta['receipt']
    assert len(f['source_origins']) == 18 and set(f['source_origins']) == set(parent['source_origins'])
    changed = sorted(k for k, v in f['source_origins'].items() if v != parent['source_origins'][k])
    assert set(changed) == CHANGES and sorted(fa['v127_changed_aliases']) == changed
    for alias in changed:
        assert f['source_origins'][alias] == pin('fpga/experiments/cu66-v127-owner/' + Path(alias).name)
    ps = read(f['stages']['parent']['path'])
    assert dict(path=ps['path'], sha256=ps['sha256']) == f['stages']['parent']['receipt']
    pr = read(ps['path'])
    assert len(pr['runs']) == 4
    assert {(r['variant'], r['profile']) for r in pr['runs']} == {
        ('byte', 0), ('byte', 1), ('row', 0), ('row', 1)}
    profiles = []
    for run in pr['runs']:
        live = run['live_case']
        keys = ('last_outer_to_commit_cycles', 'first_outer_to_commit_cycles', 'start_to_commit_cycles')
        profiles.append(dict(variant=run['variant'], profile=run['profile'], seed=run['seed'],
                             cycles={k: live[k] for k in keys},
                             projected_ms_if_complete_parent_125MHz={k: live[k] / 125000 for k in keys},
                             physical_SDRAM=False, complete_parent_clock_qualified=False))
        if run['variant'] == 'row':
            label = 'fast' if run['profile'] == 0 else 'stalled'
            assert live['last_outer_to_commit_cycles'] == old['row_parent'][
                'post_final_accepted_input_to_validated_commit_cycles'][label]
    nr, na = native(args.native_receipt, AREA / 'audit/native-independent.json')
    assert nr['clean_repeat_of'] is None, 'The selected primary route cannot itself be a repeat'
    assert nr['source_contract']['source_origins'] == f['source_origins']
    assert nr['source_contract']['changed_aliases'] == changed
    primary_pass = nr['result']['component_internal_target_pass']
    repeated, repeat_pass = None, False
    if primary_pass:
        assert args.repeat_receipt and args.repeat_audit, 'A positive route requires a separate fresh repeat'
        repeated, ra = native(args.repeat_receipt, args.repeat_audit)
        assert repeated['clean_repeat_of'] == pin(args.native_receipt)
        assert repeated['source_contract'] == nr['source_contract']
        assert repeated['tooling_sha256'] == nr['tooling_sha256']
        assert all(repeated['recipe_sha256'][n] == nr['recipe_sha256'][n]
                   for n in ('run.tcl', 'report.tcl', 'component.xdc'))
        repeat_pass = repeated['result']['component_internal_target_pass']
    else:
        assert not args.repeat_receipt and not args.repeat_audit
    same = [p for p in (ROOT / AREA / 'native').glob('*/receipt.json')
            if read(p)['source_contract']['source_origins'] == f['source_origins']
            and read(p)['clock_period_ns'] == 8.0]
    assert len(same) == (2 if repeated else 1), 'Unexpected same-composition route count'
    obs_path = AREA / 'pipeline-observations.json'
    obs = read(obs_path)
    assert obs['status'] == 'PASS_OBSERVATION_INTEGRITY'
    query = read(obs['candidate']['receipt']['path'])
    assert query['native_receipt'] == pin(args.native_receipt)
    focus_selector = AREA / 'owner/results.json'
    selected = read(focus_selector)
    fp = f['stages']['focused']
    assert fp['path'] == str(focus_selector) and pin(focus_selector)['sha256'] == fp['sha256']
    assert selected['status'] == 'PASS' and selected['actual_RTL_run'] is True
    assert dict(path=selected['path'], sha256=selected['sha256']) == fp['receipt']
    assert pin(selected['path']) == fp['receipt']
    focus = read(selected['path'])
    assert focus['status'] == 'PASS' and focus['actual_RTL_run'] is True
    focused_audit = read(AREA / 'audit/full-independent-focused.json')
    assert focused_audit['status'] == 'PASS_INDEPENDENT_V127_FOCUSED_AUDIT'
    assert focused_audit['qualified_focused_receipt'] == fp['receipt']
    assert focused_audit['all_original_oracles_retained'] is True
    assert focused_audit['assertions_disabled_or_downgraded'] is False
    assert focused_audit['declared_public_cycle_delta'] == 0
    assert focus['candidate_private_comparison_edits'] == 1
    assert focus['old_private_value_contract_changes'] == focus['added_source_payload_bits'] == 0
    before, after = old['candidate_result']['timing'], nr['result']['timing']
    refs = {
        'candidate_native_receipt': args.native_receipt,
        'native_independent_audit': AREA / 'audit/native-independent.json',
        'functional_proof': index_path, 'functional_audit': audit_path,
        'selected_functional_auditor': args.functional_auditor,
        'functional_input_freeze': args.functional_freeze,
        'focus_selector': focus_selector,
        'focus_independent_audit': AREA / 'audit/full-independent-focused.json',
        'root_tooling_freeze': AREA / 'orchestration/root-tooling-freeze.json',
        'native_prelaunch_gate': AREA / 'orchestration/native-prelaunch-gate.json',
        'native_prelaunch_review': AREA / 'audit/native-preflight-review.json',
        'readonly_pipeline_comparison': obs_path,
        'baseline_query_review': AREA / 'audit/baseline-query-review.json',
        'candidate_query_review': AREA / 'audit/candidate-query-review.json',
        'python_owner_model': AREA / 'python-model/owner-model.json',
        'owner_model_binding_review': AREA / 'audit/owner-model-binding-review.json',
        'focus_adapter_repair_review': AREA / 'audit/focus-adapter-repair-review.json',
        'baseline_review': AREA / 'audit/baseline-review.json',
        'qualified_control_B100': Path('experiments/python-gamebub-v120/handoff.json'),
        'previous_V126_results': old_path,
        'historical_V123_results': Path('experiments/python-gamebub-v123/results.json'),
        'report': Path('docs/cu66-v127/README.md'),
        'functional_report': Path('docs/cu66-v127/functional-results.md'),
        'timing_report': Path('docs/cu66-v127/timing-results.md'),
        'next_timing_proposal': Path('docs/cu66-v127/next-timing.md'),
    }
    review_keys = ('baseline_query_review', 'candidate_query_review', 'owner_model_binding_review',
                   'focus_adapter_repair_review', 'baseline_review', 'native_prelaunch_review')
    for key in review_keys:
        review = read(refs[key])
        assert review['status'].startswith('PASS'), (key, review['status'])
        if 'passed_checks' in review and 'check_count' in review:
            assert review['passed_checks'] == review['check_count'], key
    assert read(AREA / 'python-model/owner-model.json')['status'] == 'PASS'
    result = dict(
        schema='v127-three-lane-owner-selection-study-v1',
        status=('COMPONENT_125MHZ_FRESH_REPEAT_QUALIFIED' if primary_pass and repeat_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_REPEAT_FAIL' if primary_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_TARGET_FAIL'),
        base_commit='0d03abbd5db89cb941286626de136ac023809eac',
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        candidate_sources={a: pin(f['source_origins'][a]['path']) for a in changed},
        changed_aliases_from_V126=changed, candidate_result=nr['result'],
        baseline_result=old['candidate_result'],
        timing_delta_from_V126={k: round(after[k] - before[k], 6) for k in after},
        resource_utilization=na['actual_resource_utilization'],
        routed_resources=dict(na['actual_resource_utilization']['route'],
                              CARRY4=na['mapped_inventory']['candidate']['route']['reported_global_CARRY4']),
        mapped_inventory=na['mapped_inventory']['candidate'],
        control_sets=na['actual_control_sets'],
        resource_delta_from_V126=na['resource_delta_from_V126125'],
        control_set_delta_from_V126=na['control_set_delta_from_V126125'],
        fresh_methodology_counts={k: v['count'] for k, v in na['methodology']['candidate']['fresh'].items()},
        independent_native_evidence_checks=len(na['checks']),
        declared_and_measured_public_cycle_delta=0, source_payload_bits_added=0,
        retained_V126_successor_logical_bits=24, owner_comparison_lanes=3,
        owner_epoch_width=32, owner_block_width=16,
        private_comparison_expression_edits=1, private_comparison_value_contract_changes=0,
        all_original_oracles_retained=True, assertions_disabled_or_downgraded=False,
        full_functional_raw_stream_sets=10, row_parent=old['row_parent'],
        all_parent_fixture_latency_profiles=profiles,
        focused_attempt_receipts=[pin(p) for p in sorted((ROOT / AREA / 'owner/attempts').glob('*/receipt.json'))],
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
        collector=pin(Path('scripts/cu66-v127/collect_results.py')),
        **{key: pin(path) for key, path in refs.items()})
    if repeated:
        result.update(repeat_native_receipt=pin(args.repeat_receipt), repeat_native_audit=pin(args.repeat_audit),
                      repeat_result=repeated['result'])
    (ROOT / AREA / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
