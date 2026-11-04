#!/usr/bin/env python3
"""Independent scalar HD22 decoding and all retained-sequence byte checks."""
from pathlib import Path
import hashlib
import json
import struct
import zlib
import numpy as np
import benchmark as b
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def scalar_decode(packet,reference):
    # Intentionally does not call model.inspect/model.decode or model span code.
    fmt=struct.Struct('<4sBBHHI16s16s')
    assert 50<=len(packet)<=42290
    magic,version,mode,w,h,n,reftag,newtag=fmt.unpack_from(packet)
    assert (magic,version)==(b'HD22',1) and mode in (0,1,2)
    assert 0<w<=720 and 0<h<=480 and w*h<=21120 and n<=42240
    assert len(packet)==50+n and zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
    def tag(words):return hashlib.sha256(struct.pack('<HH',w,h)+struct.pack('<'+'H'*len(words),*words)).digest()[:16]
    data=packet[fmt.size:-4]
    if mode==0:
        assert reftag==bytes(16) and n==2*w*h
        words=list(struct.unpack('<'+'H'*(w*h),data))
    else:
        assert reference is not None and reference.shape==(h,w)
        words=[int(x) for x in reference.flat]
        assert tag(words)==reftag
        if mode==1:assert n==0
        else:
            count=struct.unpack_from('<H',data)[0];assert 0<count<=w*h
            pos=2;last_y=-1;last_end=-1
            for _ in range(count):
                y,x,length=struct.unpack_from('<HHH',data,pos);pos+=6
                assert y<h and 0<length<=w and x+length<=w and y>=last_y
                if y==last_y:assert x-last_end>=3
                values=struct.unpack_from('<'+'H'*length,data,pos);pos+=2*length
                assert values[0] and values[-1]
                gap=0
                for i,value in enumerate(values):
                    gap=gap+1 if value==0 else 0;assert gap<3
                    words[y*w+x+i]^=value
                last_y,last_end=y,x+length
            assert pos==n
    assert tag(words)==newtag
    return np.asarray(words,dtype=np.uint16).reshape(h,w)


def main():
    d=json.loads((HERE/'results.json').read_text())
    assert d['schema']=='gamebub-gap-span-v22'
    for p,h in d['source_sha256'].items():assert b.sha(ROOT/p)==h,p
    old=json.loads((b.OLD/'results.json').read_text())
    words=patches=negatives=0
    for oldcase,case in zip(old['cases'],d['cases']):
        assert oldcase['name']==case['name']
        current_state=None;totals=[0,0]
        # This replay evaluates the full legacy compressor too: retained sizes
        # alone cannot stand in for paid current-candidate work.
        rebuilt,_=b.process_case(oldcase)
        for k,v in case['summary'].items():
            if k.startswith('mean_'):continue
            assert rebuilt['summary'][k]==v,(case['name'],k)
        for source,row in zip(oldcase['rows'],case['rows']):
            arrays=b.arrays(source)
            for i,(cur,detail) in enumerate(zip(arrays,row['patches'])):
                ref=None if current_state is None else current_state[i]
                packet=m.encode(cur,ref)
                assert hashlib.sha256(packet).hexdigest()==detail['hd22_sha256']
                np.testing.assert_array_equal(scalar_decode(packet,ref),cur)
                assert len(packet)==detail['hd22_bytes']<=detail['hd21_bytes']
                patches+=1;words+=cur.size
            current_state=tuple(a.copy() for a in arrays)
            assert row['hc21_bytes']==source['sidecar_bytes']
            assert row['proposed_same_overhead_bytes']==83+sum(p['selected_bytes'] for p in row['patches'])
            assert row['proposed_same_overhead_bytes']<=row['hc21_bytes']
    golden_words=0
    for v in d['goldens']:
        cur=np.frombuffer(b.raw(v['current'],HERE),dtype='<u2').reshape(v['shape'])
        ref=None if v['reference'] is None else np.frombuffer(b.raw(v['reference'],HERE),dtype='<u2').reshape(v['shape'])
        packet=b.raw(v['packet'],HERE)
        np.testing.assert_array_equal(scalar_decode(packet,ref),cur);golden_words+=cur.size
        corrupt=packet[:-1]+bytes([packet[-1]^1])
        try:scalar_decode(corrupt,ref)
        except AssertionError:negatives+=1
        else:raise AssertionError('corrupt golden accepted')
    assert patches==528 and words==2787840
    print(json.dumps(dict(patch_decisions=patches,updates=132,independent_scalar_words=words,
                          native_updates=96,synthetic_updates=36,golden_vectors=len(d['goldens']),
                          golden_words=golden_words,crc_negatives=negatives,
                          source_pins=len(d['source_sha256']),physical_30fps_proven=False),indent=2))


if __name__=='__main__':main()
