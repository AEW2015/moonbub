#!/usr/bin/env python3
"""Offline causal replay, source integrity and cap verification."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];V40=ROOT/'experiments/python-game-source-v40-study'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
    packed=(folder/d['path']).read_bytes();assert digest(packed)==d['stored_sha256']
    z=zlib.decompressobj();out=z.decompress(packed,d['raw_bytes']+1)
    assert z.eof and not z.unused_data and not z.unconsumed_tail and len(out)==d['raw_bytes']
    assert digest(out)==d['raw_sha256'];return out
def main():
    h=module('helpers',ROOT/'experiments/python-game-integrated-v38-study/helpers.py')
    decoder=module('control_qual_independent_receiver',ROOT/'experiments/python-game-implicit-v37-study/verify.py')
    result=json.loads((HERE/'results.json').read_text());manifest=json.loads((V40/'manifest.json').read_text())
    for path,want in result['source_pins_sha256'].items():assert digest((ROOT/path).read_bytes())==want,path
    assert len(result['cases'])==len(manifest['cases'])==4
    nframes=naccepted=nrejected=ntries=0
    for case,source_case in zip(result['cases'],manifest['cases'],strict=True):
        scene=Path(source_case['media_file']).stem
        assert case['scene']==scene and case['media_sha256_before']==case['media_sha256_after']==source_case['media_sha256_before']
        frames=source_case['frames'];rows=case['rows'];assert len(rows)==len(frames)
        assert [r['id'] for r in rows]==list(range(len(frames)))
        rx=decoder.Receiver();last_accepted=None
        for src,row in zip(frames,rows,strict=True):
            fid=src['id'];assert row['pts']==src['pts'] and row['time_base']==src['time_base']
            assert row['timestamp_fraction']==src['timestamp_fraction'] and row['decoded_order']==src['decoded_order']
            assert row['source_rgb_sha256']==src['canvas_rgb_sha256'] and row['source_rgb565_sha256']==src['rgb565_sha256']
            key=(fid%24==0 or last_accepted is None);rid=decoder.m.NO_REF if key else last_accepted
            assert row['requested_key']==key and row['reference_id']==rid and row['previous_accepted_id']==last_accepted
            assert [a['background'] for a in row['attempts']]==([16] if row['accepted'] and row['attempts'][0]['accepted_candidate'] else [16,32]) or (len(row['attempts'])==1 and not row['accepted'])
            canvas=np.frombuffer(raw(V40,src['canvas_rgb24']),np.uint8).reshape(480,720,3).copy()
            assert digest(canvas.tobytes())==row['source_rgb_sha256']
            original=h.m.C.corpus.rgb565(canvas).astype(np.uint16)
            assert digest(np.ascontiguousarray(original,dtype='<u2').tobytes())==row['source_rgb565_sha256']
            rects=tuple(h.n.RECTS);patches=tuple(np.ascontiguousarray(original[y:y+hh,x:x+ww],dtype=np.uint16) for x,y,ww,hh in rects)
            assert row['hud_bytes']==row['hud_packets']['HX33_selected']['raw_bytes']
            for desc in row['hud_packets'].values():raw(HERE,desc)
            ntries+=len(row['attempts'])
            for i,attempt in enumerate(row['attempts']):
                assert attempt['roi']==8 and attempt['background'] in (16,32)
                assert attempt['hud_bytes']==row['hud_bytes']
                if attempt['packet'] is None:
                    assert not attempt['cap_fit'] and attempt['encode_error'] is not None
                else:
                    packet=raw(HERE,attempt['packet'])
                    assert attempt['complete_bytes']==len(packet)<=49152 and attempt['cap_fit']
                    assert attempt['base_bytes']+attempt['hud_bytes']+attempt['binding_bytes']==len(packet)
                if i==1:assert row['attempts'][0]['accepted_candidate'] is False
            if row['accepted']:
                selected=[a for a in row['attempts'] if a.get('selected')]
                assert len(selected)==1;attempt=selected[0]
                assert row['selected_background']==attempt['background'] and row['complete_bytes']==attempt['complete_bytes']
                packet=raw(HERE,attempt['packet']);out,hud,meta=rx.receive(packet)
                assert meta['frame_id']==fid and meta['reference_id']==rid and meta['key']==key
                assert len(hud)==4 and sum(p['words'].size for p in hud)==21120
                for got,want,rect in zip(hud,patches,rects,strict=True):
                    assert tuple(got['rect'])==rect;np.testing.assert_array_equal(got['words'],want)
                display=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out));display=h.n.overlay(display,tuple(v['words'] for v in hud))
                quality=h.n.metric(original,display);assert quality==row['quality'] and quality['hud_word_errors']==0
                assert h.m.C.reference_tag(out).hex()==row['normalized_tag']==attempt['normalized_tag']
                last_accepted=fid;naccepted+=1
            else:
                assert row.get('rejected') is True and not any(a.get('selected') for a in row['attempts'])
                assert row['selected_background'] is None and row['complete_bytes'] is None
                nrejected+=1
            nframes+=1
        summary=case['summary']
        assert summary['input_frames']==len(rows) and summary['accepted_frames']==sum(r['accepted'] for r in rows)
        assert summary['rejected_frames']==sum(not r['accepted'] for r in rows)
        assert summary['accepted_complete_bytes']==sum(r['complete_bytes'] or 0 for r in rows)
        assert summary['max_accepted_complete_bytes']==max((r['complete_bytes'] for r in rows if r['accepted']),default=None)
    assert nframes==457 and naccepted+nrejected==457 and ntries>=457
    print(json.dumps(dict(input_frames=nframes,accepted_frames=naccepted,rejected_frames=nrejected,attempts=ntries,
                          source_hashes_and_pins_match=True,independent_causal_replay=True)))
if __name__=='__main__':main()
