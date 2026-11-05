"""Pay both real sender alternatives; strict local Pareto admission only."""
import time
import helpers as h
CAP=49152

def propose(source,reference,hud,*,policy,frame_id,reference_id):
    if policy not in('zero','global_grid'):raise ValueError('fixed zero/grid policy')
    started=time.perf_counter_ns()
    if policy=='zero':p=h.analysis.analyze_planes(source,reference,epoch=25,frame_id=frame_id,reference_id=reference_id,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
    else:p=h.global_search.analyze_with(h.m,source,reference,epoch=25,frame_id=frame_id,reference_id=reference_id,block_size=32,policy='global_grid',avoid_rects=h.n.ROIS)
    analysis_ms=(time.perf_counter_ns()-started)/1e6;q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    cs37,normalized,coeff,payloads,work=h.producer.encode_proposal(p,q,hud)
    packet,options,abwork=h.producer.transcode(cs37,coeff,payloads)
    sender_ms=(time.perf_counter_ns()-started)/1e6
    return dict(prepared=p,qmap=q,cs37=cs37,normalized=normalized,coefficients=coeff,payloads=payloads,proposal_work=work,
                packet=packet,options=options,transcode_work=abwork,analysis_ms=analysis_ms,analysis_work=p.work,sender_ms=sender_ms)

def choose(zero_bytes,zero_sse,grid_bytes,grid_sse):
    if any(type(v)is not int or v<0 for v in(zero_bytes,zero_sse,grid_bytes,grid_sse)):raise ValueError('integer actual byte/SSE inputs')
    grid_eligible=(grid_bytes<=CAP and grid_bytes<=zero_bytes and grid_sse<=zero_sse and(grid_bytes<zero_bytes or grid_sse<zero_sse))
    return 'global_grid'if grid_eligible else('zero'if zero_bytes<=CAP else None)
