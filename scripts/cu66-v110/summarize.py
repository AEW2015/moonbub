#!/usr/bin/env python3
"""Summarize actual V110 receipts without turning OOC results into hardware claims."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v110'
BASE = ROOT / 'experiments/python-gamebub-v109/native/20261108T121030620057Z/receipt.json'
FRONTIER = ROOT / 'experiments/python-gamebub-v109/native/20261108T112057270069Z/receipt.json'


def load(p):
    return json.loads(p.read_text())


def pin(p):
    return {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def main():
    base = load(BASE)
    rows = []
    running = []
    for p in sorted([*(AREA / 'native').glob('*/receipt.json'), *(AREA / 'default-native').glob('*/receipt.json'), *(AREA / 'cursors-native').glob('*/receipt.json'), *(AREA / 'address-cursors-native').glob('*/receipt.json'), *(AREA / 'count-domain-native').glob('*/receipt.json')]):
        d = load(p)
        assert d['part'] == base['part'] == 'xc7a100tcsg324-1'
        assert d['clock_period_ns'] == base['clock_period_ns'] == 10.0
        if d['status'] == 'RUNNING':
            running.append(d['trial_id'])
            continue
        row = dict(receipt=pin(p), trial_id=d['trial_id'], status=d['status'],
                   actual_route_finished=d.get('component_route_finished', False),
                   directives=d['directives'], synth_directive=d.get('synth_directive','RuntimeOptimized'), runtime_control=d.get('runtime_control'), synthesis_executed=d['synthesis_executed'],
                   clean_repeat_of=d['clean_repeat_of'], result=d.get('result'),
                   source_unchanged=d.get('source_snapshot_unchanged'), recipe_unchanged=d.get('recipe_unchanged'))
        if row['result']:
            row['WNS_change_vs_V109_FETCH_ns'] = round(row['result']['timing']['WNS_ns'] - base['result']['timing']['WNS_ns'], 3)
            row['absolute_TNS_reduction_vs_V109_FETCH_percent'] = round(100 * (1 - abs(row['result']['timing']['TNS_ns']) / abs(base['result']['timing']['TNS_ns'])), 3)
            row['setup_failure_reduction_vs_V109_FETCH_percent'] = round(100 * (1 - row['result']['timing']['setup_failing'] / base['result']['timing']['setup_failing']), 3)
        rows.append(row)
    completed = [r for r in rows if r['actual_route_finished'] and r['result']]
    best = max(completed, key=lambda r: r['result']['timing']['WNS_ns']) if completed else None
    positive = [r for r in completed if r['result']['component_internal_100MHz_pass']]
    repeated = [r for r in positive if r['clean_repeat_of'] and any(x['receipt'] == r['clean_repeat_of'] for x in positive)]
    proofs = []
    unqualified = []
    for directory in ['busy','fault','dequant','ready','rice','prefix','cursors','count-domain','canonical/busy','canonical/combined','canonical/fault','canonical-dequant/combined','canonical-ready-rice/combined','canonical-prefix/combined','canonical-cursors/combined','canonical-address-cursors/combined','canonical-count-domain/combined']:
        p = AREA / directory / 'results.json'
        if p.exists():
            d = load(p)
            row = dict(receipt=pin(p), status=d['status'], scope=directory, actual_RTL_run=d.get('actual_RTL_run',False))
            if row['actual_RTL_run'] and d['status'] in ('PASS','PASS_EXACT_V110_CANONICAL'):
                proofs.append(row)
            else:
                unqualified.append(row)
    result = dict(schema='v110-actual-receipt-summary-v1', status='V110_TIMING_PREREQUISITES_OPEN' if not repeated else 'V110_COMPONENT_TIMING_REPEATED_HARDWARE_OPEN',
                  baseline=pin(BASE), prior_diagnostic_frontier=pin(FRONTIER), prior_diagnostic_frontier_WNS_ns=load(FRONTIER)['result']['timing']['WNS_ns'],
                  clock_period_ns=10.0, part=base['part'], frame_width=720, frame_height=480,
                  frame_cap_bytes=49152, format='CS88 q16/all-BR88', proofs=proofs, unqualified_current_proof_attempts=unqualified, native_trials=rows, running_trials=running,
                  best_completed_trial=None if best is None else best['trial_id'],
                  best_selection_scope='Largest completed routed WNS; negative result is a diagnostic frontier, not a qualified clock.',
                  component_internal_100MHz_any_pass=bool(positive), component_internal_100MHz_fresh_repeat_pass=bool(repeated),
                  repeated_positive_trials=[r['trial_id'] for r in repeated],
                  integrated_parent_timing_qualified=False, hardware_30fps=False, complete_validated_decode_under10ms=False,
                  hardware_contact=False, bitstream_generated=False,
                  note='All route rows are OOC decoder measurements. Parent I/O/CDC/memory/display integration and calibrated complete publication measurements remain open.')
    (AREA / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    with (AREA / 'native-comparison.csv').open('w', newline='') as f:
        columns = ['trial', 'WNS_ns', 'TNS_ns', 'setup_failing', 'WHS_ns', 'WPWS_ns', 'routing_errors', 'component_internal_100MHz_pass']
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for name, data in [('V109 fault-only prior frontier', load(FRONTIER)['result']),('V109 FETCH control baseline', base['result'])] + [(r['trial_id'], r['result']) for r in completed]:
            writer.writerow(dict(trial=name, **{k: data['timing'][k] for k in columns[1:6]}, routing_errors=data['routing']['routing_errors'], component_internal_100MHz_pass=data['component_internal_100MHz_pass']))
    print(json.dumps({k: result[k] for k in ['status', 'best_completed_trial', 'component_internal_100MHz_any_pass', 'component_internal_100MHz_fresh_repeat_pass']}))


if __name__ == '__main__':
    main()
