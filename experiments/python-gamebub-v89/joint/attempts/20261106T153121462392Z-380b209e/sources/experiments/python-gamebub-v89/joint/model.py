"""Reprice a complete bounded graph from actual AB38/BR88 primitive work.

This keeps task dependencies and finite consumer lifetimes intact. It does not
subtract old arithmetic work or combine independently measured elapsed times.
"""
from __future__ import annotations
import copy

FETCH_FIELDS={'stream_bytes','raw_bytes','header_bytes','crc_bytes'}
FIELDS=FETCH_FIELDS|{'decisions','renorm','rice_values','events','emits','raw_bits','prob_init','plain_bits'}
LOW=dict(decisions=2,renorm=2,stream_bytes=2,rice_values=1,events=1,raw_bytes=2,
         header_bytes=2,crc_bytes=2,emits=1,raw_bits=1,prob_init=1,plain_bits=1)
HIGH=dict(decisions=4,renorm=4,stream_bytes=4,rice_values=1,events=1,raw_bytes=4,
          header_bytes=4,crc_bytes=4,emits=1,raw_bits=2,prob_init=1,plain_bits=2)


def checked(values):
    if any(k not in FIELDS or type(v)is not int or v<0 for k,v in values.items()):
        raise ValueError('primitive fields must be known nonnegative integers')
    return values


def reprice(original,shared,contexts,weights,*,wire_bytes,metadata_bytes):
    """Return a fresh workload with the same graph and new observed task costs."""
    if len(shared)!=len(contexts) or not shared:
        raise ValueError('observation coverage')
    if any(type(v)is not int or v<0 for v in (wire_bytes,metadata_bytes)):
        raise ValueError('byte counts')
    if set(weights)!=FIELDS or any(type(v)is not int or v<0 for v in weights.values()):
        raise ValueError('explicit complete cost table required')
    work=copy.deepcopy(original)
    front=work['frontend'];jobs=work['jobs'];count=len(shared)
    if len(front['setups'])!=count or len(front['emits'])!=count:
        raise ValueError('graph/observation tile count')
    compute=[0]*4;fetch_work=emit_work=0
    for row in shared:
        checked(row)
        if any(v and k not in FETCH_FIELDS|{'emits'} for k,v in row.items()):
            raise ValueError('unmodeled shared arithmetic primitive')
    for tile in contexts:
        if len(tile)!=4:raise ValueError('four context streams required')
        for row in tile:checked(row)
    seen=dict(shared_setup=set(),tile_emit=set(),context_fetch=set(),context_compute=set())
    for job in jobs:
        kind=job['kind']
        if kind=='outer_crc_scan':
            job['duration']=wire_bytes*weights['crc_bytes'];fetch_work+=job['duration']
        elif kind=='metadata_scan':
            job['duration']=metadata_bytes*weights['header_bytes'];fetch_work+=job['duration']
        elif kind=='shared_setup':
            t=job['tile'];seen[kind].add(t)
            job['duration']=sum(v*weights[k] for k,v in shared[t].items() if k!='emits')
            fetch_work+=job['duration']
        elif kind=='tile_emit':
            t=job['tile'];seen[kind].add(t)
            job['duration']=shared[t].get('emits',0)*weights['emits'];emit_work+=job['duration']
        elif kind=='context_fetch':
            t,c=job['tile'],job['context'];seen[kind].add((t,c))
            job['duration']=sum(v*weights[k] for k,v in contexts[t][c].items() if k in FETCH_FIELDS)
            fetch_work+=job['duration']
        elif kind=='context_compute':
            t,c=job['tile'],job['context'];seen[kind].add((t,c))
            job['duration']=sum(v*weights[k] for k,v in contexts[t][c].items() if k not in FETCH_FIELDS)
            compute[c]+=job['duration']
    expected={(t,c)for t in range(count)for c in range(4)}
    if seen['shared_setup']!=set(range(count)) or seen['tile_emit']!=set(range(count)):
        raise ValueError('missing setup/emission')
    if seen['context_fetch']!=expected or seen['context_compute']!=expected:
        raise ValueError('missing context tasks')
    front.update(wire_bytes=wire_bytes,metadata_bytes=metadata_bytes,
                 work_cycles=dict(fetch=fetch_work,arithmetic=sum(compute),emit=emit_work),
                 context_compute_cycles=compute,observed_fields=sorted(FIELDS))
    work['assumptions']['producer']='Actual independently decoded AB38/BR88 per-context work; original graph and consumer-held coefficient credits preserved.'
    work['assumptions']['plain_parser']='Plain bits cost 1 LOW / 2 HIGH cycles each, plus original symbol/event costs. These are hypothetical bit-serial costs, not RTL measurements.'
    return work
