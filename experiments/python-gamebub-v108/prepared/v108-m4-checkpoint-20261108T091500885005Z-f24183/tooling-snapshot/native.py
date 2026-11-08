#!/usr/bin/env python3
"""Prepare and launch one policy/grant/audit-bound V108 implementation trial."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v108'
FLOW=ROOT/'fpga/experiments/cu66-v108-flow'
MATRIX=AREA/'native-matrix.json'
POLICY=AREA/'study-policy.json'
BUILD_ROOT=Path('/home/lori/gamebub-build/cu66-v69')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.relative_to(ROOT))
def load(p):return json.loads(p.read_text())

def qualification():
    m=load(MATRIX);c=m['source_contract'];assert m['clock_period_ns']==10 and m['part']=='xc7a100tcsg324-1'
    for pk,hk in (('selection_path','selection_sha256'),('parent_receipt','parent_receipt_sha256'),('parent_inputs','parent_inputs_sha256'),('canonical_qualification','canonical_sha256'),('clock_constraints','clock_constraints_sha256')):assert sha(ROOT/c[pk])==c[hk],pk
    q=load(ROOT/c['canonical_qualification']);parent=load(ROOT/c['parent_receipt']);inp=load(ROOT/c['parent_inputs'])
    assert q['status']=='PASS_EXACT_THRESHOLD_CANONICAL' and q['actual_RTL_run']
    assert parent['observed_exit_code']==0 and parent['routing_checkpoint_written'] and parent['source_snapshot_unchanged']
    assert parent['clock_loaded_before_synthesis'] and c['parent_clock_loaded_before_synthesis']
    assert inp['source_sha256']==c['source_sha256'] and inp['source_origins']==c['source_origins']
    actual={v['path']:v['sha256'] for v in c['source_origins'].values()};expected={k:v for k,v in q['source_sha256'].items() if Path(k).suffix in ('.sv','.svh')};assert actual==expected and len(actual)==18
    for alias,entry in c['source_origins'].items():assert sha(ROOT/entry['path'])==entry['sha256']==c['source_sha256'][alias],alias
    p=Path(c['synthesis_checkpoint']['external_path']);assert sha(p)==c['synthesis_checkpoint']['sha256'] and p.stat().st_size==c['synthesis_checkpoint']['bytes']
    assert sha(FLOW/'component.xdc')==c['clock_constraints_sha256']
    assert sha(FLOW/'report.tcl')==sha(ROOT/'fpga/experiments/cu66-v107-flow/report.tcl')
    assert len(m['trials'])==6 and [x['id'] for x in m['trials']]==['m'+str(i) for i in range(6)]
    return m

def parser_self_test():
    p=FLOW/'run_native.py';s=importlib.util.spec_from_file_location('v108_native_runner',p);mod=importlib.util.module_from_spec(s);s.loader.exec_module(mod)
    folder=ROOT/'experiments/python-gamebub-v107/native/20261108T081254078678Z/reports';r=mod.parse_reports(folder)
    assert r['timing']['WNS_ns']==-2.333 and r['timing']['setup_failing']==21433
    assert r['timing']['WHS_ns']==.096 and r['timing']['WPWS_ns']==3.75
    assert r['routing']['fully_routed_nets']==r['routing']['routable_nets']==65912 and r['routing']['routing_errors']==0
    assert r['clock_10ns'] and not r['component_internal_100MHz_pass']
    return dict(status='PASS_EXISTING_NATIVE_REPORT_PARSER',runner_sha256=sha(p),reports={rel(x):sha(x) for x in folder.iterdir() if x.name in ('route-timing-summary.rpt','route-check-timing.rpt','route-clocks.rpt','route-status.rpt','route-setup-paths.rpt')},observed=r,scope='Parser qualification against immutable native reports only; no new FPGA/RTL execution.')

def prepare(trial_id,mode,repeat_of):
    matrix=qualification();entry=next(x for x in matrix['trials'] if x['id']==trial_id);c=matrix['source_contract'];test=parser_self_test()
    if mode=='rtl':
        assert repeat_of is not None,'A clean RTL repeat must name the source-qualified previous trial receipt'
        previous=load(repeat_of);assert previous['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and previous['trial_id']==trial_id
        assert previous['native_matrix_sha256']==sha(MATRIX) and previous['source_sha256']==c['source_sha256']
        assert previous['directives']=={k:entry[k] for k in ('opt','place','phys_opt','phys_opt_stage','route')}
        ancestry=dict(path=rel(repeat_of),sha256=sha(repeat_of))
    else:assert repeat_of is None;ancestry=None
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6];build=BUILD_ROOT/('v108-'+trial_id+'-'+mode+'-'+stamp);build.mkdir();out=AREA/'prepared'/build.name;out.mkdir(parents=True)
    for alias,source in c['source_origins'].items():
        dest=build/'snapshot'/alias;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source['path'],dest);assert sha(dest)==c['source_sha256'][alias]
    for name in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/name,build/name)
    mapped=Path('/build')/build.name
    def word(value):
        s=str(value);assert not any(x in s for x in '{}\r\n');return '{'+s+'}'
    rtl=sorted(n for n in c['source_sha256'] if n.endswith('.sv'));headers=sorted(n for n in c['source_sha256'] if n.endswith('.svh'));assert len(rtl)==17 and len(headers)==1
    lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial_id),'set start_mode '+word(mode),'set opt_directive '+word(entry['opt']),'set place_directive '+word(entry['place']),'set phys_directive '+word(entry['phys_opt'] or 'NONE'),'set route_directive '+word(entry['route']),
           'set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in rtl)+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/Path(n).parent) for n in headers)+']','set constraint_file '+word(mapped/'component.xdc')]
    (build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
    recipes={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')}
    inp=dict(schema='v108-prepared-implementation-inputs-v1',trial_id=trial_id,start_mode=mode,clean_repeat_of=ancestry,part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        native_matrix_path=rel(MATRIX),native_matrix_sha256=sha(MATRIX),source_contract=c,source_sha256=c['source_sha256'],source_origins=c['source_origins'],parent_synthesis_checkpoint=c['synthesis_checkpoint'],
        directives={k:entry[k] for k in ('opt','place','phys_opt','phys_opt_stage','route')},recipe_sha256=recipes,closure_files=18,RTL_files=17,timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,
        synthesis_strategy='RuntimeOptimized',synthesis_executed=mode=='rtl',hardware_or_full_parent_signoff=False)
    write(build/'inputs.json',inp)
    for name in ('inputs.json','inputs.tcl','run.tcl','report.tcl','component.xdc'):shutil.copyfile(build/name,out/name)
    tooling=[Path(__file__).resolve(),FLOW/'run_native.py',FLOW/'run.tcl',FLOW/'report.tcl',FLOW/'component.xdc'];(out/'tooling-snapshot').mkdir()
    for source in tooling:shutil.copyfile(source,out/'tooling-snapshot'/source.name)
    preflight=dict(schema='v108-native-preflight-v1',status='PREPARED_NOT_RUN',actual_native_run=False,trial_id=trial_id,start_mode=mode,clean_repeat_of=ancestry,prepared_build=str(build),prepared_inputs_sha256=sha(build/'inputs.json'),native_matrix_path=rel(MATRIX),native_matrix_sha256=sha(MATRIX),source_contract=c,directives=inp['directives'],source_sha256=c['source_sha256'],source_origins=c['source_origins'],recipe_sha256=recipes,tooling_sha256={rel(p):sha(p) for p in tooling},parser_self_test=test,
        source_snapshot_unchanged=all(sha(build/'snapshot'/n)==h for n,h in c['source_sha256'].items()),parent_checkpoint_sha256_before=sha(Path(c['synthesis_checkpoint']['external_path'])),limits={k:matrix[k] for k in ('timeout_seconds','max_threads','cpus','memory_limit_bytes','memory_swap_limit_bytes')},clock_period_ns=10.0,part=matrix['part'],hardware_contact=False)
    path=out/'preflight.json';write(path,preflight)
    print('V108_PREPARED',rel(path),sha(path),flush=True)

def launch(preflight_path,grant_path,audit_path,license_file):
    matrix=qualification();pre=load(preflight_path);assert pre['status']=='PREPARED_NOT_RUN' and pre['native_matrix_sha256']==sha(MATRIX)
    for n,h in pre['tooling_sha256'].items():assert sha(ROOT/n)==h,('tooling drift',n)
    build=Path(pre['prepared_build']);build.relative_to(BUILD_ROOT);assert sha(build/'inputs.json')==pre['prepared_inputs_sha256']
    inp=load(build/'inputs.json');assert inp['source_sha256']==matrix['source_contract']['source_sha256'] and inp['source_origins']==matrix['source_contract']['source_origins']
    assert inp['directives']==pre['directives'] and inp['clean_repeat_of']==pre['clean_repeat_of']
    for n,h in inp['source_sha256'].items():assert sha(build/'snapshot'/n)==h,n
    for n,h in inp['recipe_sha256'].items():assert sha(build/n)==h,n
    policy=load(POLICY);grant=load(grant_path);audit=load(audit_path)
    assert policy['native_matrix_path']==rel(MATRIX) and policy['native_matrix_sha256']==sha(MATRIX)
    assert policy['clock_period_ns']==10 and policy['max_heavy_jobs']==2 and policy['max_native_initial_trials']==6 and policy['max_native_clean_repeats']==1
    assert grant['enabled'] is True and grant['heavy_slot_granted'] is True
    for k,v in dict(trial_id=pre['trial_id'],start_mode=pre['start_mode'],preflight=rel(preflight_path),preflight_sha256=sha(preflight_path),native_matrix_sha256=sha(MATRIX)).items():assert grant[k]==v,('grant mismatch',k)
    assert audit['status']=='PASS_V108_NATIVE_PREFLIGHT_AUDIT' and audit['preflight']==rel(preflight_path) and audit['preflight_sha256']==sha(preflight_path)
    assert audit['grant']==rel(grant_path) and audit['grant_sha256']==sha(grant_path) and audit['policy_sha256']==sha(POLICY)
    existing=[]
    for p in (AREA/'native').glob('*/receipt.json'):
        r=load(p);existing.append(r)
    mode=pre['start_mode'];limit=6 if mode=='checkpoint' else 1
    assert sum(r['start_mode']==mode for r in existing)<limit,('declared trial/repeat cap',mode)
    assert not any(r['start_mode']==mode and r['trial_id']==pre['trial_id'] for r in existing),'No silent trial retry'
    dispatch_path=AREA/'coordination'/('native-dispatch-'+build.name+'.json');dispatch_path.parent.mkdir(exist_ok=True)
    record=dict(schema='v108-native-immutable-dispatch-v1',status='DISPATCHED_TO_RUNNER',trial_id=pre['trial_id'],start_mode=mode,prepared_inputs_sha256=sha(build/'inputs.json'),prepared_build=str(build),preflight=rel(preflight_path),preflight_sha256=sha(preflight_path),grant=rel(grant_path),grant_sha256=sha(grant_path),policy=rel(POLICY),policy_sha256=sha(POLICY),independent_audit=rel(audit_path),independent_audit_sha256=sha(audit_path),native_matrix_path=rel(MATRIX),native_matrix_sha256=sha(MATRIX))
    with dispatch_path.open('x') as f:f.write(json.dumps(record,indent=2,sort_keys=True)+'\n')
    command=[sys.executable,str(FLOW/'run_native.py'),'--build',str(build),'--license-file',str(license_file),'--dispatch',str(dispatch_path)]
    proc=subprocess.run(command,cwd=ROOT)
    write(AREA/'coordination'/('native-completion-'+build.name+'.json'),dict(schema='v108-native-dispatch-completion-v1',dispatch=rel(dispatch_path),dispatch_sha256=sha(dispatch_path),runner_exit_code=proc.returncode))
    proc.check_returncode()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--trial',choices=['m'+str(i) for i in range(6)]);ap.add_argument('--mode',choices=['checkpoint','rtl'],default='checkpoint');ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--grant',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));args=ap.parse_args()
    if args.run:
        assert args.preflight and args.grant and args.audit
        launch(args.preflight.resolve(),args.grant.resolve(),args.audit.resolve(),args.license_file)
    else:
        assert args.trial and not(args.preflight or args.grant or args.audit)
        prepare(args.trial,args.mode,args.repeat_of.resolve() if args.repeat_of else None)

if __name__=='__main__':main()
