#!/usr/bin/env python3
"""Uncalibrated SDRAM row-locality experiment; stdlib, no RTL or timing claim."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'fpga/experiments/cu66-v79/layout-study'
TRACE = 'fpga/experiments/cu66-v76/service/trace.mem'
REFS = 'fpga/experiments/cu66-v76/service/reference.mem'
INDEX = 'experiments/cu66-native-v69/index.tsv'
DIMS = ((90, 60), (45, 30), (45, 30))
BASES = (0x080000, 0x480000, 0x880000)
OLD_OFF = (0, 172800, 216000)


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class Layout:
    def __init__(self, width=None):
        self.width = width
        self.height = None if width is None else 16 // width
        self.name = 'current_unpadded' if width is None else f'group_{width}x{self.height}'
        self.spans = []
        self.offsets = []
        end = 0
        for w, h in DIMS:
            self.offsets.append(end)
            span = w * h * 32 if width is None else ((w + width - 1) // width) * ((h + self.height - 1) // self.height) * 512
            self.spans.append(span)
            end += span
        self.words = end

    def physical_tile(self, plane, index):
        w, _ = DIMS[plane]
        if self.width is None:
            return index
        y, x = divmod(index, w)
        group = (y // self.height) * ((w + self.width - 1) // self.width) + x // self.width
        return group * 16 + (y % self.height) * self.width + x % self.width

    def logical_tile(self, plane, physical):
        w, h = DIMS[plane]
        if self.width is None:
            return physical if physical < w * h else None
        group, within = divmod(physical, 16)
        gy, gx = divmod(group, (w + self.width - 1) // self.width)
        iy, ix = divmod(within, self.width)
        x, y = gx * self.width + ix, gy * self.height + iy
        return y * w + x if x < w and y < h else None

    def addr(self, bank, plane, index, block=0):
        assert 0 <= bank < 3 and 0 <= plane < 3 and 0 <= block < 4
        assert 0 <= index < DIMS[plane][0] * DIMS[plane][1]
        return BASES[bank] + self.offsets[plane] + self.physical_tile(plane, index) * 32 + block * 8

    def transform_display(self, address):
        if 0x100000 <= address < 0x100000 + 21120:
            return address
        relative = address - BASES[0]
        assert 0 <= relative < 259200
        plane = 0 if relative < 172800 else 1 if relative < 216000 else 2
        tile, word = divmod(relative - OLD_OFF[plane], 32)
        assert word in (0, 8, 16, 24)
        return self.addr(0, plane, tile, word // 8)


def verify_layout(layout, golden):
    """Actual YUV fixture: independent inverse scatter reconstructs raster bytes."""
    image = bytearray([0xa5]) * (layout.words * 2)
    logical_plane_start = 0
    active_tiles = 0
    for plane, (w, h) in enumerate(DIMS):
        seen = set()
        for tile in range(w * h):
            physical = layout.physical_tile(plane, tile)
            assert physical not in seen
            seen.add(physical)
            ty, tx = divmod(tile, w)
            start = layout.offsets[plane] * 2 + physical * 64
            for row in range(8):
                src = logical_plane_start + (ty * 8 + row) * w * 8 + tx * 8
                image[start + row * 8:start + row * 8 + 8] = golden[src:src + 8]
            for bank, base in enumerate(BASES):
                address = layout.addr(bank, plane, tile)
                assert address % 32 == 0 and address >> 22 == base >> 22
                assert base <= address and address + 32 <= base + 0x80000
                assert address < base + layout.words
            active_tiles += 1
        logical_plane_start += w * h * 64
    restored = bytearray(len(golden))
    start_of_plane = 0
    padding_tiles = 0
    for plane, (w, h) in enumerate(DIMS):
        for physical in range(layout.spans[plane] // 32):
            index = layout.logical_tile(plane, physical)
            start = layout.offsets[plane] * 2 + physical * 64
            packed = image[start:start + 64]
            if index is None:
                assert packed == bytes([0xa5]) * 64, 'padding overwritten'
                padding_tiles += 1
                continue
            assert layout.physical_tile(plane, index) == physical
            ty, tx = divmod(index, w)
            # Restore little-endian packed x16 words, independently of writer slices.
            for word in range(32):
                low, high = packed[word * 2], packed[word * 2 + 1]
                row, pair = divmod(word, 4)
                dst = start_of_plane + (ty * 8 + row) * w * 8 + tx * 8 + pair * 2
                restored[dst], restored[dst + 1] = low, high
        start_of_plane += w * h * 64
    assert restored == golden and active_tiles == 8100
    assert sum(layout.spans) == layout.words and layout.words <= 0x80000
    if layout.width is not None:
        assert all(x % 512 == 0 for x in layout.offsets + layout.spans)
    return dict(layout=layout.name, group_width=layout.width, group_height=layout.height,
                plane_offsets_x16=layout.offsets, plane_spans_x16=layout.spans,
                allocated_bytes=layout.words * 2, active_bytes=len(golden),
                padding_bytes=padding_tiles * 64, active_tiles=active_tiles,
                padding_tiles=padding_tiles, restored_sha256=hashlib.sha256(restored).hexdigest(),
                tests='PASS_INJECTIVE_TILES_ALL_WORDS_BYTE_ORDER_PADDING_BANK_AND_HUD_BOUNDS')


class OpenRows:
    """Source-derived work approximation, not bridge/controller cycle simulation."""
    def __init__(self, refresh=750, gap=3):
        self.rows = [None] * 4
        self.time = 0
        self.next_refresh = refresh if refresh else 10**30
        self.refresh_period = refresh
        self.gap = gap
        self.count = Counter()

    def issue(self, address, write):
        assert address % 8 == 0
        if self.time >= self.next_refresh:
            self.time += 15
            self.next_refresh = self.time - 10 + self.refresh_period
            self.rows = [None] * 4
            self.count['REF'] += 1
        bank, row = address >> 22, (address >> 9) & 8191
        if self.rows[bank] != row:
            self.time += 4
            self.count['ACT'] += 1
            if self.rows[bank] is not None:
                self.time += 4
                self.count['PRE_conflict'] += 1
            self.rows[bank] = row
        else:
            self.count['row_hit'] += 1
        self.time += (13 if write else 15) + self.gap
        self.count['write' if write else 'read'] += 1


def streams(layout, display, refs):
    result = dict(display=[(layout.transform_display(a), False) for a in display],
                  reference=[(layout.addr(0, t >> 17, t & 131071, b), False) for t in refs for b in range(4)],
                  canonical_write=[(layout.addr(1, p, i, b), True) for p, (w, h) in enumerate(DIMS) for i in range(w * h) for b in range(4)],
                  hud_write=[(0x500000 + i * 8, True) for i in range(2640)],
                  hud_verify=[(0x500000 + i * 8, False) for i in range(2640)])
    assert {k: len(v) for k, v in result.items()} == dict(display=35040, reference=31224, canonical_write=32400, hud_write=2640, hud_verify=2640)
    assert sum(map(len, result.values())) * 16 == 1663104
    return result


def measure(layout, jobs, mode, quantum, refresh):
    bus = OpenRows(refresh=refresh)
    queues = [deque(x) for x in jobs.values()]
    while any(queues):
        for q in queues:
            for _ in range(min(len(q), quantum)):
                bus.issue(*q.popleft())
    return dict(layout=layout.name, stream=mode, quantum=quantum, refresh_period=refresh,
                commands=sum(bus.count[k] for k in ('read', 'write')), wire_bytes=sum(bus.count[k] for k in ('read', 'write')) * 16,
                ACT=bus.count['ACT'], PRE_conflict=bus.count['PRE_conflict'], REF=bus.count['REF'],
                row_hits=bus.count['row_hit'], service_work_cycles=bus.time,
                calibration='UNCALIBRATED_SYNTHETIC_SERVICE_WORK_NOT_LATENCY')


def csv_text(rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=list(rows[0]), lineterminator='\n')
    w.writeheader(); w.writerows(rows)
    return s.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    first = (ROOT / INDEX).read_text().splitlines()[0].split('\t')
    yuv = 'experiments/cu66-native-v69/fixtures/' + first[3] + '.yuv'
    golden = (ROOT / yuv).read_bytes()
    assert len(golden) == 518400 and hashlib.sha256(golden).hexdigest() == first[3]
    display = [int(x, 16) & 0xffffff for x in (ROOT / TRACE).read_text().splitlines()]
    refs = [int(x, 16) for x in (ROOT / REFS).read_text().splitlines()]
    assert len(display) == 35040 and len(refs) == len(set(refs)) == 7806
    layouts = [Layout()] + [Layout(w) for w in (16, 8, 4, 2, 1)]
    mappings, measures = [], []
    for layout in layouts:
        mappings.append(verify_layout(layout, golden))
        jobs = streams(layout, display, refs)
        for refresh in (0, 750):
            for name, requests in jobs.items():
                measures.append(measure(layout, {name: requests}, 'standalone_' + name, len(requests), refresh))
            for quantum in (4, 8, 16):
                measures.append(measure(layout, jobs, 'fixed_round_robin_all_streams', quantum, refresh))
    paths = [TRACE, REFS, INDEX, yuv, 'scripts/cu66-v79/layout_study.py',
             'fpga/experiments/cu66-v72/memory/cu72_sdram_controller.sv',
             'fpga/experiments/cu66-v74/memory/cu74_tile_memory.sv']
    result = dict(schema='cu79-grouped-layout-study-v1', status='PASS_MAPPING_UNCALIBRATED_SERVICE_ONLY',
        source_sha256={p: digest(p) for p in paths}, mappings=mappings, measurements=measures,
        contract=['x16 SDRAM rows contain512 words,16 contiguous64byte tiles; one open row per physical bank.',
                  'Grouped layouts pad each plane to whole16tile groups, with new plane offsets; bank and HUD bases unchanged.',
                  'Display uses exact retained V76 physical BL8 order, remapped per logical tile; HUD order unchanged.',
                  'Reference reads use exact retained SAFE identity order in immutable bank0, shared with display.',
                  'Canonical writes use all8100 logical tiles in raster tile order in candidate bank1; padding is never transferred.',
                  'Synthetic queues all release at clock0. Round robin takes4/8/16 whole BL8 grants per stream in display,reference,canonical_write,hud_write,hud_verify order.',
                  'Standalone streams reset rows and counters independently. No arithmetic sum of separate runs is measured wall time.',
                  'Model read/write row-hit costs15/13 clocks, ACT4, conflicting PRE4, gap3; refresh sensitivity0/750, modeled cost15 and closes rows.',
                  'PRE_conflict excludes refresh precharges. REF counts reset events; no ACT/PRE command-pin qualification.',
                  'No LCD deadlines, temporal codec/qmap dependencies, CPU/HUD overlap, leases, bridge arbitration or physical device calibration modeled.',
                  'All-streams synthetic replay is one cold display trace plus one delta workload, not actual source-window traffic or repeated panels.',
                  'No hardware gain, targetFPS, validatedlatency, fit/timing or strictunder10ms claim follows from servicework.'])
    artifacts = {'results.json': json.dumps(result, indent=2) + '\n',
                 'mappings.json': json.dumps(mappings, indent=2) + '\n',
                 'measurements.csv': csv_text(measures)}
    if args.check:
        for name, data in artifacts.items():
            assert (OUT / name).read_text() == data, f'stale artifact {name}'
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, data in artifacts.items(): (OUT / name).write_text(data)
    print(json.dumps(dict(status=result['status'], mappings=len(mappings), scenarios=len(measures),
                         padding={m['layout']:m['padding_bytes'] for m in mappings}), indent=2))
    for m in measures:
        if m['refresh_period'] == 0 and (m['stream'] in ('standalone_display', 'standalone_reference', 'standalone_canonical_write') or m['quantum'] == 8):
            print(m['layout'], m['stream'], 'q'+str(m['quantum']), 'ACT',m['ACT'], 'PRE',m['PRE_conflict'],'work',m['service_work_cycles'])


if __name__ == '__main__':
    main()
