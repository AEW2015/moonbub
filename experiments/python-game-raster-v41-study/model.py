"""RR41/GR41: causal GLOBAL residual-edge predictors with exact-output guard.

The HOST precomputes the complete mode0 target; exact eligibility ensures each
accepted alternative reproduces it. A decoder still uses only prior raster
neighbors. Full-image oracle construction is not required in the decoder.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
OUTER=h.spatial.OUTER;INNER=h.spatial.INNER
PROFILE=hashlib.sha256(b'RR41:global-raster-residualEdges-v1:clippedPred:DCavailable:hiddenImmediate:distinctRanks:AB38availabilityCtx44:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def global_predictions(temporal,target):
    height,width=temporal.shape;bh,bw=height//8,width//8
    yy,xx=np.mgrid[:bh,:bw];ys=yy.reshape(-1)*8;xs=xx.reshape(-1)*8
    top=(target[np.maximum(ys-1,0)[:,None],xs[:,None]+np.arange(8)]-
         temporal[np.maximum(ys-1,0)[:,None],xs[:,None]+np.arange(8)]).astype(np.int32)
    left=(target[ys[:,None]+np.arange(8),np.maximum(xs-1,0)[:,None]]-
          temporal[ys[:,None]+np.arange(8),np.maximum(xs-1,0)[:,None]]).astype(np.int32)
    top[ys==0]=0;left[xs==0]=0
    denominator=8*((ys>0).astype(np.int32)+(xs>0).astype(np.int32))
    dc=np.where(denominator,(top.sum(1)+left.sum(1)+denominator//2)//np.maximum(denominator,1),0)
    base=h.spatial.blocks(temporal).astype(np.int32)
    predictions=[base.astype(np.int16),np.clip(base+top[:,None,:],0,255).astype(np.int16),
        np.clip(base+left[:,:,None],0,255).astype(np.int16),np.clip(base+dc[:,None,None],0,255).astype(np.int16)]
    positions=2*(ys>0).astype(np.int64)+(xs>0).astype(np.int64)
    return predictions,positions

def prepare_oracle(source,reference,qmap,frame_id,reference_id):
    old=h.m.base.old;src=old._planes(source,(720,480));q=h.m.roi.check_map(qmap,720,480)
    if not old._id(frame_id):raise ValueError('bounded frame identity')
    key=reference is None
    if key:
        if type(reference_id)is not int or reference_id!=h.m.NO_REF:raise ValueError('key identity')
        temporal=tuple(np.full_like(a,128)for a in src);reftag=bytes(16)
    else:
        if not old._id(reference_id)or reference_id>=frame_id:raise ValueError('past reference')
        temporal=old._planes(reference,(720,480));reftag=h.m.C.reference_tag(temporal)
    raw=old._forward(src,temporal);coeff=list(h.m.base._quantize(raw,q,720,480))
    for c,safe in zip(coeff,h.canonical.HIDDEN,strict=True):c[safe]=0
    target=h.m.gm.reconstruct(tuple(coeff),temporal,q,720,480)
    for plane,safe in zip(target,h.canonical.HIDDEN,strict=True):
        if not np.all(h.spatial.blocks(plane)[safe]==128):raise ValueError('canonical mode0 target hidden samples')
    return dict(source=src,temporal=temporal,target=target,coefficients=tuple(coeff),qmap=q,key=key,
                frame_id=frame_id,reference_id=reference_id,reference_tag=reftag)

def plane_proposals(source,temporal,target,control_coeff,tables,safe):
    src=h.spatial.blocks(source);expected=h.spatial.blocks(target);predictions,positions=global_predictions(temporal,target)
    canonical,menus,ranks,rankbits=h.signal.menu_metadata(predictions)
    indices=np.flatnonzero(~safe);coefficients=[];pixels=[];bits=[];sse=[]
    for mode,prediction in enumerate(predictions):
        if mode==0:c=control_coeff.copy();out=expected.copy()
        else:
            c=np.zeros_like(control_coeff);out=np.full_like(expected,128)
            raw=h.m.ft.forward(src[indices].astype(np.int64)-prediction[indices])
            quant=h.m.ft.round_quantize(raw,tables[indices]).astype(np.int16)
            if np.any(np.abs(quant.astype(np.int32))>h.m.ft.MAX_COEFF):raise ValueError('coefficient wire range')
            c[indices]=quant;out[indices]=np.clip(h.m.ft.inverse(quant.astype(np.int64)*tables[indices])+prediction[indices],0,255).astype(np.int16)
        b=np.zeros(len(src),np.int64);e=np.zeros_like(b)
        b[indices]=h.signal.coefficient_bits(c[indices]);e[indices]=np.square(src[indices].astype(np.int64)-out[indices]).sum(axis=(1,2))
        coefficients.append(c);pixels.append(out);bits.append(b);sse.append(e)
    exact=np.stack([np.all(a==expected,axis=(1,2))for a in pixels],axis=1)
    eligible=exact&canonical;eligible[safe]=False
    if not np.all(eligible[indices,0]):raise ValueError('mode0 eligible oracle')
    scores=np.where(eligible,np.stack(bits,axis=1)+rankbits,1<<60)
    chosen=np.argmin(scores,axis=1).astype(np.uint8);chosen[safe]=0
    candidate=np.zeros_like(control_coeff);actual=np.full_like(expected,128)
    for mode in range(4):
        pick=(chosen==mode)&~safe;candidate[pick]=coefficients[mode][pick];actual[pick]=pixels[mode][pick]
    if not np.array_equal(actual,expected):raise ValueError('full oracle output equality')
    costs=np.zeros((len(src),4,6),np.int64)
    for mode in range(4):costs[indices,mode]=np.stack((sse[mode][indices],bits[mode][indices],rankbits[indices,mode],canonical[indices,mode],exact[indices,mode],eligible[indices,mode]),axis=1)
    menus=menus.astype(np.uint8);menus[safe]=0
    return dict(coefficients=candidate,modes=chosen,costs=costs,eligibility=eligible.astype(np.uint8),menus=menus,
                rank_options=ranks,positions=positions,control_modes=np.zeros(len(src),np.uint8))

def rank_component(modes,proposal,safe):
    coder=h.binary.BinaryEncoder();rank_values=np.zeros(len(modes),np.uint8);contexts=set()
    for index in np.flatnonzero(~safe):
        mode=int(modes[index]);count=int(proposal['menus'][index]);rank=int(proposal['rank_options'][index,mode]);position=int(proposal['positions'][index]);rank_values[index]=rank
        if count>1:
            for decision in range(count-1):
                bit=int(rank>decision);ctx=position*12+(count-2)*3+decision
                coder.bit(bit,ctx);contexts.add(ctx)
                if not bit:break
    data,nbits=coder.finish();candidate=b'\x03'+struct.pack('<I',nbits)+data
    old=h.spatial.pack_modes(modes[~safe]);selected=candidate if len(candidate)<len(old)else old
    return selected,dict(old_mode_bytes=len(old),rank_payload_bytes=len(candidate),selected_mode_bytes=len(selected),rank_selected=len(candidate)<len(old),
        arithmetic_bits=nbits,binary_decisions=coder.decisions,probability_products=coder.decisions,renorm_steps=coder.renorm,max_renorm_per_bit=coder.maximum_renorm,
        context_ids=sorted(contexts),menu_counts=[int(np.count_nonzero(proposal['menus']==n))for n in range(1,5)],rank_counts=[int(np.count_nonzero((rank_values==n)&~safe))for n in range(4)],
        logical_probability_state_bytes=88,interval_bits=16,probability_bits=8,multiply_operand_bits=[17,8]),dict(rank_packet=candidate,menus=proposal['menus'],ranks=rank_values)

def packet_from(oracle,proposals,hud,variant):
    mode_payloads=[];coefficient_payloads=[];rank_trials=[];work=[]
    for axis,(proposal,safe,control_coeff)in enumerate(zip(proposals,h.canonical.HIDDEN,oracle['coefficients'],strict=True)):
        modes=proposal['control_modes']if variant=='control'else proposal['modes']
        coeff=control_coeff if variant=='control'else proposal['coefficients']
        mode_payload,mode_work,trial=rank_component(modes,proposal,safe);mode_payloads.append(mode_payload);rank_trials.append(trial)
        visible=coeff[~safe];bw=90 if axis==0 else 45
        full=h.entropy._plane_plan(coeff,bw,h.m);compact=h.entropy._plane_plan(visible,1,h.m);implicit=compact['bytes']+1<full['bytes']
        if implicit:data,*_=h.entropy._construct(visible,1,compact,h.m);data=b'\x04'+data
        else:data,*_=h.entropy._construct(coeff,bw,full,h.m)
        coefficient_payloads.append(data);mode_work.update(plane=axis,coefficient_bytes=len(data),implicit_selected=implicit,fullgrid_payload_bytes=full['bytes'],compact_payload_bytes=compact['bytes']+1)
        work.append(mode_work)
    tag=h.m.C.reference_tag(oracle['target']);packed=h.m.roi.pack_map(oracle['qmap'])
    inner=seal(INNER.pack(b'GR41',1,int(oracle['key']),25,oracle['frame_id'],oracle['reference_id'],720,480,oracle['reference_tag'],tag,len(packed),
        *(len(v)for v in mode_payloads),*(len(v)for v in coefficient_payloads))+packed+b''.join(mode_payloads)+b''.join(coefficient_payloads))
    wire=seal(OUTER.pack(b'RR41',1,int(oracle['key']),25,oracle['frame_id'],oracle['reference_id'],720,480,PROFILE,oracle['reference_tag'],tag,len(inner),len(hud))+inner+hud)
    return dict(packet=wire,planes=oracle['target'],rank_trials=rank_trials,plane_work=work,
                mode_arrays=tuple(p['control_modes']if variant=='control'else p['modes']for p in proposals))

def choose_packet(control,candidate):
    if type(control)is not bytes or not 0<len(control)<=49152 or type(candidate)is not bytes or not candidate:raise ValueError('actual fitting control/candidate bytes')
    return 'candidate'if len(candidate)<=49152 and len(candidate)<len(control)else'control'

def encode_pair(source,reference,qmap,hud,*,frame_id,reference_id):
    start=time.perf_counter_ns();oracle=prepare_oracle(source,reference,qmap,frame_id,reference_id)
    proposals=tuple(plane_proposals(source,base,target,coeff,h.m.roi.block_tables(oracle['qmap'],720,480,axis),safe)
        for axis,(source,base,target,coeff,safe)in enumerate(zip(oracle['source'],oracle['temporal'],oracle['target'],oracle['coefficients'],h.canonical.HIDDEN,strict=True)))
    control=packet_from(oracle,proposals,hud,'control');candidate=packet_from(oracle,proposals,hud,'candidate')
    chosen=choose_packet(control['packet'],candidate['packet']);selected=candidate['packet']if chosen=='candidate'else control['packet']
    work=dict(encode_pair_ms=(time.perf_counter_ns()-start)/1e6,selection=chosen,control_bytes=len(control['packet']),candidate_bytes=len(candidate['packet']),selected_bytes=len(selected),
        host_precomputed_mode0_target=True,exact_full_block_eligibility=True,global_raster_context=True,
        eligible_nonzero_modes=sum(int(p['eligibility'][:,1:].sum())for p in proposals),candidate_nonzero_modes=sum(int(np.count_nonzero(p['modes']))for p in proposals),
        logical_top_edge_int16_bytes=2*(720+360+360),logical_left_edge_int16_bytes=2*8*3,
        complete_FPGA_memory_fit_proven=False,source_candidate_forward_mode0_reused=True)
    return dict(packet=selected,planes=oracle['target'],control=control,candidate=candidate,work=work,proposals=proposals)
