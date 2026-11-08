"""Bounded sampled encoder search; frozen GM27 syntax and reconstruction.

Only current source and the caller's exact accepted reconstructed reference are
read. Sampling changes the encoder's vector choice, never decoder geometry.
"""
from pathlib import Path
import importlib.util
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('search28_frozen_gm27', HERE.parent / 'python-game-unified-v27-study/model.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
POLICIES = {'sample4': (4, 4), 'sample2': (2, 2), 'sample4_refine2': (4, 2)}


def _samples(source, reference, block_size, stride):
    """Top-left stride samples in each plane, including partial edge blocks."""
    h, w = source[0].shape
    mw, mh = (w + block_size - 1)//block_size, (h + block_size - 1)//block_size
    result = []
    for plane, (src, ref) in enumerate(zip(source, reference)):
        bs = block_size if plane == 0 else block_size//2
        ph, pw = src.shape
        yy = np.arange(0, ph, stride, dtype=np.int32)[:, None]
        xx = np.arange(0, pw, stride, dtype=np.int32)[None, :]
        result.append((src[::stride, ::stride].astype(np.int32), ref, yy, xx,
                       yy//bs, xx//bs, bs//stride, 2 if plane == 0 else 4,
                       1 if plane == 0 else 2, mw, mh))
    return result


def _sampled_cost(samples, vectors, *, integer=False):
    """Exact frozen integer bilinear rounding at the sampled coordinates.

    integer=True is only valid for vectors divisible by four half-luma units;
    all three planes then require one read per sampled point. Refinement uses
    the four-tap expression even if one or more weights are zero.
    """
    costs = np.zeros(vectors.shape[:2], np.int64)
    for src, ref, yy, xx, by, bx, sb, den, weight, mw, mh in samples:
        v = vectors[by, bx].astype(np.int32)
        qx, qy = v[..., 0], v[..., 1]
        ix, iy = qx//den, qy//den
        ph, pw = ref.shape
        x0, y0 = np.clip(xx+ix, 0, pw-1), np.clip(yy+iy, 0, ph-1)
        if integer:
            pred = ref[y0, x0]
        else:
            fx, fy = qx%den, qy%den
            x1, y1 = np.clip(xx+ix+1, 0, pw-1), np.clip(yy+iy+1, 0, ph-1)
            total = ((den-fx)*(den-fy)*ref[y0,x0] + fx*(den-fy)*ref[y0,x1]
                     + (den-fx)*fy*ref[y1,x0] + fx*fy*ref[y1,x1])
            pred = (total+den*den//2)//(den*den)
        error = np.abs(src-pred)
        error = np.pad(error, ((0,mh*sb-error.shape[0]), (0,mw*sb-error.shape[1])))
        costs += weight*error.reshape(mh,sb,mw,sb).sum(axis=(1,3), dtype=np.int64)
    return costs


def estimate_vectors(source, reference, block_size=16, mode='block', penalty=0,
                     motion_precision='half', search_policy='sample4'):
    if search_policy not in POLICIES:
        raise ValueError('declared sampled search policy')
    if motion_precision not in ('coarse', 'integer', 'half'):
        raise ValueError('motion precision')
    if mode not in ('zero', 'global', 'block') or type(penalty) is not int or not 0 <= penalty <= 4096:
        raise ValueError('motion policy')
    src, ref = m.old._planes(source), m.old._planes(reference)
    h,w = src[0].shape
    ref = m.old._planes(ref, (w,h))
    mw,mh = m.old._grid(w,h,block_size)
    chosen = np.zeros((mh,mw,2), np.int8)
    coarse_stride, refine_stride = POLICIES[search_policy]
    search = dict(search_policy=search_policy, coarse_sample_stride=coarse_stride,
                  refinement_sample_stride=refine_stride, candidate_vectors=0,
                  coarse_candidate_vectors=0, refinement_candidate_maps=0,
                  candidate_block_cost_evaluations=0, sad_sample_operations=0,
                  reference_sample_fetches=0, source_sample_fetches=0,
                  nonzero_vectors=0, fractional_luma_vectors=0,
                  fractional_chroma_vectors=0, motion_precision=motion_precision)
    if mode == 'zero':
        return chosen, search
    samples = _samples(src, ref, block_size, coarse_stride)
    nsamples = sum(s[0].size for s in samples)
    candidates = sorted(((dx,dy) for dy in range(-16,17,4) for dx in range(-16,17,4)),
                        key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
    best = None
    for dx,dy in candidates:
        candidate = np.empty_like(chosen); candidate[:] = (dx,dy)
        costs = _sampled_cost(samples,candidate,integer=True)+penalty*bool(dx or dy)
        if mode == 'global': costs = np.full(costs.shape,int(costs.sum()),np.int64)
        if best is None: best = costs; chosen = candidate.copy()
        else:
            improve = costs < best; chosen[improve] = candidate[improve]; best[improve] = costs[improve]
    ncoarse = len(candidates)
    search.update(candidate_vectors=ncoarse, coarse_candidate_vectors=ncoarse,
                  candidate_block_cost_evaluations=ncoarse*mh*mw,
                  sad_sample_operations=ncoarse*nsamples,
                  reference_sample_fetches=ncoarse*nsamples,
                  source_sample_fetches=ncoarse*nsamples)
    if motion_precision != 'coarse':
        samples = _samples(src,ref,block_size,refine_stride)
        nsamples = sum(s[0].size for s in samples)
        offsets = (-2,0,2) if motion_precision == 'integer' else (-2,-1,0,1,2)
        offsets = sorted(((dx,dy) for dy in offsets for dx in offsets),
                         key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
        origin = chosen.copy(); best = None
        for dx,dy in offsets:
            candidate = origin + np.array((dx,dy),np.int8)
            costs = _sampled_cost(samples,candidate)+penalty*np.any(candidate!=0,axis=2)
            if mode == 'global': costs = np.full(costs.shape,int(costs.sum()),np.int64)
            if best is None: best = costs; chosen = candidate.copy()
            else:
                improve = costs < best; chosen[improve] = candidate[improve]; best[improve] = costs[improve]
        nfine = len(offsets)
        search.update(candidate_vectors=ncoarse+nfine, refinement_candidate_maps=nfine,
                      candidate_block_cost_evaluations=(ncoarse+nfine)*mh*mw,
                      sad_sample_operations=search['sad_sample_operations']+nfine*nsamples,
                      reference_sample_fetches=search['reference_sample_fetches']+4*nfine*nsamples,
                      source_sample_fetches=search['source_sample_fetches']+nfine*nsamples)
    search.update(nonzero_vectors=int(np.count_nonzero(np.any(chosen!=0,axis=2))),
                  fractional_luma_vectors=int(np.count_nonzero(np.any(chosen%2,axis=2))),
                  fractional_chroma_vectors=int(np.count_nonzero(np.any(chosen%4,axis=2))))
    return chosen, search


def analyze_with(gm27, source, reference, *, epoch=1, frame_id=0, reference_id=m.NO_REF,
                 block_size=16, motion_mode='block', penalty=0, motion_precision='half',
                 search_policy='sample4'):
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
