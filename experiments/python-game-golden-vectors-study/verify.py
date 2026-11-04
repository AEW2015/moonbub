#!/usr/bin/env python3
"""Replay golden wire bytes against canonical arrays; never calls the exporter."""
import hashlib
import json
from pathlib import Path
import struct
import zlib
import numpy as np
import fixtures

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
u=fixtures.codec

def sha(data):return hashlib.sha256(data).hexdigest()

def read_blob(desc):
    path=Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:raise ValueError('fixture relative path')
    stored=(HERE/path).read_bytes();assert sha(stored)==desc['stored_sha256']
    assert desc['encoding'] in ('zlib','raw')
    raw=zlib.decompress(stored) if desc['encoding']=='zlib' else stored
    assert len(raw)==desc['raw_bytes'] and sha(raw)==desc['raw_sha256']
    return raw

def read_array(desc):
    dtype=np.dtype(desc['dtype']);assert dtype.str in ('|u1','<u2','<i2')
    a=np.frombuffer(read_blob(desc['blob']),dtype=dtype)
    return a.reshape(desc['shape'])

def snapshot(rx):
    return dict(last=rx.last_frame_id,readers=rx.readers,active=rx.active,
                banks={str(k):None if b is None else (b.frame_id,b.tag.hex(),tuple(sha(np.asarray(p,dtype='<i2').tobytes()) for p in b.planes)) for k,b in rx.banks.items()})

def check_banks(rx,expected):
    for key,bank in expected.items():
        actual=rx.banks[int(key)]
        assert (actual is None)==(bank is None)
        if bank is None:continue
        assert (actual.frame_id,actual.tag.hex())==(bank['id'],bank['tag'])
        for a,b in zip(actual.planes,bank['planes']):np.testing.assert_array_equal(a,read_array(b))
        h,w=actual.planes[0].shape
        canonical=struct.pack('<HH',w,h)+b''.join(np.asarray(p,dtype='<i2').tobytes() for p in actual.planes)
        assert hashlib.sha256(canonical).digest()[:16]==actual.tag

def load():
    data=json.loads((HERE/'results.json').read_text())
    assert data['schema']=='gamebub-ar02-golden-v1' and data['epoch']==16
    return data

def check_positive(data):
    frames=chunks=selected=0;formats=set();lifecycle=set()
    for cohort in data['cohorts']:
        rx=u.Receiver(epoch=data['epoch']);ingress=fixtures.transport.Reassembler(epoch=data['epoch'])
        spec=cohort['spec']
        for row in cohort['rows']:
            frame_id=row['request']['id'];packet=read_blob(row['ar02']);check_banks(rx,row['pre_banks'])
            source=read_array(row['source_rgb888'])
            np.testing.assert_array_equal(source,fixtures.image(spec['kind'],frame_id,spec['width'],spec['height']))
            assert row['scale_map']['shape']==list(u.gm.roi.geometry(spec['width'],spec['height'])[::-1])
            assert np.all(read_array(row['scale_map'])==16)
            meta=u.identity(packet,epoch=data['epoch'],decode=True)
            expected={k:v.hex() if isinstance(v,bytes) else v for k,v in meta.items() if k not in ('inner','parsed','patches','patch_packets')}
            assert expected==row['identity']
            formats.add(meta['inner_codec']);lifecycle.add('key' if meta['key'] else 'promotion' if meta['promoted'] else 'P')
            expected_chunks=fixtures.transport.datagrams(packet,data['epoch'],frame_id)
            complete=None
            for n,desc in enumerate(row['gf02']):
                datagram=read_blob(desc);assert datagram==expected_chunks[n]
                delivered=ingress.feed(datagram,frame_id*10+n/1000)
                if delivered is not None:assert complete is None;complete=delivered
                chunks+=1
            assert len(row['gf02'])==len(expected_chunks) and complete is not None and complete.data==packet
            before=snapshot(rx);task=rx.begin(complete.data)
            assert rx.last_frame_id==before['last']
            check_banks(rx,row['pre_banks'])
            assert rx.readers==(0 if meta['key'] else 1)
            for a,b in zip(task.planes,row['decoded_yuv']):np.testing.assert_array_equal(a,read_array(b))
            rgb,info,ack=rx.complete(task);ingress.commit(complete)
            assert ack==read_blob(row['af02']) and sha(rgb.tobytes())==row['decoded_rgb888_sha256']
            assert info['base_rgb_sha256']==row['base_rgb888_sha256']
            np.testing.assert_array_equal(u.corpus.rgb565(rgb),read_array(row['display_rgb565']))
            assert info['selected_pixels']==row['selected_pixels']
            for patch in meta['patches']:
                x,y,w,h=patch['rect']
                np.testing.assert_array_equal(patch['words'],u.corpus.rgb565(source[y:y+h,x:x+w]))
            check_banks(rx,row['post_banks']);assert rx.active is None and rx.readers==0 and not ingress.pending
            selected+=row['selected_pixels'];frames+=1
    assert formats=={'GM01','SR01'} and lifecycle=={'key','P','promotion'}
    return dict(positive_frames=frames,gf02_datagrams=chunks,selected_ui_words=selected,actual_inner_formats=sorted(formats))

def check_negative(data):
    cohorts={c['spec']['name']:c for c in data['cohorts']}
    counts={'receiver':0,'feedback':0}
    for case in data['negative_vectors']:
        cohort=cohorts[case['cohort']];rows={r['request']['id']:r for r in cohort['rows']}
        bad=read_blob(case['packet'])
        if case['target']=='receiver.begin':
            rx=u.Receiver(epoch=data['epoch'])
            for index in case['prelude_ids']:rx.receive(read_blob(rows[index]['ar02']))
            before=snapshot(rx)
            try:rx.begin(bad)
            except ValueError:pass
            else:raise AssertionError(case['name']+' accepted')
            assert snapshot(rx)==before,case['name'];counts['receiver']+=1
        elif case['target']=='encoder.ack':
            enc=fixtures.encoder(cohort['spec']);row=rows[case['pending_id']]
            _,decision=fixtures.prepare(enc,cohort['spec'],row['request'])
            assert decision.packet==read_blob(row['ar02'])
            before=(enc.banks.copy(),dict(enc.pending),enc.last_issued,enc._generation)
            try:enc.ack(bad)
            except ValueError:pass
            else:raise AssertionError(case['name']+' accepted')
            assert before==(enc.banks,enc.pending,enc.last_issued,enc._generation)
            assert enc.ack(read_blob(row['af02'])) and not enc.pending;counts['feedback']+=1
        else:raise ValueError('negative target')
    assert counts=={'receiver':8,'feedback':2}
    return counts

def check_lifecycle(data):
    cohort=next(c for c in data['cohorts'] if c['spec']['name']=='gm-small-lifecycle')
    rows=cohort['rows'];rx=u.Receiver(epoch=16)
    for row in rows[:3]:rx.receive(read_blob(row['ar02']))
    before=snapshot(rx);task=rx.begin(read_blob(rows[3]['ar02']));assert rx.readers==1
    rx.abort(task);assert snapshot(rx)==before
    try:rx.complete(task)
    except ValueError:pass
    else:raise AssertionError('aborted task completed')
    rx.receive(read_blob(rows[3]['ar02']))
    lease=rx.acquire(1)
    try:rx.begin(read_blob(rows[4]['ar02']))
    except ValueError:pass
    else:raise AssertionError('key replaced read-owned bank')
    assert rx.readers==1 and rx.active is None
    rx.release(lease);rx.receive(read_blob(rows[4]['ar02']));assert rx.readers==0 and rx.active is None
    return True

def verify():
    d=load()
    for rel,expected in d['source_sha256'].items():assert sha((ROOT/rel).read_bytes())==expected,rel
    positive=check_positive(d);negative=check_negative(d);assert check_lifecycle(d)
    assert positive['positive_frames']==d['counts']['positive_frames']==10
    assert positive['gf02_datagrams']==d['counts']['gf02_datagrams']
    assert positive['selected_ui_words']==d['counts']['selected_ui_words']==768
    return dict(schema=d['schema'],source_bindings=len(d['source_sha256']),**positive,negative_rejections=negative,
                abort_retry_and_read_owned_key='passed',physical_30fps_proven=False)

if __name__=='__main__':print(json.dumps(verify(),indent=2))
