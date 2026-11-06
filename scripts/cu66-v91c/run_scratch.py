#!/usr/bin/env python3
"""Qualify packed scratch and count bounded storage/burst work, not latency."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91c'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject(fn, kind=ValueError):
    try:
        fn()
    except kind:
        return
    raise AssertionError('missing rejection')


def directed_tests(scratch):
    rows = []

    def check(name, fn):
        fn()
        rows.append(dict(name=name, status='PASS'))

    def lifecycle():
        store = scratch.PackedScratch(256)
        store.begin(1, 2, (0, 0, 0))
        reject(lambda: list(store.tiles(1)))
        store.offer(1, 0, (0, 0, -2048))
        held = store.pending
        for _ in range(257):
            assert not store.consume(1, False) and store.pending == held
        reject(lambda: store.offer(1, 0, (1, 0, 2048)), BufferError)
        reject(lambda: store.complete(1, 0))
        reject(lambda: store.seal(1))
        store.consume(1, True)
        reject(lambda: store.offer(1, 0, (0, 0, 1)))
        store.offer(1, 0, (1, 0, 2048))
        store.consume(1, True)
        store.complete(1, 0)
        for band in (1, 2, 3):
            store.complete(1, band)
        store.seal(1)
        tiles = list(store.tiles(1))
        assert tiles == [(0, (-2048,) + (0,) * 63), (1, (2048,) + (0,) * 63)]
        assert store.stats['read_bursts'] * 16 == store.plan['used_bytes']
        reader = store.tiles(1)
        next(reader)
        store.begin(2, 1, (0, 0, 0))
        reject(lambda: next(reader))
        reject(lambda: store.offer(1, 0, (0, 0, 7)))
        store.offer(2, 0, (0, 0, 0))
        store.abort()
        assert store.pending is None
        reject(lambda: list(store.tiles(2)))
        reject(lambda: store.consume(2, True))
        store.begin(3, 1, (0, 0, 0))
        store.offer(3, 0, (0, 0, 0))
        store.consume(3, True)
        for band in range(4):
            store.complete(3, band)
        store.seal(3)
        assert list(store.tiles(3)) == [(0, (0,) * 64)]
        reject(lambda: store.begin(3, 1, (0, 0, 0)))
    check('credit_hold_early_read_abort_replacement_zero_default', lifecycle)
    for blocks in (0, 8193):
        check(f'bad_blocks_{blocks}', lambda blocks=blocks: reject(lambda: scratch.layout(blocks, (0, 0, 0))))
    for counts in ((-1, 0, 0), (6, 0, 0), (0, 16, 0), (0, 0, 44)):
        check(f'bad_counts_{counts}', lambda counts=counts: reject(lambda: scratch.layout(1, counts)))
    check('raw_count_reject', lambda: reject(lambda: scratch.layout(1, (1, 0, 0), True)))

    def capacity():
        required = scratch.layout(1, (0, 0, 0))['used_bytes']
        small = scratch.PackedScratch(required - 16)
        reject(lambda: small.begin(1, 1, (0, 0, 0)), BufferError)
        assert not small.active and not small.sealed
        exact = scratch.PackedScratch(required)
        exact.begin(1, 1, (0, 0, 0))
        exact.offer(1, 0, (0, 0, 2048)); exact.consume(1, True)
        for band in range(4):
            exact.complete(1, band)
        exact.seal(1)
        assert list(exact.tiles(1)) == [(0, (2048,) + (0,) * 63)]
    check('exact_budget_and_overflow_admission', capacity)

    def position_extreme():
        store = scratch.PackedScratch(32 * 1024)
        store.begin(1, 8192, (0, 0, 1))
        for block in range(8192):
            store.offer(1, 0, (block, 0, 0)); store.consume(1, True)
        for band in range(3):
            store.complete(1, band)
        store.offer(1, 3, (8191, 63, -2048)); store.consume(1, True)
        store.complete(1, 3); store.seal(1)
        last = None
        for _, tile in store.tiles(1):
            last = tile
        assert last == (0,) * 63 + (-2048,)
    check('largest_profile_position_signed_pack', position_extreme)

    def bad_events():
        store = scratch.PackedScratch(256)
        store.begin(1, 1, (2, 0, 0))
        reject(lambda: store.offer(1, 1, (0, 1, 1)))
        reject(lambda: store.offer(1, 0, (0, 0, 2049)))
        store.offer(1, 0, (0, 0, 0)); store.consume(1, True); store.complete(1, 0)
        reject(lambda: store.offer(1, 1, (0, 63, 1)))
        reject(lambda: store.offer(1, 1, (0, 1, 0)))
        store.offer(1, 1, (0, 1, 1)); store.consume(1, True)
        reject(lambda: store.offer(1, 1, (0, 1, 2)))
        reject(lambda: store.complete(1, 1))
        store.offer(1, 1, (0, 8, -1)); store.consume(1, True)
        for band in range(1, 4):
            store.complete(1, band)
        store.seal(1)
        assert list(store.tiles(1))[0][1] == (0, 1) + (0,) * 6 + (-1,) + (0,) * 55
    check('order_duplicate_band_value_and_count_rejection', bad_events)
    return rows


def replay(store, epoch, packet, blocks, context, word, control, *, stalled):
    contexts, raw = context.parse_chunk(packet, blocks)
    counts = (0, 0, 0) if raw is not None else tuple(c.event_count for c in contexts[1:])
    store.begin(epoch, blocks, counts, raw is not None)
    rng = random.Random(910300 + epoch)
    sources = ([(0, ((n // 64, n % 64, value) for n, value in enumerate(raw)))]
               if raw is not None else [(c.band, context.writes(c, word.WordRice)) for c in contexts])
    try:
        for band, source in sources:
            for item in source:
                store.offer(epoch, band, item)
                pending = store.pending
                for _ in range(rng.randrange(5) if stalled else 0):
                    assert not store.consume(epoch, False) and store.pending == pending
                assert store.consume(epoch, True)
            store.complete(epoch, band)
        store.seal(epoch)
        digest = hashlib.sha256()
        seen = 0
        for block, tile in store.tiles(epoch):
            assert block * 64 == seen
            assert tuple(control[seen:seen + 64]) == tile
            digest.update(struct.pack('<64h', *tile))
            seen += 64
        assert seen == blocks * 64
        assert store.stats['write_bursts'] == store.stats['read_bursts'] == store.plan['used_bytes'] // 16
        assert store.stats['write_assembler_high_water'] <= 16
        assert store.stats['read_cache_high_water'] <= 4
        return dict(blocks=blocks, raw=raw is not None, ac_counts=list(counts),
                    used_bytes=store.plan['used_bytes'], padding_bytes=store.plan['padding_bytes'],
                    scratch_sha256=hashlib.sha256(store.memory[:store.plan['used_bytes']]).hexdigest(),
                    dense_reservation_bytes=128 * blocks,
                    coefficient_values=seen, coefficient_sha256=digest.hexdigest(), stats=dict(store.stats))
    except BaseException:
        store.abort()
        raise


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'scratch-attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    entropy = ROOT / 'experiments/python-gamebub-v88/entropy'
    paths = [Path(__file__).resolve(), AREA / 'scratch.py',
             ROOT / 'experiments/python-gamebub-v91b/context.py', ROOT / 'experiments/python-gamebub-v91/parser.py',
             entropy / 'codec.py', entropy / 'data.py', entropy / 'index.json',
             ROOT / 'experiments/python-gamebub-v85/residual/data.py',
             ROOT / 'experiments/python-gamebub-v85/residual/index.json',
             AREA / 'packet-vectors/index.json', AREA / 'packet-vectors/packets.jsonl.gz']
    for base in (entropy, ROOT / 'experiments/python-gamebub-v85/residual'):
        paths.append(base / json.loads((base / 'index.json').read_text())['data']['path'])
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for p in paths:
        if p.suffix == '.py':
            target = out / 'sources' / p.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(p.read_bytes())
    report = dict(schema='cu66-v91c-packed-scratch-v1', status='FAIL', source_sha256=pins,
                  parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  assumptions=dict(capacity_bytes=262144, max_blocks=8192, header_bytes=32, burst_bytes=16,
                                   read_cycles_per_burst=18, write_cycles_per_burst=16,
                                   schedule='Per event: Random(910300 + transaction epoch).randrange(5) held samples; not FPGA cycles.'),
                  scope='Functional packed-scratch prototype and addressed burst-work ledger. SDRAM service weights are hypothetical, not full completion latency; scratch is not implemented in RTL.',
                  full_30fps_proven=False, complete_under10ms_proven=False, scratch_RTL_implemented=False)
    started = time.monotonic()
    try:
        scratch = load('v91c_scratch', AREA / 'scratch.py')
        context = load('v91c_context', ROOT / 'experiments/python-gamebub-v91b/context.py')
        word = load('v91c_word', ROOT / 'experiments/python-gamebub-v91/parser.py')
        frozen = load('v91c_frozen', entropy / 'codec.py')
        data = load('v91c_data', entropy / 'data.py')
        tests = directed_tests(scratch)
        (out / 'directed.json').write_text(json.dumps(tests, indent=2) + '\n')
        store = scratch.PackedScratch()
        rows = []
        identities = set()
        epoch = 0
        for frame in data.iter_frames():
            identity = frame['cohort'], frame['fid']
            assert identity not in identities
            identities.add(identity)
            for plane, chunks in enumerate(frame['variants']['65536']):
                for chunk_id, chunk in enumerate(chunks):
                    oracle = frozen.decode(chunk['br88'], chunk['blocks'])
                    # Reuse the same poisoned backing store across every source;
                    # start invalidates ownership, not every coefficient byte.
                    epoch += 1
                    result = replay(store, epoch, chunk['br88'], chunk['blocks'], context, word, oracle, stalled=True)
                    assert result['coefficient_sha256'] == chunk['coefficient_sha256']
                    writes = result['stats']['accepted']
                    result.update(cohort=identity[0], fid=identity[1], ordinal=frame['ordinal'], plane=plane, chunk=chunk_id,
                                  packet_bytes=len(chunk['br88']), packet_sha256=hashlib.sha256(chunk['br88']).hexdigest(),
                                  ideal_dense_clear_scatter_read_bytes=256 * chunk['blocks'] + 2 * writes,
                                  ideal_bitmap_external_value_bytes=4 * writes,
                                  bitmap_clear_bytes=8 * chunk['blocks'],
                                  packed_bus_bytes=32 * result['stats']['write_bursts'],
                                  hypothetical_memory_busy_cycles=34 * result['stats']['write_bursts'])
                    rows.append(result)
            if len(identities) % 50 == 0:
                print('V91C_SCRATCH_PROGRESS', len(identities), flush=True)
        assert len(identities) == 457 and len(rows) == 1371
        synthetic_rows = []
        index = json.loads((AREA / 'packet-vectors/index.json').read_text())
        with gzip.open(AREA / 'packet-vectors/packets.jsonl.gz', 'rt') as stream:
            for line in stream:
                case = json.loads(line)
                if case['case_type'] != 'synthetic':
                    continue
                packet = bytes.fromhex(case['packet_hex'])
                oracle = frozen.decode(packet, case['blocks'])
                epoch += 1
                ready = replay(store, epoch, packet, case['blocks'], context, word, oracle, stalled=False)
                epoch += 1
                held = replay(store, epoch, packet, case['blocks'], context, word, oracle, stalled=True)
                assert ready['coefficient_sha256'] == held['coefficient_sha256'] == case['coefficient_sha256']
                synthetic_rows.append(dict(id=case['id'], ready=ready, stalled=held))
        (out / 'chunks.jsonl').write_text(''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows))
        (out / 'synthetic.json').write_text(json.dumps(synthetic_rows, indent=2) + '\n')
        fields = ('coefficient_values', 'used_bytes', 'padding_bytes', 'dense_reservation_bytes',
                  'ideal_dense_clear_scatter_read_bytes', 'ideal_bitmap_external_value_bytes',
                  'bitmap_clear_bytes', 'packed_bus_bytes', 'hypothetical_memory_busy_cycles')
        totals = {field: sum(row[field] for row in rows) for field in fields}
        totals.update(sources=457, chunks=len(rows), sparse_writes=sum(row['stats']['accepted'] for row in rows),
                      held_samples=sum(row['stats']['held_samples'] for row in rows),
                      write_bursts=sum(row['stats']['write_bursts'] for row in rows),
                      read_bursts=sum(row['stats']['read_bursts'] for row in rows))
        budgets = [dict(capacity_bytes=budget, packed_fit=sum(row['used_bytes'] <= budget for row in rows),
                        dense_fit=sum(row['dense_reservation_bytes'] <= budget for row in rows))
                   for budget in (65536, 131072, 262144, 524288)]
        maxima = {field: dict(value=max(row[field] for row in rows),
                      identity={key: max(rows, key=lambda row: row[field])[key]
                                for key in ('cohort', 'fid', 'plane', 'chunk')})
                  for field in ('used_bytes', 'dense_reservation_bytes', 'hypothetical_memory_busy_cycles')}
        assert pins == {path: sha(ROOT / path) for path in pins}
        report.update(status='PASS_FULL_CORPUS_PACKED_SCRATCH', totals=totals, budget_sweep=budgets,
                      maxima=maxima, directed_checks=len(tests), synthetic_cases=len(synthetic_rows),
                      bounded_working_data_bytes=252,
                      working_data_scope='4x16B read caches +16B write assembler +128B tile +3x4B AC heads +32B descriptor, excluding control, lookup tables and host line-epoch instrumentation.')
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'scratch-results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V91C_SCRATCH', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
