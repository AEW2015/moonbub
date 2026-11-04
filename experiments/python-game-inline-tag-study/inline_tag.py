"""Fail-closed canonical YUV publication tag from ordered tiles and one stripe."""
import hashlib
import struct
import numpy as np

class StripeTagger:
    """Consumes Y/Cb/Cr raster tiles; publishes a tag only on explicit finalize.

    The input producer owns each source tile. This class retains no source tile
    or full plane, only one <=8-row int16 stripe plus hash/control state.
    """
    def __init__(self,width,height):
        if (type(width) is not int or type(height) is not int or min(width,height)<2
                or width%2 or height%2 or max(width,height)>4096):
            raise ValueError('bounded even dimensions')
        self.width,self.height=width,height
        self._shapes=((height,width),(height//2,width//2),(height//2,width//2))
        self._stripe=np.empty((min(8,height),width),dtype='<i2')
        self.stripe_storage_bytes=self._stripe.nbytes
        self.peak_stripe_storage_bytes=self.stripe_storage_bytes
        self._sha=hashlib.sha256(struct.pack('<HH',width,height))
        self.canonical_bytes_hashed=4;self.tiles_received=0;self.rows_hashed=0
        self._plane=0;self._y=0;self._x=0;self._failed=False;self._published=None
    @property
    def tag(self):
        if self._published is None:raise ValueError('tag not published')
        return self._published
    def _reject(self,message):
        self._failed=True
        raise ValueError(message)
    def push(self,plane,y,x,tile):
        if self._published is not None:raise ValueError('already finalized')
        if self._failed:raise ValueError('failed tile stream')
        if (type(plane) is not int or type(y) is not int or type(x) is not int
                or (plane,y,x)!=(self._plane,self._y,self._x) or self._plane>=3):
            self._reject('out-of-order or extra tile')
        ph,pw=self._shapes[plane];rh,rw=min(8,ph-y),min(8,pw-x)
        if (not isinstance(tile,np.ndarray) or tile.dtype.kind!='i' or tile.dtype.itemsize!=2
                or tile.shape!=(rh,rw)):
            self._reject('exact int16 tile geometry')
        if int(tile.min())<0 or int(tile.max())>255:
            self._reject('canonical reconstructed sample range')
        self._stripe[:rh,x:x+rw]=tile
        self.tiles_received+=1;self._x+=rw
        if self._x==pw:
            for row in range(rh):
                # One contiguous row view; no tobytes/full-stripe copy.
                self._sha.update(memoryview(self._stripe[row,:pw]).cast('B'))
                self.canonical_bytes_hashed+=2*pw;self.rows_hashed+=1
            self._x=0;self._y+=rh
            if self._y==ph:self._plane+=1;self._y=0
    def finalize(self):
        if self._published is not None:raise ValueError('already finalized')
        if self._failed:raise ValueError('failed tile stream')
        if self._plane!=3 or self._x or self._y:self._reject('truncated tile stream')
        self._published=self._sha.digest()[:16]
        return self._published


def tiles(planes):
    """Simulated producer reads already reconstructed planes; no copy or fusion."""
    for plane,p in enumerate(planes):
        for y in range(0,p.shape[0],8):
            for x in range(0,p.shape[1],8):
                yield plane,y,x,p[y:y+8,x:x+8]


def compute(planes):
    h,w=planes[0].shape;tagger=StripeTagger(w,h)
    for args in tiles(planes):tagger.push(*args)
    tag=tagger.finalize()
    return tag,dict(stripe_storage_bytes=tagger.stripe_storage_bytes,
                    peak_stripe_storage_bytes=tagger.peak_stripe_storage_bytes,
                    canonical_bytes_hashed=tagger.canonical_bytes_hashed,
                    tiles_received=tagger.tiles_received,rows_hashed=tagger.rows_hashed)
