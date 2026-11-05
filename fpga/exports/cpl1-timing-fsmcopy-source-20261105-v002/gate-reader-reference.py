"""Read final reports, bind actual implementation inputs, and fail closed on timing."""
import argparse,pathlib,json,re,hashlib
R=pathlib.Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('candidate');a.add_argument('--label',default='board01');a=a.parse_args()
P=R/'candidates'/a.candidate;E=P/'evidence'/a.label
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((P/'source-freeze.json').read_text())
for n,h in freeze['files'].items():assert sha(P/n)==h and sha(E/'inputs'/n)==h,n
execution=json.loads((E/'execution.json').read_text())
if isinstance(execution,dict):assert execution['returncode']==0 and execution.get('parent_unchanged',True),execution
else:assert execution and all(step['returncode']==0 for step in execution),execution
s=(E/'timing-summary.rpt').read_text();lines=s.splitlines();i=next(i for i,l in enumerate(lines)if l.strip().startswith('WNS(ns)'));v=lines[i+2].split();assert len(v)==12,v
timing=dict(setup_wns_ns=float(v[0]),setup_tns_ns=float(v[1]),setup_failing_endpoints=int(v[2]),hold_whs_ns=float(v[4]),hold_failing_endpoints=int(v[6]),pulse_wpws_ns=float(v[8]),pulse_failing_endpoints=int(v[10]))
route=(E/'route-status.rpt').read_text()
def number(label):
 m=re.search(label+r'\.*\s*:\s*(\d+)',route,re.I);assert m,label;return int(m.group(1))
# Report wording is retained verbatim; no fallback silently treats unknown as zero.
counts=dict(routable=number(r'# of routable nets'),fully_routed=number(r'# of fully routed nets'),routing_errors=number(r'# of nets with routing errors'))
ct=(E/'check-timing.rpt').read_text()
required_zero=['no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock','generated_clocks','loops','latch_loops']
for check in required_zero:assert re.search(r'checking '+check+r' \(0\)',ct),check
gaps={name:int(re.search(r'checking '+name+r' \((\d+)\)',ct)[1])for name in ['no_input_delay','no_output_delay','partial_input_delay']}
assert gaps==dict(no_input_delay=17,no_output_delay=2,partial_input_delay=1),gaps
bus=(E/'bus-skew.rpt').read_text()
bus_paths=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[0-9.]+)ns',bus)
assert len(bus_paths)==4,('Expected four declared bus-skew constraints',bus_paths)
bus_pass=all(status=='MET'and float(slack)>0 for status,slack in bus_paths)
passed=timing['setup_wns_ns']>0 and timing['hold_whs_ns']>0 and timing['pulse_wpws_ns']>0 and all(timing[n]==0 for n in ['setup_failing_endpoints','hold_failing_endpoints','pulse_failing_endpoints']) and counts['routable']>0 and counts['routable']==counts['fully_routed'] and counts['routing_errors']==0
passed=passed and bus_pass
result=dict(status='PASS_ROUTED_TIMING_ONLY'if passed else'FAIL_ROUTED_TIMING',timing=timing,route=counts,source_freeze_sha256=sha(P/'source-freeze.json'),routed_dcp_sha256=sha(E/'routed.dcp'),source_inputs_unchanged=True,constraints_relaxed=False,BIT=False,hardware=False,unique_30fps_proven=False,reports={n:sha(E/n)for n in ['timing-summary.rpt','route-status.rpt','setup-paths.rpt','hold-paths.rpt','drc.rpt','cdc.rpt','exceptions.rpt','clock-interaction.rpt','check-timing.rpt','utilization.rpt']})
result['retained_constraint_gaps']=gaps
result['bus_skew']={'declared_constraints':4,'met':bus_pass,'minimum_slack_ns':min(float(slack)for _,slack in bus_paths)}
result['reports']['bus-skew.rpt']=sha(E/'bus-skew.rpt')
result['gate_reader_sha256']=sha(pathlib.Path(__file__))
result['execution_record_sha256']=sha(E/'execution.json')
result['physical_placement_changed']=isinstance(execution,dict)and execution.get('physical_placement_changed',False)
result['qualification_scope']='Internal and originally declared I/O timing. Retained asynchronous/unbudgeted I/O coverage gaps are not silently closed.'
(E/'timing-gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if passed else 2)
