#!/usr/bin/env python3
"""CS93 strict transport, entropy rejection, retained history and recovery.

Uses the completed wire campaign's exact per-policy goldens. Every native
receiver is guarded inside the container and tracked for failure cleanup.
"""
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
AREA = ROOT / 'experiments/python-gamebub-v93/wire'
CONTAINER = 'gamebub-cu66-v69-build'
CAP = 49152


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(data, endian='>'):
    return bytes(data[:-4]) + struct.pack(endian + 'I', zlib.crc32(data[:-4]))


def chunks(packet):
    start = 128 + int.from_bytes(packet[36:40], 'big') + int.from_bytes(packet[40:44], 'big')
    result = []
    for _ in range(3):
        count = struct.unpack_from('>I', packet, start)[0]
        start += 4
        for _ in range(count):
            blocks, size = struct.unpack_from('>II', packet, start)
            start += 8
            assert size >= 48 and start + size <= len(packet) - 4
            result.append((start, size, blocks))
            start += size
    return result


def run_tests(out, report, processes):
    def checkpoint():
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')

    def pin(path):
        name = str(path.relative_to(ROOT))
        digest = sha(path)
        assert name not in report['source_sha256'] or report['source_sha256'][name] == digest
        report['source_sha256'][name] = digest
        destination = out / 'sources' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
        checkpoint()

    full = json.loads((AREA / 'results.json').read_text())
    assert full['status'] == 'PASS_NATIVE_CS93_FULL_FRAME_PARITY', 'wire campaign must finish before recovery qualification'
    run = (ROOT / full['selected_report']).parent
    legacy_path = ROOT / 'experiments/python-gamebub-v92/wire/results.json'
    old = json.loads(legacy_path.read_text())
    sources = [Path(__file__).resolve(), AREA / 'receiver.cpp',
               ROOT / 'experiments/python-gamebub-v93/python/codec.py',
               ROOT / 'experiments/python-gamebub-v93/native/codec.hpp',
               AREA / 'results.json', ROOT / full['selected_report'], run / 'frames.jsonl', legacy_path]
    if 'selected_report' in old:
        sources.append(ROOT / old['selected_report'])
    sources += [run / f'c0-f{fid}-{policy}.cs93'
                for policy in ('byte_min', 'prefix_suffix', 'small_group') for fid in (0, 1, 2)]
    for path in sources:
        pin(path)
    golden = {(row['policy'], row['fid']): row['decoded']
              for row in map(json.loads, (run / 'frames.jsonl').read_text().splitlines())
              if row['policy'] in ('byte_min', 'prefix_suffix', 'small_group') and row['cohort'] == 0 and row['fid'] in (0, 1, 2)}
    assert len(golden) == 9, 'missing per-policy recovery goldens'
    (out / 'qualified-goldens.json').write_text(json.dumps(
        {f'{policy}-f{fid}': result for (policy, fid), result in golden.items()}, indent=2) + '\n')
    spec = importlib.util.spec_from_file_location('v93_independent', ROOT / 'experiments/python-gamebub-v93/python/codec.py')
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    packets = {(policy, fid): (run / f'c0-f{fid}-{policy}.cs93').read_bytes()
               for policy in ('byte_min', 'prefix_suffix', 'small_group') for fid in (0, 1, 2)}
    for (policy, fid), packet in packets.items():
        assert len(packet) == golden[policy, fid]['wire_bytes']
    key, delta, third = (packets['byte_min', fid] for fid in (0, 1, 2))
    assert all(len(p) <= CAP for p in (key, delta, third)), 'primary requires strict 49152-byte receiver'
    cases = []

    def replace(source, chunk, start, length):
        """Replace one EC93 chunk; adjust outer length metadata and both CRCs."""
        part = bytearray(source[:start] + chunk + source[start + length:])
        difference = len(chunk) - length
        struct.pack_into('>I', part, start - 4, len(chunk))
        struct.pack_into('>I', part, 48, struct.unpack_from('>I', source, 48)[0] + difference)
        return crc(part)

    first, size, blocks = next(item for item in chunks(delta) if delta[item[0] + 5] == 0)
    original = delta[first:first + size]

    def add(name, packet, policy='byte_min'):
        assert len(packet) <= CAP, (name, len(packet))
        path = out / 'inputs' / f'{name}.cs93'
        path.write_bytes(packet)
        cases.append((name, packet, policy))
        checkpoint()

    def mutate(name, at, value):
        part = bytearray(original)
        part[at] = value
        add(name, replace(delta, crc(part, '<'), first, size))

    for name, at, value in (
            ('EC93_magic', 0, 0), ('EC93_version', 4, 2), ('EC93_flags', 5, 2),
            ('EC93_reserved_byte', 7, 1), ('EC93_blocks', 8, (original[8] + 1) % 256),
            ('EC93_predictor', 12, 0), ('EC93_reserved_word', 14, 1)):
        mutate(name, at, value)
    # All eight selector bits are meaningful in EC93; no reserved-nibble case.
    dc_method = original[6] & 3
    dc_descriptor = 44 + (6 if dc_method == 3 else 0)
    mutate('EC93_DC_k', dc_descriptor, 14)
    mutate('EC93_DC_k1', dc_descriptor + 1, 0)
    for name, at, value in (
            ('EC93_stream_length', 16, 0), ('EC93_AC_event_overrun', 32, blocks * 5 + 1),
            ('EC93_DC_bit_length', dc_descriptor + 2, 0)):
        part = bytearray(original)
        struct.pack_into('<I', part, at, value)
        add(name, replace(delta, crc(part, '<'), first, size))
    part = bytearray(original); part[-1] ^= 1
    add('EC93_inner_CRC', replace(delta, part, first, size))
    outer = bytearray(delta); outer[-1] ^= 1
    add('CS93_outer_CRC', bytes(outer))
    for name, magic in (('explicit_old_CS92_reject', b'CS92'), ('explicit_unknown_profile', b'CS94')):
        add(name, crc(magic + delta[4:]))

    for policy, method in (('prefix_suffix', 2), ('small_group', 3)):
        source = packets[policy, 1]
        if len(source) > CAP:
            report.setdefault('skipped', []).append(dict(policy=policy, wire_bytes=len(source), reason='homogeneous control exceeds strict 49152-byte transport cap'))
            continue
        for context in range(4):
            target = None
            for start, length, nblocks in chunks(source):
                plane = source[start:start + length]
                if plane[5] == 0 and ((plane[6] >> (2 * context)) & 3) == method:
                    streams = reader.parse_header(plane, nblocks)[2]
                    target = start, length, plane, 44 + sum(map(len, streams[:context])), streams[context]
                    break
            assert target is not None, ('missing homogeneous method context', policy, context)
            start, length, plane, offset, stream = target
            if method == 2:
                for label, field, value in (('prefix_zero', 2, 0),
                        ('prefix_length', 2, struct.unpack_from('<I', stream, 2)[0] + 8),
                        ('suffix_length', 6, struct.unpack_from('<I', stream, 6)[0] + 8)):
                    part = bytearray(plane)
                    struct.pack_into('<I', part, offset + field, value)
                    add(f'HY_c{context}_{label}', replace(source, crc(part, '<'), start, length), policy)
            else:
                for label, field, value in (('group_size', 0, 31), ('reserved', 1, 1)):
                    part = bytearray(plane); part[offset + field] = value
                    add(f'SG_c{context}_{label}', replace(source, crc(part, '<'), start, length), policy)
                part = bytearray(plane)
                struct.pack_into('<I', part, offset + 2, struct.unpack_from('<I', stream, 2)[0] + 1)
                add(f'SG_c{context}_group_count', replace(source, crc(part, '<'), start, length), policy)
                if len(source) + 6 <= CAP:
                    # Append an unadvertised empty group within this exact stream.
                    end = offset + len(stream)
                    part = bytearray(plane[:end] + struct.pack('<BBI', 0, 255 if context == 0 else 0, 0) + plane[end:])
                    struct.pack_into('<I', part, 16 + context * 4, len(stream) + 6)
                    add(f'SG_c{context}_trailing_group', replace(source, crc(part, '<'), start, length), policy)
                else:
                    report.setdefault('skipped', []).append(dict(name=f'SG_c{context}_trailing_group', reason='adding group exceeds strict transport cap'))

    report['active_case'] = 'late_semantic_mutation_search'
    checkpoint()
    # Keep both grammars valid while forcing a LAST-plane content-root failure.
    changed = None
    last, last_size, last_blocks = chunks(delta)[-1]
    plane = delta[last:last + last_size]
    expected = reader.decode(plane, last_blocks)
    dc_length = struct.unpack_from('<I', plane, 16)[0]
    for at in range(50, min(44 + dc_length, 110)):
        for bit in range(8):
            part = bytearray(plane); part[at] ^= 1 << bit
            part = crc(part, '<')
            try:
                decoded = reader.decode(part, last_blocks)
            except ValueError:
                continue
            if decoded != expected:
                changed = replace(delta, part, last, last_size)
                break
        if changed is not None:
            break
    assert changed is not None, 'could not find grammar-valid late semantic mutation'
    add('last_plane_valid_coefficients_late_reject', changed)

    def start_receiver(binary, name):
        index = len(processes)
        pidfile = f'/tmp/cu66-v93-recovery-{out.name}-{index}.pid'
        log = (out / f'native-{index}-{name}.stderr').open('wb')
        # The PID names the in-container timeout, which forwards TERM to the
        # native child. Killing a docker exec client alone does not ensure this.
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

    for name, packet, policy in cases:
        report['active_case'] = name
        checkpoint()
        record = start_receiver(full['binary'], name)
        accepted = receive(record, key)
        rejected = receive(record, packet)
        assert accepted == golden['byte_min', 0], (name, accepted)
        assert not rejected['accepted'] and rejected['retained_fid'] == 0, (name, rejected)
        if name == 'last_plane_valid_coefficients_late_reject':
            assert rejected['error'] == 'CS93 reconstructed content root', rejected
        recovery = packets[policy, 1]
        recovered = receive(record, recovery)
        replayed = receive(record, recovery)
        next_frame = receive(record, third)
        assert recovered == golden[policy, 1], (name, recovered)
        assert replayed == dict(golden[policy, 1], replayed=True), (name, replayed)
        assert next_frame == golden['byte_min', 2], (name, next_frame)
        finish(record)
        report['checks'].append(dict(name=name, status='PASS_REJECT_RETAIN_RECOVER_REPLAY_NEXT',
            recovery_policy=policy, rejected=rejected, recovered=recovered,
            packet_sha256=hashlib.sha256(packet).hexdigest()))
        checkpoint()

    # Histories are format-independent while wire-byte accounting is per packet.
    if all(len(packets[policy, fid]) <= CAP for policy, fid in (('prefix_suffix', 1), ('small_group', 2))):
        report['active_case'] = 'cross_method_history_byte_min_HY_SG'
        checkpoint()
        record = start_receiver(full['binary'], 'cross-method')
        for policy, fid in (('byte_min', 0), ('prefix_suffix', 1), ('small_group', 2)):
            result = receive(record, packets[policy, fid])
            assert result == golden[policy, fid], (policy, fid, result)
        result = receive(record, packets['small_group', 2])
        assert result == dict(golden['small_group', 2], replayed=True)
        finish(record)
        report['checks'].append(dict(name='cross_method_history_byte_min_HY_SG', status='PASS_FULL_POLICY_GOLDENS_AND_REPLAY'))
    else:
        report.setdefault('skipped', []).append(dict(name='cross_method_history_byte_min_HY_SG', reason='HY delta or SG next frame exceeds strict 49152-byte transport cap'))

    # Strict binary must fail before packet allocation at cap+1.
    oversized = crc(delta + bytes(CAP + 1 - len(delta)))
    (out / 'inputs' / 'complete_frame_49153_reject.cs93').write_bytes(oversized)
    report['active_case'] = 'complete_frame_49153_reject'
    checkpoint()
    record = start_receiver(full['binary'], 'oversized')
    process = record['process']
    output, _ = process.communicate(struct.pack('>II', 0, len(oversized)) + oversized, timeout=30)
    record['finished'] = True
    record['log'].flush()
    error = (out / f'native-{processes.index(record)}-oversized.stderr').read_bytes()
    assert process.returncode != 0 and not output and b'transport framing' in error, (process.returncode, output, error)
    report['checks'].append(dict(name='complete_frame_49153_reject', status='PASS_FAIL_CLOSED_TRANSPORT_CAP',
                               error=error.decode(), observed_exit_code=process.returncode))

    report['active_case'] = 'legacy_CS92_rejects_CS93'
    checkpoint()
    record = start_receiver(old['binary'], 'legacy-CS92')
    result = receive(record, key)
    assert not result['accepted'] and 'profile' in result['error'], result
    finish(record)
    report['checks'].append(dict(name='legacy_CS92_rejects_CS93', status='PASS', result=result))
    assert report['source_sha256'] == {name: sha(ROOT / name) for name in report['source_sha256']}, 'executed inputs changed'
    report.update(status='PASS_CS93_PROTOCOL_RECOVERY', checks_count=len(report['checks']),
                  strict_binary=full['binary'], research_binary_used=False)
    report.pop('active_case', None)


def main():
    out = AREA / 'test-attempts' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    (out / 'inputs').mkdir(parents=True)
    report = dict(schema='cu66-v93-wire-recovery-v1', status='FAIL', checks=[], watchdog_seconds=180,
                  source_sha256={str(Path(__file__).resolve().relative_to(ROOT)): sha(Path(__file__).resolve())},
                  scope='Strict 49152-byte synchronous host native admission/commit; no RTL asynchronous drain or hardware proof.')
    (out / 'source-test_wire.py').write_bytes(Path(__file__).read_bytes())
    (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    processes = []
    started = time.monotonic()
    prior = signal.getsignal(signal.SIGALRM)
    def watchdog(signum, frame):
        raise TimeoutError('CS93 recovery test watchdog expired')
    signal.signal(signal.SIGALRM, watchdog)
    signal.alarm(180)
    try:
        run_tests(out, report, processes)
    except BaseException as error:
        report.update(status='FAIL', failure=repr(error))
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prior)
        for record in processes:
            process = record['process']
            try:
                # Terminate container-side timeout first, forwarding TERM to the
                # receiver; do not rely on closing the docker client pipe.
                cleanup = ('rm -f "$1"' if record['finished'] else
                    'if test -r "$1"; then read -r p < "$1"; kill -TERM "$p" 2>/dev/null || :; rm -f "$1"; fi')
                result = subprocess.run(['docker', 'exec', CONTAINER, 'sh', '-c', cleanup, 'sh', record['pidfile']], capture_output=True, timeout=10)
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
    assert report['status'] == 'PASS_CS93_PROTOCOL_RECOVERY', report.get('failure')


if __name__ == '__main__':
    main()
