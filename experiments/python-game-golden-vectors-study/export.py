#!/usr/bin/env python3
"""Export complete AR02/GF02/AF02 fixtures and canonical golden arrays."""
import hashlib
import json
from pathlib import Path
import struct
import time
import zlib
import numpy as np
import fixtures

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
u=fixtures.codec

def sha(data):return hashlib.sha256(data).hexdigest()

def blob(data,kind,compress=False):
    raw=bytes(data);stored=zlib.compress(raw,9) if compress else raw
    rel='objects/'+sha(raw)+'.'+kind+('.zlib' if compress else '.bin')
    p=HERE/rel;p.parent.mkdir(exist_ok=True);p.write_bytes(stored)
    return dict(path=rel,encoding='zlib' if compress else 'raw',raw_bytes=len(raw),raw_sha256=sha(raw),stored_sha256=sha(stored))

def array(a,kind):
    return dict(blob=blob(a.tobytes(),kind,True),shape=list(a.shape),dtype=a.dtype.str)

def banks(obj):
    return {str(k):None if b is None else dict(id=b.frame_id,tag=b.tag.hex(),planes=[array(np.asarray(p,dtype='<i2'),'yuv16') for p in b.planes]) for k,b in obj.banks.items()}

def metadata(meta):
    return {k: v.hex() if isinstance(v,bytes) else v for k,v in meta.items() if k not in ('inner','parsed','patch_packets','patches')}

def pins():
    old=json.loads((HERE.parent/'python-game-unified-codec-study/results.json').read_text())['source_sha256']
    paths={ROOT/raw.split('/moonbub-30fps-study/',1)[1] for raw in old}
    paths|={HERE/x for x in ('fixtures.py','export.py','verify.py','test_vectors.py')}
    paths.add(Path(fixtures.transport.__file__))
    return {str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(paths)}

def mutate(packet,*,field=None,value=None,inner=None,patches=None):
    f=list(u.HEADER.unpack_from(packet));m=u.identity(packet)
    if field is not None:f[field]=value
    base=m['inner'] if inner is None else inner
    ps=m['patch_packets'] if patches is None else patches
    section=b''.join(struct.pack('<I',len(p))+p for p in ps)
    f[10],f[11],f[12]=len(base),len(ps),len(section)
    return u.seal(u.HEADER.pack(*f)+base+section)

def main():
    source_pins=pins();started=time.perf_counter();out=[];packets={}
    for spec in fixtures.specs():
        enc=fixtures.encoder(spec);rx=u.Receiver(epoch=16);rows=[]
        for request in spec['frames']:
            rgb,d=fixtures.prepare(enc,spec,request);assert d.accepted
            packet=d.packet;packets[(spec['name'],request['id'])]=packet
            before=banks(rx);task=rx.begin(packet)
            planes=[array(np.asarray(p,dtype='<i2'),'yuv16') for p in task.planes]
            decoded,info,ack=rx.complete(task)
            assert enc.ack(ack)
            assert rx.readers==0 and rx.active is None and not enc.pending
            for slot,b in enc.banks.items():
                other=rx.banks[slot];assert (b is None)==(other is None)
                if b is not None:
                    assert (b.frame_id,b.tag)==(other.frame_id,other.tag)
                    for a,c in zip(b.planes,other.planes):assert np.array_equal(a,c)
            chunks=fixtures.transport.datagrams(packet,16,request['id'])
            rows.append(dict(request=request,source_rgb888=array(rgb,'rgb888'),scale_map=array(np.full(u.gm.roi.geometry(spec['width'],spec['height'])[::-1],16,np.uint8),'map'),
                             ar02=blob(packet,'ar02'),gf02=[blob(c,'gf02') for c in chunks],af02=blob(ack,'af02'),
                             identity=metadata(u.identity(packet)),pre_banks=before,decoded_yuv=planes,
                             decoded_rgb888_sha256=sha(decoded.tobytes()),base_rgb888_sha256=info['base_rgb_sha256'],
                             display_rgb565=array(np.asarray(u.corpus.rgb565(decoded),dtype='<u2'),'rgb565'),
                             post_banks=banks(rx),selected_pixels=info['selected_pixels']))
        out.append(dict(spec=spec,rows=rows))
    key=packets[('gm-small-lifecycle',0)];p=packets[('gm-small-lifecycle',1)];meta=u.identity(key)
    patch=meta['patch_packets'][0];badpatch=patch[:-1]+bytes([patch[-1]^1])
    inner=meta['inner'];unsupported=u.seal(b'BAD!'+inner[4:-4])
    negatives=[]
    cases=[('outer-crc',key[:-1]+bytes([key[-1]^1]),[]),('truncated-frame',key[:-1],[]),
           ('patch-crc-resealed-outer',mutate(key,patches=(badpatch,)),[]),
           ('truncated-patch-resealed-outer',mutate(key,patches=(patch[:-1],)),[]),
           ('overlapping-patches',mutate(key,patches=(patch,patch)),[]),
           ('wrong-published-yuv-tag',mutate(key,field=9,value=b'X'*16),[]),
           ('wrong-reference-tag',mutate(p,field=8,value=b'X'*16),[0]),
           ('unsupported-inner-resealed',mutate(key,inner=unsupported),[])]
    for name,data,prefix in cases:
        negatives.append(dict(name=name,target='receiver.begin',cohort='gm-small-lifecycle',prelude_ids=prefix,
                              packet=blob(data,'negative-ar02'),expected='ValueError; banks/last identity/active/readers unchanged'))
    ack=out[0]['rows'][0]['af02'];ackdata=(HERE/ack['path']).read_bytes()
    fields=list(u.FEEDBACK.unpack_from(ackdata))
    for name,index,value in [('feedback-wrong-outer-crc',5,u.body_crc(meta['inner'])),('feedback-wrong-stored-tag',8,b'X'*16)]:
        modified=fields.copy();modified[index]=value
        negatives.append(dict(name=name,target='encoder.ack',cohort='gm-small-lifecycle',prelude_ids=[],pending_id=0,
                              packet=blob(u.seal(u.FEEDBACK.pack(*modified)),'negative-af02'),expected='ValueError; pending and banks unchanged; original ACK still succeeds'))
    assert source_pins==pins()
    result=dict(schema='gamebub-ar02-golden-v1',epoch=16,source_sha256=source_pins,cohorts=out,negative_vectors=negatives,
                counts=dict(cohorts=len(out),positive_frames=sum(len(c['rows']) for c in out),negative_vectors=len(negatives),
                            gf02_datagrams=sum(len(r['gf02']) for c in out for r in c['rows']),
                            selected_ui_words=sum(r['selected_pixels'] for c in out for r in c['rows'])),
                elapsed_python_seconds=time.perf_counter()-started,
                scope='Deterministic synthetic golden interoperability fixtures, not compression quality/live30fps/FPGA fit or independent decoder implementation. Array bytes canonical little endian; zlib storage is offline fixture packaging, never wire codec.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['counts'],indent=2))

if __name__=='__main__':main()
