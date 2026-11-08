#!/usr/bin/env python3
"""Summarize source-bound V113 evidence, with explicit component/system limits."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v113'


def load(p):
    return json.loads(p.read_text())


def pin(p):
    return dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    spec=importlib.util.spec_from_file_location('native',ROOT/'scripts/cu66-v113/native.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    policy=load(native.POLICY)
    native.qualify('spatial-125',policy)
    controls=[]
    for meta in policy['comparison_controls']:
        p=ROOT/meta['path'];d=load(p)
        assert pin(p)['sha256']==meta['sha256']
        controls.append(dict(label=meta['label'],receipt=pin(p),period_ns=meta['period_ns'],
                             reused_not_rerun=True,result=native.parse_reports(p.parent/'reports',meta['period_ns'])))
    rows=[]
    for p in sorted((AREA/'native').glob('*/receipt.json')):
        d=load(p)
        if d.get('result'):
            assert native.parse_reports(p.parent/'reports',d['clock_period_ns'])==d['result']
            for name,expected in d['retained_artifact_sha256'].items():
                assert pin(p.parent/name)['sha256']==expected,name
        rows.append(dict(receipt=pin(p),trial_id=d['trial_id'],status=d['status'],
                         period_ns=d['clock_period_ns'],clean_repeat_of=d['clean_repeat_of'],
                         source_sha256=d['source_contract']['source_sha256'],
                         recipe_sha256=d['recipe_sha256'],image_id=d['image_id'],result=d.get('result'),
                         source_unchanged=d.get('source_snapshot_unchanged'),recipe_unchanged=d.get('recipe_unchanged')))
    targets={}
    for period in (10.0,8.0):
        completed=[r for r in rows if r['period_ns']==period and r['result']]
        passing=[r for r in completed if r['result']['component_internal_target_pass']]
        repeated=[]
        for r in passing:
            if r['clean_repeat_of']:
                parent=next(x for x in passing if x['receipt']==r['clean_repeat_of'])
                assert parent['source_sha256']==r['source_sha256'] and parent['image_id']==r['image_id']
                assert all(parent['recipe_sha256'][n]==r['recipe_sha256'][n] for n in ('run.tcl','report.tcl','component.xdc'))
                repeated.append(r['receipt'])
        best=max(completed,key=lambda r:r['result']['timing']['WNS_ns']) if completed else None
        targets[str(int(1000/period))]=dict(period_ns=period,completed=len(completed),
            any_single_pass=bool(passing),fresh_repeat_pass=bool(repeated),repeated_receipts=repeated,
            best_diagnostic=None if best is None else dict(receipt=best['receipt'],result=best['result']))
    comparisons=[]
    for r in rows:
        if not r['result']:continue
        for c in controls:
            if r['period_ns']!=c['period_ns']:continue
            a,b=r['result']['timing'],c['result']['timing']
            comparisons.append(dict(candidate=r['receipt'],control=c['receipt'],label=c['label'],period_ns=r['period_ns'],
                WNS_change_ns=round(a['WNS_ns']-b['WNS_ns'],3),setup_failure_change=a['setup_failing']-b['setup_failing']))
    evidence={}
    for name in ('geometry/results.json','scratch/results.json','inverse/selected.json','inverse/benchmark-selected.json',
                 'spatial/results.json','lanes/results.json','performance.json'):
        p=AREA/name;d=load(p)
        evidence[name]=dict(pin=pin(p),status=d.get('status','SELECTED_PIN'))
    running=[r['trial_id'] for r in rows if r['status']=='RUNNING']
    status=('V113_125MHZ_COMPONENT_QUALIFIED_SYSTEM_OPEN' if targets['125']['fresh_repeat_pass'] else
            'V113_100MHZ_COMPONENT_QUALIFIED_125MHZ_SYSTEM_OPEN' if targets['100']['fresh_repeat_pass'] else
            'V113_TIMING_IN_PROGRESS' if running else 'V113_TIMING_OPEN')
    result=dict(schema='v113-source-bound-evidence-summary-v1',status=status,comparison_controls=controls,
        same_clock_comparisons=comparisons,clock_targets=targets,native_trials=rows,running_trials=running,evidence=evidence,
        candidate_adoption='FRESH_REPEAT_COMPONENT_QUALIFIED' if any(t['fresh_repeat_pass'] for t in targets.values()) else 'NOT_TIMING_QUALIFIED',
        coded_width=720,coded_height=480,frame_cap_bytes=49152,profile='CS88 q16/all-BR88',
        functional_contract='IV113.1 accepted-event/value/owner contract; old public cycles intentionally not claimed.',
        actual_V97_custom_decoder_common_clock_executed=True,actual_QSPI_custom_decoder_executed=False,
        sunshine_executed=False,ESP32_firmware_executed=False,full_production_firmware_qualified=False,
        C2_HUD_seal_and_publication_qualified=False,full_custom_top_qualified=False,
        hardware_30fps=False,complete_validated_decode_under10ms=False,hardware_contact=False,bitstream_generated=False)
    (AREA/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    fields=['trial','period_ns','repeat','WNS_ns','TNS_ns','setup_failing','WHS_ns','WPWS_ns','routing_errors','component_internal_target_pass']
    with (AREA/'native-comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in [dict(trial=c['label']+' (frozen)',period_ns=c['period_ns'],repeat=False,result=c['result']) for c in controls]+[
            dict(trial=r['trial_id'],period_ns=r['period_ns'],repeat=bool(r['clean_repeat_of']),result=r['result']) for r in rows if r['result']]:
            d=r.pop('result')
            w.writerow(dict(r,**{k:d['timing'][k] for k in ('WNS_ns','TNS_ns','setup_failing','WHS_ns','WPWS_ns')},
                            routing_errors=d['routing']['routing_errors'],component_internal_target_pass=d['component_internal_target_pass']))
    print(json.dumps(dict(status=status,targets=targets),sort_keys=True))


if __name__=='__main__':
    main()
