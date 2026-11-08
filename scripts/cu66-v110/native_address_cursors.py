#!/usr/bin/env python3
"""One prospective Default source composition, gated by Cursor outcome and full Q.

No automatic retries or checkpoint starts. Root grants preparation and native
execution separately; both eligibility and the exact proof closure are rechecked.
"""
import argparse,datetime,hashlib,importlib.util,json,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v110';FLOW=ROOT/'fpga/experiments/cu66-v110-address-cursors-flow';POLICY=AREA/'address-cursors-policy.json';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
DIRECTIVES=dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default')
OBSERVABILITY=dict(public_cycles='exact, including invalid addresses/data/counters/debug/memory',live_cursors='exact whenever either reference or candidate owner is live',retired_private_cursor_payload='intentionally may differ; restored before new ownership',request_prepared_payload='coherent with original full-width address/bounds in uncancelled FETCH_REQ; inactive speculative private values unconstrained',all_private_state_exact=False,public_latency_delta_cycles=0,original_proofs_unchanged=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.resolve().relative_to(ROOT))
def word(s):
 s=str(s);assert not any(c in s for c in '{}\r\n');return '{'+s+'}'
def module(path):
 spec=importlib.util.spec_from_file_location('address_bound_'+path.stem,path);m=importlib.util.module_from_spec(spec);sys.dont_write_bytecode=True;spec.loader.exec_module(m);return m

def helpers(policy):
 mods=[]
 for key in ('qualification_helper','shared_validation_helper','default_evidence_helper'):
  p=policy[key];assert sha(ROOT/p['path'])==p['sha256'];mods.append(module(ROOT/p['path']))
 return mods

def validate_cursor_gate(r,policy):
 assert r['policy_path']==policy['cursor_policy_path'] and r['policy_sha256']==policy['cursor_policy_sha256']
 assert r['start_mode']=='rtl' and r['synthesis_executed'] and not r['clean_repeat_of'] and r['synth_directive']=='RuntimeOptimized' and r['synth_directive_cli']=='explicit'
 if r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
  assert r['result']['component_internal_100MHz_pass'] is False,'Cursor achieved timing: skip composition and repeat Cursor'
 else:
  assert r['status'] in ('TOOL_OR_BUILD_FAILED','STOPPED_RESOURCE_OR_TIME_GATE','ROUTE_FINISHED_REPORT_PARSE_FAILED'),'Cursor attempt is not terminal'
  assert not (r.get('result') or {}).get('component_internal_100MHz_pass',False)
 assert 'observed_exit_code' in r and r['log_sha256'],'Require actual terminal Cursor evidence'

def parent_closure(policy):
 prefix,shared,evidence=helpers(policy)
 for key in ('original','default','cursor'):assert sha(ROOT/policy[key+'_policy_path'])==policy[key+'_policy_sha256']
 for n,h in policy['frozen_default_flow_sha256'].items():assert sha(ROOT/'fpga/experiments/cu66-v110-default-flow'/n)==h
 control_pin=policy['source_method_control'];cp=ROOT/control_pin['path'];assert sha(cp)==control_pin['sha256'];control=load(cp)
 assert control['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and control['result']['component_internal_100MHz_pass'] is False and control['result']['timing']['WNS_ns']==-1.199
 assert control['start_mode']=='rtl' and control['synthesis_executed'] and control['clock_loaded_before_synthesis_in_this_run'] and not control['clock_inherited_from_parent_checkpoint'] and not control['clean_repeat_of']
 assert control['synth_directive']=='default' and control['synth_directive_cli']=='omitted' and control['directives']==DIRECTIVES and control['clock_period_ns']==10.0
 assert control['cpus']==control['max_threads']==2 and control['memory_limit_bytes']==control['memory_swap_limit_bytes']==8*1024**3 and control['timeout_seconds']==2400
 base,card,parent=prefix.qualification('combined');assert parent==control['source_contract'] and parent['source_sha256']==control['source_sha256'] and parent['source_origins']==control['source_origins']
 shared.validate_canonical(ROOT/parent['canonical_qualification'])
 for n,h in parent['focused_proofs'].items():assert sha(ROOT/n)==h;shared.validate_focused(ROOT/n)
 for a,m in parent['source_origins'].items():assert sha(ROOT/m['path'])==m['sha256']==sha(cp.parent/'source-snapshot'/a)
 for n in ('run.tcl','report.tcl','component.xdc'):assert sha(FLOW/n)==policy['frozen_default_flow_sha256'][n]==control['recipe_sha256'][n]==sha(cp.parent/'recipe-snapshot'/n)
 ev=evidence.default_log_evidence(control,cp.parent/'vivado.log')
 pins=dict(source_method_control=dict(control_pin),source_method_control_evidence=ev,qualification_helper=dict(policy['qualification_helper'],variant='combined'),shared_validation_helper=policy['shared_validation_helper'],default_evidence_helper=policy['default_evidence_helper'])
 return base,card,parent,pins,shared,evidence

def eligibility(policy):
 result=parent_closure(policy);gp=ROOT/policy['cursor_gate_path'];gate=load(gp);validate_cursor_gate(gate,policy);assert sha(gp.parent/'vivado.log')==gate['log_sha256']
 result[3]['cursor_gate']=dict(path=rel(gp),sha256=sha(gp),status=gate['status'],role='terminal eligibility only; not source or method baseline')
 return result

def validate_source_delta(parent,origins,policy):
 assert set(origins)==set(parent['source_origins']) and len(origins)==18
 changed={a for a in origins if origins[a]!=parent['source_origins'][a]}
 assert changed=={policy['scratch_alias'],policy['request_alias']},'Exactly scratch and synchronous ingress may change from actual Default source control'
 for alias,key in ((policy['scratch_alias'],'candidate_scratch_path'),(policy['request_alias'],'candidate_request_path')):
  assert origins[alias]['path']==policy[key] and origins[alias]['sha256']!=parent['source_sha256'][alias]

def request_closure(policy):
 fp=ROOT/policy['request_focus_path'];assert sha(fp)==policy['request_focus_sha256'];f=load(fp);assert f['status']=='PASS' and f['actual_RTL_run'] and f['strict_warnings']
 selected=ROOT/f['selected_report'];assert sha(selected)==f['selected_report_sha256']
 for n,h in f['source_sha256'].items():assert sha(ROOT/n)==h
 for n,h in f['artifacts_sha256'].items():assert sha(selected.parent/n)==h
 adapter=ROOT/policy['request_adapter_path'];assert sha(adapter)==policy['request_adapter_sha256']==f['source_sha256'][rel(adapter)]
 assert load(adapter)['all_public_ports_compared'] is True and len(f['negative_owner_contract_rejections'])==6
 assert f['source_sha256'][policy['candidate_request_path']]=='ac7260e749ace036495a162882fdb30fdb129d2c7ddde8df67bc2a8957f8f4b1'
 return f

def qualification(policy):
 base,card,parent,pins,shared,evidence=eligibility(policy);path=AREA/'canonical-address-cursors/combined/results.json';q=shared.validate_canonical(path);assert len(q['replacements'])==8
 aliases=card['source_order']['rtl_read_order_aliases']+[a for a in card['source_origins'] if a.endswith('.svh')];paths=q['rtl_source_order']
 assert len(aliases)==len(paths)==18 and len(set(paths))==18 and sum(n.endswith('.sv') for n in paths)==17
 origins={a:dict(path=n,sha256=sha(ROOT/n)) for a,n in zip(aliases,paths)};validate_source_delta(parent,origins,policy)
 assert all(q['source_sha256'][m['path']]==m['sha256'] for m in origins.values())
 fp=ROOT/policy['cursor_focus_path'];f=shared.validate_focused(fp);assert f['strict_warnings'] and not f['warning_suppression'] and len(f['scratch_runs'])==2
 adapter=ROOT/policy['observability_adapter_path'];assert sha(adapter)==policy['observability_adapter_sha256']==f['source_sha256'][rel(adapter)] and load(adapter)['original_assertions_and_oracles_retained'] is True
 assert any(x['source']==parent['source_origins'][policy['scratch_alias']]['path'] and x['source_sha256']==parent['source_sha256'][policy['scratch_alias']] for x in load(adapter)['adapters'])
 for row in f['scratch_runs']:
  v=row['cursor_retirement'];assert v['status']=='TEST_PASS' and v['cursor_retirement_cases']==v['inactive_divergence_cases']==v['restored_new_owner_cases']==6 and row['inherited']['status']=='TEST_PASS'
 assert f['source_sha256'][policy['candidate_scratch_path']]==origins[policy['scratch_alias']]['sha256'];request_closure(policy)
 proofs=dict(parent['focused_proofs']);proofs.pop('experiments/python-gamebub-v110/busy/results.json');proofs[rel(fp)]=sha(fp);proofs[policy['request_focus_path']]=policy['request_focus_sha256']
 for n,h in proofs.items():assert sha(ROOT/n)==h==q['source_sha256'][n]
 c=dict(source_origins=origins,source_sha256={a:m['sha256'] for a,m in origins.items()},parent_receipt=parent['parent_receipt'],parent_receipt_sha256=parent['parent_receipt_sha256'],parent_clock_loaded_before_synthesis=True,canonical_qualification=rel(path),canonical_sha256=sha(path),focused_proofs=proofs,observability_contract=OBSERVABILITY,qualification_scope='Exact all public/invalid addresses/cycles/counters/debug/memory and live cursors. Retired private cursors and inactive prepared request payload may differ. No hardware or complete-parent qualification.')
 return base,card,c,pins,evidence

def budget(policy,repeat,dispatch=False):
 rows=[load(p) for n in policy['global_receipt_roots'] for p in (ROOT/n).glob('*/receipt.json')]
 assert sum(bool(r.get('clean_repeat_of')) for r in rows)<policy['global_validation_repeat_if_nonnegative']==1
 assert not any((ROOT/n).exists() for n in policy['global_repeat_reservation_paths']),'Global repeat already reserved'
 previous=list((ROOT/policy['result_root']).glob('*/receipt.json'));coord=ROOT/policy['coordination_root']
 if repeat:assert len(previous)==1 and (load(previous[0]).get('result') or {}).get('component_internal_100MHz_pass') is True
 else:assert not previous and not (coord/'source-trial-reservation.json').exists(),'Only one source trial; no silent retry'
 if dispatch:
  active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith(policy['heavy_container_prefix']) for n in active)<policy['max_heavy_jobs']==2

def validate_positive_parent(r,c,pins,recipes,policy_sha,parent_log,evidence):
 assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and r['result']['component_internal_100MHz_pass'] is True and not r['clean_repeat_of']
 assert all(r[n]==pins[n] for n in ('source_method_control','source_method_control_evidence','cursor_gate','qualification_helper'))
 assert r['policy_path']==rel(POLICY) and r['policy_sha256']==policy_sha and r['source_contract']==c and r['source_sha256']==c['source_sha256'] and r['source_origins']==c['source_origins']
 assert r['observability_contract']==OBSERVABILITY and r['directives']==DIRECTIVES and r['synth_directive']=='default' and r['synth_directive_cli']=='omitted'
 assert r['start_mode']=='rtl' and r['synthesis_executed'] and r['clock_loaded_before_synthesis_in_this_run'] and not r['clock_inherited_from_parent_checkpoint']
 assert r['timeout_seconds']==3600 and r['cpus']==r['max_threads']==2 and r['memory_limit_bytes']==r['memory_swap_limit_bytes']==8*1024**3
 for n in ('run.tcl','report.tcl','component.xdc'):assert r['recipe_sha256'][n]==recipes[n]
 return evidence.default_log_evidence(r,parent_log)

def prepare(a):
 policy=load(POLICY);base,card,c,pins,evidence=qualification(policy);budget(policy,bool(a.repeat_of));repeat=None;positive_evidence=None
 if a.repeat_of:
  assert a.repeat_of.resolve().parent.parent==(ROOT/policy['result_root']).resolve()
  positive_evidence=validate_positive_parent(load(a.repeat_of),c,pins,{n:sha(FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')},sha(POLICY),a.repeat_of.parent/'vivado.log',evidence);repeat=dict(path=rel(a.repeat_of),sha256=sha(a.repeat_of))
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6];trial='v110-address-cursors-'+('positive-repeat' if repeat else 'comparison');build=BUILD/(trial+'-'+stamp);out=ROOT/policy['prepared_root']/build.name;build.mkdir();out.mkdir(parents=True)
 for a,m in c['source_origins'].items():p=build/'snapshot'/a;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/m['path'],p)
 for n in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/n,build/n)
 mapped=Path('/build')/build.name;order=card['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial),'set start_mode {rtl}','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')];(build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
 common=dict(**pins,source_contract=c,source_order=order,directives=DIRECTIVES,synth_directive='default',synth_directive_cli='omitted',observability_contract=OBSERVABILITY,policy_sha256=sha(POLICY),clock_period_ns=10.0,part=policy['part'],positive_parent_evidence=positive_evidence,source_delta_aliases=[policy['scratch_alias'],policy['request_alias']])
 write(out/'contract.json',dict(schema='v110-address-cursors-contract-v1',**common));parent=base['artifacts']['synth.dcp'];assert sha(Path(parent['external_path']))==parent['sha256']
 i=dict(schema='v110-address-cursors-inputs-v1',**common,trial_id=trial,profile_label='same-default-two-source-composition',variant='combined',start_mode='rtl',clean_repeat_of=repeat,checkpoint_from=None,hypothesis='Compose existing cursor owner-local reset cut with exact prepared-request bounds/address, targeting measured R5 cursor reset and R6 band-address bounds cones.',source_origins=c['source_origins'],source_sha256=c['source_sha256'],top='cs88_pipeline_v91k',closure_files=18,RTL_files=17,parent_synthesis_checkpoint=parent,timeout_seconds=3600,native_contract_path=rel(out/'contract.json'),native_contract_sha256=sha(out/'contract.json'),policy_path=rel(POLICY),recipe_sha256={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},tooling_sha256={rel(p):sha(p) for p in (Path(__file__).resolve(),FLOW/'run_native.py',*[ROOT/pins[k]['path'] for k in ('qualification_helper','shared_validation_helper','default_evidence_helper')])})
 write(build/'inputs.json',i)
 for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl','inputs.json'):shutil.copyfile(build/n,out/n)
 cp=ROOT/pins['source_method_control']['path'];assert module(FLOW/'run_native.py').parse_reports(cp.parent/'reports')==load(cp)['result']
 write(out/'preflight.json',dict(schema='v110-native-preflight-v1',status='PREPARED_NOT_RUN',trial_id=trial,profile_label=i['profile_label'],build_external=str(build),inputs_sha256=sha(build/'inputs.json'),**common,recipe_sha256=i['recipe_sha256'],tooling_sha256=i['tooling_sha256'],start_mode='rtl',timeout_seconds=3600,parser_test='PASS_ACTUAL_DEFAULT_R6_CONTROL_REPORTS'));print('ADDRESS_CURSORS_PREPARED_NOT_RUN',rel(out/'preflight.json'),sha(out/'preflight.json'))

def launch(a):
 p=load(a.preflight);build=Path(p['build_external']);i=load(build/'inputs.json');policy=load(POLICY)
 assert p['status']=='PREPARED_NOT_RUN' and sha(build/'inputs.json')==p['inputs_sha256'] and sha(POLICY)==i['policy_sha256']==p['policy_sha256']
 contract=load(ROOT/i['native_contract_path']);assert sha(ROOT/i['native_contract_path'])==i['native_contract_sha256']
 _,card,c,pins,evidence=qualification(policy);assert c==i['source_contract']==p['source_contract']==contract['source_contract'] and card['source_order']==i['source_order']==p['source_order']==contract['source_order']
 for n,v in pins.items():assert v==i[n]==p[n]==contract[n]
 for n,v in dict(directives=DIRECTIVES,synth_directive='default',synth_directive_cli='omitted',observability_contract=OBSERVABILITY,clock_period_ns=10.0,part=policy['part'],source_delta_aliases=[policy['scratch_alias'],policy['request_alias']]).items():assert v==i[n]==p[n]==contract[n]
 assert i['start_mode']=='rtl' and i['checkpoint_from'] is None and i['timeout_seconds']==p['timeout_seconds']==policy['native_timeout_seconds']==3600 and i['source_sha256']==c['source_sha256'] and i['source_origins']==c['source_origins']
 for n,h in i['tooling_sha256'].items():assert sha(ROOT/n)==h
 assert i['tooling_sha256']==p['tooling_sha256']
 for n,h in i['recipe_sha256'].items():assert sha(build/n)==h==p['recipe_sha256'][n]
 for n in ('run.tcl','report.tcl','component.xdc'):assert sha(FLOW/n)==i['recipe_sha256'][n]
 for n,h in i['source_sha256'].items():assert sha(build/'snapshot'/n)==h
 gate=load(a.audit);assert gate['status']=='PASS_V110_NATIVE_PREFLIGHT_AUDIT' and gate['preflight_sha256']==sha(a.preflight) and gate['policy_sha256']==sha(POLICY)
 budget(policy,bool(i['clean_repeat_of']),True);positive_evidence=None
 if i['clean_repeat_of']:
  rp=ROOT/i['clean_repeat_of']['path'];assert rp.resolve().parent.parent==(ROOT/policy['result_root']).resolve() and sha(rp)==i['clean_repeat_of']['sha256'];positive_evidence=validate_positive_parent(load(rp),c,pins,{n:sha(FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')},sha(POLICY),rp.parent/'vivado.log',evidence)
 assert positive_evidence==i['positive_parent_evidence']==p['positive_parent_evidence']==contract['positive_parent_evidence']
 coord=ROOT/policy['coordination_root'];coord.mkdir(parents=True,exist_ok=True);reservation=coord/('positive-repeat-reservation.json' if i['clean_repeat_of'] else 'source-trial-reservation.json')
 d=dict(status='DISPATCHED_TO_RUNNER',trial_id=i['trial_id'],profile_label=i['profile_label'],prepared_inputs_sha256=sha(build/'inputs.json'),preflight=rel(a.preflight),preflight_sha256=sha(a.preflight),audit=rel(a.audit),audit_sha256=sha(a.audit),policy_sha256=sha(POLICY),**pins,synth_directive='default',positive_parent_evidence=positive_evidence,observability_contract=OBSERVABILITY,hypothesis=i['hypothesis'])
 with reservation.open('x') as f:f.write(json.dumps(d,indent=2,sort_keys=True)+'\n')
 proc=subprocess.run([sys.executable,str(FLOW/'run_native.py'),'--build',str(build),'--dispatch',str(reservation),'--license-file',str(a.license_file)],cwd=ROOT);write(coord/('completion-'+build.name+'.json'),dict(reservation=rel(reservation),exit_code=proc.returncode));proc.check_returncode()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
 if a.run:assert a.preflight and a.audit and not a.repeat_of;launch(a)
 else:assert not a.preflight and not a.audit;prepare(a)
if __name__=='__main__':main()
