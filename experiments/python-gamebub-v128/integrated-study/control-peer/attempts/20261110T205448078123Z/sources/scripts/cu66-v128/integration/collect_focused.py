#!/usr/bin/env python3
"""Compose actual separate raw/padding focused receipts; no simulator runs."""
import argparse,datetime,json,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
from contract import ROOT,AREA,load,sha,pin,verify,composition,legacy

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--collect',action='store_true');a=ap.parse_args();verify();c=composition()
 selected={};sources={};artifacts={};commands=[]
 for role,name in [('raw_validation','raw'),('header_padding','padding')]:
  sp=AREA/name/'results.json';s=load(sp);rp=ROOT/s.get('path',s.get('selected_report',''));r=load(rp)
  assert s['status']==r['status']=='PASS'and s['actual_RTL_run']is True and r['actual_RTL_run']is True
  assert sha(rp)==s.get('sha256',s.get('selected_report_sha256'))
  legacy().verify_closure(rp,r,role)
  for alias in c['proof_roles'][role]:assert r['source_sha256'][c['source_origins'][alias]['path']]==c['source_origins'][alias]['sha256']
  selected[role]=dict(selector=pin(sp),receipt=pin(rp))
  for p,h in r['source_sha256'].items():assert p not in sources or sources[p]==h;sources[p]=h
  commands.extend(r['commands'])
 if not a.collect:print('V128_FOCUSED_AGGREGATE_PREPARED_NOT_COLLECTED');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'focused/attempts'/stamp;out.mkdir(parents=True)
 for meta in selected.values():
  rp=ROOT/meta['receipt']['path'];r=load(rp)
  artifacts[os.path.relpath(rp,out)]=sha(rp)
  for p,h in r.get('artifact_sha256',r.get('artifacts_sha256',{})).items():
   target=rp.parent/p;relative=os.path.relpath(target,out);assert relative not in artifacts or artifacts[relative]==h;artifacts[relative]=h
 for p in [Path(__file__).resolve(),ROOT/'scripts/cu66-v128/integration/contract.py',ROOT/'fpga/experiments/cu66-v128-raw/selected-composition.json']:
  sources[str(p.relative_to(ROOT))]=sha(p)
 report=dict(schema='v128-separated-raw-padding-focused-aggregate-v1',status='PASS',actual_RTL_run=True,source_sha256=sources,artifact_sha256=artifacts,commands=commands,source_origins=c['complete_source_origins'],focused_components=selected,proof_roles=c['proof_roles'],strict_warnings=True,assertions_disabled_or_downgraded=False,all_original_oracles_retained=True,declared_public_cycle_delta=0,aggregate_is_single_whole_composition_binary=False,scope='Actual separate paired-scratch/extracted-algebra and source-bound padding-kernel executions. Allfive source bindings explicit; full five-origin simultaneous execution is a later decoder/transport/peer/parent gate.')
 rp=out/'receipt.json';rp.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');selector=AREA/'focused/results.json';selector.write_text(json.dumps(dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp),status='PASS',actual_RTL_run=True),indent=2,sort_keys=True)+'\n')
 print('PASS_FOCUSED_RAW_PADDING_AGGREGATE',str(rp.relative_to(ROOT)),sha(rp))
if __name__=='__main__':main()
