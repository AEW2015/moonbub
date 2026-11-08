"""EC26 exact sparse coefficient runs; GE26 lossless GM25 plane repacking.

No native decoder or FPGA-resource claim. Zlib is CRC/artifact storage only.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return m


old = load_module('entropy26_frozen_base', HERE.parent/'python-game-base-motion-v25-study/model.py')
f = old.gm.token_coeff.frozen
HEADER = old.HEADER
COEFF = struct.Struct('<4sBBIHH4I3I')
NO_REF, C, roi, ft, _id = old.NO_REF, old.C, old.roi, old.ft, old._id
BANDS = ((1, 6), (6, 21), (21, 64))


def seal(body): return body+struct.pack('<I',zlib.crc32(body))


def _rice_cost(values, maximum, escape):
    a = np.asarray(values, np.int64)
    if not a.size: return 0
    if np.any(a < 0) or np.any(a >= 1 << escape): raise ValueError('Rice domain')
    return min(range(maximum+1),key=lambda k:int(np.where((a>>k)<15,(a>>k)+1+k,15+escape).sum()))


def _bits(values, k, escape):
    return ''.join(f._rice(int(v),k,escape) for v in values)


def encode_coefficients(coefficients, blocks_w, *, layout=0):
    """Exact coefficient coding: DC row deltas + three cross-block sparse runs."""
    a = f._check(coefficients, blocks_w)
    if type(layout) is not int or layout not in (0,1): raise ValueError('EC26 layout')
    zig = a.reshape(-1,64)[:,f.frozen.ZIGZAG].astype(np.int32)
    dc = zig[:,0].copy(); dc[1:] -= zig[:-1,0]; dc[::blocks_w] = zig[::blocks_w,0]
    values = f._mapped(dc); kd = f._best_k(values,13,14)
    payloads = [bytes([kd])+f._pack(_bits(values,kd,14))]; counts = []
    for lo,hi in BANDS:
        v = zig[:,lo:hi]; seq = (v if layout==0 else v.T).reshape(-1)
        indices = np.flatnonzero(seq); counts.append(len(indices))
        runs = np.diff(np.r_[-1,indices])-1
        levels = f._mapped(seq[indices])-1
        kr,kv = _rice_cost(runs,19,24),f._best_k(levels,11,12)
        tokens = [f._rice(int(r),kr,24)+f._rice(int(v),kv,12) for r,v in zip(runs,levels)]
        payloads.append(bytes([kr,kv])+f._pack(''.join(tokens)))
    flags = layout << 1
    lengths = [len(v) for v in payloads]
    if sum(lengths) >= a.size*2:
        flags, payloads, lengths, counts = 1,[a.astype('<i2').tobytes()],[a.size*2,0,0,0],[0,0,0]
    packet = seal(COEFF.pack(b'EC26',1,flags,len(a),blocks_w,0,*lengths,*counts)+b''.join(payloads))
    return packet


def decode_coefficients(packet, blocks, blocks_w):
    if (type(blocks) is not int or not 1<=blocks<=f.MAX_BLOCKS or type(blocks_w) is not int
            or not 1<=blocks_w<=256 or blocks%blocks_w): raise ValueError('EC26 geometry')
    if type(packet) is not bytes or not COEFF.size+4<=len(packet)<=COEFF.size+4+128*blocks:
        raise ValueError('EC26 bounded packet')
    magic,version,flags,n,bw,reserved,*tail = COEFF.unpack_from(packet)
    lengths,counts = tail[:4],tail[4:]
    if (magic,version,n,bw,reserved)!=(b'EC26',1,blocks,blocks_w,0) or flags not in (0,1,2): raise ValueError('EC26 identity')
    if len(packet)!=COEFF.size+4+sum(lengths) or zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]: raise ValueError('EC26 length/CRC')
    if flags==1:
        if lengths!=[128*blocks,0,0,0] or any(counts): raise ValueError('EC26 raw grammar')
        a=np.frombuffer(packet[COEFF.size:-4],'<i2').copy().reshape(blocks,8,8)
        f._check(a,blocks_w); return a
    if not 2<=lengths[0] or any(v<2 for v in lengths[1:]): raise ValueError('EC26 streams')
    pos=COEFF.size; streams=[]
    for size in lengths: streams.append(packet[pos:pos+size]);pos+=size
    if streams[0][0]>13: raise ValueError('EC26 DC Rice')
    reader=f._Bits(streams[0][1:]);zig=np.zeros((blocks,64),np.int16);prior=0
    for i in range(blocks):
        if i%blocks_w==0: prior=0
        prior+=f._unmap(reader.rice(streams[0][0],14))
        if not -f.MAX_COEFF<=prior<=f.MAX_COEFF: raise ValueError('EC26 DC range')
        zig[i,0]=prior
    reader.finish()
    for (lo,hi),count,data in zip(BANDS,counts,streams[1:]):
        size=blocks*(hi-lo)
        if count>size or data[0]>19 or data[1]>11: raise ValueError('EC26 band bounds')
        seq=np.zeros(size,np.int16);reader=f._Bits(data[2:]);index=-1
        for _ in range(count):
            index+=1+reader.rice(data[0],24)
            if index>=size: raise ValueError('EC26 run overrun')
            value=f._unmap(reader.rice(data[1],12)+1)
            if not value or not -f.MAX_COEFF<=value<=f.MAX_COEFF: raise ValueError('EC26 level')
            seq[index]=value
        reader.finish()
        zig[:,lo:hi]=seq.reshape(blocks,hi-lo) if flags==0 else seq.reshape(hi-lo,blocks).T
    a=np.empty((blocks,64),np.int16);a[:,f.frozen.ZIGZAG]=zig
    return a.reshape(blocks,8,8)


def iter_block_major(packet, blocks, blocks_w):
    """Separate block-at-a-time oracle: four cursors, one128B output block.

    Input packet retained; all iterator errors must complete before publication.
    Frequency-major is deliberately rejected rather than silently staging it.
    """
    if (type(blocks) is not int or not 1<=blocks<=f.MAX_BLOCKS or type(blocks_w) is not int
            or not 1<=blocks_w<=256 or blocks%blocks_w):raise ValueError('stream geometry')
    if type(packet) is not bytes or not COEFF.size+4<=len(packet)<=128*blocks+COEFF.size+4:raise ValueError('stream length')
    magic,version,flags,n,bw,reserved,*tail=COEFF.unpack_from(packet);lengths,counts=tail[:4],tail[4:]
    if (magic,version,n,bw,reserved)!=(b'EC26',1,blocks,blocks_w,0) or flags not in (0,1):raise ValueError('block-major streaming profile')
    if len(packet)!=COEFF.size+4+sum(lengths) or zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('stream framing/CRC')
    if flags==1:
        if lengths!=[128*blocks,0,0,0] or any(counts):raise ValueError('stream raw fields')
        for i in range(blocks):
            a=np.frombuffer(packet,dtype='<i2',count=64,offset=COEFF.size+128*i).copy().reshape(8,8)
            f._check(a[None],1);yield a
        return
    if lengths[0]<2 or any(v<2 for v in lengths[1:]):raise ValueError('stream bounds')
    pos=COEFF.size;streams=[]
    for size in lengths:streams.append(packet[pos:pos+size]);pos+=size
    if streams[0][0]>13:raise ValueError('stream DC parameter')
    dc=f._Bits(streams[0][1:]);readers=[];indices=[-1]*3;remaining=list(counts);heads=[None]*3
    for (lo,hi),data,count in zip(BANDS,streams[1:],counts):
        if count>blocks*(hi-lo) or data[0]>19 or data[1]>11:raise ValueError('stream AC bounds')
        readers.append(f._Bits(data[2:]))
    def advance(band):
        if not remaining[band]:heads[band]=None;return
        lo,hi=BANDS[band];data=streams[band+1];reader=readers[band]
        indices[band]+=1+reader.rice(data[0],24)
        if indices[band]>=blocks*(hi-lo):raise ValueError('stream run overrun')
        value=f._unmap(reader.rice(data[1],12)+1)
        if not value or not -f.MAX_COEFF<=value<=f.MAX_COEFF:raise ValueError('stream level')
        heads[band]=(indices[band],value);remaining[band]-=1
    for band in range(3):advance(band)
    previous=0
    for block in range(blocks):
        if block%blocks_w==0:previous=0
        previous+=f._unmap(dc.rice(streams[0][0],14))
        if not -f.MAX_COEFF<=previous<=f.MAX_COEFF:raise ValueError('stream DC range')
        a=np.zeros(64,np.int16);a[0]=previous
        for band,(lo,hi) in enumerate(BANDS):
            start=block*(hi-lo);end=start+hi-lo
            while heads[band] is not None and heads[band][0]<end:
                index,value=heads[band]
                if index<start:raise ValueError('stream ordering')
                a[int(f.frozen.ZIGZAG[lo+index-start])]=value;advance(band)
        yield a.reshape(8,8)
    if any(remaining) or any(h is not None for h in heads):raise ValueError('stream unfinished')
    dc.finish()
    for reader in readers:reader.finish()


def repack(packet, *, layouts=(0,1)):
    """Try both actual EC26 layouts per plane; old payload fallback never grows."""
    if type(layouts) is not tuple or layouts not in ((0,),(0,1)):raise ValueError('declared entropy layouts')
    start=time.perf_counter_ns();meta=old.parse(packet)
    fields=list(HEADER.unpack_from(packet));nq,nv,*sizes=fields[-5:]
    pos=HEADER.size+nq+nv;payloads=[];work=[]
    for plane,(size,coeff) in enumerate(zip(sizes,meta['coefficients'])):
        before=packet[pos:pos+size];pos+=size
        pw=meta['width'] if plane==0 else meta['width']//2;bw=(pw+7)//8
        candidates=[encode_coefficients(coeff,bw,layout=l) for l in layouts]
        chosen=min(range(len(layouts)),key=lambda i:len(candidates[i]))
        candidate=b'\x03'+candidates[chosen]
        selected=candidate if len(candidate)<len(before) else before
        payloads.append(selected)
        work.append(dict(old_bytes=len(before),ec26_bytes=[len(p)+1 for p in candidates],
                         selected_bytes=len(selected),selected_mode='EC26' if selected is candidate else 'frozen',
                         selected_layout=layouts[chosen] if selected is candidate else None,
                         blocks=len(coeff),nonzero_coefficients=int(np.count_nonzero(coeff)),actual_entropy_candidates=1+len(layouts)))
    fields[0]=b'GE26';fields[-3:]=[len(p) for p in payloads]
    body=HEADER.pack(*fields)+packet[HEADER.size:HEADER.size+nq+nv]+b''.join(payloads)
    output=seal(body);assert len(output)<=len(packet)
    return output,dict(old_bytes=len(packet),new_bytes=len(output),planes=work,
                       repack_ms=(time.perf_counter_ns()-start)/1e6,
                       scope='Paid reparse, both EC26 layouts, fixed frozen incumbent; prior encoder cost is separate.')


def parse(packet, *, expected_epoch=None):
    if type(packet) is not bytes or not HEADER.size+4<=len(packet)<=old.MAX_PACKET: raise ValueError('GE26 length')
    fields=HEADER.unpack_from(packet)
    magic,version,key,epoch,fid,refid,w,h,bs,limit,reftag,outtag,nq,nv,*sizes=fields
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('GE26 CRC')
    if magic!=b'GE26' or version!=1 or key not in (0,1) or limit!=old.LIMIT:raise ValueError('GE26 profile')
    roi.geometry(w,h);mw,mh=old._grid(w,h,bs)
    if not _id(epoch) or not _id(fid) or expected_epoch is not None and epoch!=expected_epoch:raise ValueError('GE26 identity')
    if key:
        if refid!=NO_REF or reftag!=old.ZERO_TAG or nv:raise ValueError('GE26 key')
    elif not _id(refid) or refid>=fid or not 1<=nv<=1+2*mw*mh:raise ValueError('GE26 reference')
    if nq!=((w+15)//16*((h+15)//16)+3)//4 or len(packet)!=HEADER.size+4+nq+nv+sum(sizes):raise ValueError('GE26 framing')
    pos=HEADER.size; q=roi.unpack_map(packet[pos:pos+nq],(w+15)//16,(h+15)//16);pos+=nq
    vectors=np.zeros((mh,mw,2),np.int8) if key else old.unpack_vectors(packet[pos:pos+nv],mw,mh);pos+=nv
    coefficients=[]
    for plane,size in enumerate(sizes):
        pw,ph=(w,h) if plane==0 else (w//2,h//2);n=((pw+7)//8)*((ph+7)//8);bw=(pw+7)//8
        if not 1<=size<=132*n+256:raise ValueError('GE26 plane bound')
        payload=packet[pos:pos+size];pos+=size
        coeff=decode_coefficients(payload[1:],n,bw) if payload[0]==3 else old._decode_plane(payload,n,bw)
        coefficients.append(coeff)
    return dict(epoch=epoch,frame_id=fid,reference_id=refid,key=bool(key),width=w,height=h,block_size=bs,
                vectors=vectors,scale_map=q,coefficients=tuple(coefficients),reference_tag=reftag,reconstructed_tag=outtag)


def decode(packet, reference=None, *, expected_epoch=None, expected_reference_id=None):
    meta=parse(packet,expected_epoch=expected_epoch);w,h=meta['width'],meta['height']
    if meta['key']:
        prediction=tuple(np.full(s,128,np.int16) for s in ((h,w),(h//2,w//2),(h//2,w//2)))
    else:
        if expected_reference_id is None or expected_reference_id!=meta['reference_id']:raise ValueError('GE26 expected reference')
        ref=old._planes(reference,(w,h))
        if C.reference_tag(ref)!=meta['reference_tag']:raise ValueError('GE26 actual reference tag')
        prediction=old.predict(ref,meta['vectors'],meta['block_size'])
    rebuilt=old.gm.reconstruct(meta['coefficients'],prediction,meta['scale_map'],w,h)
    if C.reference_tag(rebuilt)!=meta['reconstructed_tag']:raise ValueError('GE26 output tag')
    return rebuilt,meta
