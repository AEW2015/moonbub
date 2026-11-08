"""One-level 32->16 half-luma vector refinement, unchanged valid GM27 wire."""
import time
import numpy as np


def seed16(parent_vectors, width, height):
    a = np.asarray(parent_vectors)
    if a.dtype != np.int8 or a.shape != ((height+31)//32,(width+31)//32,2) or np.any(np.abs(a.astype(np.int16))>18):
        raise ValueError('bounded parent32 vector field')
    return np.repeat(np.repeat(a,2,axis=0),2,axis=1)[:(height+15)//16,:(width+15)//16].copy()


def refine(adaptive, source, reference, parent_vectors):
    h,w = source[0].shape
    seed = seed16(parent_vectors,w,h)
    zero = np.zeros_like(seed)
    all_samples = adaptive.compact_samples(source,reference,16,2,np.ones(seed.shape[:2],bool))
    nsamples = sum(len(s[0]) for s in all_samples)
    best = adaptive.compact_cost(all_samples,zero,integer=True)
    counts = np.zeros(best.size,np.int64)
    for _,_,_,_,ids,_,weight,_,_ in all_samples:
        counts += weight*np.bincount(ids,minlength=best.size)
    active = best>2*counts.reshape(best.shape)
    chosen = zero.copy()
    samples = adaptive.compact_samples(source,reference,16,2,active)
    nactive = sum(len(s[0]) for s in samples)
    offsets = sorted(((x,y) for y in (-2,-1,0,1,2) for x in (-2,-1,0,1,2)),
                     key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
    calls = 0
    if active.any():
        for offset in offsets:
            candidate = np.clip(seed.astype(np.int16)+np.array(offset,np.int16),-18,18).astype(np.int8)
            candidate[~active] = 0
            costs = adaptive.compact_cost(samples,candidate)
            improve = active & (costs<best)
            chosen[improve] = candidate[improve]; best[improve] = costs[improve]
            calls += 1
    work = dict(search_policy='parent32_seed16_offsets2_stride2_zero_first',
        parent_grid=list(parent_vectors.shape[:2]), child_grid=list(chosen.shape[:2]),
        quiet_blocks=int((~active).sum()),active_blocks=int(active.sum()),
        candidate_maps=1+calls, candidate_block_cost_evaluations=best.size+calls*int(active.sum()),
        sad_sample_operations=nsamples+calls*nactive,
        reference_sample_fetches=nsamples+4*calls*nactive,
        source_sample_fetches=nsamples+calls*nactive,
        nonzero_vectors=int(np.any(chosen!=0,axis=2).sum()),
        bounded_half_luma_units=18,nearby_parent_candidates=False,
        selected_sampled_weighted_sad=int(best.sum()))
    return chosen,work


def analyze16(module, adaptive, parent, reference):
    start = time.perf_counter_ns()
    if not isinstance(parent,module.Prepared) or parent.owner is not module._PREPARED_OWNER or parent.block_size != 32:
        raise ValueError('owned parent32 preparation')
    p = parent
    if p.key:
        if reference is not None: raise ValueError('key without reference')
        vectors = np.zeros(((p.height+15)//16,(p.width+15)//16,2),np.int8)
        prediction = tuple(a.copy() for a in p.prediction)
        vector_bytes = b''; vector_work = {}; search = dict(sad_sample_operations=0,reference_sample_fetches=0,
            source_sample_fetches=0,nonzero_vectors=0,candidate_maps=0)
        prediction_reads = 0; search_ms = 0.
    else:
        ref = module.base._planes(reference,(p.width,p.height))
        if module.C.reference_tag(ref) != p.reference_tag: raise ValueError('exact parent reference')
        parent_vectors = module.base.unpack_vectors(p.vector_bytes,(p.width+31)//32,(p.height+31)//32)
        began = time.perf_counter_ns()
        vectors,search = refine(adaptive,p.source,ref,parent_vectors)
        search_ms = (time.perf_counter_ns()-began)/1e6
        prediction,taps = module.taps.predict_with_info(ref,vectors,16)
        prediction_reads = taps['reference_sample_fetches']
        vector_bytes,vector_work = module.base.pack_vectors(vectors,return_work=True)
    began = time.perf_counter_ns()
    raw = module.base.old._forward(p.source,prediction)
    transform_ms = (time.perf_counter_ns()-began)/1e6
    for a in prediction: a.setflags(write=False)
    for a in raw: a.setflags(write=False)
    work = dict(key=p.key,block_size=16,motion_mode='block',search=search,search_ms=search_ms,
        forward_plane_calls=3,transform_ms=transform_ms,motion_map=vector_work,
        prediction_reference_sample_fetches=prediction_reads,
        retained_analysis_array_bytes=sum(a.nbytes for a in prediction+raw+p.source),
        analysis_wall_ms=(time.perf_counter_ns()-start)/1e6,reference_tag=p.reference_tag.hex())
    return module.Prepared(module._PREPARED_OWNER,p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.key,16,
        'block',p.reference_tag,vector_bytes,prediction,raw,p.source,work)
