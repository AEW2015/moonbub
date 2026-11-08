#!/usr/bin/env python3
"""Prepare/dispatch ONLY the globally allowed positive fresh-RTL Default repeat.

No preparation occurs without a selected completed --control. Existing study
sources, helpers, flows, policies and receipts are read-only inputs.
"""
import argparse,datetime,hashlib,importlib.util,json,subprocess,sys,uuid,shutil,re,shlex
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v110';FLOW=ROOT/'fpga/experiments/cu66-v110-default-flow';POLICY=AREA/'default-policy.json';BUILD=Path('/home/lori/gamebub-build/cu66-v69')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.resolve().relative_to(ROOT))
def word(s):
 s=str(s);assert not any(c in s for c in '{}\r\n');return '{'+s+'}'
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.dont_write_bytecode=True;spec.loader.exec_module(m);return m

def receipts(policy):
 return [(p,load(p))for n in policy['global_receipt_roots']for p in(ROOT/n).glob('*/receipt.json')]
def selection(path,policy):
 assert sha(ROOT/policy['original_policy_path'])==policy['original_policy_sha256']
 rows=[(p,load(p))for p in(AREA/'native').glob('*/receipt.json')]
 assert len(rows)==policy['required_completed_negative_controls']==5,'Wait for exactly five completed RuntimeOptimized controls'
 for p,r in rows:
  assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and not r['result']['component_internal_100MHz_pass'] and r['result']['timing']['WNS_ns']<0
  assert r['start_mode']=='rtl' and r['synthesis_executed'] and r['clock_loaded_before_synthesis_in_this_run'] and r['clock_period_ns']==10.0
  assert sha(p.parent/'recipe-snapshot/run.tcl')==r['recipe_sha256']['run.tcl']
  assert '-directive RuntimeOptimized' in(p.parent/'recipe-snapshot/run.tcl').read_text()
  assert not r['clean_repeat_of']
  assert r['directives']==dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default')
  assert r['cpus']==r['max_threads']==2 and r['memory_limit_bytes']==r['memory_swap_limit_bytes']==8*1024**3 and r['timeout_seconds']==2400
 selected=next((r for p,r in rows if p.resolve()==path.resolve()),None);assert selected,'Control must be an original V110 receipt'
 assert selected['result']['timing']['WNS_ns']==max(r['result']['timing']['WNS_ns']for p,r in rows),'Select highest final WNS control'
 return selected

def qualification(control):
 q=control['source_contract'];parts=Path(q['canonical_qualification']).parts
 mapping={'canonical':'native.py','canonical-dequant':'native_dequant.py','canonical-ready-rice':'native_ready.py','canonical-prefix':'native_prefix.py'}
 labels=[(label,name)for label,name in mapping.items()if label in parts];assert len(labels)==1,parts
 label,name=labels[0];variant=parts[parts.index(label)+1];helper=ROOT/'scripts/cu66-v110'/name;bound=dict(path=rel(helper),sha256=sha(helper),variant=variant)
 base,card,current=module(helper,'default_qualification_helper').qualification(variant)
 assert current==q and current['source_origins']==control['source_origins'] and current['source_sha256']==control['source_sha256']
 assert len(current['source_origins'])==18 and len(card['source_order']['rtl_read_order_aliases'])==17
 for alias,m in current['source_origins'].items():assert sha(ROOT/m['path'])==m['sha256']
 canonical=load(ROOT/q['canonical_qualification']);assert canonical['actual_RTL_run'] and canonical['status']=='PASS_EXACT_V110_CANONICAL'
 assert all(sha(ROOT/n)==h for n,h in canonical['source_sha256'].items())
 return base,card,current,bound

def budget(policy,repeat,at_dispatch=False):
 all_receipts=receipts(policy)
 assert sum(bool(r.get('clean_repeat_of'))for p,r in all_receipts)<policy['global_validation_repeat_if_nonnegative']==1,'Global positive-repeat budget exhausted'
 existing=list((ROOT/policy['result_root']).glob('*/receipt.json'))
 coord=ROOT/policy['coordination_root']
 if repeat:
  assert len(existing)==1 and load(existing[0])['result']['component_internal_100MHz_pass']
  assert not(coord/'positive-repeat-reservation.json').exists(),'Repeat already reserved'
 else:
  assert not existing and not(coord/'methodology-trial-reservation.json').exists(),'Methodology trial already used/reserved'
 if at_dispatch:
  active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
  assert sum(n.startswith(policy['heavy_container_prefix'])for n in active)<policy['max_heavy_jobs']==2,'Global heavy budget exhausted'

def default_log_evidence(parent,parent_log_path):
 """Prove effective Default from actual hash-pinned tool command, never invent a message."""
 assert sha(parent_log_path)==parent['log_sha256'],'Positive parent actual log SHA changed'
 text=Path(parent_log_path).read_text();commands=[]
 for line in text.splitlines():
  match=re.match(r'^\s*Command:\s*(.*)$',line)
  if match:
   args=shlex.split(match[1])
   if args and args[0]=='synth_design':commands.append((line.strip(),args))
 assert len(commands)==1,'Require exactly one tool-emitted synthesis Command line'
 line,args=commands[0]
 expected=['synth_design','-top','cs88_pipeline_v91k','-part','xc7a100tcsg324-1','-mode','out_of_context','-flatten_hierarchy','rebuilt']
 assert args in(expected,expected+['-directive','default']),'Synthesis command differs from frozen Default flow (or adds retiming)'
 messages=re.findall(r'Directive used for synth_design is:\s*(\w+)',text)
 assert all(value.lower()=='default'for value in messages),'Actual directive message is not default'
 observed=parent.get('observed_synth_directive_log')
 assert observed is None or(isinstance(observed,str)and observed.lower()=='default'),'Parent observed directive is not default'
 return dict(schema='v110-default-repeat-parent-log-evidence-v1',method='effective-default-from-hash-pinned-tool-command',parent_log_path=str(Path(parent_log_path).resolve()),parent_log_sha256=parent['log_sha256'],tool_command=line,tool_command_argv=args,effective_synth_directive='default',command_directive_omitted=args==expected,tool_directive_messages=messages,parent_observed_synth_directive_log=observed,parent_observed_value_modified=False)

def validate_positive_parent(parent,runtime_control,policy_sha256,source_contract,source_sha256,directives,recipe_sha256,parent_log_path):
 """One shared, side-effect-free preparation/dispatch repeat-parent guard.

 inputs.tcl is deliberately excluded: its source paths name a new build.
 Every functional run/report/XDC byte hash and all eighteen sources must match.
 """
 assert parent['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and parent['result']['component_internal_100MHz_pass'] is True
 assert parent['runtime_control']==runtime_control,'Positive parent RuntimeOptimized control changed'
 assert parent['policy_sha256']==policy_sha256 and parent['policy_path']==rel(POLICY),'Positive parent policy changed'
 assert parent['source_contract']==source_contract and parent['source_sha256']==source_sha256 and len(source_sha256)==18,'Positive parent source/proof contract changed'
 assert parent['directives']==directives,'Positive parent implementation directives changed'
 assert parent['synth_directive']=='default' and parent['synth_directive_cli']=='omitted','Positive parent method changed'
 assert parent['start_mode']=='rtl' and parent['synthesis_executed'] is True and parent['clock_loaded_before_synthesis_in_this_run'] is True
 assert parent['clock_inherited_from_parent_checkpoint'] is False and not parent['clean_repeat_of'],'Positive parent must be original fresh RTL Default trial'
 for name in('run.tcl','report.tcl','component.xdc'):
  assert parent['recipe_sha256'][name]==recipe_sha256[name],('Positive parent functional recipe changed',name)
 return default_log_evidence(parent,parent_log_path)

def prepare(a):
 assert a.repeat_of,'This driver only prepares a positive fresh repeat'
 policy=load(POLICY);control=selection(a.control,policy);base,card,c,helper=qualification(control);budget(policy,bool(a.repeat_of))
 runtime=dict(path=rel(a.control),sha256=sha(a.control),trial_id=control['trial_id'],WNS_ns=control['result']['timing']['WNS_ns'],synth_directive='RuntimeOptimized')
 repeat=None
 if a.repeat_of:
  r=load(a.repeat_of);assert a.repeat_of.resolve().is_relative_to((ROOT/policy['result_root']).resolve())
  evidence=validate_positive_parent(r,runtime,sha(POLICY),c,control['source_sha256'],dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default'),{n:sha(FLOW/n)for n in('run.tcl','report.tcl','component.xdc')},a.repeat_of.parent/'vivado.log')
  repeat=dict(path=rel(a.repeat_of),sha256=sha(a.repeat_of))
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6]
 trial='v110-default-'+('positive-repeat'if repeat else'comparison');build=BUILD/(trial+'-'+stamp);out=ROOT/policy['prepared_root']/build.name;build.mkdir();out.mkdir(parents=True)
 for alias,m in c['source_origins'].items():p=build/'snapshot'/alias;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/m['path'],p)
 for n in('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/n,build/n)
 mapped=Path('/build')/build.name;order=card['source_order'];directives=dict(opt='Default',place='ExtraNetDelay_high',phys_opt=None,phys_opt_stage=None,route='Default')
 lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial),'set start_mode {rtl}','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n)for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n)for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
 (build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
 contract=dict(schema='v110-default-repeat-contract-v1',positive_parent_evidence=evidence,runtime_control=runtime,qualification_helper=helper,source_contract=c,source_order=order,directives=directives,synth_directive='default',synth_directive_cli='omitted',policy_sha256=sha(POLICY),clock_period_ns=10.0,part=policy['part'])
 write(out/'contract.json',contract)
 parent=base['artifacts']['synth.dcp'];assert sha(Path(parent['external_path']))==parent['sha256']
 inp=dict(schema='v110-default-repeat-inputs-v1',positive_parent_evidence=evidence,trial_id=trial,profile_label='same-source-default',variant=helper['variant'],start_mode='rtl',synth_directive='default',synth_directive_cli='omitted',runtime_control=runtime,qualification_helper=helper,clean_repeat_of=repeat,checkpoint_from=None,hypothesis='Single same-source Default synthesis comparison; all implementation settings unchanged.',source_order=order,source_contract=c,source_origins=c['source_origins'],source_sha256=c['source_sha256'],part=policy['part'],top='cs88_pipeline_v91k',clock_period_ns=10.0,closure_files=18,RTL_files=17,parent_synthesis_checkpoint=parent,directives=directives,timeout_seconds=2400,native_contract_path=rel(out/'contract.json'),native_contract_sha256=sha(out/'contract.json'),policy_path=rel(POLICY),policy_sha256=sha(POLICY),recipe_sha256={n:sha(build/n)for n in('run.tcl','report.tcl','component.xdc','inputs.tcl')},tooling_sha256={rel(p):sha(p)for p in(Path(__file__).resolve(),FLOW/'run_native.py',ROOT/helper['path'])})
 write(build/'inputs.json',inp)
 for n in('run.tcl','report.tcl','component.xdc','inputs.tcl','inputs.json'):shutil.copyfile(build/n,out/n)
 assert module(FLOW/'run_native.py','default_report_parser').parse_reports(a.control.parent/'reports')==control['result']
 pf=dict(schema='v110-native-preflight-v1',positive_parent_evidence=evidence,status='PREPARED_NOT_RUN',trial_id=trial,profile_label='same-source-default',build_external=str(build),inputs_sha256=sha(build/'inputs.json'),policy_sha256=sha(POLICY),runtime_control=runtime,qualification_helper=helper,synth_directive='default',synth_directive_cli='omitted',source_contract=c,source_order=order,recipe_sha256=inp['recipe_sha256'],tooling_sha256=inp['tooling_sha256'],start_mode='rtl',parser_test='PASS_ACTUAL_SELECTED_RUNTIME_CONTROL_REPORTS')
 write(out/'preflight.json',pf);print('DEFAULT_PREPARED_NOT_RUN',rel(out/'preflight.json'),sha(out/'preflight.json'))

def launch(a):
 p=load(a.preflight);build=Path(p['build_external']);i=load(build/'inputs.json');policy=load(POLICY)
 assert i['clean_repeat_of'],'This driver only launches a positive fresh repeat'
 assert p['status']=='PREPARED_NOT_RUN' and sha(build/'inputs.json')==p['inputs_sha256'] and sha(POLICY)==p['policy_sha256']==i['policy_sha256']
 assert sha(ROOT/i['native_contract_path'])==i['native_contract_sha256']
 control_path=ROOT/i['runtime_control']['path'];assert sha(control_path)==i['runtime_control']['sha256'];control=selection(control_path,policy);_,_,current,helper=qualification(control)
 assert current==i['source_contract']==p['source_contract'] and helper==i['qualification_helper']==p['qualification_helper']
 for n,h in i['tooling_sha256'].items():assert sha(ROOT/n)==h
 for n,h in i['recipe_sha256'].items():assert sha(build/n)==h
 for n,h in i['source_sha256'].items():assert sha(build/'snapshot'/n)==h
 gate=load(a.audit);assert gate['status']=='PASS_V110_NATIVE_PREFLIGHT_AUDIT' and gate['preflight_sha256']==sha(a.preflight) and gate['policy_sha256']==sha(POLICY)
 budget(policy,bool(i['clean_repeat_of']),True)
 if i['clean_repeat_of']:
  rp=ROOT/i['clean_repeat_of']['path'];assert sha(rp)==i['clean_repeat_of']['sha256'];r=load(rp)
  evidence=validate_positive_parent(r,i['runtime_control'],sha(POLICY),current,i['source_sha256'],i['directives'],{n:sha(FLOW/n)for n in('run.tcl','report.tcl','component.xdc')},rp.parent/'vivado.log')
  assert evidence==i['positive_parent_evidence']==p['positive_parent_evidence']==load(ROOT/i['native_contract_path'])['positive_parent_evidence'],'Pinned positive-parent evidence changed'
 coord=ROOT/policy['coordination_root'];coord.mkdir(parents=True,exist_ok=True)
 reservation=coord/('positive-repeat-reservation.json'if i['clean_repeat_of']else'methodology-trial-reservation.json')
 dispatch=dict(status='DISPATCHED_TO_RUNNER',positive_parent_evidence=evidence,trial_id=i['trial_id'],profile_label='same-source-default',prepared_inputs_sha256=sha(build/'inputs.json'),preflight=rel(a.preflight),preflight_sha256=sha(a.preflight),audit=rel(a.audit),audit_sha256=sha(a.audit),policy_sha256=sha(POLICY),runtime_control=i['runtime_control'],synth_directive='default',hypothesis=i['hypothesis'])
 with reservation.open('x')as f:f.write(json.dumps(dispatch,indent=2,sort_keys=True)+'\n')
 proc=subprocess.run([sys.executable,str(FLOW/'run_native.py'),'--build',str(build),'--dispatch',str(reservation),'--license-file',str(a.license_file)],cwd=ROOT)
 write(coord/('completion-'+build.name+'.json'),dict(reservation=rel(reservation),exit_code=proc.returncode));proc.check_returncode()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--control',type=Path);ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));a=ap.parse_args()
 if a.run:assert a.preflight and a.audit and not a.control and not a.repeat_of;launch(a)
 else:assert a.control and a.repeat_of and not a.preflight and not a.audit;prepare(a)
if __name__=='__main__':main()
