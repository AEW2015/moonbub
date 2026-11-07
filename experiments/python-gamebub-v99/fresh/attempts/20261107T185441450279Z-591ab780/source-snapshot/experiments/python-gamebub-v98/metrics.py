"""Common RGB565 display-domain diagnostics, with explicit masks and fences.

ROI error is a pixel proxy, not an OCR/readability or perceptual-quality score.
Temporal error measures changes in reconstruction error, not motion compensation.
"""
import hashlib
import math
import numpy as np


def displayed(rgb):
    a = np.asarray(rgb)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError('uint8 RGB required')
    r = a[..., 0] >> 3
    g = a[..., 1] >> 2
    b = a[..., 2] >> 3
    return np.stack(((r << 3) | (r >> 2), (g << 2) | (g >> 4),
                     (b << 3) | (b >> 2)), axis=-1)


def mask(shape, rectangles):
    height, width = shape[:2]
    result = np.zeros((height, width), bool)
    for x, y, w, h in rectangles:
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > width or y+h > height:
            raise ValueError('rectangle outside source')
        result[y:y+h, x:x+w] = True
    return result


def psnr(mse):
    return 10*math.log10(65025/mse) if mse else None


def sequence_quality(originals, decoded, active_rect, roi_rectangles):
    if len(originals) != len(decoded) or not len(originals):
        raise ValueError('complete equally sized sequences required')
    shape = originals[0].shape
    active = mask(shape, [active_rect])
    roi = mask(shape, roi_rectangles) & active
    regions = {'active': active, 'roi': roi, 'background': active & ~roi}
    if not all(np.any(v) for v in regions.values()):
        raise ValueError('nonempty active, ROI and background masks required')
    rows = []
    previous = None
    for index, (source, output) in enumerate(zip(originals, decoded)):
        if source.shape != shape or output.shape != shape:
            raise ValueError('geometry mismatch')
        actual = displayed(output)
        error = actual.astype(np.float64)-source.astype(np.float64)
        sq = np.mean(error*error, axis=2)
        row = {'id': index, 'display_rgb_sha256': hashlib.sha256(actual.tobytes()).hexdigest(),
               'regions': {name: {'squared_error_sum': float(sq[m].sum()),
                                   'pixels': int(m.sum()), 'mse': float(sq[m].mean()),
                                   'psnr_db': psnr(float(sq[m].mean()))}
                           for name, m in regions.items()}}
        row['temporal_error_mse'] = (None if previous is None else
            float(np.mean((error[active]-previous[active])**2)))
        previous = error
        rows.append(row)
    pooled = {}
    for name in regions:
        mse = sum(row['regions'][name]['squared_error_sum'] for row in rows)/sum(
            row['regions'][name]['pixels'] for row in rows)
        pooled[name] = {'mse': mse, 'psnr_db': psnr(mse)}
    temporal = [row['temporal_error_mse'] for row in rows[1:]]
    return {'frames': rows, 'pooled': pooled,
            'worst_active_frame_psnr_db': psnr(max(row['regions']['active']['mse'] for row in rows)),
            'temporal_error_mse_mean': float(np.mean(temporal)) if temporal else None,
            'temporal_error_mse_max': max(temporal) if temporal else None}


def distribution(values):
    a = np.asarray(values, dtype=float)
    if not len(a) or np.any(~np.isfinite(a)) or np.any(a < 0):
        raise ValueError('finite nonnegative samples required')
    return {'n': len(a), 'min': float(a.min()), 'median': float(np.median(a)),
            'p95_nearest_rank': float(np.sort(a)[math.ceil(.95*len(a))-1]),
            'max': float(a.max())}


def pareto(cases):
    """Per-source 3-objective measured frontier; no interpolation or target cost."""
    frontier = []
    for a in cases:
        dominates = lambda b: (
            b['coded_bytes'] <= a['coded_bytes'] and
            b['active_mse'] <= a['active_mse'] and b['roi_mse'] <= a['roi_mse'] and
            (b['coded_bytes'] < a['coded_bytes'] or b['active_mse'] < a['active_mse'] or
             b['roi_mse'] < a['roi_mse']))
        if not any(dominates(b) for b in cases if b is not a):
            frontier.append(a['case_id'])
    return frontier
