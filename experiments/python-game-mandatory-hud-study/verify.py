#!/usr/bin/env python3
"""Retained mandatory-HUD evidence and actual independent golden packet replay."""
from pathlib import Path
import hashlib,json,zlib
import numpy as np
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];C=model.codec

def raw(desc):
    p=Path(desc['path']);assert not p.is_absolute() and '..' not in p.parts
    b=(HERE/p).read_bytes();assert hashlib.sha256(b).hexdigest()==desc['stored_sha256']
    dec=zlib.decompressobj();out=dec.decompress(b,desc['raw_bytes']+1)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(out)==desc['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==desc['raw_sha256'];return out

def array(desc):
    assert desc['dtype'] in ('|u1','<i2','<u2')
    return np.frombuffer(raw(desc['blob']),dtype=desc['dtype']).reshape(desc['shape'])

def check_case(case):
    rows=case['rows'];assert len(rows)==48 and len({r['input_sha256'] for r in rows})==48
    assert [r['id'] for r in rows]==list(range(48))
    for r in rows:
        assert r['state_before']==r['state_after_builds'] and r['readers_before']==r['readers_after']==0
        assert len(r['attempts'])<=(4 if case['policy']=='mandatory' else 1)
        for a in r['attempts']:
            assert a['build_ms']>0 and a['map_ms']>0 and (a['analyze_calls'],a['forward_calls'])==(1,3)
            if not a['accepted']:assert a['discard_ms']>0
        if r['accepted']:
            assert r['packet_bytes']<=49152 and r['selected_word_errors']==0 and r['receiver_readers_after']==0
            assert r['readers_after_builds']==(0 if r['key'] else 1)
            assert r['selected_words']==sum(w*h for _,_,w,h in r['selected_rectangles'])
            assert {tuple(x) for x in r['selected_rectangles']}|{tuple(x) for x in r['omitted_rectangles']}==set(model.RECTANGLES)
            assert r['state_after']['last_issued']==r['id'] and not r['state_after']['pending']
            if case['policy']=='mandatory':
                assert r['selected_words']==21120 and not r['omitted_rectangles']
                assert r['packet_bytes']==C.HEADER.size+4+r['inner_bytes']+r['mandatory_patch_bytes']
                assert r['inner_bytes']<=r['reserved_inner_bytes']
        else:assert r['state_before']==r['state_after']

def main():
    d=json.loads((HERE/'results.json').read_text());assert d['schema']=='gamebub-mandatory-hud-v1'
    for p,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    assert d['counts']==dict(cases=4,source_acquisitions=96,frame_decisions=192,golden_vectors=20)
    vectors=words=negatives=0
    for case in d['cases']:
        check_case(case)
        for v in case['vectors']:
            vectors+=1;rx=C.Receiver();packet=raw(v['packet']);meta=C.identity(packet,decode=True)
            assert len(packet)<=49152 and meta['frame_id']==v['id'] and (meta['width'],meta['height'])==(720,480)
            for k,b in v['pre_banks'].items():
                if b is not None:
                    planes=tuple(array(x) for x in b['planes']);tag=bytes.fromhex(b['tag']);assert C.reference_tag(planes)==tag
                    rx.banks[int(k)]=C.Bank(b['id'],tag,planes)
            rx.last_frame_id=v['id']-1
            before=(rx.last_frame_id,tuple((k,None if b is None else (b.frame_id,b.tag)) for k,b in rx.banks.items()))
            bad=packet[:-1]+bytes([packet[-1]^1])
            try:rx.begin(bad)
            except ValueError:pass
            else:raise AssertionError('corrupt packet accepted')
            assert (rx.last_frame_id,tuple((k,None if b is None else (b.frame_id,b.tag)) for k,b in rx.banks.items()))==before
            assert rx.active is None and not rx.readers;negatives+=1
            task=rx.begin(packet)
            for a,desc in zip(task.planes,v['decoded_yuv']):np.testing.assert_array_equal(a,array(desc))
            rgb,info,ack=rx.complete(task);assert ack==raw(v['ack']) and model.digest(rgb)==v['rgb_sha256']
            display=C.corpus.rgb565(rgb);np.testing.assert_array_equal(display,array(v['display_rgb565']))
            source=C.corpus.rgb565(array(v['source']));selected=0
            for x,y,w,h in v['selected_rectangles']:
                np.testing.assert_array_equal(display[y:y+h,x:x+w],source[y:y+h,x:x+w]);selected+=w*h
            assert selected==v['selected_words'] and info['selected_pixels']==selected;words+=selected
            if case['policy']=='mandatory':assert not v['omitted_rectangles'] and selected==21120
            assert not rx.readers and rx.active is None
            for k,b in v['post_banks'].items():
                got=rx.banks[int(k)];assert (got is None)==(b is None)
                if got is not None:assert (got.frame_id,got.tag.hex())==(b['id'],b['tag'])
    assert vectors==20
    print(json.dumps(dict(cases=4,frame_decisions=192,golden_vectors=vectors,exact_golden_selected_words=words,atomic_negative_rejections=negatives,
        mandatory_full_hud_gate='all accepted frames',native_or_physical_30fps_proven=False),indent=2))
if __name__=='__main__':main()
