#!/usr/bin/env python3
"""Verify retained quant source, strict actual-RTL results and attempt history."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/quant'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selected=json.loads((AREA/'results.json').read_text());path=ROOT/selected['selected_report'];r=json.loads(path.read_text());assert r['status']=='PASS' and r['actual_RTL_run']
 for n,h in r['artifacts_sha256'].items():assert sha(path.parent/n)==h,n
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert r['assertions_disabled_or_downgraded'] is False and r['strict_warnings']
 assert r['complete_production_body_preserved_by_adapters']
 assert all(c['exit_code']==0 for c in r['commands'])
 assert '%Warning-' not in (path.parent/'compile.log').read_text()
 assert len(r['runs'])==2
 edges=0
 for run in r['runs']:
  v=run['terminal_verdict'];assert v['status']=='TEST_PASS' and v['cases']==86 and v['directed_checks']==35 and v['prepared_edges']==348673
  assert run['trace_replay']['status']=='PASS'
  q=run['quant_replay'];assert q['status']=='PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE' and q['fill_edges']==103950 and q['run_edges']==2776 and q['rejected_run_edges']==1 and q['terminal_edges']==77
  assert v['scale_lookup_checks']>900000
  edges+=v['clock_edges']+v['prepared_edges']
 assert edges==19518735
 attempts=[]
 for p in sorted((AREA/'attempts').glob('*/results.json')):
  x=json.loads(p.read_text());attempts.append({'receipt':str(p.relative_to(ROOT)),'sha256':sha(p),'status':x['status'],'error_class':x.get('error_class'),'error':x.get('error')})
 assert len(attempts)==2 and [a['status'] for a in attempts]==['FAIL','PASS']
 out={'status':'PASS_QUANT_RETAINED_ARTIFACT_AUDIT','selected_receipt':str(path.relative_to(ROOT)),'selected_receipt_sha256':sha(path),'candidate':r['candidate'],'selected_actual_clock_edges':edges,'artifact_hashes_checked':len(r['artifacts_sha256']),'attempts':attempts,'attempt_note':'First actual RTL seed passed; packet oracle semantic replay matched but predeclared >100000 fill coverage floor was unmet (60750). Added32 complete mode2 stimulus packets; retained original floor/checkers/production RTL. Both new seeds pass.','limits':'Artifact/campaign/source audit; physical timing, parent integration, four-state, CDC and hardware qualification separate.'}
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
