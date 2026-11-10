#!/usr/bin/env python3
"""Collect only completed source-bound V128 functional and physical evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = Path('experiments/python-gamebub-v128')
SELECTION = Path('fpga/experiments/cu66-v128-raw/selected-composition.json')


def read(path):
    return json.loads((ROOT / path).read_text())


def pin(path):
    p = (ROOT / path).resolve()
    return dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def native(path, audit_path, selection):
    n, a = read(path), read(audit_path)
    assert n['status'] == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
    assert n['component_route_finished'] and n['source_snapshot_unchanged'] and n['recipe_unchanged']
    assert n['clock_period_ns'] == 8.0 and n['start_mode'] == 'rtl'
    assert n['source_contract']['source_origins'] == selection['complete_source_origins']
    assert n['source_contract']['changed_aliases'] == selection['changed_aliases']
    assert a['status'] == 'PASS_V128_INDEPENDENT_TERMINAL_EVIDENCE'
    assert a['receipt'] == pin(path) and not a['failed_checks'] and not a['errors']
    assert a['design_timing_pass'] == n['result']['component_internal_target_pass']
    for name, digest in n['retained_artifact_sha256'].items():
        assert pin(path.parent / name)['sha256'] == digest
    return n, a


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-receipt', type=Path, required=True)
    ap.add_argument('--repeat-receipt', type=Path)
    ap.add_argument('--repeat-audit', type=Path)
    ap.add_argument('--functional-freeze', type=Path,
                    default=AREA / 'audit/functional-tooling-freeze-revision2.json')
    args = ap.parse_args()
    c = read(SELECTION)
    assert c['schema'] == 'v128-selected-raw-padding-composition-v1'
    assert len(c['source_origins']) == c['changed_origin_count'] == 5
    assert len(c['complete_source_origins']) == 18 and c['unchanged_origin_count'] == 13
    assert c['declared_public_cycle_delta'] == 0 and c['source_payload_bits_added'] == 1
    freeze = read(args.functional_freeze)
    assert freeze['schema'] == 'v128-functional-tooling-freeze-v1'
    assert freeze['status'].startswith('FROZEN') and freeze['actual_RTL_run'] is False
    assert freeze['selected_composition'] == pin(SELECTION)
    assert freeze['source_sha256']
    for path, digest in freeze['source_sha256'].items():
        assert pin(path)['sha256'] == digest
    index_path = AREA / 'integration/results.json'
    audit_path = AREA / 'audit/full-independent.json'
    f, fa = read(index_path), read(audit_path)
    assert f['schema'] == 'v128-raw-functional-composition-v1'
    assert f['status'] == 'PASS_V128_RAW_FULL_FUNCTIONAL'
    assert f['source_origins'] == c['complete_source_origins']
    assert set(f['stages']) == {'focused', 'spatial', 'peer', 'parent'}
    assert f['declared_public_cycle_delta'] == 0 and f['exact_B_public_cycles'] is True
    assert f['all_original_oracles_retained'] is True and f['assertions_disabled_or_downgraded'] is False
    assert fa['status'] == 'PASS_INDEPENDENT_V128_FULL_FUNCTIONAL_AUDIT'
    assert fa['integration_index_sha256'] == pin(index_path)['sha256']
    assert fa['source_B_count'] == 18 and fa['source_B_hashes_match_handoff'] is True
    assert fa['source_origins'] == c['complete_source_origins']
    assert fa['exact_comparisons'] == dict(spatial_stdout_event_and_canonical_streams=4,
                                         peer_stdout_event_and_canonical_streams=2,
                                         parent_stdout_and_terminal_stream_sets=4)
    assert freeze['source_sha256']['scripts/cu66-v128/audit_functional.py'] == pin(
        'scripts/cu66-v128/audit_functional.py')['sha256']
    for meta in f['stages'].values():
        assert pin(meta['path'])['sha256'] == meta['sha256']
        assert pin(meta['receipt']['path']) == meta['receipt']
    focused = read(f['stages']['focused']['receipt']['path'])
    assert focused['status'] == 'PASS' and focused['actual_RTL_run'] is True
    assert focused['aggregate_is_single_whole_composition_binary'] is False
    assert focused['proof_roles'] == c['proof_roles']
    assert set(focused['focused_components']) == {'raw_validation', 'header_padding'}
    focused_audit = read(AREA / 'audit/focused-independent.json')
    assert focused_audit['status'] == 'PASS_INDEPENDENT_V128_FOCUSED_AUDIT'
    assert focused_audit['focused_receipt'] == f['stages']['focused']['receipt']
    old = read('experiments/python-gamebub-v127/results.json')
    assert pin('experiments/python-gamebub-v127/results.json')['sha256'] == \
        '5e872674c6243a3faf4aafab1a3df5cca842e23b8427ce91403130a30c6d40b9'
    assert c['parent'] == old['functional_proof']
    pr = read(f['stages']['parent']['receipt']['path'])
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
    nr, na = native(args.native_receipt, AREA / 'audit/native-independent.json', c)
    assert nr['clean_repeat_of'] is None
    primary_pass = nr['result']['component_internal_target_pass']
    repeated, repeat_pass = None, False
    if primary_pass:
        assert args.repeat_receipt and args.repeat_audit, 'A positive source needs a fresh identical repeat'
        repeated, ra = native(args.repeat_receipt, args.repeat_audit, c)
        assert repeated['clean_repeat_of'] == pin(args.native_receipt)
        assert repeated['source_contract'] == nr['source_contract']
        assert repeated['tooling_sha256'] == nr['tooling_sha256']
        assert all(repeated['recipe_sha256'][name] == nr['recipe_sha256'][name]
                   for name in ('run.tcl', 'report.tcl', 'component.xdc'))
        repeat_pass = repeated['result']['component_internal_target_pass']
    else:
        assert not args.repeat_receipt and not args.repeat_audit
    same = [p for p in (ROOT / AREA / 'native').glob('*/receipt.json')
            if read(p)['source_contract']['source_origins'] == c['complete_source_origins']
            and read(p)['clock_period_ns'] == 8.0]
    assert len(same) == (2 if repeated else 1), 'Unexpected unchanged-composition trial count'
    observation = read(AREA / 'pipeline-observations.json')
    assert observation['status'] == 'PASS_OBSERVATION_INTEGRITY'
    query = read(observation['candidate']['receipt']['path'])
    assert query['native_receipt'] == pin(args.native_receipt)
    refs = dict(
        selected_composition=SELECTION, functional_input_freeze=args.functional_freeze,
        functional_proof=index_path, functional_audit=audit_path,
        focused_audit=AREA / 'audit/focused-independent.json',
        selected_functional_auditor=Path('scripts/cu66-v128/audit_functional.py'),
        candidate_native_receipt=args.native_receipt,
        native_independent_audit=AREA / 'audit/native-independent.json',
        native_prelaunch_gate=AREA / 'orchestration/native-prelaunch-gate.json',
        native_prelaunch_review=AREA / 'audit/native-preflight-review.json',
        root_tooling_freeze=AREA / 'orchestration/root-tooling-freeze.json',
        focused_repair_review=AREA / 'audit/focused-repair-review.json',
        baseline_review=AREA / 'audit/baseline-review.json',
        baseline_query_review=AREA / 'audit/baseline-query-review.json',
        candidate_query_review=AREA / 'audit/candidate-query-review.json',
        readonly_pipeline_comparison=AREA / 'pipeline-observations.json',
        python_raw_model=AREA / 'python-model/raw-model.json',
        qualified_control_B100=Path('experiments/python-gamebub-v120/handoff.json'),
        previous_V127_results=Path('experiments/python-gamebub-v127/results.json'),
        report=Path('docs/cu66-v128/README.md'),
        functional_report=Path('docs/cu66-v128/functional-results.md'),
        timing_report=Path('docs/cu66-v128/timing-results.md'),
        next_timing_proposal=Path('docs/cu66-v128/next-timing.md'))
    for key in ('native_prelaunch_review', 'focused_repair_review', 'baseline_review',
                'baseline_query_review', 'candidate_query_review'):
        review = read(refs[key])
        assert review['status'].startswith('PASS'), key
        if 'passed_checks' in review and 'check_count' in review:
            assert review['passed_checks'] == review['check_count'], key
    assert read(refs['python_raw_model'])['status'] == 'PASS_MODEL_ONLY'
    t, prior = nr['result']['timing'], old['candidate_result']['timing']
    result = dict(
        schema='v128-full-raw-validation-and-owned-padding-study-v1',
        status=('COMPONENT_125MHZ_FRESH_REPEAT_QUALIFIED' if primary_pass and repeat_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_REPEAT_FAIL' if primary_pass else
                'COMPLETED_BOUNDED_STUDY_125MHZ_TARGET_FAIL'),
        base_commit='c196ad83e4c077bb50f9706058fb6416425d4fc5',
        branch=subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
        candidate_sources=c['source_origins'], changed_aliases_from_V127=c['changed_aliases'],
        proof_roles=c['proof_roles'], candidate_result=nr['result'], baseline_result=old['candidate_result'],
        timing_delta_from_V127={k: round(t[k] - prior[k], 6) for k in t},
        resource_utilization=na['actual_resource_utilization'], control_sets=na['actual_control_sets'],
        resource_delta_from_V127=na['resource_delta_from_V127125'],
        control_set_delta_from_V127=na['control_set_delta_from_V127125'],
        mapped_inventory=na['mapped_inventory']['candidate'],
        padding_mapped_observations=na['padding_mapped_observations'],
        fresh_methodology_counts={k: v['count'] for k, v in na['methodology']['candidate']['fresh'].items()},
        independent_native_evidence_checks=len(na['checks']),
        declared_and_measured_public_cycle_delta=0, source_payload_bits_added=1,
        raw_tuple_bits=72, raw_validation_lanes=2, phase_encodings=8,
        full_functional_raw_stream_sets=10, row_parent=old['row_parent'],
        all_parent_fixture_latency_profiles=profiles,
        all_original_oracles_retained=True, assertions_disabled_or_downgraded=False,
        focused_attempt_receipts={kind: [pin(p) for p in sorted((ROOT / AREA / kind / 'attempts').glob('*/receipt.json'))]
                                  for kind in ('raw', 'padding')},
        candidate_component_125MHz_qualified=bool(primary_pass and repeat_pass),
        positive_same_source_repeat_performed=repeated is not None, negative_same_source_rerouted=False,
        qualified_control_original_18_files_unchanged=True,
        full_single_timebase_custom_endpoint_harness_complete=False,
        custom_CU66_profile_negotiation_complete=False,
        ESP32_CPU_WiFi_QSPI_physical_service_calibrated=False,
        whole_parent_routed_clock_qualified=False, sustained_hardware_30fps_qualified=False,
        validated_hardware_decode_under10ms_qualified=False,
        hardware_contact=False, board_bitstream_generated=False,
        next_timing_proposal_implemented=False,
        collector=pin('scripts/cu66-v128/collect_results.py'),
        **{key: pin(path) for key, path in refs.items()})
    if repeated:
        result.update(repeat_native_receipt=pin(args.repeat_receipt), repeat_native_audit=pin(args.repeat_audit),
                      repeat_result=repeated['result'])
    (ROOT / AREA / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
