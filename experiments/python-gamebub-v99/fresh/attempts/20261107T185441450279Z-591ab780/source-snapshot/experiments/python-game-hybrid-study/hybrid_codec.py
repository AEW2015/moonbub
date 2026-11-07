"""Bounded HG01 HP01/HR01 selective display overlays over frozen temporal GM01.

No entropy decode in sender preflight. The receiver fully validates patch syntax
before its atomic GM01 decode. Patches never enter the YUV reference state.
"""
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import struct
import sys
import time
import zlib

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-row-study'))
import row_codec as row
hp=row.hp
gm=hp.gm
MAX_FRAME=49152
BROAD=((16,48,192,80),(160,352,400,80))
COMPACT=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))


@dataclass(frozen=True)
class Config:
    frame_cap:int=MAX_FRAME
    rectangles:tuple=COMPACT
    patch_policy:str='adaptive_row'
    max_attempts:int=4
    work_budget_ms:float|None=None

    def __post_init__(self):
        if type(self.frame_cap) is not int or not 1<=self.frame_cap<=MAX_FRAME:raise ValueError('hybrid negotiated frame cap')
        if type(self.rectangles) is not tuple or len(self.rectangles)>4 or any(type(r) is not tuple for r in self.rectangles):
            raise ValueError('bounded immutable declared priorities')
        if self.patch_policy not in ('hp01','adaptive_row'):raise ValueError('hybrid patch policy')
        if type(self.max_attempts) is not int or not 0<=self.max_attempts<=4:raise ValueError('bounded hybrid attempts')
        if self.work_budget_ms is not None and (not math.isfinite(self.work_budget_ms) or self.work_budget_ms<0):
            raise ValueError('observed work budget')


@dataclass(frozen=True)
class Decision:
    packet:bytes|None
    format:str|None
    reason:str
    attempts:tuple
    selected:tuple
    requested_pixels:int
    selected_pixels:int
    service_ms:float
    spent_before_ms:float
    observed_total_ms:float
    preflight_ms:float
    assembly_ms:float
    wrapper_bytes_built:int
    deadline_hit:bool
    unattempted_rectangles:int
    identity:dict

    @property
    def accepted(self):return self.packet is not None


def _preflight_base(packet,epoch=None):
    """Bounded header/map/length/whole-CRC checks, NOT coefficient validation."""
    if type(packet) is not bytes or len(packet)<gm.HEADER.size+4:raise ValueError('complete immutable GM01 base')
    fields=gm.HEADER.unpack_from(packet)
    magic,version,key,session,frame,ref,w,h,dx,dy,mw,mh,nmap,ny,ncb,ncr=fields
    expected=gm.roi.geometry(w,h)
    if (magic!=gm.MAGIC or version!=1 or key not in (0,1) or session==gm.NO_REF
        or (epoch is not None and session!=epoch) or frame==gm.NO_REF or (mw,mh)!=expected
        or dx%2 or dy%2 or abs(dx)>gm.mt.MV_LIMIT or abs(dy)>gm.mt.MV_LIMIT
        or bool(key)!=(ref==gm.NO_REF) or (key and (dx or dy)) or (not key and ref>=frame)):
        raise ValueError('GM01 preflight identity/geometry')
    if nmap!=(mw*mh+3)//4:raise ValueError('GM01 preflight map length')
    for n,(pw,ph) in zip((ny,ncb,ncr),((w,h),(w//2,h//2),(w//2,h//2))):
        blocks=((pw+7)//8)*((ph+7)//8)
        if not gm.word_coeff.PAYLOAD_OVERHEAD<=n<=128*blocks+gm.word_coeff.PAYLOAD_OVERHEAD:
            raise ValueError('GM01 preflight plane length')
    if len(packet)!=gm.HEADER.size+nmap+ny+ncb+ncr+4:raise ValueError('GM01 preflight exact length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('GM01 preflight CRC')
    gm.roi.unpack_map(packet[gm.HEADER.size:gm.HEADER.size+nmap],mw,mh)
    return {'epoch':session,'frame_id':frame,'key':bool(key),'reference_id':None if key else ref,
            'width':w,'height':h,'base_bytes':len(packet),'dx':dx,'dy':dy}


def _envelope(packet,epoch,cap):
    if type(packet) is not bytes or len(packet)>cap:raise ValueError('hybrid negotiated packet cap/type')
    if packet[:4]==b'GM01':return packet,[],_preflight_base(packet,epoch)
    if len(packet)<row.FRAME.size+4:raise ValueError('HG01 truncated frame')
    magic,version,count,nbase,w,h,npatch=row.FRAME.unpack_from(packet)
    gm.roi.geometry(w,h)
    if (magic!=b'HG01' or version!=1 or count>4 or not gm.HEADER.size+4<=nbase<=hp._base_bound(w,h)
        or len(packet)!=row.FRAME.size+4+nbase+npatch
        or npatch>3*w*h+4*(4+row.HEADER.size+4+512+2*h)):
        raise ValueError('HG01 envelope geometry/profile/length')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('HG01 envelope CRC')
    base=packet[row.FRAME.size:row.FRAME.size+nbase];identity=_preflight_base(base,epoch)
    if (identity['width'],identity['height'])!=(w,h):raise ValueError('HG01 base/envelope geometry')
    pos=row.FRAME.size+nbase;patches=[];rects=[]
    for _ in range(count):
        if pos+4>len(packet)-4:raise ValueError('HG01 missing patch length')
        length=struct.unpack_from('<I',packet,pos)[0];pos+=4
        if length<row.HEADER.size+4 or pos+length>len(packet)-4:raise ValueError('HG01 patch byte bound')
        p=packet[pos:pos+length];pos+=length
        if p[:4] not in (b'HP01',b'HR01'):raise ValueError('HG01 patch magic')
        rects.append(hp._rect(row.HEADER.unpack_from(p)[3:7],w,h));patches.append(p)
    if pos!=len(packet)-4:raise ValueError('HG01 trailing bytes')
    hp._disjoint(rects)
    return base,patches,identity


def base_identity(packet,epoch=None,frame_cap=MAX_FRAME):
    """Cheap GM/HG identity for transport ACK routing; not a decode certificate.

    Complete envelope/base CRC, header/map/bounds checked; HP/HR payload and GM
    entropy are NOT validated. Decoder.receive performs complete validation.
    """
    if type(frame_cap) is not int or not 1<=frame_cap<=MAX_FRAME:raise ValueError('hybrid identity frame cap')
    if epoch is not None and (type(epoch) is not int or not 0<=epoch<gm.NO_REF):raise ValueError('hybrid identity epoch')
    _,patches,identity=_envelope(packet,epoch,frame_cap)
    return {**identity,'format':packet[:4].decode(),'packet_bytes':len(packet),'patch_count':len(patches)}


def extract_base(packet,epoch=None,frame_cap=MAX_FRAME):
    """Return immutable base bytes and cheap identity; same partial-validation scope."""
    identity=base_identity(packet,epoch,frame_cap)
    base=packet if packet[:4]==b'GM01' else packet[row.FRAME.size:row.FRAME.size+identity['base_bytes']]
    return base,identity


def _encode_patch(rgb,rect,policy):
    if policy=='adaptive_row':return row.choose_patch(rgb,rect)
    packet=hp.encode_patch(rgb,rect)
    return packet,{'chosen_format':'HP01','chosen_bytes':len(packet),'candidate_count':1,
                   'attempts':[{'format':'HP01','bytes':len(packet)}]}


def select_frame(base,rgb,config=None,*,spent_before_ms=0.0,clock_ns=time.perf_counter_ns,patch_encoder=_encode_patch):
    cfg=config or Config()
    if not math.isfinite(spent_before_ms) or spent_before_ms<0:raise ValueError('prior work accounting')
    previous=started=clock_ns()
    def stamp():
        nonlocal previous
        value=clock_ns()
        if not math.isfinite(value) or value<previous:raise ValueError('nonmonotonic hybrid clock')
        previous=value;return value
    def elapsed():return (stamp()-started)/1e6
    def expired():return cfg.work_budget_ms is not None and spent_before_ms+elapsed()>=cfg.work_budget_ms
    a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
    rects=[hp._rect(r,w,h) for r in cfg.rectangles];hp._disjoint(rects)
    identity=_preflight_base(base)
    if (identity['width'],identity['height'])!=(w,h):raise ValueError('GM/source canvas mismatch')
    preflight=elapsed();requested=sum(r[2]*r[3] for r in rects)
    attempts=[];chosen=[];deadline=False;assembly=0.;built=0
    if len(base)>cfg.frame_cap:
        total=elapsed();return Decision(None,None,'base_over_cap',(),(),requested,0,total,spent_before_ms,spent_before_ms+total,
                                       preflight,0.,0,False,len(rects),identity)
    reason='no_patch_fits'
    for index,rect in enumerate(rects):
        if len(attempts)>=cfg.max_attempts:reason='attempt_limit';break
        if expired():deadline=True;reason='work_budget';break
        began=stamp();patch,details=patch_encoder(a,rect,cfg.patch_policy);encode_ms=(stamp()-began)/1e6
        began=stamp();meta=row.decode_any(patch,w,h);validate_ms=(stamp()-began)/1e6
        if tuple(meta['rect'])!=rect or (cfg.patch_policy=='hp01' and patch[:4]!=b'HP01'):
            raise ValueError('patch encoder changed contract')
        projected=row.FRAME.size+4+len(base)+sum(4+len(p) for p,_ in chosen)+4+len(patch)
        fits=projected<=cfg.frame_cap
        attempt={'priority_index':index,'rect':rect,'pixels':rect[2]*rect[3],'patch_bytes':len(patch),
                 'format':patch[:4].decode(),'mode':meta['mode'],'palette_colors':meta['colors'],
                 'candidate_details':details,'encode_ms':encode_ms,'validate_ms':validate_ms,
                 'projected_packet_bytes':projected,'fits':fits,'selected_in_output':False}
        attempts.append(attempt)
        if expired():deadline=True;reason='work_budget';break
        if fits:chosen.append((patch,{**{k:v for k,v in meta.items() if k!='words'},'format':patch[:4].decode(),'priority_index':index}))
    packet=base;fmt='GM01';output=[]
    if chosen and not deadline:
        began=stamp();candidate=row.wrap(base,[p for p,_ in chosen],w,h);assembly=(stamp()-began)/1e6;built=len(candidate)
        if expired():deadline=True;reason='work_budget'
        else:
            assert len(candidate)<=cfg.frame_cap
            packet=candidate;fmt='HG01';output=[meta for _,meta in chosen];reason='patched'
    if fmt=='GM01' and not rects:reason='no_priorities'
    kept={p['priority_index'] for p in output}
    for attempt in attempts:attempt['selected_in_output']=attempt['priority_index'] in kept
    total=elapsed()
    return Decision(packet,fmt,reason,tuple(attempts),tuple(output),requested,sum(p['rect'][2]*p['rect'][3] for p in output),
                    total,spent_before_ms,spent_before_ms+total,preflight,assembly,built,deadline,len(rects)-len(attempts),identity)


class Decoder:
    def __init__(self,epoch=1,frame_cap=MAX_FRAME):
        self.frame_cap=Config(frame_cap=frame_cap).frame_cap
        self.epoch=epoch;self.base=gm.Receiver(epoch)

    def receive(self,packet):
        if type(packet) is not bytes or len(packet)>self.frame_cap:raise ValueError('hybrid negotiated packet cap/type')
        # Raw GM has no patches to validate; atomic GM01 receive checks everything.
        if packet[:4]==b'GM01':
            rgb,info=self.base.receive(packet)
            return rgb,{**info,'format':'GM01','packet_bytes':len(packet),'patches':[],
                        'base_rgb_sha256':hashlib.sha256(rgb.tobytes()).hexdigest()}
        # Frozen HG01 parser fully validates every patch before one atomic base
        # entropy decode. It performs only base header/session/geometry preflight.
        base,patches,meta=row.parse_frame(packet,self.epoch)
        rgb,info=self.base.receive(base);base_hash=hashlib.sha256(rgb.tobytes()).hexdigest()
        words=hp.corpus.rgb565(rgb)
        for patch in patches:
            x,y,w,h=patch['rect'];words[y:y+h,x:x+w]=patch['words']
        return hp.corpus.expand565(words),{**info,'format':'HG01','packet_bytes':len(packet),
            'base_bytes':len(base),'patches':[{**{k:v for k,v in p.items() if k!='words'}} for p in patches],
            'base_rgb_sha256':base_hash}
