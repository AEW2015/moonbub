"""MA01 host optimization: P reconstruction is unnecessary for an immutable anchor.

Only key reconstruction becomes a future predictor. P packets can therefore
skip host IDCT/snapshot/RGB reconstruction, while emitting identical bytes.
The optional expected_hash oracle runs lazily, outside production preparation,
and retains the already-produced packet until ACK; window bounds still apply.
"""
import hashlib
from pathlib import Path
import struct
import sys
import zlib

import fast_coeff

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-anchor-study'))
import anchor_codec as frozen


class Encoder(frozen.AnchorEncoder):
    def prepare(self,rgb,frame_id,*,quant_scale=8,force_key=False,mode='global'):
        mt=frozen.mt
        a=mt.ft._check_rgb(rgb)
        key=force_key or self._anchor is None or self._anchor[0].shape!=a.shape[:2]
        if key:
            return super().prepare(a,frame_id,quant_scale=quant_scale,force_key=force_key,mode=mode)
        if not self.can_prepare(False) or type(frame_id) is not int or not self.last_issued<frame_id<mt.NO_REF:
            raise ValueError('anchor credits or identity')
        if mode not in ('zero','global'):
            raise ValueError('motion mode')
        mt.ft.qtable(quant_scale)
        source=mt.ft.rgb_to_planes(a)
        dx,dy=mt.estimate_motion(source[0],self._anchor[0]) if mode=='global' else (0,0)
        prediction=mt.predict(self._anchor,dx,dy)
        coeffs=mt.residual_coefficients(source,prediction,quant_scale)
        chunks=[]
        for coeff,plane in zip(coeffs,source):
            payload=fast_coeff.encode_coefficients(coeff,(plane.shape[1]+7)//8)
            chunks.append(mt.LENGTH.pack(len(payload))+payload)
        payload=b''.join(chunks);h,w=a.shape[:2]
        body=mt.HEADER.pack(b'MT02',1,self.epoch,frame_id,self.anchor_id,quant_scale,w,h,dx,dy,len(payload))+payload
        packet=frozen._remagic(body+struct.pack('<I',zlib.crc32(body)),b'MT02',b'MA01')
        self.pending[frame_id]={'key':False,'expected_rgb_sha256':None,'reference_id':self.anchor_id,
                                'planes':None,'oracle_packet':packet}
        self.last_issued=frame_id
        self.peak_pending=max(self.peak_pending,len(self.pending))
        return packet

    def expected_hash(self,frame_id):
        row=self.pending[frame_id]
        if row['expected_rgb_sha256'] is None:
            scratch=frozen.mt.Receiver(self.epoch)
            scratch.reference_id,scratch._reference=self.anchor_id,self._anchor
            rgb,_=scratch.receive(frozen._remagic(row['oracle_packet'],b'MA01',b'MT02'))
            row['expected_rgb_sha256']=hashlib.sha256(rgb.tobytes()).hexdigest()
        return row['expected_rgb_sha256']
