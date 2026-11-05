"""Fine coefficient-bit/rank-decision proxy, actual frozen RP39 proof sender.

This is a new encoder policy only, not a new prediction/decoder wire contract.
The proxy removes isolated CP02 byte rounding but is still not full-plane rate.
"""
import time
import numpy as np
import helpers as h

def coefficient_bits(coefficients):
    """Unrounded CP02 payload proxy:32 parameterbits+DCbits+ACbits vs raw1024.

    Frozen Rice tables/parameters and exact syntax costs are reused; the final
    DC and AC stream byte ceilings are deliberately omitted. Fixed packet
    header/CRC bytes are constant and omitted from this relative proxy.
    """
    counter=h.m.counter;a=counter._check(coefficients);out=np.empty(len(a),np.int64)
    positions=np.arange(1,64)
    for start in range(0,len(a),1024):
        zig=a[start:start+1024].reshape(-1,64)[:,counter.ZIGZAG];ac=zig[:,1:];nz=ac!=0
        last=np.maximum.accumulate(np.where(nz,positions,0),axis=1)
        previous=np.empty_like(last);previous[:,0]=0;previous[:,1:]=last[:,:-1];run=positions-previous-1
        bits=5*nz.sum(1)+2*np.where(nz,run//16,0).sum(1)+2*(last[:,-1]!=63)
        mapped=counter._mapped(ac)-1;mapped[~nz]=0
        for lo,hi in((0,5),(5,20),(20,63)):
            costs=(counter._AC_LENGTHS[:,mapped[:,lo:hi]]*nz[:,lo:hi]).sum(axis=2)
            bits=bits+costs.min(axis=0)
        dc=counter._DC_MIN_LENGTH[counter._mapped(zig[:,0])]
        out[start:start+len(zig)]=np.minimum(1024,32+dc+bits)
    return out

def menu_metadata(predictions):
    count=len(predictions[0]);representatives=np.tile(np.arange(4),(count,1))
    for mode in range(1,4):
        for previous in range(mode):
            equal=np.all(predictions[mode]==predictions[previous],axis=(1,2))
            representatives[:,mode]=np.where(equal&(representatives[:,mode]==mode),previous,representatives[:,mode])
    canonical=representatives==np.arange(4)[None,:];menus=canonical.sum(1)
    ranks=np.stack([(canonical&(np.arange(4)[None,:]<representatives[:,mode,None])).sum(1)for mode in range(4)],axis=1)
    rankbits=np.where(menus[:,None]==1,0,np.minimum(ranks+1,menus[:,None]-1))
    return canonical,menus,ranks,rankbits

def encode_plane(source,temporal,tables,safe,policy):
    if policy not in('mode0control','lambda1','lambda4','lambda16'):raise ValueError('declared signal policy')
    lam=0 if policy=='mode0control'else int(policy[6:])
    height,width=source.shape;bh,bw=height//8,width//8;src=h.spatial.blocks(source);base=h.spatial.blocks(temporal)
    decoded=np.zeros_like(base);coeff=np.zeros_like(base);modes=np.zeros(len(base),np.uint8)
    costs=np.zeros((len(base),4,4),np.int64);yy,xx=np.mgrid[:bh,:bw]
    for dy,dx in((0,0),(0,1),(1,0),(1,1)):
        wave=np.flatnonzero(((yy%2==dy)&(xx%2==dx)).reshape(-1));decoded[wave[safe[wave]]]=128
        indices=wave[~safe[wave]]
        if not len(indices):continue
        predictions=[h.spatial.predictor(base,decoded,indices,bw,dy,dx,mode)for mode in range(4)]
        canonical,menus,ranks,rankbits=menu_metadata(predictions)
        allcoeff=[];allpixels=[];scores=[]
        for mode,prediction in enumerate(predictions):
            raw=h.m.ft.forward(src[indices].astype(np.int64)-prediction)
            quant=h.m.ft.round_quantize(raw,tables[indices]).astype(np.int16)
            if np.any(np.abs(quant.astype(np.int32))>h.m.ft.MAX_COEFF):raise ValueError('coefficient wire range')
            pixels=np.clip(h.m.ft.inverse(quant.astype(np.int64)*tables[indices])+prediction,0,255).astype(np.int16)
            sse=np.square(src[indices].astype(np.int64)-pixels).sum(axis=(1,2));bits=coefficient_bits(quant)
            costs[indices,mode]=np.stack((sse,bits,rankbits[:,mode],canonical[:,mode].astype(np.int64)),axis=1)
            scores.append(np.where(canonical[:,mode],sse+lam*(bits+rankbits[:,mode]),1<<60))
            allcoeff.append(quant);allpixels.append(pixels)
        chosen=np.zeros(len(indices),np.int64)if policy=='mode0control'else np.argmin(np.stack(scores),axis=0)
        for mode in range(4):
            pick=chosen==mode;dest=indices[pick];coeff[dest]=allcoeff[mode][pick];decoded[dest]=allpixels[mode][pick];modes[dest]=mode
    return coeff,h.spatial.plane_from_blocks(decoded,height,width),modes,costs

def encode_planes(source,reference,qmap,hud,*,policy,frame_id,reference_id):
    start=time.perf_counter_ns();old=h.m.base.old;src=old._planes(source,(720,480));q=h.m.roi.check_map(qmap,720,480)
    if not old._id(frame_id)or type(hud)is not bytes:raise ValueError('frame identity/HUD')
    key=reference is None
    if key:
        if type(reference_id)is not int or reference_id!=h.m.NO_REF:raise ValueError('key identity')
        base=tuple(np.full_like(a,128)for a in src);reftag=bytes(16)
    else:
        if not old._id(reference_id)or reference_id>=frame_id:raise ValueError('past reference')
        base=old._planes(reference,(720,480));reftag=h.m.C.reference_tag(base)
    output=[];mode_payloads=[];coefficient_payloads=[];arrays=[];cost_arrays=[];details=[]
    for axis,(plane,temporal,safe)in enumerate(zip(src,base,h.canonical.HIDDEN,strict=True)):
        tables=h.m.roi.block_tables(q,720,480,axis);coeff,pixels,modes,costs=encode_plane(plane,temporal,tables,safe,policy)
        visible=coeff[~safe];bw=plane.shape[1]//8
        full=h.entropy._plane_plan(coeff,bw,h.m);compact=h.entropy._plane_plan(visible,1,h.m);implicit=compact['bytes']+1<full['bytes']
        if implicit:data,*_=h.entropy._construct(visible,1,compact,h.m);data=b'\x04'+data
        else:data,*_=h.entropy._construct(coeff,bw,full,h.m)
        mode_payload=h.spatial.pack_modes(modes[~safe]);mode_payloads.append(mode_payload);coefficient_payloads.append(data)
        output.append(pixels);arrays.append(modes);cost_arrays.append(costs)
        details.append(dict(plane=axis,coefficient_bytes=len(data),SP38_mode_bytes=len(mode_payload),visible_blocks=int((~safe).sum()),
            hidden_blocks=int(safe.sum()),evaluated_block_candidates=4*int((~safe).sum()),
            mode_counts=[int(np.count_nonzero(modes[~safe]==v))for v in range(4)],implicit_selected=implicit,
            fullgrid_payload_bytes=full['bytes'],compact_payload_bytes=compact['bytes']+1))
    output=tuple(output);tag=h.m.C.reference_tag(output);packed=h.m.roi.pack_map(q)
    inner=h.spatial.seal(h.spatial.INNER.pack(b'TS38',1,int(key),25,frame_id,reference_id,720,480,reftag,tag,len(packed),
        *(len(v)for v in mode_payloads),*(len(v)for v in coefficient_payloads))+packed+b''.join(mode_payloads)+b''.join(coefficient_payloads))
    sp38=h.spatial.seal(h.spatial.OUTER.pack(b'SP38',1,int(key),25,frame_id,reference_id,720,480,h.spatial.PROFILE,reftag,tag,len(inner),len(hud))+inner+hud)
    packet,rank_output,rank_work,rank_trials=h.rank.transcode(sp38,reference)
    for actual,expected in zip(rank_output,output,strict=True):
        if not np.array_equal(actual,expected):raise ValueError('proof transcoder reconstruction mismatch')
    work=dict(encode_ms=(time.perf_counter_ns()-start)/1e6,policy=policy,lambda_value=0 if policy=='mode0control'else int(policy[6:]),
        planes=details,SP38_complete_bytes=len(sp38),RP39_complete_bytes=len(packet),SP38_mode_bytes=sum(map(len,mode_payloads)),
        coefficient_bytes=sum(map(len,coefficient_payloads)),rank=rank_work,
        coefficient_proxy='min(1024,32+unrounded_DC_min_Rice_bits+AC_syntax+band_min_Rice_bits)',
        rank_proxy='0ifN1elsemin(distinct_rank+1,N-1),rawtruncatedunarydecisions;notadaptivecodedbits',
        score='source_YUV_SSE+lambda*(coefficient_bit_proxy+raw_rank_decisions);firstcanonicalmodewins ties',
        research_oracle_evaluates_all4_modes_even_control=True,cap_fit=len(packet)<=49152)
    return packet,output,work,tuple(arrays),tuple(cost_arrays),sp38,rank_trials
