#!/usr/bin/env python3
"""Replay retained AR03 wire/arrays and exact entropy traces; no source video needed."""
import hashlib,json,struct,zlib
from pathlib import Path
import numpy as np
import trace_codec as t
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def raw(desc):
    p=Path(desc['path'])
    assert not p.is_absolute() and '..' not in p.parts
    stored=(HERE/p).read_bytes();assert hashlib.sha256(stored).hexdigest()==desc['stored_sha256']
    if desc['encoding']=='zlib':
        dec=zlib.decompressobj();data=dec.decompress(stored,desc['raw_bytes']+1)
        assert dec.eof and not dec.unused_data and not dec.unconsumed_tail
    else:assert desc['encoding']=='raw';data=stored
    assert len(data)==desc['raw_bytes'] and hashlib.sha256(data).hexdigest()==desc['raw_sha256']
    return data

def array(desc):
    assert desc['dtype'] in ('|u1','<u2','<i2')
    return np.frombuffer(raw(desc['blob']),dtype=desc['dtype']).reshape(desc['shape'])
def bankcheck(r,expected):
    for slot in (0,1):
        b=r.banks[slot];want=expected[str(slot)]
        assert (b is None)==(want is None)
        if b is not None:
            assert b.frame_id==want['id'] and b.tag.hex()==want['tag']
            assert t.codec.reference_tag(b.planes)==b.tag
            for got,desc in zip(b.planes,want['planes']):np.testing.assert_array_equal(got,array(desc))
def semantic(r):
    return r.last_frame_id,r.active,r.readers,tuple((k,None if b is None else (b.frame_id,b.tag,tuple(hashlib.sha256(p.tobytes()).hexdigest() for p in b.planes))) for k,b in r.banks.items())
def main():
    d=json.loads((HERE/'results.json').read_text());assert d['schema']=='gamebub-ar03-exact-traces-v1'
    for path,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h,path
    frames=datagrams=words=blocks=negative=0;formats=set();peak=0
    for c in d['cohorts']:
        r=t.codec.Receiver(epoch=18);ingress=t.transport.Reassembler(epoch=18);previous=None
        for row in c['rows']:
            frames+=1;bankcheck(r,row['pre_banks']);packet=raw(row['ar03']);trace=t.parse_packet(packet)
            assert trace==json.loads(raw(row['trace']));formats.add(trace['inner_codec'])
            # Negative operations use exact positive precondition and no active owner.
            bads=[packet[:-1],packet[:-1]+bytes([packet[-1]^1])]
            fields=list(t.codec.HEADER.unpack_from(packet))
            if fields[2]:
                f=fields.copy();f[9]=b'X'*16;bads.append(t.codec.seal(t.codec.HEADER.pack(*f)+packet[t.codec.HEADER.size:-4]))
            if fields[2]!=t.codec.KEY:
                f=fields.copy();f[8]=b'Y'*16;bads.append(t.codec.seal(t.codec.HEADER.pack(*f)+packet[t.codec.HEADER.size:-4]))
            for bad in bads:
                before=semantic(r)
                try:r.begin(bad)
                except ValueError:pass
                else:raise AssertionError('negative AR03 accepted')
                assert semantic(r)==before;negative+=1
            complete=None
            for part in reversed(row['gf02']):
                datagrams+=1;value=ingress.feed(raw(part),row['id']*10)
                if value is not None:complete=value
            assert complete is not None and complete.data==packet
            task=r.begin(complete.data)
            for got,desc in zip(task.planes,row['decoded_yuv']):np.testing.assert_array_equal(got,array(desc))
            rgb,info,ack=r.complete(task);ingress.commit(complete)
            assert ack==raw(row['af03']);assert hashlib.sha256(rgb.tobytes()).hexdigest()==row['rgb888_sha256']
            assert info['base_rgb_sha256']==row['base_rgb888_sha256']
            display=t.codec.corpus.rgb565(rgb);np.testing.assert_array_equal(display,array(row['display_rgb565']))
            original=t.codec.corpus.rgb565(array(row['source_rgb888']));selected=0
            for p in t.codec.identity(packet,decode=True)['patches']:
                x,y,w,h=p['rect'];np.testing.assert_array_equal(original[y:y+h,x:x+w],display[y:y+h,x:x+w]);selected+=w*h
            assert selected==row['selected_pixels']==trace['selected_ui_pixels'];words+=selected;bankcheck(r,row['post_banks'])
            for plane in trace['planes']:
                for stripe in plane['stripes']:
                    blocks+=stripe['block_count'];assert stripe['zero']+stripe['dc']+stripe['general']==stripe['block_count']
                    for rec in stripe['blocks']:
                        entry=rec.get('compact_cp02',rec);peak=max(peak,entry.get('reservoir_peak_bits',0))
            assert r.readers==0 and r.active is None and not ingress.pending
    count=d['counts'];assert frames==count['frames']==16 and datagrams==count['gf02_datagrams']
    assert words==count['selected_ui_words']==12*21120 and blocks==count['coefficient_blocks']
    assert formats=={'GM01','SR01'} and peak<=64
    files=list((HERE/'objects').iterdir());assert len(files)==count['objects'] and sum(p.stat().st_size for p in files)==count['stored_object_bytes']
    print(json.dumps(dict(frames=frames,gf02_datagrams=datagrams,exact_source_ui_words=words,coefficient_blocks=blocks,
        negative_atomic_rejections=negative,formats=sorted(formats),peak_single_reservoir_bits=peak,
        physical_or_native_30fps_proven=False),indent=2))
if __name__=='__main__':main()
