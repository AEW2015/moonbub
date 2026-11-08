"""Direct CS38/GS38 decoder: entropy decode once, reconstruct once, commit last.

Full coefficient arrays remain. No entropy encode/planning, converted CS37
packet or frozen-global mutation is used anywhere in this receive path.
"""
import hashlib,json,struct,time,zlib
import numpy as np
import helpers as h
HEADER=h.f.HEADER
PROFILE=hashlib.sha256(b'CS38:adaptive-binary-coefficients-v1:'+json.dumps(h.f.f.n.RECTS,separators=(',',':')).encode()).digest()[:16]
CAP=49152

def parse(packet):
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
    coefficients=[];dispatches=[];payloads=[];binary_planes=0;counts=[0]*7
    for axis,(length,safe)in enumerate(zip(lengths,h.f.f.safe_blocks(),strict=True)):
        data=inner[pos:pos+length];pos+=length
        if not data:raise ValueError('GS38 empty coefficient component')
        dispatch=data[0];mask=safe.reshape(-1);blocks=len(mask);bw=(w if axis==0 else w//2)//8
        if dispatch in(0,1,2,3):coeff=m.base._decode_plane(data,blocks,bw)
        elif dispatch==4:
            visible=m.base._decode_plane(data[1:],int((~mask).sum()),1)
            coeff=np.zeros((blocks,8,8),np.int16);coeff[~mask]=visible
        elif dispatch in(5,6):
            compact=dispatch==6;count=int((~mask).sum())if compact else blocks
            decoded=h.arithmetic.decode(data[1:],count,1 if compact else bw)
            if compact:
                coeff=np.zeros((blocks,8,8),np.int16);coeff[~mask]=decoded
            else:coeff=decoded
            binary_planes+=1
        else:raise ValueError('GS38 coefficient dispatch0..6')
        if coeff.shape!=(blocks,8,8)or coeff.dtype!=np.int16 or np.any(coeff[mask]):raise ValueError('GS38 canonical hidden coefficients')
        coeff.setflags(write=False);coefficients.append(coeff);dispatches.append(dispatch);payloads.append(data);counts[dispatch]+=1
    if pos!=len(inner)-4:raise ValueError('GS38 coefficient component ending')
    qmap.setflags(write=False);vectors.setflags(write=False)
    return dict(key=key,frame_id=fid,reference_id=rid,reference_tag=rt,output_tag=ot,base_tag=base_tag,
        qmap=qmap,vectors=vectors,block_size=bs,coefficients=tuple(coefficients),hud=hud,
        dispatch=dispatches,plane_payloads=payloads,binary_planes=binary_planes,
        decode_work=dict(parse_ms=(time.perf_counter_ns()-start)/1e6,dispatch_counts=counts,
            entropy_plan_calls=0,entropy_construct_calls=0,synthetic_reencoded_packets=0,
            binary_plane_decode_calls=binary_planes,coefficient_array_bytes=sum(c.nbytes for c in coefficients)))

class Receiver:
    def __init__(self):self.ref=None;self.rid=h.m.NO_REF;self.hud=None;self.last=-1
    def receive(self,packet):
        start=time.perf_counter_ns();meta=parse(packet);key=meta['key'];fid=meta['frame_id'];m=h.m
        if fid<=self.last:raise ValueError('CS38 monotonic publication')
        if key:prediction=tuple(np.full(s,128,np.int16)for s in((480,720),(240,360),(240,360)))
        else:
            if self.ref is None or self.rid!=meta['reference_id']or m.C.reference_tag(self.ref)!=meta['reference_tag']:
                raise ValueError('CS38 actual committed reference')
            prediction=m.predict(self.ref,meta['vectors'],meta['block_size'])
        began=time.perf_counter_ns();rebuilt=m.gm.reconstruct(meta['coefficients'],prediction,meta['qmap'],720,480)
        reconstruction_ms=(time.perf_counter_ns()-began)/1e6
        if m.C.reference_tag(rebuilt)!=meta['base_tag']:raise ValueError('GS38 pre-normalization reconstruction tag')
        began=time.perf_counter_ns();normalized=h.f.f.normalize(rebuilt);normalization_ms=(time.perf_counter_ns()-began)/1e6
        if m.C.reference_tag(normalized)!=meta['output_tag']:raise ValueError('CS38 normalized output tag')
        began=time.perf_counter_ns();patches,_=h.f.f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,
            expected_reference_id=None if key else self.rid)
        owned=[]
        for patch in patches:
            words=patch['words'].copy();words.setflags(write=False);owned.append(dict(patch,words=words))
        hud_ms=(time.perf_counter_ns()-began)/1e6
        for plane in normalized:plane.setflags(write=False)
        patches=tuple(owned)
        meta['decode_work'].update(reconstruction_ms=reconstruction_ms,normalization_ms=normalization_ms,hud_decode_and_copy_ms=hud_ms,
            output_reconstructions=1,normalization_passes=1,pre_norm_tag_checked=True,outer_tag_checked=True,
            HUD_validated_before_publication=True,receive_ms=(time.perf_counter_ns()-start)/1e6,
            normalized_array_bytes=sum(p.nbytes for p in normalized),owned_HUD_array_bytes=sum(p['words'].nbytes for p in patches))
        # No state is changed until all entropy, both output tags and HUD pass.
        self.ref,self.rid,self.hud,self.last=normalized,fid,patches,fid
        return normalized,patches,meta,meta['binary_planes']
