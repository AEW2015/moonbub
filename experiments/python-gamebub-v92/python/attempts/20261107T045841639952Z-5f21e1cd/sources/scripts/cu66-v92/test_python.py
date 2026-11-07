#!/usr/bin/env python3
"""Strict independent EC92 fixtures; immutable attempts, pins and watchdog.

No encoder or previous decoder is imported. Fixed AB zero vectors and literal
Rice grammar fixtures exercise the parser independently of native fixtures.
"""

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import struct
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v92/python'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(body):
    return body + struct.pack('<I', zlib.crc32(body))


def literal_stream(bits, k0=0, k1=0):
    data = bytearray((len(bits) + 7) // 8)
    for index, bit in enumerate(bits):
        data[index // 8] |= int(bit) << (7 - index % 8)
    return struct.pack('<BBI', k0, k1, len(bits)) + data


def rice_literal(value, k, escape):
    quotient = value >> k
    if quotient >= 15:
        return '0' * 15 + format(value, '0%db' % escape)
    return '0' * quotient + '1' + (format(value & ((1 << k) - 1), '0%db' % k) if k else '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path,
                        default=ROOT / 'experiments/python-gamebub-v92/native/fixtures/manifest.json')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources = [Path(__file__).resolve(), AREA / 'codec.py']
    if args.fixtures.exists():
        sources.append(args.fixtures)
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    for path in sources:
        dest = out / 'sources' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    report = dict(schema='cu66-v92-independent-python-tests-v1', status='FAIL',
                  source_sha256=pins, watchdog_seconds=args.timeout,
                  physical_timing_proven=False, checks=[])
    started = time.monotonic()
    def timeout(signum, frame):
        raise TimeoutError('EC92 independent Python watchdog expired')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(args.timeout)
    try:
        spec = importlib.util.spec_from_file_location('ec92_independent_test', AREA / 'codec.py')
        codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codec)
        def packet(streams, mask=15, blocks=1, counts=(0, 0, 0), flags=0):
            return crc(codec.FRAME.pack(b'EC92', 1, flags, mask, 0, blocks, 1, 0,
                                        *map(len, streams), *counts) + b''.join(streams))
        def check(name, data, blocks, expected=None, accepted=True, bw=1):
            path = out / 'fixtures' / (name + '.ec92')
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
            try:
                values = codec.decode(data, blocks, bw)
            except ValueError:
                if accepted:
                    raise
                values = None
            else:
                assert accepted, ('unexpected accept', name)
                if expected is not None:
                    assert values == expected, ('coefficient mismatch', name)
            report['checks'].append(dict(name=name, accepted=accepted,
                                         packet_sha256=sha(path), blocks=blocks))
            return values
        def mutate(data, offset, value):
            body = bytearray(data[:-4])
            body[offset:offset + len(value)] = value
            return crc(body)
        dc_zero_br = literal_stream('1', 0, 255)
        ac_zero_br = literal_stream('')
        dc_zero_ab = struct.pack('<BBI', 0, 255, 19) + bytes.fromhex('a00000')
        ac_zero_ab = struct.pack('<BBI', 0, 0, 18) + bytes.fromhex('400000')
        # Fixed arithmetic vectors include termination, not a test encoder.
        for mask in range(16):
            streams = [dc_zero_br if mask & 1 else dc_zero_ab]
            streams += [ac_zero_br if mask & (1 << i) else ac_zero_ab for i in range(1, 4)]
            check('all16_zero_mask_%02d' % mask, packet(streams, mask), 1, [0] * 64)
        base_streams = [dc_zero_br] + [ac_zero_br] * 3
        base = packet(base_streams)
        # All DC k parameters, both signed boundaries, and explicit 15-zero escape.
        for value in (-2048, 2048):
            mapped = 2 * value if value >= 0 else -2 * value - 1
            for k in range(14):
                stream = literal_stream(rice_literal(mapped, k, 14), k, 255)
                check('dc_%d_k%d' % (value, k), packet([stream] + [ac_zero_br] * 3),
                      1, [value] + [0] * 63)
        # First/last positions in every band verify zigzag placement and flattening.
        blocks = 2
        for context, (lo, hi) in enumerate(zip((1, 6, 21), (6, 21, 64)), 1):
            width = hi - lo
            for last in (False, True):
                run = blocks * width - 1 if last else 0
                value = 2048 if last else -2048
                level = 2 * value - 1 if value > 0 else -2 * value - 2
                streams = [literal_stream('11', 0, 255)] + [ac_zero_br] * 3
                streams[context] = literal_stream(rice_literal(run, 0, 24) + rice_literal(level, 0, 12))
                counts = [0, 0, 0]
                counts[context - 1] = 1
                expected = [0] * 128
                expected[(blocks - 1 if last else 0) * 64 + codec.ORDER[hi - 1 if last else lo]] = value
                check('band%d_%s_boundary' % (context, 'last' if last else 'first'),
                      packet(streams, blocks=blocks, counts=counts), blocks, expected)
        raw_values = [-2048, 2048] * 32
        raw = packet([struct.pack('<64h', *raw_values), b'', b'', b''], mask=0, flags=1)
        check('raw_signed_boundaries', raw, 1, raw_values)
        # Upper block bound and long context traverse without allocating a raw fixture.
        max_blocks = 65536
        check('maximum_block_count', packet([literal_stream('1' * max_blocks, 0, 255)] +
              [ac_zero_br] * 3, blocks=max_blocks), max_blocks, [0] * (max_blocks * 64))
        invalid = [
            ('magic', 0, b'BAD!'), ('version', 4, b'\x02'), ('flags', 5, b'\x02'),
            ('mask_reserved', 6, b'\x10'), ('reserved8', 7, b'\x01'),
            ('block_binding', 8, struct.pack('<I', 2)), ('predictor', 12, b'\x02\x00'),
            ('reserved16', 14, b'\x01\x00'), ('length_sum', 16, struct.pack('<I', 1)),
            ('ac_count_bound', 32, struct.pack('<I', 6)), ('dc_k_bound', 44, b'\x0e'),
            ('dc_marker', 45, b'\x00'), ('dc_bitcount', 46, struct.pack('<I', 0)),
            ('dc_padding', 50, b'\x81'),
        ]
        for name, offset, value in invalid:
            check('reject_' + name, mutate(base, offset, value), 1, accepted=False)
        for name, data, blocks, bw in (
            ('crc', base[:-1] + bytes([base[-1] ^ 1]), 1, 1),
            ('truncated', base[:-1], 1, 1), ('trailing', base + b'\x00', 1, 1),
            ('trailing_valid_crc', crc(base[:-4] + b'\x00'), 1, 1),
            ('zero_blocks', base, 0, 1), ('large_blocks', base, 65537, 1),
            ('boolean_blocks', base, True, 1), ('bw', base, 1, 2),
            ('raw_mask', mutate(raw, 6, b'\x01'), 1, 1),
            ('raw_count', mutate(raw, 32, struct.pack('<I', 1)), 1, 1),
            ('raw_range', mutate(raw, 44, struct.pack('<h', 2049)), 1, 1),
            ('raw_length', mutate(raw, 16, struct.pack('<II', 127, 1)), 1, 1),
            ('coded_payload_equals_raw', mutate(raw, 5, b'\x00'), 1, 1),
        ):
            check('reject_' + name, data, blocks, accepted=False, bw=bw)
        for context in range(4):
            streams = list(base_streams)
            streams[context] = literal_stream('11', 0, 255) if context == 0 else literal_stream('1')
            check('reject_unused_bits_context%d' % context, packet(streams), 1, accepted=False)
            streams = [dc_zero_ab] + [ac_zero_ab] * 3
            bad = bytearray(streams[context]); bad[-1] |= 1
            streams[context] = bytes(bad)
            check('reject_arithmetic_padding_context%d' % context, packet(streams, mask=0), 1, accepted=False)
            streams = [dc_zero_ab] + [ac_zero_ab] * 3
            bad = bytearray(streams[context])
            # Change a declared termination bit while preserving zero byte padding.
            bad[-1] |= 0x20 if context == 0 else 0x40
            streams[context] = bytes(bad)
            check('reject_arithmetic_termination_context%d' % context, packet(streams, mask=0), 1, accepted=False)
            streams = [dc_zero_ab] + [ac_zero_ab] * 3
            bad = bytearray(streams[context])
            bad[2:6] = struct.pack('<I', 20 if context == 0 else 19)
            streams[context] = bytes(bad)
            check('reject_arithmetic_unused_context%d' % context, packet(streams, mask=0), 1, accepted=False)
            streams = list(base_streams)
            streams[context] = bytes([20, 0]) + streams[context][2:]
            check('reject_rice_k_context%d' % context, packet(streams), 1, accepted=False)
            streams = list(base_streams)
            streams[context] = literal_stream('0' * 14, 0, 255) if context == 0 else literal_stream('0' * 14)
            counts = [0, 0, 0]
            if context:
                counts[context - 1] = 1
            check('reject_unterminated_unary_context%d' % context, packet(streams, counts=counts), 1, accepted=False)
        for value, name in ((2049, 'dc_range'),):
            stream = literal_stream(rice_literal(value * 2, 0, 14), 0, 255)
            check('reject_' + name, packet([stream] + [ac_zero_br] * 3), 1, accepted=False)
        for context in range(1, 4):
            width = (5, 15, 43)[context - 1]
            streams = list(base_streams)
            streams[context] = literal_stream(rice_literal(width, 0, 24) + '1')
            counts = [0, 0, 0]; counts[context - 1] = 1
            check('reject_run_overflow_context%d' % context, packet(streams, counts=counts), 1, accepted=False)
        native_count = 0
        if args.fixtures.exists():
            fixture_manifest = json.loads(args.fixtures.read_text())
            for fixture in fixture_manifest['fixtures']:
                fixture_path = args.fixtures.parent / fixture['path']
                data = fixture_path.read_bytes()
                values = check('native_' + fixture_path.stem, data, fixture['blocks'])
                packed = struct.pack('<' + 'h' * len(values), *values)
                assert hashlib.sha256(packed).hexdigest() == fixture['coefficient_sha256']
                pins[str(fixture_path.relative_to(ROOT))] = sha(fixture_path)
                native_count += 1
        assert pins == {name: sha(ROOT / name) for name in pins}, 'executed sources changed'
        report.update(status='PASS_INDEPENDENT_EC92_STRICT_GRAMMAR', checks_count=len(report['checks']),
                      native_fixtures=native_count, source_sha256=pins,
                      scope='Exact EC92 coefficient syntax and native fixtures; no frame, pixels, reference or hardware timing claim.')
    except BaseException as error:
        report['error'] = repr(error)
        raise
    finally:
        signal.alarm(0)
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print(report['status'], out / 'results.json', flush=True)
    (AREA / 'index.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')


if __name__ == '__main__':
    main()
