#!/usr/bin/env python3
"""Collect actual V119 receipts without promoting conditional clocks to hardware."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v119'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def terminal_positive(raw):
    """A positive timing number alone never qualifies an implementation."""
    return (raw.get('status') == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
            and raw.get('start_mode') == 'rtl'
            and all(raw.get(key) is True for key in (
                'component_route_finished', 'synthesis_executed',
                'clock_loaded_before_synthesis_in_this_run',
                'observed_default_command_exact', 'source_snapshot_unchanged',
                'recipe_unchanged'))
            and raw.get('observed_exit_code') == 0
            and (raw.get('result') or {}).get('component_internal_target_pass') is True)


def selected(path):
    summary = load(path)
    target = ROOT / summary.get('path', summary.get('selected_receipt', summary.get('selected_report', '')))
    assert target.is_file(), path
    raw = load(target)
    expected = summary.get('sha256', summary.get('selected_report_sha256'))
    if expected:
        assert sha(target) == expected
    else:
        assert raw == {key: value for key, value in summary.items() if key != 'selected_receipt'}
    return dict(selector=pin(path), receipt=pin(target), status=raw['status'],
                actual_RTL_run=raw.get('actual_RTL_run', False)), raw


def main():
    answer = dict(schema='v119-source-bound-measurements-v1', base_revision='d310e4d77fdb0d12b46640202b5b5f1648987a8f',
                  policy=pin(AREA / 'study-policy.json'), focused={}, compositions={}, native=[], live=[], standalone_prototypes={},
                  component_internal_positive_runs=[], component_fresh_repeat_qualified_clocks_MHz=[], component_fresh_repeat_qualified_sources=[],
                  milestones=dict(sustained_hardware_30fps=False, hardware_validated_decode_under10ms=False,
                                  full_parent_routed_clock_qualified=False, production_Sunshine_ESP32_endpoint_integrated=False))
    for name in ('scratch', 'owner/producer', 'owner/admission', 'owner/reconstruct', 'owner/response', 'owner/nonce-boundary'):
        path = AREA / name / 'results.json'
        if path.exists():
            entry, raw = selected(path)
            entry['contract'] = raw.get('contract')
            entry['scope'] = raw.get('scope')
            entry['scope_limits'] = raw.get('scope_limits')
            entry['actual_Python_model_run'] = raw.get('actual_Python_model_run',False)
            entry['source_sha256'] = raw.get('source_sha256', {})
            entry['current_source_pins_match'] = all((ROOT / name).is_file() and sha(ROOT / name) == expected
                                                     for name, expected in entry['source_sha256'].items())
            entry['runs'] = raw.get('runs', raw.get('generic_runs', []))
            answer['focused'][name] = entry
    probe = AREA / 'range-probe/results.json'
    if probe.exists():
        entry, raw = selected(probe)
        receipt_folder = (ROOT / entry['receipt']['path']).parent
        snapshots_unchanged = (raw['source_sha256'] == raw.get('final_source_sha256')
                               and all(sha(ROOT / name) == expected
                                       and sha(receipt_folder / 'sources' / name) == expected
                                       for name, expected in raw['source_sha256'].items()))
        entry.update(scope=raw['scope'], runs=raw.get('runs', []),
                     production_pipeline_source_selected=False,
                     clock_or_hardware_performance_claim=False,
                     source_snapshots_unchanged=snapshots_unchanged)
        answer['standalone_prototypes']['signed16_range_prefix_RTL'] = entry
    for label, directory in (('A', 'integrated-study'), ('B', 'repair-study')):
        group = {}
        for name in ('spatial', 'control-peer', 'live-parent', 'live-guard'):
            path = AREA / directory / name / 'results.json'
            if not path.exists():
                continue
            entry, raw = selected(path)
            group[name] = entry
            if name in ('live-parent', 'live-guard'):
                entry['baseline_B_guard_exact_parent_control'] = raw.get('baseline_B_guard_exact_parent_control')
                entry['baseline_C_exact_parent_control'] = raw.get('baseline_C_exact_parent_control')
                entry['baseline_C_semantic_parent_control'] = raw.get('baseline_C_semantic_parent_control')
                for run in raw.get('runs', []):
                    cycles = run['live_case']['last_outer_to_commit_cycles']
                    answer['live'].append(dict(composition=label, parent_proof=name, variant=run['variant'], profile=run['profile'],
                                               seed=run['seed'], source_receipt=entry['receipt'], live_case=run['live_case'],
                                               fences=run.get('fences'), service=run['service'],
                                               spatial_pipeline=run.get('spatial_pipeline'),
                                               baseline_C_comparison=run.get('baseline_C_comparison'),
                                               conditional125_ms=cycles / 125000, conditional100_ms=cycles / 100000,
                                               strict125_cycle_budget_only=cycles < 1250000,
                                               strict100_cycle_budget_only=cycles < 1000000,
                                               achieved_full_parent_clock=False, hardware_latency_validated=False))
        if group:
            answer['compositions'][label] = group
    for path in sorted(AREA.glob('*/native/*/receipt.json')):
        raw = load(path)
        entry = dict(receipt=pin(path), composition=path.parent.parent.parent.name, trial_id=raw['trial_id'], status=raw['status'], clock_period_ns=raw['clock_period_ns'],
                     result=raw.get('result'), clean_repeat_of=raw.get('clean_repeat_of'),
                     source_sha256=raw['source_contract']['source_sha256'])
        answer['native'].append(entry)
        if not terminal_positive(raw):
            continue
        answer['component_internal_positive_runs'].append(entry['receipt'])
        if entry['clean_repeat_of']:
            parent = ROOT / entry['clean_repeat_of']['path']
            assert sha(parent) == entry['clean_repeat_of']['sha256']
            original = load(parent)
            assert terminal_positive(original) and original['clean_repeat_of'] is None
            assert parent.resolve() != path.resolve()
            assert original['clock_period_ns'] in (8.0, 10.0)
            assert original['source_contract'] == raw['source_contract']
            assert original['tooling_sha256'] == raw['tooling_sha256'] and original['image_id'] == raw['image_id']
            assert all(original['recipe_sha256'][name] == raw['recipe_sha256'][name]
                       for name in ('run.tcl', 'report.tcl', 'component.xdc'))
            assert original['clock_period_ns'] == raw['clock_period_ns']
            answer['component_fresh_repeat_qualified_clocks_MHz'].append(1000 / raw['clock_period_ns'])
            answer['component_fresh_repeat_qualified_sources'].append(dict(composition=entry['composition'], clock_MHz=1000/raw['clock_period_ns'], source_sha256=raw['source_contract']['source_sha256'], initial_receipt=entry['clean_repeat_of'], repeat_receipt=entry['receipt'], scope='Only this exact out-of-context component source/tool/recipe; no full-parent or hardware clock claim.'))
    answer['status'] = 'V119_MEASURED_RESULTS_SEPARATE_OPEN_MILESTONES'
    (AREA / 'results.json').write_text(json.dumps(answer, indent=2, sort_keys=True) + '\n')
    print(answer['status'], len(answer['native']), 'native runs', len(answer['live']), 'LIVE cases')


if __name__ == '__main__':
    main()
