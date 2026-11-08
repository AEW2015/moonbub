#!/usr/bin/env python3
"""Exhaustive next-state algebra and reversible source audit, separate from RTL."""
import hashlib,itertools,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'fpga/experiments/cu66-v110-fault';AREA=ROOT/'experiments/python-gamebub-v110/fault'
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
   old=re.findall(r'(?<![\w])fault_o\s*<=\s*([^;]+);',p.read_text());new=re.findall(r'(?<![\w])fault_o\s*<=\s*([^;]+);',q.read_text());assert old==new==['(reason)!=0','(0)!=0'];counts[name]=len(old)
   assert s.count('fault_pending_o<=0;')==1
   assert s.count('fault_pending_o<=(reason)!=0&&!fault_ack_i&&!fault_o;')==1
   assert s.index('fault_pending_o<=0;')<s.index('if(reset||start||cancel)begin' if name.startswith('cu66_inverse') else 'if(reset||cancel||start)begin')
   assert len(re.findall(r'(?<![\w])error\s*<=',s))==2
  assert r['source_origins'][e['alias']]['path']==e['candidate']
 assert len(r['source_origins'])==18
 for alias,m in r['source_origins'].items():
  assert sha(ROOT/m['path'])==m['sha256']
  if alias not in [e['alias'] for e in r['production'].values()]:assert m==origins[alias]
 # All pre-edge fault/ack pairs, all top clear causes, arbitrary local cancellation,
 # held fault or an ordered sequence of failure calls (all 256 reason values).
 # Controls dominate fail calls exactly as in both production always_ff blocks.
 rows=0;multi_rows=0
 for fault,ack,reset,abort,accepted,local_cancel,write in itertools.product(range(2),repeat=7):
  cancel=abort or local_cancel;clear=reset or accepted or cancel
  next_ack=0 if(reset or abort or accepted)else(ack or fault)
  for reason in range(256):
   next_fault=0 if clear else bool(reason)if write else fault
   pending=bool(write and reason and not ack and not fault and not clear)
   assert pending==bool(next_fault and not next_ack),(fault,ack,reset,abort,accepted,local_cancel,write,reason)
   rows+=1
 # Recon can call fail twice; last reason wins in fault_o and pending in same task.
 for fault,ack,clear,reason1,reason2 in itertools.product(range(2),range(2),range(2),range(256),range(256)):
  next_ack=ack or fault
  next_fault=False if clear else bool(reason2)
  pending=False if clear else bool(reason2 and not ack and not fault)
  assert pending==bool(next_fault and not next_ack)
  multi_rows+=1
 # Coupled top cancels retain accepted-start suppression and sticky status priority.
 top_rows=0
 for reset,abort,accepted,coef,inv,rec,ia,ra,ifail,rfail in itertools.product(range(2),repeat=10):
  icancel=abort or(not accepted and(coef or rec));rcancel=abort or(not accepted and(coef or inv))
  iac=0 if(reset or abort or accepted)else(ia or inv);rac=0 if(reset or abort or accepted)else(ra or rec)
  inf=0 if(reset or accepted or icancel)else(inv or ifail);rnf=0 if(reset or accepted or rcancel)else(rec or rfail)
  ip=bool(ifail and not ia and not inv and not(reset or accepted or icancel));rp=bool(rfail and not ra and not rec and not(reset or accepted or rcancel))
  assert ip==bool(inf and not iac) and rp==bool(rnf and not rac)
  assert bool(abort or ip or rp)==bool(abort or(inf and not iac)or(rnf and not rac))
  top_rows+=1
 result=dict(status='PASS_STRUCTURAL_INDUCTION_AND_CONTROL_MODEL_NOT_RTL',assignments_unchanged=counts,local_transition_rows=rows,ordered_double_fail_rows=multi_rows,coupled_top_rows=top_rows,added_public_cycles=0,source_sha256={str((ROOT/e[k]).relative_to(ROOT)):sha(ROOT/e[k]) for e in r['production'].values() for k in ('original','candidate')},limitations=['Algebra exhausts two-state fault/ack/control/reason next-state combinations, conditional on structurally audited assignments. It is not formal HDL equivalence or four-state proof.','All original error, fault, cancellation, state, counter and output assignments are retained. Focused actual RTL and full canonical qualification remain separate gates.'])
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],rows,multi_rows,top_rows)
if __name__=='__main__':main()
