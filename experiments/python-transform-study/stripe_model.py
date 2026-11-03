"""Decoded-sample stripe oracle, not a compressed streaming decoder.

The source supplies already reconstructed Y/Cb/Cr sample rows. One overlapping
chroma row reproduces FT01's forward bilinear interpolation exactly. FT01's
plane-first packet cannot supply these rows in this order without retaining,
reordering or re-decoding data. Sample payload counts exclude coefficient/IDCT
work RAM, output buffers, FIFOs, Python temporaries and controller resources.
"""
import numpy as np


def render_stripes(planes, rows=16):
    """Yield (row_start, RGB uint8 stripe, retained sample payload bytes)."""
    if type(rows) is not int or rows <= 0 or rows % 2:
        raise ValueError('stripe height must be positive and even')
    if len(planes) != 3:
        raise ValueError('three sample planes required')
    y, cb, cr = [np.asarray(p) for p in planes]
    if y.ndim != 2:
        raise ValueError('two-dimensional sample planes required')
    h, w = y.shape
    if h <= 0 or w <= 0 or h % 2 or w % 2 or h*w > 720*480:
        raise ValueError('bounded even dimensions required')
    if cb.shape != (h//2, w//2) or cr.shape != cb.shape:
        raise ValueError('chroma shape')
    if any(p.dtype.kind not in 'iu' or np.any(p < 0) or np.any(p > 255) for p in (y, cb, cr)):
        raise ValueError('decoded samples must be integers in 0..255')
    for start in range(0, h, rows):
        end = min(h, start+rows)
        sample_y = y[start:end].astype(np.uint8, copy=True)
        first, last = start//2, min(h//2, end//2+1)
        sample_cb = cb[first:last].astype(np.uint8, copy=True)
        sample_cr = cr[first:last].astype(np.uint8, copy=True)
        height = end-start

        def up(sample):
            p = sample.astype(np.int32)
            right = np.concatenate((p[:, 1:], p[:, -1:]), axis=1)
            horizontal = np.empty((len(p), w), np.int32)
            horizontal[:, ::2] = p
            horizontal[:, 1::2] = (p+right+1)//2
            count = height//2
            above = horizontal[:count]
            below = horizontal[np.minimum(np.arange(count)+1, len(horizontal)-1)]
            out = np.empty((height, w), np.int32)
            out[::2] = above
            out[1::2] = (above+below+1)//2
            return out-128

        yy = sample_y.astype(np.int32)
        u, v = up(sample_cb), up(sample_cr)
        rgb = np.clip(np.stack((yy+((359*v+128)>>8),
                               yy-((88*u+183*v+128)>>8),
                               yy+((454*u+128)>>8)), axis=-1), 0, 255).astype(np.uint8)
        yield start, rgb, sample_y.nbytes+sample_cb.nbytes+sample_cr.nbytes


def sample_layout(width=720, height=480, rows=16):
    """Report only the declared decoded-sample payload/overlap allocation."""
    if min(width, height, rows) <= 0 or any(v % 2 for v in (width, height, rows)):
        raise ValueError('positive even geometry required')
    if width*height > 720*480:
        raise ValueError('geometry exceeds study bound')
    footprints = []
    for start in range(0, height, rows):
        end = min(height, start+rows)
        chroma_rows = min(height//2, end//2+1)-start//2
        footprints.append((end-start)*width+chroma_rows*width)
    return {'width': width, 'height': height, 'stripe_rows': rows,
            'full_decoded_yuv420_bytes': width*height*3//2,
            'peak_decoded_sample_payload_bytes': max(footprints),
            'stripes': len(footprints),
            'extra_chroma_overlap_sample_bytes': sum(footprints)-width*height*3//2,
            'excluded': 'coefficient/IDCT work RAM, output staging, FIFO/control and Python temporaries',
            'availability_assumption': 'predecoded Y/Cb/Cr rows including next chroma row; FT01 plane order does not provide this'}
