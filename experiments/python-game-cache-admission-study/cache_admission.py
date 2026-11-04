"""Exact-source P-payload reuse with bounded preview/admission/commit.

Wire-compatible GM01, not a new skip syntax. A cached preview remains pure and
cannot consume credit until the complete current-ID packet fits and is committed.
"""
from dataclasses import dataclass
from pathlib import Path
import struct
import sys
import time
import weakref
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
for folder in ('python-game-codec-study', 'python-game-rate-study'):
    sys.path.insert(0, str(HERE.parent / folder))
import game_codec as gm
import controller as normal


def ms(start):
    return (time.perf_counter_ns() - start) / 1e6


@dataclass(frozen=True, eq=False)
class Payload:
    owner: object
    epoch: int
    reference_id: int
    anchor: tuple
    header: tuple
    scale_map: np.ndarray
    body_payload: bytes


@dataclass(frozen=True, eq=False)
class CachedCandidate:
    owner: object
    generation: int
    epoch: int
    frame_id: int
    payload: Payload
    packet: bytes
    candidate_ms: float


class Encoder(gm.Encoder):
    """Frozen fresh GM01 path plus separate registered cached capabilities."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._payloads = weakref.WeakSet()
        self._cached_candidates = weakref.WeakSet()

    def remember(self, candidate):
        if candidate not in self._candidates:
            raise ValueError('foreign fresh cache candidate')
        self._check_prepared(candidate.prepared)
        p = candidate.prepared
        if p.key or self._anchor is None:
            raise ValueError('cache only P payloads under an ACKed key')
        item = Payload(self._owner, self.epoch, self.anchor_id, self._anchor,
                       gm.HEADER.unpack_from(candidate.packet), gm._readonly(candidate.scale_map),
                       candidate.packet[gm.HEADER.size:-4])
        self._payloads.add(item)
        return item

    def preview_cached(self, payload, frame_id):
        start = time.perf_counter_ns()
        if (not isinstance(payload, Payload) or payload not in self._payloads
                or payload.owner is not self._owner or payload.epoch != self.epoch
                or payload.anchor is not self._anchor or payload.reference_id != self.anchor_id
                or type(frame_id) is not int or not self.last_issued < frame_id < gm.NO_REF
                or not self.can_prepare(False)):
            raise ValueError('stale/foreign cache payload or unavailable credit')
        fields = list(payload.header)
        fields[4] = frame_id
        body = gm.HEADER.pack(*fields) + payload.body_payload
        packet = body + struct.pack('<I', zlib.crc32(body))
        candidate = CachedCandidate(self._owner, self._generation, self.epoch,
                                    frame_id, payload, packet, ms(start))
        self._cached_candidates.add(candidate)
        return candidate

    def commit(self, candidate):
        if not isinstance(candidate, CachedCandidate):
            return super().commit(candidate)
        p = candidate.payload
        if (candidate not in self._cached_candidates or candidate.owner is not self._owner
                or candidate.generation != self._generation or candidate.epoch != self.epoch
                or candidate.frame_id <= self.last_issued or not self.can_prepare(False)
                or p not in self._payloads or p.anchor is not self._anchor
                or p.reference_id != self.anchor_id or p.epoch != self.epoch):
            raise ValueError('stale/foreign cached preview')
        self.pending[candidate.frame_id] = dict(key=False, planes=None, expected_rgb_sha256=None,
                                               packet=candidate.packet, reference_id=self.anchor_id)
        self.last_issued = candidate.frame_id
        self._generation += 1
        self.peak_pending = max(self.peak_pending, len(self.pending))
        return candidate.packet


class Controller(normal.Controller):
    """At most one source image and two map-specific P payloads on the PC.

    Rejected P candidates may populate the exact cache, but they do not commit
    codec state. A repeat still undergoes complete current packet cap admission.
    """
    def __init__(self, encoder=None, config=None):
        if encoder is not None and not isinstance(encoder, Encoder):
            raise ValueError('cache-aware Encoder required')
        super().__init__(encoder or Encoder(), config)
        self._cache = None
        self.last_cache = None

    def cache_bytes(self):
        if self._cache is None:
            return 0
        return self._cache['source'].nbytes + sum(
            p.scale_map.nbytes + gm.HEADER.size + len(p.body_payload) for p in self._cache['payloads'])

    def prepare(self, rgb, frame_id, *, force_key=False, reuse=True):
        if not reuse:
            raise ValueError('cache controller uses one shared fresh analysis')
        start = time.perf_counter_ns()
        a = gm.ft._check_rgb(rgb)
        h, w = a.shape[:2]
        enc = self.encoder
        key = bool(force_key or enc._anchor is None or enc._anchor[0].shape != (h, w))
        if (type(frame_id) is not int or not enc.last_issued < frame_id < gm.NO_REF
                or not enc.can_prepare(key)):
            raise ValueError('GM01 credit, drain or identity')
        began = time.perf_counter_ns()
        maps = self.maps(a)
        map_ms = ms(began)
        began = time.perf_counter_ns()
        cache = self._cache
        compatible = (not key and cache is not None and cache['epoch'] == enc.epoch
                      and cache['anchor'] is enc._anchor and cache['reference_id'] == enc.anchor_id
                      and cache['mode'] == self.config.motion_mode and cache['source'].shape == a.shape)
        equal = bool(compatible and np.array_equal(cache['source'], a))
        if not equal:
            self._cache = None
        lookup_ms = ms(began)
        attempts = []
        prepared = None
        analyze_calls = forward_calls = 0
        chosen = selected = counts = None
        for label, mapped in maps:
            began = time.perf_counter_ns()
            payload = next((p for p in self._cache['payloads'] if np.array_equal(p.scale_map, mapped)), None) if self._cache else None
            row_lookup_ms = ms(began) + (lookup_ms if not attempts else 0)
            analyze_ms = copy_ms = 0.0
            hit = payload is not None
            if hit:
                began = time.perf_counter_ns()
                candidate = enc.preview_cached(payload, frame_id)
                candidate_ms = ms(began)
            else:
                if prepared is None:
                    began = time.perf_counter_ns()
                    prepared = enc.analyze(a, frame_id, force_key=force_key, mode=self.config.motion_mode)
                    analyze_ms = ms(began)
                    analyze_calls += 1
                    forward_calls += prepared.forward_calls
                began = time.perf_counter_ns()
                candidate = enc.encode_candidate(prepared, mapped)
                candidate_ms = ms(began)
                if not key:
                    began = time.perf_counter_ns()
                    payload = enc.remember(candidate)
                    if self._cache is None:
                        source = gm._readonly(a)
                        self._cache = dict(source=source, epoch=enc.epoch, anchor=enc._anchor,
                                           reference_id=enc.anchor_id, mode=self.config.motion_mode, payloads=[])
                    entries = self._cache['payloads']
                    if len(entries) == 2:
                        entries.pop(0)
                    entries.append(payload)
                    copy_ms = ms(began)
            size = len(candidate.packet)
            row_counts = {str(s): int((mapped == s).sum()) for s in (8, 16, 32)}
            attempts.append(dict(label=label, bytes=size, fits=size <= self.config.frame_cap,
                                 analyze_ms=analyze_ms, candidate_ms=candidate_ms, scale_counts=row_counts,
                                 cache_hit=hit, cache_lookup_ms=row_lookup_ms, cache_copy_ms=copy_ms,
                                 cache_bytes_after=self.cache_bytes()))
            if size <= self.config.frame_cap:
                chosen, selected, counts = candidate, label, row_counts
                break
        packet = None
        commit_ms = 0.0
        if chosen is not None:
            began = time.perf_counter_ns()
            packet = enc.commit(chosen)
            commit_ms = ms(began)
        self.last_cache = dict(source_equal=equal, key=key, hits=sum(r['cache_hit'] for r in attempts),
                               lookup_ms=sum(r['cache_lookup_ms'] for r in attempts),
                               copy_ms=sum(r['cache_copy_ms'] for r in attempts), bytes=self.cache_bytes(),
                               admission_before_commit=True)
        return normal.Decision(packet, selected, tuple(attempts), analyze_calls, forward_calls,
                               ms(start), commit_ms, map_ms, counts)
