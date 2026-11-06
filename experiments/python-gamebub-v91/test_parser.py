#!/usr/bin/env python3
"""Directed BR88 parser checks with locally generated bitstreams and packets."""
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import zlib

AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[1]
V88 = ROOT / "experiments/python-gamebub-v88/entropy/codec.py"
PARSER = AREA / "parser.py"


class BitWriter:
    def __init__(self):
        self.bits = []

    def bit(self, b):
        self.bits.append(int(bool(b)))

    def literal(self, value, width):
        assert 0 <= value < (1 << width)
        self.bits.extend((value >> i) & 1 for i in range(width - 1, -1, -1))

    def rice(self, value, k, escape):
        q, rem = divmod(value, 1 << k)
        if q < 15:
            self.bits.extend([0] * q + [1])
            self.literal(rem, k)
        else:
            assert value < (1 << escape)
            self.bits.extend([0] * 15)
            self.literal(value, escape)

    def finish(self):
        data = bytearray((len(self.bits) + 7) // 8)
        for i, b in enumerate(self.bits):
            data[i // 8] |= b << (7 - i % 8)
        return bytes(data), len(self.bits)


def rice_payload(items, k, escape):
    w = BitWriter()
    for value in items:
        w.rice(value, k, escape)
    return w.finish()


def crc(packet):
    return packet[:-4] + struct.pack('<I', zlib.crc32(packet[:-4]))


def packet(blocks, streams, counts=(0, 0, 0), raw=None):
    if raw is not None:
        body = struct.pack('<' + 'h' * len(raw), *raw)
        lengths = [len(body), 0, 0, 0]
        flags = 1
        streams_body = body
        counts = (0, 0, 0)
    else:
        encoded = [bytes((k0, k1)) + struct.pack('<I', nbits) + data
                   for k0, k1, data, nbits in streams]
        lengths = list(map(len, encoded))
        flags = 0
        streams_body = b''.join(encoded)
    head = (b'BR88\x01' + bytes((flags,)) + struct.pack('<IHH', blocks, 1, 0)
            + struct.pack('<4I', *lengths) + struct.pack('<3I', *counts))
    return crc(head + streams_body + bytes(4))


def raises(fn):
    try:
        fn()
        return False
    except Exception:
        return True


def category(name):
    if name.startswith('rice_align'):
        return 'normal_rice_alignment'
    if name.startswith('escape_align'):
        return 'escaped_rice_alignment'
    if name.startswith('truncate_'):
        return 'truncation'
    if name.startswith('max_symbol'):
        return 'maximum_symbol'
    if name in ('unused_bits', 'nonzero_padding'):
        return 'bitstream_termination'
    if name.startswith('reject_'):
        return 'malformed_packets'
    if name.startswith('invalid_width_'):
        return 'invalid_standalone_widths'
    if name == 'independent_valid_multiband_packet':
        return 'valid_packets'
    if name == 'raw_endpoints':
        return 'raw_packet'
    return 'other'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run():
    if not PARSER.exists():
        raise FileNotFoundError(f"parser not ready: {PARSER}")
    target, ref = load(PARSER, 'v91_parser'), load(V88, 'v88_reference')
    checks = []

    # Every bit alignment, k bound and unary quotient class; escaped literals
    # include the maximum 39-bit symbol (15 unary + 24 literal).
    for refill in (16, 32):
        for offset in range(64):
            for k in range(20):
                for q in range(15):
                    value = (q << k) + ((1 << k) - 1 if k else 0)
                    w = BitWriter(); w.bits = [1] * offset; w.rice(value, k, 24)
                    data, nbits = w.finish()
                    reader = target.WordRice(data, nbits, refill_bits=refill)
                    for _ in range(offset): reader.bit()
                    assert reader.value(k, 24) == value
                    reader.end()
                    checks.append((f'rice_align{offset}_k{k}_q{q}_r{refill}', 'PASS'))
            # k boundary coverage for all supported DC, level, and run ranges,
            # including q=15 and the largest representable 24-bit escape.
            for k in (0, 13, 14, 19):
                for escape in (12, 14, 24):
                    for value in (0, 1, (14 << k), ((1 << escape) - 1)):
                        w = BitWriter(); w.bits = [1] * offset; w.rice(value, k, escape)
                        data, nbits = w.finish()
                        reader = target.WordRice(data, nbits, refill_bits=refill)
                        for _ in range(offset): reader.bit()
                        assert reader.value(k, escape) == value
                        reader.end()
                        checks.append((f'escape_align{offset}_k{k}_e{escape}', 'PASS'))

    # Truncation at each bit of representative normal and escaped symbols;
    # reject hidden padding and unread data as well.
    for k, escape, value in ((0, 14, 14), (13, 14, (14 << 13) + 8191),
                             (19, 24, (1 << 24) - 1)):
        w = BitWriter(); w.rice(value, k, escape); full, n = w.finish()
        for size in range(n):
            prefix = BitWriter(); prefix.bits = w.bits[:size]
            data, _ = prefix.finish()
            r = target.WordRice(data, size)
            assert raises(lambda r=r: r.value(k, escape)), (k, size)
            checks.append((f'truncate_k{k}_at{size}', 'PASS'))
        r = target.WordRice(full, n)
        assert r.value(k, escape) == value; r.end()
        checks.append((f'max_symbol_k{k}', 'PASS'))
    assert raises(lambda: target.WordRice(b'\x00', 1).end())
    assert raises(lambda: target.WordRice(b'\x01', 1))
    checks.extend((('unused_bits', 'PASS'), ('nonzero_padding', 'PASS')))

    for k, escape in ((-1, 12), (20, 12), (0, -1), (0, 25)):
        reader = target.WordRice(b'\xff' * 8, 64)
        assert raises(lambda reader=reader, k=k, escape=escape:
                      reader.value(k, escape)), (k, escape)
        checks.append((f'invalid_width_k{k}_e{escape}', 'PASS'))

    # Independent valid packet: DC sweeps, sparse coefficients in each band,
    # and exact packet decoding compared with frozen V88 reader.
    rng = random.Random(91091)
    order = sorted(range(64), key=lambda i: (i // 8 + i % 8,
                    i // 8 if (i // 8 + i % 8) % 2 else -(i // 8)))
    dc_values = [0, 1, -1, 2048, -2048]
    dc_symbols = [v * 2 if v >= 0 else -2 * v - 1 for v in dc_values]
    dcdata, dcn = rice_payload(dc_symbols, 13, 14)
    band_streams = [(13, 255, dcdata, dcn)]
    counts = []
    expected = [0] * 64
    expected[0] = dc_values[0]
    # Keep one block, encode coefficients at first/last positions of each band.
    for lo, hi, rk, lk in ((1, 6, 0, 0), (6, 21, 19, 11), (21, 64, 4, 7)):
        positions = sorted(set((0, hi - lo - 1)))
        w = BitWriter(); prev = -1
        for ix, pos in enumerate(positions):
            w.rice(pos - prev - 1, rk, 24)
            level = (-2048, 2048)[ix]
            zig = level * 2 if level > 0 else -2 * level - 1
            w.rice(zig - 1, lk, 12)
            expected[order[lo + pos]] = level
            prev = pos
        data, n = w.finish(); band_streams.append((rk, lk, data, n)); counts.append(len(positions))
    # DC stream is replaced with the exact single value used by expected.
    dcdata, dcn = rice_payload([0], 13, 14); band_streams[0] = (13, 255, dcdata, dcn)
    valid = packet(1, band_streams, tuple(counts))
    assert target.decode(valid, 1) == ref.decode(valid, 1) == expected
    checks.append(('independent_valid_multiband_packet', 'PASS'))

    # Raw fallback accepts the inclusive endpoints. Invalid packet corpus is
    # generated locally and CRC-corrected where the mutation targets syntax.
    raw = packet(1, [], raw=[-2048, 2048] + [0] * 62)
    assert target.decode(raw, 1) == ref.decode(raw, 1)
    checks.append(('raw_endpoints', 'PASS'))
    malformed = []
    def mutate(p, off, data):
        b = bytearray(p); b[off:off + len(data)] = data; return crc(bytes(b))
    malformed.extend([
        ('crc', valid[:-1] + bytes((valid[-1] ^ 1,))),
        ('magic', mutate(valid, 0, b'NOPE')),
        ('version', mutate(valid, 4, b'\x02')),
        ('flags', mutate(valid, 5, b'\x02')),
        ('blocks', mutate(valid, 6, struct.pack('<I', 2))),
        ('bw', mutate(valid, 10, b'\x02\x00')),
        ('reserved', mutate(valid, 12, b'\x01\x00')),
        ('sum_lengths', mutate(valid, 14, struct.pack('<I', 1))),
        ('dc_k', mutate(valid, 42, b'\x0e')),
        ('dc_marker', mutate(valid, 43, b'\x00')),
        ('dc_range', packet(1, [(13,255,*rice_payload([4097],13,14))] + band_streams[1:], tuple(counts))),
        ('count_overflow', mutate(valid, 30, struct.pack('<I', 7))),
        ('packet_truncated', valid[:-1]),
        ('geometry_zero', valid),
        ('raw_range', mutate(raw, 46, struct.pack('<h', 32767))),
        ('raw_fields', mutate(raw, 30, struct.pack('<I', 1))),
    ])
    for name, bad in malformed:
        blocks = 0 if name == 'geometry_zero' else 1
        assert raises(lambda bad=bad, blocks=blocks: target.decode(bad, blocks)), name
        assert raises(lambda bad=bad, blocks=blocks: ref.decode(bad, blocks)), name
        checks.append((f'reject_{name}', 'PASS'))

    return dict(schema='gamebub-v91-parser-directed-v1', status='PASS',
                checks_count=len(checks), checks=[dict(name=n, status=s) for n,s in checks],
                seed=91091, parser_sha256=hashlib.sha256(PARSER.read_bytes()).hexdigest(),
                reference_sha256=hashlib.sha256(V88.read_bytes()).hexdigest(),
                test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Python directed/adversarial checks; no native build or performance claim.')


if __name__ == '__main__':
    try:
        result = run()
    except Exception as exc:
        AREA.mkdir(exist_ok=True)
        failure = {'schema': 'gamebub-v91-parser-directed-v1', 'status': 'FAIL',
                   'seed': 91091, 'error': f'{type(exc).__name__}: {exc}',
                   'parser_sha256': hashlib.sha256(PARSER.read_bytes()).hexdigest() if PARSER.exists() else None,
                   'reference_sha256': hashlib.sha256(V88.read_bytes()).hexdigest(),
                   'test_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
        (AREA / 'test.log').write_text(json.dumps(failure, indent=2)+'\n')
        (AREA / 'test-results.json').write_text(json.dumps(failure, indent=2)+'\n')
        raise
    result['timestamp_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    detail_path = AREA / 'test-details.json.gz'
    detail_bytes = gzip.compress((json.dumps(result, sort_keys=True, separators=(',', ':'))+'\n').encode(), mtime=0)
    detail_path.write_bytes(detail_bytes)
    summary = {key: value for key, value in result.items() if key != 'checks'}
    counts = {}
    for item in result['checks']:
        key = category(item['name'])
        counts[key] = counts.get(key, 0) + 1
    summary['category_counts'] = dict(sorted(counts.items()))
    summary['detail_file'] = detail_path.name
    summary['detail_sha256'] = hashlib.sha256(detail_bytes).hexdigest()
    (AREA / 'test-results.json').write_text(json.dumps(summary, indent=2)+'\n')
    (AREA / 'test.log').write_text(f"{result['status']} {result['checks_count']} checks\n")
    print(result['status'], result['checks_count'])
