"""Canonical SHA128 from ordered 8x8 uint8 tiles, one eight-row strip.

This is a functional reorder component. It does not model a SHA circuit's
clocking, ready/valid, DSP use or bank publication. The caller supplies already
normalized canonical samples and checks the final expected content tag.
"""
import hashlib
import struct
import numpy as np

SHAPES=((480,720),(240,360),(240,360))
DOMAINS=('CS66_i16','CU66_u8')

class TileHash:
    def __init__(self,domain):
        if domain not in DOMAINS:raise ValueError('explicit fixed canonical domain')
        self._domain=domain;self._hash=hashlib.sha256(struct.pack('<HH',720,480))
        self.plane=0;self.y=0;self.x=0;self.strip=np.empty((8,720),np.uint8)
        self.failed=False;self.finished=False;self._tag=None
        self.tiles=0;self.samples=0;self.rows=0;self.max_strip_bytes=self.strip.nbytes
        self.serialized_bytes=4;self.max_serialized_row_bytes=0

    @property
    def domain(self):return self._domain

    def _fail(self,message):
        self.failed=True
        raise ValueError(message)

    def feed(self,plane,y,x,tile):
        if self.failed or self.finished:raise ValueError('closed/poisoned frame hash')
        if self.plane>=3:self._fail('extra tile after complete planes')
        if any(type(v)is not int for v in (plane,y,x)) or (plane,y,x)!=(self.plane,self.y,self.x):
            self._fail('exact planar tile-raster identity/order')
        if not isinstance(tile,np.ndarray) or tile.shape!=(8,8) or tile.dtype!=np.uint8:
            self._fail('already-normalized uint8 8x8 tile required; no casts/truncation')
        # Copy input ownership before returning; previous input tiles may change.
        self.strip[:,x:x+8]=tile
        self.tiles+=1;self.samples+=64;self.x+=8
        height,width=SHAPES[self.plane]
        if self.x==width:
            for row in self.strip[:,:width]:
                payload=(row.astype('<u2').tobytes() if self.domain=='CS66_i16' else row.tobytes())
                self._hash.update(payload);self.serialized_bytes+=len(payload);self.rows+=1
                self.max_serialized_row_bytes=max(self.max_serialized_row_bytes,len(payload))
            self.x=0;self.y+=8
            if self.y==height:
                self.plane+=1;self.y=0
                # Reuse one maximum-width strip across Y/U/V. No second
                # plane-transition strip allocation; unused columns are not hashed.
                if self.plane==3:self.strip=None

    def finish(self):
        if self.failed:raise ValueError('poisoned frame hash cannot publish')
        if self.plane!=3 or self.x or self.y:self._fail('incomplete canonical planes')
        if not self.finished:self._tag=self._hash.digest()[:16];self.finished=True
        return self._tag

    def work(self):
        return dict(tiles=self.tiles,canonical_samples=self.samples,rows_serialized=self.rows,
                    serialized_bytes=self.serialized_bytes,maximum_strip_data_bytes=self.max_strip_bytes,
                    maximum_serialized_row_bytes=self.max_serialized_row_bytes,
                    retained_strip_data_bytes=0 if self.strip is None else self.strip.nbytes,
                    failed=self.failed,finished=self.finished,
                    full_frame_staged=False,hardware_cycle_or_fit_proven=False)
