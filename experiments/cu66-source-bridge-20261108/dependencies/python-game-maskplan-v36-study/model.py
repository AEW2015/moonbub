"""Compile fixed opaque geometry once, then apply owned canonical plane copies.

Host Python component experiment. No ESP32 image allocation or FPGA claim.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Plan:
    shape: tuple
    runs: tuple
    blocks: tuple


def compile_plan(shape, rectangles):
    if (not isinstance(shape, (tuple, list)) or len(shape) != 2 or
            any(type(v) is not int or v < 2 or v % 2 for v in shape)):
        raise ValueError('even integer luma geometry')
    height, width = shape
    covered = np.zeros((height, width), dtype=bool)
    try:
        rectangles = tuple(rectangles)
    except TypeError as exc:
        raise ValueError('rectangle sequence') from exc
    for rect in rectangles:
        if not isinstance(rect, (tuple, list)) or len(rect) != 4:
            raise ValueError('rectangle fields')
        x, y, w, h = rect
        if (any(type(v) is not int for v in rect) or min(x, y) < 0 or
                min(w, h) <= 0 or x+w > width or y+h > height):
            raise ValueError('bounded positive rectangle')
        covered[y:y+h, x:x+w] = True
    missing = np.pad((~covered).astype(np.int64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    all_runs, block_counts = [], []
    for axis in range(3):
        ph, pw = (height, width) if axis == 0 else (height//2, width//2)
        rows, blocks = [], 0
        for by in range(0, ph-7, 8):
            spans = []
            for bx in range(0, pw-7, 8):
                # A chroma sample i contributes at2*i-1,2*i,2*i+1;
                # clamp the first/last footprint to the RGB image.
                if axis == 0:
                    x0, y0, x1, y1 = bx, by, bx+8, by+8
                else:
                    x0, y0 = max(0, 2*bx-1), max(0, 2*by-1)
                    x1 = min(width, 2*(bx+8))
                    y1 = min(height, 2*(by+8))
                absent = missing[y1, x1]-missing[y0, x1]-missing[y1, x0]+missing[y0, x0]
                if absent == 0:
                    blocks += 1
                    if spans and spans[-1][1] == bx:
                        spans[-1] = (spans[-1][0], bx+8)
                    else:
                        spans.append((bx, bx+8))
            rows.extend((y, x0, x1) for y in range(by, by+8) for x0, x1 in spans)
        all_runs.append(tuple(rows));block_counts.append(blocks)
    return Plan(tuple(shape), tuple(all_runs), tuple(block_counts))


def apply_plan(planes, plan):
    """Validate all inputs before mutation; copy all planes, then write128."""
    if not isinstance(plan, Plan):
        raise ValueError('compiled Plan required')
    h, w = plan.shape
    expected = ((h, w), (h//2, w//2), (h//2, w//2))
    if not isinstance(planes, (tuple, list)) or len(planes) != 3:
        raise ValueError('three source planes')
    for plane, shape in zip(planes, expected, strict=True):
        if (not isinstance(plane, np.ndarray) or plane.shape != shape or
                plane.dtype.kind not in 'iu' or np.any(plane < 0) or np.any(plane > 255)):
            raise ValueError('bounded integer420 planes')
    out = tuple(plane.copy() for plane in planes)
    for plane, runs in zip(out, plan.runs, strict=True):
        for y, x0, x1 in runs:
            plane[y, x0:x1] = 128
    return out
