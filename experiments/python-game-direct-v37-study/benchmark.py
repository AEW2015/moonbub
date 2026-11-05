"""Paired equivalent one-output senders, plus own causal byte-identical replay."""
from dataclasses import replace
import json,platform,statistics,time
import numpy as np
import helpers as h
model=h.module('direct37_benchmark_model',h.HERE/'model.py')

def clock(fn):
    t=time.perf_counter_ns();v=fn();return v,(time.perf_counter_ns()-t)/1e6

def prepare(source,ref,fid,rid,motion=False):
    p=h.m.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=rid,
        block_size=32,motion_mode='zero',motion_precision='half',penalty=0)
    if motion and ref is not None:
        vectors=np.empty((15,23,2),np.int8);vectors[:]=(-3,1)
        prediction=h.m.predict(ref,vectors,32)
        p=replace(p,motion_mode='block',vector_bytes=h.m.base.pack_vectors(vectors),prediction=prediction,
                  raw_coefficients=h.m.base.old._forward(source,prediction))
    return p

def sender(kind,source,ref,fid,rid,q,hud,motion):
    p=prepare(source,ref,fid,rid,motion)
    if kind=='direct':return model.encode_prepared(p,q,hud)
    full,_,_=h.m.encode_prepared(p,q)
    inner,pixels,work=h.canonical.skip_inner(full,p.prediction)
    normalized=h.canonical.normalize(pixels)
    packet=h.canonical.wrap(inner,hud,normalized,skip=True)
    return packet,normalized,work

def metric(planes,original,parts):
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(planes)),tuple(v['words'] for v in parts))
    return h.n.metric(original,display),h.n.digest(display)

def run(inp,oldcase,hudcase,motion=False):
    rx=h.canonical.Receiver();ref=None;rid=h.m.NO_REF;rows=[]
    source_rows=inp['rows'][:6] if motion else inp['rows']
    oldrows=oldcase['rows']
    for src,oldrow,hu in zip(source_rows,oldrows,hudcase['rows'][:len(source_rows)],strict=True):
        fid=src['id'];key=fid%24==0
        if key:ref=None;rid=h.m.NO_REF
        source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD)
        q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        timings={'proof':[],'direct':[]};outputs={};orders=[]
        # Three alternating paired repetitions for every frame, including
        # analysis, quantize/RDO/planning, entropy, inverse, normalize and wrap.
        for rep in range(3):
            order=('proof','direct') if (fid+rep)%2==0 else ('direct','proof');orders.append(list(order))
            for kind in order:
                outputs[kind],wall=clock(lambda:sender(kind,source,ref,fid,rid,q,hud,motion));timings[kind].append(wall)
            assert outputs['proof'][0]==outputs['direct'][0]
            for a,b in zip(outputs['proof'][1],outputs['direct'][1],strict=True):np.testing.assert_array_equal(a,b)
        wire,normalized,work=outputs['direct']
        archived=h.raw(oldrow['skip']['packet'],h.HERE.parent/'python-game-canonical-v36-study')
        assert wire==archived,'CN36 archived skip byte mismatch'
        (decoded,parts),decode_ms=clock(lambda:rx.receive(wire))
        for a,b in zip(decoded,normalized,strict=True):np.testing.assert_array_equal(a,b)
        quality,tag=metric(decoded,original,parts)
        assert quality==oldrow['skip']['hybrid'] and tag==oldrow['skip']['display_sha256']
        meta=h.canonical.parse(wire)
        row=dict(id=fid,key=key,reference_id=rid,reference_tag=meta['reference_tag'].hex(),
                 source_sha256=src['common_yuv420_u8_sha256'],background=16,
                 packet=h.blob(wire),inner=h.blob(meta['inner']),complete_bytes=len(wire),inner_bytes=len(meta['inner']),
                 hud_bytes=len(hud),binding_bytes=80,hybrid=quality,display_sha256=tag,normalized_tag=h.m.C.reference_tag(decoded).hex(),
                 paired_timing_ms=timings,paired_order=orders,paired_median_ms={k:statistics.median(v) for k,v in timings.items()},
                 direct_work=work,receiver_ms=decode_ms,configured_vector_halfpel=None if key or not motion else [-3,1])
        rows.append(row);ref=decoded;rid=fid
        if (fid+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames=fid+1,motion=motion)),flush=True)
    summary=dict(frames=len(rows),complete_bytes=sum(r['complete_bytes'] for r in rows),maximum_complete_bytes=max(r['complete_bytes'] for r in rows),
                 mean_paired_medians_ms={k:statistics.mean(r['paired_median_ms'][k] for r in rows) for k in ('proof','direct')},
                 removed_nonzero_coefficients=sum(r['direct_work']['removed_nonzero_coefficients'] for r in rows))
    summary['paired_sender_ratio']=summary['mean_paired_medians_ms']['proof']/summary['mean_paired_medians_ms']['direct']
    summary['active_mse']=sum(r['hybrid']['active_squared_error'] for r in rows)/sum(r['hybrid']['active_channel_samples'] for r in rows)
    return dict(scene=inp['scene'],rows=rows,summary=summary)

def main():
    pins=h.pins();old=h.load(h.HERE.parent/'python-game-canonical-v36-study/results.json')
    inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    for inp in inputs:
        cases.append(run(inp,next(c for c in old['cases'] if c['scene']==inp['scene']),next(c for c in huds if c['scene']==inp['scene'])))
        print(json.dumps(cases[-1]['summary']),flush=True)
    inp=inputs[0];motion=run(inp,old['motion_probe'],next(c for c in huds if c['scene']==inp['scene']),True)
    assert h.pins()==pins
    result=dict(schema='gamebub-direct-v37',source_sha256=pins,cases=cases,motion_probe=motion,
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['Three alternating paired repetitions EVERYframe; both one-outputsender clocks include complete fixedpolicy analysis+quantization+RDO+originalglobalreversion decisions+entropy+reconstruction+normalization+CN36wrapper.',
               'Proofsender excludes discarded canonicalFULL normalization/wrapper fromv36campaign, making a fair one-skip-outputbaseline ratherthan comparing against twooutputproofcost.',
               'Directsender avoids fullpacketserialize/decode and discardedfullinverse but retains fullforwardtransform, originalRDO and originallegacy-size reversionplanning for exact visibledecisions.',
               'Compiledplan setup importedonce outsideframe clocks; fixture/HUDreads, archives, metrics/equality, receiver, transport anddisplay excluded.',
               'Actualowncausal96mainframesplus6directedfractionalmotionframes, eachbyteidentical toarchivedv36skip. Noheldoutgameplay or nativeendpoint30fps claim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
