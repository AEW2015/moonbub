#!/usr/bin/env python3
"""Independent V95 pixel-palette grammar tests and native/archive parity.

Fixture construction is local to this test, never imported by the reader.
Synthetic UI/HUD, motion, noise and scene-change samples are grammar evidence;
they are not raw-capture coverage or measured predecode/pixel-generation cost.
"""

import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import signal
import struct
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95/python'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bitbytes(bits):
    return bytes(sum(int(v) << (7 - j) for j, v in enumerate(bits[i:i + 8]))
                 for i in range(0, len(bits), 8))


def encoded_indices(values, width):
    return bitbytes(''.join(format(v, '0%db' % width) if width else '' for v in values))


def own(kind, palette, body=b''):
    return bytes([kind, len(palette), *palette]) + body


def pack(pixels, palette):
    width = (len(palette) - 1).bit_length()
    return own(0, palette, encoded_indices([palette.index(v) for v in pixels], width))


def pred(palette, instructions):
    width = (len(palette) - 1).bit_length()
    body = b''
    for op, run, indices in instructions:
        body += bytes([(op << 6) | (run - 1)])
        if op == 2:
            body += encoded_indices(indices, width)
    return own(1, palette, body)


def esc(pixels, palette):
    width, bits = len(palette).bit_length(), ''
    for pixel in pixels:
        index = palette.index(pixel) if pixel in palette else len(palette)
        bits += format(index, '0%db' % width)
        if index == len(palette):
            bits += format(pixel, '08b')
    return own(2, palette, bitbytes(bits))


def plane(entries, residual_blocks=0, entropy=b''):
    return (struct.pack('>I', len(entries)) +
            b''.join(struct.pack('>HH', pos, len(rec)) + rec for pos, rec in entries) +
            struct.pack('>II', residual_blocks, len(entropy)) + entropy)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)
    pins, checks, fixtures, synthetic = {}, [], [], []
    report = dict(schema='cu66-v95-independent-python-tests-v1', status='FAIL',
                  watchdog_seconds=args.timeout, physical_timing_proven=False,
                  predecoded_pixel_generation_cost_measured=False,
                  source_sha256=pins, checks=checks, synthetic=synthetic,
                  raw_capture_coverage_claim=False)
    started = time.monotonic()

    def pin(path):
        path = path.resolve()
        name = str(path.relative_to(ROOT))
        digest = sha(path)
        if name in pins:
            assert pins[name] == digest, ('input changed', name)
        else:
            pins[name] = digest
            dest = out / 'sources' / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
        return path

    def timeout(signum, frame):
        raise TimeoutError('V95 independent Python watchdog expired')

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(args.timeout)
    try:
        pin(Path(__file__))
        pin(AREA / 'codec.py')
        spec = importlib.util.spec_from_file_location('v95_independent_test', AREA / 'codec.py')
        codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codec)

        def check(name, call, expected=None, accepted=True):
            try:
                result = call()
            except ValueError:
                assert not accepted, ('unexpected rejection', name)
            else:
                assert accepted, ('unexpected acceptance', name)
                if expected is not None:
                    assert result == expected, ('mismatch', name)
            checks.append(dict(name=name, accepted=accepted))

        def good(name, record, pixels, previous=None, next_palette='infer'):
            if next_palette == 'infer':
                next_palette = previous if record[0] == 4 else None if record[0] == 3 else tuple(record[2:2 + record[1]])
            check(name, lambda: codec.decode(record, previous), (bytes(pixels), next_palette))
            fixtures.append((name, record, previous))
            return record

        def bad(name, record, previous=None):
            check('reject_' + name, lambda: codec.decode(record, previous), accepted=False)

        for count in range(1, 9):
            palette = tuple(range(11, 11 + 17 * count, 17))
            pixels = bytes(palette[i % count] for i in range(64))
            good('PACK_count_%d' % count, pack(pixels, palette), pixels)
            good('PRED_literal_count_%d' % count,
                 pred(palette, [(2, 64, [i % count for i in range(64)])]), pixels)
            good('ESC_count_%d' % count, esc(pixels, palette), pixels)
            for kind, record in ((0, pack(pixels, palette)),
                                 (1, pred(palette, [(2, 64, [i % count for i in range(64)])])),
                                 (2, esc(pixels, palette))):
                good('REUSE_kind_%d_count_%d' % (kind, count),
                     bytes([4, kind, 0]) + record[2 + count:], pixels, palette)
        palette = (10, 20, 30)
        row = [0, 1, 2, 1, 0, 1, 2, 1]
        top = good('TOP_sequential_across_rows', pred(palette, [(2, 8, row), (0, 56, [])]),
                   bytes(palette[i] for i in row) * 8)
        left_ops = [(op, run, values) for _ in range(8)
                    for op, run, values in ((2, 1, [1]), (1, 7, []))]
        good('LEFT_each_row', pred(palette, left_ops), bytes([20] * 64))
        good('zero_bit_singleton_LITERAL', pred((99,), [(2, 64, [])]), bytes([99] * 64))
        maximum = good('maximum_138_byte_record',
                       pred(tuple(range(8)), [(2, 1, [i % 8]) for i in range(64)]),
                       bytes(i % 8 for i in range(64)))
        assert len(maximum) == 138
        escapes = bytes([10, 0, 20, 255, 30, 19, 10, 33] * 8)
        good('ESC_interleaved_literals', esc(escapes, palette), escapes)
        raw = good('RAW_all_U8', b'\x03\0' + bytes(range(64)), bytes(range(64)), palette)
        good('own_unused_entries', pack(bytes([10] * 64), palette), bytes([10] * 64))
        good('reuse_subset', bytes([4, 0, 0]) + bytes(16), bytes([10] * 64), palette)
        for name, record, previous in fixtures[:]:
            for extent in range(len(record)):
                bad(name + '_trunc_%d' % extent, record[:extent], previous)
            bad(name + '_trailing', record + b'\0', previous)
        for name, record, previous in (
                ('unknown_kind', b'\5\0', None), ('large_record', bytes(139), None),
                ('count_zero', b'\0\0', None), ('count_nine', b'\0\11' + bytes(range(9)), None),
                ('duplicate_palette', b'\0\2\1\1' + bytes(8), None),
                ('unsorted_palette', b'\0\2\2\1' + bytes(8), None),
                ('PACK_unused_index', own(0, palette, b'\xc0' + bytes(15)), None),
                ('PRED_unused_index', pred(palette, [(2, 64, [3] + [0] * 63)]), None),
                ('TOP_first_row', own(1, (10,), b'\x3f'), None),
                ('LEFT_first_column', own(1, (10,), b'\x7f'), None),
                ('LEFT_cross_row', pred(palette, [(2, 1, [0]), (1, 8, [])]), None),
                ('LEFT_next_row_start', pred(palette, [(2, 8, [0] * 8), (1, 1, [])]), None),
                ('PRED_overrun', pred(palette, [(2, 8, [0] * 8), (0, 57, [])]), None),
                ('PRED_reserved', own(1, (10,), b'\xff'), None),
                ('PRED_literal_padding', own(1, palette, b'\x80\x01\x3e'), None),
                ('PRED_singleton_trailing_literal', own(1, (10,), b'\xbf\0'), None),
                ('ESC_unused_index', own(2, (10, 20), b'\xc0' + bytes(15)), None),
                ('ESC_missing_literal', own(2, (10,), b'\x80'), None),
                ('ESC_terminal_escape_truncation', esc(bytes([0] + [10] * 63), (10,))[:-1] + b'\x01', None),
                ('RAW_reserved', b'\3\1' + bytes(64), None),
                ('REUSE_missing', b'\4\0\0', None),
                ('REUSE_unknown_ID', b'\4\0\1', (10,)),
                ('REUSE_unknown_subkind', b'\4\3\0', (10,)),
                ('previous_unsorted', pack(bytes([10] * 64), (10,)), (20, 10)),
                ('previous_empty', pack(bytes([10] * 64), (10,)), ()),
                ('previous_U8', pack(bytes([10] * 64), (10,)), (256,)),
                ('previous_bool', pack(bytes([10] * 64), (10,)), (True,)),
                ('previous_list', pack(bytes([10] * 64), (10,)), [10]),
                ('record_bytearray', bytearray(raw), None)):
            bad(name, record, previous)

        # Every partial-byte literal extent has its own independent zero padding.
        for count in (3, 5, 8):
            pal = tuple(range(count))
            for run in range(1, 8):
                record = pred(pal, [(2, run, [0] * run), (2, 64 - run, [0] * (64 - run))])
                good('independent_literal_extent_%d_%d' % (count, run), record, bytes(64))
                if run * (count - 1).bit_length() % 8:
                    broken = bytearray(record)
                    broken[3 + count + (run * (count - 1).bit_length() - 1) // 8] |= 1
                    bad('literal_extent_padding_%d_%d' % (count, run), bytes(broken))

        first = pack(bytes([10] * 64), (10,))
        reuse = b'\4\0\0'
        parsed = codec.parse_plane(plane([(2, first), (9, reuse)]), [2, 9])
        assert [v['pixels'] for v in parsed['palettes']] == [bytes([10] * 64)] * 2
        checks.append(dict(name='plane_history_same_plane', accepted=True))
        replaced = codec.parse_plane(plane([(2, first), (9, pack(bytes([20] * 64), (20,))),
                                           (11, reuse)]), [2, 9, 11])
        assert replaced['palettes'][-1]['pixels'] == bytes([20] * 64)
        checks.append(dict(name='plane_own_replaces_history', accepted=True))
        check('plane_empty_directory_fixed_12B', lambda: codec.parse_plane(plane([]), []),
              dict(palettes=[], residual_blocks=0, entropy=b''))
        residual = plane([(2, first)], 1, b'EC92opaque')
        check('plane_residual_partition', lambda: codec.parse_plane(residual, [2, 9])['residual_blocks'], 1)
        bad_planes = [
            ('history_plane_reset', plane([(2, reuse)]), [2]),
            ('history_frame_reset', plane([(2, reuse)]), [2]),
            ('RAW_clears_history', plane([(2, first), (9, raw), (11, reuse)]), [2, 9, 11]),
            ('own_replaces_history', plane([(2, first), (9, pack(bytes([20] * 64), (20,))),
                                           (11, bytes([4, 0, 0, 0]))]), [2, 9, 11]),
            ('directory_descending', plane([(9, first), (2, first)]), [2, 9]),
            ('directory_duplicate', plane([(2, first), (2, first)]), [2]),
            ('directory_nonactive', plane([(3, first)]), [2]),
            ('residual_missing', plane([], 1), [2]),
            ('residual_unexpected', plane([], 0, b'EC92'), []),
            ('residual_wrong_format', plane([], 1, b'EC94'), [2]),
            ('residual_partition', residual, [2, 9, 11]),
            ('active_duplicate', plane([]), [2, 2]),
            ('active_descending', plane([]), [9, 2]),
            ('active_bool', plane([]), [True]),
            ('directory_count', struct.pack('>I', 2**32 - 1) + bytes(8), None),
            ('directory_length_small', struct.pack('>IHH', 1, 2, 1) + b'\0' + bytes(8), [2]),
            ('directory_length_large', struct.pack('>IHH', 1, 2, 139) + bytes(147), [2]),
        ]
        full_plane = plane([(2, first), (9, reuse)])
        bad_planes += [('truncation_%d' % n, full_plane[:n], [2, 9]) for n in range(len(full_plane))]
        bad_planes += [('trailing', full_plane + b'\0', [2, 9])]
        for name, data, positions in bad_planes:
            check('reject_plane_' + name, lambda d=data, p=positions: codec.parse_plane(d, p), accepted=False)

        # Deterministic stress patterns; no claim that these are captured footage.
        rng = random.Random(95)
        patterns = [
            ('synthetic_UI_HUD_borders', bytes(220 if x in (0, 7) or y in (0, 7) else 20 for y in range(8) for x in range(8))),
            ('synthetic_UI_HUD_glyph', bytes(255 if (x + y) % 3 == 0 else 0 for y in range(8) for x in range(8))),
            *[('synthetic_moving_bar_%d' % frame, bytes(180 if x == frame else 20 for y in range(8) for x in range(8))) for frame in range(8)],
            ('synthetic_noise', bytes(rng.randrange(256) for _ in range(64))),
            ('synthetic_scene_change_black', bytes(64)),
            ('synthetic_scene_change_white', bytes([255] * 64)),
        ]
        for name, pixels in patterns:
            pal = tuple(sorted(set(pixels)))[:8]
            record = pack(pixels, pal) if len(set(pixels)) <= 8 else esc(pixels, pal)
            good(name, record, pixels)
            synthetic.append(dict(name=name, pixel_sha256=hashlib.sha256(pixels).hexdigest(),
                                  record_bytes=len(record), coverage='synthetic grammar only'))

        native_count, native_malformed = 0, 0
        if args.fixtures is not None:
            manifest_path = pin(args.fixtures)
            manifest = json.loads(manifest_path.read_text())
            for fixture in manifest.get('fixtures', manifest.get('valid', [])):
                previous = fixture.get('previous_palette')
                previous = tuple(previous) if previous else None
                if 'record_hex' in fixture:
                    record = bytes.fromhex(fixture['record_hex'])
                else:
                    path = pin(manifest_path.parent / fixture['path'])
                    record = path.read_bytes()
                pixels, _ = codec.decode(record, previous)
                assert hashlib.sha256(pixels).hexdigest() == fixture['pixel_sha256'], fixture['name']
                checks.append(dict(name='native_' + fixture['name'], accepted=True))
                native_count += 1
                for extent in range(len(record)):
                    bad('native_' + fixture['name'] + '_trunc_%d' % extent, record[:extent], previous)
                bad('native_' + fixture['name'] + '_trailing', record + b'\0', previous)
            for fixture in manifest.get('malformed', []):
                previous = fixture.get('previous_palette')
                previous = tuple(previous) if previous else None
                bad('native_' + fixture['name'], bytes.fromhex(fixture['record_hex']), previous)
                native_malformed += 1

        assert pins == {name: sha(ROOT / name) for name in pins}, 'pinned inputs changed'
        report.update(status='PASS_INDEPENDENT_V95_STRICT_PIXEL_GRAMMAR', checks_count=len(checks),
                      native_fixtures=native_count, native_malformed=native_malformed,
                      scope='Exact U8 pixel records and plane directories; EC92 residual opaque; synthetic patterns are not raw-capture coverage; predecoded V82 target generation cost unmeasured.')
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
