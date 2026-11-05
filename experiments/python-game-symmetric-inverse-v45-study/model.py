"""Exact Q14 inverse by mirrored outputs, keeping both rounding boundaries.

Logical multiply counts describe a sparse MAC implementation, not NumPy timing.
No new codec bits or synthesis results are implied.
"""
from pathlib import Path
import importlib.util,sys
import numpy as np
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('symmetric45_frozen_transform',HERE.parent/'python-transform-study/fixed_codec.py');ft=importlib.util.module_from_spec(s);sys.modules[s.name]=ft;s.loader.exec_module(ft)
Q=ft.Q14
assert all(np.array_equal(Q[k,::-1],Q[k]*(-1 if k%2 else 1)) for k in range(8))
def checked(a):
 a=np.asarray(a)
 if a.shape[-2:]!=(8,8) or a.dtype.kind not in 'iu' or np.any(a<-522240) or np.any(a>522240):raise ValueError('dequantized int domain ±2048*255')
 return a.astype(np.int64,copy=False)
def inverse(a):
 a=checked(a);even=a[...,::2]@Q[::2,:4];odd=a[...,1::2]@Q[1::2,:4]
 mid=np.empty_like(a);mid[...,:4]=(even+odd+8192)>>14;mid[...,4:]=((even-odd+8192)>>14)[...,::-1]
 even=Q[::2,:4].T@mid[...,::2,:];odd=Q[1::2,:4].T@mid[...,1::2,:]
 out=np.empty_like(a);out[...,:4,:]=(even+odd+8192)>>14;out[...,4:,:]=((even-odd+8192)>>14)[...,::-1,:]
 return out

def scalar_sparse(a):
 a=checked(a)
 if a.shape!=(8,8):raise ValueError('single tile')
 mid=np.zeros((8,8),np.int64);out=np.zeros_like(mid);first=second=0;max_first=max_second=0
 for row in range(8):
  for x in range(4):
   e=o=0
   for k in range(8):
    if not a[row,k]:continue
    p=int(a[row,k])*int(Q[k,x]);first+=1
    if k%2:o+=p
    else:e+=p
   max_first=max(max_first,abs(e),abs(o),abs(e+o+8192),abs(e-o+8192));mid[row,x]=(e+o+8192)>>14;mid[row,7-x]=(e-o+8192)>>14
 for col in range(8):
  for y in range(4):
   e=o=0
   for k in range(8):
    if not mid[k,col]:continue
    p=int(mid[k,col])*int(Q[k,y]);second+=1
    if k%2:o+=p
    else:e+=p
   max_second=max(max_second,abs(e),abs(o),abs(e+o+8192),abs(e-o+8192));out[y,col]=(e+o+8192)>>14;out[7-y,col]=(e-o+8192)>>14
 return out,dict(first_products=first,second_products=second,total_products=first+second,max_first_accumulator_magnitude=max_first,max_second_accumulator_magnitude=max_second)

def logical_work(a):
 a=checked(a);mid=(a@Q+8192)>>14;n=int(np.prod(a.shape[:-2])) if a.ndim>2 else 1
 nz_a=int(np.count_nonzero(a));nz_mid=int(np.count_nonzero(mid))
 return dict(blocks=n,dense_direct_products=1024*n,dense_symmetric_products=512*n,sparse_direct_products=8*(nz_a+nz_mid),sparse_symmetric_products=4*(nz_a+nz_mid),
             max_abs_dequant=int(np.abs(a).max(initial=0)),max_abs_mid=int(np.abs(mid).max(initial=0)),
             paired_output_recombination_add_subtracts=128*n,both_Q14_rounding_boundaries_preserved=True,zero_DC_shortcuts_included=False,
             NumPy_matmul_actually_skips_zeros=False)

def scalar_shortcuts(a):
 a=checked(a)
 if a.shape!=(8,8):raise ValueError('single tile')
 nz=np.flatnonzero(a)
 if len(nz)==0:return np.zeros((8,8),np.int64),dict(total_products=0,shortcut='zero')
 if len(nz)==1 and nz[0]==0:
  mid=(int(a[0,0])*5793+8192)>>14;value=(mid*5793+8192)>>14
  return np.full((8,8),value,np.int64),dict(total_products=2,shortcut='DC')
 out,work=scalar_sparse(a);work['shortcut']='complex';return out,work

def interval_bounds():
 limit=522240;first=np.abs(Q).sum(axis=0)*limit+8192;mid=(first>>14);second=np.abs(Q).T@np.broadcast_to(mid,(8,8))+8192
 def signedbits(v):return int(v).bit_length()+1
 return dict(input_absolute_bound=limit,input_signed_bits=signedbits(limit),basis_absolute_bound=int(np.abs(Q).max()),basis_signed_bits=signedbits(np.abs(Q).max()),
             first_accumulator_absolute_bound=int(first.max()),first_accumulator_signed_bits=signedbits(first.max()),mid_absolute_bound=int(mid.max()),mid_signed_bits=signedbits(mid.max()),
             second_accumulator_absolute_bound=int(second.max()),second_accumulator_signed_bits=signedbits(second.max()),
             interval_bound_is_conservative=True,DSP_mapping_or_routed_timing_proven=False)
