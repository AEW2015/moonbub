import struct
import unittest
import zlib

from hud_control import (ABORT, ACK_EXTERNAL_WRITE_DRAIN, COMMIT, HEADER,
                        MAGIC_REQUEST, MAGIC_RESPONSE, MAX_PAYLOAD, PREPARE,
                        READ_CANDIDATE, RESET, STATUS, Message, ProtocolError,
                        StreamDecoder, decode, encode)


def req(opcode, payload=b'', generation=0x0102030405060708, argument=0x99aabbcc):
    return Message(MAGIC_REQUEST, opcode, generation, 0x11223344,
                   0x55667788, argument, payload)


class CodecTests(unittest.TestCase):
    def test_all_seven_commands_roundtrip(self):
        messages = [req(PREPARE, b'original-hu'), req(STATUS),
                    req(READ_CANDIDATE, struct.pack('<II', 12, 5)),
                    req(ACK_EXTERNAL_WRITE_DRAIN, struct.pack('<I', 5) + bytes(range(16))),
                    req(COMMIT), req(ABORT), req(RESET, argument=1)]
        for message in messages:
            with self.subTest(opcode=message.opcode):
                self.assertEqual(decode(encode(message)), message)

    def test_exact_little_endian_header_layout(self):
        wire = encode(req(COMMIT))
        self.assertEqual(len(wire), 36)
        self.assertEqual(wire[:4], b'HC70')
        self.assertEqual(wire[4:8], bytes((1, COMMIT, 0, 0)))
        self.assertEqual(wire[8:12], b'\0\0\0\0')
        self.assertEqual(wire[12:20], bytes.fromhex('0807060504030201'))
        self.assertEqual(wire[20:32], bytes.fromhex('4433221188776655ccbbaa99'))
        self.assertEqual(HEADER.size, 32)
        self.assertEqual(struct.unpack('<I', wire[-4:])[0], zlib.crc32(wire[:HEADER.size]))

    def test_response_magic_roundtrip(self):
        response = Message(MAGIC_RESPONSE, READ_CANDIDATE, 4, 8, 12, 200, b'pixels')
        self.assertEqual(decode(encode(response)), response)

    def test_maximum_payload_and_oversize(self):
        message = req(PREPARE, b'p' * MAX_PAYLOAD)
        self.assertEqual(decode(encode(message)), message)
        with self.assertRaisesRegex(ProtocolError, 'exceeds'):
            encode(req(PREPARE, b'p' * (MAX_PAYLOAD + 1)))
        raw = bytearray(encode(req(COMMIT)))
        raw[8:12] = struct.pack('<I', MAX_PAYLOAD + 1)
        with self.assertRaisesRegex(ProtocolError, 'exceeds'):
            decode(raw)

    def test_fragmented_stream_and_multiple_frames(self):
        a = encode(req(STATUS, generation=9))
        b = encode(req(READ_CANDIDATE, struct.pack('<II', 0x01020304, 0x05060708), generation=10))
        decoder = StreamDecoder()
        self.assertEqual(decoder.feed(a[:3]), [])
        self.assertEqual(decoder.feed(a[3:17]), [])
        self.assertEqual(decoder.feed(a[17:] + b[:11]), [decode(a)])
        self.assertEqual(decoder.feed(b[11:]), [decode(b)])
        decoder.finish()
        self.assertEqual(decoder.buffered_bytes, 0)

    def test_truncation_and_exact_length(self):
        wire = encode(req(PREPARE, b'payload'))
        with self.assertRaisesRegex(ProtocolError, 'truncated'):
            decode(wire[:-1])
        with self.assertRaisesRegex(ProtocolError, 'trailing'):
            decode(wire + b'\0')
        decoder = StreamDecoder()
        self.assertEqual(decoder.feed(wire[:-1]), [])
        with self.assertRaisesRegex(ProtocolError, 'EOF'):
            decoder.finish()

    def test_reject_bad_magic_version_opcode_reserved_length_crc(self):
        cases = []
        wire = bytearray(encode(req(COMMIT)))
        wire[0:4] = b'NOPE'
        cases.append(wire)
        wire = bytearray(encode(req(COMMIT)))
        wire[4] = 2
        cases.append(wire)
        wire = bytearray(encode(req(COMMIT)))
        wire[5] = 8
        cases.append(wire)
        wire = bytearray(encode(req(COMMIT)))
        wire[6:8] = b'\1\0'
        cases.append(wire)
        wire = bytearray(encode(req(PREPARE, b'abc')))
        wire[12] ^= 1
        cases.append(wire)
        wire = bytearray(encode(req(PREPARE, b'abc')))
        wire[HEADER.size] ^= 1
        cases.append(wire)
        for wire in cases:
            with self.subTest(wire=wire[:8]):
                with self.assertRaises(ProtocolError):
                    decode(wire)

    def test_header_generation_and_opcode_are_crc_protected(self):
        wire = encode(req(COMMIT))
        for offset, mask in ((12, 1), (5, 1)):
            changed = bytearray(wire)
            changed[offset] ^= mask
            with self.subTest(offset=offset):
                with self.assertRaisesRegex(ProtocolError, 'CRC32'):
                    decode(changed)

    def test_payload_contracts_and_integer_bounds(self):
        for opcode, payload in ((READ_CANDIDATE, b'1234'),
                                (ACK_EXTERNAL_WRITE_DRAIN, b'x' * 19),
                                (COMMIT, b'x'), (ABORT, b'x'),
                                (STATUS, b'x'), (RESET, b'x')):
            with self.subTest(opcode=opcode):
                with self.assertRaises(ProtocolError):
                    encode(req(opcode, payload))
        with self.assertRaisesRegex(ProtocolError, 'u64'):
            encode(req(STATUS, generation=1 << 64))
        with self.assertRaisesRegex(ProtocolError, 'quiescence'):
            encode(req(RESET, argument=0))

    def test_codec_preserves_stale_generation_for_endpoint_policy(self):
        stale = req(STATUS, generation=2)
        self.assertEqual(decode(encode(stale)).generation, 2)

    def test_stream_rejects_and_clears_bad_frame(self):
        decoder = StreamDecoder()
        bad = bytearray(encode(req(STATUS)))
        bad[5] = 0
        with self.assertRaises(ProtocolError):
            decoder.feed(bad)
        self.assertEqual(decoder.buffered_bytes, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
