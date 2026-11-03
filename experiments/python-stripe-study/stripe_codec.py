"""SS01 byte-driven compressed stripe research, not a device protocol.

Frozen FT01 arithmetic and CP02 coefficient payloads. Frame header <4sBBHHHI>
contains magic/version/scale/width/height/region_count/payload_length. Regions
<HBHHHI> declare stripe/plane/global_row/height/width/coefficient_payload_length;
each has CRC32(header+payload), then the frame ends with CRC32(all prior bytes).
Per stripe, Cb8 rows, Cr8 rows, then Y16 rows are transmitted. The next Cb/Cr
stripe permits the preceding Y stripe to finish its bilinear lookahead.

Callbacks write provisional pixels to a BACK buffer only. Only a complete
frame's commit event makes those pixels valid. Corruption/truncation/reset
never commits partially emitted pixels. Decoder stores one compressed region,
one Y stripe and previous/current chroma stripes, not a full packet or planes.
"""
from __future__ import annotations
import math
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
for sibling in ('python-transform-study', 'python-coefficient-study'):
    sys.path.insert(0, str(HERE.parent/sibling))
import fixed_codec as ft
import coeff_codec as cc

HEADER = struct.Struct('<4sBBHHHI')
REGION = struct.Struct('<HBHHHI')
MAGIC = b'SS01'
CRC = struct.Struct('<I')
CP_OVERHEAD = 26


def geometry(width, height):
    if (type(width) is not int or type(height) is not int or min(width, height)<2
            or max(width, height)>ft.MAX_DIM or width%2 or height%2 or width*height>ft.MAX_PIXELS):
        raise ValueError('bounded even frame geometry required')
    result = []
    for stripe in range(math.ceil(height/16)):
        for plane in (1, 2, 0):
            pw, ph = (width, height) if plane == 0 else (width//2, height//2)
            row, count = (stripe*16, 16) if plane == 0 else (stripe*8, 8)
            count = min(count, ph-row)
            blocks_w = math.ceil(pw/8)
            blocks = blocks_w*math.ceil(count/8)
            result.append((stripe, plane, row, count, pw, blocks, blocks_w))
    return result


def encode(rgb, quant_scale=16):
    a = ft._check_rgb(rgb)
    ft.qtable(quant_scale)
    height, width = a.shape[:2]
    coeff = ft.quantized_coefficients(a, quant_scale)
    chunks = []
    plan = geometry(width, height)
    for stripe, plane, row, count, pw, blocks, bw in plan:
        first = row//8*bw
        payload = cc.encode_coefficients(coeff[plane][first:first+blocks], bw)
        if len(payload)>128*blocks+CP_OVERHEAD:
            raise ValueError('coefficient helper exceeded declared bound')
        header = REGION.pack(stripe, plane, row, count, pw, len(payload))
        chunks.append(header+payload+CRC.pack(zlib.crc32(header+payload)))
    payload = b''.join(chunks)
    header = HEADER.pack(MAGIC, 1, quant_scale, width, height, len(plan), len(payload))
    body = header+payload
    return body+CRC.pack(zlib.crc32(body))


def _render(y, cb, cr, next_cb=None, next_cr=None):
    """One stripe, exact FT01 bilinear phase, with one future chroma row."""
    height, width = y.shape
    def up(p, future):
        p = p.astype(np.int32)
        right = np.concatenate((p[:, 1:], p[:, -1:]), axis=1)
        horizontal = np.empty((len(p), width), np.int32)
        horizontal[:, ::2] = p
        horizontal[:, 1::2] = (p+right+1)//2
        below = np.empty_like(horizontal)
        below[:-1] = horizontal[1:]
        if future is None:
            below[-1] = horizontal[-1]
        else:
            r = future.astype(np.int32)
            below[-1, ::2] = r
            below[-1, 1::2] = (r+np.r_[r[1:], r[-1]]+1)//2
        full = np.empty((height, width), np.int32)
        full[::2] = horizontal
        full[1::2] = (horizontal+below+1)//2
        return full-128
    u, v = up(cb, next_cb), up(cr, next_cr)
    yy = y.astype(np.int32)
    return np.clip(np.stack((yy+((359*v+128)>>8), yy-((88*u+183*v+128)>>8),
                             yy+((454*u+128)>>8)), axis=-1), 0, 255).astype(np.uint8)


class Decoder:
    """Incremental parser. Caller owns provisional output and commit policy.

    ``on_stripe(row, rgb)`` receives an ephemeral RGB array; copying or writing
    it to a provisional framebuffer is the caller's responsibility. No output
    pixels are retained inside this object. Reuse requires explicit reset().
    """
    def __init__(self, on_stripe=None):
        self.on_stripe = on_stripe or (lambda row, rgb: None)
        self.reset()

    def reset(self):
        self.buffer = bytearray()
        self.state, self.need = 'header', HEADER.size
        self.width = self.height = self.scale = None
        self.plan = []
        self.index = self.seen_payload = self.declared_payload = 0
        self.frame_crc = 0
        self.current_header = None
        self.pending_y = None
        self.chroma = {}
        self.failed = self.committed = False
        self.emitted_rows = 0
        self.metrics = dict(peak_staged_bytes=0, peak_retained_sample_bytes=0,
                            peak_coefficient_array_bytes=0, peak_idct_int64_input_bytes=0,
                            max_output_stripe_bytes=0, validated_regions=0)

    def _sample_peak(self):
        amount = 0 if self.pending_y is None else self.pending_y[1].nbytes
        amount += sum(a.nbytes for a in self.chroma.values())
        self.metrics['peak_retained_sample_bytes'] = max(self.metrics['peak_retained_sample_bytes'], amount)

    def _emit(self, final=False):
        if self.pending_y is None:
            return None
        stripe, y = self.pending_y
        cb, cr = self.chroma[(stripe, 1)], self.chroma[(stripe, 2)]
        if not final:
            if (stripe+1, 1) not in self.chroma or (stripe+1, 2) not in self.chroma:
                return None
            next_cb, next_cr = self.chroma[(stripe+1, 1)][0], self.chroma[(stripe+1, 2)][0]
        else:
            next_cb = next_cr = None
        rgb = _render(y, cb, cr, next_cb, next_cr)
        row = stripe*16
        self.on_stripe(row, rgb)
        self.metrics['max_output_stripe_bytes'] = max(self.metrics['max_output_stripe_bytes'], rgb.nbytes)
        self.emitted_rows += len(rgb)
        self.pending_y = None
        del self.chroma[(stripe, 1)], self.chroma[(stripe, 2)]
        return {'kind': 'provisional_stripe', 'row': row, 'rows': len(rgb), 'committed': False}

    def _process(self, value):
        events = []
        if self.state == 'header':
            magic, version, scale, width, height, count, size = HEADER.unpack(value)
            if magic != MAGIC or version != 1 or not 1<=scale<=128:
                raise ValueError('unsupported stripe profile')
            plan = geometry(width, height)
            maximum = sum(REGION.size+128*p[5]+CP_OVERHEAD+4 for p in plan)
            minimum = len(plan)*(REGION.size+CP_OVERHEAD+4)
            if count != len(plan) or not minimum<=size<=maximum:
                raise ValueError('invalid frame region count/payload bound')
            self.width, self.height, self.scale = width, height, scale
            self.plan, self.declared_payload = plan, size
            self.frame_crc = zlib.crc32(value)
            self.state, self.need = 'region_header', REGION.size
        elif self.state == 'region_header':
            stripe, plane, row, count, width, size = REGION.unpack(value)
            expected = self.plan[self.index]
            if (stripe, plane, row, count, width) != expected[:5]:
                raise ValueError('region order/geometry mismatch')
            if not CP_OVERHEAD<=size<=128*expected[5]+CP_OVERHEAD:
                raise ValueError('region coefficient payload bound')
            if self.seen_payload+REGION.size+size+4>self.declared_payload:
                raise ValueError('region exceeds declared frame length')
            self.current_header = value
            self.frame_crc = zlib.crc32(value, self.frame_crc)
            self.state, self.need = 'region_payload', size+4
        elif self.state == 'region_payload':
            payload = value[:-4]
            if zlib.crc32(payload, zlib.crc32(self.current_header)) != CRC.unpack(value[-4:])[0]:
                raise ValueError('region CRC mismatch')
            self.frame_crc = zlib.crc32(value, self.frame_crc)
            stripe, plane, row, count, width, blocks, bw = self.plan[self.index]
            coefficients = cc.decode_coefficients(payload, blocks, bw)
            if coefficients.shape != (blocks, 8, 8) or coefficients.dtype != np.int16:
                raise ValueError('coefficient helper result')
            self.metrics['peak_coefficient_array_bytes'] = max(self.metrics['peak_coefficient_array_bytes'], coefficients.nbytes)
            self.metrics['peak_idct_int64_input_bytes'] = max(self.metrics['peak_idct_int64_input_bytes'], coefficients.size*8)
            samples = ft._reconstruct_plane(coefficients, width, count, self.scale, plane != 0).astype(np.uint8)
            if plane == 0:
                if self.pending_y is not None:
                    raise ValueError('previous stripe not drained')
                self.pending_y = (stripe, samples)
            else:
                self.chroma[(stripe, plane)] = samples
            self._sample_peak()
            if plane == 2:
                event = self._emit()
                if event is not None:
                    events.append(event)
            self.metrics['validated_regions'] += 1
            self.seen_payload += REGION.size+len(value)
            self.index += 1
            self.current_header = None
            if self.index == len(self.plan):
                if self.seen_payload != self.declared_payload:
                    raise ValueError('incomplete frame length')
                event = self._emit(final=True)
                if event is not None:
                    events.append(event)
                self.state, self.need = 'frame_crc', 4
            else:
                self.state, self.need = 'region_header', REGION.size
        elif self.state == 'frame_crc':
            if CRC.unpack(value)[0] != self.frame_crc or self.emitted_rows != self.height or self.chroma:
                raise ValueError('frame CRC/completeness mismatch')
            self.state, self.need = 'done', 0
            events.append({'kind': 'frame_validated', 'width': self.width, 'height': self.height,
                           'committed': False})
        else:
            raise ValueError('trailing frame bytes')
        return events

    def feed(self, data):
        """Consume bytes without retaining more than one region; return metadata events."""
        if self.failed:
            raise ValueError('decoder failed; reset required')
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise ValueError('bytes required')
        events = []
        view = memoryview(data)
        position = 0
        try:
            while position < len(view):
                if self.state == 'done':
                    raise ValueError('trailing frame bytes')
                take = min(self.need-len(self.buffer), len(view)-position)
                self.buffer.extend(view[position:position+take])
                position += take
                self.metrics['peak_staged_bytes'] = max(self.metrics['peak_staged_bytes'], len(self.buffer))
                if len(self.buffer) == self.need:
                    value = bytes(self.buffer)
                    self.buffer.clear()
                    events.extend(self._process(value))
        except Exception:
            self.failed, self.committed = True, False
            self.buffer.clear()
            self.pending_y = None
            self.chroma.clear()
            raise
        return events

    def finish(self):
        """Require exact complete frame; EOF before CRC is a non-commit failure."""
        if self.failed or self.state != 'done':
            self.failed, self.committed = True, False
            self.buffer.clear()
            self.pending_y = None
            self.chroma.clear()
            raise ValueError('incomplete stripe frame')
        self.committed = True
        return dict(self.metrics, committed=True)


def decode(packet, chunk_size=1024):
    """Convenience full-frame BACK buffer; only return it after commit."""
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError('positive chunk size required')
    output = {}
    def store(row, rgb):
        if 'back' not in output:
            output['back'] = np.empty((decoder.height, decoder.width, 3), np.uint8)
        output['back'][row:row+len(rgb)] = rgb
    decoder = Decoder(store)
    for start in range(0, len(packet), chunk_size):
        decoder.feed(packet[start:start+chunk_size])
    decoder.finish()
    return output['back']
