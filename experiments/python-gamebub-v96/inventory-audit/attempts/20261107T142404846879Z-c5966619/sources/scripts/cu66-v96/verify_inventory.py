#!/usr/bin/env python3
"""Independent reader of every V96 research descriptor against frozen targets.

Never imports the V96 encoder/parser. Cross-position sources must exist in the
bounded accepted-frame FIFO dictionary; all destination tiles are materialized.
"""
from collections import Counter, deque
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import struct
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v96/inventory-audit'
COUNTS = (5400, 1350, 1350)
BASES = (0, 345600, 432000)
STARTS = (0, 5400, 6750)
PROFILES = ('control', 'cross64', 'cross256')
SLOTS = (0, 64, 256)
DESCRIPTOR = struct.Struct('<BBHHBBIIII')


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def bounded_positions(tiles, limit):
    positions = []
    for start, count in zip(STARTS, COUNTS):
        order, values = deque(), {}
        if limit:
            for local in range(count):
                value = tiles[start + local]
                if value in values:
                    continue
                if len(order) == limit:
                    del values[order.popleft()]
                order.append(value)
                values[value] = local
        positions.append(values)
    return positions


def read_exact(stream, count):
    result = stream.read(count)
    assert len(result) == count, ('truncated archive', count, len(result))
    return result


def packets(attempt, report):
    for shard in report['shards']:
        path = attempt / shard['path']
        assert sha(path) == shard['gzip_sha256']
        digest, size, records = hashlib.sha256(), 0, 0
        with gzip.open(path, 'rb') as stream:
            while True:
                head = stream.read(4)
                if not head:
                    break
                assert len(head) == 4
                length, = struct.unpack('<I', head)
                assert 1 <= length <= 32768
                raw_meta = read_exact(stream, length)
                digest.update(head + raw_meta)
                size += 4 + length
                meta = json.loads(raw_meta)
                variants = []
                for _ in range(3):
                    head = read_exact(stream, 4)
                    length, = struct.unpack('<I', head)
                    assert 194400 <= length <= 1024 * 1024
                    value = read_exact(stream, length)
                    variants.append(value)
                    digest.update(head + value)
                    size += 4 + length
                records += 1
                yield meta, variants
        assert (records, size, digest.hexdigest()) == (shard['frames'], shard['raw_bytes'], shard['raw_sha256'])


def decode(packet, frame, accepted, slot_limit, expected_profile, totals):
    assert packet[:8] == b'V96RS01\0'
    length, count = struct.unpack_from('<II', packet, 8)
    assert 1 <= length <= 8192 and count == 8100
    header = json.loads(packet[16:16 + length])
    assert header['profile'] == expected_profile
    assert header['schema'] == 'v96-addressed-research-stream-1'
    assert header['tile_count'] == 8100 and header['tile_bytes'] == 64 and header['descriptor_bytes'] == 24
    for name in ('cohort', 'ordinal', 'fid', 'refid', 'key', 'canonical_sha256'):
        assert header[name] == frame[name], name
    assert header['epoch'] == frame['cohort'] + 1
    assert header['destination_generation'] == frame['ordinal'] + 1
    assert header['accepted_generation'] == (frame['ordinal'] if accepted else None)
    assert header['accepted_fid'] == (accepted['fid'] if accepted else None)
    assert header['plane_counts'] == list(COUNTS) and header['plane_bases'] == list(BASES)
    assert header['bank_stride_bytes'] == 1 << 23
    assert header['dictionary_slots_per_plane'] == slot_limit
    assert header['no_sameframe_dependencies'] is True
    assert header['destination_bank'] in range(3)
    if accepted:
        assert header['source_bank'] == accepted['bank']
        assert header['source_bank'] != header['destination_bank']
    else:
        assert header['source_bank'] is None and frame['key']
    dictionaries = bounded_positions(accepted['tiles'], slot_limit) if accepted else [{}, {}, {}]
    at, samples, ops = 16 + length, [], Counter()
    for plane, (start, tile_count, base) in enumerate(zip(STARTS, COUNTS, BASES)):
        for local in range(tile_count):
            assert at + 24 <= len(packet)
            op, axis, dst, src, db, sb, dr, dg, sr, sg = DESCRIPTOR.unpack_from(packet, at)
            at += 24
            assert op <= 3 and axis == plane and dst == local and db == header['destination_bank']
            assert dr == local * 64 and dg == (db << 23) + base + dr
            assert base + dr + 64 <= 518400
            global_pos = start + local
            if frame['hidden_mask'][global_pos]:
                assert op == 2
            elif frame['copy_ref_mask'][global_pos]:
                assert op == 1
            elif op != 0:
                assert op == 3 and expected_profile != 'control'
            if op in (1, 3):
                assert accepted and not frame['key'] and sb == accepted['bank'] and sb != db
                assert src < tile_count and sr == src * 64 and sg == (sb << 23) + base + sr
                assert (src == local) == (op == 1)
                value = accepted['tiles'][start + src]
                if op == 3:
                    assert dictionaries[plane].get(value) == src
                ops['COPY_REF' if op == 1 else 'CROSSCOPY'] += 1
            else:
                assert (src, sb, sr, sg) == (65535, 255, 0xffffffff, 0xffffffff)
                if op == 0:
                    assert at + 64 <= len(packet)
                    value = packet[at:at + 64]
                    at += 64
                    ops['FALLBACK'] += 1
                else:
                    value = bytes([128]) * 64
                    ops['CONST128'] += 1
            assert value == frame['tiles'][global_pos], (expected_profile, frame['fid'], plane, local)
            samples.append(value)
    assert at == len(packet)
    totals.update(ops)
    totals.update(frames=1, stream_bytes=len(packet), descriptor_bytes=8100 * 24,
                  header_bytes=16 + length, fallback_bytes=64 * ops['FALLBACK'])
    return header, samples, ops


def main():
    out = AREA / 'attempts' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    pointer = ROOT / 'experiments/python-gamebub-v96/inventory/index.json'
    index = json.loads(pointer.read_text())
    selected = ROOT / index['selected_report']
    report = json.loads(selected.read_text())
    assert report['status'] == 'PASS_ALL457_EXACT_ADDRESSED_STREAMS'
    sources = [Path(__file__).resolve(), pointer, selected, ROOT / 'experiments/python-gamebub-v82/native/data.py', ROOT / 'experiments/python-gamebub-v82/native/index.json']
    sources += sorted((ROOT / 'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    result = dict(schema='cu66-v96-independent-inventory-v1', status='FAIL', source_sha256=pins,
                  encoder_imported=False, hardware_tested=False)
    for path in sources:
        if path.suffix != '.gz':
            target = out / 'sources' / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
    started = time.monotonic()
    def expired(signum, frame):
        raise TimeoutError('independent V96 inventory watchdog')
    prior = signal.signal(signal.SIGALRM, expired)
    signal.alarm(600)
    try:
        spec = importlib.util.spec_from_file_location('v96_frozen_tiles', ROOT / 'experiments/python-gamebub-v82/native/data.py')
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)
        cohort, accepted, frames = None, None, 0
        totals = {profile: Counter() for profile in PROFILES}
        for frame, (meta, variants) in zip(native.iter_frames(), packets(selected.parent, report), strict=True):
            if cohort != frame['cohort']:
                cohort, accepted = frame['cohort'], None
            assert meta['cohort'] == frame['cohort'] and meta['fid'] == frame['fid']
            dest_bank = None
            for profile, limit, packet in zip(PROFILES, SLOTS, variants):
                expected = meta['profiles'][profile]
                assert hashlib.sha256(packet).hexdigest() == expected['stream_sha256']
                header, samples, ops = decode(packet, frame, accepted, limit, profile, totals[profile])
                assert hashlib.sha256(b''.join(samples)).hexdigest() == expected['tile_major_sha256']
                assert all(ops.get(name, 0) == expected['ops'][name] for name in ('FALLBACK', 'COPY_REF', 'CONST128', 'CROSSCOPY'))
                copies = ops['COPY_REF'] + ops['CROSSCOPY']
                fence = expected['materialization_fence']
                assert fence['source_read_bytes'] == copies * 64 and fence['destination_write_bytes'] == 518400
                assert fence['source_read_words16'] == copies * 32 and fence['destination_write_words16'] == 259200
                assert fence['const_generated_bytes'] == ops['CONST128'] * 64
                if dest_bank is not None:
                    assert dest_bank == header['destination_bank']
                dest_bank = header['destination_bank']
            accepted = dict(frame, bank=dest_bank)
            frames += 1
        assert frames == 457
        assert pins == {name: sha(ROOT / name) for name in pins}
        result.update(status='PASS_ALL457_INDEPENDENT_ADDRESSED_MATERIALIZATION', frames=frames,
                      streams=frames * 3, independently_checked_tiles=frames * 3 * 8100,
                      totals=totals, scope='Byte-for-byte target tiles, accepted reference sources, bounded dictionary membership, physical addresses and complete research stream bytes. Full raster/HUD/root/seal are inherited target commitments, not new reconstructed HUD or RTL qualification.')
    except BaseException as error:
        result['failure'] = repr(error)
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prior)
        result['wall_seconds'] = time.monotonic() - started
        result['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'results.json'}
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        if result['status'].startswith('PASS'):
            (AREA / 'results.json').write_text(json.dumps(dict(result, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
    print(result['status'], 'streams', result.get('streams'))


if __name__ == '__main__':
    main()
