#!/usr/bin/env python3
"""Audit single runtime9 post-route diagnostic provenance/reports without Vivado."""
import argparse,csv,hashlib,json,re
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,sort_keys=True,indent=2)+'\n')
def metrics(p):
 lines=p.read_text().splitlines();j=next(i for i,s in enumerate(lines) if s.lstrip().startswith('WNS(ns)'));v=lines[j+2].split();assert len(v)==12
 return dict(WNS_ns=float(v[0]),TNS_ns=float(v[1]),setup_failing_endpoints=int(v[2]),setup_total_endpoints=int(v[3]),WHS_ns=float(v[4]),THS_ns=float(v[5]),hold_failing_endpoints=int(v[6]),hold_total_endpoints=int(v[7]),WPWS_ns=float(v[8]),TPWS_ns=float(v[9]),pulse_failing_endpoints=int(v[10]),pulse_total_endpoints=int(v[11]))
def rules(p):return [dict(rule=a,severity=b,checks=int(c)) for a,b,c in re.findall(r'^\|\s*([A-Z]+-\d+)\s*\|\s*(Warning|Critical Warning|Error)\s*\|[^\n]*\|\s*(\d+)\s*\|',p.read_text(),re.M)]
def normalized(p):return [s.strip() for s in p.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')]
def legal(p):
 s=p.read_text();find=lambda n:int(re.search(n+r'\.+\s*:\s*(\d+)',s).group(1));r=dict(routable=find('# of routable nets'),fully_routed=find('# of fully routed nets'),routing_errors=find('# of nets with routing errors'));assert r['routable']==r['fully_routed'] and r['routing_errors']==0;return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--area',type=Path,default=Path(__file__).resolve().parents[2]/'experiments/python-gamebub-v107/postroute-probe');args=ap.parse_args();area=args.area;selected=json.loads((area/'results.json').read_text());out=area/Path(selected['selected_receipt']).parent.name;r=json.loads((out/'receipt.json').read_text());assert sha(out/'receipt.json')==selected['sha256'];assert r['status'] in ('DIAGNOSTIC_ROUTE_COMPLETED_SIGNOFF_UNASSESSED','FAIL_OR_BOUNDED_PROBE');assert not r['stop_reason']
 for n,h in r['retained_sha256'].items():assert sha(out/n)==h,n
 parent=json.loads((out/'parent-receipt.json').read_text());inp=json.loads((out/'parent-inputs.json').read_text());q=json.loads((out/'canonical-qualification.json').read_text());dispatch=json.loads((out/'parent-dispatch.json').read_text())
 assert parent['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and parent['observed_exit_code']==0;assert dispatch['status']=='RUNNER_RETURNED' and dispatch['runner_exit_code']==0
 assert r['parent_receipt_sha256']==r['parent_receipt_sha256_after']==sha(out/'parent-receipt.json');assert r['checkpoint_sha256_before']==r['checkpoint_sha256_after']==parent['artifacts']['route.dcp']['sha256'];assert r['parent_unchanged'] and r['source_snapshots_unchanged']
 assert sha(out/'parent-inputs.json')==parent['source_manifest_sha256']==r['parent_manifest_sha256'];assert sha(out/'canonical-qualification.json')==inp['behavioral_qualification']['sha256']==r['canonical_sha256'];assert q['status']=='PASS_EXACT_THRESHOLD_CANONICAL' and q['actual_RTL_run']
 expected={n:h for n,h in q['source_sha256'].items() if Path(n).suffix in ('.sv','.svh')};assert expected==r['source_sha256']=={v['path']:v['sha256'] for v in inp['source_origins'].values()} and len(expected)==18
 for n,h in parent['retained_source_snapshot_sha256'].items():assert sha(out/'sources'/n)==h,n
 assert sha(out/'report.tcl')==parent['recipe_snapshots_sha256']['report.tcl']==r['report_tcl_sha256'];assert sha(out/'component.xdc')==parent['recipe_snapshots_sha256']['component.xdc']==r['constraint_file_sha256'];assert r['physical_commands']==['phys_opt_design -directive AggressiveExplore']
 t=(out/'run.tcl').read_text();assert t.count('\nphys_opt_design -directive AggressiveExplore\n')==1 and '\nroute_design ' not in t and 'synth_design' not in t and 'read_xdc' not in t
 settings=dict(csv.reader((out/'reports/settings.tsv').open(),delimiter='\t'));assert settings['part']=='xc7a100tcsg324-1' and float(settings['period_ns'])==10 and settings['clock']=='component_clk' and settings['max_threads']=='2'
 assert normalized(out/'reports/before-effective-timing.xdc')==normalized(out/'parent-reports/effective-timing.xdc')
 if r['status']=='FAIL_OR_BOUNDED_PROBE':
  assert r['exit_code']==139 and 'Abnormal program termination (11)' in (out/'tool.log').read_text();crash=out/'crash/hs_err_pid59.log';assert crash.is_file() and 'Segmentation fault' in crash.read_text() and 'HAPSRouteMgr::route' in crash.read_text()
  assert not any((out/'reports'/n).exists() for n in ('route-timing-summary.rpt','route-status.rpt'));assert not any(n.endswith('.dcp') for n in r['artifacts'])
  assert 'No valid timing exceptions found.' in (out/'parent-reports/route-exceptions.rpt').read_text()
  result=dict(status='PASS_FAILURE_PROVENANCE_AND_CRASH_RETENTION_AUDIT',actual_probe_outcome='FAIL_TOOL_SIGSEGV_NO_COMPLETED_TIMING_RESULT',raw_receipt_sha256=sha(out/'receipt.json'),parent_receipt_sha256=sha(out/'parent-receipt.json'),parent_DCP_sha256=r['checkpoint_sha256_before'],crash_sha256=sha(crash),parent_metrics=metrics(out/'parent-reports/route-timing-summary.rpt'),parent_route_status=legal(out/'reports/before-route-status.rpt'),exit_code=139,wall_seconds=r['wall_seconds'],host_stop_reason=r['stop_reason'],min_available_memory_bytes=min(x['available_bytes'] for x in r['memory_samples']),max_memory_PSI_full_avg10=max(x['psi_full_avg10'] for x in r['memory_samples']),source_files=18,physical_commands=r['physical_commands'],final_reports_absent=True,new_checkpoint_absent=True,parent_and_sources_unchanged=True,warnings=r['warnings'],scope='Failure evidence audit only. Intermediate in-memory timing is not a completed routed result. No retry, timing closure, fresh synthesis, reproducibility or hardware qualification.')
  write(out/'audit.json',result);write(out/'evidence-index.json',dict(retained_sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-index.json'},parent_DCP_sha256=r['checkpoint_sha256_before'],candidate_checkpoint_present=False));print(result['status'],result['actual_probe_outcome']);return
 assert r['exit_code']==0
 assert normalized(out/'reports/before-effective-timing.xdc')==normalized(out/'reports/effective-timing.xdc');assert 'No valid timing exceptions found.' in (out/'reports/route-exceptions.rpt').read_text()
 before=metrics(out/'parent-reports/route-timing-summary.rpt');after=metrics(out/'reports/route-timing-summary.rpt');assert before['WNS_ns']==-2.333
 after_route=legal(out/'reports/route-status.rpt');before_route=legal(out/'reports/before-route-status.rpt')
 paths=(out/'reports/route-setup-paths.rpt').read_text();worst={}
 for label,rx in [('slack_ns',r'Slack \([^)]*\)\s*:\s*([-+0-9.]+)ns'),('source',r'Source:\s*([^\n]+)'),('destination',r'Destination:\s*([^\n]+)'),('data_delay_ns',r'Data Path Delay:\s*([-+0-9.]+)ns'),('logic_delay_ns',r'\(logic\s+([-+0-9.]+)ns'),('route_delay_ns',r'route\s+([-+0-9.]+)ns'),('logic_levels',r'Logic Levels:\s*(\d+)')]:
  m=re.search(rx,paths);assert m,label;worst[label]=m.group(1).strip() if label in ('source','destination') else float(m.group(1))
 checks={n:int(v) for n,v in re.findall(r'checking ([a-z_]+) \((\d+)\)',(out/'reports/route-check-timing.rpt').read_text())}
 targets=dict(setup_pass=after['WNS_ns']>=0 and after['setup_failing_endpoints']==0,hold_pass=after['WHS_ns']>=0 and after['hold_failing_endpoints']==0,pulse_pass=after['WPWS_ns']>=0 and after['pulse_failing_endpoints']==0,legal_route=True,original_constraints_unchanged=True,source_and_parent_unchanged=True)
 result=dict(status='PASS_DIAGNOSTIC_PROVENANCE_REPORT_AUDIT',diagnostic_target_outcome='TIMING_TARGETS_PASS_WITH_SIGNOFF_GAPS' if all(targets.values()) else 'TIMING_TARGETS_FAIL',raw_receipt_sha256=sha(out/'receipt.json'),before=before,after=after,delta_WNS_ns=round(after['WNS_ns']-before['WNS_ns'],3),worst_setup_path=worst,checks=targets,check_timing=checks,DRC=rules(out/'reports/route-drc.rpt'),methodology=rules(out/'reports/route-methodology.rpt'),parent_route_status=before_route,diagnostic_route_status=after_route,warnings=r['warnings'],source_files=18,physical_commands=r['physical_commands'],scope='One post-route optimization diagnostic on runtime9 existing routed state. Provenance/report audit PASS is not timing closure, fresh synthesis, reproducibility, public contract change or board/hardware qualification.')
 write(out/'audit.json',result);write(out/'evidence-index.json',dict(retained_sha256={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='evidence-index.json'},external_checkpoints={n:a for n,a in r['artifacts'].items() if n.endswith('.dcp')},parent_DCP_sha256=r['checkpoint_sha256_before']));print(result['status'],result['diagnostic_target_outcome']);print(json.dumps({'before':before,'after':after,'worst':worst}))
if __name__=='__main__':main()
