#!/usr/bin/env python3
"""Bounded CS95 rejection, retained state, recovery and directed pixel tests.

Research receivers are explicit for oversized policy/directed frames. Primary
work15 mutations use the strict 49152-byte receiver. These are host protocol
tests, not original-coefficient parity or physical throughput measurements.
"""
import argparse
import copy
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import struct
import subprocess
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95/wire'
CONTAINER = 'gamebub-cu66-v69-build'
CAP = 49152
POLICIES = ('control', 'byte_min', 'P8', 'E8', 'work15')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def crc(packet):
    return bytes(packet[:-4]) + struct.pack('>I', zlib.crc32(packet[:-4]))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def layout(packet):
    start = 128 + int.from_bytes(packet[36:40], 'big') + int.from_bytes(packet[40:44], 'big')
    cursor, planes = start, []
    for axis in range(3):
        begin = cursor
        count, = struct.unpack_from('>I', packet, cursor)
        cursor += 4
        entries = []
        for _ in range(count):
            directory = cursor
            position, length = struct.unpack_from('>HH', packet, cursor)
            cursor += 4
            record = packet[cursor:cursor + length]
            assert len(record) == length and 2 <= length <= 138
            entries.append(dict(position=position, record=record, directory=directory))
            cursor += length
        residual_directory = cursor
        blocks, length = struct.unpack_from('>II', packet, cursor)
        cursor += 8
        entropy = packet[cursor:cursor + length]
        assert len(entropy) == length
        cursor += length
        planes.append(dict(start=begin, end=cursor, entries=entries, residual_blocks=blocks,
                           entropy=entropy, residual_directory=residual_directory))
    assert cursor - start == int.from_bytes(packet[48:52], 'big')
    return start, cursor, planes


def plane_bytes(plane):
    return (struct.pack('>I', len(plane['entries'])) +
            b''.join(struct.pack('>HH', item['position'], len(item['record'])) + item['record']
                     for item in plane['entries']) +
            struct.pack('>II', plane['residual_blocks'], len(plane['entropy'])) + plane['entropy'])


def compose(packet, planes):
    start, end, _ = layout(packet)
    body = b''.join(plane_bytes(plane) for plane in planes)
    result = bytearray(packet[:start] + body + packet[end:])
    struct.pack_into('>I', result, 48, len(body))
    return crc(result)


def all_escape(pixels, palette, reuse=False):
    """Independent literal builder: every sample uses ESC even if in palette."""
    width = len(palette).bit_length()
    bits = ''.join(format(len(palette), '0%db' % width) + format(pixel, '08b') for pixel in pixels)
    body = bytes(sum(int(bit) << (7 - j) for j, bit in enumerate(bits[i:i + 8]))
                 for i in range(0, len(bits), 8))
    return (bytes([4, 2, 0]) if reuse else bytes([2, len(palette), *palette])) + body


def run_tests(out, report, processes, campaign_path):
    campaign_path = campaign_path.resolve()
    def checkpoint():
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')

    def pin(path, copy_source=True):
        path = path.resolve()
        name = str(path.relative_to(ROOT))
        value = sha(path)
        assert name not in report['source_sha256'] or report['source_sha256'][name] == value
        report['source_sha256'][name] = value
        if copy_source:
            target = out / 'sources' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        checkpoint()

    selected = json.loads(campaign_path.read_text())
    assert selected['status'] == 'PASS_NATIVE_CS95_FULL_PIXEL_ROOT_HUD_PARITY', 'qualified wire campaign required'
    full_path = ROOT / selected['selected_report'] if 'selected_report' in selected else campaign_path
    full = json.loads(full_path.read_text())
    run = full_path.parent
    for path in (Path(__file__), campaign_path, full_path, run / 'frames.jsonl', AREA / 'receiver.cpp',
                 ROOT / 'experiments/python-gamebub-v95/python/codec.py',
                 ROOT / 'experiments/python-gamebub-v95/native/codec.hpp',
                 ROOT / 'experiments/python-gamebub-v92/native/codec.hpp'):
        pin(path)
    report['executed_binary_sha256'] = {}
    for key, filename in (('strict_binary', 'receiver-strict.bin'), ('research_binary', 'receiver-research.bin')):
        path = run / filename
        pin(path, copy_source=False)
        observed = subprocess.run(['docker', 'exec', CONTAINER, 'sha256sum', full[key]],
                                  capture_output=True, timeout=15, check=True)
        value = observed.stdout.decode().split()[0]
        assert value == sha(path), ('executed binary differs from qualified binary', full[key])
        report['executed_binary_sha256'][full[key]] = value
    reader = load('v95_wire_independent_record_reader', ROOT / 'experiments/python-gamebub-v95/python/codec.py')
    rows = [json.loads(line) for line in (run / 'frames.jsonl').read_text().splitlines()]
    qualified = {(row['policy'], row['fid']): row for row in rows
                 if row['cohort'] == 0 and row['policy'] in POLICIES and row['fid'] in (0, 1, 2, 3)}
    golden = {key: row['decoded'] for key, row in qualified.items()}
    assert all((policy, fid) in golden for policy in POLICIES for fid in (0, 1, 2))
    (out / 'qualified-goldens.json').write_text(json.dumps(
        {f'{policy}-f{fid}': value for (policy, fid), value in golden.items()}, indent=2) + '\n')
    packets = {}
    for policy in POLICIES:
        for fid in (0, 1, 2):
            path = run / f'c0-f{fid}-{policy}.cs95'
            if path.exists():
                pin(path)
                packets[policy, fid] = path.read_bytes()
        if any((policy, fid) not in packets for fid in (0, 1, 2)) or policy == 'byte_min':
            archive_path = run / f'packets-{policy}.bin.gz'
            pin(archive_path, copy_source=False)
            with gzip.open(archive_path, 'rb') as archive:
                while True:
                    head = archive.read(8)
                    if not head:
                        break
                    assert len(head) == 8
                    meta_length, packet_length = struct.unpack('<II', head)
                    assert 0 < meta_length <= 131072 and 132 <= packet_length <= 2097152
                    raw_meta, packet = archive.read(meta_length), archive.read(packet_length)
                    assert len(raw_meta) == meta_length and len(packet) == packet_length
                    meta = json.loads(raw_meta)
                    if meta['cohort'] == 0 and meta['fid'] in (0, 1, 2, 3):
                        assert meta == qualified[policy, meta['fid']]
                        packets[policy, meta['fid']] = packet
    for (policy, fid), packet in packets.items():
        assert len(packet) == golden[policy, fid]['wire_bytes']
        assert digest(packet) == qualified[policy, fid]['packet_sha256']
        (out / 'inputs' / f'valid-c0-f{fid}-{policy}.cs95').write_bytes(packet)

    # Frozen target bytes supply directed RAW/ESC fixtures, outside measured
    # encoder work. Pin the exact compressed source shard as byte provenance.
    target_area = ROOT / 'experiments/python-gamebub-v82/native'
    for path in (target_area / 'data.py', target_area / 'index.json'):
        pin(path)
    target_index = json.loads((target_area / 'index.json').read_text())
    pin(target_area / target_index['chunks'][0]['path'], copy_source=False)
    target_loader = load('v95_wire_frozen_v82', target_area / 'data.py')
    target_iter = target_loader.iter_frames()
    targets = [next(target_iter) for _ in range(3)]
    for fid, target in enumerate(targets):
        assert (target['cohort'], target['fid']) == (0, fid)
        assert target['canonical_sha256'] == golden['control', fid]['canonical_sha256']

    key, delta, third = (packets['work15', fid] for fid in (0, 1, 2))
    assert all(len(packet) <= CAP for packet in (key, delta, third))
    _, _, source_planes = layout(delta)
    axis = next(axis for axis, plane in enumerate(source_planes) if len(plane['entries']) >= 2)
    entry = source_planes[axis]['entries'][0]
    cases = []

    def add(name, packet, error=None, policy='work15'):
        assert len(packet) <= CAP, (name, len(packet))
        (out / 'inputs' / (name + '.cs95')).write_bytes(packet)
        cases.append(dict(name=name, packet=packet, policy=policy, expected_error=error))
        checkpoint()

    def records(name, changes, error=None, plane_axis=axis):
        planes = copy.deepcopy(source_planes)
        for index, record in changes.items():
            planes[plane_axis]['entries'][index]['record'] = record
        add(name, compose(delta, planes), error)

    def field(name, offset, value, error=None):
        packet = bytearray(delta)
        packet[offset:offset + len(value)] = value
        add(name, crc(packet), error)

    malformed = (
        ('palette_kind', b'\5\0'), ('palette_count_zero', b'\0\0'),
        ('palette_count_nine', b'\0\11'), ('palette_sorted', b'\0\2\2\1'),
        ('palette_duplicate', b'\0\2\1\1'),
        ('PACK_unused_index', bytes([0, 3, 0, 1, 2]) + bytes([255] * 16)),
        ('PACK_truncated', bytes([0, 2, 0, 1])),
        ('PRED_TOP_origin', bytes([1, 1, 0, 63])),
        ('PRED_LEFT_origin', bytes([1, 1, 0, 127])),
        ('PRED_LEFT_row_overrun', bytes([1, 1, 0, 128, 71])),
        ('PRED_reserved', bytes([1, 1, 0, 255])),
        ('PRED_literal_padding', bytes([1, 2, 0, 255, 128, 1, 62])),
        ('PRED_output_overrun', bytes([1, 1, 0, 135, 63])),
        ('PRED_trailing', bytes([1, 1, 0, 191, 0])),
        ('ESC_unused_index', bytes([2, 2, 0, 1]) + bytes([255] * 16)),
        ('ESC_literal_truncation', bytes([2, 1, 0, 128])),
        ('RAW_reserved', bytes([3, 1]) + bytes(64)), ('RAW_truncation', b'\3\0'),
        ('REUSE_missing_plane_history', bytes([4, 0, 0])),
        ('REUSE_unsupported_ID', bytes([4, 0, 1])),
        ('REUSE_unsupported_subkind', bytes([4, 3, 0])),
    )
    for name, record in malformed:
        records(name, {0: record})
    target_pixels = targets[1]['planes'][axis][entry['position']]
    records('RAW_clears_palette_history', {0: b'\3\0' + target_pixels, 1: b'\4\0\0'}, 'palette count')
    for name, length in (('record_length_below_minimum', 1), ('record_length_above_maximum', 139)):
        field(name, entry['directory'] + 2, struct.pack('>H', length), 'CS95 palette record length')
    field('directory_count_overrun', source_planes[axis]['start'], struct.pack('>I', 65536), 'CS95 palette count')
    second = source_planes[axis]['entries'][1]
    field('directory_position_duplicate', second['directory'], struct.pack('>H', entry['position']),
          'CS95 palette position/order/mode')
    field('directory_position_descending', second['directory'], struct.pack('>H', max(0, entry['position'] - 1)),
          'CS95 palette position/order/mode')
    field('directory_position_bounds', entry['directory'], struct.pack('>H', 1350 if axis else 5400),
          'CS95 palette position/order/mode')
    global_offset = (0, 5400, 6750)[axis]
    for name, mask in (('hidden', targets[1]['hidden_mask']), ('COPY', targets[1]['copy_ref_mask'])):
        position = next(pos for pos in range(1350 if axis else 5400) if mask[global_offset + pos])
        field('directory_position_' + name, entry['directory'], struct.pack('>H', position),
              'CS95 palette position/order/mode')
    for plane_axis in range(3):
        plane = source_planes[plane_axis]
        field('residual_complement_count_p%d' % plane_axis, plane['residual_directory'],
              struct.pack('>I', plane['residual_blocks'] + 1), 'CS95 residual complement count')
        field('residual_length_zero_p%d' % plane_axis, plane['residual_directory'] + 4,
              bytes(4), 'CS95 fallback length')
        assert plane['entropy'][:4] == b'EC92'
        at = plane['end'] - 1
        field('EC92_CRC_p%d' % plane_axis, at, bytes([delta[at] ^ 1]))
    field('CS95_data_length', 48, struct.pack('>I', int.from_bytes(delta[48:52], 'big') + 1))
    outer = bytearray(delta)
    outer[-1] ^= 1
    add('CS95_outer_CRC', bytes(outer), 'CS95 outer CRC')
    for name, magic in (('old_CS94_profile', b'CS94'), ('unknown_CS96_profile', b'CS96')):
        field(name, 0, magic, 'CS95 explicit profile/version')

    # A grammatically valid changed final palette sample must reach C2 content
    # validation, then reject without publishing any provisional frame state.
    last_axis = max(a for a, plane in enumerate(source_planes) if plane['entries'])
    last_index = len(source_planes[last_axis]['entries']) - 1
    last_position = source_planes[last_axis]['entries'][last_index]['position']
    changed_pixels = bytearray(targets[1]['planes'][last_axis][last_position])
    changed_pixels[-1] ^= 1
    reader.decode(b'\3\0' + bytes(changed_pixels))
    records('valid_palette_pixel_change_late_root', {last_index: b'\3\0' + bytes(changed_pixels)},
            'CS95 reconstructed content root', last_axis)

    def start_receiver(binary, name):
        index = len(processes)
        pidfile = f'/tmp/cu66-v95-recovery-{out.name}-{index}.pid'
        log = (out / f'native-{index}-{name}.stderr').open('wb')
        process = subprocess.Popen(['docker', 'exec', '-i', CONTAINER, 'sh', '-c',
            'printf "%s\\n" "$$" > "$1"; exec timeout -s TERM -k 2 120 "$2"',
            'sh', pidfile, binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        record = dict(process=process, pidfile=pidfile, log=log, finished=False)
        processes.append(record)
        return record

    def receive(record, packet):
        process = record['process']
        process.stdin.write(struct.pack('>II', 0, len(packet)) + packet)
        process.stdin.flush()
        line = process.stdout.readline()
        assert line, 'native receiver closed without response'
        return json.loads(line)

    def finish(record):
        process = record['process']
        process.stdin.close()
        assert process.wait(timeout=15) == 0
        record['finished'] = True

    for case in cases:
        name, packet, policy = case['name'], case['packet'], case['policy']
        report['active_case'] = name
        checkpoint()
        record = start_receiver(full['strict_binary'], name)
        accepted = receive(record, key)
        rejected = receive(record, packet)
        assert accepted == golden['work15', 0], (name, accepted)
        assert not rejected['accepted'] and rejected['retained_fid'] == 0, (name, rejected)
        if case['expected_error']:
            assert rejected['error'] == case['expected_error'], (name, rejected)
        recovered = receive(record, packets[policy, 1])
        replayed = receive(record, packets[policy, 1])
        next_frame = receive(record, third)
        assert recovered == golden[policy, 1], (name, recovered)
        assert replayed == dict(golden[policy, 1], replayed=True), (name, replayed)
        assert next_frame == golden['work15', 2], (name, next_frame)
        finish(record)
        report['checks'].append(dict(name=name, status='PASS_REJECT_RETAIN_RECOVER_REPLAY_NEXT',
                                     strict_receiver=True, packet_sha256=digest(packet),
                                     rejected=rejected, recovered=recovered, next_frame=next_frame))
        checkpoint()

    # First REUSE in a new frame must fail even when the previous accepted
    # frame ended with a palette. Every frame/plane owns a fresh local cache.
    _, _, next_planes = layout(third)
    next_axis = next(a for a, plane in enumerate(next_planes) if plane['entries'])
    next_planes[next_axis]['entries'][0]['record'] = b'\4\0\0'
    invalid_next = compose(third, next_planes)
    (out / 'inputs' / 'REUSE_missing_new_frame_history.cs95').write_bytes(invalid_next)
    report['active_case'] = 'REUSE_missing_new_frame_history'
    checkpoint()
    record = start_receiver(full['strict_binary'], 'frame-cache-reset')
    assert receive(record, key) == golden['work15', 0]
    assert receive(record, delta) == golden['work15', 1]
    rejected = receive(record, invalid_next)
    assert not rejected['accepted'] and rejected['retained_fid'] == 1
    assert rejected['error'] == 'palette count', ('new-frame REUSE must lack history', rejected)
    assert receive(record, third) == golden['work15', 2]
    assert receive(record, third) == dict(golden['work15', 2], replayed=True)
    assert receive(record, packets['byte_min', 3]) == golden['byte_min', 3]
    finish(record)
    report['checks'].append(dict(name='REUSE_missing_new_frame_history', status='PASS_REJECT_RETAIN_RECOVER_REPLAY_NEXT',
                                 strict_receiver=True, rejected=rejected, packet_sha256=digest(invalid_next)))

    # Uniform P8 contains palette records on consecutive planes. It is an
    # explicit research fixture because this complete packet exceeds the cap.
    plane_source = packets['P8', 1]
    _, _, cross_planes = layout(plane_source)
    cross_axis = next(a for a in range(1, 3) if cross_planes[a - 1]['entries'] and cross_planes[a]['entries'])
    assert reader.parse_plane(plane_bytes(cross_planes[cross_axis - 1]))['palettes'][-1]['palette_after'] is not None
    cross_planes[cross_axis]['entries'][0]['record'] = b'\4\0\0'
    invalid_plane = compose(plane_source, cross_planes)
    (out / 'inputs' / 'REUSE_missing_new_plane_history.cs95').write_bytes(invalid_plane)
    report['active_case'] = 'REUSE_missing_new_plane_history'
    checkpoint()
    record = start_receiver(full['research_binary'], 'plane-cache-reset')
    assert receive(record, key) == golden['work15', 0]
    rejected = receive(record, invalid_plane)
    assert rejected == dict(accepted=False, error='palette count', retained_fid=0), rejected
    assert receive(record, plane_source) == golden['P8', 1]
    assert receive(record, plane_source) == dict(golden['P8', 1], replayed=True)
    assert receive(record, packets['E8', 2]) == golden['E8', 2]
    finish(record)
    report['checks'].append(dict(name='REUSE_missing_new_plane_history', status='PASS_REJECT_RETAIN_RECOVER_REPLAY_NEXT',
                                 strict_receiver=False, research_reason='uniform P8 complete frame exceeds strict cap',
                                 rejected=rejected, packet_sha256=digest(invalid_plane)))

    # Positive cross-policy sequences compare the entire qualified result,
    # including residual/palette digest arrays, C2, pixels, HUD and byte count.
    for sequence in ((('control', 0), ('work15', 1), ('byte_min', 2)),
                     (('byte_min', 0), ('control', 1), ('work15', 2)),
                     (('control', 0), ('P8', 1), ('E8', 2)),
                     (('control', 0), ('E8', 1), ('P8', 2))):
        research = any(len(packets[item]) > CAP for item in sequence)
        name = 'cross_profile_' + '_'.join(policy for policy, fid in sequence)
        report['active_case'] = name
        checkpoint()
        binary = full['research_binary'] if research else full['strict_binary']
        record = start_receiver(binary, name)
        for item in sequence:
            assert receive(record, packets[item]) == golden[item], (name, item)
            assert receive(record, packets[item]) == dict(golden[item], replayed=True), (name, item)
        finish(record)
        report['checks'].append(dict(name=name, status='PASS_FULL_QUALIFIED_GOLDENS_AND_REPLAY',
                                     strict_receiver=not research, research_reason='uniform P8/E8 exceeds 49152 bytes' if research else None))

    # Valid all-escape forms preserve every palette pixel and history value.
    parsed = reader.parse_plane(plane_bytes(source_planes[axis]))
    for reuse in (False, True):
        index = (next(i for i, item in enumerate(parsed['palettes']) if item['record'][0] == 4)
                 if reuse else next(i for i, item in enumerate(parsed['palettes']) if item['record'][0] in (0, 1, 2)))
        item = parsed['palettes'][index]
        palette = item['palette_before'] if reuse else item['palette_after']
        replacement = all_escape(item['pixels'], palette, reuse)
        assert reader.decode(replacement, item['palette_before']) == (item['pixels'], item['palette_after'])
        planes = copy.deepcopy(source_planes)
        planes[axis]['entries'][index]['record'] = replacement
        packet = compose(delta, planes)
        assert len(packet) <= CAP
        name = 'positive_all_escape_' + ('REUSE' if reuse else 'own_palette')
        (out / 'inputs' / (name + '.cs95')).write_bytes(packet)
        expected = dict(golden['work15', 1], wire_bytes=len(packet))
        report['active_case'] = name
        checkpoint()
        record = start_receiver(full['strict_binary'], name)
        assert receive(record, key) == golden['work15', 0]
        actual = receive(record, packet)
        assert actual == expected, (name, actual, expected)
        assert receive(record, packet) == dict(expected, replayed=True)
        assert receive(record, third) == golden['work15', 2]
        finish(record)
        report['checks'].append(dict(name=name, status='PASS_EXACT_PIXELS_ROOT_HUD_SEAL_REPLAY_NEXT',
                                     strict_receiver=True, decoded=actual, packet_sha256=digest(packet)))

    # Full key from RAW U8 records, zero coefficient fallback on all three
    # planes. This deliberately exceeds the cap and proves only semantics.
    raw_planes, raw_hashes, offset = [], [], 0
    for a, total in enumerate((5400, 1350, 1350)):
        entries = [dict(position=pos, record=b'\3\0' + targets[0]['planes'][a][pos])
                   for pos in range(total) if not targets[0]['hidden_mask'][offset + pos]]
        raw_planes.append(dict(entries=entries, residual_blocks=0, entropy=b''))
        raw_hashes.append(digest(b''.join(item['record'][2:] for item in entries)))
        offset += total
    raw_packet = compose(key, raw_planes)
    assert len(raw_packet) > CAP and sum(len(plane['entries']) for plane in raw_planes) == 7806
    (out / 'inputs' / 'directed_all_RAW_zero_fallback_key.cs95').write_bytes(raw_packet)
    expected = dict(golden['work15', 0], wire_bytes=len(raw_packet), palette_tiles=7806,
                    residual_tiles=0, residual_plane_sha256=[digest(b'')] * 3,
                    palette_plane_sha256=raw_hashes)
    report['active_case'] = 'directed_all_RAW_zero_fallback_key'
    checkpoint()
    record = start_receiver(full['research_binary'], 'all-RAW-key')
    actual = receive(record, raw_packet)
    assert actual == expected, (actual, expected)
    assert receive(record, raw_packet) == dict(expected, replayed=True)
    assert receive(record, delta) == golden['work15', 1]
    assert receive(record, third) == golden['work15', 2]
    finish(record)
    report['checks'].append(dict(name='directed_all_RAW_zero_fallback_key',
                                 status='PASS_EXACT_CANONICAL_HUD_DISPLAY_ROOT_SEAL_FID_GENERATION',
                                 strict_receiver=False, research_reason='directed all-RAW key exceeds strict transport cap; semantic test only',
                                 cap_fit_claim=False, decoded=actual, packet_sha256=digest(raw_packet)))

    # Strict binary rejects cap+1 before allocation and emits no frame result.
    oversized = crc(delta + bytes(CAP + 1 - len(delta)))
    (out / 'inputs' / 'complete_frame_49153_reject.cs95').write_bytes(oversized)
    report['active_case'] = 'complete_frame_49153_reject'
    checkpoint()
    record = start_receiver(full['strict_binary'], 'oversized')
    process = record['process']
    output, _ = process.communicate(struct.pack('>II', 0, len(oversized)) + oversized, timeout=30)
    record['finished'] = True
    record['log'].flush()
    error = (out / f'native-{processes.index(record)}-oversized.stderr').read_bytes()
    assert process.returncode != 0 and not output and b'transport framing' in error
    report['checks'].append(dict(name='complete_frame_49153_reject', status='PASS_FAIL_CLOSED_TRANSPORT_CAP',
                                 strict_receiver=True, observed_exit_code=process.returncode,
                                 error=error.decode(), packet_sha256=digest(oversized)))
    assert report['source_sha256'] == {name: sha(ROOT / name) for name in report['source_sha256']}, 'executed input changed'
    report.update(status='PASS_CS95_PROTOCOL_RECOVERY_AND_DIRECTED_PIXELS', checks_count=len(report['checks']),
                  strict_binary=full['strict_binary'], research_binary=full['research_binary'],
                  research_binary_used=True, qualified_wire_report=str(full_path.relative_to(ROOT)))
    report.pop('active_case', None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', type=Path, default=AREA / 'results.json')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error('--timeout must be positive')
    out = AREA / 'test-attempts' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    (out / 'inputs').mkdir(parents=True)
    report = dict(schema='cu66-v95-wire-recovery-v1', status='FAIL', checks=[],
                  watchdog_seconds=args.timeout, source_sha256={}, physical_timing_proven=False,
                  original_coefficient_parity_claimed=False, predecoded_pixel_generation_cost_measured=False,
                  scope='Strict 49152-byte host admission/commit and explicit research-size directed semantics. Exact qualified full-result recovery comparisons. No original coefficient parity, physical throughput, or target generation timing claim.')
    (out / 'source-test_wire.py').write_bytes(Path(__file__).read_bytes())
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    processes, started = [], time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    def watchdog(signum, frame):
        raise TimeoutError('CS95 recovery test watchdog expired')
    signal.signal(signal.SIGALRM, watchdog)
    signal.alarm(args.timeout)
    try:
        run_tests(out, report, processes, args.campaign)
    except BaseException as error:
        report.update(status='FAIL', failure=repr(error))
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prior)
        for record in processes:
            process = record['process']
            try:
                cleanup = ('rm -f "$1"' if record['finished'] else
                    'if test -r "$1"; then read -r p < "$1"; kill -TERM "$p" 2>/dev/null || :; rm -f "$1"; fi')
                result = subprocess.run(['docker', 'exec', CONTAINER, 'sh', '-c', cleanup, 'sh', record['pidfile']],
                                        capture_output=True, timeout=10)
                if result.returncode:
                    report.setdefault('cleanup_errors', []).append(result.stderr.decode(errors='replace'))
                if process.stdin is not None and not process.stdin.closed:
                    try:
                        process.stdin.close()
                    except (BrokenPipeError, OSError):
                        pass
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if process.stdout is not None and not process.stdout.closed:
                    process.stdout.close()
                if not record['log'].closed:
                    record['log'].close()
            except BaseException as error:
                report.setdefault('cleanup_errors', []).append(repr(error))
        if report.get('cleanup_errors') and report['status'].startswith('PASS'):
            report.update(status='FAIL', failure='native child cleanup failed')
        report['wall_seconds'] = time.monotonic() - started
        report['artifact_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*')
                                     if path.is_file() and path != out / 'results.json'}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (AREA / 'tests.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print(report['status'], out / 'results.json', flush=True)
    assert report['status'] == 'PASS_CS95_PROTOCOL_RECOVERY_AND_DIRECTED_PIXELS', report.get('failure')


if __name__ == '__main__':
    main()
