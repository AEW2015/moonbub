"""MT02 bounded global-motion transform prototype with stop-and-wait commit.

Prediction uses the exact ACKed reconstructed YUV420 planes, not host originals.
Each bounded even vector samples reference[y+dy,x+dx] with border replication;
chroma uses half the vector. Key prediction is constant128, matching FT01.
Residuals use the frozen Q14 transform and CP02 coefficient payloads. All
reconstruction is complete-frame/CRC checked before receiver reference commit.

This Python reference is not an integrated sender, FPGA decoder or memory-drain
ACK. One outstanding transaction is intentional; feedback/throughput is a
separate gate. Timeout/abort invalidates the encoder reference and requires a
new independent frame, including when an ACK rather than data was lost.
"""
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
for p in (HERE.parent/'python-transform-study', HERE.parent/'python-coefficient-study'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import fixed_codec as ft
import coeff_codec as cc

HEADER = struct.Struct('<4sBIIIBHHhhI')
LENGTH = struct.Struct('<I')
NO_REF = 0xffffffff
MV_LIMIT = 16


def predict(planes, dx=0, dy=0):
    out = []
    for i, plane in enumerate(planes):
        h, w = plane.shape
        x, y = (dx, dy) if i == 0 else (dx//2, dy//2)
        xx = np.clip(np.arange(w)+x, 0, w-1)
        yy = np.clip(np.arange(h)+y, 0, h-1)
        out.append(plane[yy[:, None], xx].astype(np.int16))
    return out


def estimate_motion(current, reference):
    """Host-only bounded even translation search; brightness SAD on a grid."""
    h, w = current.shape
    if min(h, w) <= 2*MV_LIMIT+4:
        return 0, 0
    yy, xx = np.mgrid[MV_LIMIT:h-MV_LIMIT:8, MV_LIMIT:w-MV_LIMIT:8]
    target = current[yy, xx].astype(np.int32)
    def cost(x, y):
        return float(np.abs(target-reference[yy+y, xx+x]).mean())
    coarse = [(cost(x, y), abs(x)+abs(y), x, y)
              for y in range(-MV_LIMIT, MV_LIMIT+1, 4)
              for x in range(-MV_LIMIT, MV_LIMIT+1, 4)]
    _, _, x, y = min(coarse)
    fine = [(cost(a, b), abs(a)+abs(b), a, b)
            for b in range(max(-MV_LIMIT, y-2), min(MV_LIMIT, y+2)+1, 2)
            for a in range(max(-MV_LIMIT, x-2), min(MV_LIMIT, x+2)+1, 2)]
    best, _, x, y = min(fine)
    return (x, y) if best+.1 < cost(0, 0) else (0, 0)


def residual_coefficients(source, prediction, scale):
    result = []
    for i, (src, pred) in enumerate(zip(source, prediction)):
        residual = src.astype(np.int64)-pred
        h, w = residual.shape
        padded = np.pad(residual, ((0, (-h)%8), (0, (-w)%8)), mode='edge')
        ph, pw = padded.shape
        blocks = padded.reshape(ph//8, 8, pw//8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        coeff = ft.round_quantize(ft.forward(blocks), ft.qtable(scale, i != 0))
        if np.any(np.abs(coeff) > ft.MAX_COEFF):
            raise ValueError('motion residual coefficient outside wire range')
        result.append(coeff.astype(np.int16))
    return result


def reconstruct(coefficients, prediction, scale):
    planes = []
    for i, (coeff, pred) in enumerate(zip(coefficients, prediction)):
        h, w = pred.shape
        ph, pw = ((h+7)//8)*8, ((w+7)//8)*8
        residual = ft.inverse(coeff.astype(np.int64)*ft.qtable(scale, i != 0))
        residual = residual.reshape(ph//8, pw//8, 8, 8).transpose(0, 2, 1, 3).reshape(ph, pw)[:h, :w]
        planes.append(np.clip(pred+residual, 0, 255).astype(np.int16))
    return planes


def _snapshot(planes):
    result = [x.copy() for x in planes]
    for x in result:
        x.setflags(write=False)
    return result


class Encoder:
    def __init__(self, epoch=1):
        if type(epoch) is not int or not 0 <= epoch < NO_REF:
            raise ValueError('invalid session epoch')
        self.epoch = epoch
        self.reference_id = None
        self._reference = None
        self._pending = None
        self._last_issued = -1

    def prepare(self, rgb, frame_id, *, quant_scale=16, mode='global', force_key=False):
        if self._pending is not None:
            raise ValueError('one outstanding transaction; await ACK or abort')
        if type(frame_id) is not int or not self._last_issued < frame_id < NO_REF:
            raise ValueError('frame ID must increase without wrap')
        if mode not in ('global', 'zero'):
            raise ValueError('unsupported motion mode')
        source = ft.rgb_to_planes(rgb)
        ft.qtable(quant_scale)
        h, w = source[0].shape
        key = force_key or self._reference is None or self._reference[0].shape != (h, w)
        if key:
            ref_id, dx, dy = NO_REF, 0, 0
            prediction = [np.full_like(x, 128) for x in source]
        else:
            ref_id = self.reference_id
            dx, dy = estimate_motion(source[0], self._reference[0]) if mode == 'global' else (0, 0)
            prediction = predict(self._reference, dx, dy)
        coeffs = residual_coefficients(source, prediction, quant_scale)
        rebuilt = reconstruct(coeffs, prediction, quant_scale)
        chunks = []
        for c, plane in zip(coeffs, source):
            payload = cc.encode_coefficients(c, (plane.shape[1]+7)//8)
            chunks.append(LENGTH.pack(len(payload))+payload)
        payload = b''.join(chunks)
        body = HEADER.pack(b'MT02', 1, self.epoch, frame_id, ref_id, quant_scale,
                           w, h, dx, dy, len(payload))+payload
        packet = body+struct.pack('<I', zlib.crc32(body))
        self._pending = (frame_id, _snapshot(rebuilt))
        self._last_issued = frame_id
        return packet

    def prepared_rgb(self):
        if self._pending is None:
            raise ValueError('no pending frame')
        return ft.planes_to_rgb(self._pending[1])

    def ack(self, frame_id, *, epoch):
        if (type(epoch) is not int or epoch != self.epoch or type(frame_id) is not int
                or self._pending is None or self._pending[0] != frame_id):
            raise ValueError('unexpected or stale ACK')
        self.reference_id, self._reference = self._pending
        self._pending = None

    def abort(self):
        self._pending = None
        self.reference_id = None
        self._reference = None


class Receiver:
    def __init__(self, epoch=1):
        if type(epoch) is not int or not 0 <= epoch < NO_REF:
            raise ValueError('invalid session epoch')
        self.epoch = epoch
        self.reference_id = None
        self._reference = None

    def receive(self, packet):
        if not isinstance(packet, bytes) or len(packet) < HEADER.size+16:
            raise ValueError('truncated motion packet')
        magic, version, epoch, frame, ref, scale, w, h, dx, dy, length = HEADER.unpack_from(packet)
        if magic != b'MT02' or version != 1 or epoch != self.epoch or epoch == NO_REF:
            raise ValueError('motion profile/session mismatch')
        if (frame == NO_REF or (self.reference_id is not None and frame <= self.reference_id)
                or not 2 <= w <= ft.MAX_DIM or not 2 <= h <= ft.MAX_DIM
                or w%2 or h%2 or w*h > ft.MAX_PIXELS or not 1 <= scale <= 128
                or dx%2 or dy%2 or abs(dx) > MV_LIMIT or abs(dy) > MV_LIMIT):
            raise ValueError('invalid motion identity/geometry/vector')
        dimensions = ((h, w), (h//2, w//2), (h//2, w//2))
        maximum = sum(4+128*((hh+7)//8)*((ww+7)//8)+26 for hh, ww in dimensions)
        if length > maximum or len(packet) != HEADER.size+length+4:
            raise ValueError('invalid motion payload length/bound')
        if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
            raise ValueError('motion CRC mismatch')
        if ref == NO_REF:
            if dx or dy:
                raise ValueError('key frame cannot name motion')
            prediction = [np.full(d, 128, np.int16) for d in dimensions]
        else:
            if ref >= frame or ref != self.reference_id or self._reference is None or self._reference[0].shape != (h, w):
                raise ValueError('missing exact committed reference')
            prediction = predict(self._reference, dx, dy)
        position = HEADER.size
        coeffs = []
        for hh, ww in dimensions:
            if position+4 > len(packet)-4:
                raise ValueError('missing plane length')
            count = LENGTH.unpack_from(packet, position)[0]
            position += 4
            if position+count > len(packet)-4:
                raise ValueError('plane outside frame')
            bw, bh = (ww+7)//8, (hh+7)//8
            coeffs.append(cc.decode_coefficients(packet[position:position+count], bw*bh, bw))
            position += count
        if position != len(packet)-4:
            raise ValueError('trailing motion payload')
        rebuilt = reconstruct(coeffs, prediction, scale)
        rgb = ft.planes_to_rgb(rebuilt)
        self._reference = _snapshot(rebuilt)
        self.reference_id = frame
        pixels = w*h
        return rgb, {'epoch': self.epoch, 'frame_id': frame, 'reference_id': None if ref == NO_REF else ref,
                     'key': ref == NO_REF, 'dx': dx, 'dy': dy, 'bytes': len(packet),
                     'reference_sample_read_bytes': 0 if ref == NO_REF else pixels*3//2,
                     'reconstruction_sample_write_bytes': pixels*3//2,
                     'rgb565_output_write_bytes': pixels*2,
                     'reference_storage_payload_bytes': pixels*3//2,
                     'python_reference_array_bytes': sum(x.nbytes for x in self._reference),
                     'scope': 'logical sample/pixel payload counts; no physical transaction/cache model'}
