#!/usr/bin/env python3
"""Model-only exact live-block capacity bounds; no RTL/tool execution."""
import os
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import hashlib,json,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'experiments/python-gamebub-v107/capacity-model';M=1<<28;C=1<<14;MASK=(1<<32)-1

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def original(b,p):
 return (np.uint64(32)+((2*b+15)&np.uint64(MASK^15))+p)&np.uint64(MASK)
def proposed(b,p):
 a=(np.uint64(2)+(p>>np.uint64(4)))&np.uint64(M-1)
 normal=a<=C
 # Signed intermediates keep the unused normal/wrap branch from unsigned underflow.
 aa=np.asarray(a,dtype=np.int64);bb=np.asarray(b,dtype=np.int64)
 upper_normal=8*(C-aa);lower_wrap=8*(M-aa-1);upper_wrap=8*(M-aa+C)
 return (normal&(bb<=upper_normal))|((~normal)&(bb>lower_wrap)&(bb<=upper_wrap))
def simplified(b,p):
 a=(np.uint64(2)+(p>>np.uint64(4)))&np.uint64(M-1)
 upper=((np.uint64(C+M)-a)&np.uint64(M-1))<<np.uint64(3)
 lower=((~a)&np.uint64(M-1))<<np.uint64(3)
 return (b<=upper)&((a<=C)|(b>lower))
def checked(b,p):
 expected=original(b,p)<=C*16;actual=proposed(b,p);assert np.array_equal(actual,simplified(b,p))
 if not np.array_equal(expected,actual):
  bad=np.flatnonzero(expected!=actual);idx=int(bad[0]);raise AssertionError(dict(b=int(np.broadcast_to(b,actual.shape).flat[idx]),p=int(np.broadcast_to(p,actual.shape).flat[idx])))
 return int(np.size(actual))

def main():
 start=time.monotonic();OUT.mkdir(exist_ok=True);b=np.arange(1<<17,dtype=np.uint64);r=np.asarray((b+7)//8,dtype=np.int64)
 aa={0,1,2,3,7,8,C-2,C-1,C,C+1,C+2,2*C-1,2*C,M-C-2,M-C-1,M-C,M-C+1,M-3,M-2,M-1}
 for bit in range(28):
  x=1<<bit
  for delta in (-2,-1,0,1,2):aa.add((x+delta)&(M-1));aa.add((M-x+delta)&(M-1))
 edge_grid=0
 for a in sorted(aa):edge_grid+=checked(b,np.uint64(((a-2)&(M-1))<<4))
 # Every block at all low/wrap transition boundaries tied to its exact ceil(b/8).
 tied=0
 for delta in (-2,-1,0,1,2):
  for a in ((C-r+delta)&np.uint64(M-1),(M-r+delta)&np.uint64(M-1),(M+C-r+delta)&np.uint64(M-1)):
   p=np.asarray(((a-2)&(M-1))<<4,dtype=np.uint64);tied+=checked(b,p)
 raw_plan=np.uint64(32)+np.uint64(128)*b;assert np.array_equal(raw_plan<=C*16,b<=2047)
 rng=np.random.default_rng(108801);random_aligned=random_counts=fault_cases=0;max_bounds=[0,0,0]
 for _ in range(16):
  bb=rng.integers(0,1<<17,65536,dtype=np.uint64);p=rng.integers(0,M,65536,dtype=np.uint64)<<np.uint64(4);random_aligned+=checked(bb,p)
  counts=rng.integers(0,1<<32,(3,65536),dtype=np.uint64)
  aligned=(counts*4+15)&np.uint64(MASK^15);pc=(np.sum(aligned,axis=0,dtype=np.uint64))&np.uint64(MASK);random_counts+=checked(bb,pc)
  old_capacity=original(bb,pc)<=C*16;new_capacity=proposed(bb,pc)
  raw=rng.integers(0,2,65536,dtype=np.uint8).astype(bool);stale=rng.integers(0,2,65536,dtype=np.uint8).astype(bool)
  base_bad=(bb==0)|(bb>8192)|(counts[0]>bb*5)|(counts[1]>bb*15)|(counts[2]>bb*43)|(raw&np.any(counts!=0,axis=0))
  old_bad=base_bad|np.where(raw,raw_plan[np.asarray(bb,dtype=np.int64)]>C*16,~old_capacity)
  new_bad=base_bad|np.where(raw,bb>2047,~new_capacity)
  old_error=np.where(stale,2,np.where(old_bad,1,0));new_error=np.where(stale,2,np.where(new_bad,1,0));assert np.array_equal(old_error,new_error);fault_cases+=len(bb)
 # Width maxima over their qualified branches, derived algebraically.
 max_bounds=[8*C,8*(M-C-2),8*(M-1)];assert all(0<=x<1<<32 for x in max_bounds)
 source=ROOT/'fpga/experiments/cu66-v107-count-threshold/packed_scratch_v91g2.sv'
 result=dict(schema='v107-capacity-bound-model-v1',status='PASS_MODEL_ONLY',actual_RTL_run=False,native_run=False,formal_tool_run=False,script_sha256=sha(Path(__file__).resolve()),numpy_version=np.__version__,frozen_source= str(source.relative_to(ROOT)),frozen_source_sha256=sha(source),domain=dict(blocks_bits=17,blocks_min=0,blocks_max=131071,prefix_bits=32,prefix_alignment=16,a_modulus=M,capacity_units16=C),checks=dict(full_u17_edge_grid=edge_grid,distinct_a_grid_values=len(aa),full_u17_tied_boundary_grid=tied,raw_all_u17=len(b),random_arbitrary_aligned_prefix=random_aligned,random_full_u32_count_triples=random_counts,error_priority_model_cases=fault_cases),bounds_max_u32=dict(normal_upper=max_bounds[0],wrap_lower=max_bounds[1],wrap_upper=max_bounds[2],simplified_upper=(M-1)*8,simplified_lower=(M-1)*8),theorem='plan/16=(a+ceil(b/8))mod2^28; normal a<=C needs b<=8(C-a); wrap a>C needs b>8(M-a-1) andb<=8(M-a+C); raw capacity iff b<=2047. Simplified upper=((C-a)modM)*8,lower=((~a)&(M-1))*8; capok=b<=upper and(a<=C orb>lower).',limitations=['Independent integer/NumPy finite model with algebraic derivation only; not actual RTL simulation, formal equivalence, native area/timing or achieved-clock evidence.','No production file edited. Future variant must precompute packet-only bounds with matching owner, leave original plan_used capture/debug and all later error/owner behavior unchanged, and pass actual complete-module/canonical qualification.','Bounds are valid for every aligned32-bitP andfull17-bitb; finite grids/randoms are not exhaustive of all2^45pairs.'],elapsed_seconds=time.monotonic()-start)
 (OUT/'results.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
