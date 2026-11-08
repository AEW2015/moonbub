#!/usr/bin/env python3
"""Independent finite integer/stage/schedule checks. This never executes RTL."""
import hashlib,json,random
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/count-threshold';FPGA=ROOT/'fpga/experiments/cu66-v107-count-threshold';MASK=(1<<32)-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ceiling(n,d):return n//d+int(n%d!=0)
def partial(n,d):
 m=(1<<32)//d;lo=n&65535;hi=n>>16;ml=m&65535;mh=m>>16
 p00=lo*ml;p01=lo*mh;p10=hi*ml;p11=hi*mh
 cross=p01+p10+(p00>>16);q0=p11+(cross>>16)
 assert q0==n*m>>32 and q0 in (n//d,n//d-1)
 product=((q0&65535)*d+(((q0>>16)*d&65535)<<16))&MASK
 assert product==q0*d<=n
 rem=n-product;assert 0<=rem<2*d
 actual=q0+int(rem!=0)+int(rem>d);assert actual==ceiling(n,d)
 return actual,rem

class Pipe:
 def __init__(self,d):
  self.d=d;self.m=(1<<32)//d;self.s=dict(cap=0,p0=0,p1=0,p2=0,p3=0,cross=0,low=0,h1=0,carry=0,h2=0,q3=0,cl=0,ch=0,q4=0,prod=0,q5=0,rem=0,q6=0,nd=[0]*6,valid=0,live=False,cache=0);self.pending=deque();self.t=0;self.commits=0;self.flushes=0;self.max_pending=0
 def step(self,n,capture=False,flush=False):
  o=self.s;d=self.d;m=self.m
  expected=None
  if flush:self.pending.clear();self.flushes+=1
  elif o['valid']&128:
   due,owner=self.pending.popleft();assert due==self.t
   expected=ceiling(owner,d);assert o['q6'] in (owner//d,owner//d-1);assert o['rem']==owner-o['q6']*d<2*d
  if capture and not flush:self.pending.append((self.t+8,n))
  a=o['cap'];q=o['q3'];nd=[a]+o['nd'][:5]
  s=dict(cap=n,p0=((a&65535)*(m&65535))>>16,p1=(a&65535)*(m>>16),p2=(a>>16)*(m&65535),p3=(a>>16)*(m>>16),cross=o['p1']+o['p2'],low=o['p0'],h1=o['p3'],carry=(o['cross']+o['low'])>>16,h2=o['h1'],q3=(o['h2']+o['carry'])&MASK,cl=(q&65535)*d,ch=((q>>16)*d)&65535,q4=q,prod=(o['cl']+(o['ch']<<16))&MASK,q5=o['q4'],rem=(o['nd'][5]-o['prod'])&MASK,q6=o['q5'],nd=nd,valid=0 if flush else ((o['valid']<<1)|int(capture))&255,live=False if flush else o['live'] or bool(o['valid']&128),cache=o['cache'])
  if o['valid']&128:s['cache']=(o['q6']+(0 if o['rem']==0 else 2 if o['rem']>d else 1))&MASK
  if expected is not None:assert s['cache']==expected and s['live'];self.commits+=1
  self.s=s;self.t+=1;self.max_pending=max(self.max_pending,len(self.pending));assert len(self.pending)<=8
  return expected is not None

def recipe_audit():
 r=json.loads((FPGA/'edit-recipe.json').read_text());assert r['post_capture_edges']==8
 for name,e in r['production'].items():
  original=ROOT/e['original'];assert sha(original)==e['original_sha256'];s=original.read_text()
  for edit in e['edits']:assert s.count(edit['before'])==1;s=s.replace(edit['before'],edit['after'],1)
  assert s==(FPGA/name).read_text() and sha(FPGA/name)==e['candidate_sha256']
  for edit in reversed(e['edits']):assert s.count(edit['after'])==1;s=s.replace(edit['after'],edit['before'],1)
  assert s==original.read_text()
 return r

def header(pipes,counts,rng,abort_index=None):
 for pipe in pipes:pipe.step(rng.getrandbits(32),False,True)
 cache=[rng.randrange(256) for _ in range(46)];packet=[rng.randrange(256) for _ in range(46)]
 for g,n in enumerate(counts):packet[30+4*g:34+4*g]=n.to_bytes(4,'little')
 captured={};committed={};edge=0
 for index in range(46):
  for wait in (False,True):
   flush=bool(wait and index==abort_index)
   for g,pipe in enumerate(pipes):
    last=33+4*g;n=packet[index]<<24|cache[last-1]<<16|cache[last-2]<<8|cache[last-3]
    take=wait and index==last and not flush
    if take:assert n==counts[g];captured[g]=edge
    if pipe.step(n,take,flush):committed[g]=edge
   if flush:return dict(aborted=True,edges=edge+1)
   if wait:cache[index]=packet[index]
   edge+=1
 # HEADER is the93rd edge after the46 REQ/WAIT pairs.
 for g,pipe in enumerate(pipes):
  pipe.step(rng.getrandbits(32));assert pipe.s['live'] and pipe.s['cache']==ceiling(counts[g],pipe.d);assert committed[g]-captured[g]==8
 assert edge==92 and captured[2]==83 and committed[2]==91
 for _ in range(17):
  for g,pipe in enumerate(pipes):old=pipe.s['cache'];pipe.step(rng.getrandbits(32));assert pipe.s['cache']==old==ceiling(counts[g],pipe.d)
 return dict(aborted=False,edges=93,latest_capture=83,latest_commit=91,header=92,held_edges=17)

def main():
 AREA.mkdir(exist_ok=True);recipe=recipe_audit();rng=random.Random(109101);metrics={};boundary_cases=0;random_cases=0
 for d in (5,15,43):
  maxrem=0
  for b in range(1<<17):
   bound=b*d
   for n in (max(0,bound-1),bound,bound+1,0,MASK):
    t,rem=partial(n,d);assert (n>b*d)==(b<t);maxrem=max(maxrem,rem);boundary_cases+=1
  extremes=set([0,1,d-1,d,d+1,65535,65536,65537,(1<<31)-1,1<<31,(1<<31)+1])|{MASK-r for r in range(2*d+2)}
  for n in sorted(extremes):partial(n,d)
  for _ in range(100000):
   n=rng.getrandbits(32);b=rng.randrange(1<<17);t,rem=partial(n,d);assert(n>b*d)==(b<t);maxrem=max(maxrem,rem);random_cases+=1
  pipe=Pipe(d)
  for _ in range(30000):pipe.step(rng.getrandbits(32),rng.randrange(4)!=0,rng.randrange(97)==0)
  for _ in range(9):pipe.step(rng.getrandbits(32))
  assert not pipe.pending;metrics[str(d)]=dict(reciprocal=(1<<32)//d,max_remainder=maxrem,stream_cycles=pipe.t,stream_commits=pipe.commits,stream_flushes=pipe.flushes,max_pending=pipe.max_pending)
 pipes=[Pipe(d) for d in (5,15,43)];header_packets=0;abandoned=0;held=0
 for _ in range(1024):
  counts=[rng.getrandbits(32) for _ in pipes];result=header(pipes,counts,rng);assert not result['aborted'];header_packets+=1;held+=17
  for index in (33,37,41):
   assert header(pipes,[rng.getrandbits(32) for _ in pipes],rng,index)['aborted'];abandoned+=1
   result=header(pipes,[rng.getrandbits(32) for _ in pipes],rng);assert not result['aborted'];header_packets+=1;held+=17
 independent=AREA/'arithmetic-review.json';assert independent.exists()
 r=dict(schema='v107-count-threshold-model-preparation-v1',status='PASS_PREPARATION_MODEL_NOT_RTL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [FPGA/n for n in recipe['production']]+[FPGA/'edit-recipe.json',Path(__file__).resolve(),Path(__file__).parent/'prepare.py',independent]},integer_boundary_predicate_cases=boundary_cases,random_full_u32_predicate_cases=random_cases,full_u17_block_domain_per_divisor=131072,pipelines=metrics,packet_schedule=dict(successful_headers=header_packets,abandoned_headers=abandoned,held_metadata_edges=held,latest_count_capture_edge=83,latest_threshold_commit_edge=91,header_edge=92,post_capture_edges=8,actual_RTL_edges=0),limits=['Finite integer and independently modeled pipeline/schedule checks only; no RTL execution, native DSP/register inference or timing claim.','All high32 counts and full17bit blocks remain defined; full2^32 numerator domain is supported by the integer theorem, not exhaustively simulated.','Model header schedules use coherent little-endian current-byte forwarding and existing46 REQ/WAIT pairs; real production shortest RAW path remains an actual RTL proof obligation.'])
 (AREA/'preparation.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:r[k] for k in ['status','integer_boundary_predicate_cases','random_full_u32_predicate_cases','pipelines','packet_schedule']},indent=2))
if __name__=='__main__':main()
