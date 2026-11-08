"""Causal mandatory-HUD AR03 construction; payload syntax is unchanged.

Full exact display-patch bytes are prepared before bounded base-map choices.
Losing AR03 builds are paid and discarded before identity/publication commit.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-candidate-commit-study'))
import candidate_codec as codec
ui=codec._ui()
RECTANGLES=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
BASE_REGIONS=((16,48,192,80),(160,352,400,80))
PROFILES=((8,16),(8,32),(16,32),(32,32))

def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def state(e):
    return dict(last_issued=e.last_issued,generation=e._generation,geometry=e._geometry,pending=sorted(e.pending),
        banks={str(s):None if b is None else dict(id=b.frame_id,tag=b.tag.hex()) for s,b in e.banks.items()})
def measured(fn):
    start=time.perf_counter_ns();value=fn();return value,(time.perf_counter_ns()-start)/1e6

class MandatoryPatches:
    """Prepares every requested patch; complete outer cap remains authoritative."""
    def __init__(self,rectangles=RECTANGLES):
        self.rectangles=rectangles;self.selector=ui.PatchSelector(rectangles=rectangles);self.selection=None
    def prepare(self,rgb):
        # The safe codec upper bound is independent of actual compression ratio.
        selection=self.selector.select(rgb,3*rgb.shape[0]*rgb.shape[1]+16384)
        if len(selection.patches)!=len(self.rectangles) or selection.selected_pixels!=selection.requested_pixels or selection.deadline_hit:
            raise ValueError('mandatory patch preparation incomplete')
        self.selection=selection
        return selection
    def select(self,rgb,byte_budget):
        if self.selection is None:raise ValueError('mandatory patches must be prepared before base')
        selected=self.selection
        # Full patch validation against the actual current RGB source is repeated
        # by candidate_codec.build. Returning over-budget patches is intentional:
        # its complete outer-cap guard rejects the entire candidate atomically.
        details=dict(selected.details,byte_budget=byte_budget,mandatory=True,reserved_bytes=selected.used_bytes,
            reservation_fits=selected.used_bytes<=byte_budget)
        return ui.Selection(selected.patches,details,selected.used_bytes,0.0,selected.selected_pixels,selected.requested_pixels,False)

@dataclass(frozen=True)
class Prepared:
    candidate:object|None
    info:dict
    @property
    def accepted(self):return self.candidate is not None

class Policy:
    def __init__(self,*,rectangles=RECTANGLES,base_regions=BASE_REGIONS,profiles=PROFILES,frame_cap=49152,mode='gm'):
        if (type(profiles)is not tuple or not 1<=len(profiles)<=4 or
            any(type(p)is not tuple or len(p)!=2 or any(type(x)is not int or x not in codec.gm.roi.SCALES for x in p) for p in profiles)):
            raise ValueError('one to four declared legal base-map profiles')
        self.patches=MandatoryPatches(rectangles);self.encoder=codec.Encoder(frame_cap=frame_cap,mode=mode,patch_builder=self.patches)
        self.rectangles,self.base_regions,self.profiles=rectangles,base_regions,profiles
    def prepare(self,rgb,frame_id,**kwargs):
        if self.encoder.active_candidate is not None:raise ValueError('unresolved mandatory candidate')
        before=state(self.encoder);readers_before=self.encoder.readers;leases_before=set(self.encoder._leases)
        selection,patch_ms=measured(lambda:self.patches.prepare(rgb))
        reserve=selection.used_bytes;budget=self.encoder.frame_cap-(codec.HEADER.size+4)-reserve
        attempts=[];chosen=None;reason='all_declared_maps_exceed_complete_cap'
        try:
            if budget<codec.gm.HEADER.size+4:reason='mandatory_ui_exceeds_complete_cap'
            else:
                h,w=rgb.shape[:2]
                for index,(roi,bg) in enumerate(self.profiles):
                    mapped,map_ms=measured(lambda:codec.gm.roi.declared_map(w,h,self.base_regions,roi,bg))
                    c,build_ms=measured(lambda:self.encoder.build(rgb,frame_id,scale_map=mapped,**kwargs))
                    info=codec.plain_info(c)
                    full=len(info['selected'])==len(self.rectangles) and info['selected_pixels']==selection.requested_pixels
                    accepted=c.accepted and full and info['inner_bytes']<=budget
                    attempt=dict(index=index,roi_scale=roi,background_scale=bg,map_ms=map_ms,build_ms=build_ms,
                        candidate_build_internal_ms=c.service_ms,inner_bytes=info['inner_bytes'],
                        attempted_complete_bytes=codec.HEADER.size+4+info['inner_bytes']+reserve,
                        built_packet_bytes=info['bytes'],candidate_accepted=c.accepted,full_mandatory_patches=full,
                        accepted=accepted,analyze_calls=info['analyze_calls'],forward_calls=info['forward_calls'],
                        source_readers_during=self.encoder.readers,discard_ms=0.)
                    attempts.append(attempt)
                    if state(self.encoder)!=before:raise AssertionError('candidate build changed semantic state')
                    if accepted:chosen=c;reason='mandatory_complete';break
                    _,attempt['discard_ms']=measured(lambda:self.encoder.discard(c))
                    if (state(self.encoder)!=before or self.encoder.readers!=readers_before or set(self.encoder._leases)!=leases_before):
                        raise AssertionError('discard changed semantic state/external leases')
            return Prepared(chosen,dict(frame_id=frame_id,reason=reason,state_before=before,state_after_builds=state(self.encoder),
                readers_before=readers_before,readers_after_builds=self.encoder.readers,
                mandatory_patch_bytes=reserve,reserved_inner_bytes=budget,requested_rectangles=self.rectangles,
                requested_pixels=selection.requested_pixels,patch_prepare_ms=patch_ms,patch_details=selection.details,
                attempts=attempts,selected_profile=None if chosen is None else list(self.profiles[len(attempts)-1]),
                complete_bytes=None if chosen is None else len(chosen.packet),
                paid_service_ms=patch_ms+sum(x['map_ms']+x['build_ms']+x['discard_ms'] for x in attempts)))
        except BaseException:
            if self.encoder.active_candidate is not None:self.encoder.discard(self.encoder.active_candidate)
            if self.encoder.readers!=readers_before or set(self.encoder._leases)!=leases_before:
                raise AssertionError('exception changed external leases')
            raise
        finally:self.patches.selection=None
    def commit(self,prepared):
        if not isinstance(prepared,Prepared) or prepared.candidate is None:raise ValueError('no mandatory candidate')
        return self.encoder.commit(prepared.candidate)
    def discard(self,prepared):
        if not isinstance(prepared,Prepared) or prepared.candidate is None:raise ValueError('no mandatory candidate')
        return self.encoder.discard(prepared.candidate)
