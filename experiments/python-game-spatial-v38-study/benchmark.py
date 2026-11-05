"""Twelve-frame own-reference pilot plus synthetic spatial controls."""
import json,platform,time
import numpy as np
import helpers as h
model=h.module('spatial38_benchmark_model',h.HERE/'model.py')

def array_blob(a):return dict(**h.blob(a.tobytes()),shape=list(a.shape),dtype=a.dtype.str)
def summary(rows):
    sse=sum(r['hybrid']['active_squared_error']for r in rows);samples=sum(r['hybrid']['active_channel_samples']for r in rows)
    return dict(frames=len(rows),complete_bytes=sum(r['complete_bytes']for r in rows),maximum_complete_bytes=max(r['complete_bytes']for r in rows),
        mode_bytes=sum(r['work']['mode_bytes']for r in rows),coefficient_bytes=sum(r['work']['coefficient_bytes']for r in rows),
        active_mse=sse/samples,peak_frame_mse=max(r['hybrid']['active_mse']for r in rows),
        mean_encode_ms=sum(r['work']['encode_ms']for r in rows)/len(rows),all_frames_cap_fit=all(r['cap_fit']for r in rows),
        mode_counts=[sum(p['mode_counts'][mode]for r in rows for p in r['work']['planes'])for mode in range(4)],
        nominal_Mbps_at30=sum(r['complete_bytes']for r in rows)*240/len(rows)/1e6)

def frame(source,original,hud,policy,fid,state,source_id):
    if fid%24==0:state.update(ref=None,rid=h.m.NO_REF)
    q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    packet,pixels,work,modes,costs=model.encode_planes(source,state['ref'],q,hud,policy=policy,frame_id=fid,reference_id=state['rid'])
    patches=tuple(original[y:y+hh,x:x+w]for x,y,w,hh in h.n.RECTS)
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),patches)
    quality=h.n.metric(original,display)
    row=dict(id=fid,key=state['ref']is None,reference_id=state['rid'],source_sha256=h.digest(b''.join(v.astype('u1').tobytes()for v in source)),
        source_id=source_id,packet=h.blob(packet),hud_packet=h.blob(hud),complete_bytes=len(packet),cap_fit=len(packet)<=49152,
        reference_tag=(bytes(16)if state['ref']is None else h.m.C.reference_tag(state['ref'])).hex(),
        normalized_tag=h.m.C.reference_tag(pixels).hex(),display_sha256=h.n.digest(display),hybrid=quality,work=work,
        mode_arrays=[array_blob(a)for a in modes],candidate_cost_arrays=[array_blob(a)for a in costs])
    if not row['cap_fit']:raise ValueError(('pilot frame exceedscompletecap',source_id,policy,fid,len(packet)))
    state.update(ref=pixels,rid=fid)
    return row

def synthetic_hud(original):
    ui=h.m.C._ui();patches=[]
    for x,y,w,hh in h.n.RECTS:
        words=original[y:y+hh,x:x+w].astype('<u2');payload=words.tobytes()
        patches.append(model.seal(ui.row.HEADER.pack(b'HP01',1,0,x,y,w,hh,0,w*hh,len(payload))+payload))
    old=h.p.hud.p
    baseline,_=old.encode_hud(patches,epoch=25,frame_id=0,reference_id=h.m.NO_REF,motion=False)
    v32,_=h.p.hud.old.encode_hud(baseline)
    # Synthetic fixtures retain actual HX32 exact patches; the frozen HX33
    # receive adapter explicitly accepts HX32 fallback. No free HUD is assumed.
    return v32

def synthetics():
    yy,xx=np.mgrid[:480,:720];rng=np.random.default_rng(38001)
    values={'flat':np.full((480,720),96,np.int16),
            'directional_tiles':(70+6*((xx//16+2*(yy//16))%20)).astype(np.int16),
            'low_amplitude_noise':(128+rng.integers(-4,5,(480,720))).astype(np.int16)}
    result=[]
    for name,y in values.items():
        source=(y,np.full((240,360),128,np.int16),np.full((240,360),128,np.int16))
        original=h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(source))
        for x,py,w,hh in h.n.RECTS:original[py:py+hh,x:x+w]=np.uint16(0x4a49)
        result.append((name,source,original,synthetic_hud(original)))
    return result

def main():
    before=h.pins();inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[];synthetic_inputs=[]
    for inp in inputs:
        hc=next(c for c in huds if c['scene']==inp['scene']);states={p:dict(ref=None,rid=h.m.NO_REF)for p in('mode0control','spatial')};rows={p:[]for p in states}
        for src,hu in zip(inp['rows'][:12],hc['rows'][:12],strict=True):
            source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD)
            order=('mode0control','spatial')if src['id']%2==0 else('spatial','mode0control')
            for policy in order:rows[policy].append(frame(source,original,hud,policy,src['id'],states[policy],dict(scene=inp['scene'],id=src['id'],kind='main')))
            print(json.dumps(dict(scene=inp['scene'],frame=src['id'])),flush=True)
        for policy in states:
            c=dict(scene=inp['scene'],kind='main',policy=policy,rows=rows[policy],summary=summary(rows[policy]));cases.append(c);print(json.dumps({k:v for k,v in c.items()if k!='rows'}),flush=True)
    for name,source,original,hud in synthetics():
        synthetic_inputs.append(dict(scene=name,source=array_blob(np.concatenate([v.astype('u1').reshape(-1)for v in source])),original=array_blob(original),hud_packet=h.blob(hud)))
        for policy in('mode0control','spatial'):
            row=frame(source,original,hud,policy,0,dict(ref=None,rid=h.m.NO_REF),dict(scene=name,id=0,kind='synthetic'))
            c=dict(scene=name,kind='synthetic',policy=policy,rows=[row],summary=summary([row]));cases.append(c);print(json.dumps({k:v for k,v in c.items()if k!='rows'}),flush=True)
    assert h.pins()==before
    result=dict(schema='gamebub-spatial-v38',source_sha256=before,cases=cases,synthetic_inputs=synthetic_inputs,
        profile=dict(magic='SP38',inner_magic='TS38',profile_tag=model.PROFILE.hex(),outer_format=model.OUTER.format,inner_format=model.INNER.format,
                     tile_blocks=[2,2],block_pixels=[8,8],mode_names=['temporal','verticalResidualEdge','horizontalResidualEdge','DCavailableResidualEdges'],
                     qmap='ROI8/background16',lambda_value=1,DC_rounding='floor((sum+denominator//2)/denominator)',hidden_commit=128),
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['NewSP38/TS38profile, independent2x2-blocktiles perplane. Modesreadonlyalreadyreconstructedadjacentedgeswithintile, temporalbasekey128/Powncanonicalref.',
               'Bothcontrol/spatial useactualquantize/inverse sameQ14/qmap, noRDO/pruning. SpatialselectorusesexactisolatedCP02byteproxyandYUVSSE; actualmodeandfullplaneentropybytesarepaid.',
               'Hiddensafe8blocks forcedmode0/coeffzero/commit128BEFORElaterneighbors; compactgrammaromitsfixedhiddenmodes/coeffs. PerblockcandidateSSE/packetbytecostsretained, notunselectedfullframebitstreams.',
               'TwoREUSED12frameMassEffectprefixes andthreesyntheticone-framefixtures, separateownacceptedhistories. Noheldoutcorpus, perceptionmetric, nativecodeccomparisonorhardwareproof.',
               'Encodeclocksincludevalidation/allcandidateforwardquantinverse+exactproxycosts/selectedentropy+modepacking/headers. Fixture/source/HUDgeneration, metrics/hashes/archiveIO, independentdecode/network/displayexcluded. Singleclockperframe,nopairedspeedclaim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
