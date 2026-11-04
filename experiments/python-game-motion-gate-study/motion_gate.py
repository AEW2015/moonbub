"""Causal four-corner luma screen before optional actual GM/BM rate choice.

The screen reads only the current RGB source and immutable ACKed reconstructed
key. It cannot inspect coded lengths, reconstructed candidate quality or future
frames. A positive screen enables both actual candidates; all work is charged.
RM01 syntax and canonical reference/credit implementation remain frozen v12.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-rate-motion-study'))
import rate_motion as r


@dataclass(frozen=True)
class Config:
    minimum_gain: float = 3.0
    minimum_relative_gain: float = .35
    minimum_moving_fraction: float = .25
    maximum_best_error: float = 24.0
    search_range: int = 4

    def __post_init__(self):
        values = (self.minimum_gain, self.minimum_relative_gain,
                  self.minimum_moving_fraction, self.maximum_best_error)
        if any(not np.isfinite(x) or x < 0 for x in values):
            raise ValueError('finite nonnegative screen thresholds required')
        if self.minimum_relative_gain > 1 or self.minimum_moving_fraction > 1:
            raise ValueError('screen fractions must be bounded')
        if type(self.search_range) is not int or self.search_range not in (4, 8):
            raise ValueError('bounded even-integer search required')


def screen(rgb, anchor, *, force_key=False, config=Config()):
    started = time.perf_counter_ns()
    a = r.gm.ft._check_rgb(rgb)
    h, w = a.shape[:2]
    reason = ('key' if force_key or anchor is None else
              'geometry_key' if anchor[0].shape != (h, w) else None)
    if reason:
        return dict(allow_block=False, reason=reason, samples=0, comparisons=0,
                    zero_mae=None, best_mae=None, gain=None, relative_gain=None,
                    moving_fraction=None, gate_ms=(time.perf_counter_ns()-started)/1e6)
    mw, mh = r.gm.roi.geometry(w, h)
    # Four corners deliberately sample block boundaries; interior-only samples
    # can miss small shifts of otherwise flat 16x16 texture blocks.
    by, bx = np.mgrid[:mh, :mw]
    yy = np.minimum(by[..., None]*16 + np.array([0, 0, 15, 15]), h-1)
    xx = np.minimum(bx[..., None]*16 + np.array([0, 15, 0, 15]), w-1)
    sampled = a[yy, xx].astype(np.int32)
    current = ((77*sampled[..., 0]+150*sampled[..., 1]+29*sampled[..., 2]+128)>>8).astype(np.int16)
    reference = anchor[0]
    vectors = sorted(((dx, dy) for dy in range(-config.search_range, config.search_range+1, 2)
                      for dx in range(-config.search_range, config.search_range+1, 2)),
                     key=lambda xy: (abs(xy[0])+abs(xy[1]), xy[1], xy[0]))
    best = np.full((mh, mw), 2**31-1, np.int64)
    zero = None
    nonzero = np.zeros((mh, mw), bool)
    for dx, dy in vectors:
        predicted = reference[np.clip(yy+dy, 0, h-1), np.clip(xx+dx, 0, w-1)]
        sad = np.abs(current-predicted).sum(axis=-1, dtype=np.int64)
        if dx == dy == 0:
            zero = sad.copy()
        update = sad < best
        best[update] = sad[update]
        nonzero[update] = dx != 0 or dy != 0
    zero_mae = float(zero.mean()/4)
    best_mae = float(best.mean()/4)
    gain = zero_mae-best_mae
    relative = gain/zero_mae if zero_mae else 0.0
    moving = float(np.mean(nonzero & (zero-best >= 4*config.minimum_gain)))
    allowed = (gain >= config.minimum_gain and relative >= config.minimum_relative_gain
               and moving >= config.minimum_moving_fraction and best_mae <= config.maximum_best_error)
    return dict(allow_block=bool(allowed), reason='motion_screen' if allowed else 'screen_declined',
                samples=int(current.size), comparisons=int(current.size*len(vectors)),
                candidate_vectors=len(vectors), zero_mae=zero_mae, best_mae=best_mae,
                gain=gain, relative_gain=relative, moving_fraction=moving,
                gate_ms=(time.perf_counter_ns()-started)/1e6)


class Encoder(r.Encoder):
    """Frozen complete rate choice with a causal optional-candidate screen."""
    def __init__(self, epoch=1, window=2, config=Config()):
        super().__init__(epoch, window, modes=('gm_zero', 'bm_block'), search_range=config.search_range)
        self.gate_config = config
        self.last_gate = None
        self.last_total_service_ms = None

    def prepare(self, rgb, frame_id, *, scale_map, force_key=False, frame_cap=r.MAX_FRAME):
        started = time.perf_counter_ns()
        self.last_gate = screen(rgb, self._anchor, force_key=force_key, config=self.gate_config)
        modes = self.modes
        self.modes = ('gm_zero', 'bm_block') if self.last_gate['allow_block'] else ('gm_zero',)
        try:
            result = super().prepare(rgb, frame_id, scale_map=scale_map,
                                     force_key=force_key, frame_cap=frame_cap)
        finally:
            self.modes = modes
        self.last_total_service_ms = (time.perf_counter_ns()-started)/1e6
        return result
