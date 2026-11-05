"""RP39: arithmetic-code ranks among distinct decoder-derived predictors.

SP38 input is already paid. Stable clipped-predictor dedup removes impossible
duplicate mode alternatives without changing coefficients or selected pixels.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
OUTER=h.f.OUTER;INNER=h.f.INNER
PROFILE=hashlib.sha256(b'RP39:distinct-clipped-prediction-rank-v1:tilemajor:truncated-unary:AB38ctx44:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def tile_order(bh,bw):
    return tuple((by,bx)for ty in range(0,bh,2)for tx in range(0,bw,2)for dy,dx in((0,0),(0,1),(1,0),(1,1))
                 for by,bx in((ty+dy,tx+dx),)if by<bh and bx<bw)

def ranks_from_predictions(predictions,modes):
    """Return stable distinct-menu size/rank; reject duplicate nonfirst modes."""
    if len(predictions)!=4 or any(a.shape!=predictions[0].shape for a in predictions):raise ValueError('four prediction batches')
    count=len(modes);canonical=np.ones((count,4),bool)
    for mode in range(1,4):
        for earlier in range(mode):canonical[:,mode]&=~np.all(predictions[mode]==predictions[earlier],axis=(1,2))
    if np.any(~canonical[np.arange(count),modes]):raise ValueError('selected mode must be first identical clipped predictor')
    menu=canonical.sum(1).astype(np.uint8)
    ranks=(canonical&(np.arange(4)[None,:]<modes[:,None])).sum(1).astype(np.uint8)
    return menu,ranks

def emit_rank(coder,rank,count,position):
    if type(rank)is not int or type(count)is not int or not 1<=count<=4 or not 0<=rank<count:raise ValueError('bounded distinct predictor rank')
    if count==1:return
    for decision in range(count-1):
        bit=int(rank>decision);context=position*12+(count-2)*3+decision
        coder.bit(bit,context)
        if not bit:break

def encode_plane(temporal,coefficients,modes,tables,safe):
    ph,pw=temporal.shape;bh,bw=ph//8,pw//8;base=h.spatial.blocks(temporal);decoded=np.zeros_like(base)
    safe=safe.reshape(-1);menus=np.zeros(len(base),np.uint8);ranks=np.zeros_like(menus)
    yy,xx=np.mgrid[:bh,:bw]
    for dy,dx in((0,0),(0,1),(1,0),(1,1)):
        wave=np.flatnonzero(((yy%2==dy)&(xx%2==dx)).reshape(-1));decoded[wave[safe[wave]]]=128
        indices=wave[~safe[wave]]
        if not len(indices):continue
        predictions=[h.spatial.predictor(base,decoded,indices,bw,dy,dx,mode)for mode in range(4)]
        menu,rank=ranks_from_predictions(predictions,modes[indices]);menus[indices]=menu;ranks[indices]=rank
        prediction=np.stack(predictions,axis=1)[np.arange(len(indices)),modes[indices]]
        decoded[indices]=np.clip(h.m.ft.inverse(coefficients[indices].astype(np.int64)*tables[indices])+prediction,0,255).astype(np.int16)
    coder=h.binary.BinaryEncoder();contexts=set();visible=0
    for by,bx in tile_order(bh,bw):
        index=by*bw+bx
        if safe[index]:continue
        rank,count=int(ranks[index]),int(menus[index]);position=(by&1)*2+(bx&1)
        emit_rank(coder,rank,count,position);visible+=1
        if count>1:
            for decision in range(min(rank+1,count-1)):contexts.add(position*12+(count-2)*3+decision)
    body,nbits=coder.finish();payload=b'\x03'+struct.pack('<I',nbits)+body
    output=h.spatial.plane_from_blocks(decoded,ph,pw)
    work=dict(visible_blocks=visible,menu_counts=[int(np.count_nonzero(menus==n))for n in range(1,5)],
        rank_counts=[int(np.count_nonzero((ranks==r)&~safe))for r in range(4)],
        rank_payload_bytes=len(payload),arithmetic_bit_count=nbits,binary_decisions=coder.decisions,
        probability_products=coder.decisions,renorm_steps=coder.renorm,max_renorm_per_bit=coder.maximum_renorm,
        context_ids=sorted(contexts),logical_probability_state_bytes=88,active_contexts=len(contexts),
        interval_bits=16,probability_bits=8,multiply_operand_bits=[17,8],maximum_decisions_per_rank=3,
        hidden_bitmap_bytes=0,rank_header_bytes=5,termination_guard_bits=18)
    return payload,output,work,menus,ranks

def transcode(packet,reference=None):
    start=time.perf_counter_ns();meta=h.f.parse(packet);key=meta['key']
    if key:temporal=tuple(np.full(s,128,np.int16)for s in((480,720),(240,360),(240,360)))
    else:
        temporal=h.m.base.old._planes(reference,(720,480))
        if h.m.C.reference_tag(temporal)!=meta['reference_tag']:raise ValueError('actual canonical incoming reference')
    output=[];payloads=[];plane_work=[];trials=[]
    for axis,(base,coeff,modes,safe,oldpayload)in enumerate(zip(temporal,meta['coefficients'],meta['modes'],h.f.f.safe_blocks(),meta['mode_payloads'],strict=True)):
        candidate,decoded,work,menus,ranks=encode_plane(base,coeff,modes,h.m.roi.block_tables(meta['qmap'],720,480,axis),safe)
        use_rank=len(candidate)<len(oldpayload);payload=candidate if use_rank else oldpayload
        work.update(plane=axis,old_mode_bytes=len(oldpayload),selected_mode_bytes=len(payload),rank_selected=use_rank)
        payloads.append(payload);output.append(decoded);plane_work.append(work)
        trials.append(dict(rank_packet=candidate,menus=menus,ranks=ranks))
    output=tuple(output)
    if h.m.C.reference_tag(output)!=meta['output_tag']:raise ValueError('SP38 exact reconstruction before rank coding')
    outer=list(OUTER.unpack_from(packet));oldinner=packet[OUTER.size:OUTER.size+outer[11]];fields=list(INNER.unpack_from(oldinner))
    fields[0]=b'TR39';fields[11:14]=[len(v)for v in payloads]
    qdata=oldinner[INNER.size:INNER.size+fields[10]]
    inner=seal(INNER.pack(*fields)+qdata+b''.join(payloads)+b''.join(meta['plane_payloads']))
    outer[0]=b'RP39';outer[8]=PROFILE;outer[11]=len(inner)
    result=seal(OUTER.pack(*outer)+inner+meta['hud'])
    assert len(result)<=len(packet)<=49152
    return result,output,dict(transcode_ms=(time.perf_counter_ns()-start)/1e6,planes=plane_work,
        input_complete_bytes=len(packet),output_complete_bytes=len(result),old_encode_already_paid=True,
        new_outer_bytes=80,new_inner_header_bytes=84,coefficient_payloads_unchanged=True),trials
