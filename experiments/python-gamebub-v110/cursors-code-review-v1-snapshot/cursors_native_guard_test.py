#!/usr/bin/env python3
"""Lightweight actual validator tests; no PF, Docker, synthesis, simulation or launch."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile
P=Path(__file__).resolve().with_name('native_cursors.py');spec=importlib.util.spec_from_file_location('cursors_tested',P);m=importlib.util.module_from_spec(spec);sys.dont_write_bytecode=True;spec.loader.exec_module(m)
policy=m.load(m.POLICY);out=m.AREA/'cursors-native-guard-tests.json';cases=[]
def check(name,call,pass_expected):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:
  assert not pass_expected,(name,repr(e));cases.append(dict(name=name,rejected=True,error=repr(e)));return
 assert pass_expected,name;cases.append(dict(name=name,accepted=True))
runtime=policy['runtime_control'];control=m.load(m.ROOT/runtime['path']);dp=m.ROOT/policy['default_gate_path'];default=m.load(dp)
# Mock terminal states explicitly; the actual Default attempt may still be RUNNING.
gate=copy.deepcopy(default);gate.update(status='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN',observed_exit_code=0,log_sha256='actual-format-mock',result=dict(component_internal_100MHz_pass=False,timing=dict(WNS_ns=-1.0)))
check('terminal-negative-Default-mock',lambda:m.validate_default_gate(gate,runtime,policy['default_policy_sha256']),True)
for status in ('TOOL_OR_BUILD_FAILED','STOPPED_RESOURCE_OR_TIME_GATE','ROUTE_FINISHED_REPORT_PARSE_FAILED'):
 x=copy.deepcopy(gate);x['status']=status;check('terminal-failure-'+status,lambda:m.validate_default_gate(x,runtime,policy['default_policy_sha256']),True)
for name,change in [('active-Default',lambda x:x.update(status='RUNNING')),('positive-Default',lambda x:x.update(result=dict(component_internal_100MHz_pass=True,timing=dict(WNS_ns=0.1)))),('wrong-Default-control',lambda x:x['runtime_control'].update(sha256='changed')),('wrong-Default-policy',lambda x:x.update(policy_sha256='changed')),('wrong-Default-method',lambda x:x.update(synth_directive='RuntimeOptimized')),('missing-terminal-log',lambda x:x.pop('log_sha256'))]:
 x=copy.deepcopy(gate);change(x);check(name,lambda:m.validate_default_gate(x,runtime,policy['default_policy_sha256']),False)
parent=control['source_contract'];origins=copy.deepcopy(parent['source_origins']);alias=policy['scratch_alias'];origins[alias]=dict(path=policy['candidate_scratch_path'],sha256=m.sha(m.ROOT/policy['candidate_scratch_path']))
check('actual-eighteen-only-scratch-delta',lambda:m.validate_source_delta(parent,origins,policy),True)
for name,change in [('unchanged-scratch',lambda x:x.update({alias:parent['source_origins'][alias]})),('second-source-changed',lambda x:x[next(a for a in x if a!=alias)].update(sha256='changed')),('missing-header',lambda x:x.pop(next(a for a in x if a.endswith('.svh')))),('wrong-scratch-body',lambda x:x[alias].update(path='other/scratch.sv'))]:
 x=copy.deepcopy(origins);change(x);check(name,lambda:m.validate_source_delta(parent,x,policy),False)
check('actual-frozen-PREFIX-full-public-raw-artifact-closure',lambda:m.validate_canonical(m.ROOT/parent['canonical_qualification']),True)
for n in ('busy','fault','dequant','ready','prefix','cursors'):check('actual-'+n+'-focus-source-and-artifact-closure',lambda n=n:m.validate_focused(m.AREA/n/'results.json'),True)
c=copy.deepcopy(parent);c['source_origins']=origins;c['source_sha256']={a:x['sha256'] for a,x in origins.items()};pins=dict(runtime_control=runtime,default_gate=dict(path=m.rel(dp),sha256=m.sha(dp)),qualification_helper=dict(policy['qualification_helper'],variant='combined'));recipes={n:m.sha(m.FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')}
r=copy.deepcopy(control);r.update(status='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN',result=dict(component_internal_100MHz_pass=True),runtime_control=runtime,default_gate=pins['default_gate'],qualification_helper=pins['qualification_helper'],policy_path=m.rel(m.POLICY),policy_sha256=m.sha(m.POLICY),source_contract=c,source_sha256=c['source_sha256'],source_origins=origins,observability_contract=m.OBSERVABILITY,synth_directive='RuntimeOptimized',synth_directive_cli='explicit',observed_synth_directive_log='RuntimeOptimized',recipe_sha256=recipes)
check('positive-cursor-parent-mock',lambda:m.validate_positive_parent(r,c,pins,recipes,m.sha(m.POLICY)),True)
for name,change in [('parent-control-changed',lambda x:x['runtime_control'].update(sha256='changed')),('parent-Default-gate-changed',lambda x:x['default_gate'].update(sha256='changed')),('parent-policy-changed',lambda x:x.update(policy_sha256='changed')),('parent-proof-changed',lambda x:x['source_contract'].update(canonical_sha256='changed')),('parent-source-changed',lambda x:x['source_sha256'].update({alias:'changed'})),('parent-private-scope-changed',lambda x:x['observability_contract'].update(all_private_state_exact=True)),('parent-method-changed',lambda x:x.update(synth_directive='default')),('parent-observed-method-missing',lambda x:x.update(observed_synth_directive_log=None)),('parent-nonpositive',lambda x:x['result'].update(component_internal_100MHz_pass=False)),('parent-checkpoint',lambda x:x.update(start_mode='checkpoint')),('parent-repeat-of-repeat',lambda x:x.update(clean_repeat_of={'path':'prior'}))]+[(f'parent-{n}-changed',lambda x,n=n:x['recipe_sha256'].update({n:'changed'})) for n in recipes]:
 x=copy.deepcopy(r);change(x);check(name,lambda:m.validate_positive_parent(x,c,pins,recipes,m.sha(m.POLICY)),False)
# Temporary global ledger fixtures exercise actual shared budget guard without subprocess.
oldroot=m.ROOT
with tempfile.TemporaryDirectory(prefix='v110-cursors-budget-test-') as d:
 m.ROOT=Path(d)
 for n in policy['global_receipt_roots']+['experiments/python-gamebub-v110/cursors-coordination']:(m.ROOT/n).mkdir(parents=True)
 check('empty-cursor-ledger',lambda:m.budget(policy,False),True)
 p=m.ROOT/policy['global_receipt_roots'][1]/'trial/receipt.json';p.parent.mkdir();m.write(p,dict(clean_repeat_of={'path':'prior'}));check('global-Default-repeat-already-used',lambda:m.budget(policy,False),False);p.unlink()
 reservation=m.ROOT/policy['global_repeat_reservation_paths'][0];reservation.parent.mkdir(parents=True,exist_ok=True);reservation.write_text('{}');check('global-Default-repeat-reserved',lambda:m.budget(policy,False),False);reservation.unlink()
 p=m.ROOT/policy['result_root']/'first/receipt.json';p.parent.mkdir();m.write(p,dict(result=dict(component_internal_100MHz_pass=False)));check('cursor-trial-already-used',lambda:m.budget(policy,False),False);check('negative-cursor-repeat',lambda:m.budget(policy,True),False)
 m.write(p,dict(result=dict(component_internal_100MHz_pass=True)));check('one-positive-cursor-repeat-eligible',lambda:m.budget(policy,True),True)
 p.unlink();res=m.ROOT/policy['coordination_root']/'source-trial-reservation.json';res.write_text('{}');check('cursor-initial-reserved',lambda:m.budget(policy,False),False)
m.ROOT=oldroot
m.write(out,dict(status='PASS',scope='Actual pure validators plus explicit mocked terminal/positive-parent/temporary-ledger fixtures; no PF/native/heavy. No timing result is inferred.',driver_sha256=m.sha(P),policy_sha256=m.sha(m.POLICY),actual_Default_status_at_test=default['status'],positive_tests=sum('accepted'in x for x in cases),negative_tests=sum('rejected'in x for x in cases),tests=cases,frozen_parent_flow_sha256=policy['frozen_parent_flow_sha256']))
print('CURSOR_NATIVE_GUARDS_PASS',len(cases),m.sha(out))
