#!/usr/bin/env python3
"""Qualify sparse BR88 context integration on the full frozen corpus.

No cycle, bitrate improvement or hardware-latency claim is made by this runner.
"""
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
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v91b'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packed(values):
    return struct.pack('<' + str(len(values)) + 'h', *values)


def stall_samples(seed):
    # Bounded, deterministic consumer service: <=7 False samples then True.
    # The generator advances only when a pending coefficient is being held.
    rng = random.Random(seed)
    while True:
        for _ in range(rng.randrange(8)):
            yield False
        yield True


def code(values, k, escape):
    bits = []
    for value in values:
        q = value >> k
        if q >= 15:
            if not 0 <= value < 1 << escape:
                raise ValueError('test literal overflow')
            bits.extend([0] * 15)
            width = escape
        else:
            bits.extend([0] * q + [1])
            width = k
        bits.extend((value >> bit) & 1 for bit in range(width - 1, -1, -1))
    data = bytearray((len(bits) + 7) // 8)
    for at, bit in enumerate(bits):
        data[at // 8] |= bit << (7 - at % 8)
    return bytes(data), len(bits)


def run_checks(model, reader):
    rows = []

    def check(name, fn):
        fn()
        rows.append(dict(name=name, status='PASS'))

    def reject(fn, kind=ValueError):
        try:
            fn()
        except kind:
            return
        raise AssertionError('expected rejection')

    def context(blocks, band, k0, k1, count, values):
        bits = []
        # Each entry may have a different field width (run/level).
        for value, k, escape in values:
            data, size = code([value], k, escape)
            bits.extend((data[i // 8] >> (7 - i % 8)) & 1 for i in range(size))
        data = bytearray((len(bits) + 7) // 8)
        for at, bit in enumerate(bits):
            data[at // 8] |= bit << (7 - at % 8)
        return model.Context(blocks, band, k0, k1, count, len(bits), bytes(data))

    for band in range(1, 4):
        c = context(1, band, 0, 0, 0, [])
        check(f'empty_ac_{band}', lambda c=c: (
            None if list(model.writes(c, reader)) == [] else (_ for _ in ()).throw(AssertionError())))
        bad = model.Context(1, band, 0, 0, 0, 1, b'\x80')
        check(f'nonempty_zero_event_{band}', lambda bad=bad: reject(lambda: list(model.writes(bad, reader))))
    dcvalues = [-2048, 2048, 0, -1, 1]
    dc = context(5, 0, 2, 255, 5,
                 [(2 * v if v >= 0 else -2 * v - 1, 2, 14) for v in dcvalues])
    check('dc_extrema', lambda: require(list(model.writes(dc, reader)) == [(i, 0, v) for i, v in enumerate(dcvalues)]))
    for band in range(1, 4):
        width = model.LIMITS[band] - model.LIMITS[band - 1]
        for sign, level in ((-2048, 4094), (2048, 4095)):
            c = context(2, band, 0, 0, 1, [(2 * width - 1, 0, 24), (level, 0, 12)])
            want = [(1, model.ORDER[model.LIMITS[band] - 1], sign)]
            check(f'ac_last_band{band}_value{sign}', lambda c=c, want=want: require(list(model.writes(c, reader)) == want))
        for run in (2 * width, 0xffffff):
            c = context(2, band, 0, 0, 1, [(run, 0, 24), (0, 0, 12)])
            check(f'ac_run_overflow_band{band}_run{run}', lambda c=c: reject(lambda: list(model.writes(c, reader))))
    for band, k0, k1, count in ((0, 14, 255, 1), (0, 0, 0, 1), (0, 0, 255, 0),
                                 (1, 20, 0, 0), (1, 0, 12, 0), (3, 0, 0, 44)):
        c = model.Context(1, band, k0, k1, count, 0, b'')
        check(f'bad_metadata_{band}_{k0}_{k1}_{count}', lambda c=c: reject(c.validate))
    dc_bad = context(1, 0, 2, 255, 1, [(4097, 2, 14)])
    check('dc_range_reject', lambda: reject(lambda: list(model.writes(dc_bad, reader))))
    ac_bad = context(1, 1, 0, 11, 1, [(0, 0, 24), (4096, 11, 12)])
    check('ac_range_reject', lambda: reject(lambda: list(model.writes(ac_bad, reader))))
    for size in range(dc.bit_size):
        data = bytearray(dc.data[:(size + 7) // 8])
        if size % 8:
            data[-1] &= 0xff << (8 - size % 8)
        c = model.Context(dc.blocks, dc.band, dc.k0, dc.k1, dc.event_count, size, bytes(data))
        check(f'dc_truncated_at_{size}', lambda c=c: reject(lambda: list(model.writes(c, reader))))
    bad_padding = model.Context(1, 0, 0, 255, 1, 1, b'\x81')
    check('padding_reject', lambda: reject(bad_padding.validate))
    extra = context(1, 0, 0, 255, 1, [(0, 0, 14), (0, 0, 14)])
    check('exact_end_reject', lambda: reject(lambda: list(model.writes(extra, reader))))

    def transaction_checks():
        tx = model.Transaction()
        tx.begin(10, 2)
        tx.offer(10, 0, (0, 0, 7))
        pending = tx.pending
        for _ in range(257):
            assert not tx.consume(False) and tx.pending == pending
        reject(lambda: tx.offer(10, 0, (1, 0, 8)), BufferError)
        reject(lambda: tx.complete(10, 0))
        reject(lambda: tx.finish(10))
        assert tx.consume(True)
        reject(lambda: tx.offer(10, 0, (0, 0, 8)))
        tx.offer(10, 0, (1, 0, 8))
        tx.begin(11, 1)  # Atomic abort/restart must clear pending and old scratch.
        assert tx.pending is None and not any(tx.scratch)
        reject(lambda: tx.offer(10, 0, (0, 0, 2)))
        reject(lambda: tx.begin(10, 1))
        tx.offer(11, 0, (0, 0, 1))
        tx.consume(True)
        for band in range(4):
            tx.complete(11, band)
        published = tx.finish(11)
        assert published == (1,) + (0,) * 63
        reject(lambda: tx.offer(11, 0, (0, 0, 2)))
        tx.begin(12, 1)
        tx.offer(12, 0, (0, 0, 3))
        tx.abort()
        assert tx.pending is None and tx.published is None
        reject(lambda: tx.finish(12))
        assert tx.high_water == 1
    check('finite_credit_hold_abort_restart_stale_epoch_and_commit', transaction_checks)
    raw = struct.pack('<64h', *([0] * 63 + [2048]))
    prefix = b'BR88\x01\x01' + struct.pack('<IHH4I3I', 1, 1, 0, 128, 0, 0, 0, 0, 0, 0) + raw
    packet = prefix + struct.pack('<I', zlib.crc32(prefix))
    check('raw_bypass', lambda: require(model.decode(packet, 1, reader)[0] == (0,) * 63 + (2048,)))
    check('crc_reject', lambda: reject(lambda: model.decode(packet[:-1] + bytes([packet[-1] ^ 1]), 1, reader)))
    return rows


def require(condition):
    if not condition:
        raise AssertionError('check failed')


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    entropy = ROOT / 'experiments/python-gamebub-v88/entropy'
    paths = [Path(__file__).resolve(), AREA / 'context.py', entropy / 'codec.py', entropy / 'data.py',
             entropy / 'index.json', ROOT / 'experiments/python-gamebub-v91/parser.py',
             ROOT / 'experiments/python-gamebub-v85/residual/data.py',
             ROOT / 'experiments/python-gamebub-v85/residual/index.json']
    for base in (entropy, ROOT / 'experiments/python-gamebub-v85/residual'):
        index = json.loads((base / 'index.json').read_text())
        paths.append(base / index['data']['path'])
    pins = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    report = dict(schema='cu66-v91b-context-model-v1', status='FAIL', source_sha256=pins,
                  parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  schedule='Per output: Random(910100 + source_ordinal*3 + plane).randrange(8) holds then one ready; consumer samples, not clock cycles.',
                  physical_30fps_proven=False, complete_under10ms_proven=False,
                  scope='Full residual chunk coefficients only; no pixel reconstruction, HUD, publication or FPGA memory fit. Packet CRC is software-prevalidated, not RTL.')
    start = time.monotonic()
    try:
        for path in paths:
            if path.suffix == '.py':
                target = out / 'sources' / path.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        model = load('v91b_context', AREA / 'context.py')
        word = load('v91b_word', ROOT / 'experiments/python-gamebub-v91/parser.py')
        frozen = load('v91b_frozen', entropy / 'codec.py')
        data = load('v91b_data', entropy / 'data.py')
        directed = run_checks(model, word.WordRice)
        (out / 'directed.json').write_text(json.dumps(directed, indent=2) + '\n')
        totals = dict(sources=0, chunks=0, coefficient_values=0, chunk_bytes=0,
                      sparse_writes=0, held_samples=0, pending_high_water=0,
                      contexts=0, zero_event_contexts=0, canonical_chunk_hash_matches=0)
        identities = set()
        with (out / 'chunks.jsonl').open('w') as target:
            for frame in data.iter_frames():
                identity = (frame['cohort'], frame['fid'])
                assert identity not in identities
                identities.add(identity)
                for plane, chunks in enumerate(frame['variants']['65536']):
                    for chunk_id, chunk in enumerate(chunks):
                        packet, blocks = chunk['br88'], chunk['blocks']
                        oracle = frozen.decode(packet, blocks)
                        contexts, raw = model.parse_chunk(packet, blocks)
                        # All-ready and adversarial consumer schedules must have
                        # identical final coefficients; stalled mode keeps at
                        # most one pending coefficient and no next-event decode.
                        ready, ready_stats = model.decode(packet, blocks, word.WordRice)
                        held, held_stats = model.decode(packet, blocks, word.WordRice,
                            epoch=frame['ordinal'], stalls=stall_samples(910100 + frame['ordinal'] * 3 + plane))
                        assert ready == held == tuple(oracle)
                        digest = hashlib.sha256(packed(held)).hexdigest()
                        assert digest == chunk['coefficient_sha256']
                        assert ready_stats['writes'] == held_stats['writes']
                        assert ready_stats['held_samples'] == 0
                        expected_writes = sum(context.event_count for context in contexts)
                        assert ready_stats['writes'] == expected_writes
                        assert held_stats['pending_high_water'] == int(expected_writes != 0)
                        row = dict(cohort=identity[0], fid=identity[1], ordinal=frame['ordinal'], plane=plane, chunk=chunk_id,
                                   blocks=blocks, bytes=len(packet), packet_sha256=sha_bytes(packet),
                                   coefficient_values=len(held), coefficient_sha256=digest,
                                   contexts=len(contexts), zero_event_contexts=sum(c.event_count == 0 for c in contexts),
                                   ready=ready_stats, stalled=held_stats, matches_frozen=True)
                        target.write(json.dumps(row, separators=(',', ':')) + '\n')
                        totals['chunks'] += 1
                        totals['coefficient_values'] += len(held)
                        totals['chunk_bytes'] += len(packet)
                        totals['sparse_writes'] += held_stats['writes']
                        totals['held_samples'] += held_stats['held_samples']
                        totals['pending_high_water'] = max(totals['pending_high_water'], held_stats['pending_high_water'])
                        totals['contexts'] += len(contexts)
                        totals['zero_event_contexts'] += row['zero_event_contexts']
                        totals['canonical_chunk_hash_matches'] += 1
                totals['sources'] += 1
                if totals['sources'] % 50 == 0:
                    print('V91B_MODEL_PROGRESS', totals['sources'], flush=True)
        assert totals['sources'] == 457 and totals['chunks'] == 1371
        assert pins == {path: sha(ROOT / path) for path in pins}
        report.update(status='PASS_FULL_CORPUS_SPARSE_CONTEXT_MODEL', totals=totals,
                      directed_checks=len(directed), directed_all_passed=all(row['status'] == 'PASS' for row in directed))
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        report['wall_seconds'] = time.monotonic() - start
        report['artifacts_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*') if path.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        selected = dict(report, selected_report=str((out / 'results.json').relative_to(ROOT)))
        (AREA / 'results.json').write_text(json.dumps(selected, indent=2) + '\n')
        print('V91B_MODEL', report['status'], out, flush=True)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


if __name__ == '__main__':
    main()
