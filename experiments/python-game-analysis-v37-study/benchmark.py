"""Paired whole fixedpolicy sender clocks after exact zero-map analysis change."""
import hashlib,json,platform,statistics,time
import numpy as np
import helpers as h
model=h.module('analysis37_benchmark_model',h.HERE/'model.py')
direct=h.module('analysis37_frozen_direct_model',h.HERE.parent/'python-game-direct-v37-study/model.py')

def clock(fn):
    start=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-start)/1e6
def tag(planes):return hashlib.sha256(b''.join(v.astype('<i2').tobytes() for v in planes)).hexdigest()
def sender(kind,source,ref,fid,rid,q,hud):
    analyzer=h.m.analyze_planes if kind=='direct' else model.analyze_planes
    p=analyzer(source,ref,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
    return (*direct.encode_prepared(p,q,hud),p)

def main():
    pins=h.pins();old=h.load(h.HERE.parent/'python-game-direct-v37-study/results.json')
    inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    for inp in inputs:
        archived=next(c for c in old['cases'] if c['scene']==inp['scene']);hc=next(c for c in huds if c['scene']==inp['scene'])
        rx=h.canonical.Receiver();ref=None;rid=h.m.NO_REF;rows=[]
        for src,oldrow,hu in zip(inp['rows'],archived['rows'],hc['rows'],strict=True):
            fid=src['id'];key=fid%24==0
            if key:ref=None;rid=h.m.NO_REF
            source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD);q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
            samples={'direct':[],'faster':[]};orders=[];outputs={}
            for rep in range(3):
                order=('direct','faster') if (fid+rep)%2==0 else ('faster','direct');orders.append(list(order))
                for kind in order:
                    outputs[kind],wall=clock(lambda:sender(kind,source,ref,fid,rid,q,hud));samples[kind].append(wall)
                assert outputs['direct'][0]==outputs['faster'][0]
                for name in ('prediction','raw_coefficients','source'):
                    for a,b in zip(getattr(outputs['direct'][3],name),getattr(outputs['faster'][3],name),strict=True):np.testing.assert_array_equal(a,b)
            wire,normalized,work,prepared=outputs['faster']
            assert wire==h.raw(oldrow['packet'],h.HERE.parent/'python-game-direct-v37-study')
            (decoded,parts),receiver_ms=clock(lambda:rx.receive(wire))
            for a,b in zip(decoded,normalized,strict=True):np.testing.assert_array_equal(a,b)
            display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)),tuple(v['words'] for v in parts))
            quality=h.n.metric(original,display);displaytag=h.n.digest(display)
            assert quality==oldrow['hybrid'] and displaytag==oldrow['display_sha256']
            meta=h.canonical.parse(wire)
            rows.append(dict(id=fid,key=key,reference_id=rid,reference_tag=prepared.reference_tag.hex(),source_sha256=src['common_yuv420_u8_sha256'],background=16,
                packet=h.blob(wire),inner=h.blob(meta['inner']),complete_bytes=len(wire),inner_bytes=len(meta['inner']),hud_bytes=len(hud),binding_bytes=80,
                hybrid=quality,display_sha256=displaytag,normalized_tag=h.m.C.reference_tag(decoded).hex(),
                prepared_evidence={name+'_sha256':tag(getattr(prepared,name)) for name in ('prediction','raw_coefficients','source')},
                analysis_work=prepared.work,direct_work=work,receiver_ms=receiver_ms,paired_timing_ms=samples,paired_order=orders,
                paired_median_ms={k:statistics.median(v) for k,v in samples.items()}))
            ref=decoded;rid=fid
            if (fid+1)%12==0:print(json.dumps(dict(scene=inp['scene'],frames=fid+1)),flush=True)
        means={k:statistics.mean(r['paired_median_ms'][k] for r in rows) for k in samples}
        summary=dict(frames=48,complete_bytes=sum(r['complete_bytes'] for r in rows),maximum_complete_bytes=max(r['complete_bytes'] for r in rows),
            mean_paired_medians_ms=means,paired_sender_ratio=means['direct']/means['faster'],
            active_mse=sum(r['hybrid']['active_squared_error'] for r in rows)/sum(r['hybrid']['active_channel_samples'] for r in rows))
        cases.append(dict(scene=inp['scene'],rows=rows,summary=summary));print(json.dumps(summary),flush=True)
    assert h.pins()==pins
    result=dict(schema='gamebub-analysis-v37',source_sha256=pins,cases=cases,physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        scope=['Explicitfixedzero/half/block32 analyzer directlyconstructsownedfrozenPrepared; nevercallsoldanalyzeroroldfour-tappredict.',
               'Bothsenderclocksincludevalidation,source/referenceidentity,motionzeroestimate+vectorpack,prediction,fullforward,ownedreadonlysourcecopies,andfrozendirectencode/RDO/entropy/inverse/normalize/wrap.',
               'Every96frameshas3alternatingpairedrepetitions; fixtures/HUDgeneration,metrics/assertions/hashes,archiveIO,receiver,transport/displayexcluded. Fixedcompiledplanimportsetupoutsideclocks.',
               'Actualowncausal96packetsbyteidenticaltofrozendirect37andv36CN36skip. Nocompressionchange,newmotionpolicy,heldoutcorpus,nativeendpointorhardware30fpsproof.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
