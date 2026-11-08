#!/usr/bin/env python3
"""One prospective caller-specialized count-domain Default source trial.

No automatic retries or checkpoint starts. Root grants preparation and native
execution separately; both eligibility and the exact proof closure are rechecked.
"""
import argparse,datetime,hashlib,importlib.util,json,shutil,subprocess,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v110';FLOW=ROOT/'fpga/experiments/cu66-v110-count-domain-flow';POLICY=AREA/'count-domain-policy.json';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
DIRECTIVES=dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default')
OBSERVABILITY=dict(public_cycles='exact, including invalid addresses/data/counters/debug/memory',live_cursors='exact whenever either reference or candidate owner is live',retired_private_cursor_payload='intentionally may differ; restored before new ownership',request_prepared_payload='coherent with original full-width address/bounds in uncancelled FETCH_REQ; inactive speculative private values unconstrained',generic_context='PREVALIDATED_EVENT_COUNT defaults false; unconditional all-input equivalence',specialized_context='True only at selected synchronous ingress; AC event_count<=uint64(blocks)*band_width at actual consumed start; comparison conditional on this owner precondition',external_packet_API='all public invalid/error/counter/memory cycles exact; caller precondition failure blocks qualification',all_private_state_exact=False,public_latency_delta_cycles=0,original_proofs_unchanged=True)
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

def validate_negative_parent(control):
 assert control['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and control['result']['component_internal_100MHz_pass'] is False,'Positive parent must be repeated, not extended'
 assert control['result']['timing']['WNS_ns']==-1.365
 assert control['start_mode']=='rtl' and control['synthesis_executed'] and control['clock_loaded_before_synthesis_in_this_run'] and not control['clock_inherited_from_parent_checkpoint'] and not control['clean_repeat_of']
 assert control['synth_directive']=='default' and control['synth_directive_cli']=='omitted' and control['directives']==DIRECTIVES and control['clock_period_ns']==10.0
 assert control['cpus']==control['max_threads']==2 and control['memory_limit_bytes']==control['memory_swap_limit_bytes']==8*1024**3 and control['timeout_seconds']==3600

def parent_closure(policy):
 parent_helper,shared,evidence=helpers(policy)
 for key in ('original','default','cursor','parent'):assert sha(ROOT/policy[key+'_policy_path'])==policy[key+'_policy_sha256']
 for n,h in policy['frozen_default_flow_sha256'].items():assert sha(ROOT/'fpga/experiments/cu66-v110-address-cursors-flow'/n)==h
 control_pin=policy['source_method_control'];cp=ROOT/control_pin['path'];assert sha(cp)==control_pin['sha256'];control=load(cp);validate_negative_parent(control)
 base,card,parent,_,_=parent_helper.qualification(load(ROOT/policy['parent_policy_path']))
 assert parent==control['source_contract'] and parent['source_sha256']==control['source_sha256'] and parent['source_origins']==control['source_origins']
 shared.validate_canonical(ROOT/parent['canonical_qualification'])
 for n,h in parent['focused_proofs'].items():assert sha(ROOT/n)==h
 for a,m in parent['source_origins'].items():assert sha(ROOT/m['path'])==m['sha256']==sha(cp.parent/'source-snapshot'/a)
 for n in ('run.tcl','report.tcl','component.xdc'):assert sha(FLOW/n)==policy['frozen_default_flow_sha256'][n]==control['recipe_sha256'][n]==sha(cp.parent/'recipe-snapshot'/n)
 ev=evidence.default_log_evidence(control,cp.parent/'vivado.log')
 pins=dict(source_method_control=dict(control_pin),source_method_control_evidence=ev,qualification_helper=dict(policy['qualification_helper'],variant='combined'),shared_validation_helper=policy['shared_validation_helper'],default_evidence_helper=policy['default_evidence_helper'],negative_parent_gate=dict(control_pin,status=control['status'],role='negative actual source/method parent; positive would skip extension'))
 return base,card,parent,pins,shared,evidence

def eligibility(policy):return parent_closure(policy)

def validate_source_delta(parent,origins,policy):
 assert set(origins)==set(parent['source_origins']) and len(origins)==18
 changed={a for a in origins if origins[a]!=parent['source_origins'][a]}
 assert changed=={policy['context_alias'],policy['request_alias']},'Exactly context and synchronous ingress may change from actual composed Default control'
 for alias,key in ((policy['context_alias'],'candidate_context_path'),(policy['request_alias'],'candidate_request_path')):
  assert origins[alias]['path']==policy[key] and origins[alias]['sha256']!=parent['source_sha256'][alias]

def validate_specialization_scope(adapter,recipe,model):
 assert adapter['generic_pair_unconditional'] is True and adapter['all_public_ports_including_invalid_and_counters'] is True and adapter['all_original_assertions_and_goldens_retained'] is True
 assert adapter['specialized_pair_precondition']=='Owned start band0 or band>3 or AC count<=unsigned64 blocks*factor; reset/abort always compared. Other invalid config fields do not exempt comparison.'
 assert recipe['all_original_assertions_retained'] is True and recipe['added_public_cycles']==0
 assert model['independent_arithmetic_check']['status']=='PASS_INTEGER_MODEL_NOT_RTL' and model['independent_arithmetic_check']['rows']==3944427 and model['domain']['valid_blocks']==[1,65536]
 assert model['domain']['factor_by_band']=={'0':1,'1':5,'2':15,'3':43}

def specialization_inputs(policy):
 for key in ('count_adapter','count_recipe','caller_model'):
  assert sha(ROOT/policy[key+'_path'])==policy[key+'_sha256']
 adapter=load(ROOT/policy['count_adapter_path']);recipe=load(ROOT/policy['count_recipe_path']);model=load(ROOT/policy['caller_model_path']);validate_specialization_scope(adapter,recipe,model)
 for n,h in policy['candidate_source_sha256'].items():assert sha(ROOT/n)==h
 context=(ROOT/policy['candidate_context_path']).read_text();caller=(ROOT/policy['candidate_request_path']).read_text()
 assert "parameter bit PREVALIDATED_EVENT_COUNT=1'b0" in context and '(!PREVALIDATED_EVENT_COUNT && event_count>start_limit)' in context
 assert caller.count("br88_context #(.PREVALIDATED_EVENT_COUNT(1'b1)) context_decoder (")==1
 assert 'prevalidated context block domain' in caller and 'prevalidated DC count relation' in caller and 'prevalidated AC count relation' in caller
 # Reconstruct both candidates from immutable originals and exact bounded edits.
 for entry in recipe['production'].values():
  origin=ROOT/entry['original'];assert sha(origin)==entry['original_sha256'];text=origin.read_text()
  for edit in entry['edits']:assert text.count(edit['before'])==edit['expected_occurrences'];text=text.replace(edit['before'],edit['after'])
  assert hashlib.sha256(text.encode()).hexdigest()==entry['candidate_sha256']==sha(ROOT/entry['candidate'])
 return adapter,recipe,model

def validate_focused_execution(f):
 """Fourteen actual commands include six successful original-assertion rejections."""
 commands=f['commands'];assert len(commands)==14 and f['new_commands_use_pinned_content_ID'] is True
 image=f['tool_image_identity']['content_id'];assert image.startswith('sha256:')
 expected={(mode,index) for mode in (1,2) for index in (33,37,41)};negative=set()
 for command in commands:
  argv=command['argv'];assert image in argv and command['stop_reason'] is None
  assert argv[argv.index('--memory')+1]==argv[argv.index('--memory-swap')+1]=='4g' and argv[argv.index('--cpus')+1]=='2'
  if command.get('status')=='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION':
   assert command['exit_code']==134;negative.add((int(argv[-2]),int(argv[-1])))
  else:assert command['exit_code']==0
 assert negative==expected and len([x for x in commands if x.get('status')=='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'])==6
 assert {(x['mode'],x['index']) for x in f['negative_owner_contract_rejections']}==expected
 context=[];ingress_compile=[]
 for command in commands:
  argv=command['argv'];exe=next((i for i,x in enumerate(argv) if x.endswith('/context-obj/Vcontext_probe')),None)
  if exe is not None:context.append(int(argv[exe+2]))
  if '--top-module' in argv:
   assert argv[argv.index('--top-module')+1]=='ingress_capture_probe' and '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='1';ingress_compile.append(command)
 assert context==[111401,111402] and len(ingress_compile)==1
 reuse=f['context_compile_reuse'];assert reuse['status']=='REUSED_NOT_NEWLY_COMPILED' and reuse['binary_sha256']==f['context_binary_sha256'] and reuse['tool_image_content_id']==image
 for n,h in reuse['all_compilation_inputs_unchanged'].items():assert f['source_sha256'][n]==h
 argv=reuse['compile_command']['argv'];assert reuse['compile_command']['exit_code']==0 and reuse['compile_command']['stop_reason'] is None
 mapped=argv[argv.index('--Mdir')+1].removesuffix('/context-obj');normalized=[x.replace(mapped,'BUILD') for x in argv[argv.index('verilator'):]]
 assert normalized==reuse['normalized_actual_compile_command'] and hashlib.sha256(json.dumps(normalized,separators=(',',':')).encode()).hexdigest()==reuse['source_order_and_compiler_flags_sha256']
 assert normalized[normalized.index('--top-module')+1]=='context_probe' and '--assert' in normalized and '-Wall' in normalized and normalized[normalized.index('-j')+1]=='1'
 return dict(actual_new_commands=14,successful_positive_commands=8,expected_original_assertion_rejections=6,negative_exit_code=134,context_compile='REUSED_NOT_NEWLY_COMPILED',fresh_context_simulation_seeds=context,fresh_ingress_compiles=1)

def focused_closure(policy,shared):
 specialization_inputs(policy);path=ROOT/policy['count_focus_path'];f=shared.validate_focused(path);validate_focused_execution(f)
 reuse=f['context_compile_reuse'];prior_path=ROOT/reuse['prior_receipt'];assert sha(prior_path)==reuse['prior_receipt_sha256'];prior=load(prior_path)
 assert prior['context_binary_sha256']==reuse['binary_sha256'] and reuse['compile_command'] in prior['commands']
 for n,h in reuse['all_compilation_inputs_unchanged'].items():assert sha(ROOT/n)==h==prior['source_sha256'][n]
 selected=ROOT/f['selected_report'];assert sha(selected.parent/'version.log')==reuse['tool_version_stdout_sha256']
 for mode in (1,2):
  for index in (33,37,41):
   text=(selected.parent/f'negative-{mode}-{index}.log').read_text();assert 'stale staging response' in text and 'EXPECTED_ASSERTION_ARMED' in text and '"capture_enable":false' in text
 assert f['schema']=='v110-count-domain-focused-qualification-v1' and f['strict_warnings'] and not f['warning_suppression'] and f['all_private_state_exact_claim'] is False
 assert f['specialized_precondition']=='On consumed start: band0 or band>3 or event_count<=unsigned64(blocks)*(band1?5:band2?15:43). Captured per owner; reset/abort always compared. Only AC count-invalid owner excluded from enabled-context equivalence; generic remains unconditional.'
 assert len(f['context_runs'])==len(f['capture_runs'])==len(f['whole_ingress_runs'])==2 and len(f['negative_owner_contract_rejections'])==6
 for row in f['context_runs']:
  d=row['domain'];g=row['geometry'];v=row['inherited'];assert d['status']=='TEST_PASS' and d['cases']==8064 and d['enabled_cases']>0 and d['excluded_AC_count_cases']>0
  assert g['status']=='TEST_PASS' and g['cases']==4260918 and v['status']=='TEST_PASS' and v['cases']==55 and v['configurations']==8 and v['directed_checks']==172
 for row in f['whole_ingress_runs']:assert row['status']=='TEST_PASS' and row['packets']==76 and row['cancel_retries']==36 and row['boundary_mask']==15
 for key in ('count_adapter','count_recipe','caller_model'):assert f['source_sha256'][policy[key+'_path']]==policy[key+'_sha256']
 for n,h in policy['candidate_source_sha256'].items():assert f['source_sha256'][n]==h
 return f

def qualification(policy):
 base,card,parent,pins,shared,evidence=eligibility(policy);path=AREA/'canonical-count-domain/combined/results.json';q=shared.validate_canonical(path);assert len(q['replacements'])==9
 aliases=card['source_order']['rtl_read_order_aliases']+[a for a in card['source_origins'] if a.endswith('.svh')];paths=q['rtl_source_order']
 assert len(aliases)==len(paths)==18 and len(set(paths))==18 and sum(n.endswith('.sv') for n in paths)==17
 origins={a:dict(path=n,sha256=sha(ROOT/n)) for a,n in zip(aliases,paths)};validate_source_delta(parent,origins,policy)
 assert all(q['source_sha256'][m['path']]==m['sha256'] for m in origins.values())
 # Only the owned selected synchronous instance may enable specialization.
 assert sum((ROOT/m['path']).read_text().count(".PREVALIDATED_EVENT_COUNT(1'b1)") for m in origins.values())==1
 focused_closure(policy,shared);proofs=dict(parent['focused_proofs']);fp=ROOT/policy['count_focus_path'];proofs[rel(fp)]=sha(fp)
 for n,h in proofs.items():assert sha(ROOT/n)==h==q['source_sha256'][n]
 c=dict(source_origins=origins,source_sha256={a:m['sha256'] for a,m in origins.items()},parent_receipt=parent['parent_receipt'],parent_receipt_sha256=parent['parent_receipt_sha256'],parent_clock_loaded_before_synthesis=True,canonical_qualification=rel(path),canonical_sha256=sha(path),focused_proofs=proofs,observability_contract=OBSERVABILITY,caller_precondition_proof=dict(path=policy['caller_model_path'],sha256=policy['caller_model_sha256']),qualification_scope='Exact external packet API/public invalid/error/counter/debug/memory cycles; generic context unconditional, selected enabled context under verified internal caller count precondition. Existing retired cursor/inactive request private scope retained. No hardware or complete-parent qualification.')
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
 assert all(r[n]==pins[n] for n in ('source_method_control','source_method_control_evidence','negative_parent_gate','qualification_helper'))
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
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6];trial='v110-count-domain-'+('positive-repeat' if repeat else 'comparison');build=BUILD/(trial+'-'+stamp);out=ROOT/policy['prepared_root']/build.name;build.mkdir();out.mkdir(parents=True)
 for a,m in c['source_origins'].items():p=build/'snapshot'/a;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/m['path'],p)
 for n in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/n,build/n)
 mapped=Path('/build')/build.name;order=card['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial),'set start_mode {rtl}','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')];(build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
 common=dict(**pins,source_contract=c,source_order=order,directives=DIRECTIVES,synth_directive='default',synth_directive_cli='omitted',observability_contract=OBSERVABILITY,policy_sha256=sha(POLICY),clock_period_ns=10.0,part=policy['part'],positive_parent_evidence=positive_evidence,source_delta_aliases=[policy['context_alias'],policy['request_alias']])
 write(out/'contract.json',dict(schema='v110-count-domain-contract-v1',**common));parent=base['artifacts']['synth.dcp'];assert sha(Path(parent['external_path']))==parent['sha256']
 i=dict(schema='v110-count-domain-inputs-v1',**common,trial_id=trial,profile_label='same-default-count-domain-specialization',variant='combined',start_mode='rtl',clean_repeat_of=repeat,checkpoint_from=None,hypothesis='Remove only selected-caller redundant AC count rejection after proving its actual consumed-start domain; preserve generic default, all external packet behavior and runtime position bounds.',source_origins=c['source_origins'],source_sha256=c['source_sha256'],top='cs88_pipeline_v91k',closure_files=18,RTL_files=17,parent_synthesis_checkpoint=parent,timeout_seconds=3600,native_contract_path=rel(out/'contract.json'),native_contract_sha256=sha(out/'contract.json'),policy_path=rel(POLICY),recipe_sha256={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},tooling_sha256={rel(p):sha(p) for p in (Path(__file__).resolve(),FLOW/'run_native.py',*[ROOT/pins[k]['path'] for k in ('qualification_helper','shared_validation_helper','default_evidence_helper')])})
 write(build/'inputs.json',i)
 for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl','inputs.json'):shutil.copyfile(build/n,out/n)
 cp=ROOT/pins['source_method_control']['path'];assert module(FLOW/'run_native.py').parse_reports(cp.parent/'reports')==load(cp)['result']
 write(out/'preflight.json',dict(schema='v110-native-preflight-v1',status='PREPARED_NOT_RUN',trial_id=trial,profile_label=i['profile_label'],build_external=str(build),inputs_sha256=sha(build/'inputs.json'),**common,recipe_sha256=i['recipe_sha256'],tooling_sha256=i['tooling_sha256'],start_mode='rtl',timeout_seconds=3600,parser_test='PASS_ACTUAL_COMPOSED_DEFAULT_P8_CONTROL_REPORTS'));print('COUNT_DOMAIN_PREPARED_NOT_RUN',rel(out/'preflight.json'),sha(out/'preflight.json'))

def launch(a):
 p=load(a.preflight);build=Path(p['build_external']);i=load(build/'inputs.json');policy=load(POLICY)
 assert p['status']=='PREPARED_NOT_RUN' and sha(build/'inputs.json')==p['inputs_sha256'] and sha(POLICY)==i['policy_sha256']==p['policy_sha256']
 contract=load(ROOT/i['native_contract_path']);assert sha(ROOT/i['native_contract_path'])==i['native_contract_sha256']
 _,card,c,pins,evidence=qualification(policy);assert c==i['source_contract']==p['source_contract']==contract['source_contract'] and card['source_order']==i['source_order']==p['source_order']==contract['source_order']
 for n,v in pins.items():assert v==i[n]==p[n]==contract[n]
 for n,v in dict(directives=DIRECTIVES,synth_directive='default',synth_directive_cli='omitted',observability_contract=OBSERVABILITY,clock_period_ns=10.0,part=policy['part'],source_delta_aliases=[policy['context_alias'],policy['request_alias']]).items():assert v==i[n]==p[n]==contract[n]
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
