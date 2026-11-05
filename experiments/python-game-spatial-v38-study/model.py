"""SP38 pilot: tile-local residual-edge predictors over a zero-motion base.

The four waves are independent across 2x2-block tiles. Only already reconstructed
neighbors are read. Actual mode maps and entropy payloads are serialized.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
OUTER=h.canonical.HEADER
INNER=struct.Struct('<4sBBHIIHH16s16s7I')
PROFILE=hashlib.sha256(b'SP38:tile2x2-residualEdges-v1:clippedPred:DCavailable:zeroTemporal:Q14:hiddenImmediate:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]
CAP=49152

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def blocks(plane):
    ph,pw=plane.shape
    if ph%8 or pw%8:raise ValueError('complete8x8 plane geometry')
    return plane.reshape(ph//8,8,pw//8,8).transpose(0,2,1,3).reshape(-1,8,8)
def plane_from_blocks(values,height,width):
    return values.reshape(height//8,width//8,8,8).transpose(0,2,1,3).reshape(height,width)

def pack_modes(modes):
    a=np.asarray(modes)
    if a.dtype!=np.uint8 or a.ndim!=1 or not len(a) or np.any(a>3):raise ValueError('bounded visible mode vector')
    pad=np.pad(a,(0,(-len(a))%4));dense=b'\x00'+((pad[::4]<<6)|(pad[1::4]<<4)|(pad[2::4]<<2)|pad[3::4]).tobytes()
    runs=bytearray(b'\x01');index=0
    while index<len(a):
        end=index+1
        while end<len(a)and a[end]==a[index]and end-index<65535:end+=1
        runs.extend(struct.pack('<BH',int(a[index]),end-index));index=end
    options=[dense,bytes(runs)]
    if not np.any(a):options.append(b'\x02')
    return min(options,key=len)

def predictor(base,decoded,indices,bw,dy,dx,mode):
    """Vectorized same tile-position; unavailable residual edges are zero."""
    temporal=base[indices].astype(np.int32)
    top=np.zeros((len(indices),8),np.int32);left=np.zeros_like(top)
    if dy:top=decoded[indices-bw,7,:].astype(np.int32)-base[indices-bw,7,:]
    if dx:left=decoded[indices-1,:,7].astype(np.int32)-base[indices-1,:,7]
    if mode==0:correction=0
    elif mode==1:correction=top[:,None,:]
    elif mode==2:correction=left[:,:,None]
    elif mode==3:
        denominator=8*(dy+dx)
        dc=np.zeros(len(indices),np.int32)if not denominator else(top.sum(1)+left.sum(1)+denominator//2)//denominator
        correction=dc[:,None,None]
    else:raise ValueError('spatial mode0..3')
    return np.clip(temporal+correction,0,255).astype(np.int16)

def encode_plane(source,temporal,tables,safe,policy):
    if policy not in('mode0control','spatial'):raise ValueError('explicit spatial policy')
    height,width=source.shape;bw=width//8;bh=height//8
    src=blocks(source);base=blocks(temporal);decoded=np.zeros_like(base)
    coeff=np.zeros_like(base);modes=np.zeros(len(base),np.uint8)
    costs=np.full((len(base),4,2),-1,np.int64);costs[safe]=0
    yy,xx=np.mgrid[:bh,:bw];evaluated=0
    for dy,dx in((0,0),(0,1),(1,0),(1,1)):
        wave=np.flatnonzero(((yy%2==dy)&(xx%2==dx)).reshape(-1))
        decoded[wave[safe[wave]]]=128
        indices=wave[~safe[wave]]
        if not len(indices):continue
        menu=(0,)if policy=='mode0control'else(0,1,2,3)
        candidate_coeff=[];candidate_pixels=[];scores=[]
        for mode in menu:
            prediction=predictor(base,decoded,indices,bw,dy,dx,mode)
            raw=h.m.ft.forward(src[indices].astype(np.int64)-prediction)
            quant=h.m.ft.round_quantize(raw,tables[indices]).astype(np.int16)
            if np.any(np.abs(quant.astype(np.int32))>h.m.ft.MAX_COEFF):raise ValueError('spatial coefficient wire range')
            pixels=np.clip(h.m.ft.inverse(quant.astype(np.int64)*tables[indices])+prediction,0,255).astype(np.int16)
            sse=np.square(src[indices].astype(np.int64)-pixels).sum(axis=(1,2))
            packet_bytes=h.m.counter.isolated_packet_bytes(quant)
            costs[indices,mode,0]=sse;costs[indices,mode,1]=packet_bytes
            scores.append(sse+8*(packet_bytes-h.m.counter.OVERHEAD))
            candidate_coeff.append(quant);candidate_pixels.append(pixels);evaluated+=len(indices)
        chosen=np.argmin(np.stack(scores),axis=0)
        for menu_index,mode in enumerate(menu):
            selected=chosen==menu_index;dest=indices[selected]
            coeff[dest]=candidate_coeff[menu_index][selected];decoded[dest]=candidate_pixels[menu_index][selected];modes[dest]=mode
    return coeff,plane_from_blocks(decoded,height,width),modes,costs,evaluated

def encode_planes(source,reference,qmap,hud,*,policy,frame_id,reference_id):
    start=time.perf_counter_ns();old=h.m.base.old
    src=old._planes(source,(720,480));q=h.m.roi.check_map(qmap,720,480)
    if not old._id(frame_id)or type(hud)is not bytes:raise ValueError('source identity/HUD')
    key=reference is None
    if key:
        if type(reference_id)is not int or reference_id!=h.m.NO_REF:raise ValueError('key identity')
        base=tuple(np.full_like(a,128)for a in src);reftag=bytes(16)
    else:
        if not old._id(reference_id)or reference_id>=frame_id:raise ValueError('past reference')
        base=old._planes(reference,(720,480));reftag=h.m.C.reference_tag(base)
    coefficients=[];output=[];mode_payloads=[];coeff_payloads=[];mode_arrays=[];cost_arrays=[];details=[]
    for axis,(plane,temporal,safe)in enumerate(zip(src,base,h.canonical.HIDDEN,strict=True)):
        tables=h.m.roi.block_tables(q,720,480,axis)
        c,pixels,modes,costs,evaluated=encode_plane(plane,temporal,tables,safe,policy)
        visible=c[~safe];bw=plane.shape[1]//8
        full=h.entropy._plane_plan(c,bw,h.m);compact=h.entropy._plane_plan(visible,1,h.m)
        implicit=compact['bytes']+1<full['bytes']
        if implicit:
            data,*_=h.entropy._construct(visible,1,compact,h.m);data=b'\x04'+data
        else:data,*_=h.entropy._construct(c,bw,full,h.m)
        mode_blob=pack_modes(modes[~safe]);mode_payloads.append(mode_blob);coeff_payloads.append(data)
        coefficients.append(c);output.append(pixels);mode_arrays.append(modes);cost_arrays.append(costs)
        details.append(dict(plane=axis,mode_bytes=len(mode_blob),coefficient_bytes=len(data),implicit_selected=implicit,
            visible_blocks=int((~safe).sum()),hidden_blocks=int(safe.sum()),mode_counts=[int(np.count_nonzero(modes[~safe]==v))for v in range(4)],
            evaluated_block_candidates=evaluated,fullgrid_payload_bytes=full['bytes'],compact_payload_bytes=compact['bytes']+1))
    output=tuple(output);outtag=h.m.C.reference_tag(output);packed_q=h.m.roi.pack_map(q)
    inner=seal(INNER.pack(b'TS38',1,int(key),25,frame_id,reference_id,720,480,reftag,outtag,len(packed_q),
        *(len(v)for v in mode_payloads),*(len(v)for v in coeff_payloads))+packed_q+b''.join(mode_payloads)+b''.join(coeff_payloads))
    wire=seal(OUTER.pack(b'SP38',1,int(key),25,frame_id,reference_id,720,480,PROFILE,reftag,outtag,len(inner),len(hud))+inner+hud)
    work=dict(encode_ms=(time.perf_counter_ns()-start)/1e6,planes=details,policy=policy,
        mode_bytes=sum(map(len,mode_payloads)),coefficient_bytes=sum(map(len,coeff_payloads)),qmap_bytes=len(packed_q),
        outer_bytes=OUTER.size+4,inner_header_bytes=INNER.size+4,cap_fit=len(wire)<=CAP,
        selector='sourceYUVSSE+8*(isolatedCP02packetbytes-fixedOVERHEAD),lambda1;tieslowestmode',
        RDO_pruning=False,frame_complete_bytes=len(wire),fullgrid_coefficient_arrays_bytes=sum(c.nbytes for c in coefficients))
    return wire,output,work,tuple(mode_arrays),tuple(cost_arrays)
