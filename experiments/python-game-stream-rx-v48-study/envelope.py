"""Original CS38 envelopes, arithmetic-only receiver capability; no coefficients."""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
HEADER=h.f.HEADER
PROFILE=hashlib.sha256(b'CS38:adaptive-binary-coefficients-v1:'+json.dumps(h.f.f.n.RECTS,separators=(',',':')).encode()).digest()[:16]
CAP=49152

def parse_envelope(packet):
    start=time.perf_counter_ns();m=h.m
    if type(packet)is not bytes or not HEADER.size+8<=len(packet)<=CAP:raise ValueError('CS38 bounded immutable packet')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('CS38 original CRC')
    magic,version,flags,epoch,fid,rid,w,hh,profile,rt,ot,nb,nh=HEADER.unpack_from(packet)
    if (magic,version,epoch,w,hh,profile)!=(b'CS38',1,25,720,480,PROFILE)or flags not in(2,3):raise ValueError('CS38 fixed profile')
    key=bool(flags&1)
    if fid>=m.NO_REF or ot==bytes(16):raise ValueError('CS38 frame/output identity')
    if key:
        if rid!=m.NO_REF or rt!=bytes(16):raise ValueError('CS38 independent key identity')
    elif rid>=fid or rt==bytes(16):raise ValueError('CS38 prior reference identity')
    if nb<m.HEADER.size+7 or nh<=0 or len(packet)!=HEADER.size+nb+nh+4:raise ValueError('CS38 exact component lengths')
    inner=packet[HEADER.size:HEADER.size+nb];hud=packet[HEADER.size+nb:-4]
    if zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('GS38 original CRC')
    im,iv,ik,ie,iff,ir,iw,ih,bs,limit,irt,base_tag,nq,nv,*lengths=m.HEADER.unpack_from(inner)
    if (im,iv,ik,ie,iff,ir,iw,ih,irt)!=(b'GS38',m.VERSION,int(key),25,fid,rid,720,480,rt)or limit!=m.base.LIMIT:
        raise ValueError('GS38 identity/profile binding')
    mw,mh=m.base._grid(w,hh,bs)
    if base_tag==bytes(16)or nq!=(((w+15)//16)*((hh+15)//16)+3)//4:raise ValueError('GS38 quant/output identity')
    if key:
        if nv:raise ValueError('GS38 independent key vectors')
    elif not 1<=nv<=1+2*mw*mh:raise ValueError('GS38 P vector bytes')
    if len(lengths)!=3 or any(not 1<=length<=132*((((w if axis==0 else w//2)+7)//8)*(((hh if axis==0 else hh//2)+7)//8))+256 for axis,length in enumerate(lengths)):
        raise ValueError('GS38 bounded coefficient component length')
    if m.HEADER.size+nq+nv+sum(lengths)+4!=len(inner):raise ValueError('GS38 exact body length')
    hm=h.f.f.hud._meta(hud)
    if (hm['epoch'],hm['frame_id'],hm['reference_id'],hm['width'],hm['height'],tuple(hm['rectangles']))!=(25,fid,rid,w,hh,h.f.f.n.RECTS):
        raise ValueError('CS38 exact HUD identity/rectangles')
    pos=m.HEADER.size;qmap=m.roi.unpack_map(inner[pos:pos+nq],(w+15)//16,(hh+15)//16);pos+=nq
    vectors=np.zeros((mh,mw,2),np.int8)if key else m.base.unpack_vectors(inner[pos:pos+nv],mw,mh);pos+=nv
    payloads=[]
    for length in lengths:
        data=inner[pos:pos+length];pos+=length
        if not data or data[0] not in (5,6):raise ValueError('stream48 arithmetic-only coefficient capability')
        payloads.append(data)
    if pos!=len(inner)-4:raise ValueError('GS38 component ending')
    qmap.setflags(write=False);vectors.setflags(write=False)
    return dict(key=key,frame_id=fid,reference_id=rid,reference_tag=rt,output_tag=ot,base_tag=base_tag,qmap=qmap,vectors=vectors,block_size=bs,hud=hud,plane_payloads=tuple(payloads),parse_ms=(time.perf_counter_ns()-start)/1e6)
