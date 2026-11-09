#!/usr/bin/env python3
"""Emit one immutable source-pinned refined live driver after actual main PASS."""
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[2]
OLD=R/'scripts/cu66-v115/live-parent/qualify.py'
OLD_SHA='a1924428efc3efb62038ef36b90d499b7038974522b5710858ba9a38b3908452'
SELECT=R/'experiments/python-gamebub-v115/refined/spatial/results.json'
TARGET=R/'scripts/cu66-v115/live_refined.py'
AREA=R/'experiments/python-gamebub-v115/refined/live-parent'
FROZEN={
 'fpga/experiments/cu66-v115-live-parent/cs88_live_v91l.sv':'9f1144799e320061520611633f4829435d9e75c067f3cdd4becd7ff3c9fa36f9',
 'fpga/experiments/cu66-v115-live-parent/tb_keyframe.cpp':'5d99cdf28fd9f5cb1a85cabed43e27bb8a92f50672755d44fd195da7e3216f44',
 'fpga/experiments/cu66-v115-live-parent/derivation.json':'c9e6f3b85e891157bfdbdefb132bfe7eb9bc933f3bfac6b8b2db00b06e03db63'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def load(p):return json.loads(p.read_text())
def create_or_match(path,data):
 if path.exists():
  if path.read_bytes()!=data:raise RuntimeError('Refuse to overwrite previously emitted different bytes: '+rel(path))
 else:
  path.parent.mkdir(parents=True,exist_ok=True)
  with path.open('xb')as stream:stream.write(data)

def main():
 if not SELECT.exists():
  print('PREREQUISITES_NOT_READY: refined selected main absent; no driver emitted.');return
 q=load(SELECT)
 if q.get('status')!='PASS_V115_REFINED_SPATIAL_CANONICAL':raise RuntimeError('Refined selected main is not PASS: '+str(q.get('status')))
 assert q['actual_RTL_run']and not q['candidate_model_reused']and not q['canonical_reused_actual_RTL']
 raw=R/q['selected_receipt'];assert load(raw)=={k:v for k,v in q.items()if k!='selected_receipt'}
 assert q['seeds']==[107601,107602]and len(q['runs'])==len(q['transport_runs'])==2
 assert sum(r['verdict']['cases']for r in q['runs'])==44 and sum(r['verdict']['directed_checks']for r in q['runs'])==42
 assert sum(r['verdict']['successful_case_profiles']for r in q['transport_runs'])==24
 for run in q['runs']+q['transport_runs']:assert run['verdict']['status']=='TEST_PASS'and run['canonical_exact']
 assert len(q['source_origins'])==18
 for origin in q['source_origins'].values():assert sha(R/origin['path'])==q['source_sha256'][origin['path']]==origin['sha256']
 def header(p):s=p.read_text();return s[s.index('(')+1:s.index(');')]
 top=R/q['source_origins']['fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv']['path']
 assert header(top)==header(R/'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv')
 assert sha(OLD)==OLD_SHA
 for name,want in FROZEN.items():assert sha(R/name)==want
 text=OLD.read_text();edits=[]
 def edit(before,after):
  nonlocal text
  assert text.count(before)==1,(before,text.count(before));text=text.replace(before,after,1);edits.append(dict(before=before,after=after))
 edit('R=Path(__file__).resolve().parents[3]','R=Path(__file__).resolve().parents[2]')
 edit("A=R/'experiments/python-gamebub-v115/live-parent'","A=R/'experiments/python-gamebub-v115/refined/live-parent'")
 edit("SELECT=R/'experiments/python-gamebub-v115/spatial/results.json'","SELECT=R/'experiments/python-gamebub-v115/refined/spatial/results.json'")
 edit("SELECT_SHA='52697a476f23ec0c44c17fc80026daeb63755d5481f2c360c8af9b4f557fc907'",f"SELECT_SHA='{sha(SELECT)}'")
 edit("RAW_SHA='fb381cd142dfb9c4712bf8dacb280b45555859591af264bde244fa8f4ccff573'",f"RAW_SHA='{sha(raw)}'")
 edit("q['status']=='PASS_V115_SPATIAL_CANONICAL'","q['status']=='PASS_V115_REFINED_SPATIAL_CANONICAL'")
 # The unchanged bench recipe honestly retains its initial V115/API reference;
 # this driver's chosen producer is independently pinned to refined origins.
 before="source_derivation=dict(path=rel(S/'derivation.json'),sha256=sha(S/'derivation.json')),contract=derivation['contract']"
 after="source_derivation=dict(path=rel(S/'derivation.json'),sha256=sha(S/'derivation.json')),bench_derivation_reference=derivation['selected_spatial'],bench_derivation_reference_is_actual_producer_selection=False,actual_producer_variant='refined-owned-header-and-tile-write',contract=derivation['contract']"
 edit(before,after)
 before="return q,d"
 after="""prepared=load(A/'preparation.json')
 for pin in [prepared['source_emitter'],prepared['old_driver'],prepared['new_driver']]:assert sha(R/pin['path'])==pin['sha256']
 assert prepared['qualification']['sha256']==SELECT_SHA and prepared['qualification']['receipt_sha256']==RAW_SHA
 return q,d"""
 edit(before,after)
 edit("files=sorted(set(sources+endpoints+inputs+support+", "files=sorted(set(sources+endpoints+inputs+support+[R/'scripts/cu66-v115/prepare_live_refined.py',R/'scripts/cu66-v115/live-parent/qualify.py',A/'preparation.json']+")
 back=text
 for e in reversed(edits):assert back.count(e['after'])==1;back=back.replace(e['after'],e['before'],1)
 assert back==OLD.read_text()
 compile(text,str(TARGET),'exec')
 manifest=dict(schema='v115-refined-live-driver-reversible-source-emission-v1',status='PREPARED_NOT_RUN',actual_RTL_run=False,
  source_emitter=dict(path=rel(Path(__file__).resolve()),sha256=sha(Path(__file__))),old_driver=dict(path=rel(OLD),sha256=OLD_SHA),
  new_driver=dict(path=rel(TARGET),sha256=hashlib.sha256(text.encode()).hexdigest()),
  qualification=dict(path=rel(SELECT),sha256=sha(SELECT),receipt=rel(raw),receipt_sha256=sha(raw)),actual_producer_source_origins=q['source_origins'],
  unchanged_live_sources=FROZEN,bench_derivation_initial_reference=load(R/'fpga/experiments/cu66-v115-live-parent/derivation.json')['selected_spatial'],
  producer_header_equal_original=True,producer_header_reference=dict(path='fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv',sha256=sha(R/'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv'),header_sha256=hashlib.sha256(header(top).encode()).hexdigest()),edits=edits,reverse_verified=True,strict_checks_and_watchdogs_retained=True,
  scope='Same ACK/C2/HUD/seal/publication partition and negative ownership checks, selected refined18producer bodies; actual C++ HUD semantic decode, abstract memory, no hardware or achieved-clock claim.')
 # Validate both destinations before creating either one; never rewrite a prior
 # driver or source/selection map after its original generation.
 data=text.encode();prepared=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode();dest=AREA/'preparation.json'
 for path,blob in ((TARGET,data),(dest,prepared)):
  if path.exists()and path.read_bytes()!=blob:raise RuntimeError('Refuse changed existing emitted artifact: '+rel(path))
 create_or_match(TARGET,data);create_or_match(dest,prepared)
 print('REFINED_LIVE_PREPARED_NOT_RUN',manifest['new_driver']['sha256'],rel(dest))
if __name__=='__main__':main()
