"""Lossless post-RDO MB mixture; no re-quantization/re-RDO in serialization."""
import struct,time,zlib
import numpy as np
import helpers as h
HEADER=h.base.canonical.HEADER

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def source_proposal(prepared,qmap,hud):
    start=time.perf_counter_ns();cs37,normalized,coeff,payloads,work=h.producer.encode_proposal(prepared,qmap,hud)
    packet,attempts,abwork=h.producer.transcode(cs37,coeff,payloads)
    return dict(packet=packet,cs37=cs37,normalized=normalized,coefficients=coeff,payloads=payloads,proposal_work=work,attempts=attempts,
                transcode_work=abwork,encode_ms=(time.perf_counter_ns()-start)/1e6,prepared=prepared)

def selection(zero,grid,grid_vectors):
    start=time.perf_counter_ns();difference=np.zeros((345,3),np.int64);costs=np.zeros((345,2,2),np.int64)
    for axis,(a,b,safe)in enumerate(zip(zero['normalized'],grid['normalized'],h.base.canonical.HIDDEN,strict=True)):
        pixel_ids,block_ids=h.geometry(axis);np.add.at(difference[:,axis],pixel_ids,(a!=b).astype(np.int64).reshape(-1))
        for index,p in enumerate((zero,grid)):
            bits=h.fine.coefficient_bits(p['coefficients'][axis]);bits[safe]=0;np.add.at(costs[:,index,0],block_ids,bits)
    nonzero=np.any(grid_vectors.reshape(-1,2)!=0,axis=1);costs[:,1,1]=16*nonzero
    eligible=nonzero&~np.any(difference!=0,axis=1)
    chosen=eligible&(costs[:,1].sum(1)<costs[:,0].sum(1))
    return chosen.reshape(15,23),eligible.reshape(15,23),difference.reshape(15,23,3),costs.reshape(15,23,2,2),dict(
        selection_ms=(time.perf_counter_ns()-start)/1e6,eligible_nonzero_MB=int(eligible.sum()),selected_MB=int(chosen.sum()),
        fine_bits_post_RDO=True,hidden_bits_excluded=True,motion_proxy_bits=16)

def mix(zero,grid,choice,grid_vectors):
    start=time.perf_counter_ns();flat=choice.reshape(-1);coefficients=[];prediction=[]
    if choice.dtype!=np.bool_ or choice.shape!=(15,23):raise ValueError('fixed bool MB map')
    for axis,(cz,cg,pz,pg)in enumerate(zip(zero['coefficients'],grid['coefficients'],zero['prepared'].prediction,grid['prepared'].prediction,strict=True)):
        pixels,blocks=h.geometry(axis);c=np.where(flat[blocks,None,None],cg,cz).copy();p=np.where(flat[pixels].reshape(pz.shape),pg,pz).copy()
        c.setflags(write=False);p.setflags(write=False);coefficients.append(c);prediction.append(p)
    vectors=np.where(choice[...,None],grid_vectors,0).astype(np.int8)
    return tuple(coefficients),tuple(prediction),vectors,dict(materialize_ms=(time.perf_counter_ns()-start)/1e6,post_RDO_coefficient_mixture=True,
        source_quantize_calls=0,source_RDO_calls=0,source_reversion_calls=0,source_forward_calls=0)

def serialize(prepared,coefficients,prediction,vectors,qmap,hud,expected_normalized):
    start=time.perf_counter_ns();m=h.m
    if not isinstance(prepared,m.Prepared)or prepared.owner is not m._PREPARED_OWNER:raise ValueError('owned metadata')
    if(prepared.width,prepared.height,prepared.epoch)!=(720,480,25):raise ValueError('fixed profile')
    if type(hud)is not bytes or not hud:raise ValueError('immutable HUD')
    q=m.roi.check_map(qmap,720,480)
    if vectors.dtype!=np.int8 or vectors.shape!=(15,23,2)or np.any(np.abs(vectors.astype(np.int16))>16)or np.any(vectors%4):raise ValueError('integer-chroma bounded vectors')
    if prepared.key and np.any(vectors):raise ValueError('independent key vectors')
    vector_bytes=b''if prepared.key else m.base.pack_vectors(vectors)
    payloads=[];attempts=[]
    for axis,(coeff,safe)in enumerate(zip(coefficients,h.base.canonical.HIDDEN,strict=True)):
        if coeff.dtype!=np.int16 or coeff.shape!=(len(safe),8,8)or np.any(np.abs(coeff.astype(np.int32))>2048)or np.any(coeff[safe]):raise ValueError('fixed hidden-zero selected coefficients')
        bw=90 if axis==0 else 45;full=h.base.entropy._plane_plan(coeff,bw,m);visible=coeff[~safe];compact=h.base.entropy._plane_plan(visible,1,m)
        if compact['bytes']+1<full['bytes']:legacy,*_=h.base.entropy._construct(visible,1,compact,m);legacy=b'\x04'+legacy
        else:legacy,*_=h.base.entropy._construct(coeff,bw,full,m)
        options=[legacy];trials=[]
        for implicit in(False,True):
            source=visible if implicit else coeff;blocks_w=1 if implicit else bw;begin=time.perf_counter_ns();encoded,work=h.AB.encode(source,blocks_w)
            wall=(time.perf_counter_ns()-begin)/1e6;data=bytes([6 if implicit else 5])+encoded;options.append(data)
            trials.append(dict(compact=implicit,packet=encoded,payload_bytes=len(data),encode_ms=wall,work=work))
        selected=min(range(3),key=lambda i:len(options[i]));payloads.append(options[selected])
        attempts.append(dict(plane=axis,legacy_payload=legacy,old_bytes=len(legacy),selected=selected,selected_bytes=len(payloads[-1]),trials=trials,
            fullgrid_legacy_bytes=full['bytes'],compact_legacy_bytes=compact['bytes']+1))
    rebuilt=m.gm.reconstruct(coefficients,prediction,q,720,480);normalized=h.base.maskplan.apply_plan(rebuilt,h.base.PLAN)
    for got,want in zip(normalized,expected_normalized,strict=True):
        if not np.array_equal(got,want):raise ValueError('mixed canonical output must equal zero exactly')
    qbytes=m.roi.pack_map(q);inner=seal(m.HEADER.pack(b'GS38',m.VERSION,int(prepared.key),25,prepared.frame_id,prepared.reference_id,720,480,32,m.base.LIMIT,
        prepared.reference_tag,m.C.reference_tag(rebuilt),len(qbytes),len(vector_bytes),*(len(v)for v in payloads))+qbytes+vector_bytes+b''.join(payloads))
    packet=seal(HEADER.pack(b'CS38',1,2|int(prepared.key),25,prepared.frame_id,prepared.reference_id,720,480,h.rx.PROFILE,
        prepared.reference_tag,m.C.reference_tag(normalized),len(inner),len(hud))+inner+hud)
    return dict(packet=packet,normalized=normalized,coefficients=coefficients,prediction=prediction,vectors=vectors,vector_bytes=vector_bytes,attempts=attempts,
        serialize_work=dict(serialize_ms=(time.perf_counter_ns()-start)/1e6,source_quantize_calls=0,source_RDO_calls=0,source_reversion_calls=0,
            legacy_plane_plans=6,legacy_plane_constructions=3,AB38_encode_calls=6,output_inverse_reconstructions=1,canonical_output_exact_zero=True))

def choose(zero_bytes,candidate_bytes):
    if any(type(v)is not int or v<0 for v in(zero_bytes,candidate_bytes)):raise ValueError('actual integer complete byte lengths')
    return 'mixed'if candidate_bytes<=49152 and candidate_bytes<zero_bytes else'zero'
