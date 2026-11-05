"""Equivalent complete fixedpolicy senders: transcode versus integrated CS37."""
from dataclasses import replace
import json,platform,statistics,time
import numpy as np
import helpers as h
model=h.module('integrated38_active_model',h.HERE/'model.py')
analysis=h.module('integrated38_fastanalysis37',h.HERE.parent/'python-game-analysis-v37-study/model.py')
direct=h.module('integrated38_direct37',h.HERE.parent/'python-game-direct-v37-study/model.py')
implicit=h.module('integrated38_transcode37',h.HERE.parent/'python-game-implicit-v37-study/model.py')
decoder=h.module('integrated38_frozenCS37_decoder',h.HERE.parent/'python-game-implicit-v37-study/verify.py')

def clock(fn):
    start=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-start)/1e6
def prepare(source,ref,fid,rid,motion):
    p=analysis.analyze_planes(source,ref,frame_id=fid,reference_id=rid)
    if motion and ref is not None:
        vectors=np.empty((15,23,2),np.int8);vectors[:]=(-3,1)
        prediction=h.m.taps.predict(ref,vectors,32)
        p=replace(p,motion_mode='block',vector_bytes=h.m.base.pack_vectors(vectors),prediction=prediction,
                  raw_coefficients=h.m.base.old._forward(source,prediction))
    return p
def sender(kind,source,ref,fid,rid,q,hud,motion):
    p=prepare(source,ref,fid,rid,motion)
    if kind=='integrated':return model.encode_prepared(p,q,hud)
    cn36,normalized,direct_work=direct.encode_prepared(p,q,hud)
    wire,transcode_work=implicit.transcode(cn36)
    return wire,normalized,dict(direct=direct_work,transcode=transcode_work)
def run(inp,oldcase,hc,motion=False):
    rx=decoder.Receiver();ref=None;rid=h.m.NO_REF;rows=[]
    count=6 if motion else 48
    for src,prior,hu in zip(inp['rows'][:count],oldcase['rows'],hc['rows'][:count],strict=True):
        fid=src['id'];key=fid%24==0
        if key:ref=None;rid=h.m.NO_REF
        source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD);q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        timings={'baseline':[],'integrated':[]};orders=[];outputs={}
        for rep in range(3):
            order=('baseline','integrated')if(fid+rep)%2==0 else('integrated','baseline');orders.append(list(order))
            for name in order:
                outputs[name],wall=clock(lambda:sender(name,source,ref,fid,rid,q,hud,motion));timings[name].append(wall)
            assert outputs['baseline'][0]==outputs['integrated'][0]
            for a,b in zip(outputs['baseline'][1],outputs['integrated'][1],strict=True):np.testing.assert_array_equal(a,b)
        wire,normalized,work=outputs['integrated'];assert wire==h.raw(prior['packet'],h.HERE.parent/'python-game-implicit-v37-study')
        (decoded,parts,meta),receive_ms=clock(lambda:rx.receive(wire))
        for a,b in zip(decoded,normalized,strict=True):np.testing.assert_array_equal(a,b)
        display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)),tuple(v['words']for v in parts))
        quality=h.n.metric(original,display);displaytag=h.n.digest(display)
        assert quality==prior['hybrid'] and displaytag==prior['display_sha256']
        rows.append(dict(id=fid,key=key,reference_id=rid,reference_tag=meta['reference_tag'].hex(),source_sha256=src['common_yuv420_u8_sha256'],background=16,
            packet=h.blob(wire),complete_bytes=len(wire),inner_bytes=len(wire)-len(hud)-80,hud_bytes=len(hud),binding_bytes=80,
            hybrid=quality,display_sha256=displaytag,normalized_tag=h.m.C.reference_tag(decoded).hex(),
            paired_timing_ms=timings,paired_order=orders,paired_median_ms={name:statistics.median(v)for name,v in timings.items()},
            integrated_work=work,baseline_work=outputs['baseline'][2],receiver_ms=receive_ms,
            configured_vector_halfpel=None if key or not motion else[-3,1]))
        ref=decoded;rid=fid
        if(fid+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames=fid+1,motion=motion)),flush=True)
    means={name:statistics.mean(r['paired_median_ms'][name]for r in rows)for name in timings}
    summary=dict(frames=len(rows),complete_bytes=sum(r['complete_bytes']for r in rows),maximum_complete_bytes=max(r['complete_bytes']for r in rows),
                 mean_paired_medians_ms=means,paired_sender_ratio=means['baseline']/means['integrated'],
                 implicit_planes=sum(sum(p['implicit_selected']for p in r['integrated_work']['planes'])for r in rows),
                 active_mse=sum(r['hybrid']['active_squared_error']for r in rows)/sum(r['hybrid']['active_channel_samples']for r in rows))
    return dict(scene=inp['scene'],kind='fractional_motion'if motion else'main',rows=rows,summary=summary)
def main():
    pins=h.pins();inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];old=h.load(h.HERE.parent/'python-game-implicit-v37-study/results.json');cases=[]
    for inp in inputs:
        case=run(inp,next(c for c in old['cases']if c['scene']==inp['scene']and c['kind']=='main'),next(c for c in huds if c['scene']==inp['scene']))
        cases.append(case);print(json.dumps(case['summary']),flush=True)
    inp=inputs[0];motion=run(inp,next(c for c in old['cases']if c['kind']=='fractional_motion'),next(c for c in huds if c['scene']==inp['scene']),True)
    assert h.pins()==pins
    result=dict(schema='gamebub-integrated-v38',source_sha256=pins,cases=cases,motion_probe=motion,
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['All96main+6motionframeshave3alternatingpairs. Bothcompletefixedpolicyclocksincludesamefastanalysis37andoriginalRDO/globallegacyreversiondecisions.',
               'Baseline emitsCN36thenfrozenimplicittranscoder. Integratedplansfullgridandcompactcomponentsbutserializesonlywinner,rebuildsonceandwrapsGS37/CS37directly.',
               'NoCN36intermediate,coefficientsyntaxparse,transcode,discardedcomponentserializationorredundantinverseinintegratedpath. Rawforward/RDOremainpaid.',
               'Compiledgeometryimportsetup,source/HUDfixtureloading/generation,archiveIO,metricsequalityandreceiver/network/displayexcludedfromsenderclocks.',
               'ActualCS37bytesandcanonicalrefsidenticaltoarchivedv37; nochangedcompressiondecisionsorquality,heldoutgameplay,nativeendpointorhardware30fpsproof.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
