"""Compose admission-aware host reuse and bit-exact receive in the finite model.

Codec syntax and GF02/GA01 are unchanged. Both baseline and cache use the frozen
normal rate controller's policy, rather than changing a size gate simultaneously.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
for folder in ('python-game-hybrid-study', 'python-game-rate-study',
               'python-game-feedback-study', 'python-game-sparse-study',
               'python-game-cache-admission-study', 'python-game-ui-cache-study'):
    sys.path.insert(0, str(HERE.parent / folder))
import hybrid_codec as hybrid
import controller as normal
import fast_codec
import transport
import ui_cache


@dataclass(frozen=True)
class Decision:
    packet: bytes | None
    selected: str | None
    attempts: tuple
    analyze_calls: int
    forward_calls: int
    service_ms: float
    commit_ms: float
    map_build_ms: float
    selected_scale_counts: dict | None
    identity: dict | None
    hybrid: dict
    oracle_excluded: bool = True

    @property
    def accepted(self):
        return self.packet is not None


class DecoderState:
    def __init__(self, epoch=1, frame_cap=49152, *, fast=False):
        self.impl = (fast_codec.HybridReceiver if fast else hybrid.Decoder)(epoch, frame_cap)

    @property
    def base(self): return self.impl.base
    @property
    def anchor_id(self): return self.base.anchor_id
    @anchor_id.setter
    def anchor_id(self, value): self.base.anchor_id = value
    @property
    def _anchor(self): return self.base._anchor
    @_anchor.setter
    def _anchor(self, value): self.base._anchor = value
    @property
    def last_frame_id(self): return self.base.last_frame_id
    @last_frame_id.setter
    def last_frame_id(self, value): self.base.last_frame_id = value
    def receive(self, packet): return self.impl.receive(packet)


def identity(packet, epoch=1, frame_cap=49152):
    return hybrid.base_identity(packet, epoch, frame_cap)


def make_controller(*, credit_window=2, ui=True, rectangles=hybrid.COMPACT, ui_cache_enabled=True):
    if type(credit_window) is not int or credit_window not in (2,3):
        raise ValueError('two or three PC transactions required')
    if type(ui_cache_enabled) is not bool:raise ValueError('UI cache boolean required')
    import cache_admission
    base_factory = cache_admission.Controller
    cache = True

    class Controller:
        def __init__(self, config=None):
            self.base = base_factory(config=config)
            self.encoder = self.base.encoder
            self.encoder.window = credit_window
            self.patch_cache = ui_cache.PatchCache() if ui_cache_enabled else None
            self.config = self.base.config
            self._oracle_packets = {}

        def prepare(self, rgb, frame_id, *, force_key=False):
            started = time.perf_counter_ns()
            base = self.base.prepare(rgb, frame_id, force_key=force_key)
            if not base.accepted:
                return Decision(None, base.selected, base.attempts, base.analyze_calls,
                                base.forward_calls, (time.perf_counter_ns()-started)/1e6,
                                base.commit_ms, base.map_build_ms, base.selected_scale_counts,
                                None, {'base_rejected': True, 'cache_enabled': cache})
            selection = hybrid.select_frame(base.packet, rgb, hybrid.Config(
                frame_cap=self.config.frame_cap, rectangles=rectangles,
                patch_policy='adaptive_row', max_attempts=4 if ui else 0),
                spent_before_ms=(time.perf_counter_ns()-started)/1e6,
                patch_encoder=self.patch_cache if self.patch_cache is not None else hybrid._encode_patch)
            if not selection.accepted:
                raise AssertionError('admitted GM base unexpectedly rejected')
            self._oracle_packets[frame_id] = selection.packet
            detail = dict(base_packet_bytes=len(base.packet),
                          base_packet_sha256=hashlib.sha256(base.packet).hexdigest(),
                          cache_enabled=cache, ui_cache_enabled=ui_cache_enabled, format=selection.format, reason=selection.reason,
                          selected_pixels=selection.selected_pixels,
                          requested_pixels=selection.requested_pixels,
                          selected=selection.selected, attempts=selection.attempts,
                          selector_ms=selection.service_ms,
                          selector_deadline_hit=selection.deadline_hit,
                          preflight_ms=selection.preflight_ms,
                          wrapper_assembly_ms=selection.assembly_ms,
                          patch_policy='adaptive_row')
            return Decision(selection.packet, base.selected, base.attempts, base.analyze_calls,
                            base.forward_calls, (time.perf_counter_ns()-started)/1e6,
                            base.commit_ms, base.map_build_ms, base.selected_scale_counts,
                            selection.identity, detail)

        def expected_hashes(self, frame_id):
            # Verification-only decode after the model's measured preparation.
            packet = self._oracle_packets.pop(frame_id)
            receiver = hybrid.Decoder(frame_cap=self.config.frame_cap)
            receiver.base.anchor_id = self.encoder.anchor_id
            receiver.base._anchor = self.encoder._anchor
            rgb, info = receiver.receive(packet)
            return hashlib.sha256(rgb.tobytes()).hexdigest(), info['base_rgb_sha256']

    return Controller
