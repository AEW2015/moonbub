"""MA01-compatible key preparation with no eager verification RGB work.

Only the reconstructed YUV key is future prediction state. The new key uses
v5 fast CP02 serialization, marks newly-owned reconstructed planes read-only
without an extra snapshot copy, and defers optional verification RGB/hash.
P preparation is the unchanged v5 lazy-P implementation. Timing fields are
observations only and cannot change packet decisions.
"""
import hashlib
from pathlib import Path
import struct
import sys
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-fast-entropy-study'))
import fast_anchor
import fast_coeff

frozen = fast_anchor.frozen


class Encoder(fast_anchor.Encoder):
    def __init__(self, epoch=1, window=2):
        super().__init__(epoch=epoch, window=window)
        self.last_prepare_stages_ms = {}

    def prepare(self, rgb, frame_id, *, quant_scale=8, force_key=False, mode='global'):
        started = time.perf_counter_ns()
        mt = frozen.mt
        a = mt.ft._check_rgb(rgb)
        key = force_key or self._anchor is None or self._anchor[0].shape != a.shape[:2]
        if not key:
            packet = super().prepare(a, frame_id, quant_scale=quant_scale, force_key=False, mode=mode)
            self.last_prepare_stages_ms = {'kind': 'P', 'prepare_ms': (time.perf_counter_ns() - started) / 1e6}
            return packet
        if not self.can_prepare(True) or type(frame_id) is not int or not self.last_issued < frame_id < mt.NO_REF:
            raise ValueError('anchor credits, refresh drain or frame identity')
        if mode not in ('zero', 'global'):
            raise ValueError('unsupported motion mode')
        mt.ft.qtable(quant_scale)
        timings = {'kind': 'KEY'}
        began = time.perf_counter_ns()
        source = mt.ft.rgb_to_planes(a)
        prediction = [np.full_like(x, 128) for x in source]
        timings['rgb_planes_prediction_ms'] = (time.perf_counter_ns() - began) / 1e6
        began = time.perf_counter_ns()
        coefficients = mt.residual_coefficients(source, prediction, quant_scale)
        timings['transform_quantize_ms'] = (time.perf_counter_ns() - began) / 1e6
        began = time.perf_counter_ns()
        chunks = []
        for coeff, plane in zip(coefficients, source):
            payload = fast_coeff.encode_coefficients(coeff, (plane.shape[1] + 7) // 8)
            chunks.append(mt.LENGTH.pack(len(payload)) + payload)
        timings['entropy_ms'] = (time.perf_counter_ns() - began) / 1e6
        began = time.perf_counter_ns()
        rebuilt = mt.reconstruct(coefficients, prediction, quant_scale)
        # reconstruct returns newly-owned arrays; no caller source or prior
        # anchor aliases them. Freeze them directly instead of copying again.
        for plane in rebuilt:
            plane.setflags(write=False)
        timings['reconstruct_freeze_ms'] = (time.perf_counter_ns() - began) / 1e6
        began = time.perf_counter_ns()
        h, w = a.shape[:2]
        payload = b''.join(chunks)
        body = mt.HEADER.pack(b'MA01', 1, self.epoch, frame_id, mt.NO_REF, quant_scale,
                              w, h, 0, 0, len(payload)) + payload
        packet = body + struct.pack('<I', zlib.crc32(body))
        self.anchor_id, self._anchor = None, None
        self.pending[frame_id] = {'key': True, 'expected_rgb_sha256': None,
                                  'reference_id': None, 'planes': rebuilt}
        self.last_issued = frame_id
        self.peak_pending = max(self.peak_pending, len(self.pending))
        timings['packet_state_ms'] = (time.perf_counter_ns() - began) / 1e6
        timings['prepare_ms'] = (time.perf_counter_ns() - started) / 1e6
        self.last_prepare_stages_ms = timings
        return packet

    def expected_hash(self, frame_id):
        row = self.pending[frame_id]
        if row['key'] and row['expected_rgb_sha256'] is None:
            rgb = frozen.mt.ft.planes_to_rgb(row['planes'])
            row['expected_rgb_sha256'] = hashlib.sha256(rgb.tobytes()).hexdigest()
        return super().expected_hash(frame_id)

    def oracle_packet_bytes(self):
        """Additional retained host P packet bytes, excluding shared aliases."""
        return sum(len(row.get('oracle_packet', b'')) for row in self.pending.values())
