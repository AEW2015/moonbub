"""Bounded exact-source GM01 P-payload reuse under one immutable ACKed key.

No new wire format, decoder reference or source-image approximation. Cache hits
still issue full GM01 packets with current IDs and CRC and consume normal credit.
"""
from pathlib import Path
import struct
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-codec-study'))
import game_codec as gm


class Encoder(gm.Encoder):
    def __init__(self,epoch=1,window=2):
        super().__init__(epoch,window);self._cache=None;self.last_memo_info=None

    def prepare(self,rgb,frame_id,*,scale_map=None,quant_scale=16,force_key=False,mode='zero'):
        started=time.perf_counter_ns();a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
        key=bool(force_key or self._anchor is None or self._anchor[0].shape!=(h,w))
        if (type(frame_id) is not int or not self.last_issued<frame_id<gm.NO_REF or not self.can_prepare(key)
            or mode not in ('zero','global')):
            raise ValueError('memo GM01 credit/identity/drain/mode')
        if scale_map is None:
            if type(quant_scale) is not int or quant_scale not in gm.roi.SCALES:raise ValueError('GM01 uniform scale')
            mw,mh=gm.roi.geometry(w,h);mapped=np.full((mh,mw),quant_scale,np.uint8)
        else:mapped=gm.roi.check_map(scale_map,w,h)
        began=time.perf_counter_ns();cache=self._cache
        compatible=(not key and cache is not None and cache['epoch']==self.epoch and
                    cache['reference_id']==self.anchor_id and cache['anchor'] is self._anchor and
                    cache['shape']==a.shape and cache['mode']==mode and np.array_equal(cache['scale_map'],mapped))
        equal=bool(compatible and np.array_equal(cache['source'],a))
        compare_ms=(time.perf_counter_ns()-began)/1e6
        if equal:
            fields=list(cache['header']);fields[4]=frame_id
            body=gm.HEADER.pack(*fields)+cache['payload'];packet=body+struct.pack('<I',zlib.crc32(body))
            self.pending[frame_id]={'key':False,'planes':None,'expected_rgb_sha256':None,
                                    'packet':packet,'reference_id':self.anchor_id}
            self.last_issued=frame_id;self._generation+=1;self.peak_pending=max(self.peak_pending,len(self.pending))
        else:
            packet=super().prepare(a,frame_id,scale_map=mapped,force_key=force_key,mode=mode)
            if key:self._cache=None
            else:
                source=a.copy();source.setflags(write=False);m=mapped.copy();m.setflags(write=False)
                self._cache={'epoch':self.epoch,'reference_id':self.anchor_id,'anchor':self._anchor,
                    'shape':a.shape,'mode':mode,'scale_map':m,'source':source,
                    'header':gm.HEADER.unpack_from(packet),'payload':packet[gm.HEADER.size:-4]}
        self.last_memo_info={'hit':equal,'key':key,'comparison_ms':compare_ms,
            'service_ms':(time.perf_counter_ns()-started)/1e6,'cached_bytes':self.cache_bytes(),
            'forward_transform_calls':0 if equal else 3,
            'scope':'Exactlastsource/map/ACKkey/modeequality; fullpacketstillsent, no newreference/wiremode'}
        return packet

    def ack(self,frame_id,*,epoch):
        prior=self._anchor
        ok=super().ack(frame_id,epoch=epoch)
        if self._anchor is not prior:self._cache=None
        return ok

    def expire(self,frame_id):
        prior=self._anchor
        ok=super().expire(frame_id)
        if self._anchor is not prior:self._cache=None
        return ok

    def cache_bytes(self):
        if self._cache is None:return 0
        return self._cache['source'].nbytes+self._cache['scale_map'].nbytes+len(self._cache['payload'])+gm.HEADER.size
