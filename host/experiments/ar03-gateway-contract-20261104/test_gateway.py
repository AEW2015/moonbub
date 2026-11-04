"""Native UBSan replay of pinned wire vectors, plus malformed boundary cases."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

HERE = Path(__file__).resolve().parent


class Frame(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ('epoch', 'frame', 'total', 'body_crc')] + [
        ('nonce', C.c_uint64), ('slot', C.c_uint16), ('kind', C.c_uint8)]


class Data(C.Structure):
    _fields_ = [(n, C.c_uint32) for n in ('epoch', 'frame', 'total', 'complete_crc', 'body_crc', 'token_header_crc')] + [
        ('sequence', C.c_uint64)] + [(n, C.c_uint16) for n in ('packet_slot', 'index', 'count', 'payload_bytes')]


def seal(data):
    return data + struct.pack('!I', zlib.crc32(data))


class Tests(unittest.TestCase):
    def parse(self, name, data, cls, epoch=1):
        out = cls()
        C.memset(C.byref(out), 0xa5, C.sizeof(out))
        before = bytes(out)
        buf = C.create_string_buffer(data)
        rc = getattr(self.lib, name)(buf, len(data), epoch, C.byref(out))
        if rc:
            self.assertEqual(bytes(out), before, 'rejection must not mutate output')
        return rc, out

    def test_all_retained_controls(self):
        count = 0
        for case in self.contract['frame_control_sequences']:
            for event in case['events']:
                data = bytes.fromhex(event['wire_hex'])
                self.assertEqual(hashlib.sha256(data).hexdigest(), event['wire_sha256'])
                rc, out = self.parse('gb_parse_fg19', data, Frame)
                self.assertEqual(rc, 0)
                expected = event['parsed']
                for field, source in [('epoch', 'epoch'), ('frame', 'frame'), ('total', 'total'),
                                      ('body_crc', 'crc'), ('nonce', 'seq'), ('slot', 'slot'), ('kind', 'kind')]:
                    self.assertEqual(getattr(out, field), expected[source])
                encoded = C.create_string_buffer(40)
                C.memset(encoded, 0xa5, 40)
                self.assertEqual(self.lib.gb_write_fg19(C.byref(out), encoded, 40), 36)
                self.assertEqual(encoded.raw[:36], data)
                self.assertEqual(encoded.raw[36:], bytes([0xa5]) * 4)
                count += 1
        self.assertEqual(count, 1725)

    def test_controls_all_single_bit_corruptions(self):
        valid = bytes.fromhex(self.contract['frame_control_sequences'][0]['events'][0]['wire_hex'])
        for i in range(len(valid)):
            for bit in range(8):
                bad = bytearray(valid); bad[i] ^= 1 << bit
                self.assertNotEqual(self.parse('gb_parse_fg19', bytes(bad), Frame)[0], 0)

    def test_control_boundaries_valid_crc(self):
        fmt = struct.Struct('!4sBBHIIQII')
        good = [b'FG19', 1, 1, 0, 1, 10, 1, 49152, 123]
        for offset, value in [(0, b'BAD!'), (1, 2), (2, 0), (2, 9), (3, 2),
                              (3, 65535), (4, 2), (6, 0), (7, 0), (7, 49153)]:
            row = good.copy(); row[offset] = value
            self.assertNotEqual(self.parse('gb_parse_fg19', seal(fmt.pack(*row)), Frame)[0], 0)
        for length in range(36):
            self.assertNotEqual(self.parse('gb_parse_fg19', seal(fmt.pack(*good))[:length], Frame)[0], 0)
        self.assertNotEqual(self.parse('gb_parse_fg19', seal(fmt.pack(*good)) + b'X', Frame)[0], 0)

    def test_actual_gf03_example(self):
        packet = bytes.fromhex(self.contract['packet_example']['wrapped_first_gf03_hex'])
        rc, out = self.parse('gb_parse_data', packet, Data)
        self.assertEqual(rc, 0)
        self.assertEqual(out.token_header_crc, zlib.crc32(packet[:47]))
        self.assertEqual(out.payload_bytes, 1008)
        self.assertEqual(out.index, 0)
        pc = bytes.fromhex(self.contract['packet_example']['pc18_hex'])
        self.assertEqual(out.token_header_crc, struct.unpack_from('!I', pc, 21)[0])

    def test_fragment_geometry_and_legal_extremes(self):
        for total in (1, 1007, 1008, 1009, 49151, 49152):
            count = (total + 1007) // 1008
            for index in range(count):
                size = min(1008, total - index * 1008)
                p = struct.pack('!IHHQ4sBIIIHHHII', 1, 5, 0, (1 << 64) - 1,
                                b'GF03', 3, 1, 12, total, index, count, size, 100, 200) + bytes(size)
                rc, out = self.parse('gb_parse_data', p, Data)
                self.assertEqual(rc, 0)
                self.assertEqual(out.payload_bytes, size)
                f = Frame(epoch=1, frame=12, total=total, body_crc=200, nonce=7, slot=0, kind=3)
                self.assertEqual(self.lib.gb_route_matches(C.byref(f), C.byref(out)), 1)
                for field in ('epoch', 'frame', 'total', 'body_crc', 'kind', 'slot'):
                    bad = Frame.from_buffer_copy(f)
                    setattr(bad, field, 2 if field == 'slot' else getattr(bad, field) + 1)
                    self.assertEqual(self.lib.gb_route_matches(C.byref(bad), C.byref(out)), 0)

    def test_bad_gf03_headers(self):
        original = bytes.fromhex(self.contract['packet_example']['wrapped_first_gf03_hex'])
        for offset, fmt, value in [(0, '!I', 2), (4, '!H', 6), (6, '!H', 1),
                                   (8, '!Q', 0), (20, '!B', 2), (21, '!I', 2),
                                   (25, '!I', 0xffffffff), (29, '!I', 0),
                                   (29, '!I', 49153), (33, '!H', 65535),
                                   (35, '!H', 0), (37, '!H', 0)]:
            bad = bytearray(original); struct.pack_into(fmt, bad, offset, value)
            self.assertNotEqual(self.parse('gb_parse_data', bytes(bad), Data)[0], 0)
        for size in range(len(original)):
            self.assertNotEqual(self.parse('gb_parse_data', original[:size], Data)[0], 0)
        self.assertNotEqual(self.parse('gb_parse_data', original + b'x', Data)[0], 0)

    def test_null_pointers(self):
        for func, cls in [('gb_parse_fg19', Frame), ('gb_parse_data', Data)]:
            out = cls()
            self.assertEqual(getattr(self.lib, func)(None, 36, 1, C.byref(out)), -1)
            self.assertEqual(getattr(self.lib, func)(b'x', 1, 1, None), -1)
        self.assertEqual(self.lib.gb_route_matches(None, None), 0)

    def test_writer_rejections_leave_output_unchanged(self):
        valid = Frame(epoch=1, frame=12, total=10, body_crc=42, nonce=1, slot=0, kind=3)
        buf = C.create_string_buffer(bytes([0xa5]) * 40)
        before = buf.raw
        for size in range(36):
            self.assertEqual(self.lib.gb_write_fg19(C.byref(valid), buf, size), -1)
            self.assertEqual(buf.raw, before)
        for field, value in [('total', 0), ('total', 49153), ('nonce', 0), ('kind', 0), ('slot', 2)]:
            invalid = Frame.from_buffer_copy(valid)
            setattr(invalid, field, value)
            self.assertEqual(self.lib.gb_write_fg19(C.byref(invalid), buf, 40), -1)
            self.assertEqual(buf.raw, before)
        self.assertEqual(self.lib.gb_write_fg19(None, buf, 40), -1)
        self.assertEqual(self.lib.gb_write_fg19(C.byref(valid), None, 40), -1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    args = p.parse_args()
    contract_path = args.source / 'hardware/gamebub-v20/wire-contract.json'
    Tests.contract = json.loads(contract_path.read_text())
    with tempfile.TemporaryDirectory(prefix='ar03-gateway-') as tmp:
        library = Path(tmp) / 'gateway.so'
        command = ['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                   '-fsanitize=undefined', '-fno-sanitize-recover=all', str(HERE / 'gb_gateway.c'), '-o', str(library)]
        subprocess.run(command, check=True)
        Tests.lib = C.CDLL(str(library))
        for name in ('gb_parse_fg19', 'gb_parse_data'):
            getattr(Tests.lib, name).argtypes = [C.c_void_p, C.c_size_t, C.c_uint32, C.c_void_p]
            getattr(Tests.lib, name).restype = C.c_int
        Tests.lib.gb_route_matches.argtypes = [C.c_void_p, C.c_void_p]
        Tests.lib.gb_route_matches.restype = C.c_int
        Tests.lib.gb_write_fg19.argtypes = [C.c_void_p, C.c_void_p, C.c_size_t]
        Tests.lib.gb_write_fg19.restype = C.c_int
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        output = dict(passed=result.wasSuccessful(), tests=result.testsRun, failures=len(result.failures),
                      errors=len(result.errors), retained_fg19_messages=1725, command=command,
                      compiler=subprocess.check_output(['gcc', '--version'], text=True).splitlines()[0],
                      wire_contract_sha256=hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                      source_sha256={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                     for name in ('gb_gateway.c', 'gb_gateway.h', 'test_gateway.py')},
                      scope='Linux host C UBSan replay; no ESP32 performance, ownership ledger or hardware qualification')
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(json.dumps(output, indent=2) + '\n')
        raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
