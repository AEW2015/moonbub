"""Direct byte-identical CN36 skip sender; preserve original RDO decisions.

No full-packet encode, syntax decode or discarded full inverse reconstruction.
The unmasked legacy size plans remain paid: their plane-global reversion choice
can affect visible coefficients and cannot be skipped without changing output.
"""
import struct,time,zlib
import numpy as np
import helpers as h

def encode_prepared(prepared,scale_map,hud,rdo_lambda=1):
    start=time.perf_counter_ns();m=h.m;p=prepared
    if not isinstance(p,m.Prepared) or p.owner is not m._PREPARED_OWNER:raise ValueError('owned GM27 preparation')
    if type(rdo_lambda) not in (int,float) or not np.isfinite(rdo_lambda) or not 0<=rdo_lambda<=1000000:raise ValueError('RDO lambda')
    if (p.width,p.height)!=(720,480) or p.epoch!=25:raise ValueError('fixed CN36 profile')
    q=m.roi.check_map(scale_map,p.width,p.height)
    original=m.base._quantize(p.raw_coefficients,q,p.width,p.height)
    pruned,rdo=m.counter.rdo_skip(p,original,q,rdo_lambda)
    selected=[];reversions=[];legacy_calls=0;plane_details=[]
    for axis,c in enumerate(pruned):
        bw=((p.width if axis==0 else p.width//2)+7)//8
        plan=m.legacy_plan(c,bw);legacy_calls+=1;reverted=False
        if not np.array_equal(c,original[axis]):
            other=m.legacy_plan(original[axis],bw);legacy_calls+=1
            if other['bytes']<plan['bytes']:c=original[axis];plan=other;reverted=True
        # RDO/reversion is decided on the original coefficient fields BEFORE
        # suppressing hidden blocks, matching runtime28 and the v36 proof path.
        selected.append(c.copy());reversions.append(reverted)
        plane_details.append(dict(original_selected_legacy_bytes=plan['bytes'],rdo_reverted=reverted))
    removed=0
    for c,mask in zip(selected,h.canonical.HIDDEN,strict=True):
        removed+=int(np.count_nonzero(c[mask]));c[mask]=0
    payloads=[]
    for axis,c in enumerate(selected):
        bw=((p.width if axis==0 else p.width//2)+7)//8
        plan=h.entropy._plane_plan(c,bw,m);data,*_=h.entropy._construct(c,bw,plan,m)
        assert len(data)==plan['bytes'];payloads.append(data)
        plane_details[axis].update(skip_mode=plan['mode'],skip_payload_bytes=len(data))
    rebuilt=m.gm.reconstruct(tuple(selected),p.prediction,q,p.width,p.height)
    outtag=m.C.reference_tag(rebuilt);qmap=m.roi.pack_map(q)
    body=m.HEADER.pack(m.MAGIC,m.VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,m.base.LIMIT,
        p.reference_tag,outtag,len(qmap),len(p.vector_bytes),*(len(v) for v in payloads))+qmap+p.vector_bytes+b''.join(payloads)
    inner=body+struct.pack('<I',zlib.crc32(body))
    normalized=h.maskplan.apply_plan(rebuilt,h.PLAN)
    # Frozen wrapper only checks metadata; it does not entropy-decode a packet.
    wire=h.canonical.wrap(inner,hud,normalized,skip=True)
    work=dict(direct_encode_ms=(time.perf_counter_ns()-start)/1e6,
        legacy_selection_plan_calls=legacy_calls,original_rdo_reversions=reversions,
        removed_nonzero_coefficients=removed,planes=plane_details,
        full_packet_encode_calls=0,coefficient_parse_calls=0,skip_entropy_plane_constructions=3,
        output_inverse_reconstructions=1,normalization_passes=1,wrappers=1,
        raw_forward_and_RDO_work_retained=True,compiled_mask_plan_setup_paid_once=True)
    return wire,normalized,work
