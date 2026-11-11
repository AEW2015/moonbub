#!/usr/bin/env python3
"""Bind separately executed V128 inheritance and two focused V129 RTL tests."""
import argparse,datetime,json,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
from contract import ROOT,AREA,load,sha,pin,verify,composition,legacy

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collect',action='store_true');a=ap.parse_args();verify();c=composition()
 selectors={'inherited_v128':ROOT/'experiments/python-gamebub-v128/focused/results.json','parser':AREA/'parser/results.json','scratch':AREA/'scratch-factor/results.json'}
 selected={};sources={};commands=[]
 for name,sp in selectors.items():
  s=load(sp);rp=ROOT/s.get('path',s.get('selected_report',''));r=load(rp)
  assert s['status']==r['status']=='PASS' and s['actual_RTL_run'] is r['actual_RTL_run'] is True and sha(rp)==s.get('sha256',s.get('selected_report_sha256'))
  legacy().verify_closure(rp,r,name);assert r.get('assertions_disabled_or_downgraded',False) is False
  if name!='inherited_v128':
   assert r['declared_public_cycle_delta']==0 and r['compiled_input_snapshots_unchanged'] is True
   alias='fpga/experiments/cu66-v91/br88_rice_elastic.sv' if name=='parser' else 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv';m=c['source_origins'][alias];assert r['source_sha256'][m['path']]==m['sha256']
  selected[name]=dict(selector=pin(sp),receipt=pin(rp))
  for path,h in r['source_sha256'].items():assert path not in sources or sources[path]==h;sources[path]=h
  commands.extend(r['commands'])
 if not a.collect:print('V129_FOCUSED_PREPARED_NOT_COLLECTED');return
 out=AREA/'focused/attempts'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
 artifacts={}
 for meta in selected.values():
  rp=ROOT/meta['receipt']['path'];r=load(rp);artifacts[os.path.relpath(rp,out)]=sha(rp)
  for p,h in r.get('artifact_sha256',r.get('artifacts_sha256',{})).items():
   k=os.path.relpath(rp.parent/p,out);assert k not in artifacts or artifacts[k]==h;artifacts[k]=h
 for p in [Path(__file__).resolve(),Path(__file__).with_name('contract.py')]:sources[str(p.relative_to(ROOT))]=sha(p)
 report=dict(schema='v129-focused-aggregate-v1',status='PASS',actual_RTL_run=True,source_sha256=sources,artifact_sha256=artifacts,commands=commands,source_origins=c['complete_source_origins'],focused_components=selected,strict_warnings=True,assertions_disabled_or_downgraded=False,all_original_oracles_retained=True,declared_public_cycle_delta=0,aggregate_is_single_whole_composition_binary=False,scope='Separate inherited V128 and V129 parser and scratch RTL tests; no whole-composition or timing claim.')
 rp=out/'receipt.json';rp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');(AREA/'focused/results.json').write_text(json.dumps(dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp),status='PASS',actual_RTL_run=True),indent=2,sort_keys=True)+'\n');print('PASS_V129_FOCUSED_AGGREGATE',rp)
if __name__=='__main__':main()
