"""Fixed global_grid32 versus zero motion, actual CS37 and AB38 options paid.

The CS37 constructor below explicitly retains integrated38's decisions, deferring
ONLY its intermediate packet cap. A final CS38 candidate must fit before receive.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
HEADER=h.base.canonical.HEADER
PROFILE=hashlib.sha256(b'CS37:implicit-hidden-raster-v1:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]
def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def encode_proposal(prepared,scale_map,hud,rdo_lambda=1):
    start=time.perf_counter_ns();m=h.m;p=prepared
    if not isinstance(p,m.Prepared)or p.owner is not m._PREPARED_OWNER:raise ValueError('owned preparation')
    if(p.width,p.height,p.epoch)!=(720,480,25):raise ValueError('fixed profile')
    if type(rdo_lambda)not in(int,float)or not np.isfinite(rdo_lambda)or not 0<=rdo_lambda<=1000000:raise ValueError('bounded RDO')
    if type(hud)is not bytes or not hud:raise ValueError('immutable HUD')
    q=m.roi.check_map(scale_map,p.width,p.height);original=m.base._quantize(p.raw_coefficients,q,p.width,p.height)
    pruned,rdo=m.counter.rdo_skip(p,original,q,rdo_lambda);selected=[];details=[];legacy_calls=0
    for axis,c in enumerate(pruned):
        bw=(p.width if axis==0 else p.width//2)//8;plan=m.legacy_plan(c,bw);legacy_calls+=1;reverted=False
        if not np.array_equal(c,original[axis]):
            other=m.legacy_plan(original[axis],bw);legacy_calls+=1
            if other['bytes']<plan['bytes']:c=original[axis];plan=other;reverted=True
        selected.append(c.copy());details.append(dict(plane=axis,original_legacy_bytes=plan['bytes'],rdo_reverted=reverted))
    removed=0;payloads=[]
    for axis,(coeff,mask,detail)in enumerate(zip(selected,h.base.canonical.HIDDEN,details,strict=True)):
        removed+=int(np.count_nonzero(coeff[mask]));coeff[mask]=0;bw=(p.width if axis==0 else p.width//2)//8
        full=h.base.entropy._plane_plan(coeff,bw,m);visible=coeff[~mask];compact=h.base.entropy._plane_plan(visible,1,m)
        sparse=compact['bytes']+1<full['bytes']
        if sparse:payload,*_=h.base.entropy._construct(visible,1,compact,m);payload=b'\x04'+payload
        else:payload,*_=h.base.entropy._construct(coeff,bw,full,m)
        payloads.append(payload);coeff.setflags(write=False)
        detail.update(fullgrid_payload_bytes=full['bytes'],compact_payload_bytes=compact['bytes']+1,selected_payload_bytes=len(payload),implicit_selected=sparse)
    rebuilt=m.gm.reconstruct(tuple(selected),p.prediction,q,p.width,p.height);tag=m.C.reference_tag(rebuilt);qmap=m.roi.pack_map(q)
    inner=seal(m.HEADER.pack(b'GS37',m.VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,m.base.LIMIT,
        p.reference_tag,tag,len(qmap),len(p.vector_bytes),*(len(v)for v in payloads))+qmap+p.vector_bytes+b''.join(payloads))
    normalized=h.base.maskplan.apply_plan(rebuilt,h.base.PLAN)
    packet=seal(HEADER.pack(b'CS37',1,2|int(p.key),25,p.frame_id,p.reference_id,720,480,PROFILE,p.reference_tag,m.C.reference_tag(normalized),len(inner),len(hud))+inner+hud)
    work=dict(encode_ms=(time.perf_counter_ns()-start)/1e6,legacy_selection_plan_calls=legacy_calls,planes=details,
        original_rdo_reversions=[v['rdo_reverted']for v in details],removed_nonzero_coefficients=removed,
        fullgrid_plane_plans=3,compact_plane_plans=3,selected_plane_constructions=3,output_inverse_reconstructions=1,
        original_global_RDO_reversion_before_hidden=True,intermediate_cap_deferred=True,intermediate_bytes=len(packet),
        intermediate_overcap=len(packet)>49152)
    return packet,normalized,tuple(selected),tuple(payloads),work

def transcode(packet,coefficients,legacy_payloads):
    start=time.perf_counter_ns();outer=list(HEADER.unpack_from(packet));inside=packet[HEADER.size:HEADER.size+outer[11]]
    fields=list(h.m.HEADER.unpack_from(inside));end=h.m.HEADER.size+fields[12]+fields[13];maps=inside[h.m.HEADER.size:end]
    payloads=[];attempts=[]
    for axis,(coeff,mask,old)in enumerate(zip(coefficients,h.base.canonical.HIDDEN,legacy_payloads,strict=True)):
        options=[old];trials=[]
        for compact in(False,True):
            source=coeff[~mask]if compact else coeff;bw=1 if compact else(90 if axis==0 else 45)
            began=time.perf_counter_ns();encoded,work=h.AB.encode(source,bw);wall=(time.perf_counter_ns()-began)/1e6
            candidate=bytes([6 if compact else 5])+encoded;options.append(candidate)
            trials.append(dict(compact=compact,packet=encoded,payload_bytes=len(candidate),encode_ms=wall,work=work))
        index=min(range(3),key=lambda i:len(options[i]));payloads.append(options[index])
        attempts.append(dict(plane=axis,legacy_payload=old,old_bytes=len(old),selected=index,selected_bytes=len(payloads[-1]),trials=trials))
    fields[0]=b'GS38';fields[14:17]=map(len,payloads);inner=seal(h.m.HEADER.pack(*fields)+maps+b''.join(payloads))
    outer[0]=b'CS38';outer[8]=h.rx.PROFILE;outer[11]=len(inner)
    result=seal(HEADER.pack(*outer)+inner+packet[HEADER.size+HEADER.unpack_from(packet)[11]:-4])
    return result,attempts,dict(transcode_ms=(time.perf_counter_ns()-start)/1e6,AB38_encode_calls=6,final_bytes=len(result),final_cap_fit=len(result)<=49152)
