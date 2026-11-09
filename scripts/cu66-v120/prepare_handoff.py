#!/usr/bin/env python3
"""Prepare the exact qualified RTL alias tree without running any tools."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mapped-path',type=Path);a=ap.parse_args()
 source=ROOT/'experiments/python-gamebub-v120/handoff.json';m=json.loads(source.read_text())
 assert m['part']=='xc7a100tcsg324-1' and m['top']=='cs88_pipeline_v91k','Manifest part/top differs from measured component'
 assert m['period_ns'] in (8.0,10.0),'Only the measured 8 ns and 10 ns clocks are supported'
 assert m['qualified_internal_component_clock_MHz']==1000/m['period_ns'],'Manifest clock identity differs'
 assert m.get('parameter_overrides',[])==[],'Only the measured default parameters are supported'
 assert m['initial_receipt']['path'] != m['repeat_receipt']['path'],'Fresh repeat must have a distinct receipt'
 receipts=[]
 for key in ('initial_receipt','repeat_receipt'):
  p=ROOT/m[key]['path'];assert sha(p)==m[key]['sha256'];r=json.loads(p.read_text());assert r['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and r['start_mode']=='rtl' and r['observed_exit_code']==0
  assert r['part']==m['part'] and r['top']==m['top'],'Receipt part/top differs from manifest'
  assert all(r.get(k) is True for k in ('component_route_finished','synthesis_executed','clock_loaded_before_synthesis_in_this_run','observed_default_command_exact','source_snapshot_unchanged','recipe_unchanged'))
  assert r['result']['component_internal_target_pass'] and r['clock_period_ns']==m['period_ns'];receipts.append(r)
 assert receipts[0]['clean_repeat_of'] is None and receipts[1]['clean_repeat_of']==m['initial_receipt']
 assert receipts[0]['build_external']!=receipts[1]['build_external'] and receipts[0]['container']!=receipts[1]['container'],'Repeat must identify a distinct fresh build'
 assert receipts[0]['image_id']==receipts[1]['image_id'] and receipts[0]['tooling_sha256']==receipts[1]['tooling_sha256']
 assert all(receipts[0]['recipe_sha256'][n]==receipts[1]['recipe_sha256'][n]==m['recipe_sha256'][n] for n in ('run.tcl','report.tcl','component.xdc'))
 assert receipts[0]['source_contract']==receipts[1]['source_contract']
 assert m['source_origins']==receipts[1]['source_contract']['source_origins']
 assert m['source_order']==receipts[1]['source_contract']['source_order']
 for alias,meta in m['source_origins'].items():
  q=Path(alias);assert not q.is_absolute() and '..'not in q.parts
  p=ROOT/meta['path'];assert p.is_file() and sha(p)==meta['sha256']
 out=a.output.resolve();assert not out.exists(),'Refusing to overwrite an existing directory'
 mapped=(a.mapped_path or out);assert mapped.is_absolute() and not any(c in str(mapped)for c in '{}\r\n')
 out.mkdir(parents=True)
 for alias,meta in m['source_origins'].items():
  p=out/'snapshot'/alias;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/meta['path'],p)
 for n in ('run.tcl','report.tcl'):
  p=ROOT/'fpga/experiments/cu66-v120-flow'/n;assert sha(p)==m['recipe_sha256'][n];shutil.copyfile(p,out/n)
 clock=ROOT/'fpga/experiments/cu66-v120-flow'/('clock-125.xdc' if m['period_ns']==8.0 else 'clock-100.xdc');assert sha(clock)==m['recipe_sha256']['component.xdc'];shutil.copyfile(clock,out/'component.xdc')
 word=lambda x:'{'+str(x)+'}'
 order=m['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id {prepared-handoff}','set start_mode {rtl}','set expected_period_ns '+str(m['period_ns']),'set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n)for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n)for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
 (out/'inputs.tcl').write_text('\n'.join(lines)+'\n');shutil.copyfile(source,out/'handoff-manifest.json')
 report=dict(status='PREPARED_NOT_RUN',builder_sha256=sha(Path(__file__)),manifest_sha256=sha(source),output=str(out),mapped_path=str(mapped),source_count=len(m['source_origins']),hardware_contact=False,tool_invoked=False,physical_trial_consumed=False,scope='Exact selected OOC source preparation at the manifest clock. Any new run is a separately budgeted campaign; board integration requires actual board constraints.',files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()})
 (out/'preparation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('PREPARED_NOT_RUN',out)
if __name__=='__main__':main()
