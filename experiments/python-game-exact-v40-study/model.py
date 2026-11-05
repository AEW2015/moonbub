"""Exact block-output eligibility plus actual complete-packet byte guard."""
import time
import numpy as np
import helpers as h

def exact_eligibility(candidate_pixels,canonical):
    if len(candidate_pixels)!=4 or canonical.shape!=(len(candidate_pixels[0]),4):raise ValueError('four block candidates/canonical shape')
    exact=np.stack([np.all(pixels==candidate_pixels[0],axis=(1,2))for pixels in candidate_pixels],axis=1)
    eligible=exact&canonical
    if not np.all(eligible[:,0]):raise ValueError('mode0 must remain eligible')
    return exact,eligible

def choose_modes(coefficient_bits,rank_bits,eligible):
    if coefficient_bits.shape!=rank_bits.shape or coefficient_bits.shape!=eligible.shape or not np.all(eligible[:,0]):
        raise ValueError('bounded eligible rate-choice arrays')
    return np.argmin(np.where(eligible,coefficient_bits+rank_bits,1<<60),axis=1)

def choose_packet(control,candidate):
    if type(control)is not bytes or not 0<len(control)<=49152:raise ValueError('actual fitting immutable control')
    if type(candidate)is not bytes or not candidate:raise ValueError('actual immutable candidate')
    return 'candidate'if len(candidate)<=49152 and len(candidate)<len(control)else'control'

def encode_plane(source,temporal,tables,safe):
    height,width=source.shape;bh,bw=height//8,width//8;src=h.spatial.blocks(source);base=h.spatial.blocks(temporal)
    decoded=np.zeros_like(base);coeff=np.zeros_like(base);modes=np.zeros(len(base),np.uint8)
    costs=np.zeros((len(base),4,6),np.int64);eligible_array=np.zeros((len(base),4),np.uint8);yy,xx=np.mgrid[:bh,:bw]
    for dy,dx in((0,0),(0,1),(1,0),(1,1)):
        wave=np.flatnonzero(((yy%2==dy)&(xx%2==dx)).reshape(-1));decoded[wave[safe[wave]]]=128
        indices=wave[~safe[wave]]
        if not len(indices):continue
        predictions=[h.spatial.predictor(base,decoded,indices,bw,dy,dx,mode)for mode in range(4)]
        canonical,menus,ranks,rankbits=h.signal.menu_metadata(predictions)
        allcoeff=[];allpixels=[];allbits=[];allsse=[]
        for prediction in predictions:
            raw=h.m.ft.forward(src[indices].astype(np.int64)-prediction)
            quant=h.m.ft.round_quantize(raw,tables[indices]).astype(np.int16)
            if np.any(np.abs(quant.astype(np.int32))>h.m.ft.MAX_COEFF):raise ValueError('coefficient wire range')
            pixels=np.clip(h.m.ft.inverse(quant.astype(np.int64)*tables[indices])+prediction,0,255).astype(np.int16)
            allcoeff.append(quant);allpixels.append(pixels);allbits.append(h.signal.coefficient_bits(quant))
            allsse.append(np.square(src[indices].astype(np.int64)-pixels).sum(axis=(1,2)))
        exact,eligible=exact_eligibility(allpixels,canonical);eligible_array[indices]=eligible.astype(np.uint8)
        chosen=choose_modes(np.stack(allbits,axis=1),rankbits,eligible)
        for mode in range(4):
            costs[indices,mode]=np.stack((allsse[mode],allbits[mode],rankbits[:,mode],canonical[:,mode],exact[:,mode],eligible[:,mode]),axis=1)
            pick=chosen==mode;dest=indices[pick]
            coeff[dest]=allcoeff[mode][pick];decoded[dest]=allpixels[mode][pick];modes[dest]=mode
        # This full-block equality, not a scalar error guard, is the inductive
        # condition that preserves all later spatial and temporal predictions.
        if not np.array_equal(decoded[indices],allpixels[0]):raise ValueError('exact mode0 reconstruction invariant')
    return coeff,h.spatial.plane_from_blocks(decoded,height,width),modes,costs,eligible_array

def encode_candidate(source,reference,qmap,hud,frame_id,reference_id):
    old=h.m.base.old;src=old._planes(source,(720,480));q=h.m.roi.check_map(qmap,720,480);key=reference is None
    if key:
        if type(reference_id)is not int or reference_id!=h.m.NO_REF:raise ValueError('key identity')
        base=tuple(np.full_like(a,128)for a in src);reftag=bytes(16)
    else:
        if not old._id(reference_id)or reference_id>=frame_id:raise ValueError('past reference')
        base=old._planes(reference,(720,480));reftag=h.m.C.reference_tag(base)
    mode_payloads=[];coefficient_payloads=[];output=[];modes=[];costs=[];eligible_arrays=[];details=[]
    for axis,(plane,temporal,safe)in enumerate(zip(src,base,h.canonical.HIDDEN,strict=True)):
        coeff,pixels,mode,cost,eligible=encode_plane(plane,temporal,h.m.roi.block_tables(q,720,480,axis),safe)
        visible=coeff[~safe];bw=plane.shape[1]//8
        full=h.entropy._plane_plan(coeff,bw,h.m);compact=h.entropy._plane_plan(visible,1,h.m);implicit=compact['bytes']+1<full['bytes']
        if implicit:data,*_=h.entropy._construct(visible,1,compact,h.m);data=b'\x04'+data
        else:data,*_=h.entropy._construct(coeff,bw,full,h.m)
        mp=h.spatial.pack_modes(mode[~safe]);mode_payloads.append(mp);coefficient_payloads.append(data)
        output.append(pixels);modes.append(mode);costs.append(cost);eligible_arrays.append(eligible)
        details.append(dict(plane=axis,visible_blocks=int((~safe).sum()),hidden_blocks=int(safe.sum()),
            mode_counts=[int(np.count_nonzero(mode[~safe]==v))for v in range(4)],
            eligible_nonzero_modes=int(eligible[:,1:].sum()),selected_nonzero_modes=int(np.count_nonzero(mode)),
            all_candidate_blocks=4*int((~safe).sum()),SP38_mode_bytes=len(mp),coefficient_bytes=len(data),
            implicit_selected=implicit,fullgrid_payload_bytes=full['bytes'],compact_payload_bytes=compact['bytes']+1))
    output=tuple(output);tag=h.m.C.reference_tag(output);packed=h.m.roi.pack_map(q)
    inner=h.spatial.seal(h.spatial.INNER.pack(b'TS38',1,int(key),25,frame_id,reference_id,720,480,reftag,tag,len(packed),
        *(len(v)for v in mode_payloads),*(len(v)for v in coefficient_payloads))+packed+b''.join(mode_payloads)+b''.join(coefficient_payloads))
    sp38=h.spatial.seal(h.spatial.OUTER.pack(b'SP38',1,int(key),25,frame_id,reference_id,720,480,h.spatial.PROFILE,reftag,tag,len(inner),len(hud))+inner+hud)
    packet,rank_output,rank_work,rank_trials=h.rank.transcode(sp38,reference)
    for a,b in zip(output,rank_output,strict=True):
        if not np.array_equal(a,b):raise ValueError('actual candidate packet reconstruction')
    return dict(packet=packet,planes=output,SP38_packet=sp38,rank_trials=rank_trials,rank_work=rank_work,
                plane_work=details,modes=tuple(modes),costs=tuple(costs),eligibility=tuple(eligible_arrays))

def encode_pair(source,reference,qmap,hud,*,frame_id,reference_id):
    start=time.perf_counter_ns()
    control,control_pixels,control_work,control_modes,control_costs,control_sp38,control_trials=h.signal.encode_planes(
        source,reference,qmap,hud,policy='mode0control',frame_id=frame_id,reference_id=reference_id)
    candidate=encode_candidate(source,reference,qmap,hud,frame_id,reference_id)
    for a,b in zip(control_pixels,candidate['planes'],strict=True):
        if not np.array_equal(a,b):raise ValueError('whole committed reference must equal mode0 control')
    chosen=choose_packet(control,candidate['packet']);selected=candidate['packet']if chosen=='candidate'else control
    work=dict(encode_pair_ms=(time.perf_counter_ns()-start)/1e6,selection=chosen,control_bytes=len(control),candidate_bytes=len(candidate['packet']),
        selected_bytes=len(selected),strict_complete_byte_guard=True,whole_mode0_reference_equal=True,
        eligible_nonzero_modes=sum(p['eligible_nonzero_modes']for p in candidate['plane_work']),
        candidate_nonzero_modes=sum(p['selected_nonzero_modes']for p in candidate['plane_work']),
        control_work=control_work,candidate_planes=candidate['plane_work'],candidate_rank_work=candidate['rank_work'])
    return dict(packet=selected,planes=control_pixels,work=work,
        control=dict(packet=control,SP38_packet=control_sp38,rank_trials=control_trials,mode_arrays=control_modes,cost_arrays=control_costs),
        candidate=candidate)
