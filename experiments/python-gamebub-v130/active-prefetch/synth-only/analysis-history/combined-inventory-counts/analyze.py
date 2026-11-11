#!/usr/bin/env python3
"""Compare completed synthesis reports to V130, explicitly not routed timing."""
import argparse,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json';PARSER=ROOT/'scripts/cu66-v128/audit_terminal.py';AREA=ROOT/'experiments/python-gamebub-v130/active-prefetch/synth-only'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def need(x,msg):
 if not x:raise ValueError(msg)
def capacity(path):
 text=path.read_text();out={}
 for name in ('Slice LUTs*','Slice Registers','Block RAM Tile','DSPs'):
  match=re.search(r'^\|\s*'+re.escape(name)+r'\s*\|\s*([\d.]+)\s*\|',text,re.M);need(match is not None,'resource missing '+name);out[name]=float(match.group(1))
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();path=a.receipt.resolve();r=load(path);old=load(BASE);root=path.parent;baseline=BASE.parent
 need(r['status']=='SYNTH_COMPLETE_EXPLORATORY' and r['actual_synth_complete'] and r['route_run'] is False and r['physical_timing_qualified'] is False,'not completed synth-only result')
 need(r['source_snapshot_unchanged'] and r['recipe_unchanged'] and r['observed_exit_code']==0 and r['monitor_stop_reason'] is None and r['clock_period_ns']==8.0,'identity/clock')
 need(r['source_contract']['baseline_component']['sha256']==sha(BASE) and old['clock_period_ns']==8.0,'V130 baseline mismatch')
 for name,h in r['retained_artifact_sha256'].items():need(sha(root/name)==h,'candidate artifact '+name)
 for name,h in old['retained_artifact_sha256'].items():need(sha(baseline/name)==h,'baseline artifact '+name)
 spec=importlib.util.spec_from_file_location('v128_retained_parser',PARSER);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def reports(dir):
  d=dir/'reports';return {'timing':m.timing((d/'synth-timing-summary.rpt').read_text()),'worst_setup':m.worst_setup((d/'synth-setup-paths.rpt').read_text()),'check_timing':m.check_timing((d/'synth-check-timing.rpt').read_text()),'resources':capacity(d/'synth-capacity.rpt')}
 new,prior=reports(root),reports(baseline);inv=(root/'reports/active-cell-inventory.tsv').read_text().splitlines();need(inv and inv[0]=='kind\tinstance\tprimitive','mapping inventory absent');cells=[line.split('\t') for line in inv[1:] if line.strip()];need(all(len(row)==3 for row in cells),'invalid inventory')
 selected=[{'kind':x[0],'instance':x[1],'primitive':x[2]} for x in cells];types={}
 for x in selected:types[x['primitive']]=types.get(x['primitive'],0)+1
 memory_primitives=[x for x in selected if x['primitive'].startswith(('RAMB','RAM32','RAM64','RAM128','RAM256'))]
 result={'schema':'v130-active-synth-analysis-v1','status':'SYNTHESIS_REPORTS_COMPARED_NOT_TIMING_QUALIFIED','candidate_receipt':{'path':str(path.relative_to(ROOT)),'sha256':sha(path)},'baseline_receipt':{'path':str(BASE.relative_to(ROOT)),'sha256':sha(BASE)},'parser_sha256':sha(PARSER),'candidate':new,'v130_baseline':prior,'wns_delta_ns':round(new['timing']['WNS_ns']-prior['timing']['WNS_ns'],3),'resource_delta':{k:new['resources'][k]-prior['resources'][k] for k in prior['resources']},'active_mapping_inventory':selected,'active_mapping_primitive_counts':types,'named_memory_primitives':memory_primitives,'mapping_interpretation':'Only explicitly named inventory cells and observed register-D startpoints are reported; no named primitive is not proof of no memory inference.','scope':'OOC synthesised netlist estimated delays; no placement, route, complete-parent qualification, FPGA silicon, 30 fps or <10ms claim.','route_run':False,'physical_timing_qualified':False}
 out=AREA/'analysis.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('SYNTH_REPORT_ANALYSIS',new['timing']['WNS_ns'],'vs',prior['timing']['WNS_ns'],'named_memory_primitives',len(memory_primitives),'receipt',sha(out))
if __name__=='__main__':main()
