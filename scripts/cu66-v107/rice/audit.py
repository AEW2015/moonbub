#!/usr/bin/env python3
"""Check frozen actual-RTL artifacts and reproduce the exact source edits."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/rice'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selection=json.loads((AREA/'probe-results.json').read_text());receipt=ROOT/selection['selected_receipt'];assert sha(receipt)==selection['sha256']
 r=json.loads(receipt.read_text());assert r['status']==selection['status']=='PASS_ACTUAL_RICE_FIXED_TAP_EQUIVALENCE'
 for name,digest in r['artifacts_sha256'].items():assert sha(receipt.parent/name)==digest,name
 for source,digest in r['source_sha256'].items():assert sha(ROOT/source)==digest,source
 recipe=json.loads((receipt.parent/'edit-recipe.json').read_text())
 a=(receipt.parent/'rice_original.sv').read_text().replace('module rice_original (','module br88_rice_elastic (',1)
 b=(receipt.parent/'rice_candidate.sv').read_text().replace('module rice_candidate (','module br88_rice_elastic (',1)
 assert hashlib.sha256(a.encode()).hexdigest()==recipe['baseline_sha256']
 assert hashlib.sha256(b.encode()).hexdigest()==recipe['candidate_sha256']
 for edit in reversed(recipe['changes']):
  assert a[edit['start']:edit['end']]==edit['old'];a=a[:edit['start']]+edit['new']+a[edit['end']:]
 assert a==b
 for command in r['commands']:assert command['exit_code']==0
 assert r['output_names']==13 and r['port_names']==27
 assert len(r['runs'])==2
 for run in r['runs']:
  assert run['status']=='TEST_PASS' and run['parameter_cases']==6096 and run['prepared_clocks']==189105
  assert run['historical_verdict']['cases']==1520 and run['historical_verdict']['configurations']==8 and run['historical_verdict']['directed_checks']==104
  rows=[json.loads(x) for x in (receipt.parent/f"seed-{run['seed']}.log").read_text().splitlines()]
  assert rows[-1]['status']=='TEST_PASS'
  assert rows[-2]==run['historical_verdict']
 assert not any('warning:' in l.lower() or '%warning' in l.lower() or 'TEST_FAIL' in l for l in (receipt.parent/'compile.log').read_text().splitlines())
 assert r['total_clock_edges']==17839670
 out={'status':'PASS_FROZEN_ACTUAL_RTL_AUDIT','receipt':str(receipt.relative_to(ROOT)),'receipt_sha256':sha(receipt),'candidate_sha256':recipe['candidate_sha256'],'total_clock_edges':r['total_clock_edges'],'artifact_hashes_checked':len(r['artifacts_sha256']),'assertion_policy':'--assert enabled; no candidate assertion or functional warning suppression','scope':'Artifact/source/campaign audit, not timing, CDC, formal or hardware signoff.'}
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
