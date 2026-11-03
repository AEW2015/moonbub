"""Causal bounded HP01 selection with exact GM01 fallback.

The caller supplies the base bytes and RGB from the same capture. Selection uses
actual packet sizes and observed work only; no future or quality-error oracle.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-hud-study'))
import hud_codec as hud

BROAD=((16,48,192,80),(160,352,400,80))
COMPACT=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
MAX_FRAME=49152


@dataclass(frozen=True)
class Config:
    frame_cap:int=MAX_FRAME
    rectangles:tuple=COMPACT
    max_attempts:int=4
    work_budget_ms:float|None=None

    def __post_init__(self):
        if type(self.frame_cap) is not int or not 1<=self.frame_cap<=MAX_FRAME:
            raise ValueError('positive negotiated frame cap up to49152 required')
        if not isinstance(self.rectangles,tuple) or len(self.rectangles)>hud.MAX_PATCHES or any(not isinstance(r,tuple) for r in self.rectangles):
            raise ValueError('immutable bounded rectangle tuples required')
        if type(self.max_attempts) is not int or not 0<=self.max_attempts<=hud.MAX_PATCHES:
            raise ValueError('bounded patch attempts required')
        if self.work_budget_ms is not None and (not math.isfinite(self.work_budget_ms) or self.work_budget_ms<0):
            raise ValueError('nonnegative observed work budget required')


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
    base_validation_ms:float
    assembly_ms:float
    wrapper_bytes_built:int
    deadline_hit:bool
    unattempted_rectangles:int
    base_epoch:int
    base_frame_id:int

    @property
    def accepted(self):return self.packet is not None


def _assemble(base,validated,w,h):
    # All bytes came from this call's encoder and frozen HP01 decoder. Reuse
    # the bytes; do not call encode_patch a second time during wrapping.
    pieces=b''.join(hud.LENGTH.pack(len(packet))+packet for packet,_ in validated)
    body=hud.FRAME.pack(b'GH01',1,len(validated),len(base),w,h,len(pieces))+base+pieces
    return hud._crc(body)


def select_frame(base,rgb,config=None,*,spent_before_ms=0.0,
                 clock_ns=time.perf_counter_ns,patch_encoder=hud.encode_patch):
    cfg=config or Config()
    if not math.isfinite(spent_before_ms) or spent_before_ms<0:
        raise ValueError('observed prior work must be nonnegative')
    started=clock_ns()
    def elapsed():
        value=(clock_ns()-started)/1e6
        if not math.isfinite(value) or value<0:raise ValueError('nonmonotonic work clock')
        return value
    def expired():
        return cfg.work_budget_ms is not None and spent_before_ms+elapsed()>=cfg.work_budget_ms
    a=hud.gm.ft._check_rgb(rgb);h,w=a.shape[:2]
    rects=[hud._rect(r,w,h) for r in cfg.rectangles];hud._disjoint(rects)
    requested=sum(r[2]*r[3] for r in rects)
    if type(base) is not bytes or len(base)<hud.gm.HEADER.size+4:raise ValueError('complete GM01 base required')
    fields=hud.gm.HEADER.unpack_from(base)
    parsed=hud.gm.parse(base,fields[3])
    if (parsed['width'],parsed['height'])!=(w,h):raise ValueError('base/source canvas mismatch')
    epoch,frame=parsed['epoch'],parsed['frame_id'];del parsed
    validation_ms=elapsed()
    attempts=[];selected=[];deadline=False;assembly_ms=0.0;built=0
    if len(base)>cfg.frame_cap:
        service=elapsed()
        return Decision(None,None,'base_over_cap',(),(),requested,0,service,float(spent_before_ms),
                        spent_before_ms+service,validation_ms,0.0,0,False,len(rects),epoch,frame)
    reason='no_patch_fits'
    for index,rect in enumerate(rects):
        if len(attempts)>=cfg.max_attempts:
            reason='attempt_limit';break
        if expired():deadline=True;reason='work_budget';break
        began=clock_ns();patch=patch_encoder(a,rect);encoded_ms=(clock_ns()-began)/1e6
        if encoded_ms<0 or not math.isfinite(encoded_ms):raise ValueError('invalid encoding clock')
        began=clock_ns();meta=hud.decode_patch(patch,w,h);validate_ms=(clock_ns()-began)/1e6
        if tuple(meta['rect'])!=rect:raise ValueError('patch encoder changed requested rectangle')
        projected=hud.FRAME.size+4+len(base)+sum(4+len(p) for p,_ in selected)+4+len(patch)
        fits=projected<=cfg.frame_cap
        row={'priority_index':index,'rect':rect,'pixels':rect[2]*rect[3],
             'patch_bytes':len(patch),'mode':meta['mode'],'palette_colors':meta['colors'],
             'encode_ms':encoded_ms,'validate_ms':validate_ms,'projected_wrapper_bytes':projected,
             'fits':fits,'selected_in_output':False}
        attempts.append(row)
        if expired():deadline=True;reason='work_budget';break
        if fits:
            selected.append((patch,{**{k:v for k,v in meta.items() if k!='words'},'priority_index':index}))
    packet=base;fmt='GM01';output=[]
    if selected and not deadline:
        began=clock_ns();candidate=_assemble(base,selected,w,h);assembly_ms=(clock_ns()-began)/1e6
        built=len(candidate)
        if expired():deadline=True;reason='work_budget'
        else:
            assert len(candidate)<=cfg.frame_cap
            packet=candidate;fmt='GH01';reason='patched';output=[meta for _,meta in selected]
    if not deadline and fmt=='GM01' and not attempts and not rects:reason='no_priorities'
    kept={m['priority_index'] for m in output}
    for row in attempts:row['selected_in_output']=row['priority_index'] in kept
    service=elapsed()
    return Decision(packet,fmt,reason,tuple(attempts),tuple(output),requested,
                    sum(m['rect'][2]*m['rect'][3] for m in output),service,float(spent_before_ms),
                    spent_before_ms+service,validation_ms,assembly_ms,built,deadline,len(rects)-len(attempts),epoch,frame)


class Decoder:
    """GM01 fallback and GH01 selection share the exact same GM01 predictor."""
    def __init__(self,epoch=1,frame_cap=MAX_FRAME):
        self.frame_cap=Config(frame_cap=frame_cap).frame_cap
        self._hud=hud.Receiver(epoch)

    @property
    def base(self):return self._hud.base

    def receive(self,packet):
        if type(packet) is not bytes:raise ValueError('immutable selective packet required')
        if len(packet)>self.frame_cap:raise ValueError('selective frame over negotiated cap')
        if packet[:4]==b'GH01':
            rgb,info=self._hud.receive(packet);return rgb,{**info,'selected_format':'GH01'}
        if packet[:4]==b'GM01':
            rgb,info=self.base.receive(packet)
            return rgb,{**info,'selected_format':'GM01','base_rgb_sha256':hud.hashlib.sha256(rgb.tobytes()).hexdigest(),'patches':[]}
        raise ValueError('unsupported selective codec')
