#!/usr/bin/env python3
"""Exact sequential tile8x8 BL8 gather with bounded next-row retention (Python only)."""
import argparse
from array import array
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
GOLDEN = ROOT / 'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de/inputs/canonical_actual.tsv.gz'
REPORT = GOLDEN.parent.parent / 'results.json'
PLANES = ((0, 720, 480), (345600, 360, 240), (432000, 360, 240))
EXTENT = 518400


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def physical(logical):
    base, width, _height = next(p for p in reversed(PLANES) if logical >= p[0])
    y, x = divmod(logical - base, width)
    return base + ((y // 8) * (width // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8


def frames():
    found = {}
    with gzip.open(GOLDEN, 'rt') as f:
        for line in f:
            ident, profile, payload = line.rstrip().split('\t')
            if ident in ('actual_001', 'actual_006') and profile == '0':
                assert ident not in found
                found[ident] = bytes.fromhex(payload)
    assert set(found) == {'actual_001', 'actual_006'}
    assert all(len(frame) == EXTENT for frame in found.values())
    return found


def evaluate(frame):
    # Full inverse/physical arrays are test-oracle storage, NOT proposed FPGA RAM.
    inverse = array('I', [0]) * EXTENT
    memory = bytearray(EXTENT)
    used = bytearray(EXTENT)
    for logical, value in enumerate(frame):
        address = physical(logical)
        assert 0 <= address < EXTENT and used[address] == 0
        used[address] = 1
        inverse[address] = logical
        memory[address] = value
    assert all(used)
    pending, fetched = {}, set()
    reconstructed = bytearray()
    bursts = rowchanges = max_pending = max_per_request = max_future_rows = 0
    previous_row = None
    plane_max = [0, 0, 0]
    for start in range(0, EXTENT, 16):
        output = bytearray()
        new = 0
        for logical in range(start, start + 16):
            plane = 0 if logical < 345600 else 1 if logical < 432000 else 2
            base, width, height = PLANES[plane]
            current_y = (logical - base) // width
            if logical == base:
                assert not pending
            if logical not in pending:
                burst = physical(logical) & ~15
                assert burst not in fetched
                fetched.add(burst)
                bursts += 1
                new += 1
                row = burst // 1024
                rowchanges += int(row != previous_row)
                previous_row = row
                for byte_address in range(burst, burst + 16):
                    target = inverse[byte_address]
                    assert target >= logical and target not in pending
                    assert base <= target < base + width * height
                    distance = (target - base) // width - current_y
                    assert 0 <= distance <= 1
                    max_future_rows = max(max_future_rows, distance)
                    pending[target] = memory[byte_address]
            max_pending = max(max_pending, len(pending))
            plane_max[plane] = max(plane_max[plane], len(pending))
            # Stream-ordered fetch only retains bytes in this row or next row.
            assert len(pending) <= width + 16
            output.append(pending.pop(logical))
        assert output == frame[start:start + 16]
        reconstructed.extend(output)
        max_per_request = max(max_per_request, new)
    assert not pending and reconstructed == frame
    assert bursts == EXTENT // 16 == len(fetched)
    return dict(check='PASS_BYTE_EXACT_ORDERED_BL8_GATHER', logical_requests=EXTENT // 16,
                useful_bytes=EXTENT, physical_bl8_bursts=bursts, physical_read_bytes=bursts * 16,
                overfetch_bytes=bursts * 16 - EXTENT, unique_physical_bursts=len(fetched),
                no_refetch=True, maximum_pending_data_bytes=max_pending,
                per_plane_maximum_pending_data_bytes=plane_max,
                maximum_new_bursts_per_16byte_request=max_per_request,
                maximum_future_rows_retained=max_future_rows,
                address_only_row_activations=rowchanges,
                sha256=hashlib.sha256(reconstructed).hexdigest())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    result = dict(schema='cu66-v91l-tile-rowpair-cache-v1', status='PASS_PYTHON_EXACT_ROWPAIR_GATHER',
                  source_revision='78162802af92f3a99773683aaf4929159e50a63b',
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in (GOLDEN, REPORT, Path(__file__).resolve())},
                  geometry='720x480 Y + two360x240 chroma planes; canonical518400bytes; no HUD/scanout',
                  schedule='DERIVED monotonic aligned16byte canonical requests; independent of actual converter request order',
                  frames={name: evaluate(frame) for name, frame in frames().items()},
                  proposed_data_storage=dict(next_row_ram_bytes=720, physical_burst_scratch_bytes=16,
                                             logical_response_bytes=16, total_data_bytes=752,
                                             metadata_included=False),
                  contract=['Only sequential canonical plane/row order with an immutable leased bank.',
                            'Each physical BL8 contains two eight-byte rows; retain unused next-row bytes.',
                            'Requests and output are16bytes; physical reads are aligned16byte BL8.',
                            'Invalidate pending data/tags on bank generation/epoch changes, cancel and reset.',
                            'Next-row cache, read arbiter and invalidation are not implemented in RTL.',
                            'Dictionary, inverse array, full frame and fetched set are Python test-oracle storage, not FPGA architecture.'],
                  limitations=['No refresh, arbitration, controller latency, target timing/fit, random order, or concurrent consumer claim.',
                               'This schedule differs from converter chroma-prefill order; integrate per-plane caches/scheduling before promotion.',
                               'No current hardware throughput, decoder latency, ESP32 or HEVC/AV1 rate/quality result.'])
    data = json.dumps(result, indent=2) + '\n'
    dest = AREA / 'rowpair-cache-results.json'
    if args.check:
        assert dest.read_text() == data, 'stale result'
    else:
        dest.write_text(data)
    print(json.dumps(dict(status=result['status'], frames=len(result['frames']), output=str(dest))))


if __name__ == '__main__':
    main()
