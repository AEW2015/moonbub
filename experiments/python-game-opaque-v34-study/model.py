"""Host-only source formation under the fixed exact opaque HUD profile."""
import numpy as np

def mask_source(planes, rectangles, *, preserve_chroma_border=True):
    if len(planes) != 3:
        raise ValueError('three source planes')
    h, w = planes[0].shape
    if w % 2 or h % 2 or [p.shape for p in planes] != [(h,w),(h//2,w//2),(h//2,w//2)]:
        raise ValueError('even 420 source')
    if any(p.dtype.kind not in 'iu' or np.any(p<0) or np.any(p>255) for p in planes):
        raise ValueError('eight-bit integer source')
    out = tuple(p.copy() for p in planes)
    for x, y, rw, rh in rectangles:
        if any(type(v) is not int for v in (x,y,rw,rh)) or min(x,y)<0 or min(rw,rh)<=0 or any(v%2 for v in (x,y,rw,rh)) or x+rw>w or y+rh>h:
            raise ValueError('bounded even opaque rectangle')
        for axis, p in enumerate(out):
            scale = 1 if axis == 0 else 2
            # Frozen chroma upsampling looks right/below: first chroma row and
            # column influence RGB just above/left of the opaque rectangle.
            border = 1 if axis and preserve_chroma_border else 0
            p[y//scale+border:(y+rh)//scale,x//scale+border:(x+rw)//scale] = 128
    return out
