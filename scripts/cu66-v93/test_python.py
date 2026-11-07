#!/usr/bin/env python3
"""Independent EC93 fixtures with immutable attempts, snapshot pins, watchdog.

No encoder is imported. Literal arithmetic prefixes use initially equal,
previously untouched contexts; their final two declared bits are zero.
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
AREA = ROOT / 'experiments/python-gamebub-v93/python'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(body):
    return body + struct.pack('<I', zlib.crc32(body))


def bitbytes(bits):
    data = bytearray((len(bits) + 7) // 8)
    for index, bit in enumerate(bits):
        data[index // 8] |= int(bit) << (7 - index % 8)
    return bytes(data)


def literal_stream(bits, k0=0, k1=0):
    return struct.pack('<BBI', k0, k1, len(bits)) + bitbytes(bits)


def hybrid(prefix, size, suffix='', k0=0, k1=0):
    return struct.pack('<BBII', k0, k1, size, len(suffix)) + bytes.fromhex(prefix) + bitbytes(suffix)


def groups(parts):
    return struct.pack('<BBI', 32, 0, len(parts)) + b''.join(parts)


def rice_literal(value, k, escape):
    quotient = value >> k
    if quotient >= 15:
        return '0' * 15 + format(value, '0%db' % escape)
    return '0' * quotient + '1' + (format(value & ((1 << k) - 1), '0%db' % k) if k else '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path,
                        default=ROOT / 'experiments/python-gamebub-v93/native/fixtures/manifest.json')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    sources = [Path(__file__).resolve(), AREA / 'codec.py']
    if args.fixtures.exists():
        sources.append(args.fixtures)
    pins = {}
    def pin(path):
        name = str(path.relative_to(ROOT))
        digest = sha(path)
        if name in pins:
            assert pins[name] == digest, 'pinned input changed'
        pins[name] = digest
        dest = out / 'sources' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
    for path in sources:
        pin(path)
    report = dict(schema='cu66-v93-independent-python-tests-v1', status='FAIL',
                  source_sha256=pins, watchdog_seconds=args.timeout,
                  physical_timing_proven=False, checks=[])
    started = time.monotonic()
    def timeout(signum, frame):
        raise TimeoutError('EC93 independent Python watchdog expired')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(args.timeout)
    try:
        spec = importlib.util.spec_from_file_location('ec93_independent_test', AREA / 'codec.py')
        codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codec)
        def packet(streams, selector=85, blocks=1, counts=(0, 0, 0), flags=0):
            return crc(codec.FRAME.pack(b'EC93', 1, flags, selector, 0, blocks, 1, 0,
                                        *map(len, streams), *counts) + b''.join(streams))
        def check(name, data, blocks, expected=None, accepted=True, bw=1):
            path = out / 'fixtures' / (name + '.ec93')
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
        dc_br = literal_stream('1', 0, 255)
        ac_br = literal_stream('')
        dc_ab = struct.pack('<BBI', 0, 255, 19) + bytes.fromhex('a00000')
        ac_ab = struct.pack('<BBI', 0, 0, 18) + bytes.fromhex('400000')
        dc_hy = hybrid('a00000', 19, k1=255)
        ac_hy = hybrid('400000', 18)
        dc_choices = [dc_ab, dc_br, dc_hy, groups([dc_br])]
        ac_choices = [ac_ab, ac_br, ac_hy, groups([])]
        for selector in range(256):
            streams = [dc_choices[selector & 3]]
            streams += [ac_choices[(selector >> (i * 2)) & 3] for i in range(1, 4)]
            check('all256_zero_selector_%03d' % selector, packet(streams, selector), 1, [0] * 64)
        base_streams = [dc_br] + [ac_br] * 3
        base = packet(base_streams)
        # DC Rice parameters and signed boundaries, with an explicit escape.
        for value in (-2048, 2048):
            mapped = 2 * value if value >= 0 else -2 * value - 1
            for k in range(14):
                stream = literal_stream(rice_literal(mapped, k, 14), k, 255)
                check('dc_%d_k%d' % (value, k), packet([stream] + [ac_br] * 3),
                      1, [value] + [0] * 63)
            # Unary q=0, all thirteen suffix bits separately coded.
            stream = hybrid('a00000', 19, format(mapped, '013b'), 13, 255)
            check('hy_dc_%d_suffix_boundary' % value, packet([stream] + [ac_br] * 3, 86),
                  1, [value] + [0] * 63)
            # Fifteen untouched prefix contexts emit 15 zero unary symbols.
            stream = hybrid('0000800000', 33, format(mapped, '014b'), 0, 255)
            check('hy_dc_%d_escape' % value, packet([stream] + [ac_br] * 3, 86),
                  1, [value] + [0] * 63)
        # Literal unary 1 at run context 0 and 01 at level contexts 48/49.
        for context, (lo, hi) in enumerate(zip((1, 6, 21), (6, 21, 64)), 1):
            width = hi - lo
            for last in (False, True):
                run = 2 * width - 1 if last else 0
                value = 2048 if last else -2048
                level = 2 * value - 1 if value > 0 else -2 * value - 2
                counts = [0, 0, 0]; counts[context - 1] = 1
                expected = [0] * 128
                expected[(1 if last else 0) * 64 + codec.ORDER[hi - 1 if last else lo]] = value
                streams = [literal_stream('11', 0, 255)] + [ac_br] * 3
                streams[context] = literal_stream(rice_literal(run, 0, 24) + rice_literal(level, 0, 12))
                check('br_band%d_%s_boundary' % (context, last), packet(streams, blocks=2, counts=counts), 2, expected)
                # At this k the run quotient is zero; the level quotient is one.
                streams[context] = hybrid('a80000', 21, format(run, '019b') + format(level & 2047, '011b'), 19, 11)
                selector = 85 + (1 << (2 * context))
                check('hy_band%d_%s_boundary' % (context, last), packet(streams, selector, 2, counts), 2, expected)
        # SG32 group boundaries for both DC values and interleaved AC events.
        for count in (31, 32, 33, 64, 65):
            parts = []
            values = [(-1 if i & 1 else 1) for i in range(count)]
            for start in range(0, count, 32):
                bits = ''.join(rice_literal(2 * v if v >= 0 else -2 * v - 1, 0, 14) for v in values[start:start + 32])
                parts.append(literal_stream(bits, 0, 255))
            expected = [0] * (count * 64); expected[::64] = values
            check('sg_dc_%d' % count, packet([groups(parts)] + [ac_br] * 3, 87, count), count, expected)
            for context in range(1, 4):
                width = (5, 15, 43)[context - 1]
                blocks = (count * 2 + width - 1) // width
                counts = [0, 0, 0]; counts[context - 1] = count
                parts = [literal_stream('011' * min(32, count - start), 0, 0) for start in range(0, count, 32)]
                streams = [literal_stream('1' * blocks, 0, 255)] + [ac_br] * 3
                streams[context] = groups(parts)
                expected = [0] * (blocks * 64)
                for event in range(count):
                    position = event * 2 + 1
                    expected[(position // width) * 64 + codec.ORDER[(1, 6, 21)[context - 1] + position % width]] = -1
                check('sg_ac%d_%d' % (context, count), packet(streams, 85 + (2 << (2 * context)), blocks, counts), blocks, expected)
        raw_values = [-2048, 2048] * 32
        raw = packet([struct.pack('<64h', *raw_values), b'', b'', b''], selector=0, flags=1)
        check('raw_signed_boundaries', raw, 1, raw_values)
        max_blocks = 65536
        check('maximum_block_count', packet([literal_stream('1' * max_blocks, 0, 255)] +
              [ac_br] * 3, blocks=max_blocks), max_blocks, [0] * (max_blocks * 64))
        invalid = [
            ('magic', 0, b'BAD!'), ('version', 4, b'\x02'), ('flags', 5, b'\x02'),
            ('reserved8', 7, b'\x01'), ('block_binding', 8, struct.pack('<I', 2)),
            ('predictor', 12, b'\x02\x00'), ('reserved16', 14, b'\x01\x00'),
            ('length_sum', 16, struct.pack('<I', 1)), ('ac_count_bound', 32, struct.pack('<I', 6)),
            ('dc_k_bound', 44, b'\x0e'), ('dc_marker', 45, b'\x00'),
            ('dc_bitcount', 46, struct.pack('<I', 0)), ('dc_padding', 50, b'\x81'),
        ]
        for name, offset, value in invalid:
            check('reject_' + name, mutate(base, offset, value), 1, accepted=False)
        for name, data, blocks, bw in (
            ('crc', base[:-1] + bytes([base[-1] ^ 1]), 1, 1),
            ('truncated', base[:-1], 1, 1), ('trailing', base + b'\x00', 1, 1),
            ('trailing_valid_crc', crc(base[:-4] + b'\x00'), 1, 1),
            ('zero_blocks', base, 0, 1), ('large_blocks', base, 65537, 1),
            ('boolean_blocks', base, True, 1), ('bw', base, 1, 2),
            ('raw_selector', mutate(raw, 6, b'\x01'), 1, 1),
            ('raw_count', mutate(raw, 32, struct.pack('<I', 1)), 1, 1),
            ('raw_range', mutate(raw, 44, struct.pack('<h', 2049)), 1, 1),
            ('raw_length', mutate(raw, 16, struct.pack('<II', 127, 1)), 1, 1),
            ('coded_payload_equals_raw', mutate(raw, 5, b'\x00'), 1, 1),
        ):
            check('reject_' + name, data, blocks, accepted=False, bw=bw)
        for context in range(4):
            for method in range(4):
                selector = 85 + ((method - 1) << (2 * context))
                good = dc_choices[method] if context == 0 else ac_choices[method]
                streams = list(base_streams)
                # All methods must reject extra payload, even after zero AC events.
                streams[context] = good + b'\x00'
                check('reject_extra_c%d_m%d' % (context, method), packet(streams, selector), 1, accepted=False)
                if method in (0, 2):
                    streams[context] = good
                    bad = bytearray(good); bad[-1] |= 1
                    streams[context] = bytes(bad)
                    check('reject_arith_padding_c%d_m%d' % (context, method), packet(streams, selector), 1, accepted=False)
                    bad = bytearray(good); bad[-1] |= 0x20 if context == 0 else 0x40
                    streams[context] = bytes(bad)
                    check('reject_arith_terminal_c%d_m%d' % (context, method), packet(streams, selector), 1, accepted=False)
                if method == 3:
                    for label, offset, replacement in (
                        ('groupsize', 0, b'\x1f'), ('reserved', 1, b'\x01'),
                        ('groupcount', 2, struct.pack('<I', 2)),
                    ):
                        bad = bytearray(good); bad[offset:offset + len(replacement)] = replacement
                        streams[context] = bytes(bad)
                        check('reject_sg_%s_c%d' % (label, context), packet(streams, selector), 1, accepted=False)
                else:
                    bad = bytearray(good); bad[0] = 20
                    streams[context] = bytes(bad)
                    check('reject_k_c%d_m%d' % (context, method), packet(streams, selector), 1, accepted=False)
            # Separate suffix padding, excess suffix, and insufficient suffix bits.
            for suffix, k, label in (('1', 0, 'unused'), ('01', 1, 'extra'), ('', 1, 'missing')):
                streams = list(base_streams)
                streams[context] = hybrid('a00000' if context == 0 else 'd00000', 19 if context == 0 else 20,
                                          suffix, k, 255 if context == 0 else 0)
                counts = [0, 0, 0]
                if context:
                    counts[context - 1] = 1
                check('reject_hy_suffix_%s_c%d' % (label, context), packet(streams, 85 + (1 << (2 * context)), counts=counts), 1, accepted=False)
        # AC run overflow and DC out-of-profile symbols.
        check('reject_dc_range', packet([literal_stream(rice_literal(4098, 0, 14), 0, 255)] + [ac_br] * 3), 1, accepted=False)
        for context in range(1, 4):
            width = (5, 15, 43)[context - 1]
            streams = list(base_streams)
            streams[context] = literal_stream(rice_literal(width, 0, 24) + '1')
            counts = [0, 0, 0]; counts[context - 1] = 1
            check('reject_run_overflow_context%d' % context, packet(streams, counts=counts), 1, accepted=False)
        # Direct grouped grammar checks bypass packet fallback size as appropriate.
        def context_reject(name, stream, context=0, count=1, blocks=1):
            try:
                codec.decode_context(stream, context, count, blocks, 3)
            except ValueError:
                report['checks'].append(dict(name=name, accepted=False, context_only=True))
            else:
                raise AssertionError(('unexpected context accept', name))
        context_reject('reject_sg_missing_group', groups([]))
        context_reject('reject_sg_truncated_group', groups([b'\x00']))
        context_reject('reject_sg_group_length', groups([struct.pack('<BBI', 0, 255, 100)]))
        context_reject('reject_sg_group_padding', groups([literal_stream('1', 0, 255)[:-1] + b'\x81']))
        context_reject('reject_sg_group_unused', groups([literal_stream('11', 0, 255)]))
        context_reject('reject_sg_dc_k', groups([literal_stream('1', 14, 255)]))
        context_reject('reject_sg_dc_marker', groups([literal_stream('1', 0, 0)]))
        context_reject('reject_sg_ac_k', groups([literal_stream('11', 20, 0)]), 1)
        context_reject('reject_sg_ac_level_k', groups([literal_stream('11', 0, 12)]), 1)
        context_reject('reject_sg_run_across_group', groups([literal_stream('11' * 32), literal_stream('00001' + '1')]), 1, 33, 7)
        native_count = 0
        native_selectors = set()
        if args.fixtures.exists():
            fixture_manifest = json.loads(args.fixtures.read_text())
            for fixture in fixture_manifest['fixtures']:
                fixture_path = args.fixtures.parent / fixture['path']
                pin(fixture_path)
                data = fixture_path.read_bytes()
                values = check('native_' + fixture_path.stem, data, fixture['blocks'])
                packed = struct.pack('<' + 'h' * len(values), *values)
                assert hashlib.sha256(packed).hexdigest() == fixture['coefficient_sha256']
                if data[5] == 0:
                    native_selectors.add(data[6])
                native_count += 1
            assert native_selectors == set(range(256)), 'native fixtures must cover all 256 selectors'
        assert pins == {name: sha(ROOT / name) for name in pins}, 'executed sources changed'
        report.update(status='PASS_INDEPENDENT_EC93_STRICT_GRAMMAR', checks_count=len(report['checks']),
                      native_fixtures=native_count, native_selector_count=len(native_selectors), source_sha256=pins,
                      scope='Exact EC93 coefficient syntax and native fixtures; no frame, pixels, reference or hardware timing claim.')
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
