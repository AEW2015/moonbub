"""MA01 immutable-anchor experiment, not an installed MT02 capability.

Wire arithmetic equals MT02, but P packets name a retained ACKed key anchor.
P ACKs release bounded credits and never advance that anchor. Refresh keys
are prepared only after old P credits drain. Epoch/frame checks and complete
frame CRC validation precede commit. No network ACK serialization, physical
drain or authentication is implemented by these Python state machines.
"""
from pathlib import Path
import hashlib
import sys
import zlib
import struct

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-motion-study'))
import motion_codec as mt


def _remagic(packet, expected, replacement):
    if not isinstance(packet, bytes) or len(packet) < mt.HEADER.size+4 or packet[:4] != expected:
        raise ValueError('anchor packet profile')
    # Validate supplied bytes before changing the profile, so a damaged CRC
    # cannot be repaired accidentally by the adapter.
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('anchor packet CRC')
    body = replacement+packet[4:-4]
    return body+struct.pack('<I', zlib.crc32(body))


class AnchorEncoder:
    def __init__(self, epoch=1, window=2):
        if type(epoch) is not int or not 0 <= epoch < mt.NO_REF or type(window) is not int or not 1 <= window <= 8:
            raise ValueError('invalid anchor session/window')
        self.epoch, self.window = epoch, window
        self.anchor_id, self._anchor = None, None
        self.pending = {}
        self.last_issued = -1
        self.peak_pending = 0

    def can_prepare(self, force_key=False):
        if any(row['key'] for row in self.pending.values()):
            return False
        if force_key or self._anchor is None:
            return not self.pending
        return len(self.pending) < self.window

    def prepare(self, rgb, frame_id, *, quant_scale=8, force_key=False, mode='global'):
        source = mt.ft._check_rgb(rgb)
        key = force_key or self._anchor is None or self._anchor[0].shape != source.shape[:2]
        if not self.can_prepare(key) or type(frame_id) is not int or not self.last_issued < frame_id < mt.NO_REF:
            raise ValueError('anchor credits, refresh drain or frame identity')
        scratch = mt.Encoder(self.epoch)
        if not key:
            scratch.reference_id, scratch._reference = self.anchor_id, self._anchor
        packet = scratch.prepare(source, frame_id, quant_scale=quant_scale, mode=mode, force_key=key)
        expected = scratch.prepared_rgb()
        row = {'key': key, 'expected_rgb_sha256': hashlib.sha256(expected.tobytes()).hexdigest(),
               'reference_id': None if key else self.anchor_id,
               'planes': scratch._pending[1] if key else None}
        if key:
            # No old anchor is needed after its readers/ACK credits drained.
            self.anchor_id, self._anchor = None, None
        self.pending[frame_id] = row
        self.last_issued = frame_id
        self.peak_pending = max(self.peak_pending, len(self.pending))
        return _remagic(packet, b'MT02', b'MA01')

    def expected_hash(self, frame_id):
        return self.pending[frame_id]['expected_rgb_sha256']

    def ack(self, frame_id, *, epoch):
        if type(epoch) is not int or epoch != self.epoch or type(frame_id) is not int:
            raise ValueError('ACK epoch/identity')
        row = self.pending.pop(frame_id, None)
        if row is None:
            return False  # Duplicates/expired ACKs cannot consume another credit.
        if row['key']:
            self.anchor_id, self._anchor = frame_id, row['planes']
        return True

    def expire(self, frame_id):
        row = self.pending.pop(frame_id, None)
        if row is None:
            return False
        if row['key']:
            self.anchor_id, self._anchor = None, None
        return True

    def retained_reference_bytes(self):
        planes = self._anchor
        if planes is None:
            planes = next((r['planes'] for r in self.pending.values() if r['key']), None)
        return sum(x.nbytes for x in planes) if planes is not None else 0


class AnchorReceiver:
    def __init__(self, epoch=1):
        mt.Receiver(epoch)  # Validate epoch with the frozen state machine.
        self.epoch = epoch
        self.anchor_id, self._anchor = None, None
        self.last_frame_id = -1

    def receive(self, packet):
        mt_packet = _remagic(packet, b'MA01', b'MT02')
        fields = mt.HEADER.unpack_from(mt_packet)
        frame, ref = fields[3:5]
        if frame <= self.last_frame_id:
            raise ValueError('anchor frame replay/regression')
        scratch = mt.Receiver(self.epoch)
        scratch.reference_id, scratch._reference = self.anchor_id, self._anchor
        actual, info = scratch.receive(mt_packet)
        if ref == mt.NO_REF:
            self.anchor_id, self._anchor = frame, scratch._reference
        self.last_frame_id = frame
        info.update(anchor_id=self.anchor_id, last_frame_id=self.last_frame_id,
                    retained_reference_array_bytes=sum(x.nbytes for x in self._anchor))
        return actual, info
