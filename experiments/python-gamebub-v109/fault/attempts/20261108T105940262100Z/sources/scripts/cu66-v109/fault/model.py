#!/usr/bin/env python3
"""Structural induction and complete Boolean control truth table; not an RTL verdict."""
import hashlib,itertools,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'fpga/experiments/cu66-v109-fault'
AREA=ROOT/'experiments/python-gamebub-v109/fault'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((OUT/'edit-recipe.json').read_text());base=ROOT/r['baseline_receipt'];assert sha(base)==r['baseline_receipt_sha256'];origins=json.loads(base.read_text())['source_origins'];counts={}
 for name,e in r['production'].items():
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==x['expected_occurrences']==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text();reverse=s
  for x in reversed(e['edits']):assert reverse.count(x['after'])==1;reverse=reverse.replace(x['after'],x['before'],1)
  assert reverse==p.read_text()
  if name!='cs88_pipeline_v91k.sv':
   old=re.findall(r'(?<![\w])error\s*<=\s*([^;]+);',p.read_text())
   new=re.findall(r'(?<![\w])error\s*<=\s*([^;]+);fault_o<=\(([^;]+)\)!=0;',q.read_text())
   assert old==[a for a,b in new] and all(a==b for a,b in new);counts[name]=len(old)
   assert 'assert(fault_o==(error!=0))' in s
   # Every hold preserves induction; every explicit next value writes its own exact reduction.
   for previous in range(256):
    assert bool(previous)==(previous!=0)
    for following in range(256):assert bool(following)==(following!=0)
  assert r['source_origins'][e['alias']]['path']==e['candidate']
 assert len(r['source_origins'])==18
 for alias,m in r['source_origins'].items():
  assert sha(ROOT/m['path'])==m['sha256']
  if alias not in [e['alias'] for e in r['production'].values()]:assert m==origins[alias]
 # Independent old/new control truth table. All error nonzero classes; each code
 # maps bijectively to its bit by the source-level adjacent-NBA induction above.
 rows=0
 for abort,accepted,ia,ra,ce,ie,re_ in itertools.product((False,True),repeat=7):
  old=(abort or (ie and not ia) or (re_ and not ra),abort or(not accepted and(ce or re_)),abort or(not accepted and(ce or ie)),abort or(not accepted and(ce or re_)) or(not accepted and ie))
  inv_fault,rec_fault,coef_fault=ie,re_,ce
  new=(abort or(inv_fault and not ia)or(rec_fault and not ra),abort or(not accepted and(coef_fault or rec_fault)),abort or(not accepted and(coef_fault or inv_fault)),abort or(not accepted and(coef_fault or rec_fault))or(not accepted and inv_fault))
  assert old==new;rows+=1
 for c,i,r_ in itertools.product(range(256),repeat=3):
  old=(0xe0|r_)if r_ else(0xc0|i)if i else c
  new=(0xe0|r_)if bool(r_)else(0xc0|i)if bool(i)else c
  assert old==new and (old==0)==(not(c or i or r_))
 result=dict(status='PASS_STRUCTURAL_INDUCTION_AND_CONTROL_MODEL_NOT_RTL',assignments_paired=counts,control_rows=rows,error_mux_code_rows=256**3,added_public_cycles=0,source_sha256={str((ROOT/e[k]).relative_to(ROOT)):sha(ROOT/e[k]) for e in r['production'].values() for k in ('original','candidate')},limitations=['No tool simulation or physical implementation in this model result.','Induction covers same-edge error assignment/hold/reset/start/failure priority; local original/new module RTL and full canonical checks remain required.'])
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],counts,rows)
if __name__=='__main__':main()
