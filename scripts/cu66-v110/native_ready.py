#!/usr/bin/env python3
"""Prepare bounded V110 native runs from actual qualified RTL; no hidden retry."""
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
AREA=ROOT/'experiments/python-gamebub-v110'
FLOW=ROOT/'fpga/experiments/cu66-v110-ready-flow'
BASE=ROOT/'experiments/python-gamebub-v109/native/20261108T121030620057Z'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
POLICY=AREA/'study-policy.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.relative_to(ROOT))
def tcl(s):
    s=str(s);assert not any(x in s for x in '{}\r\n');return '{'+s+'}'

def qualification(variant):
    baseline=load(BASE/'receipt.json');card=load(BASE/'inputs.json')
    assert baseline['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
    assert baseline['clock_loaded_before_synthesis_in_this_run'] and baseline['clock_period_ns']==10.0
    assert sha(BASE/'inputs.json')==baseline['source_manifest_sha256']
    canonical=AREA/'canonical-ready-rice'/variant/'results.json';q=load(canonical)
    assert q['status']=='PASS_EXACT_V110_CANONICAL' and q['actual_RTL_run']
    paths=q['rtl_source_order'];aliases=card['source_order']['rtl_read_order_aliases']+[n for n in card['source_origins'] if n.endswith('.svh')]
    assert len(paths)==len(aliases)==18 and sum(n.endswith('.sv') for n in paths)==17
    origins={alias:dict(path=n,sha256=sha(ROOT/n)) for alias,n in zip(aliases,paths)}
    assert all(q['source_sha256'][meta['path']]==meta['sha256'] for meta in origins.values())
    proofs=[]
    if variant in ('busy','combined'):proofs.append(AREA/'busy/results.json')
    if variant in ('fault','combined'):proofs.append(AREA/'fault/results.json')
    assert variant=='combined'
    proofs.append(AREA/'dequant/results.json')
    proofs.append(AREA/'ready/results.json')
    proofs.append(AREA/'rice/results.json')
    for p in proofs:
        proof=load(p);assert proof['status']=='PASS' and proof['actual_RTL_run']
        assert q['source_sha256'][rel(p)]==sha(p)
    return baseline,card,dict(source_origins=origins,source_sha256={a:x['sha256'] for a,x in origins.items()},
        parent_receipt=rel(BASE/'receipt.json'),parent_receipt_sha256=sha(BASE/'receipt.json'),parent_clock_loaded_before_synthesis=True,
        canonical_qualification=rel(canonical),canonical_sha256=sha(canonical),focused_proofs={rel(p):sha(p) for p in proofs},
        qualification_scope='Exact public cycles/events/canonical RTL; full parent and hardware remain unqualified.')

def prepare(a):
    baseline,card,c=qualification(a.variant);policy=load(POLICY)
    mode='checkpoint' if a.checkpoint_from else 'rtl'
    parent=baseline['artifacts']['synth.dcp']
    ancestry=None
    if a.checkpoint_from:
        r=load(a.checkpoint_from);assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and r['source_sha256']==c['source_sha256']
        assert r['synthesis_executed'] and r['clock_loaded_before_synthesis_in_this_run']
        parent=r['artifacts']['synth.dcp'];ancestry=dict(path=rel(a.checkpoint_from),sha256=sha(a.checkpoint_from))
    assert sha(Path(parent['external_path']))==parent['sha256']
    if a.repeat_of:
        r=load(a.repeat_of);assert r['result']['component_internal_100MHz_pass'] and r['source_sha256']==c['source_sha256']
        assert mode=='rtl';ancestry=dict(path=rel(a.repeat_of),sha256=sha(a.repeat_of))
    profile_label='combined-dequant'  # Same codec/control/DSP family; READY is the measured adaptive tag.
    assert profile_label in policy['initial_variants']
    tag=a.tag or ('ready-rice-repeat' if a.repeat_of else 'ready-rice')
    assert a.repeat_of or a.hypothesis, 'READY/RICE is only a measured adaptive source hypothesis'
    assert tag.replace('-','').isalnum()
    trial='v110-'+a.variant+'-'+tag
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6]
    build=BUILD/(trial+'-'+stamp);build.mkdir();out=AREA/'prepared'/build.name;out.mkdir(parents=True)
    for alias,meta in c['source_origins'].items():
        p=build/'snapshot'/alias;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/meta['path'],p)
    for name in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/name,build/name)
    directives=r['directives'] if a.repeat_of else dict(opt='Default',place='ExtraNetDelay_high',phys_opt=a.phys_opt,phys_opt_stage='pre_route' if a.phys_opt else None,route='Default')
    mapped=Path('/build')/build.name;order=card['source_order']
    lines=['set part xc7a100tcsg324-1','set trial_id '+tcl(trial),'set start_mode '+tcl(mode),
        'set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive '+tcl(directives['phys_opt'] or 'NONE'),'set route_directive {Default}',
        'set rtl_sources [list '+' '.join(tcl(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']',
        'set include_dirs [list '+' '.join(tcl(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+tcl(mapped/'component.xdc')]
    (build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
    contract=dict(schema='v110-native-contract-v1',profile_label=profile_label,source_contract=c,source_order=order,directives=directives,
                  clock_period_ns=10.0,part=policy['part'],policy_sha256=sha(POLICY),hypothesis=a.hypothesis)
    write(out/'contract.json',contract)
    inp=dict(schema='v110-native-inputs-v1',trial_id=trial,profile_label=profile_label,variant=a.variant,start_mode=mode,clean_repeat_of=ancestry if a.repeat_of else None,checkpoint_from=ancestry if a.checkpoint_from else None,
        hypothesis=a.hypothesis,source_order=order,source_contract=c,source_sha256=c['source_sha256'],source_origins=c['source_origins'],
        part=policy['part'],top='cs88_pipeline_v91k',clock_period_ns=10.0,closure_files=18,RTL_files=17,parent_synthesis_checkpoint=parent,
        directives=directives,recipe_sha256={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},timeout_seconds=2400,
        native_contract_path=rel(out/'contract.json'),native_contract_sha256=sha(out/'contract.json'),policy_sha256=sha(POLICY),
        tooling_sha256={rel(p):sha(p) for p in (Path(__file__).resolve(),FLOW/'run_native.py')})
    write(build/'inputs.json',inp)
    for name in ('run.tcl','report.tcl','component.xdc','inputs.tcl','inputs.json'):shutil.copyfile(build/name,out/name)
    spec=importlib.util.spec_from_file_location('v110_runner',FLOW/'run_native.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.parse_reports(BASE/'reports')==baseline['result']
    pre=dict(status='PREPARED_NOT_RUN',schema='v110-native-preflight-v1',trial_id=trial,profile_label=profile_label,build_external=str(build),inputs_sha256=sha(build/'inputs.json'),
             policy_sha256=sha(POLICY),source_contract=c,source_order=order,recipe_sha256=inp['recipe_sha256'],tooling_sha256=inp['tooling_sha256'],
             parser_test='PASS_ACTUAL_V109_FETCH_REPORTS',start_mode=mode,hypothesis=a.hypothesis)
    write(out/'preflight.json',pre);print('V110_PREPARED',rel(out/'preflight.json'),sha(out/'preflight.json'))

def launch(a):
    pf=a.preflight.resolve();p=load(pf);build=Path(p['build_external']);inp=load(build/'inputs.json');policy=load(POLICY)
    assert p['status']=='PREPARED_NOT_RUN' and sha(build/'inputs.json')==p['inputs_sha256']
    assert p['policy_sha256']==sha(POLICY)==inp['policy_sha256']
    assert sha(ROOT/inp['native_contract_path'])==inp['native_contract_sha256']
    _,_,contract=qualification(inp['variant']);assert contract==inp['source_contract']==p['source_contract']
    for path,digest in p['tooling_sha256'].items():assert sha(ROOT/path)==digest
    for n,h in inp['source_sha256'].items():assert sha(build/'snapshot'/n)==h
    for n,h in p['recipe_sha256'].items():assert sha(build/n)==h
    gate=load(a.audit);assert gate['status']=='PASS_V110_NATIVE_PREFLIGHT_AUDIT' and gate['preflight_sha256']==sha(pf) and gate['policy_sha256']==sha(POLICY)
    active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith('gamebub-v110') for n in active)<policy['max_heavy_jobs']
    previous=list((AREA/'native').glob('*/receipt.json'))
    assert all(load(p)['trial_id']!=inp['trial_id'] for p in previous),'No silent trial retry'
    if inp['clean_repeat_of']:assert sum(bool(load(p).get('clean_repeat_of')) for p in previous)<policy['validation_repeat_if_nonnegative']
    elif inp['hypothesis']:
        assert sum(bool(load(p).get('predispatch',{}).get('record',{}).get('hypothesis')) for p in previous)<policy['adaptive_native_trials_after_measured_hypothesis']
        assert any(load(p)['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' for p in previous),'Measured native result required before adaptation'
    else:
        assert inp['profile_label'] in policy['initial_variants']
        initial=[load(p) for p in previous if not load(p).get('clean_repeat_of') and not load(p).get('predispatch',{}).get('record',{}).get('hypothesis')]
        assert len(initial)<policy['initial_native_trials']
        assert all(r['predispatch']['record']['profile_label']!=inp['profile_label'] for r in initial),'Initial profile already executed; a measured adaptive hypothesis is required'

    dispatch=AREA/'coordination'/('dispatch-'+build.name+'.json');dispatch.parent.mkdir(exist_ok=True)
    d=dict(status='DISPATCHED_TO_RUNNER',prepared_inputs_sha256=sha(build/'inputs.json'),trial_id=inp['trial_id'],profile_label=inp['profile_label'],preflight=rel(pf),preflight_sha256=sha(pf),
           audit=rel(a.audit.resolve()),audit_sha256=sha(a.audit),policy_sha256=sha(POLICY),hypothesis=inp['hypothesis'])
    with dispatch.open('x') as f:f.write(json.dumps(d,indent=2,sort_keys=True)+'\n')
    proc=subprocess.run([sys.executable,str(FLOW/'run_native.py'),'--build',str(build),'--dispatch',str(dispatch),'--license-file',str(a.license_file)],cwd=ROOT)
    write(AREA/'coordination'/('completion-'+build.name+'.json'),dict(dispatch=rel(dispatch),dispatch_sha256=sha(dispatch),exit_code=proc.returncode));proc.check_returncode()

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--variant',choices=('busy','fault','combined'));ap.add_argument('--tag');ap.add_argument('--hypothesis');ap.add_argument('--phys-opt',choices=('AggressiveFanoutOpt',));ap.add_argument('--checkpoint-from',type=Path);ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
    if a.run:
        assert a.preflight and a.audit;launch(a)
    else:
        assert a.variant and not a.preflight and not a.audit
        assert not(a.checkpoint_from and a.repeat_of)
        if a.phys_opt or a.checkpoint_from:assert a.hypothesis
        prepare(a)

if __name__=='__main__':main()
