#!/usr/bin/env python3
"""Lightweight prefix algebra/fetch-schedule feasibility and exact-source audit only."""
import hashlib,itertools,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v107/plan-prefix';SRC=ROOT/'fpga/experiments/cu66-v107-plan-prefix';MASK=(1<<32)-1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def aligned(n):return ((n+15)&MASK)&0xfffffff0
def part(count):return aligned((count*4)&MASK)
def sum3(a,b,c):return ((a^b^c)+(((a&b)|(a&c)|(b&c))<<1))&MASK
def sum4(a,b,c,d):return sum3(a^b^c,(((a&b)|(a&c)|(b&c))<<1)&MASK,d)
def sum5(a,b,c,d,e):
 s=a^b^c;carry=(((a&b)|(a&c)|(b&c))<<1)&MASK
 return sum3(s^d^e,(((s&d)|(s&e)|(d&e))<<1)&MASK,carry)
def main():
 AREA.mkdir(parents=True,exist_ok=True);recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for file in recipe['files']:
  old=ROOT/file['original'];new=ROOT/file['candidate'];assert sha(old)==file['original_sha256'] and sha(new)==file['candidate_sha256'];s=old.read_text()
  for e in file['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
  assert s==new.read_text()
  for e in reversed(file['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
  assert s==old.read_text()
 rng=random.Random(108041);points=[0,1,2,3,4,7,8,15,16,17,0x1ffff,0x3ffffffc,0x3fffffff,0x40000000,0x7fffffff,0x80000000,0xbfffffff,0xfffffff0,0xfffffffc,0xffffffff];digest=hashlib.sha256();rows=0
 triples=itertools.chain(itertools.product(points,repeat=3),((rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32)) for _ in range(100000)))
 for c1,c2,c3 in triples:
  b=rng.randrange(1<<17);a1,a2,a3=map(part,(c1,c2,c3));base=(32+aligned(b*2))&MASK;p12=(a1+a2)&MASK;p123=(p12+a3)&MASK
  old=(sum3(32,aligned(b*2),a1),sum4(32,aligned(b*2),a1,a2),sum5(32,aligned(b*2),a1,a2,a3));new=((base+a1)&MASK,(base+p12)&MASK,(base+p123)&MASK);assert old==new
  for count,a in zip((c1,c2,c3),(a1,a2,a3)):assert a==((((count*4)&MASK)+15)&MASK)//16*16
  digest.update(b.to_bytes(3,'little')+b''.join(n.to_bytes(4,'little') for n in (c1,c2,c3,*new)));rows+=1
 # Model the existing minimum two-edge byte fetch and nonblocking pipeline.
 # Partial previous packets are deliberately abandoned with private data held.
 a=[rng.getrandbits(32) for _ in range(3)];p12=rng.getrandbits(32);p123=rng.getrandbits(32);schedule_rows=0;captures=0;held=0;retries=0
 def edge(byte=None,index=None,valid=True,buffer=None):
  nonlocal p12,p123,captures,schedule_rows
  new12=(a[0]+a[1])&MASK;new123=(p12+a[2])&MASK
  if byte is not None and valid and index in (33,37,41):
   at={33:0,37:1,41:2}[index];start=(30,34,38)[at];word=int.from_bytes(bytes(buffer[start:start+3])+bytes([byte]),'little');a[at]=part(word);captures+=1
  p12,p123=new12,new123;schedule_rows+=1
 for attempt in range(2048):
  previous=[rng.getrandbits(8) for _ in range(46)];cut=rng.randrange(46)
  for index in range(cut):edge();edge(previous[index],index,buffer=previous)
  # Reset/start/cancel and rejected epoch/address/context responses cannot own
  # metadata; private pipeline continues, while captures reject those events.
  for _ in range(7):edge(rng.randrange(256),rng.choice((33,37,41)),False,previous)
  retries+=1;counts=[rng.getrandbits(32) for _ in range(3)] if attempt else [0,0,0];header=[rng.randrange(256) for _ in range(46)]
  for at,n in zip((30,34,38),counts):header[at:at+4]=n.to_bytes(4,'little')
  buf=previous.copy()
  for index,byte in enumerate(header):
   edge();edge(byte,index,buffer=buf);buf[index]=byte
  # The next actual edge is HEADER, then earliest RAW METADATA. All prefixes
  # must already match before HEADER; no use of newly updated public counts.
  expected=(part(counts[0]),(part(counts[0])+part(counts[1]))&MASK,sum(map(part,counts))&MASK)
  assert (a[0],p12,p123)==expected
  for _ in range(17):edge();assert (a[0],p12,p123)==expected;held+=1
 report=dict(schema='v107-plan-count-prefix-feasibility-v1',status='PASS_PREPARATION_MODEL_ONLY',actual_RTL_run=False,source_sha256={str((ROOT/f['candidate']).relative_to(ROOT)):f['candidate_sha256'] for f in recipe['files']},production_recipe_sha256=sha(SRC/'edit-recipe.json'),full32_count_triples=rows,mathematical_universal_basis='Aligned(count*4) uses modulo2^32 arithmetic at product and rounding; carry-save sums equal ordinary sums in Z/(2^32); associativity allows base+prefix with full32 results. Finite probes supplement this identity, not exhaustive2^96.',algebra_digest_sha256=digest.hexdigest(),fetch_schedule_edges=schedule_rows,validated_count_captures=captures,abandoned_packet_retries=retries,held_metadata_edges=held,all_public_counts_update_edge_preserved=True,live_blocks_not_precached=True,private_new_bits=160,rtl_files=4,limits=['Python algebra/source/fetch-schedule model only; actual SV controller simulation and native mapping/timing are unrun.','Schedule models legal F_HEADER fetch ordering plus discarded partial packets and rejected ownership events; arbitrary internal state does not establish a valid prefix owner.','Existing metadata ports and counts update remain unchanged; new prefix outputs are unspecified without owned metadata.'])
 (AREA/'preparation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['status'],rows,schedule_rows)
if __name__=='__main__':main()
