#!/usr/bin/env python3
"""Causal full-v40-window key-cap qualification using frozen v37/v38 models."""
from pathlib import Path
import hashlib,importlib.util,json,platform,sys,time,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];V40=ROOT/'experiments/python-game-source-v40-study'

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def digest(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return digest(Path(p).read_bytes())
def raw(folder,d):
    packed=(folder/d['path']).read_bytes();assert digest(packed)==d['stored_sha256']
    z=zlib.decompressobj();out=z.decompress(packed,d['raw_bytes']+1)
    assert z.eof and not z.unused_data and not z.unconsumed_tail and len(out)==d['raw_bytes']
    assert digest(out)==d['raw_sha256'];return out
def archive(b):
    packed=zlib.compress(b,9);name='objects/'+digest(packed)+'.zlib';(HERE/name).write_bytes(packed)
    return dict(path=name,raw_bytes=len(b),raw_sha256=digest(b),stored_sha256=digest(packed))
def copy_receiver_state(dst,src):
    dst.ref=src.ref;dst.rid=src.rid;dst.hud=src.hud;dst.last=src.last

def main():
    h=module('helpers',ROOT/'experiments/python-game-integrated-v38-study/helpers.py')
    integrated=module('control_qual_v38_sender',ROOT/'experiments/python-game-integrated-v38-study/model.py')
    analysis=module('control_qual_v37_analysis',ROOT/'experiments/python-game-analysis-v37-study/model.py')
    decoder=module('control_qual_independent_cs37',ROOT/'experiments/python-game-implicit-v37-study/verify.py')
    hud32=module('control_qual_hx32',ROOT/'experiments/python-game-hud-v32-study/model.py')
    baseline=module('baseline',ROOT/'experiments/python-game-hud-runs-v33-study/baseline.py')
    module('decoder',ROOT/'experiments/python-game-hud-runs-v33-study/decoder.py')
    hud33=module('control_qual_hx33',ROOT/'experiments/python-game-hud-runs-v33-study/model.py')
    p=baseline.p
    manifest=json.loads((V40/'manifest.json').read_text())
    assert len(manifest['cases'])==4
    pins=dict(h.pins())
    for path in [V40/'manifest.json',V40/'prepare.py',HERE/'prepare.py',HERE/'verify.py',HERE/'README.md',
       ROOT/'experiments/python-game-analysis-v37-study/model.py',ROOT/'experiments/python-game-analysis-v37-study/helpers.py',
       ROOT/'experiments/python-game-integrated-v38-study/model.py',ROOT/'experiments/python-game-integrated-v38-study/helpers.py',
       ROOT/'experiments/python-game-implicit-v37-study/verify.py',ROOT/'experiments/python-game-implicit-v37-study/results.json',
       ROOT/'experiments/python-game-hud-v32-study/model.py',ROOT/'experiments/python-game-hud-runs-v33-study/model.py',
       ROOT/'experiments/python-game-hud-runs-v33-study/baseline.py',ROOT/'experiments/python-game-hud-runs-v33-study/decoder.py',
       ROOT/'experiments/python-game-runtime-v28-study/protocol.py',ROOT/'experiments/python-game-runtime-v28-study/model.py',
       ROOT/'experiments/python-codec-study/corpus.py',ROOT/'experiments/python-transform-study/fixed_codec.py']:
        pins[path.relative_to(ROOT).as_posix()]=file_sha(path)

    cases=[];total=0
    for source_case in manifest['cases']:
        scene=Path(source_case['media_file']).stem
        frames=source_case['frames'];assert [f['id'] for f in frames]==list(range(len(frames)))
        rx=decoder.Receiver();accepted=[];rows=[];accepted_ref=None;accepted_hud=None;accepted_fid=None
        for f in frames:
            fid=f['id'];requested_key=(fid%24==0 or accepted_ref is None)
            rid=p.NO_REF if requested_key else accepted_fid
            assert requested_key==(rid==p.NO_REF)
            base_reference=None if requested_key else accepted_ref
            hud_reference=None if requested_key else accepted_hud
            # Input object read/validation and source-domain conversion have
            # separate clocks, both outside the sender timing.
            t=time.perf_counter_ns();canvas_raw=raw(V40,f['canvas_rgb24']);canvas_load_ms=(time.perf_counter_ns()-t)/1e6
            t=time.perf_counter_ns();canvas=np.frombuffer(canvas_raw,np.uint8).reshape(480,720,3).copy()
            assert digest(canvas.tobytes())==f['canvas_rgb_sha256']
            original=h.m.C.corpus.rgb565(canvas).astype(np.uint16)
            assert digest(np.ascontiguousarray(original,dtype='<u2').tobytes())==f['rgb565_sha256']
            source=tuple(np.asarray(v,dtype=np.int16) for v in h.m.ft.rgb_to_planes(canvas))
            rects=tuple(h.n.RECTS)
            source_conversion_ms=(time.perf_counter_ns()-t)/1e6

            t=time.perf_counter_ns();selector=p.ui.PatchSelector(rectangles=rects)
            chosen=selector.select(canvas,98304);hu25,hud_work=p.encode_hud(chosen.patches,reference=hud_reference,
                epoch=25,frame_id=fid,reference_id=rid,motion=True,width=720,height=480)
            hx32,hx32_work=hud32.encode_hud(hu25,hud_reference,expected_reference_id=None if requested_key else rid)
            hx33,hx33_work=hud33.encode_hud(hu25,hx32,hud_reference,expected_reference_id=None if requested_key else rid)
            hud_generation_ms=(time.perf_counter_ns()-t)/1e6
            decoded_hud,hmeta=hud33.decode_hud(hx33,hud_reference,expected_epoch=25,
                expected_reference_id=None if requested_key else rid)
            assert sum(v['words'].size for v in decoded_hud)==21120
            for got,(x,y,ww,hh) in zip(decoded_hud,rects,strict=True):
                assert tuple(got['rect'])==(x,y,ww,hh)
                np.testing.assert_array_equal(got['words'],original[y:y+hh,x:x+ww])
            hud_desc={'HU25':archive(hu25),'HX32':archive(hx32),'HX33_selected':archive(hx33)}

            t=time.perf_counter_ns();prepared=analysis.analyze_planes(source,base_reference,epoch=25,frame_id=fid,
                reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
            analysis_ms=(time.perf_counter_ns()-t)/1e6
            tries=[];selected=None;decode_errors=[]
            for background in (16,32):
                q=h.m.roi.declared_map(720,480,h.n.ROIS,8,background)
                begin=time.perf_counter_ns();attempt=dict(background=background,roi=8,encode_error=None,
                    hud_bytes=len(hx33),encode_ms=None,packet=None,complete_bytes=None,base_bytes=None,cap_fit=False)
                try:
                    wire,normalized,work=integrated.encode_prepared(prepared,q,hx33,rdo_lambda=1)
                    attempt['encode_ms']=(time.perf_counter_ns()-begin)/1e6
                    attempt['packet']=archive(wire);attempt['complete_bytes']=len(wire)
                    attempt['base_bytes']=len(wire)-80-len(hx33);attempt['binding_bytes']=80
                    attempt['cap_fit']=len(wire)<=49152
                    if not attempt['cap_fit']:raise ValueError('actual complete CS37 cap exceeded')
                    # Validate on an independent receiver against a rollback-safe
                    # copy; publish to the causal receiver only after all checks.
                    probe=decoder.Receiver();copy_receiver_state(probe,rx)
                    dt=time.perf_counter_ns()
                    decoded,got_hud,meta=probe.receive(wire)
                    attempt['decode_ms']=(time.perf_counter_ns()-dt)/1e6
                    assert meta['frame_id']==fid and meta['reference_id']==rid and meta['key']==requested_key
                    for got,want in zip(got_hud,decoded_hud,strict=True):
                        assert got['rect']==want['rect'];np.testing.assert_array_equal(got['words'],want['words'])
                    assert sum(v['words'].size for v in got_hud)==21120
                    display=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded))
                    display=h.n.overlay(display,tuple(v['words'] for v in got_hud))
                    quality=h.n.metric(original,display);assert quality['hud_word_errors']==0
                    assert h.m.C.reference_tag(decoded)==h.m.C.reference_tag(normalized)
                    assert meta['reference_tag'].hex()==prepared.reference_tag.hex()
                    attempt.update(accepted_candidate=True,normalized_tag=h.m.C.reference_tag(decoded).hex(),
                        output_tag=meta['output_tag'].hex(),hud_tag=hmeta['reconstructed_tag'].hex(),quality=quality,
                        work=work)
                    selected=(attempt,decoded,got_hud,probe);tries.append(attempt)
                    break
                except Exception as exc:
                    if attempt['encode_ms'] is None:attempt['encode_ms']=(time.perf_counter_ns()-begin)/1e6
                    attempt['encode_error']=f'{type(exc).__name__}: {exc}'
                    attempt['accepted_candidate']=False
                    tries.append(attempt);decode_errors.append(attempt['encode_error'])
            attempts_ms=sum(x['encode_ms'] for x in tries)
            row=dict(id=fid,pts=f['pts'],time_base=f['time_base'],timestamp_fraction=f['timestamp_fraction'],
                decoded_order=f['decoded_order'],source_rgb_sha256=f['canvas_rgb_sha256'],
                source_rgb565_sha256=f['rgb565_sha256'],source_yuv_sha256=f['common_yuv420_u8_sha256'],
                source_canvas_object=f['canvas_rgb24'],active_rect_xywh=f['active_rect_xywh'],
                requested_key=requested_key,reference_id=rid,previous_accepted_id=accepted_fid,
                source_read_ms=canvas_load_ms,source_conversion_ms=source_conversion_ms,
                hud_generation_ms=hud_generation_ms,hud_bytes=len(hx33),hud_tag=hmeta['reconstructed_tag'].hex(),
                hud_packets=hud_desc,hu25_work=hud_work,hx32_work=hx32_work,hx33_work=hx33_work,
                analysis_ms=analysis_ms,attempts=tries,analysis_plus_all_encode_ms=analysis_ms+attempts_ms,
                accepted=selected is not None,rejection_errors=decode_errors)
            if selected is not None:
                attempt,decoded,got_hud,probe=selected
                copy_receiver_state(rx,probe)
                accepted_ref=decoded;accepted_hud=got_hud;accepted_fid=fid
                attempt['selected']=True
                row['selected_background']=attempt['background'];row['complete_bytes']=attempt['complete_bytes']
                row['base_bytes']=attempt['base_bytes'];row['quality']=attempt['quality'];row['normalized_tag']=attempt['normalized_tag']
                accepted.append(row)
            else:
                # State and references remain unchanged; account for this input.
                row['selected_background']=None;row['complete_bytes']=None;row['base_bytes']=None
                row['rejected']=True
            rows.append(row)
            if (fid+1)%24==0:print(json.dumps(dict(scene=scene,frames=fid+1,accepted=len(accepted),rejected=len(rows)-len(accepted))),flush=True)
        assert len(rows)==len(frames)
        selected_rows=[r for r in rows if r['accepted']]
        backgrounds={str(q):sum(r['selected_background']==q for r in selected_rows) for q in (16,32)}
        errors16=sum(bool(r['attempts'] and not r['attempts'][0]['cap_fit']) for r in rows)
        summary=dict(input_frames=len(rows),accepted_frames=len(selected_rows),rejected_frames=len(rows)-len(selected_rows),
            key_attempts=sum(r['requested_key'] for r in rows),accepted_key_frames=sum(r['requested_key'] for r in selected_rows),
            selected_background_counts=backgrounds,bg32_fallbacks=backgrounds['32'],
            bg16_failed_or_overcap_frames=errors16,cap_fit_frames=sum(len(r['attempts']) and any(a['cap_fit'] for a in r['attempts']) for r in rows),
            max_accepted_complete_bytes=max((r['complete_bytes'] for r in selected_rows),default=None),
            accepted_complete_bytes=sum(r['complete_bytes'] for r in selected_rows),
            accepted_mean_active_mse=None if not selected_rows else sum(r['quality']['active_squared_error'] for r in selected_rows)/sum(r['quality']['active_channel_samples'] for r in selected_rows),
            total_source_read_ms=sum(r['source_read_ms'] for r in rows),total_source_conversion_ms=sum(r['source_conversion_ms'] for r in rows),
            total_hud_generation_ms=sum(r['hud_generation_ms'] for r in rows),total_analysis_ms=sum(r['analysis_ms'] for r in rows),
            total_encoder_attempt_ms=sum(a['encode_ms'] for r in rows for a in r['attempts']),
            total_analysis_plus_all_encode_ms=sum(r['analysis_plus_all_encode_ms'] for r in rows))
        total+=len(rows);cases.append(dict(scene=scene,media_sha256_before=source_case['media_sha256_before'],
            media_sha256_after=source_case['media_sha256_after'],
            source_frame_count=len(frames),summary=summary,rows=rows))
        print(json.dumps(dict(scene=scene,summary=summary)),flush=True)
    assert total==457
    result=dict(schema='gamebub-causal-control-qualification-v40',source_pins_sha256=pins,
      environment=dict(python=platform.python_version(),numpy=np.__version__),cases=cases,
      scope=['Every archived source-v40 frame is accounted for in original decoded order per clip; reference and HUD state advance only for fitting CS37 packets successfully decoded and exactly checked by the independent frozen CS37 receiver.',
       'Key rule is input fid modulo24 or no previously accepted base reference. After a rejected input, the next packet uses the last accepted reference ID; no frame is silently dropped from the manifest accounting.',
       'Fast fixed-zero analysis-v37 and integrated CS37-v38 sender only; ROI scale8/background16 tried first, background32 attempted only after a q16 exception/cap failure. Both alternatives use one identical actual HX33 HUD sidecar per source frame.',
       'Source/HUD generation and analysis/all q encode times are separately reported. Receiver, exact quality, archive and source reads are outside encoder-attempt clocks. No firmware/native/hardware/FPS claim and no unmeasured full-window claim.'])
    (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
    print(json.dumps(dict(done=True,input_frames=total)),flush=True)
if __name__=='__main__':main()
