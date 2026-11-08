#!/usr/bin/env python3
"""Exact mathematical header sums, modular addresses and byte-forward captures."""
import hashlib,itertools,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v107/header'
MASK32=(1<<32)-1;MASK35=(1<<35)-1

def sums(mode,qmap,hud,data):
 m=128+mode;r=m+qmap;h=4+hud;e=r+data;t=e+h
 return m,r,h,e,t

def main():
 rng=random.Random(107701);domain=[0,1,15,16,31,32,109,110,127,128,354,355,976,977,49152,49153,0x7fffffff,0x80000000,0xffffff7f,0xffffff80,0xfffffffc,0xffffffff]
 checked=forwarded=equalities=0
 tuples=itertools.chain(itertools.product(domain,repeat=4),(tuple(rng.getrandbits(32) for _ in range(4)) for _ in range(65536)))
 for mode,qmap,hud,data in tuples:
  expected=sums(mode,qmap,hud,data);m,r,h,e,t=expected
  assert max(expected)<=MASK35 and t==132+mode+qmap+hud+data
  assert [m&MASK32,r&MASK32,e&MASK32]==[(128+mode)&MASK32,(128+mode+qmap)&MASK32,(128+mode+qmap+data)&MASK32]
  for size in [0,t&MASK32,0xffffffff,rng.getrandbits(32)]:
   assert (t==size)==((132+mode+qmap+hud+data)==size);equalities+=1
  # Fresh header writes each byte; final-byte forwarding must not read stale
  # bytes left by a previous packet. Exercise a random stale backing array.
  header=bytearray(rng.getrandbits(8) for _ in range(128));cache=[None]*5
  fields=b''.join(x.to_bytes(4,'big') for x in [mode,qmap,hud,data])
  for index in range(36,56):
   byte=fields[index-36] if index<52 else rng.getrandbits(8)
   word=int.from_bytes(header[index-3:index]+bytes([byte]),'big')
   if index==39:cache[0]=128+word
   elif index==43:cache[1]=cache[0]+word
   elif index==47:cache[2]=4+word
   elif index==51:cache[3]=cache[1]+word
   elif index==55:cache[4]=cache[3]+cache[2]
   header[index]=byte
  assert tuple(cache)==expected;checked+=1;forwarded+=20
 maximum=132+4*MASK32;assert maximum==(1<<34)+128 and maximum<(1<<35)
 out={'status':'PASS_EXACT_HEADER_SUM_FORWARDING_MODEL','full32_tuple_checks':checked,'byte_capture_steps':forwarded,'total_equality_checks':equalities,'maximum_exact_total':maximum,'cache_width':35,'domain':'22 boundary values^4 plus65536 seeded full32 tuples; each with random stale header bytes and actual final-byte forwarding schedule.','full_domain_argument':'Every addend is nonnegative32bit; maximum132+4*(2^32-1)=2^34+128<2^35, so35bit sums equal original64bit mathematical sums. Low32 projections equal original modular32bit addresses for every full32 input.','limitations':'Arithmetic/forwarding model only; actual production RTL and physical timing separate.'}
 AREA.mkdir(parents=True,exist_ok=True);(AREA/'model-results.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
