"""Wider half-luma search feasibility, explicitly outside the GM27 wire limit."""
from pathlib import Path
import importlib.util,sys,time
from types import SimpleNamespace
import numpy as np
HERE=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
adaptive=load('wide32_adaptive',HERE.parent/'python-game-adaptive-v29-study/model.py')
runtime=load('wide32_runtime',HERE.parent/'python-game-runtime-v28-study/model.py')
entropy=load('wide32_entropy',HERE.parent/'python-game-entropy-v29-study/model.py')

def predict(reference,vectors,block_size=32):
 ref=runtime.base._planes(reference);h,w=ref[0].shape;mw,mh=runtime.base._grid(w,h,block_size)
 a=np.asarray(vectors)
 if a.dtype!=np.int8 or a.shape!=(mh,mw,2) or np.any(np.abs(a.astype(np.int16))>68):raise ValueError('wide bounded int8 vector map')
 return runtime.taps._predict(ref,a,block_size)

def estimate(source,reference,incumbent,block_size=32):
 start=time.perf_counter_ns();src=runtime.base._planes(source);h,w=src[0].shape;ref=runtime.base._planes(reference,(w,h))
 mw,mh=runtime.base._grid(w,h,block_size);chosen=np.zeros((mh,mw,2),np.int8)
 if incumbent.shape!=chosen.shape or incumbent.dtype!=np.int8 or np.any(np.abs(incumbent.astype(np.int16))>18):raise ValueError('bounded GM27 incumbent map')
 screen=adaptive.compact_samples(src,ref,block_size,4,np.ones((mh,mw),bool));ns=sum(len(s[0]) for s in screen)
 zero=adaptive.compact_cost(screen,chosen,True);counts=np.zeros(mh*mw,np.int64)
 for a,b,y,x,ids,den,weight,_,_ in screen:counts+=weight*np.bincount(ids,minlength=mh*mw)
 active=zero>2*counts.reshape(mh,mw)
 stats=dict(quiet_blocks=int((~active).sum()),active_blocks=int(active.sum()),screen_samples=ns,
            sad_sample_operations=ns,reference_sample_fetches=ns,coarse_candidates=0,refinement_candidates=0,incumbent_maps_scored=0)
 if active.any():
  samples=adaptive.compact_samples(src,ref,block_size,4,active);nc=sum(len(s[0]) for s in samples);best=None
  coarse=sorted(((x,y) for y in range(-64,65,8) for x in range(-64,65,8)),key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
  for dx,dy in coarse:
   v=np.zeros_like(chosen);v[active]=(dx,dy);cost=adaptive.compact_cost(samples,v,True)
   if best is None:best=cost;chosen=v.copy()
   else:
    improve=(cost<best)&active;chosen[improve]=v[improve];best[improve]=cost[improve]
  fine=adaptive.compact_samples(src,ref,block_size,2,active);nf=sum(len(s[0]) for s in fine);origin=chosen.copy();best=None
  offsets=sorted(((x,y) for y in range(-4,5) for x in range(-4,5)),key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
  for dx,dy in offsets:
   v=origin.copy();v[active]+=np.array((dx,dy),np.int8);cost=adaptive.compact_cost(fine,v)
   if best is None:best=cost;chosen=v.copy()
   else:
    improve=(cost<best)&active;chosen[improve]=v[improve];best[improve]=cost[improve]
  own=adaptive.compact_cost(fine,chosen);old=adaptive.compact_cost(fine,incumbent)
  chosen[(old<=own)&active]=incumbent[(old<=own)&active]
  stats.update(coarse_candidates=len(coarse),refinement_candidates=len(offsets),incumbent_maps_scored=2,
   sad_sample_operations=ns+len(coarse)*nc+(len(offsets)+2)*nf,
   reference_sample_fetches=ns+len(coarse)*nc+4*(len(offsets)+2)*nf,
   final_sampled_cost=int(np.minimum(own,old)[active].sum()),incumbent_sampled_cost=int(old[active].sum()))
 stats.update(beyond_GM27_blocks=int(np.any(np.abs(chosen.astype(np.int16))>18,axis=2).sum()),
  max_vector_half_luma=int(np.abs(chosen.astype(np.int16)).max()),search_ms=(time.perf_counter_ns()-start)/1e6)
 return chosen,stats

def residual(source,prediction,q,key):
 """Actual coefficient payloads; no invalid GM27 frame is constructed."""
 m=runtime;start=time.perf_counter_ns();h,w=source[0].shape
 raw=m.base.old._forward(source,prediction);original=m.base._quantize(raw,q,w,h)
 p=SimpleNamespace(key=key,width=w,height=h,source=source,prediction=prediction)
 pruned,rdo=m.counter.rdo_skip(p,original,q,1);coeff=[];payload=[];plans=[]
 for plane,c in enumerate(pruned):
  bw=((w if plane==0 else w//2)+7)//8;cp=m.legacy_plan(c,bw)
  if not np.array_equal(c,original[plane]):
   op=m.legacy_plan(original[plane],bw)
   if op['bytes']<cp['bytes']:c=original[plane]
  plan=entropy._plane_plan(c,bw,m);data,*_=entropy._construct(c,bw,plan,m)
  decoded=m.base._decode_plane(data,len(c),bw);np.testing.assert_array_equal(c,decoded)
  coeff.append(c);payload.append(data);plans.append(plan)
 rebuilt=m.gm.reconstruct(tuple(coeff),prediction,q,w,h)
 return tuple(payload),rebuilt,dict(residual_bytes=sum(map(len,payload)),plans=plans,rdo=rdo,residual_work_ms=(time.perf_counter_ns()-start)/1e6)
