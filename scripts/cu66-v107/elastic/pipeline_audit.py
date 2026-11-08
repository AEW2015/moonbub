#!/usr/bin/env python3
"""Audit full canonical elastic qualification without assuming cycle equality."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/elastic-pipeline'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 selected=json.loads((AREA/'results.json').read_text());receipt=ROOT/selected['selected_report'];r=json.loads(receipt.read_text())
 assert r['status']=='PASS' and r['actual_RTL_run'] and not r['exact_same_seed_transcripts_events_cycles']
 assert r['exact_same_seed_canonical_bytes'] and r['ordered_good_frame_semantic_streams_equal']
 for n,h in r['artifacts_sha256'].items():assert sha(receipt.parent/n)==h,n
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert r['compile_source_counts']=={'baseline':{'rtl':16,'include_headers':1,'closure_files':17},'candidate':{'rtl':17,'include_headers':1,'closure_files':18}}
 assert all(c['exit_code']==0 for c in r['commands'])
 assert len(r['runs'])==2
 totals={'baseline_edges':0,'candidate_edges':0,'candidate_up':0,'candidate_down':0,'candidate_discard':0,'good_case_profiles':0,'bad_case_profiles':0}
 for run in r['runs']:
  assert run['equalities']['canonical'] and run['semantic_streams']['status']=='PASS_ORDERED_SEMANTIC_STREAMS'
  for name in ['baseline','candidate']:
   v=run['variants'][name]['verdict'];assert v['status']=='TEST_PASS' and v['cases']==22 and v['directed_checks']==21
   totals[name+'_edges']+=v['clock_edges']
   if name=='candidate':
    assert v['elastic_total_up']==v['elastic_total_down']+v['elastic_total_discard']
    assert v['elastic_fence_checks']>0 and v['elastic_hold_checks']>0
    totals['candidate_up']+=v['elastic_total_up'];totals['candidate_down']+=v['elastic_total_down'];totals['candidate_discard']+=v['elastic_total_discard']
  for c in run['case_latency']:
   e=c['elastic'];assert e['accepted']==e['delivered']+e['discarded'] and e['final_occupied']==0
   if c['error']==0:assert e['discarded']==0;totals['good_case_profiles']+=1
   else:totals['bad_case_profiles']+=1
 for name in ['baseline','candidate']:assert '%Warning-' not in (receipt.parent/f'compile-{name}.log').read_text()
 attempts=[]
 for p in sorted((AREA/'attempts').glob('*/results.json')):
  x=json.loads(p.read_text());attempts.append({'receipt':str(p.relative_to(ROOT)),'sha256':sha(p),'status':x['status'],'error':x.get('error')})
 out={'status':'PASS_ACTUAL_ELASTIC_CANONICAL_AUDIT','selected_receipt':str(receipt.relative_to(ROOT)),'selected_receipt_sha256':sha(receipt),'artifacts_checked':len(r['artifacts_sha256']),'totals':totals,'attempts':attempts,'limits':'Complete retained canonical golden/ownership/error/semantic checks; no cycle equality, routed timing, HUD/C2 publication, CDC or hardware proof.'}
 (AREA/'audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
