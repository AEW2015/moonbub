"""Direct GS37/CS37: evaluate full/implicit plans, serialize winner only.

Original global plane reversion decisions remain paid before hidden suppression.
No CN36 intermediate packet, entropy reparse, transcoder or discarded inverse.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
HEADER=h.canonical.HEADER
PROFILE=hashlib.sha256(b'CS37:implicit-hidden-raster-v1:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))

def encode_prepared(prepared,scale_map,hud,rdo_lambda=1):
    start=time.perf_counter_ns();m=h.m;p=prepared
    if not isinstance(p,m.Prepared) or p.owner is not m._PREPARED_OWNER:raise ValueError('owned GM27 preparation')
    if (p.width,p.height,p.epoch)!=(720,480,25):raise ValueError('fixed CS37 profile')
    if type(rdo_lambda)not in (int,float) or not np.isfinite(rdo_lambda) or not 0<=rdo_lambda<=1000000:raise ValueError('bounded RDO lambda')
    if type(hud)is not bytes or not hud:raise ValueError('immutable nonempty exact HUD input')
    q=m.roi.check_map(scale_map,p.width,p.height)
    original=m.base._quantize(p.raw_coefficients,q,p.width,p.height)
    pruned,rdo=m.counter.rdo_skip(p,original,q,rdo_lambda)
    selected=[];details=[];legacy_calls=0
    for axis,c in enumerate(pruned):
        bw=((p.width if axis==0 else p.width//2)+7)//8
        plan=m.legacy_plan(c,bw);legacy_calls+=1;reverted=False
        if not np.array_equal(c,original[axis]):
            other=m.legacy_plan(original[axis],bw);legacy_calls+=1
            if other['bytes']<plan['bytes']:c=original[axis];plan=other;reverted=True
        selected.append(c.copy());details.append(dict(plane=axis,original_legacy_bytes=plan['bytes'],rdo_reverted=reverted))
    removed=0;payloads=[]
    for axis,(coeff,mask,detail) in enumerate(zip(selected,h.canonical.HIDDEN,details,strict=True)):
        removed+=int(np.count_nonzero(coeff[mask]));coeff[mask]=0
        bw=((p.width if axis==0 else p.width//2)+7)//8
        full_plan=h.entropy._plane_plan(coeff,bw,m)
        visible=coeff[~mask]
        compact_plan=h.entropy._plane_plan(visible,1,m)
        sparse=compact_plan['bytes']+1<full_plan['bytes']
        if sparse:
            payload,*_=h.entropy._construct(visible,1,compact_plan,m);payload=b'\x04'+payload
        else:payload,*_=h.entropy._construct(coeff,bw,full_plan,m)
        payloads.append(payload)
        detail.update(full_blocks=len(coeff),hidden_blocks=int(mask.sum()),visible_blocks=len(visible),
            fullgrid_payload_bytes=full_plan['bytes'],compact_payload_bytes=compact_plan['bytes']+1,
            selected_payload_bytes=len(payload),implicit_selected=sparse)
        assert len(payload)==min(full_plan['bytes'],compact_plan['bytes']+1)
    rebuilt=m.gm.reconstruct(tuple(selected),p.prediction,q,p.width,p.height)
    tag=m.C.reference_tag(rebuilt);qmap=m.roi.pack_map(q)
    inner=seal(m.HEADER.pack(b'GS37',m.VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,m.base.LIMIT,
        p.reference_tag,tag,len(qmap),len(p.vector_bytes),*(len(v)for v in payloads))+qmap+p.vector_bytes+b''.join(payloads))
    normalized=h.maskplan.apply_plan(rebuilt,h.PLAN)
    outer=HEADER.pack(b'CS37',1,2|int(p.key),25,p.frame_id,p.reference_id,720,480,PROFILE,
                      p.reference_tag,m.C.reference_tag(normalized),len(inner),len(hud))
    wire=seal(outer+inner+hud)
    if len(wire)>49152:raise ValueError('complete CS37 frame cap')
    work=dict(integrated_encode_ms=(time.perf_counter_ns()-start)/1e6,planes=details,
        legacy_selection_plan_calls=legacy_calls,original_rdo_reversions=[d['rdo_reverted']for d in details],
        removed_nonzero_coefficients=removed,fullgrid_plane_plans=3,compact_plane_plans=3,
        selected_plane_constructions=3,discarded_plane_constructions=0,
        CN36_intermediate_packets=0,coefficient_parse_calls=0,transcoder_calls=0,
        output_inverse_reconstructions=1,normalization_passes=1,CS37_wrappers=1,
        original_global_RDO_reversion_before_hidden=True)
    return wire,normalized,work
