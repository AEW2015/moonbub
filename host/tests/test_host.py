import io
import sys
from pathlib import Path
import struct
import unittest
import zlib
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moonshine.encoding import encode, letterbox, validate_jpeg
from moonshine.protocol import VIDEO, FEEDBACK, MAX_FRAME, packets, parse_packet, parse_feedback, Reassembler
from moonshine.sender import budgeted_encode, LatestFrames


class EncodingTests(unittest.TestCase):
    def test_letterbox_16_by_9_preserves_geometry(self):
        image = letterbox(Image.new("RGB", (1280, 720), (255, 0, 0)))
        self.assertEqual(image.size, (720, 480))
        for y in (0, 36, 442, 479):
            self.assertEqual(image.getpixel((360, y)), (0, 0, 0))
        for y in (37, 441):
            self.assertEqual(image.getpixel((360, y)), (255, 0, 0))

    def test_portrait_preserves_aspect(self):
        image = letterbox(Image.new("RGB", (100, 200), (0, 255, 0)))
        self.assertEqual(image.getpixel((239, 240)), (0, 0, 0))
        self.assertEqual(image.getpixel((240, 240)), (0, 255, 0))
        self.assertEqual(image.getpixel((479, 240)), (0, 255, 0))
        self.assertEqual(image.getpixel((480, 240)), (0, 0, 0))

    def test_actual_jpeg_matches_fixed_table_profile_and_decodes(self):
        jpeg = encode(Image.new("RGB", (1280, 720), (20, 100, 220)))
        validate_jpeg(jpeg)
        self.assertEqual(Image.open(io.BytesIO(jpeg)).size, (720, 480))

    def test_reject_progressive(self):
        output = io.BytesIO()
        Image.new("RGB", (720, 480)).save(output, "JPEG", progressive=True)
        with self.assertRaises(ValueError):
            validate_jpeg(output.getvalue())

    def test_reject_422(self):
        output = io.BytesIO()
        Image.new("RGB", (720, 480)).save(output, "JPEG", subsampling=1)
        with self.assertRaises(ValueError):
            validate_jpeg(output.getvalue())

    def test_reject_optimized_huffman(self):
        output = io.BytesIO()
        Image.new("RGB", (720, 480)).save(output, "JPEG", optimize=True)
        with self.assertRaises(ValueError):
            validate_jpeg(output.getvalue())

    def test_reject_restart_interval_even_zero(self):
        jpeg = encode(Image.new("RGB", (720, 480)))
        with self.assertRaises(ValueError):
            validate_jpeg(jpeg[:2] + b"\xff\xdd\x00\x04\x00\x00" + jpeg[2:])

    def test_reject_truncated_and_wrong_dimensions(self):
        jpeg = encode(Image.new("RGB", (720, 480)))
        with self.assertRaises(ValueError):
            validate_jpeg(jpeg[:-2])
        with self.assertRaises(ValueError):
            validate_jpeg(jpeg, expected=(800, 480))

    def test_reject_quantizer_precision_and_scan_mapping(self):
        jpeg = bytearray(encode(Image.new("RGB", (720, 480))))
        dqt = jpeg.index(b"\xff\xdb")
        jpeg[dqt + 4] = 0x10
        with self.assertRaises(ValueError):
            validate_jpeg(jpeg)
        jpeg = bytearray(encode(Image.new("RGB", (720, 480))))
        sos = jpeg.index(b"\xff\xda")
        jpeg[sos + 6] = 0x11
        with self.assertRaises(ValueError):
            validate_jpeg(jpeg)

    def test_budget_drops_impossible_frame(self):
        jpeg, q = budgeted_encode(Image.new("RGB", (720, 480)), 15, 100)
        self.assertIsNone(jpeg)
        self.assertEqual(q, 15)

    def test_capture_latest_frame_replaces_instead_of_queueing(self):
        latest = LatestFrames()
        latest.put(Image.new("RGB", (1, 1), "red"))
        latest.put(Image.new("RGB", (1, 1), "blue"))
        self.assertEqual(latest.queue.qsize(), 1)
        self.assertEqual(latest.queue.get_nowait()[1].getpixel((0, 0)), (0, 0, 255))
        self.assertEqual(latest.replaced, 1)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.jpeg = encode(Image.new("RGB", (720, 480), (0, 255, 0)))
        self.parts = list(packets(self.jpeg, 42, 12345))

    def test_wire_header_and_fragment_roundtrip(self):
        self.assertEqual(VIDEO.size, 40)
        self.assertEqual(FEEDBACK.size, 32)
        sink = Reassembler()
        result = None
        for chunk in self.parts:
            self.assertLessEqual(len(chunk), 1064)
            result = sink.accept(chunk)
        self.assertEqual(result[1], self.jpeg)
        self.assertEqual(result[0].frame_id, 42)
        self.assertEqual(result[0].capture_us, 12345)

    def test_actual_cross_language_fixture(self):
        path = Path(__file__).resolve().parents[1] / "fixtures" / "pattern-msv1-packets.bin"
        data = path.read_bytes()
        sink = Reassembler()
        result = None
        while data:
            length = int.from_bytes(data[:2], "big")
            result = sink.accept(data[2:2 + length])
            data = data[2 + length:]
        self.assertEqual(result[0].frame_id, 0x12345678)
        self.assertEqual(result[0].capture_us, 1234567890123)
        self.assertEqual(result[1], (path.parent / "pattern-720x480-420-q65.jpg").read_bytes())

    def test_corrupt_packet_crc_and_recover_new_frame(self):
        sink = Reassembler()
        for chunk in self.parts[:-1]:
            sink.accept(chunk)
        broken = bytearray(self.parts[-1])
        broken[-1] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            sink.accept(broken)
        for chunk in packets(self.jpeg, 43, 12346):
            result = sink.accept(chunk)
        self.assertEqual(result[1], self.jpeg)

    def test_gap_duplicate_reorder_discard_then_recover(self):
        for bad_index in (0, 2):
            sink = Reassembler()
            sink.accept(self.parts[0])
            with self.assertRaises(ValueError):
                sink.accept(self.parts[bad_index])
            for chunk in packets(self.jpeg, 43, 12346):
                result = sink.accept(chunk)
            self.assertEqual(result[1], self.jpeg)

    def test_new_frame_supersedes_incomplete(self):
        sink = Reassembler()
        sink.accept(self.parts[0])
        for chunk in packets(self.jpeg, 43, 12346):
            result = sink.accept(chunk)
        self.assertEqual(result[1], self.jpeg)
        self.assertEqual(sink.dropped, 1)

    def test_stale_frame_ids_rejected_and_wrapping_accepted(self):
        sink = Reassembler()
        for fid in (0xfffffffe, 0xffffffff, 0, 1):
            for chunk in packets(self.jpeg, fid, 12346):
                result = sink.accept(chunk)
            self.assertEqual(result[0].frame_id, fid)
        with self.assertRaisesRegex(ValueError, "stale"):
            sink.accept(next(packets(self.jpeg, 0xffffffff, 12346)))
        sink.reset()
        for chunk in packets(self.jpeg, 0, 12346):
            result = sink.accept(chunk)
        self.assertEqual(result[0].frame_id, 0)

    def test_header_mutations_rejected(self):
        # Version, codec, flags, width, height, frame length, offset, payload,
        # reserved, and boundary mutations exercise each untrusted field.
        fields = list(VIDEO.unpack_from(self.parts[0]))
        for index, value in ((0, b"BAD!"), (1, 2), (2, 4), (3, 8), (5, 800), (6, 800),
                             (7, 0), (7, MAX_FRAME + 1), (8, MAX_FRAME), (9, 0), (9, 1025), (10, 1)):
            bad = fields.copy()
            bad[index] = value
            with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                parse_packet(VIDEO.pack(*bad) + self.parts[0][40:])
        with self.assertRaises(ValueError):
            parse_packet(self.parts[0][:-1])

    def test_payload_limits(self):
        for blob in (b"", b"a" * (MAX_FRAME + 1)):
            with self.assertRaises(ValueError):
                list(packets(blob, 0, 0))
        with self.assertRaises(ValueError):
            list(packets(b"a", 0, 0, 1025))

    def test_feedback_roundtrip_and_reject(self):
        wire = FEEDBACK.pack(b"MSF1", 1, 0, 0x90, 42, 2048, 10, 2, 12345)
        result = parse_feedback(wire)
        self.assertEqual((result.buttons, result.frame_id, result.capture_us), (0x90, 42, 12345))
        with self.assertRaises(ValueError):
            parse_feedback(wire[:-1])
        with self.assertRaises(ValueError):
            parse_feedback(FEEDBACK.pack(b"MSF1", 1, 4, 0, 0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
