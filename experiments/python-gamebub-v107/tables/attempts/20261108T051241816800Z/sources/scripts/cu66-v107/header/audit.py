#!/usr/bin/env python3
"""Audit immutable actual whole-admission staged-header qualification."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/header'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selection=json.loads((AREA/'results.json').read_text());receipt=ROOT/selection['selected_report'];r=json.loads(receipt.read_text());assert r['status']=='PASS' and r['actual_RTL_run']
 assert r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['complete_production_body_preserved_by_adapters']
 for n,h in r['artifacts_sha256'].items():assert sha(receipt.parent/n)==h,n
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert all(c['exit_code']==0 for c in r['commands']);assert '%Warning-' not in (receipt.parent/'compile.log').read_text()
 ports=json.loads((ROOT/'fpga/experiments/cu66-v107-header/ports.json').read_text());assert len(ports['production_ports'])==64 and sum(p['direction']=='output' for p in ports['production_ports'])==42
 total=0
 for run in r['runs']:
  v=run['terminal_verdict'];assert v['status']=='TEST_PASS' and v['cases']==86 and v['positive_cases']==52 and v['negative_cases']==34 and v['directed_checks']==44
  assert v['header_prepared_edges']==738933 and v['prepared_edges']==348673
  assert v['scale_lookup_checks']>980000
  assert run['trace_replay']['status']=='PASS' and run['quant_replay']['status']=='PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE'
  assert run['quant_replay']['fill_edges']==116100 and run['quant_replay']['run_edges']==3100
  total+=v['clock_edges']+v['header_prepared_edges']+v['prepared_edges']
 assert len(r['runs'])==2 and total==22631856
 model=json.loads((AREA/'model-results.json').read_text());assert model['status']=='PASS_EXACT_HEADER_SUM_FORWARDING_MODEL' and model['full32_tuple_checks']==299792 and model['maximum_exact_total']==17179869312
 attempts=list((AREA/'attempts').glob('*/results.json'));assert len(attempts)==1
 out={'status':'PASS_FROZEN_ACTUAL_HEADER_AUDIT','selected_receipt':str(receipt.relative_to(ROOT)),'selected_receipt_sha256':sha(receipt),'candidate':r['candidate'],'actual_clock_edges':total,'artifact_hashes_checked':len(r['artifacts_sha256']),'attempts':[{'receipt':str(p.relative_to(ROOT)),'status':json.loads(p.read_text())['status'],'sha256':sha(p)} for p in attempts],'scope':'Exact-cycle whole-admission RTL plus independent prepared/math/packet/scale oracles. Full parent canonical comparison/native timing/hardware remain separate.'}
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
