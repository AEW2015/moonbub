"""Immutable declared CPU service table and causal source-only refresh policy."""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'python-game-hybrid-link-study/results.json'
POLICIES = ('periodic30', 'periodic60', 'initial_only', 'bounded_scene')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@dataclass(frozen=True)
class ServiceTape:
    """A fixed conditional cost table, not captured per-packet execution times.

    Frame/call count and key/P kind are determined by each causal run. Every
    policy in a workload pair uses identical table values. A fast multiplier
    is a declared what-if, never a claim of measured or achieved acceleration.
    """
    entries: tuple
    provenance: str
    scale: float = 1.0

    def __post_init__(self):
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise ValueError('positive finite replay scale required')
        if any(not math.isfinite(v) or v < 0 for _, v in self.entries):
            raise ValueError('nonnegative finite service required')
        if len(dict(self.entries)) != len(self.entries):
            raise ValueError('duplicate service names')

    def charge(self, stage, frame, key):
        name = stage if stage == 'resize' else stage + ('_key' if key else '_p')
        return dict(self.entries)[name] * self.scale

    def describe(self):
        values = dict(self.entries)
        data = dict(entries_ms=values, provenance=self.provenance, scale=self.scale,
                    interpretation='declared conditional stage means; not actual perpacket replay costs')
        data['table_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        return data


def baseline_tape(clip, mode, *, scale=1.0):
    data = json.loads(BASELINE.read_text())
    case = next(c for c in data['cases'] if c['source'] == clip and c['mode'] == mode
                and c['coded_width'] == 720 and c['coded_height'] == 480
                and c['target_ids_per_second'] == 30 and c['kind'] == 'baseline')
    result = case['result']; packets = {p['id']: p for p in result['packets']}
    values = {}
    for kind in ('key', 'p'):
        for stage in ('encode', 'decode'):
            values[stage + '_' + kind] = result['service_summary'][kind + '_' + stage + '_ms']['mean']
        for stage in ('packetize', 'feed', 'feedback_build', 'feedback_parse'):
            costs = [r['wall_ms'] for r in result['cpu_services'] if r['stage'] == stage
                     and bool(packets[r['id']]['key']) == (kind == 'key')]
            if not costs:
                raise ValueError('missing measured baseline stage ' + stage + '/' + kind)
            values[stage + '_' + kind] = sum(costs) / len(costs)
    # All policies do the same thumbnail observation during resizing. Its
    # 0.05ms scenario increment is explicit, not present in the v11 observation.
    values['resize'] = sum(r['wall_ms'] for r in result['resize_services']) / len(result['resize_services']) + 0.05
    # The four 720p v11 cases contain no rejected preparations. Rejections
    # therefore use an explicit fixed120ms scenario budget, never zero or a
    # post-hoc measured-wall fallback that would break policy pairing.
    values['encode_rejected_key'] = values['encode_rejected_p'] = 120.0
    source = f'v11:{BASELINE.name}:{sha(BASELINE)}:{clip}:{mode}:720x480@30; resize adds declared0.05ms policy observation; rejects declared120ms'
    return ServiceTape(tuple(sorted(values.items())), source, scale)


class RefreshPolicy:
    """Only current and previously preprocessed source thumbnails are observed.

    Decision snapshots are keyed by capture ID. A later observation cannot
    alter the already stored observation/decision for an earlier capture.
    Decode output, future frames, oracle error and packet byte costs are absent.
    """
    def __init__(self, mode, *, min_gap=30, max_gap=120, scene_threshold=28):
        if mode not in POLICIES or not 0 < min_gap <= max_gap or scene_threshold < 0:
            raise ValueError('invalid refresh policy')
        self.mode = mode; self.min_gap = min_gap; self.max_gap = max_gap
        self.scene_threshold = scene_threshold
        self._last_id = None; self._last_sample = None; self._last_scene = None
        self.observations = {}; self.decisions = {}

    def observe(self, frame, image):
        if type(frame) is not int or frame < 0 or (self._last_id is not None and frame <= self._last_id):
            raise ValueError('source observations must be strictly increasing')
        ys = np.linspace(0, image.shape[0] - 1, 18, dtype=int)
        xs = np.linspace(0, image.shape[1] - 1, 32, dtype=int)
        sample = image[ys[:, None], xs[None, :], :].astype(np.int16)
        score = None if self._last_sample is None else float(np.abs(sample - self._last_sample).mean())
        if score is not None and score >= self.scene_threshold:
            self._last_scene = frame
        row = dict(id=frame, prior_observed_id=self._last_id, thumbnail_mad=score,
                   latest_scene_id=self._last_scene, observed_max_id=frame)
        self.observations[frame] = row
        self._last_id, self._last_sample = frame, sample
        return dict(row)

    def due(self, frame, last_key_capture):
        observation = self.observations[frame]  # unavailable/future source is an error
        gap = None if last_key_capture is None else frame - last_key_capture
        reason = 'encoder_handles_initial_or_recovery'
        due = False
        if gap is not None:
            if self.mode.startswith('periodic'):
                due = gap >= int(self.mode.removeprefix('periodic'))
                reason = 'periodic_interval' if due else 'interval_not_due'
            elif self.mode == 'initial_only':
                reason = 'no_periodic_refresh'
            else:
                changed = observation['latest_scene_id'] is not None and observation['latest_scene_id'] > last_key_capture
                due = gap >= self.max_gap or (gap >= self.min_gap and changed)
                reason = 'maximum_interval' if gap >= self.max_gap else ('source_scene_latched' if due else 'bounded_wait')
        self.decisions[frame] = dict(id=frame, last_key_capture=last_key_capture,
                                    source_observed_through=frame, force_key=due, reason=reason)
        return due

    def describe(self):
        return dict(mode=self.mode, min_gap=self.min_gap, max_gap=self.max_gap,
                    scene_threshold=self.scene_threshold, thumbnail_shape=[18, 32, 3],
                    observations=list(self.observations.values()),
                    decisions=list(self.decisions.values()),
                    scope='source-only heuristic, no scene-classification accuracy claim')
