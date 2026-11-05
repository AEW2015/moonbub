#!/usr/bin/env python3
"""Bounded first-frame CS37 cap probe on the archived v40 source windows."""
from pathlib import Path
import hashlib, importlib.util, json, platform, statistics, sys, time, zlib
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
V40=ROOT/'experiments/python-game-source-v40-study'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj

def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):return sha(Path(path).read_bytes())
def read_object(desc):
    packed=(V40/desc['path']).read_bytes()
    assert sha(packed)==desc['stored_sha256']
    dc=zlib.decompressobj();raw=dc.decompress(packed,desc['raw_bytes']+1)
    assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==desc['raw_bytes']
    assert sha(raw)==desc['raw_sha256'];return raw

def archive(data):
    packed=zlib.compress(data,9);name='objects/'+sha(packed)+'.zlib'
    (HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(data),raw_sha256=sha(data),stored_sha256=sha(packed))

def main():
    # Load the frozen V38 helper graph, then its sender/analyzer and truly
    # independent V37 CS37 receiver. Source and HUD converters are frozen too.
    h=module('helpers',ROOT/'experiments/python-game-integrated-v38-study/helpers.py')
    sender=module('keycap_v38_sender',ROOT/'experiments/python-game-integrated-v38-study/model.py')
    analysis=module('keycap_v37_analysis',ROOT/'experiments/python-game-analysis-v37-study/model.py')
    decoder=module('keycap_independent_cs37',ROOT/'experiments/python-game-implicit-v37-study/verify.py')
    hud32=module('keycap_hx32',ROOT/'experiments/python-game-hud-v32-study/model.py')
    baseline=module('baseline',ROOT/'experiments/python-game-hud-runs-v33-study/baseline.py')
    module('decoder',ROOT/'experiments/python-game-hud-runs-v33-study/decoder.py')
    hud33=module('keycap_hx33',ROOT/'experiments/python-game-hud-runs-v33-study/model.py')
    p=baseline.p

    manifest=json.loads((V40/'manifest.json').read_text())
    source_cases=manifest['cases']
    assert len(source_cases)==4
    pins={}
    for path in [V40/'manifest.json', V40/'prepare.py',
                 HERE/'prepare.py',HERE/'verify.py',HERE/'README.md',
                 ROOT/'experiments/python-game-analysis-v37-study/model.py',
                 ROOT/'experiments/python-game-analysis-v37-study/helpers.py',
                 ROOT/'experiments/python-game-integrated-v38-study/model.py',
                 ROOT/'experiments/python-game-integrated-v38-study/helpers.py',
                 ROOT/'experiments/python-game-implicit-v37-study/verify.py',
                 ROOT/'experiments/python-game-implicit-v37-study/results.json',
                 ROOT/'experiments/python-game-hud-v32-study/model.py',
                 ROOT/'experiments/python-game-hud-runs-v33-study/model.py',
                 ROOT/'experiments/python-game-hud-runs-v33-study/baseline.py',
                 ROOT/'experiments/python-game-runtime-v28-study/protocol.py',
                 ROOT/'experiments/python-game-runtime-v28-study/model.py',
                 ROOT/'experiments/python-codec-study/corpus.py',
                 ROOT/'experiments/python-transform-study/fixed_codec.py']:
        pins[path.relative_to(ROOT).as_posix()]=file_sha(path)
    pins.update(h.pins())

    results=[]
    for case in source_cases:
        scene=Path(case['media_file']).stem
        frame=case['frames'][0]
        assert frame['id']==0 and frame['decoded_order']>=0
        canvas=np.frombuffer(read_object(frame['canvas_rgb24']),np.uint8).reshape(480,720,3).copy()
        assert sha(canvas.tobytes())==frame['canvas_rgb_sha256']
        original=h.m.C.corpus.rgb565(canvas).astype(np.uint16)
        assert sha(np.ascontiguousarray(original,dtype='<u2').tobytes())==frame['rgb565_sha256']
        source=tuple(np.asarray(v,dtype=np.int16) for v in h.m.ft.rgb_to_planes(canvas))
        rects=tuple(h.n.RECTS)
        selector=p.ui.PatchSelector(rectangles=rects)
        selected=selector.select(canvas,98304)
        patches=selected.patches
        patch_words=p.ui.validate_patches(patches,720,480)
        assert sum(v['words'].size for v in patch_words)==21120
        for got,(x,y,ww,hh) in zip(patch_words,rects,strict=True):
            np.testing.assert_array_equal(got['words'],original[y:y+hh,x:x+ww])
        hu25,hud_work=p.encode_hud(patches,reference=None,epoch=25,frame_id=0,
                                  reference_id=p.NO_REF,motion=True,width=720,height=480)
        hx32,hx32_work=hud32.encode_hud(hu25,None,expected_reference_id=None)
        hx33,hx33_work=hud33.encode_hud(hu25,hx32,None,expected_reference_id=None)
        decoded_hud,hud_meta=hud33.decode_hud(hx33,None,expected_epoch=25,expected_reference_id=None)
        assert len(decoded_hud)==4 and sum(x['words'].size for x in decoded_hud)==21120
        for got,want in zip(decoded_hud,patch_words,strict=True):
            assert got['rect']==want['rect'];np.testing.assert_array_equal(got['words'],want['words'])
        assert hud_meta['reconstructed_tag']==p._parse_hud(hu25)['reconstructed_tag']

        prepared=analysis.analyze_planes(source,None,epoch=25,frame_id=0,reference_id=p.NO_REF,
              block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
        configs=[]
        for background in (16,32):
            q=h.m.roi.declared_map(720,480,h.n.ROIS,8,background)
            started=time.perf_counter_ns()
            item=dict(background=background,roi=8,complete_cap=49152,encode_error=None)
            item['analysis_ms']=prepared.work['analysis_wall_ms']
            try:
                wire,normalized,work=sender.encode_prepared(prepared,q,hx33,rdo_lambda=1)
                item['encode_ms']=(time.perf_counter_ns()-started)/1e6
                item['complete_bytes']=len(wire);item['hud_bytes']=len(hx33)
                item['binding_bytes']=80;item['base_bytes']=len(wire)-80-len(hx33)
                item['cap_fit']=len(wire)<=49152
                assert item['cap_fit']
                rx=decoder.Receiver()
                decoded,got_hud,meta=rx.receive(wire)
                assert meta['key'] and meta['frame_id']==0 and meta['reference_id']==p.NO_REF
                for got,want in zip(got_hud,patch_words,strict=True):
                    assert got['rect']==want['rect'];np.testing.assert_array_equal(got['words'],want['words'])
                display=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded))
                display=h.n.overlay(display,tuple(v['words'] for v in got_hud))
                quality=h.n.metric(original,display)
                assert quality['hud_word_errors']==0
                item['quality']=quality
                item['normalized_tag']=h.m.C.reference_tag(decoded).hex()
                item['receiver']='frozen independent implicit-v37 Receiver'
                item['packet']=archive(wire)
                item['work']=work
            except ValueError as exc:
                item['encode_ms']=(time.perf_counter_ns()-started)/1e6
                item['encode_error']=f'{type(exc).__name__}: {exc}'
                item['cap_fit']=False
            item['hud_packets']={'HU25':archive(hu25),'HX32':archive(hx32),'HX33_selected':archive(hx33)}
            item['hud_generation_work']={'HU25':hud_work,'HX32':hx32_work,'HX33':hx33_work}
            configs.append(item)
        results.append(dict(scene=scene,frame_id=0,decoded_order=frame['decoded_order'],pts=frame['pts'],
            time_base=frame['time_base'],timestamp_fraction=frame['timestamp_fraction'],
            media_sha256_before=case['media_sha256_before'],media_sha256_after=case['media_sha256_after'],
            active_rect_xywh=frame['active_rect_xywh'],
            source_canvas_rgb_sha256=frame['canvas_rgb_sha256'],source_rgb565_sha256=frame['rgb565_sha256'],
            source_yuv_sha256=frame['common_yuv420_u8_sha256'],source_canvas_object=frame['canvas_rgb24'],
            exact_hud_words=21120,hud_tag=hud_meta['reconstructed_tag'].hex(),configs=configs))
        print(json.dumps(dict(scene=scene,bytes=[c.get('complete_bytes') for c in configs],errors=[c['encode_error'] for c in configs])),flush=True)
    out=dict(schema='gamebub-first-key-cap-probe-v40',source_pins_sha256=pins,
      environment={'python':platform.python_version(),'numpy':np.__version__},
      scope=['One archived first frame per each of four v40 PTS-selected source clips; this is a key-frame cap probe, not a causal sequence or full-window qualification.',
        'Fresh RGB565 patches are encoded through actual HU25, HX32 and HX33 APIs with epoch25/frame0/no-reference; exact 21,120 HUD words checked.',
        'Frozen fast analysis-v37 plus integrated CS37-v38 sender, block32, zero-motion key and ROI scale8 with background16 and32. Source preparation is outside per-configuration sender timer.',
        'Each fitting packet decoded by the independent implicit-v37 Receiver; scores compare original source RGB565 plus exact HUD against decoded display. No transport, firmware, native timing, FPS or full-cohort cap claim.'],
      cases=results)
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(dict(done=True,cases=len(results))),flush=True)
if __name__=='__main__':main()
