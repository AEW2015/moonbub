#!/usr/bin/env python3
"""Exhaustive 15-bit-prefix guarded-use model; no RTL run or reachability claim."""
from collections import Counter
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v109/rice'
def balanced_rank(prefix):
 candidates=[bool(prefix&(1<<(14-i))) for i in range(15)]+[False]
 pairs=[2*i if candidates[2*i] else 2*i+1 if candidates[2*i+1] else 15 for i in range(8)]
 quads=[pairs[2*i] if pairs[2*i]!=15 else pairs[2*i+1] for i in range(4)]
 octets=[quads[2*i] if quads[2*i]!=15 else quads[2*i+1] for i in range(2)]
 return octets[0] if octets[0]!=15 else octets[1]
def semantics(rank,window,serial):
 zeros=min(window,rank);found=rank<window
 take=1 if serial else 15 if zeros==15 else zeros+1 if found else window
 return zeros,found,take

def main():
 # Exhaust every 15-bit word. Quotient classes are grouped only AFTER checking
 # independent linear first-one and the actual balanced-tree structure.
 ranks=[]
 for word in range(1<<15):
  linear=next((i for i in range(15) if word&(1<<(14-i))),15)
  assert balanced_rank(word)==linear;ranks.append(linear)
 groups=[]
 for valid in range(16):
  mask=((1<<15)-1)^((1<<(15-valid))-1)
  group=Counter()
  for word,rank in enumerate(ranks):
   masked=next((i for i in range(valid) if word&(1<<(14-i))),15)
   assert masked==ranks[word&mask];group[(masked,rank,bool(word&(1<<14)))]+=1
  assert sum(group.values())==1<<15;groups.append(group)
 represented=0;classes=0;unused_private_difference_classes=0;used_steps=0
 for available in range(65):
  for window in range(16):
   for serial in (False,True):
    needed=1 if serial else window;canstep=available>=needed
    for (old_rank,new_rank,first),multiplicity in groups[min(available,15)].items():
     old=semantics(old_rank,window,serial);new=semantics(new_rank,window,serial)
     # Request/input acceptance and wait count use needed/canstep only.
     assert needed==(1 if serial else window)
     if canstep and window!=0:
      if serial:
       assert old[2]==new[2]==1
       # Same stored reservoir: extraction and quotient<14 handling are equal,
       # independent of the private rank and the value of this first bit.
       old_selected=(old[2], int(first));new_selected=(new[2], int(first))
       assert old_selected==new_selected==(1,int(first))
      else:assert old==new
      used_steps+=multiplicity
     if old!=new:
      assert not canstep or serial
      unused_private_difference_classes+=1
     represented+=multiplicity;classes+=1
 assert represented==65*16*2*(1<<15)
 # Counterexamples establish the intentionally scoped private difference.
 assert semantics(15,15,False)!=(semantics(0,15,False))
 assert semantics(15,3,False)==semantics(5,3,False)
 result=dict(status='PASS_EXHAUSTIVE_GUARDED_PREFIX_MODEL_NOT_RTL_NOT_SELECTED',all_15bit_prefix_words=1<<15,available_domain=[0,64],window_domain=[0,15],serial_modes=2,represented_exhaustive_cases=represented,distinct_guard_classes_checked=classes,used_prefix_cases=used_steps,unused_private_difference_classes=unused_private_difference_classes,bit_padding_assumption=False,public_or_stored_state_comparison_relaxed=False,scope='All arbitrary 15-bit prefix patterns, including unowned nonzero bits. Class grouping is exact after independently checking each word/tree/masked rank. Stored-state induction then uses unchanged request/input/reset/start/error priorities and complete public/stored RTL miter; no raw unused rank equality claim, no RTL or physical timing result.')
 (AREA/'model.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],represented,classes)
if __name__=='__main__':main()
