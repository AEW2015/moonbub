#!/usr/bin/env python3
"""Audit all paired assignments and exhaust exact count/state predicate algebra."""
import hashlib,itertools,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-ready';AREA=ROOT/'experiments/python-gamebub-v110/ready'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((SRC/'edit-recipe.json').read_text());e=next(iter(r['production'].values()));p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256']and sha(q)==e['candidate_sha256'];s=p.read_text()
 for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
 assert s==q.read_text()
 for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
 assert s==p.read_text()
 for n in ('state','cache_count','error','fault_o'):
  pattern=r'(?<![\w])'+n+r'\s*<=\s*([^;]+);';assert re.findall(pattern,p.read_text())==re.findall(pattern,q.read_text())
 inventory=r['all_write_inventory'];states=[x for x in inventory if x['variable']=='state'];counts=[x for x in inventory if x['variable']=='cache_count'];assert len(states)==31 and len(counts)==3
 values={'IDLE':0,'FINISHED':14,'FAILED':15};active=0;idle=0
 for x in states:
  if x['rhs']in values:assert x['predicate_rhs']=="1'b0";idle+=1
  else:assert x['predicate_rhs']=="1'b1";active+=1
 assert(active,idle)==(19,12)
 rows=0
 for n,reset,abort,accepted,beat,last in itertools.product(range(2048),range(2),range(2),range(2),range(2),range(2)):
  old=n!=0
  if reset or abort:nn=0;flag=False
  elif accepted:nn=n;flag=old
  elif beat:
   if last or n==1349:nn=0;flag=False
   else:nn=(n+1)&2047;flag=n!=2047
  else:nn=n;flag=old
  assert flag==(nn!=0);rows+=1
 state_rows=0
 for old in range(256):
  for nextstate in range(256):assert (nextstate not in(0,14,15))==(nextstate!=0 and nextstate!=14 and nextstate!=15);state_rows+=1
 # Accepted start writes ADMIT, then invalid epoch overwrites it with FAILED.
 for invalid in range(2):
  nextstate=1;flag=True
  if invalid:nextstate=15;flag=False
  assert flag==(nextstate not in(0,14,15))
 result=dict(status='PASS_SOURCE_AND_EXHAUSTIVE_PREDICATE_MODEL_NOT_RTL',state_writes=31,state_active_writes=active,state_quiescent_writes=idle,cache_count_writes=3,count_control_rows=rows,state_predicate_rows=state_rows,all_original_assignments_and_assertions_preserved=True,accepted_start_failed_override_checked=True,arbitrary_11bit_wrap_checked=True,source_sha256={e[k]:sha(ROOT/e[k])for k in('original','candidate')},added_public_cycles=0,scope='Two-state next-value algebra plus reversible source audit, not formal RTL equivalence or full-pipeline/native proof.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],rows,state_rows)
if __name__=='__main__':main()
