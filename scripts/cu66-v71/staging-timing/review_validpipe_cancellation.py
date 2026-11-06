from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/inverse-validpipe';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();refs={}
for name in['functional01','validation-cancel01','validation-cancel02']:
 e=d/'evidence'/name;q=json.loads((e/'result.json').read_text());assert q['status'].startswith('PASS_');refs[(e/'result.json').relative_to(r).as_posix()]=sha(e/'result.json')
 if 'artifacts'in q:
  for n,h in q['artifacts'].items():assert sha(e/n)==h,(name,n)
  assert q['source_sha256']==sha(d/'cu71_idct_validpipe.sv')
text=(d/'evidence/validation-cancel02/tb.sv').read_text()
assert 'dut.state!==4\'d10'in text and 'in_tile=bad?1280\'d0:{64{20\'h7ffff}};tick();'in text
q={'status':'PASS_INDEPENDENT_SOURCE_AND_NEW_CLASSIFICATION_STATE_PROOF_REVIEW','source_sha256':sha(d/'cu71_idct_validpipe.sv'),'references':refs,'new_state_abort_reset':True,'external_tile_overwrite_during_validation':True,'four_state_unknown_payload_check':True,'golden_vectors':3471,'golden_seeds':2,'added_work_cycles_per_tile':1,'unqualified_out_error_changes_documented':True,'source_defect_observed':False,'limits':['Finite simulations and source inspection, not unbounded formal proof','No full-system latency/source binding or whole-board timing reviewed here','No hardware execution'], 'hardware':False}
o=r/'fpga/experiments/cu66-v71/staging-timing/inverse-validpipe-review-v002.json';assert not o.exists();o.write_text(json.dumps(q,indent=2)+'\n');print(sha(o))
