#!/usr/bin/env python3
"""Offline integrity and independent receiver replay for the bounded V40 key probe."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def digest(b):return hashlib.sha256(b).hexdigest()
def read_object(folder,desc):
    packed=(folder/desc['path']).read_bytes();assert digest(packed)==desc['stored_sha256']
    d=zlib.decompressobj();raw=d.decompress(packed,desc['raw_bytes']+1)
    assert d.eof and not d.unused_data and not d.unconsumed_tail and len(raw)==desc['raw_bytes']
    assert digest(raw)==desc['raw_sha256'];return raw

def main():
    h=module('helpers',ROOT/'experiments/python-game-integrated-v38-study/helpers.py')
    decoder=module('keycap_v40_independent_decoder',ROOT/'experiments/python-game-implicit-v37-study/verify.py')
    data=json.loads((HERE/'results.json').read_text())
    for path,expected in data['source_pins_sha256'].items():
        assert digest((ROOT/path).read_bytes())==expected,path
    source_manifest=json.loads((ROOT/'experiments/python-game-source-v40-study/manifest.json').read_text())
    assert len(data['cases'])==len(source_manifest['cases'])==4
    frames=0
    for case,src_case in zip(data['cases'],source_manifest['cases'],strict=True):
        assert case['scene']==Path(src_case['media_file']).stem
        assert case['frame_id']==0 and case['media_sha256_before']==case['media_sha256_after']
        src=src_case['frames'][0]
        assert case['source_canvas_rgb_sha256']==src['canvas_rgb_sha256']
        assert case['source_rgb565_sha256']==src['rgb565_sha256']
        canvas=np.frombuffer(read_object(ROOT/'experiments/python-game-source-v40-study',src['canvas_rgb24']),np.uint8).reshape(480,720,3).copy()
        original=h.m.C.corpus.rgb565(canvas).astype(np.uint16)
        assert digest(np.ascontiguousarray(original,dtype='<u2').tobytes())==case['source_rgb565_sha256']
        rects=tuple(h.n.RECTS);patches=tuple(np.ascontiguousarray(original[y:y+hh,x:x+ww],dtype=np.uint16) for x,y,ww,hh in rects)
        assert len(case['configs'])==2
        for cfg in case['configs']:
            assert cfg['roi']==8 and cfg['background'] in (16,32) and cfg['complete_cap']==49152
            hudbytes=read_object(HERE,cfg['hud_packets']['HX33_selected'])
            assert len(hudbytes)==cfg['hud_packets']['HX33_selected']['raw_bytes']
            assert cfg['hud_packets']['HU25']['raw_bytes']>0 and cfg['hud_packets']['HX32']['raw_bytes']>0
            assert cfg['cap_fit'] and cfg['encode_error'] is None
            packet=read_object(HERE,cfg['packet']);assert len(packet)==cfg['complete_bytes']<=49152
            assert cfg['base_bytes']+cfg['hud_bytes']+cfg['binding_bytes']==cfg['complete_bytes']
            assert cfg['hud_bytes']==len(hudbytes)==cfg['hud_packets']['HX33_selected']['raw_bytes']
            rx=decoder.Receiver();decoded,got_hud,meta=rx.receive(packet)
            assert meta['key'] and meta['frame_id']==0 and meta['reference_id']==decoder.m.NO_REF
            assert len(got_hud)==4 and sum(v['words'].size for v in got_hud)==21120
            for got,want,rect in zip(got_hud,patches,rects,strict=True):
                assert tuple(got['rect'])==rect;np.testing.assert_array_equal(got['words'],want)
            display=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded))
            display=h.n.overlay(display,tuple(v['words'] for v in got_hud))
            quality=h.n.metric(original,display)
            assert quality==cfg['quality'] and quality['hud_word_errors']==0
            assert h.m.C.reference_tag(decoded).hex()==cfg['normalized_tag']
            frames+=1
    assert frames==8
    print(json.dumps(dict(independent_key_packet_replays=frames,exact_hud_words=21120*frames,
                          all_fit=True,all_source_pins_match=True,all_source_hashes_match=True)))
if __name__=='__main__':main()
