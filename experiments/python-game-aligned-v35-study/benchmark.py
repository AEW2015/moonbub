#!/usr/bin/env python3
"""Causal transform-aligned masked-source GM27/CP34 controller and same-processed native anchors."""
import json
import platform
import time
import numpy as np
import helpers as h


def elapsed(fn):
    t=time.perf_counter_ns();v=fn();return v,(time.perf_counter_ns()-t)/1e6


def metric(pixels,original,patches):
    hybrid=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),patches)
    return h.n.metric(original,hybrid),h.n.digest(hybrid)


def total(rows):
    sse=sum(r['hybrid']['active_squared_error'] for r in rows);samples=sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(frames=len(rows),complete_bytes=sum(r['body_bytes'] for r in rows),active_squared_error=sse,
        active_channel_samples=samples,active_mse=sse/samples,maximum_complete_bytes=max(r['body_bytes'] for r in rows),
        nominal_Mbps_at30=sum(r['body_bytes'] for r in rows)*240/len(rows)/1e6,
        cap_violations=sum(r['body_bytes']>49152 for r in rows))


def custom(inp,hudcase,baseline):
    rx=h.p.Receiver();ref=None;rid=h.m.NO_REF;slot=0;rows=[]
    for src,hu,control in zip(inp['rows'],hudcase['rows'],baseline['rows'],strict=True):
        (source,masked,original,patches),source_prep_ms=elapsed(lambda:h.source(src))
        hud=h.raw(hu['packet'],h.HUD);fid=src['id'];key=fid%24==0
        if key:ref=None;rid=h.m.NO_REF;slot=0
        prepared={};analyses={}
        for kind in (('zero',) if key else ('zero','half32')):
            prep,ms=elapsed(lambda:h.adaptive.analyze_with(h.m.base,masked,ref,epoch=25,frame_id=fid,reference_id=rid,
                block_size=32,motion_mode='zero' if kind=='zero' else 'block',motion_precision='half',penalty=0,search_policy='adaptive_zero2'))
            prepared[kind]=prep;analyses[kind]=dict(wall_ms=ms,work=prep.work)
        attempts=[];groups=[];chosen=None
        for bg in (16,32):
            q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg);bykind={}
            for kind,prep in prepared.items():
                pair,ms=elapsed(lambda:h.shared.encode_pair(h.m,prep,q));group=f'{bg}:{kind}'
                groups.append(dict(id=group,wall_ms=ms,shared=pair[0][2]['shared_pair']));bykind[kind]=[]
                for i,(packet,pixels,work) in enumerate(pair):
                    start=time.perf_counter_ns();quality,hybrid_hash=metric(pixels,original,patches);quality_ms=(time.perf_counter_ns()-start)/1e6
                    start=time.perf_counter_ns()
                    complete=h.p.seal(h.p.PAIR.pack(b'CP34',1,h.p.PUBLISH|(h.p.KEY if key else 0),25,fid,
                        h.p.NO_SLOT if key else slot,0 if key else 1-slot,len(packet),len(hud),h.p.digest(packet),h.p.digest(hud))+packet+hud)
                    fits=len(complete)<=49152
                    if fits:h.p.parse_pair(complete)
                    else:
                        try:h.p.parse_pair(complete)
                        except ValueError:pass
                        else:raise AssertionError('overcap accepted')
                    bind_ms=(time.perf_counter_ns()-start)/1e6
                    a=dict(kind=kind+('_band' if i else ''),background=bg,encode_group=group,packet=h.blob(complete),base_packet=h.blob(packet),
                        complete_bytes=len(complete),base_bytes=len(packet),cap_fit=fits,hybrid=quality,hybrid_sha256=hybrid_hash,
                        work=work,quality_ms=quality_ms,bind_ms=bind_ms)
                    bykind[kind].append(a)
            ordered=[bykind[k][0] for k in prepared]+[bykind[k][1] for k in prepared]
            attempts.extend(ordered);chosen,_=h.select30.select_tier(ordered,'band_strict')
            if chosen is not None:break
        assert chosen is not None
        for a in attempts:a['selected']=a is chosen
        packet=h.raw(chosen['packet'],h.HERE)
        (pixels,decoded_patches,ack),receive_ms=elapsed(lambda:rx.receive(packet))
        h.p.validate_ack(ack,packet)
        for a,b in zip(decoded_patches,patches,strict=True):np.testing.assert_array_equal(a['words'],b)
        quality,hybrid_hash=metric(pixels,original,tuple(a['words'] for a in decoded_patches))
        assert quality==chosen['hybrid'] and hybrid_hash==chosen['hybrid_sha256']
        rows.append(dict(id=fid,key=key,reference_id=rid,reference_tag=prepared['zero'].reference_tag.hex(),
            source_slot=h.p.NO_SLOT if key else slot,destination_slot=0 if key else 1-slot,
            source_sha256=src['common_yuv420_u8_sha256'],masked_source_sha256=h.digest(b''.join(v.astype('u1').tobytes() for v in masked)),
            source_prep_with_equivalence_ms=source_prep_ms,
            visible_precodec_equal=True,selected_kind=chosen['kind'],selected_background=chosen['background'],
            packet=chosen['packet'],base_packet=chosen['base_packet'],ack=h.blob(ack),hud_packet=hu['packet'],hud_bytes=len(hud),
            body_bytes=len(packet),base_bytes=chosen['base_bytes'],binding_bytes=60,hybrid=quality,hybrid_sha256=hybrid_hash,
            original_control_bytes=control['body_bytes'],original_control_hybrid=control['hybrid'],
            analyses=analyses,encode_groups=groups,attempts=attempts,receive_ms=receive_ms,
            paid_policy_ms=sum(a['wall_ms'] for a in analyses.values())+sum(g['wall_ms'] for g in groups)+sum(a['quality_ms']+a['bind_ms'] for a in attempts)))
        ref=pixels;rid=fid;slot=0 if key else 1-slot
        if (fid+1)%12==0:print(json.dumps(dict(scene=inp['scene'],custom_frames=fid+1)),flush=True)
    return dict(scene=inp['scene'],policy='aligned_core8_raw',rows=rows,summary=total(rows),baseline_summary=total(baseline['rows']))


def native(inp,hudcase,custom_case,name,q,processed):
    sources=[];originals=[];patches=[];source_prep=[]
    for src in inp['rows']:
        (original,masked,words,parts),prep_ms=elapsed(lambda:h.source(src));source_prep.append(prep_ms);sources.append(masked if processed=='masked' else original);originals.append(words);patches.append(parts)
    try:
        packets,extras,encode=h.standard.encode(sources,name,q)
        decoded,decode=h.standard.decode(packets,extras,name)
    except Exception as exc:
        return dict(scene=inp['scene'],encoder=name,parameter=q,processed=processed,supported=False,error=repr(exc))
    assert [p['pts'] for p in packets]==list(range(48))==[p['dts'] for p in packets]
    assert [p['pts'] for p in packets if p['is_key']]==[0,24]
    assert encode['packets_only_at_flush']==0 and decode['frames_only_at_decode_flush']==0
    assert all(c['emitted_pts']==[c['id']] for c in encode['frame_calls'])
    assert all(c['output_pts']==[c['packet_pts']] for c in decode['decode_calls'])
    rows=[]
    for packet,hu,words,parts in zip(packets,hudcase['rows'],originals,patches,strict=True):
        fid=packet['pts'];hud=h.raw(hu['packet'],h.HUD);display=h.n.overlay(decoded[fid],parts)
        quality=h.n.metric(words,display);body=len(packet['data'])+len(hud)+60+(len(extras) if fid==0 else 0)
        rows.append(dict(id=fid,pts=fid,dts=packet['dts'],key=packet['is_key'],access_unit=h.blob(packet['data']),
            access_unit_bytes=len(packet['data']),extradata_bytes_charged=len(extras) if fid==0 else 0,
            hud_packet=hu['packet'],hud_bytes=len(hud),binding_bytes=60,body_bytes=body,hybrid=quality,hybrid_sha256=h.n.digest(display)))
    summary=total(rows);summary['quality_at_least_masked_custom']=summary['active_mse']<=custom_case['summary']['active_mse']
    return dict(scene=inp['scene'],encoder=name,parameter=q,processed=processed,supported=True,
        extradata=h.blob(extras),encode=encode,decode=decode,source_prep_with_equivalence_ms=source_prep,rows=rows,summary=summary,
        accounting='Every actual native AU + extradata once at frame0 + same actual HX33 +60 byte binding cost; no native CP34 syntax claimed.')


def main():
    before=h.producer_pins();inputs=h.load(h.n.V24/'results.json')['inputs'];hud=h.load(h.HUD/'results.json')['cases']
    baseline=h.load(h.V34/'results.json')['cases'];cases=[];native_cases=[]
    for inp in inputs:
        hu=next(c for c in hud if c['scene']==inp['scene']);old=next(c for c in baseline if c['scene']==inp['scene'] and c['policy']=='control')
        case=custom(inp,hu,old);cases.append(case);print(json.dumps(dict(custom_summary=case['summary'],scene=inp['scene'])),flush=True)
        anchor={'libx265':32 if inp['scene']=='mass-effect-2600' else 28,'libsvtav1':48 if inp['scene']=='mass-effect-2600' else 38}
        for name in ('libx265','libsvtav1'):
            for processed,q in [('original',anchor[name])]+[('masked',q) for q in ((28,32) if name=='libx265' else (38,48))]:
                item=native(inp,hu,case,name,q,processed);native_cases.append(item)
                print(json.dumps(dict(scene=inp['scene'],native=name,q=q,processed=processed,supported=item['supported'],summary=item.get('summary'),error=item.get('error'))),flush=True)
        assert h.producer_pins()==before
        data=dict(schema='gamebub-aligned-v35',parent_commit='c50df93e313c9402c3741e5f6c921ee40e6f10a3',source_sha256=h.pins(),producer_sha256=before,
            cases=cases,native_cases=native_cases,rectangles=[list(v) for v in h.n.RECTS],mask_constant=[128,128,128],
            mask_policy='core8',whole_transform_blocks_only=True,
            causal_campaign=True,decoder_format_changed=False,physical_30fps_proven=False,
            environment=dict(python=platform.python_version(),numpy=np.__version__),
            scope=['Host-only whole8x8 source mask whose entire RGB support is inside exact fixed opaque HUD union; all custom/native metrics use original RGB after exact HUD.',
                'Custom actual GM27/CP34/HX33 causal accepted decoded references; key0/24; every incumbent/band zero/half32 trial retained.',
                'Native exact frozen standard-v24 PyAV options on same original/masked common YUV; every AU and extradata charged plus actual HX33+60.',
                'Native accounting is byte cost, not CP34 native syntax or Gamebub native HEVC/AV1 decoder support.',
                'Masking relies on CP34 exact fixed HUD and atomic publication; invalid/missing HUD never publishes.',
                'Source preparation with exact equivalence proof separately recorded per call; policy clocks exclude it, preencoded HX33, archive IO, network and display; no physical throughput/hardware fit claim.'])
        (h.HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')


if __name__=='__main__':main()
