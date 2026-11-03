"""Actual mixed HG01/GM01 adapter for GF02 and outer-content-bound GA01."""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
for folder in ('python-game-hybrid-study','python-game-rate-study','python-game-size-study','python-game-feedback-study'):
    sys.path.insert(0,str(HERE.parent/folder))
import hybrid_codec as hybrid
import controller as normal
import cheap_gate
import transport


@dataclass(frozen=True)
class Decision:
    packet:bytes|None
    selected:str|None
    attempts:tuple
    analyze_calls:int
    forward_calls:int
    service_ms:float
    commit_ms:float
    map_build_ms:float
    selected_scale_counts:dict|None
    identity:dict|None
    hybrid:dict
    oracle_excluded:bool=True

    @property
    def accepted(self):return self.packet is not None


class DecoderState:
    """Proxy semantic GM state so offline publication can wait for read finish."""
    def __init__(self,epoch=1,frame_cap=49152):self.impl=hybrid.Decoder(epoch,frame_cap)
    @property
    def base(self):return self.impl.base
    @property
    def anchor_id(self):return self.base.anchor_id
    @anchor_id.setter
    def anchor_id(self,value):self.base.anchor_id=value
    @property
    def _anchor(self):return self.base._anchor
    @_anchor.setter
    def _anchor(self,value):self.base._anchor=value
    @property
    def last_frame_id(self):return self.base.last_frame_id
    @last_frame_id.setter
    def last_frame_id(self,value):self.base.last_frame_id=value
    def receive(self,packet):return self.impl.receive(packet)


def identity(packet,epoch=1,frame_cap=49152):
    return hybrid.base_identity(packet,epoch,frame_cap)


def make_controller(*,patch_policy='adaptive_row',rectangles=hybrid.COMPACT,max_attempts=4,
                    work_budget_ms=None,use_gate=True):
    class Controller:
        def __init__(self,config=None):
            self.base=(cheap_gate.Controller if use_gate else normal.Controller)(config=config)
            self.encoder=self.base.encoder
            self.config=config or self.base.config
            self._oracle_packets={}
        def prepare(self,rgb,frame_id,*,force_key=False):
            began=time.perf_counter_ns()
            base=self.base.prepare(rgb,frame_id,force_key=force_key)
            if not base.accepted:
                return Decision(None,base.selected,base.attempts,base.analyze_calls,base.forward_calls,
                    (time.perf_counter_ns()-began)/1e6,base.commit_ms,base.map_build_ms,
                    base.selected_scale_counts,None,{'base_rejected':True})
            prior=(time.perf_counter_ns()-began)/1e6
            d=hybrid.select_frame(base.packet,rgb,hybrid.Config(frame_cap=self.config.frame_cap,
                rectangles=rectangles,patch_policy=patch_policy,max_attempts=max_attempts,
                work_budget_ms=work_budget_ms),spent_before_ms=prior)
            if not d.accepted:
                # Same base cap was enforced before GM commit. A differing cap
                # would need rollback/drain handling, not silent row removal.
                raise AssertionError('selected base unexpectedly rejected')
            self._oracle_packets[frame_id]=d.packet
            details={'base_packet_bytes':len(base.packet),'base_packet_sha256':hashlib.sha256(base.packet).hexdigest(),
                'format':d.format,'reason':d.reason,'selected_pixels':d.selected_pixels,
                'requested_pixels':d.requested_pixels,'selected':d.selected,'attempts':d.attempts,
                'selector_ms':d.service_ms,'selector_deadline_hit':d.deadline_hit,
                'preflight_ms':d.preflight_ms,'wrapper_assembly_ms':d.assembly_ms,'patch_policy':patch_policy}
            return Decision(d.packet,base.selected,base.attempts,base.analyze_calls,base.forward_calls,
                (time.perf_counter_ns()-began)/1e6,base.commit_ms,base.map_build_ms,
                base.selected_scale_counts,d.identity,details)
        def expected_hashes(self,frame_id):
            # Verification-only reconstruction; model calls after service timer.
            # State is cloned, never taken from patched display pixels.
            packet=self._oracle_packets.pop(frame_id)
            rx=hybrid.Decoder(frame_cap=self.config.frame_cap)
            rx.base.anchor_id,rx.base._anchor=self.encoder.anchor_id,self.encoder._anchor
            rgb,info=rx.receive(packet)
            return hashlib.sha256(rgb.tobytes()).hexdigest(),info['base_rgb_sha256']
    return Controller


def receive_complete(ingress,complete,decoder,frame_cap=49152):
    """Immediate functional completion; finite scheduler separately pays service."""
    ingress._owned(complete)
    try:
        meta=identity(complete.data,ingress.epoch,frame_cap)
        if (meta['epoch'],meta['frame_id'])!=(complete.epoch,complete.frame):
            raise ValueError('outer/inner frame identity mismatch')
        if complete.frame_crc!=transport.content_crc(complete.data):
            raise ValueError('outer body content mismatch')
        if complete.frame<=ingress.committed:raise ValueError('stale decode completion')
        rgb,info=decoder.receive(complete.data)
    except ValueError as error:
        ingress.reject(complete)
        feedback=transport.feedback_datagram(complete.epoch,complete.frame,status=transport.NACK,
                                            frame_crc=complete.frame_crc,reason=4)
        return None,None,feedback,str(error)
    ingress.commit(complete)
    return rgb,info,transport.feedback_datagram(complete.epoch,complete.frame,
                                               frame_crc=complete.frame_crc),None
