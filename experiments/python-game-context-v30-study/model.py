"""Exact sparse run/level deletion deltas with fixed Rice parameters.

This is a host planning oracle, not a new wire format. Parameter optimization,
DC coding, layout changes and coefficient insertion are outside a local query.
"""
from pathlib import Path
import importlib.util
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('context30_entropy29',HERE.parent/'python-game-entropy-v29-study/model.py')
e=importlib.util.module_from_spec(spec);sys.modules[spec.name]=e;spec.loader.exec_module(e)


def rice_bits(values,k,escape):
    a=np.asarray(values,np.int64)
    if type(k) is not int or not 0<=k<escape or np.any(a<0) or np.any(a>=1<<escape):
        raise ValueError('bounded Rice values/parameter')
    q=a>>k
    return np.where(q<15,q+1+k,15+escape)


class BandIndex:
    """O(N) retained sparse tokens plus O(log N) interval deletion queries."""
    def __init__(self,sequence,kr,kv):
        seq=np.asarray(sequence)
        if seq.ndim!=1 or seq.dtype!=np.int16 or not 1<=len(seq)<=65536*63 or np.any(np.abs(seq.astype(np.int32))>2048):
            raise ValueError('bounded int16 band')
        if type(kr) is not int or not 0<=kr<=19 or type(kv) is not int or not 0<=kv<=11:
            raise ValueError('EC26 band parameters')
        self.length=len(seq);self.kr=kr;self.kv=kv
        self.indices=np.flatnonzero(seq)
        self.runs=np.diff(np.r_[-1,self.indices])-1
        self.levels=e.ec.f._mapped(seq[self.indices])-1
        self.token_bits=rice_bits(self.runs,kr,24)+rice_bits(self.levels,kv,12)
        self.prefix=np.r_[0,np.cumsum(self.token_bits,dtype=np.int64)]
        self.bits=int(self.prefix[-1])
        self.array_bytes=sum(x.nbytes for x in (self.indices,self.runs,self.levels,self.token_bits,self.prefix))

    def delete_interval(self,start,stop):
        if type(start) is not int or type(stop) is not int or not 0<=start<=stop<=self.length:
            raise ValueError('bounded half-open deletion interval')
        left,right=np.searchsorted(self.indices,[start,stop])
        removed=int(right-left)
        delta=-int(self.prefix[right]-self.prefix[left])
        if removed and right<len(self.indices):
            prev=int(self.indices[left-1]) if left else -1
            merged=int(self.indices[right])-prev-1
            old_q=int(self.runs[right])>>self.kr;new_q=merged>>self.kr
            old_bits=old_q+1+self.kr if old_q<15 else 39
            new_bits=new_q+1+self.kr if new_q<15 else 39
            delta+=new_bits-old_bits
        bits=self.bits+delta
        assert bits>=0
        return dict(removed_tokens=removed,delta_bits=delta,new_bits=bits,
                    old_stream_bytes=2+(self.bits+7)//8,new_stream_bytes=2+(bits+7)//8,
                    delta_stream_bytes=(bits+7)//8-(self.bits+7)//8,
                    work=dict(binary_searches=2,prefix_difference_reads=2,neighbor_run_replacements=int(bool(removed and right<len(self.indices))),
                              source_coefficient_reads=0,parameter_reselection=False))


def full_bits(sequence,kr,kv):
    """Independent full recount under declared parameters, for verification."""
    seq=np.asarray(sequence);idx=np.flatnonzero(seq)
    runs=np.diff(np.r_[-1,idx])-1;levels=e.ec.f._mapped(seq[idx])-1
    return int((rice_bits(runs,kr,24)+rice_bits(levels,kv,12)).sum())
