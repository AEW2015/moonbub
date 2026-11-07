#!/usr/bin/env python3
"""Source-derived chroma-prefill-order comparison for tile8x8 BL8 reads."""
import argparse
import gzip
import hashlib
import json
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
DOC = ROOT / 'docs/cu66-v91l-tiled/prefill-contract.md'
INPUT = ROOT / 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
SOURCES = [
    ROOT / 'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',
    ROOT / 'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',
    ROOT / 'fpga/experiments/cu66-v91k-lines/tb_lines.cpp',
    ROOT / 'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',
    ROOT / 'docs/cu66-v91k-lines/read-contract.md',
    ROOT / 'experiments/python-gamebub-v91l-writepipe/layout_reads.py',
    ROOT / 'experiments/python-gamebub-v91l-writepipe/rowpair_cache.py',
]
VECTORS = AREA / 'vectors/prefill-lines.hex.gz'
PLANES = ((0, 720, 480), (345600, 360, 240), (432000, 360, 240))
FRAME_BYTES = 518400


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frames():
    out = {}
    with gzip.open(INPUT, 'rt') as f:
        for line in f:
            ident, profile, payload = line.rstrip('\n').split('\t')
            if ident in ('actual_001', 'actual_006') and profile == '0':
                assert ident not in out
                out[ident] = bytes.fromhex(payload)
    assert set(out) == {'actual_001', 'actual_006'}
    assert all(len(x) == FRAME_BYTES for x in out.values())
    return out


def consumer_addresses():
    """Exact byte order implied by CHECK_ROWS/FILL_REQ/LUMA_REQ and tb schedule."""
    result = []
    next_row = 0
    for y in range(480):
        last = min(y // 2 + 1, 239)
        while next_row <= last:
            r = next_row
            result.extend(345600 + r * 360 + x for x in range(360))
            result.extend(432000 + r * 360 + x for x in range(360))
            next_row += 1
        result.extend(y * 720 + x for x in range(720))
    assert len(result) == FRAME_BYTES
    return result


def aligned_line_schedule():
    """Replay reader's three independent plane tags over source-derived bytes."""
    tags = [None, None, None]
    out = []
    for address in consumer_addresses():
        plane = 0 if address < 345600 else 1 if address < 432000 else 2
        line = address & ~15
        if tags[plane] != line:
            out.append(line)
            tags[plane] = line
    assert len(out) == 32400
    assert len(set(out)) == 32400
    return out


def tile_address(address):
    plane = 0 if address < 345600 else 1 if address < 432000 else 2
    base, width, _height = PLANES[plane]
    y, x = divmod(address - base, width)
    # All plane dimensions are divisible by 8, including 360x240 chroma.
    tiles_per_row = width // 8
    tile = (y // 8) * tiles_per_row + x // 8
    inner = (y % 8) * 8 + x % 8
    return base + tile * 64 + inner


def evaluate(frame, accesses):
    # Test-oracle mappings are deliberately not included in the proposed RAM budget.
    inverse = {}
    physical = bytearray(FRAME_BYTES)
    for logical, value in enumerate(frame):
        a = tile_address(logical)
        assert a not in inverse and a < FRAME_BYTES
        inverse[a] = logical
        physical[a] = value
    assert len(inverse) == FRAME_BYTES

    # Baseline: reader has one current aligned line tag per plane, no unused-byte retention.
    tags = [None, None, None]
    independent_fetches = 0
    for logical in accesses:
        p = 0 if logical < 345600 else 1 if logical < 432000 else 2
        line = tile_address(logical) & ~15
        if tags[p] != line:
            independent_fetches += 1
            tags[p] = line

    # Proposed bounded retention model: each plane keeps all fetched bytes whose
    # logical consumer ordinal in that plane is still ahead of its current ordinal.
    pending = [{}, {}, {}]
    cursor = [0, 0, 0]
    pending_total = 0
    total_fetches = 0
    max_pending = [0, 0, 0]
    max_pending_total = 0
    output = bytearray()
    seen_lines = set()
    for logical in accesses:
        p = 0 if logical < 345600 else 1 if logical < 432000 else 2
        base, width, height = PLANES[p]
        local = logical - base
        assert local == cursor[p], (p, local, cursor[p])
        if local not in pending[p]:
            line = tile_address(logical) & ~15
            assert line not in seen_lines, ('would refetch', line)
            seen_lines.add(line)
            total_fetches += 1
            for a in range(line, line + 16):
                target = inverse.get(a)
                if target is None:
                    continue
                target_plane = 0 if target < 345600 else 1 if target < 432000 else 2
                assert target_plane == p
                target_local = target - base
                assert target_local >= local
                assert target_local // width <= local // width + 1
                if target_local > local:
                    assert target_local not in pending[p]
                    pending[p][target_local] = physical[a]
                    pending_total += 1
            max_pending[p] = max(max_pending[p], len(pending[p]))
            max_pending_total = max(max_pending_total, pending_total)
        if local in pending[p]:
            value = pending[p].pop(local)
            pending_total -= 1
        else:
            # The current requested byte came from the just-fetched line.
            a = tile_address(logical)
            value = physical[a]
        assert value == frame[logical]
        output.append(value)
        cursor[p] += 1
        max_pending[p] = max(max_pending[p], len(pending[p]))
        max_pending_total = max(max_pending_total, pending_total)
    assert len(output) == len(accesses)
    assert not any(pending)
    assert total_fetches == 32400 and len(seen_lines) == 32400
    assert max_pending[0] <= 720 + 15 and max_pending[1] <= 360 + 15 and max_pending[2] <= 360 + 15
    assert max_pending_total <= 1440 + 16
    return dict(
        byte_exact='PASS_ALL_518400_CONSUMER_BYTES',
        consumer_response_sha256=hashlib.sha256(output).hexdigest(),
        independent_current_line_tag_bl8_fetches=independent_fetches,
        retained_bl8_fetches=total_fetches,
        retained_per_plane_max_pending_bytes=max_pending,
        retained_total_max_pending_bytes=max_pending_total,
        retention_capacity_bytes=dict(Y=720, Cb=360, Cr=360, total=1440),
        retained_all_bl8_lines_once=True,
        right_edge_chroma_x359='covered_in_each_360-byte_row',
        bottom_edge_chroma_row239='covered; replicated bottom lookup emits no row240 reads',
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    actual_lines = aligned_line_schedule()
    # Stable plain hex, one aligned canonical client address per line-reader miss.
    raw = ''.join(f'{a:05x}\n' for a in actual_lines).encode('ascii')
    if args.check:
        with gzip.open(VECTORS, 'rb') as f:
            assert f.read() == raw, 'stale line vector'
    else:
        with closing(gzip.GzipFile(filename=str(VECTORS), mode='wb', mtime=0)) as f:
            f.write(raw)
    loaded_frames = frames()
    result = dict(
        schema='cu66-v91l-tiled-prefill-model-v1',
        status='PASS_PYTHON_SOURCE_DERIVED_EXACT',
        provenance='DERIVED_FROM_SOURCE; not captured physical line-address events',
        source_revision='438dbb2e8d5ccfa2fa38ad34706dc3c2fd904080',
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in SOURCES},
        input_sha256=sha(INPUT),
        input_report='fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/results.json',
        input_report_sha256=sha(ROOT / 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/results.json'),
        generator_sha256=sha(Path(__file__).resolve()),
        vector=dict(path=str(VECTORS.relative_to(ROOT)), format='one aligned canonical client address as lowercase five-digit hex per line',
                    line_count=len(actual_lines), raw_sha256=hashlib.sha256(raw).hexdigest(), gzip_sha256=sha(VECTORS),
                    address_order_sha256=hashlib.sha256(raw).hexdigest()),
        schedule='Source-derived CHECK_ROWS chroma prefill Cb then Cr, then raster Y; one line tag per plane as canonical_line_reader.sv.',
        aligned_line_requests_per_frame=len(actual_lines),
        frames={name: evaluate(frame, consumer_addresses()) for name, frame in loaded_frames.items()},
        proposed_data_storage=dict(per_plane_retained_bytes=[720, 360, 360], bl8_scratch_bytes=16,
                                   logical_output_bytes=16, total_data_bytes=1472,
                                   note='Candidate reuse of existing chroma RAM is a proposal only; no RTL implementation is asserted here.'),
        no_hardware_latency_claim=True,
        limitations=['Python candidate-memory replay only; no hardware timing, latency, controller, refresh, or throughput claim.',
                     'Tile8x8 mapping and retained-unused-byte policy are modeled; no RTL or physical SDRAM experiment is represented.',
                     '360x240 chroma planes are divisible by 8; each x=359 row edge and row239 bottom edge is included.'])
    data = json.dumps(result, indent=2) + '\n'
    dest = AREA / 'prefill-results.json'
    if args.check:
        assert dest.read_text() == data, 'stale result'
    else:
        dest.write_text(data)
    print(json.dumps(dict(status=result['status'], frames=len(result['frames']), lines=len(actual_lines), output=str(dest))))


if __name__ == '__main__':
    main()
