"""@brief Contract and state-machine tests for the experimental AV wire protocol."""

import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path

from av_protocol import HEADER, INPUT, InputLease, Packet, decode, newer

HERE = Path(__file__).resolve().parent
GOLDENS = HERE / "fixtures" / "av-v1"


def _recrc(raw):
    raw = bytearray(raw)
    raw[40:44] = b"\0" * 4
    raw[40:44] = struct.pack("!I", zlib.crc32(raw) & 0xFFFFFFFF)
    return bytes(raw)


def _input(session, seq, buttons=0, state=1):
    payload = INPUT.pack(buttons, 10, 1, 120, 240, 2, state, 0x4D424F50)
    return Packet(b"MSI1", 1, session, seq=seq, payload=payload).encode()


class FakeDispatcher:
    """@brief Record logical masks without loading or touching a gamepad driver."""

    def __init__(self):
        self.applied = []
        self.neutral_count = 0
        self.closed = False

    def apply(self, mask):
        self.applied.append(mask)

    def neutral(self):
        self.neutral_count += 1

    def close(self):
        self.closed = True


class GoldenPacketTests(unittest.TestCase):
    """@brief Match independent frozen bytes and hashes for every v1 packet class."""

    def test_all_seven_packet_vectors_roundtrip_byte_for_byte(self):
        manifest = json.loads((GOLDENS / "vectors.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["vectors"]), 7)
        for name, vector in manifest["vectors"].items():
            with self.subTest(name=name):
                wire = bytes.fromhex(vector["hex"])
                self.assertEqual(hashlib.sha256(wire).hexdigest(), vector["sha256"])
                packet = decode(wire)
                self.assertEqual(packet.encode(), wire)
                self.assertEqual(len(wire), HEADER.size + len(packet.payload))

    def test_bad_lengths_crc_and_contract_fields_reject(self):
        baseline = bytes.fromhex(
            json.loads((GOLDENS / "vectors.json").read_text(encoding="utf-8"))["vectors"]["hello"]["hex"]
        )
        for label, candidate in (
            ("short", baseline[:-1]),
            ("trailing", baseline + b"x"),
            ("crc", baseline[:40] + bytes((baseline[40] ^ 1,)) + baseline[41:]),
        ):
            with self.subTest(label=label), self.assertRaises(ValueError):
                decode(candidate)

        bad_fields = (
            ("magic", 0, b"NOPE"),
            ("version", 4, b"\x02"),
            ("type", 5, b"\x05"),
            ("header_size", 6, b"\x001"),
            ("rate", 20, struct.pack("!I", 48000)),
            ("sample_count", 24, struct.pack("!H", 505)),
            ("payload_length", 26, struct.pack("!H", 1)),
            ("flags", 28, struct.pack("!I", 2)),
            ("reserved", 44, struct.pack("!I", 1)),
        )
        for label, offset, replacement in bad_fields:
            candidate = bytearray(baseline)
            candidate[offset : offset + len(replacement)] = replacement
            with self.subTest(label=label), self.assertRaises(ValueError):
                decode(_recrc(candidate))

    def test_audio_header_and_reserved_fields_are_checked_after_crc(self):
        manifest = json.loads((GOLDENS / "vectors.json").read_text(encoding="utf-8"))
        baseline = bytes.fromhex(manifest["vectors"]["audio"]["hex"])
        for label, offset, value in (
            ("left index", HEADER.size + 2, b"\x59"),
            ("left reserved", HEADER.size + 3, b"\x01"),
            ("right index", HEADER.size + 6, b"\x59"),
            ("right reserved", HEADER.size + 7, b"\x01"),
        ):
            candidate = bytearray(baseline)
            candidate[offset : offset + len(value)] = value
            with self.subTest(label=label), self.assertRaises(ValueError):
                decode(_recrc(candidate))

    def test_input_button_and_state_reserved_bits_are_rejected(self):
        baseline = bytearray(_input(0x1234, 1))
        for label, offset, value in (
            ("button", HEADER.size, struct.pack("!I", 1 << 12)),
            ("state", HEADER.size + 24, struct.pack("!I", 8)),
        ):
            candidate = bytearray(baseline)
            candidate[offset : offset + len(value)] = value
            with self.subTest(label=label), self.assertRaises(ValueError):
                decode(_recrc(candidate))


class SequenceAndInputLeaseTests(unittest.TestCase):
    """@brief Verify serial wrap, source/session binding, stale rejection and expiry."""

    def test_wrapping_sequence_order(self):
        self.assertTrue(newer(0, 0xFFFFFFFF))
        self.assertFalse(newer(0xFFFFFFFF, 0))
        self.assertFalse(newer(7, 7))
        self.assertFalse(newer(0x80000000, 0))
        self.assertTrue(newer(1, None))

    def test_duplicate_stale_wrong_source_and_wrong_cookie_do_not_refresh(self):
        peer = ("127.0.0.1", 5534)
        dispatcher = FakeDispatcher()
        lease = InputLease(0x1234, peer, dispatcher)
        first = _input(0x1234, 0, buttons=1 << 11)
        self.assertTrue(lease.accept(first, peer, 1_000_000))
        self.assertEqual(dispatcher.applied, [1 << 11])
        self.assertFalse(lease.accept(first, peer, 100_000_000))
        self.assertFalse(lease.accept(_input(0x1234, 0xFFFFFFFF, 0), peer, 120_000_000))
        self.assertFalse(lease.accept(_input(0x9999, 1, 0), peer, 130_000_000))
        self.assertFalse(lease.accept(_input(0x1234, 1, 0), ("127.0.0.2", 5534), 140_000_000))
        self.assertEqual(lease.last_ns, 1_000_000)
        self.assertEqual(dispatcher.applied, [1 << 11])
        self.assertFalse(lease.expire(500_999_999))
        self.assertTrue(lease.expire(501_000_000))
        self.assertEqual(dispatcher.neutral_count, 1)

    def test_new_sequence_recovers_after_timeout_and_inactive_never_refreshes(self):
        peer = ("127.0.0.1", 5534)
        dispatcher = FakeDispatcher()
        lease = InputLease(0x1234, peer, dispatcher)
        self.assertTrue(lease.accept(_input(0x1234, 10, 1), peer, 100))
        self.assertFalse(lease.accept(_input(0x1234, 11, 2, state=0), peer, 200))
        self.assertEqual(lease.last_ns, 100)
        self.assertTrue(lease.expire(100 + 500_000_000))
        self.assertFalse(lease.accept(_input(0x1234, 10, 3), peer, 500_000_101))
        self.assertTrue(lease.accept(_input(0x1234, 11, 4), peer, 500_000_102))
        self.assertEqual(dispatcher.applied, [1, 4])
        self.assertEqual(dispatcher.neutral_count, 1)

    def test_bad_crc_does_not_refresh_or_apply_and_close_detaches(self):
        peer = ("127.0.0.1", 5534)
        dispatcher = FakeDispatcher()
        lease = InputLease(0x1234, peer, dispatcher)
        good = _input(0x1234, 1, 2)
        self.assertTrue(lease.accept(good, peer, 1_000))
        corrupted = good[:40] + bytes((good[40] ^ 1,)) + good[41:]
        with self.assertRaisesRegex(ValueError, "CRC"):
            lease.accept(corrupted, peer, 400_000_000)
        self.assertEqual(lease.last_ns, 1_000)
        self.assertEqual(dispatcher.applied, [2])
        lease.close()
        self.assertTrue(dispatcher.closed)

    def test_backwards_clock_is_rejected_after_first_valid_input(self):
        lease = InputLease(0x1234, ("127.0.0.1", 5534))
        self.assertTrue(lease.accept(_input(0x1234, 1), lease.peer, 100))
        with self.assertRaisesRegex(ValueError, "backward"):
            lease.accept(_input(0x1234, 2), lease.peer, 99)


if __name__ == "__main__":
    unittest.main()
