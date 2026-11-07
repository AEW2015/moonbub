#!/usr/bin/env python3
"""Actual CS92 rejection, retained history, recovery, replay and legacy exclusion."""
import datetime
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
AREA = ROOT/'experiments/python-gamebub-v92/wire'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def crc(data, endian='>'):
    return bytes(data[:-4])+struct.pack(endian+'I', zlib.crc32(data[:-4]))


def chunks(packet):
    start = 128+int.from_bytes(packet[36:40], 'big')+int.from_bytes(packet[40:44], 'big')
    result = []
    for _ in range(3):
        count = struct.unpack_from('>I', packet, start)[0]
        start += 4
        for _ in range(count):
            blocks, size = struct.unpack_from('>II', packet, start)
            start += 8
            result.append((start, size, blocks))
            start += size
    return result


def run_tests(out, report, processes):
    full = json.loads((AREA/'results.json').read_text())
    run = (ROOT/full['selected_report']).parent
    sources = [Path(__file__).resolve(), AREA/'receiver.cpp',
               ROOT/'experiments/python-gamebub-v92/python/codec.py',
               ROOT/'experiments/python-gamebub-v92/native/codec.hpp',
               AREA/'results.json', ROOT/full['selected_report'], run/'frames.jsonl']
    sources += [run/f'c0-f{fid}-context_work15.cs92' for fid in (0, 1, 2)]
    report['source_sha256'] = {str(path.relative_to(ROOT)): sha(path) for path in sources}
    for path in sources:
        destination = out/'sources'/path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
    # Persist pins and inputs before mutation search or receiver work can fail.
    (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    golden = {row['fid']: row['decoded'] for row in map(json.loads, (run/'frames.jsonl').read_text().splitlines())
              if row['policy'] == 'context_work15' and row['cohort'] == 0 and row['fid'] in (0, 1, 2)}
    assert set(golden) == {0, 1, 2}, 'missing qualified recovery goldens'
    spec = importlib.util.spec_from_file_location('v92_independent', ROOT/'experiments/python-gamebub-v92/python/codec.py')
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    key = (run/'c0-f0-context_work15.cs92').read_bytes()
    delta = (run/'c0-f1-context_work15.cs92').read_bytes()
    third = (run/'c0-f2-context_work15.cs92').read_bytes()
    first, size, blocks = chunks(delta)[0]
    original = delta[first:first+size]
    cases = []

    def replace(chunk, start=first, length=size):
        assert len(chunk) == length
        return crc(delta[:start]+chunk+delta[start+length:])

    def mutate(name, at, value):
        part = bytearray(original)
        part[at] = value
        cases.append((name, replace(crc(part, '<'))))

    for name, at, value in (('EC92_magic', 0, 0), ('EC92_version', 4, 2), ('EC92_flags', 5, 2),
                            ('EC92_selector_upper_nibble', 6, original[6] | 16), ('EC92_reserved_byte', 7, 1),
                            ('EC92_blocks', 8, (original[8]+1) % 256), ('EC92_predictor', 12, 0),
                            ('EC92_reserved_word', 14, 1), ('EC92_DC_k', 44, 14), ('EC92_DC_k1', 45, 0)):
        mutate(name, at, value)
    for name, at, value in (('EC92_stream_length', 16, 0), ('EC92_AC_event_overrun', 32, blocks*5+1), ('EC92_DC_bit_length', 46, 0)):
        part = bytearray(original)
        struct.pack_into('<I', part, at, value)
        cases.append((name, replace(crc(part, '<'))))
    part = bytearray(original)
    part[-1] ^= 1
    cases.append(('EC92_inner_CRC', replace(part)))
    outer = bytearray(delta)
    outer[-1] ^= 1
    cases.append(('CS92_outer_CRC', bytes(outer)))
    for name, magic in (('explicit_old_CS88_reject', b'CS88'), ('explicit_unknown_profile', b'CS93')):
        cases.append((name, crc(magic+delta[4:])))
    # Complete-wire cap fails closed in transport before packet allocation.
    oversized = delta+bytes(49153-len(delta))
    for name, packet in cases:
        (out/'inputs'/f'{name}.cs92').write_bytes(packet)
    report['active_case'] = 'late_semantic_mutation_search'
    # Flip a meaningful bit in the LAST plane, preserve both CRCs, and demand
    # a late semantic rejection after all preceding candidate work.
    changed = None
    last, last_size, last_blocks = chunks(delta)[-1]
    plane = delta[last:last+last_size]
    expected = reader.decode(plane, last_blocks)
    dc_length = struct.unpack_from('<I', plane, 16)[0]
    for at in range(50, min(44+dc_length, 90)):
        for bit in range(8):
            part = bytearray(plane)
            part[at] ^= 1 << bit
            part = crc(part, '<')
            try:
                decoded = reader.decode(part, last_blocks)
            except (ValueError, AssertionError, IndexError):
                continue
            if decoded != expected:
                changed = replace(part, last, last_size)
                break
        if changed is not None:
            break
    assert changed is not None, 'could not find grammar-valid late semantic mutation'
    cases.append(('last_plane_valid_coefficients_late_reject', changed))
    for name, packet in cases:
        (out/'inputs'/f'{name}.cs92').write_bytes(packet)
        process = subprocess.Popen(['docker', 'exec', '-i', CONTAINER, full['binary']], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(process)
        report['active_case'] = name

        def receive(p):
            process.stdin.write(struct.pack('>II', 0, len(p))+p)
            process.stdin.flush()
            line = process.stdout.readline()
            return json.loads(line) if line else None

        accepted = receive(key)
        rejected = receive(packet)
        assert accepted == golden[0] and not rejected['accepted'] and rejected['retained_fid'] == 0, (name, rejected)
        if name == 'last_plane_valid_coefficients_late_reject':
            assert rejected['error'] == 'CS92 reconstructed content root', rejected
        recovered = receive(delta)
        replayed = receive(delta)
        next_frame = receive(third)
        assert recovered == golden[1] and replayed == dict(golden[1], replayed=True), (name, recovered, replayed)
        assert next_frame == golden[2], (name, next_frame)
        process.stdin.close()
        assert process.wait(timeout=15) == 0
        report['checks'].append(dict(name=name, status='PASS_REJECT_RETAIN_RECOVER_REPLAY_NEXT',
                                     rejected=rejected, recovered=recovered, packet_sha256=hashlib.sha256(packet).hexdigest()))
    over = crc(oversized)
    (out/'inputs'/'complete_frame_49153_reject.cs92').write_bytes(over)
    report['active_case'] = 'complete_frame_49153_reject'
    boundary = subprocess.run(['docker', 'exec', '-i', CONTAINER, full['binary']],
                              input=struct.pack('>II', 0, len(over))+over, capture_output=True, timeout=30)
    assert boundary.returncode != 0 and not boundary.stdout and b'transport framing' in boundary.stderr
    report['checks'].append(dict(name='complete_frame_49153_reject', status='PASS_FAIL_CLOSED_TRANSPORT_CAP',
                                 error=boundary.stderr.decode(), observed_exit_code=boundary.returncode))
    # Old qualified receiver must reject the new explicit envelope, even though
    # the unchanged canonical/reference/HUD commitments would otherwise match.
    old = json.loads((ROOT/'experiments/python-gamebub-v88/wire/results.json').read_text())
    report['active_case'] = 'legacy_CS88_rejects_CS92'
    process = subprocess.run(['docker', 'exec', '-i', CONTAINER, old['binary']], input=struct.pack('>II', 0, len(key))+key,
                             capture_output=True, timeout=30)
    result = json.loads(process.stdout)
    assert process.returncode == 0 and not result['accepted'] and 'profile' in result['error']
    report['checks'].append(dict(name='legacy_CS88_rejects_CS92', status='PASS', result=result))
    assert report['source_sha256'] == {p: sha(ROOT/p) for p in report['source_sha256']}
    report.update(status='PASS_CS92_PROTOCOL_RECOVERY', checks_count=len(report['checks']))
    report.pop('active_case', None)


def main():
    out = AREA/'test-attempts'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    (out/'inputs').mkdir(parents=True)
    report = dict(schema='cu66-v92-wire-recovery-v1', status='FAIL', checks=[], watchdog_seconds=180,
                  source_sha256={str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__).resolve())},
                  scope='Synchronous host native admission/commit; no RTL asynchronous drain or hardware proof.')
    (out/'source-test_wire.py').write_bytes(Path(__file__).read_bytes())
    (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
    processes = []
    started = time.monotonic()
    def watchdog(signum, frame):
        raise TimeoutError('CS92 recovery test watchdog expired')
    signal.signal(signal.SIGALRM, watchdog)
    signal.alarm(180)
    try:
        run_tests(out, report, processes)
    except BaseException as error:
        report.update(status='FAIL', failure=repr(error))
        raise
    finally:
        signal.alarm(0)
        for index, process in enumerate(processes):
            try:
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
                if process.stderr is not None and not process.stderr.closed:
                    (out/f'native-{index}.stderr').write_bytes(process.stderr.read())
                for stream in (process.stdout, process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()
            except BaseException as error:
                report.setdefault('cleanup_errors', []).append(repr(error))
        report['wall_seconds'] = time.monotonic()-started
        report['artifact_sha256'] = {str(path.relative_to(out)): sha(path) for path in out.rglob('*')
                                     if path.is_file() and path != out/'results.json'}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        print(report['status'], out/'results.json', flush=True)
    (AREA/'tests.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')


if __name__ == '__main__':
    main()
