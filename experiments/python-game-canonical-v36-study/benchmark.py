#!/usr/bin/env python3
"""Actual fixed-decision causal CN36 full/skip reference-equality campaign."""
import json,time
from dataclasses import replace
import numpy as np
import helpers as h
model=h.module('canonical36_producer_model',h.HERE/'model.py')

def timed(fn):
    t=time.perf_counter_ns();r=fn();return r,(time.perf_counter_ns()-t)/1e6

def metric(planes,original,patches):
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(planes)),patches)
    return h.n.metric(original,display),h.n.digest(display)

def summarize(rows,variant):
    values=[r[variant] for r in rows];sse=sum(r['hybrid']['active_squared_error'] for r in values)
    samples=sum(r['hybrid']['active_channel_samples'] for r in values)
    return dict(frames=len(rows),complete_bytes=sum(r['complete_bytes'] for r in values),maximum_complete_bytes=max(r['complete_bytes'] for r in values),
        active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,
        nominal_Mbps_at30=sum(r['complete_bytes'] for r in values)*240/len(rows)/1e6,
        mean_receiver_ms=sum(r['decode_ms'] for r in values)/len(rows),
        mean_paid_proof_encoder_ms=None if variant=='legacy_fixed' else sum(r['paid_proof_encoder_ms'] for r in rows)/len(rows),
        mean_legacy_fixed_paid_encoder_ms=sum(r['legacy_fixed_paid_encoder_ms'] for r in rows)/len(rows) if variant=='legacy_fixed' else None,
        inner_bytes=sum(r['inner_bytes'] for r in values),hud_bytes=sum(r['hud_bytes'] for r in values),
        binding_bytes=sum(r['binding_bytes'] for r in values),peak_frame_mse=max(r['hybrid']['active_mse'] for r in values),
        mean_adjacent_frame_mse_change=sum(abs(b['hybrid']['active_mse']-a['hybrid']['active_mse']) for a,b in zip(values,values[1:]))/(len(values)-1))

def run_motion_probe(inp,hc):
    receivers={v:model.Receiver() for v in ('full','skip')};ref=None;rid=h.m.NO_REF;rows=[]
    covered=h.mask.coverage((480,720),h.n.RECTS)
    for src,hu in zip(inp['rows'][:6],hc['rows'][:6],strict=True):
        fid=src['id'];source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD)
        patches=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
        p=h.m.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',motion_precision='half',penalty=0)
        crossing=0
        if ref is not None:
            vectors=np.empty(((480+31)//32,(720+31)//32,2),np.int8);vectors[:]=(-3,1)
            prediction=h.m.predict(ref,vectors,32)
            vb=h.m.base.pack_vectors(vectors)
            raw=h.m.base.old._forward(source,prediction)
            p=replace(p,motion_mode='block',vector_bytes=vb,prediction=prediction,raw_coefficients=raw)
            indicator=tuple(np.zeros_like(v) for v in ref)
            # Canonicalize zeros =>128 on hiddenblocks, then predict; nonzeroYoutsideHUD proves hidden-to-visible reads.
            indicator=model.normalize(indicator)
            predicted=h.m.predict(indicator,vectors,32)
            crossing=int(np.count_nonzero((predicted[0]!=0)&~covered));assert crossing>0
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        inner,fullpixels,_=h.m.encode_prepared(p,q);skip,skippixels,_=model.skip_inner(inner,p.prediction)
        variants={}
        for name,packet,pixels in (('full',inner,fullpixels),('skip',skip,skippixels)):
            normalized=model.normalize(pixels);wire=model.wrap(packet,hud,normalized,skip=name=='skip')
            decoded,parts=receivers[name].receive(wire)
            quality,tag=metric(decoded,original,tuple(v['words'] for v in parts))
            variants[name]=dict(packet=h.blob(wire),inner=h.blob(packet),complete_bytes=len(wire),hybrid=quality,display_sha256=tag,normalized_tag=h.m.C.reference_tag(decoded).hex())
        for a,b in zip(receivers['full'].ref,receivers['skip'].ref,strict=True):np.testing.assert_array_equal(a,b)
        assert variants['full']['display_sha256']==variants['skip']['display_sha256']
        rows.append(dict(id=fid,key=fid==0,reference_id=rid,source_sha256=src['common_yuv420_u8_sha256'],
            configured_vector_halfpel=None if fid==0 else [-3,1],nonzero_vectors=0 if fid==0 else vectors.shape[0]*vectors.shape[1],
            hidden_to_visible_luma_samples=crossing,**variants))
        ref=receivers['full'].ref;rid=fid
    return dict(scene=inp['scene'],rows=rows,scope='Six actual retained frames with forced constant(-3,+1)half-pel block32vectors. Causal equality with hiddenreference reads into visible prediction; no searchedmotion quality or cost claim.')

def main():
    before=h.pins();inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    oldcases=h.load(h.HERE.parent/'python-game-controller-v35-study/results.json')['cases']
    for inp in inputs:
        hc=next(v for v in huds if v['scene']==inp['scene']);receivers={k:model.Receiver() for k in ('full','skip')};rows=[]
        ref=None;rid=h.m.NO_REF;legacy_rx=h.p.Receiver();legacy_ref=None
        for src,hu in zip(inp['rows'],hc['rows'],strict=True):
            fid=src['id'];key=fid%24==0
            if key:ref=None;rid=h.m.NO_REF;legacy_ref=None
            source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD)
            patches=tuple(original[y:y+hh,x:x+w] for x,y,w,hh in h.n.RECTS)
            prepared,analysis_ms=timed(lambda:h.m.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=rid,
                block_size=32,motion_mode='zero',motion_precision='half',penalty=0))
            legacy_prepared,legacy_analysis_ms=timed(lambda:h.m.analyze_planes(source,legacy_ref,epoch=25,frame_id=fid,reference_id=rid,
                block_size=32,motion_mode='zero',motion_precision='half',penalty=0))
            candidates=[]
            for bg in (16,32):
                q=h.m.roi.declared_map(720,480,h.n.ROIS,8,bg)
                (fullinner,fullpixels,work),full_ms=timed(lambda:h.m.encode_prepared(prepared,q))
                (skipinner,skippixels,skipwork),skip_ms=timed(lambda:model.skip_inner(fullinner,prepared.prediction))
                normalized=[];normalize_ms=[]
                for pixels in (fullpixels,skippixels):
                    planes,ms=timed(lambda:model.normalize(pixels));normalized.append(planes);normalize_ms.append(ms)
                for a,b in zip(*normalized,strict=True):np.testing.assert_array_equal(a,b)
                packets=[];wrap_ms=[]
                for i,inner in enumerate((fullinner,skipinner)):
                    packet,ms=timed(lambda:model.wrap(inner,hud,normalized[i],skip=bool(i)));packets.append(packet);wrap_ms.append(ms)
                (legacy_inner,legacy_pixels,legacy_work),legacy_encode_ms=timed(lambda:h.m.encode_prepared(legacy_prepared,q))
                legacy_packet,legacy_wrap_ms=timed(lambda:h.p.seal(h.p.PAIR.pack(b'CP34',1,h.p.PUBLISH|(h.p.KEY if key else 0),25,fid,255 if key else (fid-1)%2,fid%2,len(legacy_inner),len(hud),h.p.digest(legacy_inner),h.p.digest(hud))+legacy_inner+hud))
                candidate=dict(background=bg,full_bytes=len(packets[0]),skip_bytes=len(packets[1]),full_encode_ms=full_ms,
                    skip_proof_reparse_entropy_rebuild_ms=skip_ms,normalize_ms=normalize_ms,wrap_ms=wrap_ms,cap_fit=max(map(len,packets+[legacy_packet]))<=model.CAP,legacy_fixed_encode_ms=legacy_encode_ms,legacy_fixed_wrap_ms=legacy_wrap_ms,legacy_fixed_bytes=len(legacy_packet),
                    packets=dict(full=h.blob(packets[0]),skip=h.blob(packets[1]),legacy_fixed=h.blob(legacy_packet)))
                candidates.append(candidate)
                if candidate['cap_fit']:break
            assert candidates[-1]['cap_fit'],'no paired fitting q tier'
            variants={}
            for i,name in enumerate(('full','skip')):
                (decoded,parts),decode_ms=timed(lambda:receivers[name].receive(packets[i]))
                for a,b in zip(decoded,normalized[i],strict=True):np.testing.assert_array_equal(a,b)
                for part,patch in zip(parts,patches,strict=True):np.testing.assert_array_equal(part['words'],patch)
                quality,tag=metric(decoded,original,tuple(v['words'] for v in parts))
                variants[name]=dict(packet=h.blob(packets[i]),inner=h.blob((fullinner,skipinner)[i]),complete_bytes=len(packets[i]),
                    inner_bytes=len((fullinner,skipinner)[i]),hud_bytes=len(hud),binding_bytes=model.HEADER.size+4,
                    hybrid=quality,display_sha256=tag,normalized_tag=h.m.C.reference_tag(decoded).hex(),decode_ms=decode_ms,
                    normalization_ms=normalize_ms[i])
            (legacy_decoded,legacy_parts,legacy_ack),legacy_decode_ms=timed(lambda:legacy_rx.receive(legacy_packet))
            legacy_quality,legacy_display=metric(legacy_decoded,original,tuple(v['words'] for v in legacy_parts))
            variants['legacy_fixed']=dict(packet=h.blob(legacy_packet),inner=h.blob(legacy_inner),complete_bytes=len(legacy_packet),
                inner_bytes=len(legacy_inner),hud_bytes=len(hud),binding_bytes=60,hybrid=legacy_quality,display_sha256=legacy_display,
                reconstructed_tag=h.m.C.reference_tag(legacy_decoded).hex(),decode_ms=legacy_decode_ms,normalization_ms=0.)
            legacy_ref=legacy_decoded
            assert variants['full']['display_sha256']==variants['skip']['display_sha256']
            assert variants['full']['hybrid']==variants['skip']['hybrid']
            paid=analysis_ms+sum(c['full_encode_ms']+c['skip_proof_reparse_entropy_rebuild_ms']+sum(c['normalize_ms'])+sum(c['wrap_ms']) for c in candidates)
            row=dict(id=fid,key=key,reference_id=rid,background=bg,source_sha256=src['common_yuv420_u8_sha256'],
                reference_tag=prepared.reference_tag.hex(),hud_packet=hu['packet'],analysis_ms=analysis_ms,candidates=candidates,
                paid_proof_encoder_ms=paid,legacy_fixed_analysis_ms=legacy_analysis_ms,
                legacy_fixed_paid_encoder_ms=legacy_analysis_ms+sum(c['legacy_fixed_encode_ms']+c['legacy_fixed_wrap_ms'] for c in candidates),
                skip_work=skipwork,**variants)
            rows.append(row);ref=receivers['full'].ref;rid=fid
            if (fid+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames=fid+1)),flush=True)
        legacy=next(v for v in oldcases if v['scene']==inp['scene'] and v['policy']=='control')
        case=dict(scene=inp['scene'],rows=rows,summary={v:summarize(rows,v) for v in ('full','skip','legacy_fixed')},
            legacy_v35_control=dict(summary=legacy['summary'],policy='v35 independently selected zero/half32 and incumbent/band; not matched fixed CN36 policy',
                results_path='experiments/python-game-controller-v35-study/results.json',scene=inp['scene'],policy_name='control'))
        cases.append(case);print(json.dumps(dict(scene=inp['scene'],summary=case['summary'])),flush=True)
    motion_probe=run_motion_probe(inputs[0],next(v for v in huds if v['scene']==inputs[0]['scene']))
    assert h.pins()==before,'producer source changed during campaign'
    result=dict(schema='gamebub-canonical-v36',parent_commit='4b9b6bc0862e70141a7df69b0bc1731cadcdfd25',source_sha256=before,cases=cases,motion_probe=motion_probe,
        geometry=dict(coded=[720,480],active=[720,405],rectangles=h.n.RECTS,cap=model.CAP),
        profile=dict(magic='CN36',version=1,epoch=25,header_format=model.HEADER.format,header_bytes=model.HEADER.size,wrapper_bytes=model.HEADER.size+4,
            profile_tag=model.PROFILE.hex(),hidden_blocks=[int(v.sum()) for v in model.HIDDEN],normalization_value=128),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        scope=['Fixed zero motion, block32, key24, ROI8/background16 jointlyfallback32 forallthreevariants; both variants use identical shared prediction and selected visible coefficients.',
               'New CN36 profile normalizes only full transform blocks whose entireRGB support ishidden by fixed opaqueHUD; exact entire normalized refs and display equality asserted each frame.',
               'Proof sender pays full frozen encode, parse, additional skip entropy/reconstruction, bothnormalizations, wrappers, andeveryfittingtier; not an optimized sender speed benchmark.',
               'Retained input/HUD loading, source metric/equality assertions and archiveIO excluded from paidproofencoder; receiver measured separately.',
               'Actual skip emits zero hidden coefficients in existingGM27 innergrammar; saving includes full CN36wrapper plus exactHX33. Zero blocks still consume entropy representation: no new sparse implicit grammar.',
               'Actuallegacy_fixed CP34cohortuses same fixedzero/qmap/key decisions and separate noncanonical references; its paid encoder is measured separately. CN36wrapper is'+str(model.HEADER.size+4)+'BversusCP34 60B: report rawinner and complete rates separately.',
               'Frozen legacyv35control uses different candidate decisions/reference semantics and is explicitly descriptive, not an identicalquality baseline.',
               'Two reused48frameMassEffect windows, noheldoutcontent/newnativeencodes/ESP32/FPGA/hardware30fps claim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
