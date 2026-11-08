#!/usr/bin/env python3
"""Prepare one guarded cursor source trial, or its one global positive fresh repeat.

Code-only until root grants preparation: no implicit launch, retry or checkpoint mode.
"""
import argparse,datetime,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v110';FLOW=ROOT/'fpga/experiments/cu66-v110-cursors-flow';POLICY=AREA/'cursors-policy.json';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
DIRECTIVES=dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default')
OBSERVABILITY=dict(public_cycles='exact, including invalid values/counters/debug/memory',live_cursors='exact whenever either reference or candidate owner is live',retired_private_cursor_payload='intentionally may differ; restored before new ownership',all_private_state_exact=False,public_latency_delta_cycles=0,original_proofs_unchanged=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.resolve().relative_to(ROOT))
def word(s):
 s=str(s);assert not any(c in s for c in '{}\r\n');return '{'+s+'}'
def module(p):
 spec=importlib.util.spec_from_file_location('cursors_bound_helper',p);m=importlib.util.module_from_spec(spec);sys.dont_write_bytecode=True;spec.loader.exec_module(m);return m

def validate_default_gate(r,runtime,policy_sha256):
 """Default is a terminal eligibility gate only, never the source/method baseline."""
 assert r['runtime_control']['path']==runtime['path'] and r['runtime_control']['sha256']==runtime['sha256']
 assert r['policy_sha256']==policy_sha256 and r['synth_directive']=='default' and r['synth_directive_cli']=='omitted'
 assert r['start_mode']=='rtl' and r['synthesis_executed'] and not r['clean_repeat_of']
 if r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
  assert r['result']['component_internal_100MHz_pass'] is False and r['result']['timing']['WNS_ns']<0,'Default achieved timing: skip cursor trial and repeat Default'
 else:
  assert r['status'] in ('TOOL_OR_BUILD_FAILED','STOPPED_RESOURCE_OR_TIME_GATE','ROUTE_FINISHED_REPORT_PARSE_FAILED'),'Default attempt is not terminal'
  assert not r.get('result',{}).get('component_internal_100MHz_pass',False)
 assert 'observed_exit_code' in r and r['log_sha256'],'Require actual terminal attempt evidence'

def eligibility(policy):
 for key in ('original','default'):
  assert sha(ROOT/policy[key+'_policy_path'])==policy[key+'_policy_sha256']
 for n,h in policy['frozen_parent_flow_sha256'].items():assert sha(ROOT/'fpga/experiments/cu66-v110-ready-flow'/n)==h
 runtime=policy['runtime_control'];rp=ROOT/runtime['path'];assert sha(rp)==runtime['sha256'];r=load(rp)
 assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and not r['result']['component_internal_100MHz_pass'] and r['result']['timing']['WNS_ns']==-1.654
 assert r['start_mode']=='rtl' and r['synthesis_executed'] and r['clock_loaded_before_synthesis_in_this_run'] and r['clock_period_ns']==10.0 and not r['clean_repeat_of']
 assert r['cpus']==r['max_threads']==2 and r['memory_limit_bytes']==r['memory_swap_limit_bytes']==8*1024**3 and r['timeout_seconds']==2400
 assert r['directives']==DIRECTIVES and '-directive RuntimeOptimized' in(rp.parent/'recipe-snapshot/run.tcl').read_text()
 assert r['recipe_sha256']=={n:sha(rp.parent/'recipe-snapshot'/n) for n in r['recipe_sha256']}
 helper=policy['qualification_helper'];assert sha(ROOT/helper['path'])==helper['sha256']
 base,card,parent=module(ROOT/helper['path']).qualification('combined')
 assert parent==r['source_contract'] and parent['source_sha256']==r['source_sha256'] and parent['source_origins']==r['source_origins']
 validate_canonical(ROOT/parent['canonical_qualification'])
 for n,h in parent['focused_proofs'].items():assert sha(ROOT/n)==h;validate_focused(ROOT/n)
 original_flow=ROOT/'fpga/experiments/cu66-v110-ready-flow'
 for n in ('report.tcl','component.xdc'):assert sha(FLOW/n)==sha(original_flow/n)
 assert (FLOW/'run.tcl').read_text()==(original_flow/'run.tcl').read_text().replace('start_mode $start_mode trial_id $trial_id','start_mode $start_mode synth_directive RuntimeOptimized synth_directive_cli explicit trial_id $trial_id')
 dp=ROOT/policy['default_gate_path'];d=load(dp);validate_default_gate(d,runtime,policy['default_policy_sha256'])
 assert sha(dp.parent/'vivado.log')==d['log_sha256']
 return base,card,parent,dict(runtime_control=dict(runtime),default_gate=dict(path=rel(dp),sha256=sha(dp),status=d['status'],role='terminal eligibility only; not source/method baseline'),qualification_helper=dict(helper,variant='combined'))

def validate_focused(path):
 f=load(path);assert f['status']=='PASS' and f['actual_RTL_run'] and f['assertions_disabled_or_downgraded'] is False and f['added_public_cycles']==0
 selected=ROOT/f['selected_report'];assert sha(selected)==f['selected_report_sha256']
 for n,h in f['source_sha256'].items():assert sha(ROOT/n)==h
 for n,h in f.get('artifacts_sha256',f.get('artifact_sha256',{})).items():assert sha(selected.parent/n)==h
 return f

def validate_canonical(path):
 q=load(path);assert q['status']=='PASS_EXACT_V110_CANONICAL' and q['actual_RTL_run']
 assert q['variant']=='combined' and q['newly_executed_candidate_case_profiles']==44 and q['newly_executed_candidate_directed_checks']==42 and q['seeds']==[107601,107602]
 receipt=ROOT/q['selected_receipt'];assert load(receipt)=={k:v for k,v in q.items() if k!='selected_receipt'}
 for n,h in q['source_sha256'].items():assert sha(ROOT/n)==h
 for n,h in q['artifact_sha256'].items():assert sha(receipt.parent/n)==h
 baseline=ROOT/q['baseline_reference']['path'];assert sha(baseline)==q['baseline_reference']['sha256'];gold=load(baseline)
 for row in q['runs']:
  ref=next(x for x in gold['runs'] if x['seed']==row['seed'])
  assert row['exact_stdout_events_cycles_and_canonical'] and row['verdict']==ref['verdict']
  for key,m in row['artifacts'].items():
   p=receipt.parent/m['path'];assert sha(p)==m['sha256']
   assert hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest()==m['raw_sha256']==ref['artifacts'][key]['raw_sha256']
 return q

def validate_source_delta(parent,origins,policy):
 assert set(origins)==set(parent['source_origins']) and len(origins)==18
 changed=[a for a in origins if origins[a]!=parent['source_origins'][a]]
 assert changed==[policy['scratch_alias']],'Only scratch source may change from PREFIX control'
 assert origins[changed[0]]['path']==policy['candidate_scratch_path']
 assert origins[changed[0]]['sha256']!=parent['source_sha256'][changed[0]]

def qualification(policy):
 base,card,parent,pins=eligibility(policy);path=AREA/'canonical-cursors/combined/results.json';q=validate_canonical(path)
 aliases=card['source_order']['rtl_read_order_aliases']+[a for a in card['source_origins'] if a.endswith('.svh')]
 paths=q['rtl_source_order'];assert len(paths)==len(aliases)==18 and sum(p.endswith('.sv') for p in paths)==17 and len(set(paths))==18
 origins={a:dict(path=p,sha256=sha(ROOT/p)) for a,p in zip(aliases,paths)};validate_source_delta(parent,origins,policy)
 assert all(q['source_sha256'][m['path']]==m['sha256'] for m in origins.values())
 fp=ROOT/policy['cursor_focus_path'];f=validate_focused(fp)
 assert f['status']=='PASS' and f['actual_RTL_run'] and f['added_public_cycles']==0 and f['assertions_disabled_or_downgraded'] is False
 assert f['strict_warnings'] and not f['warning_suppression'] and len(f['scratch_runs'])==2
 selected=ROOT/f['selected_report'];assert sha(selected)==f['selected_report_sha256'] and load(selected)=={k:v for k,v in f.items() if k not in ('selected_report','selected_report_sha256')}
 for n,h in f['source_sha256'].items():assert sha(ROOT/n)==h
 for n,h in f['artifacts_sha256'].items():assert sha(selected.parent/n)==h
 adapter=ROOT/policy['observability_adapter_path'];assert sha(adapter)==policy['observability_adapter_sha256']==f['source_sha256'][rel(adapter)]
 ad=load(adapter);assert ad['original_assertions_and_oracles_retained'] is True
 original=next(x for x in ad['adapters'] if x['source']==parent['source_origins'][policy['scratch_alias']]['path'])
 assert original['source_sha256']==parent['source_sha256'][policy['scratch_alias']]
 for row in f['scratch_runs']:
  v=row['cursor_retirement'];assert v['status']=='TEST_PASS' and v['cursor_retirement_cases']==v['inactive_divergence_cases']==v['restored_new_owner_cases']==6 and row['inherited']['status']=='TEST_PASS'
 proofs=dict(parent['focused_proofs']);proofs.pop('experiments/python-gamebub-v110/busy/results.json');proofs[rel(fp)]=sha(fp)
 for n,h in proofs.items():assert sha(ROOT/n)==h==q['source_sha256'][n]
 assert f['source_sha256'][policy['candidate_scratch_path']]==origins[policy['scratch_alias']]['sha256']
 c=dict(source_origins=origins,source_sha256={a:m['sha256'] for a,m in origins.items()},parent_receipt=parent['parent_receipt'],parent_receipt_sha256=parent['parent_receipt_sha256'],parent_clock_loaded_before_synthesis=True,canonical_qualification=rel(path),canonical_sha256=sha(path),focused_proofs=proofs,parent_prefix_contract_sha256=hashlib.sha256(json.dumps(parent,sort_keys=True).encode()).hexdigest(),observability_contract=OBSERVABILITY,qualification_scope='Exact public/canonical cycles and live cursor payload; retired private cursors intentionally may differ. No hardware or complete-parent qualification.')
 return base,card,c,pins

def receipts(policy):return [(p,load(p)) for n in policy['global_receipt_roots'] for p in (ROOT/n).glob('*/receipt.json')]
def budget(policy,repeat,dispatch=False):
 rows=receipts(policy);assert sum(bool(r.get('clean_repeat_of')) for p,r in rows)<policy['global_validation_repeat_if_nonnegative']==1
 assert not any((ROOT/n).exists() for n in policy['global_repeat_reservation_paths']),'Global positive repeat already reserved'
 existing=list((ROOT/policy['result_root']).glob('*/receipt.json'));coord=ROOT/policy['coordination_root']
 if repeat:assert len(existing)==1 and load(existing[0]).get('result',{}).get('component_internal_100MHz_pass') is True
 else:assert not existing and not(coord/'source-trial-reservation.json').exists(),'Single cursor source trial already used/reserved'
 if dispatch:
  active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith(policy['heavy_container_prefix']) for n in active)<policy['max_heavy_jobs']==2

def validate_positive_parent(r,c,pins,recipes,policy_sha):
 assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and r['result']['component_internal_100MHz_pass'] is True and not r['clean_repeat_of']
 assert r['runtime_control']==pins['runtime_control'] and r['default_gate']==pins['default_gate'] and r['qualification_helper']==pins['qualification_helper']
 assert r['policy_path']==rel(POLICY) and r['policy_sha256']==policy_sha and r['source_contract']==c and r['source_sha256']==c['source_sha256'] and r['source_origins']==c['source_origins']
 assert r['observability_contract']==OBSERVABILITY and r['directives']==DIRECTIVES and r['synth_directive']=='RuntimeOptimized' and r['synth_directive_cli']=='explicit'
 assert r.get('observed_synth_directive_log')=='RuntimeOptimized' and r['start_mode']=='rtl' and r['synthesis_executed'] and r['clock_loaded_before_synthesis_in_this_run'] and not r['clock_inherited_from_parent_checkpoint']
 for n in ('run.tcl','report.tcl','component.xdc'):assert r['recipe_sha256'][n]==recipes[n]

def prepare(a):
 policy=load(POLICY);base,card,c,pins=qualification(policy);budget(policy,bool(a.repeat_of));repeat=None
 if a.repeat_of:
  assert a.repeat_of.resolve().parent.parent==(ROOT/policy['result_root']).resolve()
  validate_positive_parent(load(a.repeat_of),c,pins,{n:sha(FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')},sha(POLICY));repeat=dict(path=rel(a.repeat_of),sha256=sha(a.repeat_of))
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6];trial='v110-cursors-'+('positive-repeat' if repeat else 'comparison');build=BUILD/(trial+'-'+stamp);out=ROOT/policy['prepared_root']/build.name;build.mkdir();out.mkdir(parents=True)
 for a,m in c['source_origins'].items():p=build/'snapshot'/a;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/m['path'],p)
 for n in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/n,build/n)
 mapped=Path('/build')/build.name;order=card['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial),'set start_mode {rtl}','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')];(build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
 common=dict(**pins,source_contract=c,source_order=order,directives=DIRECTIVES,synth_directive='RuntimeOptimized',synth_directive_cli='explicit',observability_contract=OBSERVABILITY,policy_sha256=sha(POLICY),clock_period_ns=10.0,part=policy['part'])
 write(out/'contract.json',dict(schema='v110-cursors-contract-v1',**common));parent=base['artifacts']['synth.dcp'];assert sha(Path(parent['external_path']))==parent['sha256']
 i=dict(schema='v110-cursors-inputs-v1',**common,trial_id=trial,profile_label='same-method-cursor-source',variant='combined',start_mode='rtl',clean_repeat_of=repeat,checkpoint_from=None,hypothesis='Owner-local private cursor payload removes measured read_segment to cursor reset cone; no public or live-owner timing change.',source_origins=c['source_origins'],source_sha256=c['source_sha256'],top='cs88_pipeline_v91k',closure_files=18,RTL_files=17,parent_synthesis_checkpoint=parent,timeout_seconds=2400,native_contract_path=rel(out/'contract.json'),native_contract_sha256=sha(out/'contract.json'),policy_path=rel(POLICY),recipe_sha256={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},tooling_sha256={rel(p):sha(p) for p in (Path(__file__).resolve(),FLOW/'run_native.py',ROOT/pins['qualification_helper']['path'])})
 write(build/'inputs.json',i)
 for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl','inputs.json'):shutil.copyfile(build/n,out/n)
 control=ROOT/pins['runtime_control']['path'];assert module(FLOW/'run_native.py').parse_reports(control.parent/'reports')==load(control)['result']
 write(out/'preflight.json',dict(schema='v110-native-preflight-v1',status='PREPARED_NOT_RUN',trial_id=trial,profile_label=i['profile_label'],build_external=str(build),inputs_sha256=sha(build/'inputs.json'),**common,recipe_sha256=i['recipe_sha256'],tooling_sha256=i['tooling_sha256'],start_mode='rtl',parser_test='PASS_ACTUAL_R5_PREFIX_RUNTIME_CONTROL_REPORTS'));print('CURSORS_PREPARED_NOT_RUN',rel(out/'preflight.json'),sha(out/'preflight.json'))

def launch(a):
 p=load(a.preflight);build=Path(p['build_external']);i=load(build/'inputs.json');policy=load(POLICY)
 assert p['status']=='PREPARED_NOT_RUN' and sha(build/'inputs.json')==p['inputs_sha256'] and sha(POLICY)==i['policy_sha256']==p['policy_sha256']
 contract=load(ROOT/i['native_contract_path']);assert sha(ROOT/i['native_contract_path'])==i['native_contract_sha256']
 _,card,c,pins=qualification(policy);assert c==i['source_contract']==p['source_contract']==contract['source_contract'] and card['source_order']==i['source_order']==p['source_order']==contract['source_order']
 for n,v in pins.items():assert v==i[n]==p[n]==contract[n]
 for n,v in dict(directives=DIRECTIVES,synth_directive='RuntimeOptimized',synth_directive_cli='explicit',observability_contract=OBSERVABILITY,clock_period_ns=10.0,part=policy['part']).items():assert v==i[n]==p[n]==contract[n]
 assert i['start_mode']=='rtl' and i['checkpoint_from'] is None and i['source_sha256']==c['source_sha256'] and i['source_origins']==c['source_origins']
 for n,h in i['tooling_sha256'].items():assert sha(ROOT/n)==h
 assert i['tooling_sha256']==p['tooling_sha256']
 for n,h in i['recipe_sha256'].items():assert sha(build/n)==h==p['recipe_sha256'][n]
 for n in ('run.tcl','report.tcl','component.xdc'):assert sha(FLOW/n)==i['recipe_sha256'][n]
 for n,h in i['source_sha256'].items():assert sha(build/'snapshot'/n)==h
 gate=load(a.audit);assert gate['status']=='PASS_V110_NATIVE_PREFLIGHT_AUDIT' and gate['preflight_sha256']==sha(a.preflight) and gate['policy_sha256']==sha(POLICY)
 budget(policy,bool(i['clean_repeat_of']),True)
 if i['clean_repeat_of']:
  rp=ROOT/i['clean_repeat_of']['path'];assert rp.resolve().parent.parent==(ROOT/policy['result_root']).resolve() and sha(rp)==i['clean_repeat_of']['sha256'];validate_positive_parent(load(rp),c,pins,{n:sha(FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')},sha(POLICY))
 coord=ROOT/policy['coordination_root'];coord.mkdir(parents=True,exist_ok=True);reservation=coord/('positive-repeat-reservation.json' if i['clean_repeat_of'] else 'source-trial-reservation.json')
 d=dict(status='DISPATCHED_TO_RUNNER',trial_id=i['trial_id'],profile_label=i['profile_label'],prepared_inputs_sha256=sha(build/'inputs.json'),preflight=rel(a.preflight),preflight_sha256=sha(a.preflight),audit=rel(a.audit),audit_sha256=sha(a.audit),policy_sha256=sha(POLICY),**pins,synth_directive='RuntimeOptimized',observability_contract=OBSERVABILITY,hypothesis=i['hypothesis'])
 with reservation.open('x') as f:f.write(json.dumps(d,indent=2,sort_keys=True)+'\n')
 proc=subprocess.run([sys.executable,str(FLOW/'run_native.py'),'--build',str(build),'--dispatch',str(reservation),'--license-file',str(a.license_file)],cwd=ROOT);write(coord/('completion-'+build.name+'.json'),dict(reservation=rel(reservation),exit_code=proc.returncode));proc.check_returncode()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
 if a.run:assert a.preflight and a.audit and not a.repeat_of;launch(a)
 else:assert not a.preflight and not a.audit;prepare(a)
if __name__=='__main__':main()
