#!/usr/bin/env python3
"""Independent read-only audit of the selected portable native endpoint proof."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib

ROOT = Path(__file__).resolve().parents[2]
checks = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(ok, name):
    checks.append(dict(name=name, pass_=bool(ok)))
    if not ok:
        raise ValueError(name)


def load(path):
    return json.loads(path.read_text())


def pin(meta):
    path = ROOT / meta['path']
    check(digest(path) == meta['sha256'], 'pin ' + meta['path'])
    return path


def main():
    selector = ROOT / 'experiments/python-gamebub-v124/endpoint/results.json'
    selected = load(selector)
    receipt_path = pin(selected['selected_receipt'])
    receipt = load(receipt_path)
    attempt = receipt_path.parent
    result_path = pin(selected['result'])
    result = load(result_path)
    check(selected['status'] == 'PASS_NATIVE_PACKETIZER_TO_RUST_RECEIVER' and
          receipt['status'] == 'PASS', 'executed selected PASS')
    check(receipt['exit_code'] == 0, 'process exited zero')
    check(digest(result_path) == receipt['result_sha256'], 'receipt result hash')
    for name, meta in receipt['source_snapshots'].items():
        snap = attempt / name
        check(digest(snap) == meta['sha256'], 'snapshot ' + name)
        if meta['git_blob_sha256'] is not None:
            repo = Path(meta['repo'])
            blob = subprocess.check_output(['git', '-C', str(repo), 'show',
                meta['git_head'] + ':' + meta['source_path']])
            check(hashlib.sha256(blob).hexdigest() == meta['git_blob_sha256'] ==
                  meta['sha256'], 'Git origin ' + name)
            check((repo / meta['source_path']).read_bytes() == blob,
                  'current production source unchanged ' + name)
        else:
            check(digest(ROOT / meta['source_path']) == meta['sha256'],
                  'current probe source ' + name)
    for name, expected in receipt['output_sha256'].items():
        check(digest(attempt / name) == expected, 'output ' + name)
    for name, expected in result['binary_sha256'].items():
        check(digest(attempt / 'bin' / name) == expected, 'binary ' + name)
    check('-Wall' in receipt['commands']['cpp'] and
          '-Wextra' in receipt['commands']['cpp'] and
          '-Werror' in receipt['commands']['cpp'], 'strict C++ flags')
    rust = receipt['commands']['rust']
    check('-D' in rust and rust[rust.index('-D') + 1] == 'warnings',
          'strict Rust warnings')
    packets = (attempt / 'out/native-1024.bin').read_bytes()
    golden = (attempt / 'source/sunshine/receiver-pattern-msv1-packets.bin').read_bytes()
    jpeg = (attempt / 'source/sunshine/receiver-pattern-720x480-420-q65.jpg').read_bytes()
    check(packets == golden and len(packets) == 27251, 'native packet bytes exact')
    at = 0
    datagrams = []
    while at < len(packets):
        size = int.from_bytes(packets[at:at + 2], 'big')
        at += 2
        datagrams.append(packets[at:at + size])
        at += size
    check(at == len(packets) and len(datagrams) == 26, 'u16 framing exact')
    # Header fields are specified by the production MSV1 protocol, not Python producer output.
    offset = 0
    payloads = []
    crc = zlib.crc32(jpeg) & 0xffffffff
    for index, packet in enumerate(datagrams):
        check(len(packet) >= 40 and packet[:6] == b'MSV1\x01\x01',
              'native datagram identity ' + str(index))
        flags, frame_id, width, height, length, off, count, reserved, raw_crc, capture = \
            struct.unpack_from('>HIHHIIHHIQ', packet, 6)
        check((frame_id, width, height, length, off, reserved, raw_crc, capture) ==
              (0x12345678, 720, 480, len(jpeg), offset, 0, crc, 1234567890123),
              'native raw header fields ' + str(index))
        check(0 < count <= 1024 and len(packet) == 40 + count and
              flags == (int(off == 0) | (int(off + count == len(jpeg)) << 1)),
              'native payload bounds and flags ' + str(index))
        payloads.append(packet[40:])
        offset += count
    check(offset == len(jpeg) and b''.join(payloads) == jpeg,
          'native direct payload concatenation and CRC')
    expected = {
        'native_golden_1024': ([], [0x12345678]),
        'native_chunk_100': ([], [0x12345678]),
        'native_chunk_1_bounded': ([], [0x12345678]),
        'loss_then_recovery': (['Sequence'], [0x12345679]),
        'reorder_then_recovery': (['Sequence'], [0x12345679]),
        'duplicate_then_recovery': (['Sequence'], [0x12345679]),
        'truncated_final_then_recovery': (['Bounds'], [0x12345679]),
        'corrupt_final_then_recovery': (['Integrity'], [0x12345679]),
        'stale_id_then_recovery': (['Sequence'] * 26, [0x12345678, 0x12345679]),
        'u32_wrap_max_to_zero': ([], [0xffffffff, 0]),
    }
    check(set(expected) == {c['name'] for c in result['cases']}, 'complete case set')
    for case in result['cases']:
        name = case['name']
        errors, ids = expected[name]
        events = load(attempt / ('out/case-' + name + '.json'))
        check([e['error'] for e in events if e['type'] == 'error'] == errors,
              name + ' raw backend errors')
        check([e['id'] for e in events if e['type'] == 'done'] == ids,
              name + ' raw completed IDs')
        check(not any(e['type'] in ('wrapper_error', 'framing_error') for e in events),
              name + ' no wrapper/framing error')
        check((attempt / ('out/case-' + name + '.jpg')).read_bytes() == jpeg * len(ids),
              name + ' recovered bytes exact')
        feedback = (attempt / ('out/case-' + name + '.json.msf1')).read_bytes()
        check(len(feedback) == 32 * len(ids) and all(
            feedback[i:i + 4] == b'MSF1' and struct.unpack_from('>I', feedback, i + 8)[0] == frame_id
            for i, frame_id in zip(range(0, len(feedback), 32), ids)),
            name + ' actual feedback identity')
        raw_input = (attempt / ('out/case-' + name + '.u16')).read_bytes()
        input_packets = []
        at = 0
        while at < len(raw_input):
            size = int.from_bytes(raw_input[at:at + 2], 'big')
            at += 2
            input_packets.append(raw_input[at:at + size])
            at += size
        check(at == len(raw_input), name + ' raw case framing')
        accepted_bytes, dropped, feedback_at = 0, 0, 0
        for event in events:
            if event['type'] == 'accepted':
                accepted_bytes += event['count']
            elif event['type'] == 'error':
                dropped += 1
            elif event['type'] == 'done':
                capture = int.from_bytes(input_packets[event['index']][32:40], 'big')
                record = struct.unpack_from('>4sBBHIIIIQ', feedback, feedback_at)
                check(record == (b'MSF1', 1, 1, 0, event['id'], 0,
                      accepted_bytes & 0xffffffff, dropped, capture),
                      name + ' complete raw feedback ' + str(feedback_at // 32))
                feedback_at += 32
        check(feedback_at == len(feedback), name + ' no extra feedback records')
    policy = receipt['resource_policy']
    check(policy['cpus'] == 2 and policy['memory_bytes'] == policy['memory_swap_bytes'] ==
          8 * 1024**3 and policy['network'] == 'none', 'bounded resource policy')
    output = dict(schema='v124-independent-native-endpoint-audit-v1', status='PASS',
                  selector=dict(path=str(selector.relative_to(ROOT)), sha256=digest(selector)),
                  receipt=selected['selected_receipt'], result=selected['result'],
                  auditor_sha256=digest(Path(__file__)), checks=checks,
                  scope='Portable native serializer/parser only; no CPU/RF/QSPI/hardware timing.')
    path = ROOT / 'experiments/python-gamebub-v124/audit/endpoint.json'
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status='PASS', checks=len(checks), output=str(path.relative_to(ROOT)))))


if __name__ == '__main__':
    main()
