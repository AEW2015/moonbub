"""Current-source selective parent32 -> child16 refinement; ordinary GM27 wire.

Fixed 25/50 percent group quotas. Every unselected child inherits its parent
exactly, including quiet nonzero parents. No acceptance metric enters selection.
"""
import time
import numpy as np


def seed16(parent_vectors, width, height):
    a = np.asarray(parent_vectors)
    if (type(width) is not int or type(height) is not int or min(width,height)<=0 or
        a.dtype != np.int8 or a.shape != ((height+31)//32,(width+31)//32,2) or
        np.any(np.abs(a.astype(np.int16))>18)):
        raise ValueError('bounded parent32 vector field')
    return np.repeat(np.repeat(a,2,axis=0),2,axis=1)[:(height+15)//16,:(width+15)//16].copy()


def _budget(budget):
    if type(budget) is not int or budget not in (25,50):
        raise ValueError('fixed budget preset 25 or 50 percent')


def refine(adaptive, source, reference, parent_vectors, *, budget=25, mask=None):
    """Return owned vectors and paid work; optional explicit bool parent mask.

    Screen weighted SAD at stride4 under the inherited parent predictor. Rank
    parent groups by mean residual plus range of their child means. This favors
    error and spatially uneven residual while flat exact UI/background scores 0.
    Ties use row-major index. ceil(N*budget/100) groups are selected even on quiet
    images; groups with weighted mean residual <=2 skip search and keep parent.
    """
    _budget(budget)
    h,w = source[0].shape
    seed = seed16(parent_vectors,w,h)
    ph,pw = parent_vectors.shape[:2]
    began = time.perf_counter_ns()
    samples = adaptive.compact_samples(source,reference,16,4,np.ones(seed.shape[:2],bool))
    screen = adaptive.compact_cost(samples,seed)
    counts = np.zeros(screen.size,np.int64)
    for _,_,_,_,ids,_,weight,_,_ in samples:
        counts += weight*np.bincount(ids,minlength=screen.size)
    counts = counts.reshape(screen.shape)
    ns = sum(len(s[0]) for s in samples)
    means = screen / np.maximum(counts,1)
    scores = np.zeros((ph,pw),np.float64)
    group_means = np.zeros_like(scores)
    for y in range(ph):
        for x in range(pw):
            a = means[2*y:2*y+2,2*x:2*x+2]
            total = screen[2*y:2*y+2,2*x:2*x+2].sum()
            weight = counts[2*y:2*y+2,2*x:2*x+2].sum()
            group_means[y,x] = total/max(int(weight),1)
            scores[y,x] = group_means[y,x] + float(a.max()-a.min())
    quota = (ph*pw*budget+99)//100
    if mask is None:
        selected = np.zeros(ph*pw,bool)
        order = np.lexsort((np.arange(ph*pw),-scores.ravel()))
        selected[order[:quota]] = True
        selected = selected.reshape(ph,pw)
    else:
        mask = np.asarray(mask)
        if mask.dtype != np.bool_ or mask.shape != (ph,pw):
            raise ValueError('boolean parent-group mask')
        selected = mask.copy()
    active_groups = selected & (group_means>2)
    active = np.repeat(np.repeat(active_groups,2,axis=0),2,axis=1)[:seed.shape[0],:seed.shape[1]]
    screen_ms = (time.perf_counter_ns()-began)/1e6
    began = time.perf_counter_ns()
    chosen = seed.copy()
    fine = adaptive.compact_samples(source,reference,16,2,active)
    nf = sum(len(s[0]) for s in fine)
    offsets = sorted(((x,y) for y in range(-2,3) for x in range(-2,3)),
                     key=lambda p:(abs(p[0])+abs(p[1]),p[1],p[0]))
    best = None
    calls = 0
    if active.any():
        for offset in offsets:
            candidate = np.clip(seed.astype(np.int16)+np.array(offset,np.int16),-18,18).astype(np.int8)
            costs = adaptive.compact_cost(fine,candidate)
            if best is None:
                best = costs
            else:
                improve = active & (costs<best)
                chosen[improve] = candidate[improve]
                best[improve] = costs[improve]
            calls += 1
    search_ms = (time.perf_counter_ns()-began)/1e6
    work = dict(search_policy='selective_parent32_residual_dispersion_stride4_child16_offsets2_stride2',
        budget_percent=budget,explicit_mask=mask is not None,parent_grid=[ph,pw],child_grid=list(seed.shape[:2]),
        quota_groups=quota,selected_groups=int(selected.sum()),active_groups=int(active_groups.sum()),
        selected_group_mask=selected.astype(int).tolist(),active_group_mask=active_groups.astype(int).tolist(),
        group_scores=scores.tolist(),quiet_groups=int((group_means<=2).sum()),
        active_blocks=int(active.sum()),quiet_blocks=int((~active).sum()),
        screen_ms=screen_ms,search_ms=search_ms,screen_stride=4,refinement_stride=2,
        screen_sample_operations=ns,refinement_sample_operations=calls*nf,
        sad_sample_operations=ns+calls*nf,candidate_maps=1+calls,
        candidate_block_cost_evaluations=screen.size+calls*int(active.sum()),
        screen_reference_sample_fetches=4*ns,refinement_reference_sample_fetches=4*calls*nf,
        reference_sample_fetches=4*(ns+calls*nf),source_sample_fetches=ns+calls*nf,
        sample_gather_source_fetches=ns+nf,
        nonzero_vectors=int(np.any(chosen!=0,axis=2).sum()),bounded_half_luma_units=18,
        unselected_exact_parent=True,selection_uses_acceptance_metric=False,
        selected_fine_weighted_sad=0 if best is None else int(best[active].sum()))
    return chosen,work


def analyze16(module, adaptive, parent, reference, *, budget=25):
    """Construct a child Prepared owned by the supplied frozen runtime module."""
    _budget(budget)
    start = time.perf_counter_ns()
    if not isinstance(parent,module.Prepared) or parent.owner is not module._PREPARED_OWNER or parent.block_size != 32:
        raise ValueError('owned parent32 preparation')
    p = parent
    if p.key:
        if reference is not None: raise ValueError('key without reference')
        prediction = tuple(a.copy() for a in p.prediction)
        vector_bytes = b''; vector_work = {}
        search = dict(budget_percent=budget,sad_sample_operations=0,reference_sample_fetches=0,
            source_sample_fetches=0,nonzero_vectors=0,candidate_maps=0,screen_ms=0.,search_ms=0.,
            selected_groups=0,active_groups=0,screen_sample_operations=0,refinement_sample_operations=0)
        prediction_reads = 0; map_ms = 0.
    else:
        ref = module.base._planes(reference,(p.width,p.height))
        if module.C.reference_tag(ref) != p.reference_tag: raise ValueError('exact parent reference')
        parent_vectors = module.base.unpack_vectors(p.vector_bytes,(p.width+31)//32,(p.height+31)//32)
        vectors,search = refine(adaptive,p.source,ref,parent_vectors,budget=budget)
        prediction,taps = module.taps.predict_with_info(ref,vectors,16)
        prediction_reads = taps['reference_sample_fetches']
        began = time.perf_counter_ns()
        vector_bytes,vector_work = module.base.pack_vectors(vectors,return_work=True)
        map_ms = (time.perf_counter_ns()-began)/1e6
    began = time.perf_counter_ns()
    raw = module.base.old._forward(p.source,prediction)
    transform_ms = (time.perf_counter_ns()-began)/1e6
    for a in prediction+raw: a.setflags(write=False)
    work = dict(key=p.key,block_size=16,motion_mode='block',search=search,
        screen_ms=search['screen_ms'],search_ms=search['search_ms'],map_ms=map_ms,
        forward_plane_calls=3,transform_ms=transform_ms,motion_map=vector_work,
        prediction_reference_sample_fetches=prediction_reads,
        transform_source_sample_reads=sum(a.size for a in p.source),
        transform_prediction_sample_reads=sum(a.size for a in prediction),
        retained_analysis_array_bytes=sum(a.nbytes for a in prediction+raw+p.source),
        analysis_wall_ms=(time.perf_counter_ns()-start)/1e6,reference_tag=p.reference_tag.hex())
    return module.Prepared(module._PREPARED_OWNER,p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.key,16,
        'block',p.reference_tag,vector_bytes,prediction,raw,p.source,work)
