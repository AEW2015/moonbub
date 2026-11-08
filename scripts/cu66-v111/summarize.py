#!/usr/bin/env python3
"""Summarize actual V111 receipts, keeping clock and harness scopes separate."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v111'


def pin(p):
    return dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    policy = json.loads((AREA / 'study-policy.json').read_text())
    control_path = ROOT / policy['frozen_v110_count_receipt']
    assert pin(control_path)['sha256'] == policy['frozen_v110_count_receipt_sha256']
    control = json.loads(control_path.read_text())
    rows = []
    for p in sorted((AREA / 'native').glob('*/receipt.json')):
        d = json.loads(p.read_text())
        rows.append(dict(receipt=pin(p), trial_id=d['trial_id'], status=d['status'],
                         period_ns=d['clock_period_ns'], clean_repeat_of=d['clean_repeat_of'],
                         source_sha256=d['source_contract']['source_sha256'],
                         recipe_sha256=d['recipe_sha256'], image_id=d['image_id'],
                         result=d.get('result'), source_unchanged=d.get('source_snapshot_unchanged'),
                         recipe_unchanged=d.get('recipe_unchanged')))
    targets = {}
    for period in (10.0, 8.0):
        completed = [r for r in rows if r['period_ns'] == period and r['result']]
        passing = [r for r in completed if r['result']['component_internal_target_pass']]
        repeated = []
        for r in passing:
            if not r['clean_repeat_of']:
                continue
            parent = next((x for x in passing if x['receipt'] == r['clean_repeat_of']), None)
            assert parent is not None
            assert parent['source_sha256'] == r['source_sha256'] and parent['image_id'] == r['image_id']
            assert all(parent['recipe_sha256'][n] == r['recipe_sha256'][n] for n in ('run.tcl', 'report.tcl', 'component.xdc'))
            repeated.append(r['receipt'])
        best = max(completed, key=lambda r: r['result']['timing']['WNS_ns']) if completed else None
        targets[str(int(1000 / period))] = dict(period_ns=period, completed=len(completed),
                                              any_single_pass=bool(passing), fresh_repeat_pass=bool(repeated),
                                              repeated_receipts=repeated,
                                              best_diagnostic=None if best is None else dict(receipt=best['receipt'], timing=best['result']['timing']))
    evidence = {}
    for name in ('header/results.json', 'canonical/combined/results.json', 'harness/results.json', 'harness/trace-results.json', 'harness/trace-accounting.json'):
        p = AREA / name
        if p.exists():
            d = json.loads(p.read_text())
            evidence[name] = dict(pin=pin(p), status=d['status'])
    running = [r['trial_id'] for r in rows if r['status'] == 'RUNNING']
    comparisons = []
    for name, base in [('header-100', dict(receipt=pin(control_path), result=control['result']))]:
        candidate = next((r for r in rows if r['trial_id'] == name and r['result'] and not r['clean_repeat_of']), None)
        if candidate:
            a, b = candidate['result']['timing'], base['result']['timing']
            comparisons.append(dict(candidate=candidate['receipt'], control=base['receipt'], period_ns=10.0,
                                    WNS_change_ns=round(a['WNS_ns'] - b['WNS_ns'], 3),
                                    setup_failure_change=a['setup_failing'] - b['setup_failing']))
    base125 = next((r for r in rows if r['trial_id'] == 'count-125' and r['result'] and not r['clean_repeat_of']), None)
    header125 = next((r for r in rows if r['trial_id'] == 'header-125' and r['result'] and not r['clean_repeat_of']), None)
    if base125 and header125:
        a, b = header125['result']['timing'], base125['result']['timing']
        comparisons.append(dict(candidate=header125['receipt'], control=base125['receipt'], period_ns=8.0,
                                WNS_change_ns=round(a['WNS_ns'] - b['WNS_ns'], 3),
                                setup_failure_change=a['setup_failing'] - b['setup_failing']))
    if targets['125']['fresh_repeat_pass']:
        status = 'V111_125MHZ_COMPONENT_QUALIFIED_SYSTEM_OPEN'
    elif targets['100']['fresh_repeat_pass']:
        status = 'V111_100MHZ_COMPONENT_QUALIFIED_125MHZ_SYSTEM_OPEN'
    else:
        status = 'V111_TIMING_IN_PROGRESS' if running else 'V111_TIMING_OPEN'
    result = dict(schema='v111-source-bound-evidence-summary-v1', status=status,
                  frozen_v110_100MHz_control=dict(receipt=pin(control_path), reused_not_rerun=True, timing=control['result']['timing']),
                  same_clock_comparisons=comparisons,
                  header_adoption=('NOT_SELECTED_TIMING_REGRESSION_BOTH_CLOCKS' if len(comparisons) == 2 and all(r['WNS_change_ns'] < 0 for r in comparisons) else 'PENDING_MEASURED_SELECTION'),
                  clock_targets=targets, native_trials=rows, running_trials=running, evidence=evidence,
                  target_scope='clock_targets best_diagnostic/completed counts are NEW V111 trials only; frozen V110 control is recorded separately and retained when better.',
                  coded_width=720, coded_height=480, frame_cap_bytes=49152, profile='CS88 q16/all-BR88',
                  harness_scope='Actual emulated receiver-core JPEG/experimental QSPI functional baseline; not synchronized full system.',
                  sunshine_executed=False, guest_GP_SPI_DMA_qualified=False, shared_simulation_time=False,
                  full_production_firmware_qualified=False, production_SRAM_qualified=False,
                  full_custom_top_qualified=False, hardware_30fps=False,
                  complete_validated_decode_under10ms=False, hardware_contact=False, bitstream_generated=False)
    (AREA / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    with (AREA / 'native-comparison.csv').open('w', newline='') as stream:
        fields = ['trial', 'period_ns', 'repeat', 'status', 'WNS_ns', 'TNS_ns', 'setup_failing', 'WHS_ns', 'WPWS_ns', 'routing_errors', 'component_internal_target_pass']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        d = control['result']
        writer.writerow(dict(trial='V110 Count frozen 100MHz control (reused)', period_ns=10.0, repeat=False,
                             status=control['status'], **{k: d['timing'][k] for k in ('WNS_ns', 'TNS_ns', 'setup_failing', 'WHS_ns', 'WPWS_ns')},
                             routing_errors=d['routing']['routing_errors'], component_internal_target_pass=d['component_internal_100MHz_pass']))
        for r in rows:
            if r['result']:
                d = r['result']
                writer.writerow(dict(trial=r['trial_id'], period_ns=r['period_ns'], repeat=bool(r['clean_repeat_of']), status=r['status'],
                                     **{k: d['timing'][k] for k in ('WNS_ns', 'TNS_ns', 'setup_failing', 'WHS_ns', 'WPWS_ns')},
                                     routing_errors=d['routing']['routing_errors'], component_internal_target_pass=d['component_internal_target_pass']))
    print(json.dumps(dict(status=status, running=running, targets=targets), sort_keys=True))


if __name__ == '__main__':
    main()
