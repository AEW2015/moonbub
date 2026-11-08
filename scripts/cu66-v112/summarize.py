#!/usr/bin/env python3
"""Summarize actual V112 receipts, keeping clock and harness scopes separate."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v112'


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
    for name in ('control/results.json', 'canonical/results.json', 'harness/results.json', 'inventory/control-baseline.json', 'cdc/results.json'):
        p = AREA / name
        if p.exists():
            d = json.loads(p.read_text())
            evidence[name] = dict(pin=pin(p), status=d['status'])
    running = [r['trial_id'] for r in rows if r['status'] == 'RUNNING']
    comparisons = []
    frozen125 = ROOT/'experiments/python-gamebub-v111/native/20261108T183002986106Z/receipt.json'
    base125 = json.loads(frozen125.read_text())
    assert base125['trial_id']=='count-125' and base125['result']['timing']['WNS_ns']==-3.264
    for name, basepath, base, period in [('control-100', control_path, control, 10.0), ('control-125', frozen125, base125, 8.0)]:
        candidate = next((r for r in rows if r['trial_id']==name and r['result'] and not r['clean_repeat_of']),None)
        if candidate:
            a,b=candidate['result']['timing'],base['result']['timing']
            comparisons.append(dict(candidate=candidate['receipt'],control=pin(basepath),period_ns=period,
                                    WNS_change_ns=round(a['WNS_ns']-b['WNS_ns'],3),
                                    setup_failure_change=a['setup_failing']-b['setup_failing']))
    if targets['125']['fresh_repeat_pass']:
        status = 'V112_125MHZ_COMPONENT_QUALIFIED_SYSTEM_OPEN'
    elif targets['100']['fresh_repeat_pass']:
        status = 'V112_100MHZ_COMPONENT_QUALIFIED_125MHZ_SYSTEM_OPEN'
    else:
        status = 'V112_TIMING_IN_PROGRESS' if running else 'V112_TIMING_OPEN'
    result = dict(schema='v112-source-bound-evidence-summary-v1', status=status,
                  frozen_v110_100MHz_control=dict(receipt=pin(control_path), reused_not_rerun=True, timing=control['result']['timing']),
                  frozen_v111_125MHz_control=dict(receipt=pin(frozen125), reused_not_rerun=True, timing=base125['result']['timing']),
                  same_clock_comparisons=comparisons,
                  candidate_adoption=('FRESH_REPEAT_COMPONENT_125_QUALIFIED' if targets['125']['fresh_repeat_pass'] else 'FRESH_REPEAT_COMPONENT_100_QUALIFIED_125_OPEN' if targets['100']['fresh_repeat_pass'] else 'NOT_TIMING_QUALIFIED'),
                  clock_targets=targets, native_trials=rows, running_trials=running, evidence=evidence,
                  target_scope='clock_targets best_diagnostic/completed counts are NEW V112 trials only; frozen V110 control is recorded separately and retained when better.',
                  coded_width=720, coded_height=480, frame_cap_bytes=49152, profile='CS88 q16/all-BR88',
                  harness_scope='Bounded deterministic replay adapter through actual JPEG/QSPI/memory/display RTL; guest CPU and Sunshine integration remain separate.',
                  sunshine_executed=False, guest_GP_SPI_DMA_qualified=False, shared_guest_RTL_time_qualified=False, adapter_RTL_common_time_executed=('harness/results.json' in evidence and evidence['harness/results.json']['status']=='PASS_EXPLICIT_SOURCE_ADAPTER_JPEG_RTL'),
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
