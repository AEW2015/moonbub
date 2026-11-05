"""Read-only routed gates with exact input bindings; writes a report even on failure."""
from pathlib import Path
import argparse,hashlib,json,re
a=argparse.ArgumentParser();a.add_argument('implementation');a.add_argument('--result');args=a.parse_args()
origin=Path(args.implementation).resolve();out=Path(args.result).resolve() if args.result else origin
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((origin/'source-freeze.json').read_text())
for n,h in freeze.items():assert sha(origin/n)==h,n
execution=json.loads((out/'execution.json').read_text());assert execution['returncode']==0
lines=(out/'timing-summary.rpt').read_text().splitlines()
i=next(i for i,line in enumerate(lines)if line.strip().startswith('WNS(ns)'))
v=lines[i+2].split();assert len(v)==12,v
timing=dict(setup_ns=float(v[0]),setup_failing=int(v[2]),hold_ns=float(v[4]),hold_failing=int(v[6]),pulse_ns=float(v[8]),pulse_failing=int(v[10]))
route=(out/'route-status.rpt').read_text()
def count(label):
    found=re.search(label+r'\.*\s*:\s*(\d+)',route,re.I);assert found,label
    return int(found[1])
routing=dict(routable=count('# of routable nets'),routed=count('# of fully routed nets'),errors=count('# of nets with routing errors'))
bus=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[0-9.]+)ns',(out/'bus-skew.rpt').read_text())
assert len(bus)==4,bus
ct=(out/'check-timing.rpt').read_text()
checks={}
for name in ['no_clock','constant_clock','unconstrained_internal_endpoints','multiple_clock','generated_clocks','loops','latch_loops','no_input_delay','no_output_delay','partial_input_delay']:
    match=re.search(r'checking '+name+r' \((\d+)\)',ct);assert match,name
    checks[name]=int(match[1])
expected_gaps=dict(no_input_delay=17,no_output_delay=2,partial_input_delay=1)
coverage_pass=(all(checks[k]==v for k,v in expected_gaps.items()) and
               all(checks[k]==0 for k in checks if k not in expected_gaps))
passed=(all(timing[k]>0 for k in ['setup_ns','hold_ns','pulse_ns']) and
        all(timing[k]==0 for k in ['setup_failing','hold_failing','pulse_failing']) and
        routing['routable']==routing['routed']>0 and routing['errors']==0 and
        all(status=='MET'and float(slack)>0 for status,slack in bus) and coverage_pass)
result=dict(status='PASS_DECLARED_ROUTED_TIMING'if passed else'FAIL_DECLARED_ROUTED_TIMING',timing=timing,route=routing,
            bus_skew=bus,coverage=checks,expected_coverage_gaps=expected_gaps,coverage_pass=coverage_pass,source_inputs_unchanged=True,source_freeze_sha256=sha(origin/'source-freeze.json'),
            DCP_sha256=sha(out/'routed.dcp'),read_phase_intentionally_changed=True,numeric_external_budgets_unchanged=True,
            physical_SDRAM_timing_proven=False,BIT=False,hardware=False,
            reports={n:sha(out/n)for n in ['timing-summary.rpt','route-status.rpt','bus-skew.rpt','check-timing.rpt','setup-paths.rpt','hold-paths.rpt','drc.rpt']})
(out/'timing-gate.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(0 if passed else 2)
