"""MT02/MA01 receiver with only CP02 parsing replaced; golden Q14 unchanged."""
from pathlib import Path
import struct
import sys
import time
import zlib
import numpy as np
import word_coeff

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-anchor-study'))
import anchor_codec as anchor
mt=anchor.mt
HEADER,LENGTH,NO_REF,MV_LIMIT=mt.HEADER,mt.LENGTH,mt.NO_REF,mt.MV_LIMIT
ft,predict,reconstruct,_snapshot=mt.ft,mt.predict,mt.reconstruct,mt._snapshot


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
        parse_started=time.perf_counter_ns()
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
            coeffs.append(word_coeff.decode_coefficients(packet[position:position+count], bw*bh, bw))
            position += count
        if position != len(packet)-4:
            raise ValueError('trailing motion payload')
        parse_ms=(time.perf_counter_ns()-parse_started)/1e6
        stage_started=time.perf_counter_ns()
        rebuilt = reconstruct(coeffs, prediction, scale)
        inverse_ms=(time.perf_counter_ns()-stage_started)/1e6
        stage_started=time.perf_counter_ns()
        rgb = ft.planes_to_rgb(rebuilt)
        rgb_ms=(time.perf_counter_ns()-stage_started)/1e6
        self.last_stages_ms=dict(coefficients=parse_ms,reconstruct=inverse_ms,rgb=rgb_ms)
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


class AnchorReceiver:
    def __init__(self, epoch=1):
        Receiver(epoch)  # Validate epoch with the frozen state machine.
        self.epoch = epoch
        self.anchor_id, self._anchor = None, None
        self.last_frame_id = -1

    def receive(self, packet):
        mt_packet = anchor._remagic(packet, b'MA01', b'MT02')
        fields = mt.HEADER.unpack_from(mt_packet)
        frame, ref = fields[3:5]
        if frame <= self.last_frame_id:
            raise ValueError('anchor frame replay/regression')
        scratch = Receiver(self.epoch)
        scratch.reference_id, scratch._reference = self.anchor_id, self._anchor
        actual, info = scratch.receive(mt_packet)
        if ref == mt.NO_REF:
            self.anchor_id, self._anchor = frame, scratch._reference
        self.last_frame_id = frame
        self.last_stages_ms=scratch.last_stages_ms
        info.update(anchor_id=self.anchor_id, last_frame_id=self.last_frame_id,
                    retained_reference_array_bytes=sum(x.nbytes for x in self._anchor))
        return actual, info
