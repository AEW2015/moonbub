"""Current-source quiet-block search gating with unchanged GM27 semantics.

An integer threshold is a sampled weighted MAE gate, not a full-resolution
error guarantee. All retained pixels are still predicted and transformed.
"""
from pathlib import Path
import importlib.util
import sys
import time
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('adaptive29_search28',HERE.parent/'python-game-search-v28-study/model.py')
oldsearch=importlib.util.module_from_spec(spec);sys.modules[spec.name]=oldsearch;spec.loader.exec_module(oldsearch)
m=oldsearch.m
POLICIES={'adaptive_zero2':2,'adaptive_zero4':4}


def compact_samples(source,reference,block_size,stride,active):
    """Gather actual scored points only; IDs preserve partial edge blocks."""
    mh,mw=active.shape;out=[]
    for plane,(src,ref) in enumerate(zip(source,reference)):
        bs=block_size if plane==0 else block_size//2
        yy,xx=np.meshgrid(np.arange(0,src.shape[0],stride,dtype=np.int32),np.arange(0,src.shape[1],stride,dtype=np.int32),indexing='ij')
        ids=(yy//bs)*mw+xx//bs;keep=active.ravel()[ids]
        y,x,i=yy[keep],xx[keep],ids[keep]
        out.append((src[y,x].astype(np.int32),ref,y,x,i,2 if plane==0 else 4,1 if plane==0 else 2,mh,mw))
    return out


def compact_cost(samples,vectors,integer=False):
    result=np.zeros(vectors.shape[0]*vectors.shape[1],np.int64)
    for src,ref,yy,xx,ids,den,weight,mh,mw in samples:
        v=vectors.reshape(-1,2)[ids].astype(np.int32)
        qx,qy=v[:,0],v[:,1];ix,iy=qx//den,qy//den
        x0=np.clip(xx+ix,0,ref.shape[1]-1);y0=np.clip(yy+iy,0,ref.shape[0]-1)
        if integer:pred=ref[y0,x0]
        else:
            fx,fy=qx%den,qy%den
            x1=np.clip(xx+ix+1,0,ref.shape[1]-1);y1=np.clip(yy+iy+1,0,ref.shape[0]-1)
            total=((den-fx)*(den-fy)*ref[y0,x0]+fx*(den-fy)*ref[y0,x1]+(den-fx)*fy*ref[y1,x0]+fx*fy*ref[y1,x1])
            pred=(total+den*den//2)//(den*den)
        result+=np.bincount(ids,weights=weight*np.abs(src-pred),minlength=mh*mw).astype(np.int64)
    return result.reshape(vectors.shape[:2])


def estimate_vectors(source,reference,block_size=16,mode='block',penalty=0,motion_precision='half',search_policy='adaptive_zero2'):
    if search_policy not in POLICIES:raise ValueError('declared adaptive policy')
    if mode not in ('zero','block','global') or type(penalty) is not int or not 0<=penalty<=4096:raise ValueError('motion policy')
    if motion_precision not in ('coarse','integer','half'):raise ValueError('motion precision')
    src=m.old._planes(source);h,w=src[0].shape;ref=m.old._planes(reference,(w,h));mw,mh=m.old._grid(w,h,block_size)
    chosen=np.zeros((mh,mw,2),np.int8)
    work=dict(search_policy=search_policy,quiet_threshold=POLICIES[search_policy],candidate_vectors=0,coarse_candidate_vectors=0,refinement_candidate_maps=0,candidate_block_cost_evaluations=0,sad_sample_operations=0,reference_sample_fetches=0,source_sample_fetches=0,nonzero_vectors=0,fractional_luma_vectors=0,fractional_chroma_vectors=0,motion_precision=motion_precision,quiet_blocks=0,active_blocks=0,screen_sample_operations=0)
    if mode=='zero':return chosen,work
    screen=compact_samples(src,ref,block_size,4,np.ones((mh,mw),bool));nscreen=sum(len(v[0]) for v in screen)
    zero=compact_cost(screen,chosen,integer=True)
    counts=np.zeros(mh*mw,np.int64)
    for a,b,y,x,ids,den,weight,_,_ in screen:counts+=weight*np.bincount(ids,minlength=mh*mw)
    active=zero>POLICIES[search_policy]*counts.reshape(mh,mw)
    if mode=='global':active[:]=bool(np.any(active))
    work.update(quiet_blocks=int((~active).sum()),active_blocks=int(active.sum()),screen_sample_operations=nscreen,candidate_block_cost_evaluations=mh*mw,sad_sample_operations=nscreen,reference_sample_fetches=nscreen,source_sample_fetches=nscreen)
    if not active.any():return chosen,work
    samples=compact_samples(src,ref,block_size,4,active);nsamples=sum(len(v[0]) for v in samples)
    candidates=sorted(((dx,dy) for dy in range(-16,17,4) for dx in range(-16,17,4)),key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
    best=None
    for dx,dy in candidates:
        candidate=np.zeros_like(chosen);candidate[active]=(dx,dy)
        costs=compact_cost(samples,candidate,True)+penalty*bool(dx or dy)
        if mode=='global':costs=np.full(costs.shape,int(costs[active].sum()),np.int64)
        if best is None:best=costs;chosen=candidate.copy()
        else:
            improve=(costs<best)&active;chosen[improve]=candidate[improve];best[improve]=costs[improve]
    work.update(candidate_vectors=81,coarse_candidate_vectors=81,candidate_block_cost_evaluations=work['candidate_block_cost_evaluations']+81*int(active.sum()),sad_sample_operations=work['sad_sample_operations']+81*nsamples,reference_sample_fetches=work['reference_sample_fetches']+81*nsamples,source_sample_fetches=work['source_sample_fetches']+81*nsamples)
    if motion_precision!='coarse':
        samples=compact_samples(src,ref,block_size,2,active);nsamples=sum(len(v[0]) for v in samples)
        offsets=(-2,0,2) if motion_precision=='integer' else (-2,-1,0,1,2)
        offsets=sorted(((dx,dy) for dy in offsets for dx in offsets),key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
        origin=chosen.copy();best=None
        for dx,dy in offsets:
            candidate=origin.copy();candidate[active]+=np.array((dx,dy),np.int8)
            costs=compact_cost(samples,candidate)+penalty*np.any(candidate!=0,axis=2)
            if mode=='global':costs=np.full(costs.shape,int(costs[active].sum()),np.int64)
            if best is None:best=costs;chosen=candidate.copy()
            else:
                improve=(costs<best)&active;chosen[improve]=candidate[improve];best[improve]=costs[improve]
        nfine=len(offsets)
        work.update(candidate_vectors=81+nfine,refinement_candidate_maps=nfine,candidate_block_cost_evaluations=work['candidate_block_cost_evaluations']+nfine*int(active.sum()),sad_sample_operations=work['sad_sample_operations']+nfine*nsamples,reference_sample_fetches=work['reference_sample_fetches']+4*nfine*nsamples,source_sample_fetches=work['source_sample_fetches']+nfine*nsamples)
    work.update(nonzero_vectors=int(np.count_nonzero(np.any(chosen!=0,axis=2))),fractional_luma_vectors=int(np.count_nonzero(np.any(chosen%2,axis=2))),fractional_chroma_vectors=int(np.count_nonzero(np.any(chosen%4,axis=2))))
    return chosen,work


def analyze_with(gm27, source, reference, *, epoch=1, frame_id=0, reference_id=m.NO_REF,
                 block_size=16, motion_mode='block', penalty=0, motion_precision='half',
                 search_policy='adaptive_zero2'):
    """Construct Prepared belonging to the explicitly supplied frozen GM27.

    No module globals or imported functions are changed. Full-resolution frozen
    prediction, forward transform, source retention and MV packing are paid.
    """
    old = gm27.old
    started = time.perf_counter_ns()
    src = old._planes(source); h,w = src[0].shape
    mw,mh = old._grid(w,h,block_size)
    if not old._id(epoch) or not old._id(frame_id): raise ValueError('bounded epoch/frame')
    if motion_mode not in ('zero','global','block') or type(penalty) is not int or not 0<=penalty<=4096:
        raise ValueError('motion policy')
    if motion_precision not in ('coarse','integer','half'): raise ValueError('motion precision')
    if search_policy not in POLICIES: raise ValueError('declared sampled search policy')
    key = reference is None
    if key:
        if type(reference_id) is not int or reference_id != old.NO_REF: raise ValueError('key reference identity')
        prediction = tuple(np.full_like(v,128) for v in src)
        vector_bytes = b''; reftag = old.ZERO_TAG; search_ms = 0.
        search = dict(search_policy=search_policy,candidate_vectors=0,sad_sample_operations=0,
                      reference_sample_fetches=0,source_sample_fetches=0,
                      candidate_block_cost_evaluations=0,coarse_candidate_vectors=0,
                      refinement_candidate_maps=0,nonzero_vectors=0)
        vector_work = dict(candidate_representations=0,candidates=[],rice_axis_trials=0,
                           rice_delta_values=0,rice_value_encode_trials=0,selected_mode=None,pack_wall_ms=0.)
    else:
        if not old._id(reference_id) or reference_id>=frame_id: raise ValueError('past reference identity')
        ref = old._planes(reference,(w,h)); reftag = old.C.reference_tag(ref)
        began = time.perf_counter_ns()
        vectors,search = estimate_vectors(src,ref,block_size,motion_mode,penalty,motion_precision,search_policy)
        search_ms = (time.perf_counter_ns()-began)/1e6
        prediction = old.predict(ref,vectors,block_size)
        vector_bytes,vector_work = old.pack_vectors(vectors,return_work=True)
    began = time.perf_counter_ns(); raw = old._forward(src,prediction)
    transform_ms = (time.perf_counter_ns()-began)/1e6
    for v in prediction: v.setflags(write=False)
    retained_source = tuple(v.copy() for v in src)
    for v in retained_source: v.setflags(write=False)
    work = dict(key=key,motion_mode=motion_mode,block_size=block_size,search_policy=search_policy,
                search=search,motion_map=vector_work,search_ms=search_ms,forward_plane_calls=3,
                transform_ms=transform_ms,prediction_reference_sample_fetches=0 if key else 4*sum(v.size for v in src),
                prediction_array_bytes=sum(v.nbytes for v in prediction),
                raw_coefficient_array_bytes=sum(v.nbytes for v in raw),source_array_bytes=sum(v.nbytes for v in retained_source),
                retained_analysis_array_bytes=sum(v.nbytes for v in prediction+raw+retained_source),
                analysis_wall_ms=(time.perf_counter_ns()-started)/1e6,reference_tag=reftag.hex())
    return old.Prepared(old._PREPARED_OWNER,epoch,frame_id,reference_id,w,h,key,block_size,
                        motion_mode,reftag,vector_bytes,prediction,raw,retained_source,work)


def analyze_planes(source, reference, **kwargs):
    return analyze_with(m,source,reference,**kwargs)
