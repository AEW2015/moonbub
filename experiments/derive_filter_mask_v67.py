#!/usr/bin/env python3
"""Derive and verify a compact fixed HUD exclusion-mask program."""
import argparse
import hashlib
import importlib.util
import json
import struct
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve()
OUT = ROOT / 'docs/prototype-v67-mask-program.json'
RECTS = ((24, 56, 152, 16), (24, 88, 152, 16),
         (168, 360, 320, 24), (168, 392, 240, 16))
PIN_PATHS = (
    'experiments/derive_filter_mask_v67.py',
    'experiments/python-game-filter-qual-v67-study/helpers.py',
    'experiments/python-game-display-filter-v60-study/model.py',
    'experiments/python-game-filtered-scanout-v64-study/model.py',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def load_qual_helper():
    path = ROOT / 'experiments/python-game-filter-qual-v67-study/helpers.py'
    spec = importlib.util.spec_from_file_location('mask67_qual_helpers', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inside(x, y):
    return any(rx <= x < rx + rw and ry <= y < ry + rh
               for rx, ry, rw, rh in RECTS)


def owned_row(y):
    row = np.fromiter((inside(x, y) for x in range(720)), dtype=np.bool_, count=720)
    assert row.nbytes == 720 and row.flags.owndata
    row.setflags(write=False)
    return row


def build():
    flat = tuple(v for rect in RECTS for v in rect)
    assert len(flat) == 16 and all(type(v) is int and 0 <= v <= 0xffff for v in flat)
    packed_rectangles = struct.pack('<16H', *flat)
    assert len(packed_rectangles) == 32
    qual = load_qual_helper()
    frozen = qual.excluded()
    assert frozen.shape == (480, 720) and frozen.dtype == np.bool_
    assert not frozen.flags.writeable

    pixel_hash = hashlib.sha256()
    pixel_count = 0
    for y in range(480):
        row = owned_row(y)
        assert np.array_equal(row, frozen[y])
        pixel_hash.update(row.tobytes())
        pixel_count += int(np.count_nonzero(row))
    assert pixel_count == 16384
    assert pixel_hash.hexdigest() == sha(frozen.tobytes(order='C'))

    horizontal_hash = hashlib.sha256()
    horizontal_count = horizontal_blocked = 0
    for y in range(480):
        row = owned_row(y)
        for x in range(8, 720, 8):
            direct = any(inside(q, y) for q in (x - 2, x - 1, x, x + 1))
            expected = bool(np.any(frozen[y, x - 2:x + 2]))
            assert direct == expected
            horizontal_hash.update(bytes((int(direct),)))
            horizontal_count += 1
            horizontal_blocked += int(direct)

    vertical_hash = hashlib.sha256()
    vertical_count = vertical_blocked = 0
    for y in range(8, 480, 8):
        for x in range(720):
            direct = any(inside(x, q) for q in (y - 2, y - 1, y, y + 1))
            expected = bool(np.any(frozen[y - 2:y + 2, x]))
            assert direct == expected
            vertical_hash.update(bytes((int(direct),)))
            vertical_count += 1
            vertical_blocked += int(direct)

    return dict(
        schema='gamebub-v67-fixed-display-exclusion-mask',
        profile=dict(epoch=25, coded_width=720, coded_height=480,
                     coordinate_origin='top-left', rectangle_edges='inclusive-left/top, exclusive-right/bottom'),
        rectangles_xywh_u16=[list(r) for r in RECTS],
        packed_rectangles_little_endian_hex=packed_rectangles.hex(),
        logical_rectangle_payload_bytes=len(packed_rectangles),
        derived_row_mask=dict(width=720, bytes=720, dtype='bool/u8 logical byte per x',
                              allocation='one owned row at a time; readonly while queried'),
        verification=dict(
            frozen_reference='qual67.excluded() from frozen normalized HUD profile',
            frozen_mask_pixels=pixel_count,
            pixels_checked=480 * 720,
            predicate_matches_all_pixels=True,
            row_major_mask_sha256=pixel_hash.hexdigest(),
            horizontal_four_tap_footprints_checked=horizontal_count,
            horizontal_blocked_footprints=horizontal_blocked,
            horizontal_blocked_sha256=horizontal_hash.hexdigest(),
            vertical_four_tap_footprints_checked=vertical_count,
            vertical_blocked_footprints=vertical_blocked,
            vertical_blocked_sha256=vertical_hash.hexdigest(),
        ),
        source_sha256={p: file_sha(ROOT / p) for p in PIN_PATHS},
        scope=[
            'Fixed four-rectangle geometry is specific to the epoch25 720x480 HUD/exclusion profile.',
            'The program/query derives one owned 720-byte row at a time; only the frozen validation oracle materializes a full 345600-byte boolean mask.',
            'This validates the compact descriptor, not actual process allocation, stack/heap, or total hardware memory bounds.',
            'Four uint16 xywh rectangles use 32 logical payload bytes; object/layout overhead and hardware address logic are excluded.',
            'Pixel and horizontal/vertical four-tap footprint results are checked against the frozen full excluded-mask oracle.',
            'A changed HUD or coded geometry must regenerate and reverify this program.',
            'No FPGA cycles, synthesis, BRAM fit, ESP32 work or physical throughput are measured.',
        ],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = build()
    if args.check:
        assert json.loads(OUT.read_text()) == result
    else:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(pixels_checked=result['verification']['pixels_checked'],
                          rectangle_bytes=result['logical_rectangle_payload_bytes'],
                          row_bytes=result['derived_row_mask']['bytes'],
                          horizontal_footprints=result['verification']['horizontal_four_tap_footprints_checked'],
                          vertical_footprints=result['verification']['vertical_four_tap_footprints_checked'],
                          check_mode=args.check)))


if __name__ == '__main__':
    main()
