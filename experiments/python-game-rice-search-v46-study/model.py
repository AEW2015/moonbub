"""Bounded actual-byte Rice parameter search, unchanged AB38 decoder grammar."""
from pathlib import Path
import importlib.util,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('rice46_frozen_binary38_encoder',HERE.parent/'python-game-binary-v38-study/model.py');old=importlib.util.module_from_spec(s);sys.modules[s.name]=old;s.loader.exec_module(old)
def neighbors(k,maximum):return tuple(dict.fromkeys((k,max(0,k-1),min(maximum,k+1))))
def event_stream(values,k0,k1,dc):
 coder=old.BinaryEncoder()
 if dc:
  for value in values:coder.rice(value,k0,14,0)
 else:
  runs,levels=values
  for run,level in zip(runs,levels,strict=True):coder.rice(run,k0,24,0);coder.rice(level,k1,12,1)
 body,bits=coder.finish()
 return old.STREAM.pack(k0,k1,bits)+body,dict(binary_decisions=coder.decisions,renorm_steps=coder.renorm,max_renorm_per_bit=coder.maximum_renorm)
def encode(a,bw):
 if not isinstance(a,np.ndarray) or a.dtype!=np.int16 or a.ndim!=3 or a.shape[1:]!=(8,8) or not 1<=len(a)<=65536 or type(bw)is not int or not 1<=bw<=256 or len(a)%bw or np.any(a<-2048) or np.any(a>2048):raise ValueError('bounded coefficient geometry/domain')
 start=time.perf_counter_ns();zig=a.reshape(-1,64)[:,old.ZIGZAG].astype(np.int32);dc=zig[:,0].copy();dc[1:]-=zig[:-1,0];dc[::bw]=zig[::bw,0];dc=old.mapped(dc);kd=old.best_k(dc,13,14)
 groups=[(True,dc,[(k,255) for k in neighbors(kd,13)])];counts=[]
 for lo,hi in old.BANDS:
  seq=zig[:,lo:hi].reshape(-1);indices=np.flatnonzero(seq);runs=np.diff(np.r_[-1,indices])-1;levels=old.mapped(seq[indices])-1;counts.append(len(indices));kr,kv=old.best_k(runs,19,24),old.best_k(levels,11,12)
  keys=[(kr,kv)]+sorted(((r,v) for r in neighbors(kr,19) for v in neighbors(kv,11) if (r,v)!=(kr,kv)),key=lambda p:(abs(p[0]-kr)+abs(p[1]-kv),p))
  groups.append((False,(runs,levels),keys))
 streams=[];trials=[]
 for index,(isdc,values,keys) in enumerate(groups):
  candidates=[]
  for k0,k1 in keys:
   packet,work=event_stream(values,k0,k1,isdc);candidates.append(dict(k0=k0,k1=k1,packet=packet,bytes=len(packet),work=work))
  selected=min(range(len(candidates)),key=lambda i:candidates[i]['bytes']);streams.append(candidates[selected]['packet']);trials.append(dict(stream=index,selected=selected,candidates=candidates))
 old_streams=[t['candidates'][0]['packet'] for t in trials]
 def frame(parts):
  sizes=list(map(len,parts));flags=0;ns=counts
  if sum(sizes)>=128*len(a):flags=1;parts=[a.astype('<i2').tobytes()];sizes=[128*len(a),0,0,0];ns=[0,0,0]
  return old.seal(old.HEADER.pack(b'AB38',1,flags,len(a),bw,0,*sizes,*ns)+b''.join(parts))
 packet=frame(streams);baseline=frame(old_streams);assert len(packet)<=len(baseline)
 return packet,baseline,trials,dict(search_encode_ms=(time.perf_counter_ns()-start)/1e6,attempted_stream_encodes=sum(len(t['candidates']) for t in trials),selected_parameters=[(t['candidates'][t['selected']]['k0'],t['candidates'][t['selected']]['k1']) for t in trials],stream_changes=sum(t['selected']!=0 for t in trials),same_AB38_wire=True)
