"""Frozen-before-exact resource score, not a completion-time estimator."""
FETCH={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1,plain_bits=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1,plain_bits=2)
CAP=49152


def feature(shared,contexts,weights,wire_bytes,metadata_bytes,memory_busy,hash_work,residual_tiles):
    prefix=wire_bytes*weights['crc_bytes']+metadata_bytes*weights['header_bytes']
    inner_fetch=sum(v*weights[k]for k,v in shared.items()if k!='emits')
    inner_fetch+=sum(v*weights[k]for row in contexts for k,v in row.items()if k in FETCH)
    compute=[sum(v*weights[k]for k,v in row.items()if k not in FETCH)for row in contexts]
    parallel_compute=max(max(compute,default=0),(sum(compute)+1)//2)
    emission=shared['emits']*weights['emits']
    # A deliberately simple serialization of component resource work. This
    # overcounts overlap and omits dependency/port details; it ranks candidates.
    score=prefix+memory_busy+inner_fetch+parallel_compute+emission
    # Memory, producer and nominal stage tasks start after metadata admission;
    # tree/hash work may precede it, so its resource floor is kept outside prefix.
    necessary=max(prefix+max(memory_busy,inner_fetch,parallel_compute,emission,residual_tiles*64),hash_work)
    return dict(prefix_cycles=prefix,inner_fetch_cycles=inner_fetch,context_compute_cycles=compute,
                parallel_compute_cycles=parallel_compute,emission_cycles=emission,
                decoder_memory_busy_cycles=memory_busy,hash_work_cycles=hash_work,
                nominal_stage_work_cycles=residual_tiles*64,resource_score_cycles=score,necessary_work_floor_cycles=necessary)


def select(candidates):
    feasible=[c for c in candidates if c['wire_bytes']<=CAP]
    if not feasible:raise ValueError('no candidate fits negotiated cap')
    return min(feasible,key=lambda c:(c['resource_score_cycles'],c['wire_bytes'],c['mask']))
