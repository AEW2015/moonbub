#!/usr/bin/env python3
"""Offline source-pixel, reference, candidate-selection and block-stream replay."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import zlib
import numpy as np
import model as m
import protocol as p

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('unified27_verify_helpers',HERE/'benchmark.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)


def raw(d,folder=HERE):
    q=Path(d['path']);assert not q.is_absolute() and '..' not in q.parts
    assert type(d['raw_bytes']) is int and 0<d['raw_bytes']<=1000000
    stored=(folder/q).read_bytes();assert hashlib.sha256(stored).hexdigest()==d['stored_sha256']
    decoder=zlib.decompressobj();out=decoder.decompress(stored,d['raw_bytes']+1)
    assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(out)==d['raw_bytes']
    assert hashlib.sha256(out).hexdigest()==d['raw_sha256'];return out


def main():
    data=b.load(HERE/'results.json');assert data['schema']=='gamebub-unified-v27'
    for name,sha in data['source_sha256'].items():
        q=Path(name);assert not q.is_absolute() and '..' not in q.parts
        assert hashlib.sha256((ROOT/q).read_bytes()).hexdigest()==sha,name
    inputs=b.load(b.n.V24/'results.json')['inputs'];priors=b.load(b.OLD/'full_results.json')['cases']
    pairs=attempts=words=stream_blocks=0
    for case in data['cases']:
        inp=next(x for x in inputs if x['scene']==case['scene']);prior=next(x for x in priors if x['scene']==case['scene'])
        rx=p.Receiver(epoch=25);ref=None;slot=0;refid=m.NO_REF
        assert [r['id'] for r in case['rows']]==list(range(48))
        for r,src,old in zip(case['rows'],inp['rows'],prior['rows']):
            fid=r['id'];key=fid%24==0
            if key:ref=None;refid=m.NO_REF;slot=0
            assert r['key']==key and r['reference_id']==refid and r['source_slot']==(255 if key else slot)
            assert r['destination_slot']==(0 if key else 1-slot)
            original=b.n.original(src);selected=[a for a in r['attempts'] if a['selected']];assert len(selected)==1
            for a in r['attempts']:
                bp=raw(a['base_packet']);pair=raw(a['packet'])
                assert len(bp)==a['base_bytes'] and len(pair)==a['complete_bytes']==len(bp)+r['hud_bytes']+60
                assert a['cap_fit']==(len(pair)<=p.CAP)
                decoded,meta=m.decode(bp,ref,expected_epoch=25,expected_reference_id=None if key else refid)
                bare=m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded))
                hybrid=b.n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in b.n.RECTS))
                metric=b.n.metric(original,hybrid)
                assert metric==a['hybrid'] and b.n.digest(hybrid)==a['hybrid_rgb565_sha256']
                assert b.n.digest(bare)==a['bare_rgb565_sha256'] and meta['reconstructed_tag'].hex()==a['reconstructed_tag']
                q=m.roi.declared_map(720,480,b.n.ROIS,8,a['background']);np.testing.assert_array_equal(meta['scale_map'],q)
                if a['kind']=='zero':assert not np.any(meta['vectors'])
                assert meta['block_size']==32
                if not a['cap_fit']:
                    state=rx.last_frame_id
                    try:rx.receive(pair)
                    except ValueError:pass
                    else:raise AssertionError('overcap accepted')
                    assert rx.last_frame_id==state
                attempts+=1
            if case['policy']=='unified_causal':
                backgrounds=sorted({a['background'] for a in r['attempts']});assert backgrounds in ([16],[16,32])
                chosen=None
                for bg in backgrounds:
                    group=[a for a in r['attempts'] if a['background']==bg]
                    assert [a['kind'] for a in group]==(['zero'] if key else ['zero','half32'])
                    threshold=group[0]['hybrid']['active_squared_error']
                    for a in group:assert a['quality_eligible']==(a['hybrid']['active_squared_error']<=threshold)
                    eligible=[a for a in group if a['cap_fit'] and a['quality_eligible']]
                    if eligible:chosen=min(eligible,key=lambda a:a['complete_bytes']);break
                assert chosen==selected[0]
            else:
                assert len(r['attempts'])==1 and r['selected_kind']==old['selected_kind'] and r['selected_background']==old['selected_background']
                assert r['hybrid_rgb565_sha256']==old['hybrid_rgb565_sha256'] and r['reconstructed_tag']==old['reconstructed_tag']
                assert r['body_bytes']<=old['body_bytes']
            pair=raw(r['packet']);base=raw(r['base_packet']);hud=raw(r['hud_packet'],ROOT/r['hud_packet']['directory'])
            meta=p.parse_pair(pair);assert meta['base']==base and meta['hud']==hud
            decoded,patches,ack=rx.receive(pair);assert ack==raw(r['ack']);p.validate_ack(ack,pair)
            for v,(x,y,w,h) in zip(patches,b.n.RECTS):np.testing.assert_array_equal(v['words'],original[y:y+h,x:x+w]);words+=w*h
            hybrid=b.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),tuple(v['words'] for v in patches))
            assert b.n.digest(hybrid)==r['hybrid_rgb565_sha256'] and b.n.metric(original,hybrid)==r['hybrid']
            assert r['base_bytes']+r['hud_bytes']+60==r['body_bytes']==len(pair)<=49152
            assert selected[0]['packet']==r['packet'] and selected[0]['base_packet']==r['base_packet']
            paid=sum(a['analysis_wall_ms'] for a in r['analyses'].values())+sum(a['encode_ms'] for a in r['attempts'])
            assert abs(paid-r['paid_base_encode_ms'])<1e-8
            parsed=m.parse(base);fields=m.HEADER.unpack_from(base);pos=m.HEADER.size+fields[-5]+fields[-4]
            for plane,(size,coeff) in enumerate(zip(fields[-3:],parsed['coefficients'])):
                section=base[pos:pos+size];pos+=size
                if section[0]==3:
                    bw=((720 if plane==0 else 360)+7)//8
                    count=0
                    for expected,actual in zip(coeff,m.ec.iter_block_major(section[1:],len(coeff),bw)):
                        assert np.array_equal(expected,actual);count+=1
                    assert count==len(coeff);stream_blocks+=count
            pairs+=1;ref,refid,slot=decoded,fid,0 if key else 1-slot
        assert b.summarize(case['rows'],prior)==case['summary']
    assert pairs==192 and words==192*21120
    print(json.dumps(dict(source_pins=len(data['source_sha256']),accepted_pairs=pairs,actual_candidate_attempts=attempts,
                          exact_hud_words=words,streamed_coefficient_blocks=stream_blocks,
                          causal_selection_replayed=True,frozen_trace_pixels_exact=True,native_FPGA_or_physical_30fps_proven=False)))


if __name__=='__main__':main()
