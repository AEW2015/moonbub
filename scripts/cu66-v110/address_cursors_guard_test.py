#!/usr/bin/env python3
"""Static/pure guards only: actual proof/log reads, explicit status mocks, temp ledgers."""
from pathlib import Path
import copy,importlib.util,json,sys,tempfile
P=Path(__file__).resolve().with_name('native_address_cursors.py');sp=importlib.util.spec_from_file_location('address_cursors_guards',P);m=importlib.util.module_from_spec(sp);sys.dont_write_bytecode=True;sp.loader.exec_module(m)
policy=m.load(m.POLICY);tests=[]
def check(name,call,positive):
 try:call()
 except (AssertionError,KeyError,ValueError,FileNotFoundError) as e:
  assert not positive,(name,repr(e));tests.append(dict(name=name,rejected=True,error=repr(e)));return
 assert positive,name;tests.append(dict(name=name,accepted=True))
check('actual-Default-parent-source-proofs-recipes-and-log-closure',lambda:m.parent_closure(policy),True)
base,card,parent,pins,shared,evidence=m.parent_closure(policy)
check('actual-frozen-request-source-artifact-and-negative-proof-closure',lambda:m.request_closure(policy),True)
check('actual-cursor-focused-source-and-artifact-closure',lambda:shared.validate_focused(m.ROOT/policy['cursor_focus_path']),True)
gp=m.ROOT/policy['cursor_gate_path'];actual_gate=m.load(gp);gate=copy.deepcopy(actual_gate);gate.update(status='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN',observed_exit_code=0,log_sha256='mock-terminal-pin',result=dict(component_internal_100MHz_pass=False,timing=dict(WNS_ns=-1.0)))
check('terminal-negative-Cursor-status-mock',lambda:m.validate_cursor_gate(gate,policy),True)
for status in ('TOOL_OR_BUILD_FAILED','STOPPED_RESOURCE_OR_TIME_GATE','ROUTE_FINISHED_REPORT_PARSE_FAILED'):
 x=copy.deepcopy(gate);x.update(status=status,result=None);check('failed-null-Cursor-'+status,lambda:m.validate_cursor_gate(x,policy),True)
for name,change in [('Cursor-active',lambda x:x.update(status='RUNNING')),('Cursor-positive',lambda x:x['result'].update(component_internal_100MHz_pass=True)),('Cursor-checkpoint-mode',lambda x:x.update(start_mode='checkpoint')),('Cursor-wrong-method',lambda x:x.update(synth_directive='default')),('Cursor-wrong-policy',lambda x:x.update(policy_sha256='changed')),('Cursor-repeat-gate',lambda x:x.update(clean_repeat_of={'path':'prior'})),('Cursor-no-terminal-log',lambda x:x.pop('log_sha256'))]:
 x=copy.deepcopy(gate);change(x);check(name,lambda:m.validate_cursor_gate(x,policy),False)
origins=copy.deepcopy(parent['source_origins'])
for a,key in ((policy['scratch_alias'],'candidate_scratch_path'),(policy['request_alias'],'candidate_request_path')):origins[a]=dict(path=policy[key],sha256=m.sha(m.ROOT/policy[key]))
check('actual-only-two-alias-changes',lambda:m.validate_source_delta(parent,origins,policy),True)
for name,change in [('one-delta-only',lambda x:x.update({policy['request_alias']:parent['source_origins'][policy['request_alias']]})),('three-deltas',lambda x:x[next(a for a in x if a not in (policy['scratch_alias'],policy['request_alias']))].update(sha256='changed')),('missing-header',lambda x:x.pop(next(a for a in x if a.endswith('.svh')))),('wrong-request-body',lambda x:x[policy['request_alias']].update(path='other/request.sv'))]:
 x=copy.deepcopy(origins);change(x);check(name,lambda:m.validate_source_delta(parent,x,policy),False)
c=copy.deepcopy(parent);c.update(source_origins=origins,source_sha256={a:v['sha256'] for a,v in origins.items()},observability_contract=m.OBSERVABILITY);pins['cursor_gate']=dict(path=m.rel(gp),sha256=m.sha(gp),role='explicit-mock-fixture-pin-only');recipes={n:m.sha(m.FLOW/n) for n in ('run.tcl','report.tcl','component.xdc')}
cp=m.ROOT/policy['source_method_control']['path'];r=copy.deepcopy(m.load(cp));r.update(result=dict(component_internal_100MHz_pass=True),source_contract=c,source_sha256=c['source_sha256'],source_origins=origins,source_method_control=pins['source_method_control'],source_method_control_evidence=pins['source_method_control_evidence'],cursor_gate=pins['cursor_gate'],qualification_helper=pins['qualification_helper'],policy_path=m.rel(m.POLICY),policy_sha256=m.sha(m.POLICY),observability_contract=m.OBSERVABILITY,recipe_sha256=recipes,timeout_seconds=3600)
log=cp.parent/'vivado.log'
check('positive-parent-status-mock-actual-Default-command-and-None-observation',lambda:m.validate_positive_parent(r,c,pins,recipes,m.sha(m.POLICY),log,evidence),True)
assert r['observed_synth_directive_log'] is None,'Test preserves actual omitted-command/no-message format'
for name,change in [('parent-source-method-control',lambda x:x['source_method_control'].update(sha256='changed')),('parent-Cursor-gate',lambda x:x['cursor_gate'].update(sha256='changed')),('parent-Default-command-evidence',lambda x:x['source_method_control_evidence'].update(parent_log_sha256='changed')),('parent-policy',lambda x:x.update(policy_sha256='changed')),('parent-proof',lambda x:x['source_contract'].update(canonical_sha256='changed')),('parent-source',lambda x:x['source_sha256'].update({policy['request_alias']:'changed'})),('parent-public-RF-scope',lambda x:x['observability_contract'].update(public_cycles='valid-only')),('parent-inactive-private-RF-scope',lambda x:x['observability_contract'].update(all_private_state_exact=True)),('parent-Runtime-method',lambda x:x.update(synth_directive='RuntimeOptimized')),('parent-explicit-method-CLI',lambda x:x.update(synth_directive_cli='explicit')),('parent-observed-Runtime-message',lambda x:x.update(observed_synth_directive_log='runtimeoptimized')),('parent-checkpoint-mode',lambda x:x.update(start_mode='checkpoint')),('parent-log-SHA',lambda x:x.update(log_sha256='changed')),('parent-timeout',lambda x:x.update(timeout_seconds=2400)),('parent-memory',lambda x:x.update(memory_swap_limit_bytes=16*1024**3)),('parent-nonpositive',lambda x:x['result'].update(component_internal_100MHz_pass=False))]+[(f'parent-{n}-recipe',lambda x,n=n:x['recipe_sha256'].update({n:'changed'})) for n in recipes]:
 x=copy.deepcopy(r);change(x);check(name,lambda:m.validate_positive_parent(x,c,pins,recipes,m.sha(m.POLICY),log,evidence),False)
oldroot=m.ROOT
with tempfile.TemporaryDirectory(prefix='v110-address-cursors-budget-') as d:
 m.ROOT=Path(d)
 for n in policy['global_receipt_roots']+['experiments/python-gamebub-v110/address-cursors-coordination']:(m.ROOT/n).mkdir(parents=True)
 check('empty-new-trial-ledger',lambda:m.budget(policy,False),True)
 for idx,n in enumerate(policy['global_receipt_roots']):
  p=m.ROOT/n/'fixture/receipt.json';p.parent.mkdir();m.write(p,dict(clean_repeat_of={'path':'prior'}));check('global-repeat-used-in-root-'+str(idx),lambda:m.budget(policy,False),False);p.unlink()
 for idx,n in enumerate(policy['global_repeat_reservation_paths']):
  p=m.ROOT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('{}');check('global-repeat-reserved-in-root-'+str(idx),lambda:m.budget(policy,False),False);p.unlink()
 p=m.ROOT/policy['result_root']/'first/receipt.json';p.parent.mkdir();m.write(p,dict(result=dict(component_internal_100MHz_pass=False)));check('initial-already-used',lambda:m.budget(policy,False),False);check('negative-repeat-parent',lambda:m.budget(policy,True),False);m.write(p,dict(result=dict(component_internal_100MHz_pass=True)));check('one-positive-new-repeat-eligible',lambda:m.budget(policy,True),True);p.unlink()
 p=m.ROOT/policy['coordination_root']/'source-trial-reservation.json';p.write_text('{}');check('initial-already-reserved',lambda:m.budget(policy,False),False)
m.ROOT=oldroot
out=m.AREA/'address-cursors-guard-tests.json';m.write(out,dict(status='PASS',scope='Pure/static validators only; actual Default source/proof/log closure plus explicit terminal/positive mocks and temp ledgers. No PF/native/heavy or timing-pass inference.',driver_sha256=m.sha(P),policy_sha256=m.sha(m.POLICY),actual_Cursor_status_at_test=actual_gate['status'],actual_Default_control_sha256=m.sha(cp),actual_Default_observed_synth_directive_log=r['observed_synth_directive_log'],actual_Default_evidence=pins['source_method_control_evidence'],positive_tests=sum('accepted' in x for x in tests),negative_tests=sum('rejected' in x for x in tests),tests=tests))
print('ADDRESS_CURSOR_GUARDS_PASS',len(tests),m.sha(out))
