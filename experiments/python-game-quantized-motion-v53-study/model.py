"""Quantized MB proxy selectors; actual whole-frame Pareto gate remains final."""
import time
import numpy as np
import helpers as h
fine=h.bound('quantmotion53_frozen_fine39',h.HERE.parent/'python-game-signal-v39-study/model.py',h)
POLICIES=('zero','mixed_score4','mixed_pareto')

def geometry(axis):
    height,width=(480,720)if axis==0 else(240,360);size=32 if axis==0 else 16
    yy,xx=np.mgrid[:height,:width];pixel_ids=(yy//size)*23+xx//size
    by,bx=np.mgrid[:height//8,:width//8];block_ids=(by//(size//8))*23+bx//(size//8)
    return pixel_ids.reshape(-1),block_ids.reshape(-1)

def prepare(source,reference,*,frame_id,reference_id):
    started=time.perf_counter_ns()
    zero=h.analysis.analyze_planes(source,reference,frame_id=frame_id,reference_id=reference_id)
    grid=h.global_search.analyze_with(h.m,source,reference,frame_id=frame_id,reference_id=reference_id,policy='global_grid',avoid_rects=h.n.ROIS)
    analysis_ms=(time.perf_counter_ns()-started)/1e6;q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    assert zero.reference_tag==grid.reference_tag
    costs=np.zeros((345,2,3),np.int64);quantized=[];reconstructions=[]
    for choice,p in enumerate((zero,grid)):
        coeff=[c.copy()for c in h.m.base._quantize(p.raw_coefficients,q,720,480)]
        for c,safe in zip(coeff,h.base.canonical.HIDDEN,strict=True):c[safe]=0
        rebuilt=h.m.gm.reconstruct(tuple(coeff),p.prediction,q,720,480);normalized=h.base.maskplan.apply_plan(rebuilt,h.base.PLAN)
        quantized.append(tuple(coeff));reconstructions.append(normalized)
        for axis,(src,pixels,c,safe)in enumerate(zip(p.source,normalized,coeff,h.base.canonical.HIDDEN,strict=True)):
            pixel_ids,block_ids=geometry(axis);height,width=src.shape
            hidden=safe.reshape(height//8,width//8).repeat(8,0).repeat(8,1)
            error=np.square(src.astype(np.int64)-pixels);error[hidden]=0
            np.add.at(costs[:,choice,0],pixel_ids,error.reshape(-1))
            bits=fine.coefficient_bits(c);bits[safe]=0;np.add.at(costs[:,choice,1],block_ids,bits)
    mw,mh=h.m.base._grid(720,480,32)
    vectors=np.zeros((mh,mw,2),np.int8)if grid.key else h.m.base.unpack_vectors(grid.vector_bytes,mw,mh)
    costs[:,1,2]=16*np.any(vectors.reshape(-1,2)!=0,axis=1)
    z=costs[:,0];g=costs[:,1];zbits=z[:,1]+z[:,2];gbits=g[:,1]+g[:,2]
    maps=dict(mixed_score4=(g[:,0]+4*gbits<z[:,0]+4*zbits),
        mixed_pareto=(g[:,0]<=z[:,0])&(gbits<=zbits)&((g[:,0]<z[:,0])|(gbits<zbits)))
    maps={name:values.reshape(mh,mw)for name,values in maps.items()}
    work=dict(shared_analysis_ms=analysis_ms,shared_prepare_ms=(time.perf_counter_ns()-started)/1e6,
        shared_search_calls=0 if grid.key else 1,shared_forward_plane_calls=6,proxy_quantized_planes=6,proxy_inverse_reconstructions=2,
        proxy='visible8x8 fine39 coefficient bits +16bits per nonzeroMB; exact pre-RDO normalizedYUV SSE excluding canonical-safe full8x8 blocks',
        source_analysis={'zero':zero.work,'global_grid':grid.work},macroblocks=345)
    return zero,grid,q,costs.reshape(mh,mw,2,3),maps,vectors,work

def mix(zero,grid,choice,grid_vectors):
    start=time.perf_counter_ns()
    if choice.dtype!=np.bool_ or choice.shape!=(15,23):raise ValueError('fixed bool MB choice map')
    for name in('epoch','frame_id','reference_id','width','height','key','block_size','reference_tag'):
        if getattr(zero,name)!=getattr(grid,name):raise ValueError('matching owned analyses')
    if zero.owner is not h.m._PREPARED_OWNER or grid.owner is not h.m._PREPARED_OWNER:raise ValueError('owned analysis module')
    flat=choice.reshape(-1);prediction=[];raw=[]
    for axis,(pz,pg,rz,rg)in enumerate(zip(zero.prediction,grid.prediction,zero.raw_coefficients,grid.raw_coefficients,strict=True)):
        pixels,blocks=geometry(axis);pred=np.where(flat[pixels].reshape(pz.shape),pg,pz).copy()
        coeff=np.where(flat[blocks,None,None],rg,rz).copy();pred.setflags(write=False);coeff.setflags(write=False)
        prediction.append(pred);raw.append(coeff)
    vectors=np.where(choice[...,None],grid_vectors,0).astype(np.int8)
    vector_bytes=b''if zero.key else h.m.base.pack_vectors(vectors)
    source=tuple(v.copy()for v in zero.source)
    for v in source:v.setflags(write=False)
    work=dict(mixed_macroblocks=int(choice.sum()),nonzero_vectors=int(np.count_nonzero(np.any(vectors!=0,axis=2))),
        shared_analysis_paid=True,repeated_search_calls=0,repeated_forward_plane_calls=0,
        prediction_array_bytes=sum(v.nbytes for v in prediction),raw_coefficient_array_bytes=sum(v.nbytes for v in raw),source_array_bytes=sum(v.nbytes for v in source),
        materialize_ms=(time.perf_counter_ns()-start)/1e6)
    prepared=h.m.Prepared(h.m._PREPARED_OWNER,zero.epoch,zero.frame_id,zero.reference_id,720,480,zero.key,32,'block',zero.reference_tag,
        vector_bytes,tuple(prediction),tuple(raw),source,work)
    return prepared,vectors,work

def encode(prepared,qmap,hud):
    started=time.perf_counter_ns();cs37,normalized,coeff,payloads,work=h.producer.encode_proposal(prepared,qmap,hud)
    packet,attempts,abwork=h.producer.transcode(cs37,coeff,payloads)
    return dict(packet=packet,cs37=cs37,normalized=normalized,coefficients=coeff,payloads=payloads,proposal_work=work,attempts=attempts,
                transcode_work=abwork,encode_ms=(time.perf_counter_ns()-started)/1e6,prepared=prepared)

def choose(candidates):
    if set(candidates)!=set(POLICIES)or any(type(v)is not int or v<0 for pair in candidates.values()for v in pair):raise ValueError('fixed integer actual byte/SSE candidates')
    zero=candidates['zero'];zb,zs=zero
    admitted=[name for name in POLICIES[1:]if candidates[name][0]<=49152 and candidates[name][0]<=zb and candidates[name][1]<=zs and(candidates[name][0]<zb or candidates[name][1]<zs)]
    if admitted:return min(admitted,key=lambda name:(candidates[name][0],candidates[name][1],POLICIES.index(name)))
    return 'zero'if zb<=49152 else None
