#!/usr/bin/env python3
"""Exhaust exact take arithmetic and guarded parallel quotient/suffix identities."""
import hashlib,json,itertools
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-prefix';AREA=ROOT/'experiments/python-gamebub-v110/prefix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=json.loads((SRC/'edit-recipe.json').read_text());e=next(iter(r['production'].values()));p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256']and sha(q)==e['candidate_sha256'];s=p.read_text()
 for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
 assert s==q.read_text()
 for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
 assert s==p.read_text();rows=0;selected=0
 for window,rank,available,serial in itertools.product(range(16),range(16),range(65),range(2)):
  zeros=min(window,rank);found=rank<window;old=1 if serial else 15 if zeros==15 else zeros+1 if found else window;new=1 if serial else rank+1 if found else window
  assert old==new
  if not serial and window and available>=window and(found or window==15):assert zeros==rank and(zeros==15)==(rank==15);selected+=1
  rows+=1
 v=dict(status='PASS_EXHAUSTIVE_PARALLEL_PREFIX_MODEL_NOT_RTL',take_rows=rows,selected_parallel_rank_rows=selected,available_domain=[0,64],window_domain=[0,15],rank_domain=[0,15],serial_modes=2,arbitrary_unowned_bits_allowed=True,added_public_cycles=0,source_sha256={e[k]:sha(ROOT/e[k])for k in('original','candidate')},limitations='Two-state algebra plus reversible source audit, separate from actual RTL and final route.')
 (AREA/'model.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(v['status'],rows,selected)
if __name__=='__main__':main()
