#!/usr/bin/env python3
"""Prepare a separately qualified fresh-RTL outtile/capacity trial; activation is explicit."""
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
CONTRACT=AREA/'outtile-native-contract.json'
FALLBACK_POLICY=AREA/'output-control-fallback-policy.json'
CAPCANONICAL=AREA/'capacity-pipeline/results.json'
OUTFOCUS=AREA/'outtile/results.json'
KILLS=AREA/'outtile-kill-collisions/results.json'
FOCUS=AREA/'capacity/results.json'
CANONICAL=AREA/'outtile-pipeline/results.json'
RUNNER=frozen.FLOW/'run_native_composite.py'
REPLACEMENTS=('packed_scratch_v91g2.sv','br88_packet_ingress_sync_v91h.sv','br88_packet_ingress_v91h.sv','br88_pipeline_v91h.sv')

def parser_self_test():
    parent=frozen.parser_self_test()
    spec=importlib.util.spec_from_file_location('v108_capacity_runner',RUNNER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=ROOT/'experiments/python-gamebub-v107/native/20261108T081254078678Z/reports'
    assert module.parse_reports(report)==parent['observed']
    return dict(status='PASS_COMPOSITE_RUNNER_NATIVE_REPORT_PARSER',runner_sha256=frozen.sha(RUNNER),baseline_parser_test=parent,
        scope='Read-only actual V107 report parser check; no new RTL, native or hardware run.')

def selected_strategy(matrix,trial_id):
    receipts={}
    for path in (AREA/'native').glob('*/receipt.json'):
        r=frozen.load(path)
        if r['start_mode']!='checkpoint':continue
        assert r['trial_id'] not in receipts,'Duplicate matrix row'
        assert r['status']!='RUNNING','All six matrix rows must be terminal'
        assert r['native_matrix_sha256']==frozen.sha(frozen.MATRIX)
        assert r['source_sha256']==matrix['source_contract']['source_sha256']
        dispatch=r['predispatch'];dispatch_path=ROOT/dispatch['path'];assert frozen.sha(dispatch_path)==dispatch['sha256']
        completion=AREA/'coordination'/('native-completion-'+Path(r['build_external']).name+'.json');finished=frozen.load(completion)
        assert finished['dispatch']==dispatch['path'] and finished['dispatch_sha256']==dispatch['sha256'] and isinstance(finished['runner_exit_code'],int)
        receipts[r['trial_id']]=(path,r)
    assert set(receipts)=={'m'+str(i) for i in range(6)},'All six matrix rows required'
    eligible={}
    for key,(path,r) in receipts.items():
        if r['status']!='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' or 'result' not in r:continue
        result=r['result']
        if not(result['clock_10ns'] and result['routing']['all_routable_nets_routed'] and result['routing']['zero_routing_errors']):continue
        checks=result['check_timing'];timing=result['timing']
        if not all(checks[key]==0 for key in ('no_clock','unconstrained_internal_endpoints','loops','latch_loops','multiple_clock')):continue
        if min(timing['WHS_ns'],timing['WPWS_ns'])<0 or timing['hold_failing'] or timing['pulse_failing']:continue
        if not(r['source_snapshot_unchanged'] and r['recipe_unchanged'] and r['parent_checkpoint_unchanged']):continue
        eligible[key]=(path,r)
    assert eligible
    winner=max(eligible,key=lambda key:(eligible[key][1]['result']['timing']['WNS_ns'],eligible[key][1]['result']['timing']['TNS_ns'],-eligible[key][1]['result']['timing']['setup_failing'],-int(key[1:])))
    assert trial_id==winner,('Actual best eligible completed matrix strategy required',winner)
    path,r=eligible[winner];entry=next(x for x in matrix['trials'] if x['id']==winner)
    directives={k:entry[k] for k in ('opt','place','phys_opt','phys_opt_stage','route')};assert r['directives']==directives
    return dict(trial_id=winner,selected_receipt=dict(path=frozen.rel(path),sha256=frozen.sha(path)),directives=directives,
        measured_matrix_timing=r['result']['timing'],selected_matrix_component_100MHz_pass=r['result']['component_internal_100MHz_pass'],
        selected_setup_status='FAILED_FRONTIER_ONLY' if r['result']['timing']['WNS_ns']<0 or r['result']['timing']['setup_failing'] else 'PASS_SETUP',
        all_six_terminal_receipts={key:dict(path=frozen.rel(p),sha256=frozen.sha(p)) for key,(p,_) in receipts.items()},
        scope='Strategy transferred to a different qualified source variant; does not replace frozen-source clean repeat.')

def qualification(trial_id):
    assert frozen.sha(Path(frozen.__file__))==native_clean.BUILDER_SHA
    matrix=frozen.qualification();strategy=selected_strategy(matrix,trial_id)
    policy=frozen.load(FALLBACK_POLICY)
    assert policy['schema']=='v108-measured-output-control-fallback-policy-v2' and policy['max_composite_native_trials']==1
    assert set(policy['required_proofs'])=={'capacity/results.json','capacity-pipeline/results.json','outtile/results.json','outtile-kill-collisions/results.json','outtile-pipeline/results.json'}
    assert policy['clock_period_ns']==10 and policy['part']==matrix['part'] and policy['max_global_heavy_jobs']==2
    assert policy['native_timeout_seconds']==2400 and policy['threads']==policy['cpus']==2
    assert policy['memory_limit_bytes']==policy['memory_swap_limit_bytes']==8*1024**3
    assert policy['initial_policy_sha256']==frozen.sha(frozen.POLICY)
    assert policy['clock_relaxations'] is False and policy['exceptions_added'] is False and policy['hardware_contact'] is False
    focus=frozen.load(FOCUS);capcan=frozen.load(CAPCANONICAL);outfocus=frozen.load(OUTFOCUS);canonical=frozen.load(CANONICAL);kills=frozen.load(KILLS)
    for proof,status in ((focus,'PASS'),(capcan,'PASS_EXACT_CAPACITY_CANONICAL'),(outfocus,'PASS'),(canonical,'PASS_EXACT_OUTTILE_CAPACITY_CANONICAL')):
        assert proof['status']==status and proof['actual_RTL_run'] is True
    assert kills['schema']=='v108-outtile-kill-collisions-focused-proof-v1' and kills['status']=='PASS' and kills['actual_RTL_run'] is True
    assert kills['runs']
    for run in kills['runs']:
        verdict=run['verdict'];replay=run['trace_replay'];assert verdict['status']=='TEST_PASS' and replay['status']=='PASS'
        expected=dict(write_boundary_collision_cases=12,write_boundary_group_mask=15,write_boundary_guard_mask=7,write_boundary_matrix_mask=4095,write_boundary_good_retries=12,kill_payload_write_collisions=15)
        assert all(verdict[key]==value for key,value in expected.items())
        assert replay['write_boundary_matrix_mask']==4095 and replay['write_boundary_collisions']==12
    c=json.loads(json.dumps(matrix['source_contract']));replaced=[]
    for alias,old in c['source_origins'].items():
        if Path(old['path']).parent.name=='cu66-v107-count-threshold':
            name=Path(old['path']).name;assert name in REPLACEMENTS
            path=ROOT/'fpga/experiments/cu66-v108-capacity'/name;digest=frozen.sha(path)
            assert focus['source_sha256'][frozen.rel(path)]==capcan['source_sha256'][frozen.rel(path)]==digest
        elif old['path']=='fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv':
            name=Path(old['path']).name;path=ROOT/'fpga/experiments/cu66-v108-outtile'/name;digest=frozen.sha(path)
            assert outfocus['source_sha256'][frozen.rel(path)]==digest
            assert kills['candidate']['path']==frozen.rel(path) and kills['candidate']['sha256']==digest
        else:continue
        c['source_origins'][alias]=dict(path=frozen.rel(path),sha256=digest);c['source_sha256'][alias]=digest;replaced.append(name)
    assert set(replaced)==set(REPLACEMENTS)|{'cu66_idct8x8.sv'} and len(replaced)==5
    actual={e['path']:e['sha256'] for e in c['source_origins'].values()}
    expected={n:h for n,h in canonical['source_sha256'].items() if Path(n).suffix in ('.sv','.svh')}
    assert actual==expected and len(actual)==18,'exact full composite canonical RTL/header closure required'
    for path,digest in actual.items():assert frozen.sha(ROOT/path)==digest
    c['baseline_canonical_qualification']=dict(path=c['canonical_qualification'],sha256=c['canonical_sha256'])
    c['canonical_qualification']=frozen.rel(CANONICAL);c['canonical_sha256']=frozen.sha(CANONICAL)
    for name,path in [('capacity_focused_qualification',FOCUS),('capacity_canonical_qualification',CAPCANONICAL),('outtile_focused_qualification',OUTFOCUS),('outtile_write_kill_qualification',KILLS),('outtile_capacity_canonical_qualification',CANONICAL)]:c[name]=dict(path=frozen.rel(path),sha256=frozen.sha(path))
    c['source_revision']='V108 outtile/capacity composite; five new origins supersede baseline selection/input-card ancestry'
    c['baseline_checkpoint_role']='read-only provenance ancestry only; fresh RTL run does not open checkpoint'
    c['output_control_fallback_policy']=dict(path=frozen.rel(FALLBACK_POLICY),sha256=frozen.sha(FALLBACK_POLICY))
    c['matrix_strategy_selection']=strategy
    return matrix,c,native_clean.parent_order(matrix),strategy

def prepare(trial_id):
    matrix,c,order,strategy=qualification(trial_id)
    contract=dict(schema='v108-outtile-capacity-native-contract-v1',trial_id='outtile-capacity-'+trial_id,start_mode='rtl',part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        source_contract=c,source_order=order,directives=strategy['directives'],
        baseline_matrix=dict(path=frozen.rel(frozen.MATRIX),sha256=frozen.sha(frozen.MATRIX)),synthesis_strategy='RuntimeOptimized',
        timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,memory_swap_limit_bytes=8*1024**3,
        activation='Requires separate root activation and independent audit; all six matrix rows terminal, selected measured best eligible strategy.',
        hardware_contact=False)
    if CONTRACT.exists():assert frozen.load(CONTRACT)==contract,'capacity contract is immutable'
    else:frozen.write(CONTRACT,contract)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6]
    build=frozen.BUILD_ROOT/('v108-outtile-capacity-'+trial_id+'-rtl-'+stamp);build.mkdir();out=AREA/'outtile-native-prepared'/build.name;out.mkdir(parents=True)
    for alias,source in c['source_origins'].items():
        target=build/'snapshot'/alias;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source['path'],target);assert frozen.sha(target)==c['source_sha256'][alias]
    for name in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(frozen.FLOW/name,build/name)
    mapped=Path('/build')/build.name
    def word(value):
        value=str(value);assert not any(x in value for x in '{}\r\n');return '{'+value+'}'
    lines=['set part xc7a100tcsg324-1','set trial_id '+word('outtile-capacity-'+trial_id),'set start_mode {rtl}','set opt_directive '+word(strategy['directives']['opt']),'set place_directive '+word(strategy['directives']['place']),'set phys_directive '+word(strategy['directives']['phys_opt'] or 'NONE'),'set route_directive '+word(strategy['directives']['route']),
        'set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']',
        'set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
    (build/'inputs.tcl').write_text('\n'.join(lines)+'\n');recipes={n:frozen.sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')}
    inp=dict(schema='v108-outtile-capacity-native-inputs-v1',trial_id='outtile-capacity-'+trial_id,start_mode='rtl',clean_repeat_of=None,source_order=order,strategy_trial=trial_id,part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        native_contract_path=frozen.rel(CONTRACT),native_contract_sha256=frozen.sha(CONTRACT),source_contract=c,source_sha256=c['source_sha256'],source_origins=c['source_origins'],parent_synthesis_checkpoint=c['synthesis_checkpoint'],
        directives=contract['directives'],recipe_sha256=recipes,closure_files=18,RTL_files=17,timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,synthesis_strategy='RuntimeOptimized',synthesis_executed=True,hardware_or_full_parent_signoff=False)
    frozen.write(build/'inputs.json',inp)
    for name in ('inputs.json','inputs.tcl','run.tcl','report.tcl','component.xdc'):shutil.copyfile(build/name,out/name)
    tooling=[Path(__file__).resolve(),Path(frozen.__file__),Path(native_clean.__file__),RUNNER,frozen.FLOW/'run.tcl',frozen.FLOW/'report.tcl',frozen.FLOW/'component.xdc'];(out/'tooling-snapshot').mkdir()
    for source in tooling:shutil.copyfile(source,out/'tooling-snapshot'/source.name)
    pre=dict(schema='v108-outtile-capacity-native-preflight-v1',status='PREPARED_NOT_RUN',actual_native_run=False,prepared_build=str(build),prepared_inputs_sha256=frozen.sha(build/'inputs.json'),native_contract_path=frozen.rel(CONTRACT),native_contract_sha256=frozen.sha(CONTRACT),
        source_contract=c,source_order=order,strategy_trial=trial_id,directives=inp['directives'],source_sha256=c['source_sha256'],source_origins=c['source_origins'],recipe_sha256=recipes,tooling_sha256={frozen.rel(p):frozen.sha(p) for p in tooling},parser_self_test=parser_self_test(),
        limits={k:contract[k] for k in ('timeout_seconds','max_threads','cpus','memory_limit_bytes','memory_swap_limit_bytes')},trial_id='outtile-capacity-'+trial_id,start_mode='rtl',clock_period_ns=10.0,part=matrix['part'],hardware_contact=False)
    p=out/'preflight.json';frozen.write(p,pre);print('V108_OUTTILE_CAPACITY_NATIVE_PREPARED',frozen.rel(p),frozen.sha(p),flush=True)

def launch(preflight,activation,audit,license_file):
    pre=frozen.load(preflight);matrix,c,order,strategy=qualification(pre['strategy_trial']);contract=frozen.load(CONTRACT)
    assert pre['status']=='PREPARED_NOT_RUN' and pre['native_contract_sha256']==frozen.sha(CONTRACT)
    assert contract['source_contract']==pre['source_contract']==c and pre['source_order']==order
    expected_directives=strategy['directives']
    assert contract['directives']==pre['directives']==expected_directives
    for n,h in pre['tooling_sha256'].items():assert frozen.sha(ROOT/n)==h,n
    build=Path(pre['prepared_build']);build.relative_to(frozen.BUILD_ROOT);assert frozen.sha(build/'inputs.json')==pre['prepared_inputs_sha256'];inp=frozen.load(build/'inputs.json')
    assert inp['source_sha256']==c['source_sha256'] and inp['source_origins']==c['source_origins'] and inp['source_order']==order
    assert inp['directives']==expected_directives and inp['start_mode']=='rtl' and inp['clean_repeat_of'] is None
    for n,h in inp['source_sha256'].items():assert frozen.sha(build/'snapshot'/n)==h
    for n,h in inp['recipe_sha256'].items():assert frozen.sha(build/n)==h
    a=frozen.load(activation);gate=frozen.load(audit);policy=frozen.load(frozen.POLICY)
    assert policy['max_heavy_jobs']==2 and policy['clock_period_ns']==10
    assert a['enabled'] is True and a['heavy_slot_granted'] is True and a['trial_id']==pre['trial_id']
    assert a['fallback_policy_sha256']==frozen.sha(FALLBACK_POLICY)
    for key,value in dict(preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),native_contract_sha256=frozen.sha(CONTRACT)).items():assert a[key]==value
    terminal={}
    for p in (AREA/'native').glob('*/receipt.json'):
        r=frozen.load(p)
        if r['start_mode']=='checkpoint' and r['status']!='RUNNING':terminal[r['trial_id']]=dict(path=frozen.rel(p),sha256=frozen.sha(p))
    assert set(terminal)=={'m'+str(i) for i in range(6)}
    assert gate['status']=='PASS_V108_OUTTILE_CAPACITY_NATIVE_PREFLIGHT_AUDIT'
    assert gate['fallback_policy_sha256']==frozen.sha(FALLBACK_POLICY)
    for key,value in dict(preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),activation=frozen.rel(activation),activation_sha256=frozen.sha(activation),policy_sha256=frozen.sha(frozen.POLICY)).items():assert gate[key]==value
    assert not list((AREA/'outtile-native').glob('*/receipt.json')),'One composite native trial only; no silent retry'
    record=dict(schema='v108-outtile-capacity-native-immutable-dispatch-v1',status='DISPATCHED_TO_RUNNER',trial_id=pre['trial_id'],start_mode='rtl',prepared_inputs_sha256=frozen.sha(build/'inputs.json'),prepared_build=str(build),
        preflight=frozen.rel(preflight),preflight_sha256=frozen.sha(preflight),activation=frozen.rel(activation),activation_sha256=frozen.sha(activation),policy=frozen.rel(frozen.POLICY),policy_sha256=frozen.sha(frozen.POLICY),fallback_policy=frozen.rel(FALLBACK_POLICY),fallback_policy_sha256=frozen.sha(FALLBACK_POLICY),independent_audit=frozen.rel(audit),independent_audit_sha256=frozen.sha(audit),native_contract_sha256=frozen.sha(CONTRACT),matrix_terminal_receipts=terminal)
    path=AREA/'coordination'/('outtile-native-dispatch-'+build.name+'.json')
    with path.open('x') as f:f.write(json.dumps(record,indent=2,sort_keys=True)+'\n')
    proc=subprocess.run([sys.executable,str(RUNNER),'--build',str(build),'--license-file',str(license_file),'--dispatch',str(path)],cwd=ROOT)
    frozen.write(AREA/'coordination'/('outtile-native-completion-'+build.name+'.json'),dict(schema='v108-outtile-capacity-native-completion-v1',dispatch=frozen.rel(path),dispatch_sha256=frozen.sha(path),runner_exit_code=proc.returncode));proc.check_returncode()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--trial',choices=['m'+str(i) for i in range(6)]);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--activation',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
    if a.run:
        assert a.preflight and a.activation and a.audit;launch(a.preflight.resolve(),a.activation.resolve(),a.audit.resolve(),a.license_file)
    else:
        assert a.trial and not(a.preflight or a.activation or a.audit);prepare(a.trial)

if __name__=='__main__':main()
