"""Bounded GM01 map controller: one normal candidate plus one fallback.

The candidate selector reads only current-frame packet lengths. ROI scales never
exceed8 in the priority policy. A failed admission does not call commit or
consume a frame/reference credit. Verification work is outside service timing.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
import time

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-codec-study'))
import game_codec as codec

RECTANGLES=((16,48,192,80),(160,352,400,80))


@dataclass(frozen=True)
class Config:
    frame_cap: int=49152
    policy: str='priority'
    rectangles: tuple=RECTANGLES
    motion_mode: str='zero'

    def __post_init__(self):
        if type(self.frame_cap) is not int or self.frame_cap<=0:
            raise ValueError('positive integer frame cap required')
        if self.policy not in ('priority','uniform') or self.motion_mode not in ('zero','global'):
            raise ValueError('unsupported policy/motion')
        if not isinstance(self.rectangles,tuple) or any(not isinstance(r,tuple) for r in self.rectangles):
            raise ValueError('immutable rectangle tuples required')


@dataclass(frozen=True)
class Decision:
    packet: bytes|None
    selected: str|None
    attempts: tuple
    analyze_calls: int
    forward_calls: int
    service_ms: float
    commit_ms: float
    map_build_ms: float
    selected_scale_counts: dict|None
    oracle_excluded: bool=True

    @property
    def accepted(self):return self.packet is not None


class Controller:
    def __init__(self,encoder=None,config=None):
        self.encoder=encoder or codec.Encoder()
        self.config=config or Config()

    def maps(self,rgb):
        a=codec.ft._check_rgb(rgb);h,w=a.shape[:2]
        mw,mh=codec.roi.geometry(w,h)
        if self.config.policy=='priority':
            return [('normal',codec.roi.declared_map(w,h,self.config.rectangles,8,16)),
                    ('fallback',codec.roi.declared_map(w,h,self.config.rectangles,8,32))]
        return [('normal',np.full((mh,mw),16,np.uint8)),
                ('fallback',np.full((mh,mw),32,np.uint8))]

    def prepare(self,rgb,frame_id,*,force_key=False,reuse=True):
        started=time.perf_counter_ns()
        began=started;maps=self.maps(rgb)
        map_ms=(time.perf_counter_ns()-began)/1e6
        analyze_calls=0;forward_calls=0;prepared=None;attempts=[]
        chosen=None;chosen_label=None;chosen_counts=None
        for label,scale_map in maps:
            analyze_ms=0.0
            if prepared is None or not reuse:
                begin=time.perf_counter_ns()
                prepared=self.encoder.analyze(rgb,frame_id,force_key=force_key,mode=self.config.motion_mode)
                analyze_ms=(time.perf_counter_ns()-begin)/1e6
                analyze_calls+=1;forward_calls+=prepared.forward_calls
            begin=time.perf_counter_ns()
            candidate=self.encoder.encode_candidate(prepared,scale_map)
            candidate_ms=(time.perf_counter_ns()-begin)/1e6
            size=len(candidate.packet)
            attempts.append({'label':label,'bytes':size,'fits':size<=self.config.frame_cap,
                             'analyze_ms':analyze_ms,'candidate_ms':candidate_ms,
                             'scale_counts':{str(s):int((scale_map==s).sum()) for s in (8,16,32)}})
            if size<=self.config.frame_cap:
                chosen=candidate;chosen_label=label;chosen_counts=attempts[-1]['scale_counts'];break
            # No discarded Candidate/packet is retained by the Decision. The
            # reusable Prepared remains only until this bounded call finishes.
            candidate=None
            if not reuse:prepared=None
        commit_ms=0.0;packet=None
        if chosen is not None:
            began=time.perf_counter_ns();packet=self.encoder.commit(chosen)
            commit_ms=(time.perf_counter_ns()-began)/1e6
            if packet!=chosen.packet:raise AssertionError('commit changed selected bytes')
        elapsed=(time.perf_counter_ns()-started)/1e6
        return Decision(packet,chosen_label,tuple(attempts),analyze_calls,forward_calls,
                        elapsed,commit_ms,map_ms,chosen_counts)
