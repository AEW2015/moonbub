"""Whole-transform source masking under an exact opaque RGB HUD union.

No decoder operation is changed.  Scalar reconstruction dependencies determine
which RGB positions each chroma sample can influence, including edge clamps.
"""
import numpy as np


def scalar_axis_reads(position, chroma_length):
    """Indices read by the frozen right/below 2x upsampler on one axis."""
    first = position // 2
    return (first, min(first + 1, chroma_length - 1)) if position % 2 else (first,)


def axis_support(chroma_length):
    """Independently enumerate read dependencies; do not assume halo offsets."""
    support = [[] for _ in range(chroma_length)]
    for pixel in range(chroma_length * 2):
        for sample in set(scalar_axis_reads(pixel, chroma_length)):
            support[sample].append(pixel)
    return tuple((min(values), max(values) + 1) for values in support)


def coverage(shape, rectangles):
    h, w = shape
    covered = np.zeros((h, w), dtype=bool)
    try:
        rectangles = tuple(rectangles)
    except TypeError as exc:
        raise ValueError('opaque rectangle sequence') from exc
    for rect in rectangles:
        if not isinstance(rect, (tuple, list)) or len(rect) != 4:
            raise ValueError('four integer rectangle fields')
        x, y, rw, rh = rect
        if any(type(v) is not int for v in rect) or min(x, y) < 0 or min(rw, rh) <= 0 or x + rw > w or y + rh > h:
            raise ValueError('bounded positive integer opaque rectangle')
        covered[y:y + rh, x:x + rw] = True
    return covered


def mask_source(planes, rectangles, policy='core8', *, work=None):
    """Return three owned planes; replace only complete safe 8x8 blocks by128.

    ``core8`` masks Y/Cb/Cr; ``luma8`` masks Y only.  An optional mutable
    ``work`` dict receives block/store counts.  Source arrays are never changed.
    Odd/partial rectangles and overlapping rectangle unions are valid; partial
    transform blocks at plane edges are always preserved.
    """
    if policy not in ('core8', 'luma8'):
        raise ValueError('explicit core8 or luma8 policy')
    if not isinstance(planes, (tuple, list)) or len(planes) != 3 or any(not isinstance(p, np.ndarray) or p.ndim != 2 for p in planes):
        raise ValueError('three planar arrays')
    h, w = planes[0].shape
    if min(h, w) < 2 or h % 2 or w % 2 or [p.shape for p in planes] != [(h, w), (h // 2, w // 2), (h // 2, w // 2)]:
        raise ValueError('even 420 source')
    if any(p.dtype.kind not in 'iu' or np.any(p < 0) or np.any(p > 255) for p in planes):
        raise ValueError('eight-bit integer source')
    covered = coverage((h, w), rectangles)
    missing = np.pad((~covered).astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    def safe(x0, y0, x1, y1):
        return missing[y1, x1] - missing[y0, x1] - missing[y1, x0] + missing[y0, x0] == 0
    xs, ys = axis_support(w // 2), axis_support(h // 2)
    out = tuple(p.copy() for p in planes)
    counts = []
    for axis, plane in enumerate(out):
        count = 0
        if not axis or policy == 'core8':
            for y in range(0, plane.shape[0] - 7, 8):
                for x in range(0, plane.shape[1] - 7, 8):
                    bounds = (x, y, x + 8, y + 8) if not axis else (xs[x][0], ys[y][0], xs[x + 7][1], ys[y + 7][1])
                    if safe(*bounds):
                        plane[y:y + 8, x:x + 8] = 128
                        count += 1
        counts.append(count)
    if work is not None:
        work.update(policy=policy, masked_blocks=counts, constant_stores=sum(counts) * 64,
                    luma_constant_stores=counts[0] * 64, chroma_constant_stores=sum(counts[1:]) * 64,
                    actual_owned_array_bytes=sum(p.nbytes for p in out), logical_owned_u8_bytes=sum(p.size for p in out))
    return out
