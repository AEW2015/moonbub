"""CN36 canonical hidden references; a NEW research wire contract.

GM27 inner packets retain their own pre-normalization tags. CN36 authenticates
both the normalized input reference and normalized committed output. Full and
skip variants must use the same prediction, qmap and visible coefficients.
"""
import hashlib,json,struct,zlib,time,importlib.util,sys
from pathlib import Path
import numpy as np
_spec=importlib.util.spec_from_file_location('canonical36_model_helpers',Path(__file__).with_name('helpers.py'))
h=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=h;_spec.loader.exec_module(h)
HEADER=struct.Struct('<4sBBHIIHH16s16s16sII')
MAGIC=b'CN36';VERSION=1;EPOCH=25;CAP=49152
RECTS=h.n.RECTS
PROFILE=hashlib.sha256(json.dumps(RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def normalize(planes):return h.mask.mask_source(planes,RECTS,policy='core8')
def hidden_blocks(width=720,height=480):
    zeros=tuple(np.zeros(shape,np.int16) for shape in ((height,width),(height//2,width//2),(height//2,width//2)))
    masked=normalize(zeros);result=[]
    for plane in masked:
        ph,pw=plane.shape;bh,bw=(ph+7)//8,(pw+7)//8
        padded=np.pad(plane,((0,bh*8-ph),(0,bw*8-pw)),constant_values=0)
        result.append(np.all(padded.reshape(bh,8,bw,8).transpose(0,2,1,3).reshape(-1,8,8)==128,axis=(1,2)))
    return tuple(result)
HIDDEN=hidden_blocks()

def zero_hidden(coefficients):
    if len(coefficients)!=3 or any(c.shape!=(len(mask),8,8) for c,mask in zip(coefficients,HIDDEN,strict=True)):
        raise ValueError('fixed CN36 coefficient geometry')
    output=tuple(c.copy() for c in coefficients)
    for c,mask in zip(output,HIDDEN,strict=True):c[mask]=0
    return output

def skip_inner(packet,prediction):
    """Serialize real omitted hidden residuals, preserving every visible value.

    This proof path starts with a paid complete frozen encode, then reparses it.
    Its entropy/rebuild work is additional; no complete sender speedup claimed.
    """
    start=time.perf_counter_ns();meta=h.m.parse(packet,expected_epoch=EPOCH)
    coefficients=zero_hidden(meta['coefficients']);payloads=[]
    removed=sum(int(np.count_nonzero(a)-np.count_nonzero(b)) for a,b in zip(meta['coefficients'],coefficients,strict=True))
    for axis,c in enumerate(coefficients):
        bw=((meta['width'] if axis==0 else meta['width']//2)+7)//8
        plan=h.entropy._plane_plan(c,bw,h.m);data,*_=h.entropy._construct(c,bw,plan,h.m)
        assert len(data)==plan['bytes'];payloads.append(data)
    rebuilt=h.m.gm.reconstruct(coefficients,prediction,meta['scale_map'],meta['width'],meta['height'])
    fields=list(h.m.HEADER.unpack_from(packet));fields[11]=h.m.C.reference_tag(rebuilt)
    fields[14:17]=map(len,payloads)
    pos=h.m.HEADER.size;maps=packet[pos:pos+meta['qmap_bytes']+meta['vector_bytes']]
    result=seal(h.m.HEADER.pack(*fields)+maps+b''.join(payloads))
    h.m.parse_metadata(result,expected_epoch=EPOCH)
    return result,rebuilt,dict(removed_nonzero_coefficients=removed,zeroed_block_counts=[int(v.sum()) for v in HIDDEN],
        proof_reparse_entropy_rebuild_ms=(time.perf_counter_ns()-start)/1e6)

def wrap(inner,hud,normalized,*,skip):
    if type(skip)is not bool:raise ValueError('CN36 skip flag')
    meta=h.m.parse_metadata(inner,expected_epoch=EPOCH)
    flags=int(meta['key'])|2*int(skip)
    body=HEADER.pack(MAGIC,VERSION,flags,EPOCH,meta['frame_id'],meta['reference_id'],meta['width'],meta['height'],
        PROFILE,meta['reference_tag'],h.m.C.reference_tag(normalized),len(inner),len(hud))+inner+hud
    return seal(body)

def parse(packet):
    if type(packet)is not bytes or not HEADER.size+12<=len(packet)<=CAP:raise ValueError('CN36 bounded immutable packet')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('CN36 CRC')
    magic,version,flags,epoch,fid,rid,w,hh,profile,reftag,outtag,nb,nh=HEADER.unpack_from(packet)
    if magic!=MAGIC or version!=VERSION or flags not in (0,1,2,3) or epoch!=EPOCH or (w,hh)!=(720,480) or profile!=PROFILE:
        raise ValueError('CN36 exact fixed profile')
    if min(nb,nh)<=0 or len(packet)!=HEADER.size+nb+nh+4:raise ValueError('CN36 exact lengths')
    inner,hud=packet[HEADER.size:HEADER.size+nb],packet[HEADER.size+nb:-4]
    bm=h.m.parse_metadata(inner,expected_epoch=epoch);hm=h.p.parse_hud(hud)
    if (bm['frame_id'],bm['reference_id'],bm['key'],bm['width'],bm['height'],bm['reference_tag'])!=(fid,rid,bool(flags&1),w,hh,reftag):
        raise ValueError('CN36 inner identity')
    if (hm['epoch'],hm['frame_id'],hm['reference_id'],hm['width'],hm['height'])!=(epoch,fid,rid,w,hh):raise ValueError('CN36 HUD identity')
    if tuple(hm['rectangles'])!=RECTS:raise ValueError('CN36 exact opaque rectangle profile')
    if outtag==bytes(16):raise ValueError('CN36 normalized output tag')
    return dict(frame_id=fid,reference_id=rid,key=bool(flags&1),skip=bool(flags&2),reference_tag=reftag,
        normalized_tag=outtag,inner=inner,hud=hud,base_meta=bm)

class Receiver:
    def __init__(self):self.ref=None;self.rid=h.m.NO_REF;self.hud=();self.last=-1
    def receive(self,packet):
        meta=parse(packet);key=meta['key']
        if meta['frame_id']<=self.last:raise ValueError('CN36 monotonic ID')
        if not key and (self.ref is None or self.rid!=meta['reference_id'] or h.m.C.reference_tag(self.ref)!=meta['reference_tag']):raise ValueError('CN36 committed normalized reference')
        pixels,_=h.m.decode(meta['inner'],None if key else self.ref,expected_epoch=EPOCH,expected_reference_id=None if key else self.rid)
        parts,_=h.p.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=EPOCH,expected_reference_id=None if key else self.rid)
        if meta['skip'] and any(np.any(c[mask]) for c,mask in zip(h.m.parse(meta['inner'])['coefficients'],HIDDEN,strict=True)):raise ValueError('CN36 omitted hidden residual grammar')
        pixels=normalize(pixels)
        if h.m.C.reference_tag(pixels)!=meta['normalized_tag']:raise ValueError('CN36 normalized output binding')
        # Stage complete before modeled atomic state publication; no hardware fence claim.
        self.ref,self.rid,self.hud,self.last=pixels,meta['frame_id'],parts,meta['frame_id']
        return pixels,parts
