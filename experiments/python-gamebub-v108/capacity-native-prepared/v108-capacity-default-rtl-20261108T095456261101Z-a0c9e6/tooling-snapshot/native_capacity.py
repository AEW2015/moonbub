#!/usr/bin/env python3
"""Prepare a separately qualified fresh-RTL capacity trial; activation is explicit."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

import native as frozen
import native_clean

ROOT=frozen.ROOT
AREA=frozen.AREA
CONTRACT=AREA/'capacity-native-contract.json'
FOCUS=AREA/'capacity/results.json'
CANONICAL=AREA/'capacity-pipeline/results.json'
RUNNER=frozen.FLOW/'run_native_capacity.py'
REPLACEMENTS=('packed_scratch_v91g2.sv','br88_packet_ingress_sync_v91h.sv','br88_packet_ingress_v91h.sv','br88_pipeline_v91h.sv')

def parser_self_test():
    parent=frozen.parser_self_test()
    spec=importlib.util.spec_from_file_location('v108_capacity_runner',RUNNER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=ROOT/'experiments/python-gamebub-v107/native/20261108T081254078678Z/reports'
    assert module.parse_reports(report)==parent['observed']
    return dict(status='PASS_CAPACITY_RUNNER_NATIVE_REPORT_PARSER',runner_sha256=frozen.sha(RUNNER),baseline_parser_test=parent,
        scope='Read-only actual V107 report parser check; no new RTL, native or hardware run.')

def qualification():
    assert frozen.sha(Path(frozen.__file__))==native_clean.BUILDER_SHA
    matrix=frozen.qualification();focus=frozen.load(FOCUS);canonical=frozen.load(CANONICAL)
    assert focus['status']=='PASS' and focus['actual_RTL_run'] is True
    assert canonical['status']=='PASS_EXACT_CAPACITY_CANONICAL' and canonical['actual_RTL_run'] is True
    c=json.loads(json.dumps(matrix['source_contract']));replaced=[]
    for alias,old in c['source_origins'].items():
        if Path(old['path']).parent.name=='cu66-v107-count-threshold':
            name=Path(old['path']).name;assert name in REPLACEMENTS
            path=ROOT/'fpga/experiments/cu66-v108-capacity'/name;digest=frozen.sha(path)
            assert focus['source_sha256'][frozen.rel(path)]==digest
            c['source_origins'][alias]=dict(path=frozen.rel(path),sha256=digest)
            c['source_sha256'][alias]=digest;replaced.append(name)
    assert set(replaced)==set(REPLACEMENTS)
    actual={e['path']:e['sha256'] for e in c['source_origins'].values()}
    expected={n:h for n,h in canonical['source_sha256'].items() if Path(n).suffix in ('.sv','.svh')}
    assert actual==expected and len(actual)==18,'exact full canonical RTL/header closure required'
    for path,digest in actual.items():assert frozen.sha(ROOT/path)==digest
    c['baseline_canonical_qualification']=dict(path=c['canonical_qualification'],sha256=c['canonical_sha256'])
    c['canonical_qualification']=frozen.rel(CANONICAL);c['canonical_sha256']=frozen.sha(CANONICAL)
    c['capacity_focused_qualification']=dict(path=frozen.rel(FOCUS),sha256=frozen.sha(FOCUS))
    c['capacity_canonical_qualification']=dict(path=frozen.rel(CANONICAL),sha256=frozen.sha(CANONICAL))
    c['source_revision']='V108 capacity variant; source origins below supersede baseline selection/input-card ancestry'
    c['baseline_checkpoint_role']='read-only provenance ancestry only; fresh RTL run does not open checkpoint'
    return matrix,c,native_clean.parent_order(matrix)

def prepare():
    matrix,c,order=qualification()
    contract=dict(schema='v108-capacity-native-contract-v1',trial_id='capacity-default',start_mode='rtl',part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        source_contract=c,source_order=order,directives=dict(opt='Default',place='Default',phys_opt=None,phys_opt_stage=None,route='Default'),
        baseline_matrix=dict(path=frozen.rel(frozen.MATRIX),sha256=frozen.sha(frozen.MATRIX)),synthesis_strategy='RuntimeOptimized',
        timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,memory_swap_limit_bytes=8*1024**3,
        activation='Requires root activation plus independent audit. All six frozen matrix outcomes first unless root records a measured exception reason.',
        hardware_contact=False)
    if CONTRACT.exists():assert frozen.load(CONTRACT)==contract,'capacity contract is immutable'
    else:frozen.write(CONTRACT,contract)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6]
    build=frozen.BUILD_ROOT/('v108-capacity-default-rtl-'+stamp);build.mkdir();out=AREA/'capacity-native-prepared'/build.name;out.mkdir(parents=True)
    for alias,source in c['source_origins'].items():
        target=build/'snapshot'/alias;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source['path'],target);assert frozen.sha(target)==c['source_sha256'][alias]
    for name in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(frozen.FLOW/name,build/name)
    mapped=Path('/build')/build.name
    def word(value):
        value=str(value);assert not any(x in value for x in '{}\r\n');return '{'+value+'}'
    lines=['set part xc7a100tcsg324-1','set trial_id {capacity-default}','set start_mode {rtl}','set opt_directive {Default}','set place_directive {Default}','set phys_directive {NONE}','set route_directive {Default}',
        'set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']',
        'set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
    (build/'inputs.tcl').write_text('\n'.join(lines)+'\n');recipes={n:frozen.sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')}
    inp=dict(schema='v108-capacity-native-inputs-v1',trial_id='capacity-default',start_mode='rtl',clean_repeat_of=None,source_order=order,part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        native_contract_path=frozen.rel(CONTRACT),native_contract_sha256=frozen.sha(CONTRACT),source_contract=c,source_sha256=c['source_sha256'],source_origins=c['source_origins'],parent_synthesis_checkpoint=c['synthesis_checkpoint'],
        directives=contract['directives'],recipe_sha256=recipes,closure_files=18,RTL_files=17,timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,synthesis_strategy='RuntimeOptimized',synthesis_executed=True,hardware_or_full_parent_signoff=False)
    frozen.write(build/'inputs.json',inp)
    for name in ('inputs.json','inputs.tcl','run.tcl','report.tcl','component.xdc'):shutil.copyfile(build/name,out/name)
    tooling=[Path(__file__).resolve(),Path(frozen.__file__),Path(native_clean.__file__),RUNNER,frozen.FLOW/'run.tcl',frozen.FLOW/'report.tcl',frozen.FLOW/'component.xdc'];(out/'tooling-snapshot').mkdir()
    for source in tooling:shutil.copyfile(source,out/'tooling-snapshot'/source.name)
    pre=dict(schema='v108-capacity-native-preflight-v1',status='PREPARED_NOT_RUN',actual_native_run=False,prepared_build=str(build),prepared_inputs_sha256=frozen.sha(build/'inputs.json'),native_contract_path=frozen.rel(CONTRACT),native_contract_sha256=frozen.sha(CONTRACT),
        source_contract=c,source_order=order,directives=inp['directives'],source_sha256=c['source_sha256'],source_origins=c['source_origins'],recipe_sha256=recipes,tooling_sha256={frozen.rel(p):frozen.sha(p) for p in tooling},parser_self_test=parser_self_test(),
        limits={k:contract[k] for k in ('timeout_seconds','max_threads','cpus','memory_limit_bytes','memory_swap_limit_bytes')},trial_id='capacity-default',start_mode='rtl',clock_period_ns=10.0,part=matrix['part'],hardware_contact=False)
    p=out/'preflight.json';frozen.write(p,pre);print('V108_CAPACITY_NATIVE_PREPARED',frozen.rel(p),frozen.sha(p),flush=True)

def launch(preflight,activation,audit,license_file):
    matrix,c,order=qualification();pre=frozen.load(preflight);contract=frozen.load(CONTRACT)
    assert pre['status']=='PREPARED_NOT_RUN' and pre['native_contract_sha256']==frozen.sha(CONTRACT)
    assert contract['source_contract']==pre['source_contract']==c and pre['source_order']==order
    expected_directives=dict(opt='Default',place='Default',phys_opt=None,phys_opt_stage=None,route='Default')
    assert contract['directives']==pre['directives']==expected_directives
    for n,h in pre['tooling_sha256'].items():assert frozen.sha(ROOT/n)==h,n
    build=Path(pre['prepared_build']);build.relative_to(frozen.BUILD_ROOT);assert frozen.sha(build/'inputs.json')==pre['prepared_inputs_sha256'];inp=frozen.load(build/'inputs.json')
    assert inp['source_sha256']==c['source_sha256'] and inp['source_origins']==c['source_origins'] and inp['source_order']==order
    assert inp['directives']==expected_directives and inp['start_mode']=='rtl' and inp['clean_repeat_of'] is None
    for n,h in inp['source_sha256'].items():assert frozen.sha(build/'snapshot'/n)==h
    for n,h in inp['recipe_sha256'].items():assert frozen.sha(build/n)==h
    a=frozen.load(activation);gate=frozen.load(audit);policy=frozen.load(frozen.POLICY)
    assert policy['max_heavy_jobs']==2 and policy['clock_period_ns']==10
    assert a['enabled'] is True and a['heavy_slot_granted'] is True and a['trial_id']=='capacity-default'
    for key,value in dict(preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),native_contract_sha256=frozen.sha(CONTRACT)).items():assert a[key]==value
    terminal={}
    for p in (AREA/'native').glob('*/receipt.json'):
        r=frozen.load(p)
        if r['start_mode']=='checkpoint' and r['status']!='RUNNING':terminal[r['trial_id']]=dict(path=frozen.rel(p),sha256=frozen.sha(p))
    if set(terminal)!={'m'+str(i) for i in range(6)}:
        assert a.get('allow_before_matrix_complete') is True and len(a.get('measured_exception_reason','').strip())>=20
    assert gate['status']=='PASS_V108_CAPACITY_NATIVE_PREFLIGHT_AUDIT'
    for key,value in dict(preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),activation=frozen.rel(activation),activation_sha256=frozen.sha(activation),policy_sha256=frozen.sha(frozen.POLICY)).items():assert gate[key]==value
    assert not list((AREA/'capacity-native').glob('*/receipt.json')),'One capacity native trial only; no silent retry'
    record=dict(schema='v108-capacity-native-immutable-dispatch-v1',status='DISPATCHED_TO_RUNNER',trial_id='capacity-default',start_mode='rtl',prepared_inputs_sha256=frozen.sha(build/'inputs.json'),prepared_build=str(build),
        preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),activation=frozen.rel(activation),activation_sha256=frozen.sha(activation),policy=frozen.rel(frozen.POLICY),policy_sha256=frozen.sha(frozen.POLICY),independent_audit=frozen.rel(audit),independent_audit_sha256=frozen.sha(audit),native_contract_sha256=frozen.sha(CONTRACT),matrix_terminal_receipts=terminal)
    path=AREA/'coordination'/('capacity-native-dispatch-'+build.name+'.json')
    with path.open('x') as f:f.write(json.dumps(record,indent=2,sort_keys=True)+'\n')
    proc=subprocess.run([sys.executable,str(RUNNER),'--build',str(build),'--license-file',str(license_file),'--dispatch',str(path)],cwd=ROOT)
    frozen.write(AREA/'coordination'/('capacity-native-completion-'+build.name+'.json'),dict(schema='v108-capacity-native-completion-v1',dispatch=frozen.rel(path),dispatch_sha256=frozen.sha(path),runner_exit_code=proc.returncode));proc.check_returncode()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--activation',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
    if a.run:
        assert a.preflight and a.activation and a.audit;launch(a.preflight.resolve(),a.activation.resolve(),a.audit.resolve(),a.license_file)
    else:
        assert not(a.preflight or a.activation or a.audit);prepare()

if __name__=='__main__':main()
