"""Exact RGB565 display patches for a versioned unified codec envelope.

Patch selection knows only its byte/work budget, never reference state. All
patches validate before the caller may publish a base reference. The display
overlay never modifies the base RGB input or any YUV prediction plane.
"""
from dataclasses import dataclass
import math
from pathlib import Path
import struct
import sys
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-game-ui-cache-study'))
import ui_cache as frozen_cache

hybrid = frozen_cache.hybrid
row, hp, gm = hybrid.row, hybrid.hp, hybrid.gm
COMPACT = hybrid.COMPACT
LENGTH = struct.Struct('<I')
MAX_PATCHES = 4
MIN_PATCH_BYTES = row.HEADER.size + 4


def _patches(packets):
    if type(packets) not in (tuple, list) or len(packets) > MAX_PATCHES:
        raise ValueError('bounded UI packet sequence')
    if any(type(p) is not bytes or len(p) < MIN_PATCH_BYTES for p in packets):
        raise ValueError('UI immutable patch bytes/type/length')
    return tuple(packets)


def _header(packet, width, height):
    """Validate bounded common header/CRC; do not allocate decoded pixel words."""
    if type(packet) is not bytes or len(packet) < MIN_PATCH_BYTES:
        raise ValueError('UI patch type/truncation')
    magic, version, mode, x, y, w, h, colors, pixels, length = row.HEADER.unpack_from(packet)
    rect = hp._rect((x, y, w, h), width, height)
    if magic not in (b'HP01', b'HR01') or version != 1 or pixels != w*h:
        raise ValueError('UI patch profile/pixels')
    if len(packet) != row.HEADER.size + colors*2 + length + 4 or colors > min(256, pixels):
        raise ValueError('UI exact patch length/palette bound')
    if magic == b'HP01':
        if mode not in (0, *hp.MODES):
            raise ValueError('UI HP01 mode')
        if mode == 0:
            if colors or length != 2*pixels:
                raise ValueError('UI HP01 raw geometry')
        elif not 1 <= colors <= min(256, pixels) or hp._mode(colors) != mode or length != (pixels*mode+7)//8:
            raise ValueError('UI HP01 index geometry')
        if len(packet) > row.HEADER.size+512+2*pixels+4:
            raise ValueError('UI HP01 payload bound')
    else:
        if mode not in (row.RAW, row.WORD_RUNS, row.INDEX_RUNS) or length > h*(2+3*w):
            raise ValueError('UI HR01 mode/payload bound')
        if mode == row.RAW and (colors or length != 2*pixels):
            raise ValueError('UI HR01 raw geometry')
        if mode == row.WORD_RUNS and colors:
            raise ValueError('UI HR01 word-run palette')
        if mode == row.INDEX_RUNS and not colors:
            raise ValueError('UI HR01 index palette')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('UI patch CRC')
    return rect


def validate_patches(packets, width, height):
    """Fully validate all patches before any caller base/reference publication.

Every geometry/CRC/header and pairwise overlap is checked before invoking a
decoder that allocates pixel arrays. Full HP01/HR01 payload parsing then occurs
for every patch. Returned words are read-only; no input data is modified.
"""
    gm.roi.geometry(width, height)
    packets = _patches(packets)
    rects = [_header(p, width, height) for p in packets]
    hp._disjoint(rects)
    decoded = []
    for packet, rect in zip(packets, rects):
        info = row.decode_any(packet, width, height)
        if tuple(info['rect']) != rect:
            raise AssertionError('UI header/decoder geometry mismatch')
        decoded.append({**info, 'format': packet[:4].decode()})
    return tuple(decoded)


def apply_patches(base_rgb, validated):
    """Return display RGB without changing base RGB/YUV or reference state."""
    a = gm.ft._check_rgb(base_rgb)
    h, w = a.shape[:2]
    if type(validated) not in (tuple, list) or len(validated) > MAX_PATCHES:
        raise ValueError('bounded validated UI sequence')
    if not validated:
        return a.copy()
    rects = []
    for patch in validated:
        if type(patch) is not dict or 'rect' not in patch or 'words' not in patch:
            raise ValueError('validated UI patch shape')
        rect = hp._rect(patch['rect'], w, h)
        words = patch['words']
        if not isinstance(words, np.ndarray) or words.dtype != np.uint16 or words.shape != (rect[3], rect[2]):
            raise ValueError('validated UI word geometry')
        rects.append(rect)
    hp._disjoint(rects)
    words = hp.corpus.rgb565(a)
    for patch, (x, y, rw, rh) in zip(validated, rects):
        words[y:y+rh, x:x+rw] = patch['words']
    return hp.corpus.expand565(words)


def pack_patches(packets):
    """Length-prefix trusted immutable patch outputs; parsing validates content."""
    packets = _patches(packets)
    return b''.join(LENGTH.pack(len(p))+p for p in packets)


def parse_patches(data, count, width, height):
    """Canonical complete UI section: count exact prefixes, no trailing padding."""
    gm.roi.geometry(width, height)
    if type(data) is not bytes or type(count) is not int or not 0 <= count <= MAX_PATCHES:
        raise ValueError('UI section type/count')
    bound = 3*width*height + MAX_PATCHES*(4+row.HEADER.size+4+512+2*height)
    if len(data) > bound:
        raise ValueError('UI aggregate payload bound')
    packets = []; position = 0
    for _ in range(count):
        if position+4 > len(data):
            raise ValueError('UI missing length prefix')
        length = LENGTH.unpack_from(data, position)[0]; position += 4
        if length < MIN_PATCH_BYTES or position+length > len(data):
            raise ValueError('UI section patch length')
        packets.append(data[position:position+length]); position += length
    if position != len(data):
        raise ValueError('UI trailing patch bytes')
    return validate_patches(tuple(packets), width, height)


@dataclass(frozen=True)
class Selection:
    patches: tuple
    details: dict
    used_bytes: int
    service_ms: float
    selected_pixels: int
    requested_pixels: int
    deadline_hit: bool


class PatchSelector:
    """Bounded priority selection with exact current-word payload reuse."""
    def __init__(self, rectangles=COMPACT, patch_policy='adaptive_row', max_entries=4):
        if type(rectangles) is not tuple or len(rectangles) > MAX_PATCHES or any(type(r) is not tuple for r in rectangles):
            raise ValueError('bounded immutable UI priorities')
        if patch_policy not in ('hp01', 'adaptive_row'):
            raise ValueError('UI patch policy')
        self.rectangles = rectangles
        self.patch_policy = patch_policy
        self.cache = frozen_cache.PatchCache(max_entries)

    def select(self, rgb, byte_budget, *, max_attempts=4, work_budget_ms=None,
               spent_before_ms=0.0, clock_ns=time.perf_counter_ns):
        if type(byte_budget) is not int or byte_budget < 0:
            raise ValueError('nonnegative complete UI byte budget')
        if type(max_attempts) is not int or not 0 <= max_attempts <= MAX_PATCHES:
            raise ValueError('bounded UI attempt count')
        if (not math.isfinite(spent_before_ms) or spent_before_ms < 0
                or work_budget_ms is not None and (not math.isfinite(work_budget_ms) or work_budget_ms < 0)):
            raise ValueError('UI observed work budget')
        started = previous = clock_ns()
        if not math.isfinite(started):
            raise ValueError('finite UI clock')
        def stamp():
            nonlocal previous
            value = clock_ns()
            if not math.isfinite(value) or value < previous:
                raise ValueError('monotonic UI clock')
            previous = value
            return value
        def elapsed(): return (stamp()-started)/1e6
        def expired(): return work_budget_ms is not None and spent_before_ms+elapsed() >= work_budget_ms
        a = gm.ft._check_rgb(rgb); h, w = a.shape[:2]
        rects = [hp._rect(r, w, h) for r in self.rectangles]
        hp._disjoint(rects)
        requested = sum(r[2]*r[3] for r in rects)
        attempts = []; patches = []; selected = []; used = 0; deadline = False
        reason = 'no_patch_fits'
        for index, rect in enumerate(rects):
            if len(attempts) >= max_attempts:
                reason = 'attempt_limit'; break
            if expired():
                deadline = True; reason = 'work_budget'; break
            # A valid patch is at least a header+CRC; avoid provably impossible
            # work, without predicting the actual compression ratio.
            if byte_budget-used < 4+MIN_PATCH_BYTES:
                reason = 'byte_budget_below_minimum'; break
            began = stamp()
            packet, candidate = self.cache(a, rect, self.patch_policy)
            encode_ms = (stamp()-began)/1e6
            began = stamp()
            info = validate_patches((packet,), w, h)[0]
            validate_ms = (stamp()-began)/1e6
            if tuple(info['rect']) != rect:
                raise ValueError('UI encoder changed rectangle')
            required = 4+len(packet)
            fits = used+required <= byte_budget
            attempt = dict(priority_index=index, rect=rect, patch_bytes=len(packet),
                           framed_bytes=required, projected_ui_bytes=used+required, fits=fits,
                           candidate_details=candidate, encode_ms=encode_ms, validate_ms=validate_ms,
                           selected_in_output=False)
            attempts.append(attempt)
            if expired():
                deadline = True; reason = 'work_budget'; break
            if fits:
                patches.append(packet); used += required
                selected.append(dict(priority_index=index, rect=rect, format=packet[:4].decode(),
                                     pixels=rect[2]*rect[3], patch_bytes=len(packet)))
        if deadline:
            # Late observed budget fallback keeps all paid attempted work.
            patches, selected, used = [], [], 0
        if patches: reason = 'patched'
        keep = {item['priority_index'] for item in selected}
        for attempt in attempts: attempt['selected_in_output'] = attempt['priority_index'] in keep
        duration = elapsed()
        details = dict(reason=reason, attempts=tuple(attempts), selected=tuple(selected),
                       requested_pixels=requested, selected_pixels=sum(p['pixels'] for p in selected),
                       byte_budget=byte_budget, used_bytes=used, deadline_hit=deadline,
                       unattempted_rectangles=len(rects)-len(attempts),
                       cache_entries=len(self.cache._entries), persistent_cache_bytes=self.cache.persistent_bytes(),
                       observed_total_ms=spent_before_ms+duration,
                       scope='Exact original RGB565 selected patches; full current validation and framing costs, no YUV reference mutation')
        return Selection(tuple(patches), details, used, duration, details['selected_pixels'], requested, deadline)
