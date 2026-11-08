#!/usr/bin/env python3
"""Audit frozen actual coefficient-register unit proof and exact top recipe."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/elastic'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 s=json.loads((AREA/'results.json').read_text());receipt=ROOT/s['selected_receipt'];assert sha(receipt)==s['receipt_sha256']
 r=json.loads(receipt.read_text());assert s['status']==r['status']=='PASS_ACTUAL_ELASTIC_UNIT'
 assert not r['warning_suppression'] and not r['assertions_disabled_or_downgraded']
 for n,h in r['artifact_sha256'].items():assert sha(receipt.parent/n)==h,n
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert all(c['exit_code']==0 for c in r['commands'])
 assert '%Warning-' not in (receipt.parent/'compile.log').read_text()
 assert len(r['runs'])==3
 for v in r['runs']:
  assert v['status']=='TEST_PASS' and v['pushes']==v['pops']+v['discarded']
  assert v['discarded']==14 and v['flushes']==1269 and v['stalled_final_fences']>0
 assert r['actual_clock_edges']==508800
 recipe=json.loads((ROOT/'fpga/experiments/cu66-v107-elastic/edit-recipe.json').read_text());base=ROOT/recipe['baseline'];replacement=ROOT/recipe['replacement']
 assert sha(base)==recipe['baseline_sha256'] and sha(replacement)==recipe['replacement_sha256']
 a=base.read_text();b=replacement.read_text();assert a.split(');',1)[0]==b.split(');',1)[0]
 for e in reversed(recipe['changes']):
  assert a[e['start']:e['end']]==e['old'];a=a[:e['start']]+e['new']+a[e['end']:]
 assert a==b
 for p in recipe['additional_sources']:assert sha(ROOT/p['path'])==p['sha256']
 out={'status':'PASS_FROZEN_ELASTIC_UNIT_AUDIT','receipt':str(receipt.relative_to(ROOT)),'receipt_sha256':sha(receipt),'actual_clock_edges':r['actual_clock_edges'],'stage':r['stage'],'canonical_top':r['top'],'artifact_hashes_checked':len(r['artifact_sha256']),'warning_suppression':False,'complete_pipeline_compile_or_simulation':False,'scope':'Independent actual stage token/fence simulation plus source/recipe audit; parent pipeline integration and physical timing remain separate.'}
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
