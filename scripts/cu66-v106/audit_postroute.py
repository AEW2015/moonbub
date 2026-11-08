#!/usr/bin/env python3
"""Independently read one retained physical diagnostic; never select a candidate."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v106/postroute'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def timing(p):
    lines=p.read_text().splitlines()
    for n,line in enumerate(lines):
        if line.strip().startswith('WNS(ns)'):
            v=lines[n+2].split();assert len(v)==12
            return dict(WNS_ns=float(v[0]),TNS_ns=float(v[1]),setup_failing_endpoints=int(v[2]),setup_endpoints=int(v[3]),WHS_ns=float(v[4]),THS_ns=float(v[5]),hold_failing_endpoints=int(v[6]),hold_endpoints=int(v[7]),WPWS_ns=float(v[8]),TPWS_ns=float(v[9]),pulse_failing_endpoints=int(v[10]),pulse_endpoints=int(v[11]))
    raise AssertionError('missing full timing summary')
def route(p):
    text=p.read_text();r={}
    for label,key in (('routable nets','routable'),('fully routed nets','fully_routed'),('nets with routing errors','errors')):
        m=re.search(r'# of '+label+r'[. ]+:[ ]+(\d+)',text);assert m;r[key]=int(m.group(1))
    r['complete_legal']=r['routable']==r['fully_routed'] and r['errors']==0;return r

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-external-checkpoint',action='store_true');args=parser.parse_args()
    sp=AREA/'results.json';s=json.loads(sp.read_text());rp=ROOT/s['selected_receipt'];r=json.loads(rp.read_text());assert {k:v for k,v in s.items() if k!='selected_receipt'}==r
    assert r['parent_checkpoint']['unchanged'] and r['parent_checkpoint']['sha256_before']==r['parent_checkpoint']['sha256_after']=='7c626d0f79ba2c9546d4ac69557fc5541623f4592c7c848c7b65800961efbfd0'
    for p,h in r['source_sha256'].items():assert sha(ROOT/p)==h
    for p,h in r['retained_sha256'].items():assert sha(rp.parent/p)==h
    for n,a in r['artifacts'].items():
        p=rp.parent/'reports'/n
        if p.is_file():assert sha(p)==a['sha256']
    parent=ROOT/r['parent_receipt']['path'];assert sha(parent)==r['parent_receipt']['sha256'] and sha(rp.parent/'parent-receipt.json')==r['parent_receipt']['sha256']
    assert json.loads((rp.parent/'parent-receipt.json').read_text())['artifacts']['route.dcp']['sha256']==r['parent_checkpoint']['sha256_before']
    if args.verify_external_checkpoint:
        assert sha(Path(r['parent_checkpoint']['path']))==r['parent_checkpoint']['sha256_before']
    assert r['timeout_seconds']==600 and r['max_threads']==2 and r['memory_limit_bytes']==8*1024**3 and r['clock_period_ns']==10 and r['part']=='xc7a100tcsg324-1'
    assert r['tools_readonly'] and r['existing_legitimate_license_readonly'] and not any(r[k] for k in ('explicit_retime','clock_or_exception_edits','blanket_fanout_directive','source_changes','hardware_contact','selected_or_promoted','board_IO_CDC_qualified'))
    cmd=r['command'];assert '--rm' in cmd and '--network' in cmd and cmd[cmd.index('--network')+1]=='host' and cmd[cmd.index('--memory')+1]=='8g' and cmd[cmd.index('--cpus')+1]=='2' and '600s' in cmd
    assert any('dst=/parent/route.dcp,readonly' in x for x in cmd)
    tcl=(rp.parent/'run.tcl').read_text();assert tcl.count('\nphys_opt_design -directive AggressiveExplore\n')==1 and 'if {$route_needed} {route_design -directive Default}' in tcl
    assert not re.search(r'^\s*(create_clock|set_input_delay|set_output_delay|set_false_path|set_multicycle_path|create_waiver)\b',tcl,re.M)
    log=(rp.parent/'vivado.log').read_text();assert 'build 6511674' in log or 'Build 6511674' in log
    reports=rp.parent/'reports';out=dict(schema='v106-postroute-independent-report-audit-v1',status='RETAINED_DIAGNOSTIC_AUDITED',auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),parent_checkpoint_unchanged=True,checkpoint_audit_scope='Portable replay verifies recorded execution before/after hashes against retained parent artifact receipt. External DCP is not required; optional --verify-external-checkpoint separately verifies current external bytes without changing this report.',observed_outcome=r['status'],selected_or_promoted=False,limits=['One post-route strategy diagnostic, not another Default full-flow comparison or automatic source promotion.','Clock/input/output/CDC/board qualification remain inherited/open; no hardware FPS or complete decode latency conclusion.'])
    if (reports/'before-timing-summary.rpt').is_file():
        out['before']=dict(timing=timing(reports/'before-timing-summary.rpt'),route=route(reports/'before-route-status.rpt'));native_parent=parent.parent/'reports/route-timing-summary.rpt';assert out['before']['timing']==timing(native_parent) and out['before']['route']['complete_legal']
    if r['status']=='DIAGNOSTIC_FINISHED_REVIEW_REQUIRED':
        assert r['observed_exit_code']==0 and r['diagnostic_finished'] and 'V106_POSTROUTE_DIAGNOSTIC_FINISHED' in log
        out['after']=dict(timing=timing(reports/'after-timing-summary.rpt'),route=route(reports/'after-route-status.rpt'));assert out['after']['route']['complete_legal']
        out['WNS_change_ns']=out['after']['timing']['WNS_ns']-out['before']['timing']['WNS_ns'];out['WHS_change_ns']=out['after']['timing']['WHS_ns']-out['before']['timing']['WHS_ns']
        out['route_Default_needed']=(reports/'route-repair.txt').read_text().strip().endswith('=1')
        for name in ('before','after'):
            p=reports/f'{name}-setup-paths.rpt';text=p.read_text();out[name]['worst_source']=re.search(r'Source:\s+([^\n]+)',text).group(1).strip();out[name]['worst_destination']=re.search(r'Destination:\s+([^\n]+)',text).group(1).strip()
        constraints={name:[line.strip() for line in (reports/f'{name}-effective-timing.xdc').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')] for name in ('before','after')}
        assert constraints['before']==constraints['after'];out['effective_timing_commands_unchanged']=True
        def summary_table(path):
            result={}
            for line in path.read_text().splitlines():
                fields=[x.strip() for x in line.split('|')]
                if len(fields)>5 and fields[2] in ('Warning','Critical Warning','Error') and fields[4].isdigit():result[fields[1]]=dict(severity=fields[2],checks=int(fields[4]))
            return result
        for label in ('drc','methodology'):
            before=summary_table(reports/f'before-{label}.rpt');after=summary_table(reports/f'after-{label}.rpt');assert before==after and len(after)==5;out[label+'_summary_unchanged']=True;out[label+'_summary']=after
        def cells(path):
            result={}
            for line in path.read_text().splitlines():
                fields=[x.strip() for x in line.split('|')]
                if len(fields)>3 and fields[2].isdigit():result[fields[1].rstrip('*')]=int(fields[2])
            return {label:result[label] for label in ('Slice LUTs','Slice Registers','DSPs')}
        out['before']['cells']=cells(reports/'before-capacity.rpt');out['after']['cells']=cells(reports/'after-capacity.rpt')
        out['cell_delta']={label:out['after']['cells'][label]-out['before']['cells'][label] for label in out['before']['cells']}
        path=(reports/'after-setup-paths.rpt').read_text();out['after']['data_path_delay_ns']=float(re.search(r'Data Path Delay:\s+([\d.]+)ns',path).group(1))
        out['after']['logic_delay_ns']=float(re.search(r'logic ([\d.]+)ns',path).group(1));out['after']['route_delay_ns']=float(re.search(r'route ([\d.]+)ns',path).group(1))
        out['internal_setup_met']=out['after']['timing']['WNS_ns']>=0;out['internal_hold_met']=out['after']['timing']['WHS_ns']>=0;out['pulse_met']=out['after']['timing']['WPWS_ns']>=0
    (AREA/'report-audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2))
    if args.verify_external_checkpoint:print('EXTERNAL_PARENT_CHECKPOINT_VERIFIED; portable report unchanged')
if __name__=='__main__':main()
