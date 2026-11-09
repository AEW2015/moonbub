#!/usr/bin/env python3
"""Prepare the exact qualified RTL alias tree without running any tools."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mapped-path',type=Path);a=ap.parse_args()
 source=ROOT/'experiments/python-gamebub-v118/handoff.json';m=json.loads(source.read_text())
 receipts=[]
 for key in ('initial_receipt','repeat_receipt'):
  p=ROOT/m[key]['path'];assert sha(p)==m[key]['sha256'];r=json.loads(p.read_text());assert r['result']['component_internal_target_pass'] and r['clock_period_ns']==10.0 and r['synthesis_executed'] and r['source_snapshot_unchanged'] and r['recipe_unchanged'];receipts.append(r)
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
  p=ROOT/'fpga/experiments/cu66-v118-flow'/n;assert sha(p)==m['recipe_sha256'][n];shutil.copyfile(p,out/n)
 clock=ROOT/'fpga/experiments/cu66-v118-flow/clock-100.xdc';assert sha(clock)==m['recipe_sha256']['component.xdc'];shutil.copyfile(clock,out/'component.xdc')
 word=lambda x:'{'+str(x)+'}'
 order=m['source_order'];lines=['set part xc7a100tcsg324-1','set trial_id {prepared-handoff-100}','set start_mode {rtl}','set expected_period_ns 10.0','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n)for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/n)for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
 (out/'inputs.tcl').write_text('\n'.join(lines)+'\n');shutil.copyfile(source,out/'handoff-manifest.json')
 report=dict(status='PREPARED_NOT_RUN',builder_sha256=sha(Path(__file__)),manifest_sha256=sha(source),output=str(out),mapped_path=str(mapped),source_count=len(m['source_origins']),hardware_contact=False,tool_invoked=False,physical_trial_consumed=False,scope='Exact selected100MHz OOC source preparation. Any new run is a separately budgeted campaign; board integration requires actual board constraints.',files={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()})
 (out/'preparation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('PREPARED_NOT_RUN',out)
if __name__=='__main__':main()
