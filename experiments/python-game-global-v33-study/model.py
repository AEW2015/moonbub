"""Low-effort camera translation with bounded local exceptions, GM27 unchanged.

Global search uses sparse active, non-UI samples and a trimmed block score.
Local choices include zero and a small menu around the global vector. Every
choice still runs actual prediction, transform, rate and source quality checks.
"""
from pathlib import Path
import importlib.util
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('global33_adaptive29',HERE.parent/'python-game-adaptive-v29-study/model.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
POLICIES=('global_cross','global_grid')


def offsets(values,cross=False):
    return sorted(((x,y) for y in values for x in values if not cross or x==0 or y==0),
                  key=lambda v:(abs(v[0])+abs(v[1]),v[1],v[0]))


def estimate(source,reference,block_size=32,policy='global_cross',avoid_rects=()):
    if policy not in POLICIES:raise ValueError('declared camera policy')
    src=a.m.old._planes(source);h,w=src[0].shape;ref=a.m.old._planes(reference,(w,h))
    mw,mh=a.m.old._grid(w,h,block_size);zero=np.zeros((mh,mw,2),np.int8)
    avoid_rects=tuple(avoid_rects)
    for rect in avoid_rects:
        if len(rect)!=4 or any(type(v)is not int for v in rect):raise ValueError('integer avoid rectangle')
        x,y,rw,rh=rect
        if min(x,y)<0 or min(rw,rh)<=0 or x+rw>w or y+rh>h:raise ValueError('bounded avoid rectangle')
    all_blocks=np.ones((mh,mw),bool)
    work=dict(search_policy=policy,quiet_threshold=2,candidate_vectors=0,coarse_candidate_vectors=0,
              refinement_candidate_maps=0,candidate_block_cost_evaluations=0,sad_sample_operations=0,
              reference_sample_fetches=0,source_sample_fetches=0,nonzero_vectors=0,
              fractional_luma_vectors=0,fractional_chroma_vectors=0,quiet_blocks=0,active_blocks=0,
              screen_sample_operations=0,global_vector=[0,0],global_score_blocks=0,
              global_coarse_stride=16,global_fine_stride=8,local_stride=4,score_calls=[])

    def cost(samples,vectors,integer,label):
        count=sum(len(v[0]) for v in samples)
        result=a.compact_cost(samples,vectors,integer)
        work['sad_sample_operations']+=count
        work['source_sample_fetches']+=count
        work['reference_sample_fetches']+=(1 if integer else 4)*count
        work['candidate_vectors']+=1
        work['candidate_block_cost_evaluations']+=int(np.count_nonzero(np.bincount(samples[0][4],minlength=mw*mh)))
        work['score_calls'].append(dict(label=label,samples=count,reference_gathers=(1 if integer else 4)*count))
        return result

    screen=a.compact_samples(src,ref,block_size,4,all_blocks)
    zcost=cost(screen,zero,True,'screen');counts=np.zeros(mh*mw,np.int64)
    for s,r,y,x,ids,den,weight,_,_ in screen:counts+=weight*np.bincount(ids,minlength=mw*mh)
    active=zcost>2*counts.reshape(mh,mw)
    work.update(quiet_blocks=int((~active).sum()),active_blocks=int(active.sum()),screen_sample_operations=sum(len(v[0]) for v in screen))
    if not active.any():return zero,work
    global_mask=active.copy()
    for rect in avoid_rects:
        x,y,rw,rh=rect
        global_mask[y//block_size:(y+rh+block_size-1)//block_size,x//block_size:(x+rw+block_size-1)//block_size]=False
    if not global_mask.any():global_mask=active.copy()
    work['global_score_blocks']=int(global_mask.sum())

    def global_score(samples,vector,integer,label):
        vectors=np.zeros_like(zero);vectors[global_mask]=vector
        costs=cost(samples,vectors,integer,label)[global_mask]
        # Compare a fixed count of least-error blocks; no future frames or
        # incumbent estimated motion is consumed by this heuristic.
        weights=np.zeros(mh*mw,np.int64)
        for s,r,y,x,ids,den,weight,_,_ in samples:weights+=weight*np.bincount(ids,minlength=mw*mh)
        normalized=costs*1024//np.maximum(weights.reshape(mh,mw)[global_mask],1)
        keep=max(1,(3*len(normalized)+3)//4)
        return int(np.partition(normalized,keep-1)[:keep].sum())

    coarse=a.compact_samples(src,ref,block_size,16,global_mask)
    best=None;global_vector=(0,0)
    for vector in offsets(tuple(range(-16,17,4))):
        score=global_score(coarse,vector,True,'global_coarse')
        if best is None or score<best:best,global_vector=score,vector
        work['coarse_candidate_vectors']+=1
    if policy=='global_cross':
        fine=a.compact_samples(src,ref,block_size,8,global_mask);origin=global_vector;best=None
        for dx,dy in offsets((-2,-1,0,1,2)):
            vector=(origin[0]+dx,origin[1]+dy)
            score=global_score(fine,vector,False,'global_fine')
            if best is None or score<best:best,global_vector=score,vector
            work['refinement_candidate_maps']+=1
    work['global_vector']=list(global_vector)
    samples=a.compact_samples(src,ref,block_size,4,active)
    chosen=zero.copy();best=cost(samples,chosen,True,'local_zero')
    menu=offsets((-2,-1,0,1,2),cross=True) if policy=='global_cross' else offsets((-4,0,4))
    seen={(0,0)}
    for dx,dy in menu:
        vector=tuple(np.clip(np.asarray(global_vector,dtype=np.int32)+(dx,dy),-18,18).tolist())
        # Grid choices retain integer coordinates for both luma and chroma.
        if policy=='global_grid':vector=tuple(int(np.clip(round(v/4)*4,-16,16)) for v in vector)
        if vector in seen:continue
        seen.add(vector);candidate=zero.copy();candidate[active]=vector
        scores=cost(samples,candidate,policy=='global_grid','local_exception')
        improve=(scores<best)&active;chosen[improve]=candidate[improve];best[improve]=scores[improve]
    work.update(local_distinct_vectors=len(seen),nonzero_vectors=int(np.count_nonzero(np.any(chosen!=0,axis=2))),
                fractional_luma_vectors=int(np.count_nonzero(np.any(chosen%2,axis=2))),
                fractional_chroma_vectors=int(np.count_nonzero(np.any(chosen%4,axis=2))))
    assert np.max(np.abs(chosen.astype(np.int16)))<=18 and not np.any(chosen[~active])
    return chosen,work


def analyze_with(runtime,source,reference,*,epoch=25,frame_id=0,reference_id=4294967295,
                 block_size=32,policy='global_cross',avoid_rects=()):
    if policy not in POLICIES:raise ValueError('declared camera policy')
    old=runtime.base;started=time.perf_counter_ns();src=old._planes(source);h,w=src[0].shape
    old._grid(w,h,block_size)
    if not old._id(epoch) or not old._id(frame_id):raise ValueError('bounded frame identity')
    key=reference is None
    if key:
        if reference_id!=old.NO_REF:raise ValueError('key reference')
        prediction=tuple(np.full_like(v,128) for v in src);reftag=old.ZERO_TAG;vector_bytes=b''
        search=dict(search_policy=policy,sad_sample_operations=0,reference_sample_fetches=0,source_sample_fetches=0,quiet_blocks=0,active_blocks=0)
        vector_work={};search_ms=0.;taps=0
    else:
        if not old._id(reference_id) or reference_id>=frame_id:raise ValueError('past reference')
        ref=old._planes(reference,(w,h));reftag=old.C.reference_tag(ref);start=time.perf_counter_ns()
        vectors,search=estimate(src,ref,block_size,policy,avoid_rects)
        search_ms=(time.perf_counter_ns()-start)/1e6
        prediction,predict_info=runtime.taps.predict_with_info(ref,vectors,block_size)
        taps=predict_info['reference_sample_fetches'];vector_bytes,vector_work=old.pack_vectors(vectors,return_work=True)
    start=time.perf_counter_ns();raw=old.old._forward(src,prediction);transform_ms=(time.perf_counter_ns()-start)/1e6
    retained=tuple(v.copy() for v in src)
    for v in prediction+retained:v.setflags(write=False)
    work=dict(key=key,motion_mode='block',block_size=block_size,search_policy=policy,search=search,
              motion_map=vector_work,search_ms=search_ms,forward_plane_calls=3,transform_ms=transform_ms,
              prediction_reference_sample_fetches=taps,prediction_array_bytes=sum(v.nbytes for v in prediction),
              raw_coefficient_array_bytes=sum(v.nbytes for v in raw),source_array_bytes=sum(v.nbytes for v in retained),
              retained_analysis_array_bytes=sum(v.nbytes for v in prediction+raw+retained),
              analysis_wall_ms=(time.perf_counter_ns()-started)/1e6,reference_tag=reftag.hex())
    return old.Prepared(old._PREPARED_OWNER,epoch,frame_id,reference_id,w,h,key,block_size,'block',reftag,
                        vector_bytes,prediction,raw,retained,work)
