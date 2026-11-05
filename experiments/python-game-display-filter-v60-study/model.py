"""Defined display-only four-sample luma edge filter; never a codec reference.

Vertical then horizontal, 8-pixel edges, integer +4 rounding and bounded delta.
This is an experimental filter, not an HEVC/AV1 conformant in-loop filter.
"""
import numpy as np
PRESETS=(dict(name='identity',alpha=0,beta=0,strength=0),dict(name='weak',alpha=8,beta=4,strength=1),dict(name='medium',alpha=16,beta=8,strength=2),dict(name='strong',alpha=24,beta=12,strength=3))
def filtered_luma(plane,excluded,preset):
 if not isinstance(plane,np.ndarray) or plane.shape!=(480,720) or plane.dtype!=np.uint8:raise ValueError('fixed uint8 luma plane')
 if not isinstance(excluded,np.ndarray) or excluded.shape!=plane.shape or excluded.dtype!=bool:raise ValueError('fixed excluded normalization footprint')
 if preset not in PRESETS:raise ValueError('declared fixed filter preset')
 a=plane.astype(np.int16,copy=True);changed_edges=[]
 for axis in(1,0):
  if not preset['strength']:changed_edges.append(0);continue
  positions=np.arange(8,a.shape[axis],8)
  if axis==1:
   p1=a[:,positions-2].copy();p0=a[:,positions-1].copy();q0=a[:,positions].copy();q1=a[:,positions+1].copy();blocked=excluded[:,positions-2]|excluded[:,positions-1]|excluded[:,positions]|excluded[:,positions+1]
  else:
   p1=a[positions-2,:].copy();p0=a[positions-1,:].copy();q0=a[positions,:].copy();q1=a[positions+1,:].copy();blocked=excluded[positions-2,:]|excluded[positions-1,:]|excluded[positions,:]|excluded[positions+1,:]
  good=(~blocked)&(np.abs(q0-p0)<=preset['alpha'])&(np.abs(p0-p1)<=preset['beta'])&(np.abs(q1-q0)<=preset['beta'])
  delta=np.clip((3*(q0-p0)+(p1-q1)+4)//8,-preset['strength'],preset['strength']);delta=np.where(good,delta,0);P=np.clip(p0+delta,0,255);Q=np.clip(q0-delta,0,255)
  if axis==1:a[:,positions-1]=P;a[:,positions]=Q
  else:a[positions-1,:]=P;a[positions,:]=Q
  changed_edges.append(int(np.count_nonzero(delta)))
 out=a.astype(np.uint8);out.setflags(write=False)
 return out,dict(vertical_changed_edges=changed_edges[0],horizontal_changed_edges=changed_edges[1],changed_luma_samples=int(np.count_nonzero(out!=plane)),reference_mutated=False,full_luma_proof_array_staged=True,FPGA_line_buffer_or_timing_implemented=False)
