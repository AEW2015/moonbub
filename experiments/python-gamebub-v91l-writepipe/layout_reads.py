#!/usr/bin/env python3
"""Bounded Python comparison of candidate layouts and BL8 read gathering."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDENS = 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
LINE_REPORT = 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/results.json'
LINE_EVENTS = 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/lines-events.jsonl.gz'
ROW_REPORT = 'fpga/experiments/cu66-v91l-rows/comparison-attempts/20261106T231139409747Z-2dd7b637/results.json'
ROW_EVENTS = 'fpga/experiments/cu66-v91l-rows/comparison-attempts/20261106T231139409747Z-2dd7b637/events-rows.jsonl.gz'
SDRAM_REPORT = 'fpga/experiments/cu66-v91l-sdram/controller-attempts/20261106T233802043081Z-250d4c4c/results.json'
NATIVE_ROWS = 'fpga/experiments/cu66-v91l-sdram/controller-attempts/20261106T233802043081Z-250d4c4c/inputs/native-rows.hex.gz'
OUT = ROOT / 'experiments/python-gamebub-v91l-writepipe/layout-read-results.json'
PLANES = ((720, 480), (360, 240), (360, 240))
OFFS = (0, 345600, 432000)
FRAME_BYTES = 518400


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


class Layout:
    def __init__(self, name, tile_w=None, tile_h=None):
        self.name, self.tw, self.th = name, tile_w, tile_h
        self.offsets, self.spans = [], []
        end = 0
        for w, h in PLANES:
            self.offsets.append(end)
            if tile_w is None:
                span = w * h
            else:
                span = ((w + tile_w - 1) // tile_w) * ((h + tile_h - 1) // tile_h) * tile_w * tile_h
            self.spans.append(span)
            end += span
        self.size = end

    def addr(self, plane, raster):
        w, h = PLANES[plane]
        assert 0 <= raster < w * h
        if self.tw is None:
            return self.offsets[plane] + raster
        y, x = divmod(raster, w)
        nx = (w + self.tw - 1) // self.tw
        group = (y // self.th) * nx + x // self.tw
        inner = (y % self.th) * self.tw + (x % self.tw)
        return self.offsets[plane] + group * self.tw * self.th + inner

    def tile_addrs(self, plane, tile):
        w, h = PLANES[plane]
        nx = w // 8
        ty, tx = divmod(tile, nx)
        return [self.addr(plane, (ty * 8 + y) * w + tx * 8 + x)
                for y in range(8) for x in range(8)]


def load_frames():
    frames = {}
    with gzip.open(ROOT / GOLDENS, 'rt') as f:
        for line in f:
            ident, _profile, hx = line.rstrip('\n').split('\t')
            if ident in ('actual_001', 'actual_006'):
                raw = bytes.fromhex(hx)
                assert len(raw) == FRAME_BYTES
                frames[ident] = raw
    assert set(frames) == {'actual_001', 'actual_006'}
    return frames


def load_reference_tiles():
    events = []
    with gzip.open(ROOT / ROW_EVENTS, 'rt') as f:
        for line in f:
            d = json.loads(line)
            if d.get('type') == 'reference_request' and d.get('id') == 'actual_006' and d.get('memory_profile') == 0:
                assert 0 <= d['plane'] < 3
                assert 0 <= d['tile'] < ((PLANES[d['plane']][0] // 8) * (PLANES[d['plane']][1] // 8))
                events.append((d['plane'], d['tile']))
    assert len(events) == 7806
    return events


def load_native_rows(layout, frames):
    rows = []
    with gzip.open(ROOT / NATIVE_ROWS, 'rt') as f:
        for line in f:
            n = int(line, 16)
            payload = (n & ((1 << 64) - 1)).to_bytes(8, 'little')
            source_addr = (n >> 64) & ((1 << 20) - 1)
            bank = (n >> 84) & 3
            if source_addr < FRAME_BYTES:
                frame_id = 'actual_001' if bank == 0 else 'actual_006' if bank == 1 else None
                assert frame_id is not None
                assert payload == frames[frame_id][source_addr:source_addr + 8]
                plane = 0 if source_addr < OFFS[1] else 1 if source_addr < OFFS[2] else 2
                local = source_addr - OFFS[plane]
                address = layout.addr(plane, local)
            else:
                assert source_addr >= FRAME_BYTES
                address = layout.size + source_addr - FRAME_BYTES
            rows.append((bank, address))
    assert len(rows) == 140160
    assert sum(1 for _, a in rows if a >= layout.size) == 10560
    return rows


def src_plane(frame, plane):
    w, h = PLANES[plane]
    return frame[OFFS[plane]:OFFS[plane] + w * h]


def verify_gather(layout, frame):
    """Build candidate bytes, issue aligned logical lines, gather BL8s, compare exact bytes."""
    physical = bytearray(layout.size)
    for p, (w, h) in enumerate(PLANES):
        src = src_plane(frame, p)
        for r, value in enumerate(src):
            physical[layout.addr(p, r)] = value
    max_storage = max_bursts = total_bursts = useful = fetched = 0
    requests = 0
    for p, (w, h) in enumerate(PLANES):
        src = src_plane(frame, p)
        for start in range(0, len(src), 16):
            logical = src[start:start + 16]
            raster_indices = range(start, start + 16)
            offsets = [layout.addr(p, i) for i in raster_indices]
            bursts = sorted({a & ~15 for a in offsets})
            gathered = {b: bytes(physical[b:b + 16]) for b in bursts}
            result = bytes(gathered[a & ~15][a & 15] for a in offsets)
            assert result == logical, (layout.name, p, start)
            storage = len(bursts) * 16
            max_storage = max(max_storage, storage)
            max_bursts = max(max_bursts, len(bursts))
            total_bursts += len(bursts)
            useful += 16
            fetched += storage
            requests += 1
    assert requests == 32400
    return dict(requests_per_frame=requests, logical_bytes_per_frame=useful,
                physical_bl8_bursts=total_bursts, physical_bytes=fetched,
                overfetch_bytes=fetched - useful, max_bl8_bursts_per_logical_request=max_bursts,
                max_unique_burst_payload_per_request=max_storage,
                max_physical_response_scratch_bytes=16, logical_output_buffer_bytes=16,
                gather_storage_bound_bytes=32,
                byte_exact_frames=1, check='PASS_EXACT_ALL_LOGICAL_BYTES')


def verify_mapping_and_references(layout, frames, refs):
    for p, (w, h) in enumerate(PLANES):
        mapped = {layout.addr(p, r) for r in range(w * h)}
        assert len(mapped) == w * h
        assert min(mapped) == layout.offsets[p]
        assert max(mapped) < layout.offsets[p] + layout.spans[p]
        # Explicit 360-wide chroma right/bottom edge round trip through address inverse.
        if p in (1, 2):
            edge = layout.addr(p, h * w - 1)
            assert layout.offsets[p] <= edge < layout.offsets[p] + layout.spans[p]
    prior = frames['actual_001']
    physical = bytearray([0xA5]) * layout.size
    active_addresses = set()
    for p, (w, h) in enumerate(PLANES):
        src = src_plane(prior, p)
        for r, value in enumerate(src):
            address = layout.addr(p, r)
            active_addresses.add(address)
            physical[address] = value
    padding_addresses = set(range(layout.size)) - active_addresses
    assert all(physical[a] == 0xA5 for a in padding_addresses)
    max_bl8 = 0
    for p, tile in refs:
        addrs = layout.tile_addrs(p, tile)
        bursts = sorted({a & ~15 for a in addrs})
        max_bl8 = max(max_bl8, len(bursts))
        gather = {b: bytes(physical[b:b+16]) for b in bursts}
        actual = bytes(gather[a & ~15][a & 15] for a in addrs)
        w, h = PLANES[p]
        nx = w // 8
        ty, tx = divmod(tile, nx)
        src = src_plane(prior, p)
        expected = bytes(src[(ty*8+y)*w+tx*8+x] for y in range(8) for x in range(8))
        assert actual == expected
    return dict(reference_logical_requests=len(refs), reference_logical_bytes=len(refs)*64,
                max_bl8_bursts_per_reference_tile=max_bl8,
                reference_output_buffer_bytes=64, reference_physical_response_scratch_bytes=16,
                reference_gather_storage_bound_bytes=80,
                reference_byte_exact='PASS_ALL_REQUESTS_MATCH_PRIOR_ACCEPTED_CANONICAL',
                inactive_padding_bytes=len(padding_addresses),
                hud_region_start=layout.size, hud_region_bytes=42240,
                hud_bounds='PASS_AFTER_CANONICAL_ALLOCATION',
                mapping='PASS_INJECTIVE_PLANE_SPANS_CHROMA_EDGES_PADDING_HUD_BOUNDS')


def req_bursts(addresses):
    return sorted({a & ~15 for a in addresses})


def transitions(layout, refs, native_rows):
    """Serial phase order: candidate writes, reference tile reads, then converter reads."""
    state, counts = {}, {}
    def phase(name, addrs, useful_bytes=0, write_rows=0, logical_requests=None):
        act = conflict = hits = bursts = 0
        for bank, byte_addr in addrs:
            row = byte_addr // 1024
            bursts += 1
            if state.get(bank) is None:
                act += 1
            elif state[bank] == row:
                hits += 1
            else:
                conflict += 1
                act += 1
            state[bank] = row
        counts[name] = dict(logical_requests=logical_requests if logical_requests is not None else len(addrs),
                            physical_request_or_burst_count=len(addrs), read_bl8_bursts=0 if write_rows else bursts, useful_bytes=useful_bytes,
                            physical_read_bytes=0 if write_rows else bursts * 16, overfetch_bytes=0 if write_rows else max(0, bursts * 16 - useful_bytes),
                            eight_byte_write_rows=write_rows, x16_write_words=write_rows * 4,
                            row_activations=act,
                            row_conflicts=conflict, row_hits=hits,
                            banks_touched=sorted({b for b, _ in addrs}))
    # Native fixture contains two frame banks, tile-order canonical writes, then HUD.
    write_addrs = native_rows
    assert len(write_addrs) == 140160
    phase('candidate_writes_two_frame_fixture', write_addrs, useful_bytes=len(write_addrs) * 8, write_rows=len(write_addrs))
    ref_addrs = []
    for p, tile in refs:
        ref_addrs.extend((0, a) for a in req_bursts(layout.tile_addrs(p, tile)))
    phase('delta_reference_tiles_one_frame', ref_addrs, useful_bytes=len(refs) * 64, logical_requests=len(refs))
    canonical_addrs = []
    for p, (w, h) in enumerate(PLANES):
        for start in range(0, w * h, 16):
            canonical_addrs.extend((1, b) for b in req_bursts([layout.addr(p, i) for i in range(start, start + 16)]))
    phase('canonical_converter_fullframe_one_frame', canonical_addrs, useful_bytes=FRAME_BYTES, logical_requests=32400)
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    layouts = [Layout('raster'), Layout('tile8x8', 8, 8), Layout('micro16x8', 16, 8)]
    frames, refs = load_frames(), load_reference_tiles()
    results = []
    for layout in layouts:
        gather = [verify_gather(layout, frame) for frame in frames.values()]
        native = load_native_rows(layout, frames)
        mapping_check = verify_mapping_and_references(layout, frames, refs)
        assert all(a % 8 == 0 for _, a in native)
        hud_addrs = [a for _, a in native if a >= layout.size]
        assert len(hud_addrs) == 10560
        assert min(hud_addrs) == layout.size
        assert max(hud_addrs) < layout.size + 42240
        assert all(g['max_unique_burst_payload_per_request'] <= 32 for g in gather)
        results.append(dict(layout=layout.name, plane_offsets=layout.offsets, plane_spans=layout.spans,
                            canonical_bytes=layout.size, hud_bytes=42240, allocation_bytes=layout.size+42240,
                            mapping_reference_check=mapping_check, gather_per_frame=gather,
                            row_transitions=transitions(layout, refs, native)))
    sources = [GOLDENS, LINE_REPORT, LINE_EVENTS, ROW_REPORT, ROW_EVENTS, SDRAM_REPORT, NATIVE_ROWS,
               'scripts/cu66-v79/layout_study.py', 'docs/cu66-v91k-lines/read-contract.md',
               'docs/cu66-v91l-rows/write-contract.md', 'docs/cu66-v91l-sdram/controller-contract.md',
               'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
               'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
               'fpga/experiments/cu66-v91k-lines/tb_lines.cpp',
               'experiments/python-gamebub-v91l-writepipe/layout_reads.py']
    result = dict(schema='cu66-v91l-layout-reads-v1', status='PASS_EXACT_GATHER_BOUNDED_WORKLOAD_MODEL',
        source_revision='78162802af92f3a99773683aaf4929159e50a63b',
        source_sha256={p: sha(p) for p in sources},
        provenance=dict(canonical_corpus_frames=['actual_001', 'actual_006'],
            canonical_corpus_count=2, canonical_reads='DERIVED_FULL_CANONICAL_ORDERED_16_BYTE_LINES_PER_FRAME',
            lines_per_frame=32400, full_frame_reads_per_frame=True,
            reference_trace='ACTUAL reference_request events for actual_006, memory_profile 0; repeated events retained; one per requested 64-byte tile',
            reference_tiles_per_frame=len(refs),
            candidate_write_fixture='ACTUAL v91l-sdram native-rows.hex.gz packed 160-bit rows streamed in captured order; bank and source byte address decoded per row, canonical offsets remapped per candidate layout and HUD rebased after padded allocation',
            candidate_write_rows=140160, row_bytes=8, canonical_hud_rows_per_frame=70080),
        scheduling=dict(serialized_phase_order=['candidate_writes_two_frame_fixture','delta_reference_tiles_one_frame','canonical_converter_fullframe_one_frame'],
            row_state_continues_between_phases=True, controller_row_bytes=1024,
            meaning='Address-only ACT/conflict/hit counts for this declared serial schedule; no controller timing, arbitration, or latency.'),
        limits=['Physical BL8 is an aligned 16-byte burst. Each logical read independently deduplicates bursts; no cross-request cache reuse is credited.',
            'Overfetch is fetched bytes minus useful logical bytes (16 per converter request or 64 per reference tile); writes report 8-byte payload rows and four x16 word writes each.',
            'Converter gather bound uses one 16-byte physical response scratch plus one 16-byte logical output buffer (32 total); reference-tile reads use 64-byte output plus 16-byte scratch (80 total). Byte/control registers are excluded.',
            'Writes, reference reads and converter reads are separate phase totals in one synthetic serialized address order.',
            'The two canonical fixture frames prove byte exactness only for actual_001 and actual_006; corpus size remains two.',
            'No joint arbiter, refresh, controller latency, FPS, bandwidth, frame deadline, or hardware claim is modeled.'],
        layouts=results)
    data = json.dumps(result, indent=2) + '\n'
    if args.check:
        assert OUT.read_text() == data, 'stale result json'
    else:
        OUT.write_text(data)
    print(json.dumps(dict(status=result['status'], layouts=len(layouts), frames=len(frames), reference_tiles=len(refs), output=str(OUT)), indent=2))

if __name__ == '__main__':
    main()
