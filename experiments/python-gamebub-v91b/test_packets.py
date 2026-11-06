#!/usr/bin/env python3
"""Independent packet mutation and provisional-publication checks for V91b."""
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crc(body):
    return bytes(body) + struct.pack('<I', zlib.crc32(body))


def fixture():
    # One DC +1: unsigned zigzag2 => 001. AC band1 first-position -1:
    # run0=>1, level zigzag(-1)-1=0=>1; other AC bands empty.
    streams = [struct.pack('<BBI', 0, 255, 3) + b'\x20',
               struct.pack('<BBI', 0, 0, 2) + b'\xc0',
               struct.pack('<BBI', 0, 0, 0), struct.pack('<BBI', 0, 0, 0)]
    header = b'BR88\x01\x00' + struct.pack('<IHH4I3I', 1, 1, 0,
        *(len(stream) for stream in streams), 1, 0, 0)
    return crc(header + b''.join(streams))


def outcome(fn, packet):
    try:
        return 'accept', tuple(fn(packet))
    except ValueError:
        return 'reject', ()


def main():
    model = load('v91b_packets_model', AREA / 'context.py')
    word_path = ROOT / 'experiments/python-gamebub-v91/parser.py'
    frozen_path = ROOT / 'experiments/python-gamebub-v88/entropy/codec.py'
    word = load('v91b_packets_word', word_path)
    frozen = load('v91b_packets_control', frozen_path)
    pins = {str(path.relative_to(ROOT)): sha(path)
            for path in (Path(__file__), AREA / 'context.py', word_path, frozen_path)}
    control = lambda packet: frozen.decode(packet, 1)
    candidate = lambda packet: model.decode(packet, 1, word.WordRice)[0]
    packet = fixture()
    assert candidate(packet) == tuple(control(packet)) == (1, -1) + (0,) * 62
    cases = [('valid_fixture', packet)]
    # Every single bit, both with original CRC and deliberately recomputed CRC.
    # CRC repair is needed to reach grammar checks rather than only CRC failure.
    for at in range(len(packet) - 4):
        for bit in range(8):
            body = bytearray(packet[:-4])
            body[at] ^= 1 << bit
            cases.append((f'bit{at}_{bit}_unrepaired', bytes(body) + packet[-4:]))
            cases.append((f'bit{at}_{bit}_crc_repaired', crc(body)))
    for length in range(len(packet)):
        cases.append((f'prefix{length}', packet[:length]))
    rng = random.Random(911091)
    for trial in range(2048):
        body = bytearray(packet[:-4])
        for _ in range(1 + rng.randrange(4)):
            body[rng.randrange(len(body))] = rng.randrange(256)
        cases.append((f'multi{trial}', crc(body)))
    rows = []
    for name, item in cases:
        old, new = outcome(control, item), outcome(candidate, item)
        assert old == new, (name, old, new)
        rows.append(dict(name=name, packet_sha256=hashlib.sha256(item).hexdigest(),
                         outcome=new[0], coefficients_sha256=(hashlib.sha256(struct.pack('<64h', *new[1])).hexdigest()
                                                              if new[0] == 'accept' else None)))
    # A malformed late AC context must abort the transaction even after its DC
    # coefficient has already been consumed provisionally. Capture the actual
    # transaction used by decode rather than infer publication from an exception.
    captured = []
    original = model.Transaction

    class RecordingTransaction(original):
        def __init__(self):
            super().__init__()
            captured.append(self)

    model.Transaction = RecordingTransaction
    try:
        body = bytearray(packet[:-4])
        # AC stream starts49: leave declared bitcount2, change11 ->10. Run0
        # completes then a missing level terminator fails after valid DC output.
        body[55] = 0x80
        assert outcome(candidate, crc(body))[0] == 'reject'
        assert len(captured) == 1 and captured[0].accepted == 1
        assert not captured[0].active and captured[0].pending is None
        assert captured[0].published is None
    finally:
        model.Transaction = original
    assert pins == {path: sha(ROOT / path) for path in pins}
    details = AREA / 'packet-checks.jsonl'
    details.write_text(''.join(json.dumps(row, separators=(',', ':')) + '\n' for row in rows))
    report = dict(schema='cu66-v91b-independent-packet-checks-v1', status='PASS', source_sha256=pins,
                  seed=911091, cases=len(rows), accepted=sum(row['outcome'] == 'accept' for row in rows),
                  rejected=sum(row['outcome'] == 'reject' for row in rows),
                  late_failure_after_provisional_DC_abort_checked=True,
                  details_path=str(details.relative_to(ROOT)), details_sha256=sha(details),
                  scope='Functional Python packet and transaction qualification; no cycles, hardware or memory-fit claim.')
    (AREA / 'packet-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
