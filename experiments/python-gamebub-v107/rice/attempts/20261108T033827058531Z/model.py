#!/usr/bin/env python3
"""Independent low-bit queue versus MSB storage identities over bounded domains."""
import hashlib,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/rice'
MASK=(1<<64)-1

def run():
 rng=random.Random(107401);checks=0;prefix=0;append=0
 for avail in range(65):
  patterns={0,(1<<avail)-1}
  patterns.update(1<<i for i in range(avail))
  patterns.update(rng.getrandbits(avail) for _ in range(32))
  for low in patterns:
   high=low<<(64-avail)
   assert high<=MASK
   for take in range(min(avail,24)+1):
    old=low>>(avail-take) if take else 0
    new=high>>(64-take) if take else 0
    assert new==old
    old_keep=low&((1<<(avail-take))-1)
    new_keep=(high<<take)&MASK
    assert new_keep==old_keep<<(64-avail+take)
    checks+=1
   for window in range(16):
    old_rank=next((i for i in range(window) if avail>i and (low>>(avail-1-i))&1),window)
    new_rank=min(window,next((i for i in range(15) if avail>i and (high>>(63-i))&1),15))
    assert old_rank==new_rank
    prefix+=1
   if avail<=32:
    for n in range(1,33):
     word=rng.getrandbits(n);data=word<<(32-n)
     old=(low<<n)|word
     new=high|(data<<(32-avail))
     assert new==old<<(64-avail-n)
     append+=1
 r={'status':'PASS_BOUNDED_STORAGE_IDENTITIES','extraction_consume_checks':checks,'prefix_rank_checks':prefix,'append_checks':append,'domains':{'available':[0,64],'take':[0,24],'window':[0,15],'input_available':[0,32],'input_bits':[1,32]},'patterns':'zero, all ones, every single bit basis, 32 seeded random words per reservoir length','limitations':'Arithmetic/source proof; actual public RTL and physical timing remain separate gates.'}
 AREA.mkdir(parents=True,exist_ok=True);(AREA/'model-results.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,sort_keys=True))
if __name__=='__main__':run()
