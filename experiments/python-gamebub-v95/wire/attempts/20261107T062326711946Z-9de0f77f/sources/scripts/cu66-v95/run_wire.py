#!/usr/bin/env python3
"""Compose actual CS95 planes into complete packets and audit native decode."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import signal
import statistics
import struct
import subprocess
import sys
import time
import uuid
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v95/wire'
NATIVE = ROOT / 'experiments/python-gamebub-v95/native'
CONTAINER = 'gamebub-cu66-v69-build'
PROFILE_NAMES = ('control', 'P2', 'P4', 'P8', 'E8', 'W8')
PROFILE_INDICES = (0, 1, 2, 3, 4, 5)
POLICIES = ('control', 'P2', 'P4', 'P8', 'E8', 'W8',
            'byte_min', 'work5', 'work15')
STRICT_POLICIES = frozenset(('control', 'byte_min', 'work5', 'work15'))
FIXTURE_POLICIES = ('control', 'byte_min', 'P8', 'E8', 'work15')
STRICT_CAP = 49152
RESEARCH_CAP = 2 * 1024 * 1024
C2_CONTROL = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    return dict(min=min(values), median=statistics.median(values),
                max=max(values), total=sum(values))


def source_files(wire_path, old88_path, qcodec_path, oldmap_path, groupmap_path,
                 v92_report_path, v92_frames_path, native_index):
    paths = [Path(__file__).resolve(), AREA / 'receiver.cpp', NATIVE / 'data.py',
             native_index, NATIVE / 'codec.hpp',
             ROOT / 'experiments/python-gamebub-v95/python/codec.py',
             NATIVE / 'collect.cpp', NATIVE / 'test_codec.cpp',
             ROOT / 'experiments/python-gamebub-v82/native/data.py',
             ROOT / 'experiments/python-gamebub-v82/native/index.json', C2_CONTROL,
             wire_path, old88_path, qcodec_path, oldmap_path, groupmap_path,
             v92_report_path, v92_frames_path,
             ROOT / 'experiments/python-gamebub-v92/wire/receiver.cpp',
             ROOT / 'experiments/python-gamebub-v92/native/data.py',
             ROOT / 'experiments/python-gamebub-v92/native/index.json',
             ROOT / 'experiments/python-gamebub-v92/native/codec.hpp',
             ROOT / 'experiments/python-gamebub-v88/entropy/codec.hpp',
             ROOT / 'experiments/python-gamebub-v85/residual/encode.hpp']
    paths += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    paths += sorted((ROOT / 'experiments/python-gamebub-v82/native/data').glob('*.gz'))
    paths += sorted((ROOT / 'experiments/python-gamebub-v92/native/data').glob('*.gz'))
    paths += sorted((NATIVE / 'data').glob('*.gz'))
    # Preserve first occurrence while making missing inputs a clear preflight failure.
    unique = list(dict.fromkeys(paths))
    missing = [str(path) for path in unique if not path.is_file()]
    if missing:
        raise FileNotFoundError('V95 wire inputs are not ready: ' + ', '.join(missing))
    return unique


def cs95_packet(old_packet, planes):
    """Replace only CS88's residual body with three complete CS95 plane bodies."""
    if old_packet[:4] != b'CS88' or len(planes) != 3:
        raise ValueError('expected a complete CS88 metadata packet and three planes')
    header = bytearray(old_packet[:128])
    map_bytes = int.from_bytes(header[36:40], 'big')
    q_bytes = int.from_bytes(header[40:44], 'big')
    hud_bytes = int.from_bytes(header[44:48], 'big')
    old_data_bytes = int.from_bytes(header[48:52], 'big')
    data_start = 128 + map_bytes + q_bytes
    if data_start + old_data_bytes + hud_bytes + 4 != len(old_packet):
        raise ValueError('CS88 metadata/body extents do not match packet length')
    plane_body = b''.join(planes)
    header[:4] = b'CS95'
    struct.pack_into('>I', header, 48, len(plane_body))
    content = (bytes(header) + old_packet[128:data_start] + plane_body +
               old_packet[data_start + old_data_bytes:-4])
    return content + struct.pack('>I', zlib.crc32(content))


def plane_bytes(frame, axis, profile):
    value = frame['plane_variants'][axis][profile]
    if type(value) is not bytes:
        raise TypeError(('V95 plane variant must be bytes', axis, profile, type(value)))
    return value


def plane_stats(frame, axis, profile):
    return frame['palette_stats'][axis][profile]


def complete_bytes(frame, profile_tuple, common_bytes):
    return common_bytes + sum(len(plane_bytes(frame, axis, profile_tuple[axis]))
                              for axis in range(3))


def select_policies(frame, common_bytes, baseline_bytes):
    profiles = list(itertools.product(PROFILE_INDICES, repeat=3))
    assert len(profiles) == 216
    sizes = {choice: complete_bytes(frame, choice, common_bytes) for choice in profiles}
    avoided = {choice: sum(int(plane_stats(frame, axis, choice[axis])['avoided_tiles'])
                           for axis in range(3)) for choice in profiles}
    selected = {
        'control': (0, 0, 0),
        'P2': (1, 1, 1),
        'P4': (2, 2, 2),
        'P8': (3, 3, 3),
        'E8': (4, 4, 4),
        'W8': (5, 5, 5),
        'byte_min': min(profiles, key=lambda p: (sizes[p], -avoided[p], p)),
    }
    for policy, percent in (('work5', 105), ('work15', 115)):
        budget = min(STRICT_CAP, baseline_bytes * percent // 100)
        feasible = [p for p in profiles if sizes[p] <= budget]
        if not feasible:
            raise ValueError((policy, 'no combination meets complete-byte budget', budget))
        selected[policy] = min(feasible, key=lambda p: (-avoided[p], sizes[p], p))
    return selected, sizes, avoided


def assert_decoded_matches(decoded, frame, choice):
    residual_hashes = decoded['residual_plane_sha256']
    palette_hashes = decoded['palette_plane_sha256']
    if len(residual_hashes) != 3 or len(palette_hashes) != 3:
        raise AssertionError('CS95 receiver must return three plane hashes')
    palette_tiles = residual_tiles = 0
    for axis, profile in enumerate(choice):
        expected = plane_stats(frame, axis, profile)
        assert residual_hashes[axis] == expected['residual_coeff_sha256'], (
            'residual coefficient plane hash', axis, profile)
        assert palette_hashes[axis] == expected['palette_pixel_sha256'], (
            'palette pixel plane hash', axis, profile)
        palette_tiles += int(expected['avoided_tiles'])
        residual_tiles += int(expected['residual_blocks'])
    for key, expected in (('palette_tiles', palette_tiles),
                          ('residual_tiles', residual_tiles)):
        actual = decoded[key]
        if isinstance(actual, list):
            actual = sum(map(int, actual))
        assert int(actual) == expected, ('CS95 receiver tile/block count', key, actual, expected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-index', type=Path, default=NATIVE / 'index.json')
    args = parser.parse_args()
    args.native_index = args.native_index.resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / (stamp + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True)

    data = load('v95_data', NATIVE / 'data.py')
    wire_path = ROOT / 'scripts/cu66-v86/run_wire.py'
    old88_path = ROOT / 'scripts/cu66-v88/run_wire.py'
    qcodec_path = ROOT / 'scripts/cu66-v87/quantizer_codec.py'
    oldmap_path = ROOT / 'scripts/cu66-v84/prototype_mode_map_v2.py'
    groupmap_path = ROOT / 'scripts/cu66-v86/prototype_maps.py'
    wire = load('v95_frame', wire_path)
    old88 = load('v95_qframe', old88_path)
    qcodec = load('v95_qmap', qcodec_path)
    native = load('v95_original', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    oldmap = load('v95_oldmap', oldmap_path)
    groupmap = load('v95_groupmap', groupmap_path)

    v92_report_path = ROOT / 'experiments/python-gamebub-v92/wire/results.json'
    v92_report = json.loads(v92_report_path.read_text())
    selected_report = Path(v92_report['selected_report'])
    v92_frames_path = selected_report.with_name('frames.jsonl')
    if not v92_frames_path.is_absolute():
        v92_frames_path = ROOT / v92_frames_path
    v92_rows = {(row['cohort'], row['fid']): row
                for row in map(json.loads, v92_frames_path.read_text().splitlines())
                if row['policy'] == 'context_byte_min'}
    commitments = {(row['cohort'], row['fid']): row
                   for row in map(json.loads, wire.C2_CONTROL.read_text().splitlines())}

    sources = source_files(wire_path, old88_path, qcodec_path, oldmap_path,
                           groupmap_path, v92_report_path, v92_frames_path, args.native_index)
    pins = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    for path in sources:
        destination = out / 'sources' / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())

    report = dict(schema='cu66-v95-full-wire-v1', status='FAIL',
                  native_input_report=str(args.native_index.relative_to(ROOT)),
                  source_sha256=pins, profiles=list(PROFILE_NAMES), policies=list(POLICIES),
                  strict_cap_bytes=STRICT_CAP, research_cap_bytes=RESEARCH_CAP,
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  original_coefficient_parity_claimed=False, promoted_to_RTL=False,
                  commands=[], scope=[
                      'Exact canonical U8 pixel palettes in CS95; palette tiles bypass IDCT and reference reads.',
                      'Control/byte_min/work5/work15 use strict 49,152-byte receiver; uniform palette profiles use explicit research receiver.',
                      'All byte choices use complete serialized plane records and actually re-encoded EC92 residual streams.',
                      'Work policies maximize transforms avoided under complete-byte limits; work scores are not latency or FPS.' ])
    strict_binary = '/build/v95-wire-' + stamp
    research_binary = strict_binary + '-research'
    processes = {}
    archives = {}
    rows = []
    started = time.monotonic()
    old_handler = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise TimeoutError('CS95 complete frame campaign watchdog expired')

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 1800)
    report['watchdog_seconds'] = 1800
    try:
        for binary, flags, logname in (
                (strict_binary, [], 'compile-strict.log'),
                (research_binary, ['-DCS95_RESEARCH=1'], 'compile-research.log')):
            command = ['docker', 'exec', CONTAINER, 'g++', '-std=c++17', '-O2',
                       '-Wall', '-Wextra', '-Werror', *flags,
                       str(AREA / 'receiver.cpp'), '-o', binary]
            compiled = subprocess.run(command, capture_output=True, text=True, timeout=120)
            (out / logname).write_text(compiled.stdout + compiled.stderr)
            report['commands'].append(dict(argv=command, exit_code=compiled.returncode))
            assert compiled.returncode == 0, compiled.stderr
            copy = subprocess.run(['docker', 'cp', CONTAINER + ':' + binary,
                                   str(out / ('receiver-strict.bin' if not flags else 'receiver-research.bin'))],
                                  capture_output=True, text=True, timeout=30)
            report['commands'].append(dict(argv=['docker', 'cp', CONTAINER + ':' + binary],
                                           exit_code=copy.returncode))
            assert copy.returncode == 0, copy.stderr

        for policy in POLICIES:
            log = (out / (policy + '.stderr')).open('wb')
            binary = research_binary if policy not in STRICT_POLICIES else strict_binary
            command = ['docker', 'exec', '-i', CONTAINER, binary]
            report['commands'].append(dict(argv=command))
            process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=log)
            processes[policy] = (process, log)
            archives[policy] = gzip.open(out / ('packets-' + policy + '.bin.gz'), 'wb')

        qcache = {}
        with (out / 'frames.jsonl').open('w') as output:
            for frame, original in zip(data.iter_frames(index_path=args.native_index), native.iter_frames(), strict=True):
                ident = frame['cohort'], frame['fid']
                assert all(frame[key] == original[key]
                           for key in ('cohort', 'fid', 'ordinal', 'key'))
                assert len(frame['plane_variants']) == 3 and len(frame['palette_stats']) == 3
                for axis in range(3):
                    assert len(frame['plane_variants'][axis]) == 6
                    assert len(frame['palette_stats'][axis]) == 6
                baseline_row = v92_rows[ident]
                commitment = dict(commitments[ident])
                operations = [1 if hidden else 0 if not frame['key'] and zero == '1' else 2
                              for hidden, zero in zip(original['hidden_mask'], frame['zero_mask'], strict=True)]
                previous = None if frame['key'] else qcache.get(frame['cohort'])
                qblock = qcodec.encode(qcodec.unpacked(frame['qmap'], 1350), operations, previous)
                qcache[frame['cohort']] = qcodec.decode(qblock, operations, previous)

                # Reuse the qualified metadata/map/HUD path, then replace only its
                # EC92 body with complete CS95 plane payloads.
                old_packet, _, _ = wire.frame_packet(
                    frame, original, commitment, dict(kind='copy_group', cap=65536),
                    oldmap, groupmap)
                old_packet = old88.cs88(old_packet, qblock)
                old_data_bytes = int.from_bytes(old_packet[48:52], 'big')
                common_bytes = len(old_packet) - old_data_bytes
                baseline_bytes = common_bytes + sum(len(plane_bytes(frame, axis, 0))
                                                    for axis in range(3))
                assert baseline_bytes == baseline_row['wire_bytes'], (
                    'frozen V92 context_byte_min control bytes', ident,
                    baseline_bytes, baseline_row['wire_bytes'])

                selected, sizes, avoided = select_policies(frame, common_bytes, baseline_bytes)
                assert complete_bytes(frame, (0, 0, 0), common_bytes) == baseline_row['wire_bytes']
                for policy in POLICIES:
                    choice = selected[policy]
                    packet = cs95_packet(old_packet,
                                         [plane_bytes(frame, axis, choice[axis]) for axis in range(3)])
                    expected_size = sizes[choice]
                    assert len(packet) == expected_size
                    if policy in STRICT_POLICIES:
                        assert len(packet) <= STRICT_CAP, (policy, ident, len(packet))
                    else:
                        assert len(packet) <= RESEARCH_CAP, (policy, ident, len(packet))
                    process = processes[policy][0]
                    process.stdin.write(struct.pack('>II', frame['cohort'], len(packet)) + packet)
                    process.stdin.flush()
                    line = process.stdout.readline()
                    assert line, ('receiver ended', policy, ident, process.poll())
                    decoded = json.loads(line)
                    assert decoded['accepted'] and not decoded['replayed'], (policy, ident, decoded)
                    for key in ('canonical_sha256', 'hud_sha256', 'display_sha256'):
                        assert decoded[key] == frame[key], (policy, ident, key)
                    for key in ('root', 'seal'):
                        assert decoded[key] == commitment[key], (policy, ident, key)
                    assert decoded['generation'] == frame['ordinal'] + 1
                    assert decoded['wire_bytes'] == len(packet)
                    assert_decoded_matches(decoded, frame, choice)
                    stats_by_plane = [plane_stats(frame, axis, choice[axis]) for axis in range(3)]
                    uniform_profile_wire_bytes = {
                        PROFILE_NAMES[index]: sizes[(index, index, index)]
                        for index in PROFILE_INDICES
                    }
                    source_kind = frame.get('source_kind', frame.get('kind'))
                    row = dict(policy=policy, source_kind=source_kind,
                               cohort=frame['cohort'], fid=frame['fid'], ordinal=frame['ordinal'],
                               key=frame['key'], profile_indices=list(choice),
                               profiles=[PROFILE_NAMES[index] for index in choice],
                               wire_bytes=len(packet), fits_49152=len(packet) <= STRICT_CAP,
                               uniform_profile_wire_bytes=uniform_profile_wire_bytes,
                               avoided_tiles=avoided[choice],
                               transforms_avoided=avoided[choice],
                               residual_blocks=sum(int(stat['residual_blocks']) for stat in stats_by_plane),
                               strict_receiver=policy in STRICT_POLICIES,
                               packet_sha256=hashlib.sha256(packet).hexdigest(), decoded=decoded)
                    output.write(json.dumps(row, separators=(',', ':')) + '\n')
                    rows.append(row)
                    meta = json.dumps(row, separators=(',', ':')).encode()
                    archives[policy].write(struct.pack('<II', len(meta), len(packet)) + meta + packet)
                    if frame['cohort'] == 0 and frame['fid'] in (0, 1, 2) and policy in FIXTURE_POLICIES:
                        (out / f"c0-f{frame['fid']}-{policy}.cs95").write_bytes(packet)
                if len(rows) % (len(POLICIES) * 25) == 0:
                    print('V95_WIRE_PROGRESS', len(rows) // len(POLICIES), flush=True)

        for policy, archive in archives.items():
            archive.close()
            size = (out / ('packets-' + policy + '.bin.gz')).stat().st_size
            assert size < 50 * 1024 * 1024, ('per-policy packet archive exceeds 50 MiB', policy, size)
        for policy, (process, log) in processes.items():
            process.stdin.close()
            assert process.wait(timeout=30) == 0, policy
            log.close()
        assert len(rows) == 457 * len(POLICIES), len(rows)
        assert pins == {str(path.relative_to(ROOT)): sha(path) for path in sources}, 'source changed during campaign'
        summaries = []
        for policy in POLICIES:
            group = [row for row in rows if row['policy'] == policy]
            summaries.append(dict(policy=policy, frames=len(group),
                                  wire_bytes=stats([row['wire_bytes'] for row in group]),
                                  fits_49152=sum(row['fits_49152'] for row in group),
                                  avoided_tiles=sum(row['avoided_tiles'] for row in group),
                                  transforms_avoided=sum(row['transforms_avoided'] for row in group),
                                  residual_blocks=sum(row['residual_blocks'] for row in group)))
        report.update(status='PASS_NATIVE_CS95_FULL_PIXEL_ROOT_HUD_PARITY', frames=457,
                      packets=len(rows), summaries=summaries, strict_binary=strict_binary,
                      research_binary=research_binary, elapsed_seconds=time.monotonic() - started)
    except BaseException as error:
        report['failure'] = repr(error)
        report['elapsed_seconds'] = time.monotonic() - started
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        for archive in archives.values():
            if not archive.closed:
                archive.close()
        for process, log in processes.values():
            if process.poll() is None:
                try:
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if not log.closed:
                log.close()
        report['artifact_sha256'] = {
            str(path.relative_to(out)): sha(path)
            for path in sorted(out.rglob('*'))
            if path.is_file() and path != out / 'results.json'
        }
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        if report['status'].startswith('PASS_'):
            selected_report = str((out / 'results.json').relative_to(ROOT))
            (AREA / 'results.json').write_text(
                json.dumps(dict(report, selected_report=selected_report), indent=2) + '\n')
        print('V95_WIRE_REPORT', out / 'results.json', report['status'], flush=True)


if __name__ == '__main__':
    main()
