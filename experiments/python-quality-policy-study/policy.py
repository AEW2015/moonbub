"""Bounded causal quality ladder with acknowledged-success restoration.

Quantizer scale is inverse quality: 8 is finest, 32 coarsest. No visual quality
floor is inferred from this number; the declared maximum is only a syntax/policy
bound. Decisions use past actual packet sizes/ACK ages and current/previous
source thumbnails, never future frame data or future reconstruction error.
"""
from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class PolicyConfig:
    mode: str = 'restore'
    ladder: tuple[int, ...] = (8, 16, 32)
    successes_required: int = 4
    cooldown_frames: int = 6
    headroom_fraction: float = .5
    success_age_ms: float = 80
    cut_threshold: float = .20
    cut_cooldown_frames: int = 10


class QualityPolicy:
    def __init__(self, config=None):
        self.config = config or PolicyConfig()
        c = self.config
        if c.mode not in ('fixed', 'backoff', 'restore'):
            raise ValueError('unknown quality policy')
        if (not c.ladder or tuple(sorted(set(c.ladder))) != c.ladder
                or any(type(q) is not int or not 1 <= q <= 32 for q in c.ladder)):
            raise ValueError('quality ladder must increase and stay within1..32')
        if (type(c.successes_required) is not int or c.successes_required < 1
                or type(c.cooldown_frames) is not int or c.cooldown_frames < 0
                or type(c.cut_cooldown_frames) is not int or c.cut_cooldown_frames < 0
                or not math.isfinite(c.headroom_fraction) or not 0 < c.headroom_fraction < 1
                or not math.isfinite(c.success_age_ms) or c.success_age_ms < 0
                or not math.isfinite(c.cut_threshold) or not 0 <= c.cut_threshold <= 1):
            raise ValueError('invalid hysteresis or cut parameters')
        self.position = 0
        self.successes = 0
        self.last_change = -c.cooldown_frames
        self.last_cut = -c.cut_cooldown_frames
        self.previous_thumb = None
        self.last_capture = -1
        self.events = []

    @property
    def scale(self):
        return self.config.ladder[self.position]

    def observe_capture(self, rgb, frame_id):
        a = np.asarray(rgb)
        if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3 or frame_id <= self.last_capture:
            raise ValueError('capture must be ordered RGBuint8')
        sample = a[::8, ::8].astype(np.int32)
        thumb = (77*sample[...,0]+150*sample[...,1]+29*sample[...,2]+128)>>8
        score = None if self.previous_thumb is None or self.previous_thumb.shape != thumb.shape else float(
            np.abs(thumb-self.previous_thumb).mean()/255)
        cut = (score is not None and self.config.cut_threshold > 0 and score >= self.config.cut_threshold
               and frame_id-self.last_cut >= self.config.cut_cooldown_frames)
        self.previous_thumb = thumb
        self.last_capture = frame_id
        if cut:
            self.last_cut = frame_id
            self.successes = 0
            self.events.append({'kind':'scene_cut','id':frame_id,'score':score,'scale':self.scale})
        return cut

    def cap_failure(self, frame_id, used_scale):
        self.successes = 0
        # An old encoded frame must not change a newer policy decision.
        if self.config.mode == 'fixed' or used_scale != self.scale:
            return False
        old = self.scale
        self.position = min(self.position+1, len(self.config.ladder)-1)
        self.last_change = frame_id
        if self.scale != old:
            self.events.append({'kind':'backoff','id':frame_id,'old_scale':old,'scale':self.scale})
            return True
        return False

    def acknowledged(self, frame_id, used_scale, packet_bytes, cap, age_ms):
        if not math.isfinite(age_ms) or age_ms < 0 or not 0 < packet_bytes <= cap:
            raise ValueError('invalid successful ACK observation')
        c = self.config
        if c.mode != 'restore' or used_scale != self.scale or self.position == 0 or frame_id <= self.last_change:
            return False
        if packet_bytes > cap*c.headroom_fraction or age_ms > c.success_age_ms:
            self.successes = 0
            return False
        self.successes += 1
        if self.successes < c.successes_required or frame_id-self.last_change < c.cooldown_frames:
            return False
        old = self.scale
        self.position -= 1
        self.last_change = frame_id
        self.successes = 0
        self.events.append({'kind':'restore','id':frame_id,'old_scale':old,'scale':self.scale})
        return True
