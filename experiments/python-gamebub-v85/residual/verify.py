#!/usr/bin/env python3
"""Independently audit retained components; no encoder import or execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out);return out


def main():
    index=json.loads((HERE/'index.json').read_text())
    assert index['record_count']==457 and index['cohort_counts']==[119,119,119,100]
    for name,digest in index['source_sha256'].items():
        assert sha(ROOT/name)==digest,('source',name)
    native=module('cu85_audit_native',ROOT/'experiments/python-gamebub-v82/native/data.py')
    data=module('cu85_audit_data',HERE/'data.py')
    totals={str(cap):dict(AB38_bytes=0,chunks=0,raw_chunks=0,max_chunk_bytes=0) for cap in data.CAPS}
    count=0
    for frame,original in zip(data.iter_frames(),native.iter_frames(),strict=True):
        for name in ('cohort','ordinal','fid','refid','key','packet_sha256','canonical_sha256','hud_sha256','display_sha256'):
            assert frame[name]==original[name]
        assert frame['zero_mask']==''.join(str(v) for v in original['zero_coeff_mask'])
        assert len(frame['qmap'])==338 and hashlib.sha256(frame['hud']).hexdigest()==original['encoded_hud_sha256']
        residual=[sum(not h and (frame['key'] or not z) for h,z in zip(original['hidden_mask'][a:b],original['zero_coeff_mask'][a:b])) for a,b in ((0,5400),(5400,6750),(6750,8100))]
        assert frame['residual_counts']==residual
        for cap,planes in frame['variants'].items():
            stats=dict(AB38_bytes=0,chunks=0,raw_chunks=0,max_chunk_bytes=0)
            for axis,chunks in enumerate(planes):
                assert sum(c['blocks'] for c in chunks)==residual[axis]
                assert len(chunks)==(residual[axis]+int(cap)-1)//int(cap)
                for i,c in enumerate(chunks):
                    assert c['blocks']==min(int(cap),residual[axis]-i*int(cap))
                    p=c['data'];header=struct.unpack_from('<4sBBIHH4I3I',p)
                    assert header[:2]==(b'AB38',1) and header[2] in (0,1)
                    assert header[3:6]==(c['blocks'],1,0)
                    assert len(p)==46+sum(header[6:10])
                    assert zlib.crc32(p[:-4])==struct.unpack('<I',p[-4:])[0]
                    stats['AB38_bytes']+=len(p);stats['chunks']+=1;stats['raw_chunks']+=header[2];stats['max_chunk_bytes']=max(stats['max_chunk_bytes'],len(p))
            assert all(frame['variant_stats'][cap][k]==v for k,v in stats.items())
            for k,v in stats.items():
                totals[cap][k]=max(totals[cap][k],v) if k=='max_chunk_bytes' else totals[cap][k]+v
        count+=1
    assert count==457 and totals==index['totals']
    result=dict(schema='cu66-v85-residual-retained-audit-v1',status='PASS',records=count,totals=totals,
                source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str((HERE/'index.json').relative_to(ROOT)):sha(HERE/'index.json')},
                scope='Retained structure/count/source/native-zero-mask audit; generated coefficients were independently decoded in native collector and whole-frame receiver qualification is separate.')
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('V85_RESIDUAL_RETAINED_PASS frames=457 caps=4')


if __name__=='__main__':main()
