"""MT02 host encoder with only its CP02 serialization implementation replaced."""
from pathlib import Path
import struct
import sys
import zlib

import numpy as np

import fast_coeff

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-motion-study'))
import motion_codec as frozen


class Encoder(frozen.Encoder):
    def prepare(self, rgb, frame_id, *, quant_scale=16, mode='global', force_key=False):
        if self._pending is not None:
            raise ValueError('one outstanding transaction; await ACK or abort')
        if type(frame_id) is not int or not self._last_issued < frame_id < frozen.NO_REF:
            raise ValueError('frame ID must increase without wrap')
        if mode not in ('global','zero'):
            raise ValueError('unsupported motion mode')
        source = frozen.ft.rgb_to_planes(rgb)
        frozen.ft.qtable(quant_scale)
        h,w = source[0].shape
        key = force_key or self._reference is None or self._reference[0].shape != (h,w)
        if key:
            ref_id,dx,dy = frozen.NO_REF,0,0
            prediction = [np.full_like(x,128) for x in source]
        else:
            ref_id = self.reference_id
            dx,dy = frozen.estimate_motion(source[0],self._reference[0]) if mode=='global' else (0,0)
            prediction = frozen.predict(self._reference,dx,dy)
        coeffs = frozen.residual_coefficients(source,prediction,quant_scale)
        rebuilt = frozen.reconstruct(coeffs,prediction,quant_scale)
        chunks = []
        for coeff,plane in zip(coeffs,source):
            payload = fast_coeff.encode_coefficients(coeff,(plane.shape[1]+7)//8)
            chunks.append(frozen.LENGTH.pack(len(payload))+payload)
        payload = b''.join(chunks)
        body = frozen.HEADER.pack(b'MT02',1,self.epoch,frame_id,ref_id,quant_scale,w,h,dx,dy,len(payload))+payload
        packet = body+struct.pack('<I',zlib.crc32(body))
        self._pending = (frame_id,frozen._snapshot(rebuilt))
        self._last_issued = frame_id
        return packet
