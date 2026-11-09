#!/usr/bin/env python3
"""Summarize source-bound V115 evidence, with explicit component/system limits."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v115'


def load(p):
    return json.loads(p.read_text())


def pin(p):
    return dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    spec=importlib.util.spec_from_file_location('native',ROOT/'scripts/cu66-v115/native.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    policy=load(native.POLICY)
    native.qualify('integrated-125',policy)
    controls=[]
    for meta in policy['comparison_controls']:
        p=ROOT/meta['path'];d=load(p)
        assert pin(p)['sha256']==meta['sha256']
        controls.append(dict(label=meta['label'],receipt=pin(p),period_ns=meta['period_ns'],
                             reused_not_rerun=True,result=native.parse_reports(p.parent/'reports',meta['period_ns'])))
    rows=[]
    paths=sorted((AREA/'native').glob('*/receipt.json'))+sorted((AREA/'refined/native').glob('*/receipt.json'))+sorted((AREA/'final/native').glob('*/receipt.json'))
    for p in paths:
        d=load(p)
        if d.get('result'):
            assert native.parse_reports(p.parent/'reports',d['clock_period_ns'])==d['result']
            for name,expected in d['retained_artifact_sha256'].items():
                assert pin(p.parent/name)['sha256']==expected,name
        rows.append(dict(receipt=pin(p),composition=('refined-header-tile-write' if '/refined/' in str(p) else 'final' if '/final/' in str(p) else 'initial-five-body'),trial_id=d['trial_id'],status=d['status'],
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
    for name in ('inverse/results.json','ingress/results.json','scratch/results.json','scratch-extra/results.json',
                 'spatial/results.json','control-peer/results.json','performance.json','inventory/inventory.json','jpeg-wire/results.json',
                 'live-parent/results.json','refined/ingress/results.json','refined/scratch/results.json','refined/spatial/results.json','refined/control-peer/results.json',
                 'refined/performance.json','refined/live-parent/results.json','refined/live-performance.json',
                 'final/ingress/results.json','owner-cut-focus/results.json','final/spatial/results.json','final/control-peer/results.json','final/live-parent/results.json','final/performance.json',
                 'audit/final-focused-runtime.json','audit/final-peer-runtime.json','audit/final-functional-terminal.json','audit/final-native-terminal.json',
                 'final/register-inspection/results.json','audit/final-mapped-registers.json',
                 'audit/functional-final.json','audit/initial-native-terminal.json','audit/refined-functional-final.json','audit/refined-native-terminal.json'):
        p=AREA/name
        if not p.exists():continue
        d=load(p)
        evidence[name]=dict(pin=pin(p),status=d.get('status','SELECTED_PIN'))
    # A bounded boundary/partition PASS remains distinct from full-parent signoff.
    def selected_pass(name,expected_status="PASS"):
        p=AREA/name
        if not p.is_file():return False
        d=load(p)
        if d.get('status')!=expected_status:return False
        if 'path' in d:
            raw=ROOT/d['path'];assert pin(raw)['sha256']==d['sha256'];d=load(raw)
        elif 'selected_report' in d:
            raw=ROOT/d['selected_report'];assert pin(raw)['sha256']==d['selected_report_sha256'];d=load(raw)
        return d.get('status')==expected_status and d.get('actual_RTL_run') is True
    jpeg_boundary=selected_pass('jpeg-wire/results.json')
    validated_partition=selected_pass('live-parent/results.json','PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION')
    validated_refined_partition=selected_pass('refined/live-parent/results.json','PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION')
    validated_final_partition=selected_pass('final/live-parent/results.json','PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION')
    final_validated_rows=[]
    if validated_final_partition:
        sel=load(AREA/'final/live-parent/results.json');raw=ROOT/sel['path'];assert pin(raw)['sha256']==sel['sha256']
        live=load(raw)
        for item in live['runs']:
            c=item['live_case'];assert c['status']=='PASS'
            cycles=c['last_outer_to_commit_cycles'];assert cycles==c['commit_cycle']-c['last_outer_cycle']
            final_validated_rows.append(dict(profile=item['profile'],seed=item['seed'],last_required_byte_to_validated_commit_cycles=cycles,
                conditional_ms_at125MHz=cycles/125000,conditional_strict_under10ms_at125MHz=cycles<1250000))
        assert len(final_validated_rows)==2
    running=[r['composition']+':'+r['trial_id'] for r in rows if r['status']=='RUNNING']
    status=('V115_125MHZ_COMPONENT_QUALIFIED_SYSTEM_OPEN' if targets['125']['fresh_repeat_pass'] else
            'V115_100MHZ_COMPONENT_QUALIFIED_125MHZ_SYSTEM_OPEN' if targets['100']['fresh_repeat_pass'] else
            'V115_TIMING_IN_PROGRESS' if running else 'V115_TIMING_OPEN')
    contracts={'initial':policy['functional_contract']}
    for label in ('refined','final'):
        pp=AREA/label/'study-policy.json'
        if pp.exists():contracts[label]=load(pp)['functional_contract']
    selected_contract=contracts.get('final',contracts.get('refined',contracts['initial']))
    result=dict(schema='v115-source-bound-evidence-summary-v1',status=status,comparison_controls=controls,
        same_clock_comparisons=comparisons,clock_targets=targets,native_trials=rows,running_trials=running,evidence=evidence,
        candidate_adoption='FRESH_REPEAT_COMPONENT_QUALIFIED' if any(t['fresh_repeat_pass'] for t in targets.values()) else 'NOT_TIMING_QUALIFIED',
        coded_width=720,coded_height=480,frame_cap_bytes=49152,profile='CS88 q16/all-BR88',
        functional_contract=selected_contract,functional_contracts=contracts,
        roadmap_V115_complete_parent_exit_qualified=False,SR14_syntax_adopted=False,
        fresh_JPEG_boundary_is_custom_codec_parent=False,
        actual_QSPI_JPEG_boundary_pass=jpeg_boundary,keyframe_C2_HUD_seal_partition_pass=validated_partition,refined_keyframe_C2_HUD_seal_partition_pass=validated_refined_partition,final_keyframe_C2_HUD_seal_partition_pass=validated_final_partition,
        actual_V97_custom_decoder_common_clock_executed=True,actual_QSPI_custom_decoder_executed=False,
        sunshine_executed=False,ESP32_firmware_executed=False,full_production_firmware_qualified=False,
        bounded_final_validated_latency=dict(receipt=pin(raw)if validated_final_partition else None,
            interval='Last required accepted outer byte to validated abstract publication commit',rows=final_validated_rows,
            distinct_keyframe_fixtures=1,achieved_clock_qualified=False,physical_memory_display_qualified=False),
        C2_HUD_seal_and_publication_qualified=False,full_custom_top_qualified=False,
        hardware_30fps=False,complete_validated_decode_under10ms=False,hardware_contact=False,bitstream_generated=False)
    (AREA/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    fields=['trial','period_ns','repeat','WNS_ns','TNS_ns','setup_failing','WHS_ns','WPWS_ns','routing_errors','component_internal_target_pass']
    with (AREA/'native-comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in [dict(trial=c['label']+' (frozen)',period_ns=c['period_ns'],repeat=False,result=c['result']) for c in controls]+[
            dict(trial=r['composition']+':'+r['trial_id'],period_ns=r['period_ns'],repeat=bool(r['clean_repeat_of']),result=r['result']) for r in rows if r['result']]:
            d=r.pop('result')
            w.writerow(dict(r,**{k:d['timing'][k] for k in ('WNS_ns','TNS_ns','setup_failing','WHS_ns','WPWS_ns')},
                            routing_errors=d['routing']['routing_errors'],component_internal_target_pass=d['component_internal_target_pass']))
    lines=['# V115 selected evidence status','',
        'Generated from selected receipts and completed routed reports. A component pass does not qualify the complete operational parent.','',
        '| Evidence | Selected status |','| --- | --- |']
    for name,label in [('spatial/results.json','Initial decoder/transport'),('control-peer/results.json','Initial peer faults'),
        ('refined/ingress/results.json','Refined ingress'),('refined/scratch/results.json','Refined scratch'),
        ('refined/spatial/results.json','Refined decoder/transport'),('refined/control-peer/results.json','Refined peer faults'),
        ('jpeg-wire/results.json','Actual QSPI/JPEG boundary'),('live-parent/results.json','Initial-component C2/HUD/seal partition'),
        ('refined/live-parent/results.json','Refined-component C2/HUD/seal partition'),
        ('final/ingress/results.json','Final request-bounds focus'),('owner-cut-focus/results.json','Final owner-certificate focus'),
        ('final/spatial/results.json','Final decoder/transport'),('final/control-peer/results.json','Final peer faults'),
        ('final/live-parent/results.json','Final-component C2/HUD/seal partition')]:
        path=AREA/name
        selected=load(path).get('status','UNKNOWN') if path.is_file() else 'NO_SELECTED_RESULT'
        lines.append(f'| {label} | [{selected}](../../experiments/python-gamebub-v115/{name}) |' if path.is_file() else f'| {label} | {selected} |')
    lines += ['', '| Composition | Clock | Setup WNS | Setup failures | Hold / pulse / routing errors | Internal OOC target |',
        '| --- | ---: | ---: | ---: | --- | --- |']
    for row in rows:
        if not row['result']:continue
        r=row['result'];t=r['timing'];frequency=int(1000/row['period_ns'])
        label=row['composition']+(' fresh repeat' if row['clean_repeat_of'] else '')
        lines.append(f"| {label} | {frequency} MHz | {t['WNS_ns']:.3f} ns | {t['setup_failing']} | {t['hold_failing']} / {t['pulse_failing']} / {r['routing']['routing_errors']} | {'PASS' if r['component_internal_target_pass'] else 'FAIL'} |")
    if final_validated_rows:
        lines += ['', 'Final bounded keyframe validation: last required byte to validated abstract commit (125-MHz conversions remain conditional).', '',
            '| Service profile | Actual cycles | Conditional time at125 MHz | Strict<10 ms |',
            '| --- | ---: | ---: | --- |']
        for r in final_validated_rows:
            lines.append(f"| {r['profile']} | {r['last_required_byte_to_validated_commit_cycles']:,} | {r['conditional_ms_at125MHz']:.6f} ms | {'PASS'if r['conditional_strict_under10ms_at125MHz']else'FAIL'} |")
        lines += ['', 'One distinct keyframe fixture, two service profiles; not a sustained distinct-frame campaign.']
    lines += ['', 'Fresh positive repeat: '+', '.join(f"{k} MHz = {v['fresh_repeat_pass']}"for k,v in targets.items())+'.', '',
        'Complete parent timing/CDC/I/O and SDRAM/LCD integration, sustained hardware 30 fps, and validated full decoding below 10 ms remain open. See [cycle ledger](performance.md), [refined implementation](refined.md), [final cuts](final.md), [parent gaps](full-parent-gap.md), and [machine-readable results](../../experiments/python-gamebub-v115/results.json).','']
    (ROOT/'docs/cu66-v115/status.md').write_text('\n'.join(lines))
    print(json.dumps(dict(status=status,targets=targets),sort_keys=True))


if __name__=='__main__':
    main()
