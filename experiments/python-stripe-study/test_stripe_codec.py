import hashlib
import struct
import unittest
import zlib

import numpy as np

import stripe_codec as sc


class StripeCodecTests(unittest.TestCase):
    def test_exact_goldens_edge_geometry_and_feed_boundaries(self):
        rng = np.random.default_rng(20261103)
        for h, w in ((2, 2), (18, 34), (34, 18), (48, 64)):
            rgb = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
            packet = sc.encode(rgb, 16)
            golden = sc.ft.reconstruct(rgb, 16)
            for size in (1, 3, 17, 1024, len(packet)):
                self.assertTrue(np.array_equal(sc.decode(packet, size), golden), (h, w, size))

    def test_no_commit_until_explicit_complete_finish(self):
        image = np.zeros((32, 32, 3), np.uint8)
        packet = sc.encode(image)
        emitted, events = [], []
        decoder = sc.Decoder(lambda row, rgb: emitted.append((row, hashlib.sha256(rgb).hexdigest())))
        events.extend(decoder.feed(packet[:-4]))
        self.assertTrue(emitted)
        self.assertFalse(decoder.committed)
        with self.assertRaises(ValueError):
            decoder.finish()
        self.assertFalse(decoder.committed)
        decoder.reset()
        events = decoder.feed(packet)
        self.assertEqual(events[-1]['kind'], 'frame_validated')
        self.assertFalse(decoder.committed)
        self.assertTrue(decoder.finish()['committed'])

    def test_late_frame_crc_failure_never_commits_provisional_pixels(self):
        image = np.zeros((48, 64, 3), np.uint8)
        packet = bytearray(sc.encode(image))
        packet[-1] ^= 1
        rows = []
        decoder = sc.Decoder(lambda row, rgb: rows.append(row))
        with self.assertRaisesRegex(ValueError, 'frame CRC'):
            decoder.feed(packet)
        self.assertEqual(rows, [0, 16, 32])
        self.assertFalse(decoder.committed)
        self.assertEqual(len(decoder.buffer), 0)
        with self.assertRaises(ValueError):
            decoder.feed(b'x')

    def test_region_order_length_crc_and_global_bound_fail_early(self):
        image = np.zeros((32, 32, 3), np.uint8)
        packet = sc.encode(image)
        # Wrong first plane is rejected from its header before payload buffering.
        bad = bytearray(packet[:sc.HEADER.size+sc.REGION.size])
        bad[sc.HEADER.size+2] = 0
        decoder = sc.Decoder()
        with self.assertRaisesRegex(ValueError, 'order'):
            decoder.feed(bad)
        self.assertEqual(decoder.metrics['peak_staged_bytes'], sc.HEADER.size)
        bad = bytearray(packet[:sc.HEADER.size+sc.REGION.size])
        struct.pack_into('<I', bad, sc.HEADER.size+sc.REGION.size-4, 0xffffffff)
        with self.assertRaisesRegex(ValueError, 'bound'):
            sc.Decoder().feed(bad)
        bad = bytearray(packet)
        bad[sc.HEADER.size+sc.REGION.size] ^= 1
        with self.assertRaisesRegex(ValueError, 'region CRC'):
            sc.Decoder().feed(bad)
        fields = list(sc.HEADER.unpack_from(packet)); fields[-1] = 0xffffffff
        with self.assertRaisesRegex(ValueError, 'payload bound'):
            sc.Decoder().feed(sc.HEADER.pack(*fields))

    def test_full_size_resident_payload_bounds(self):
        yy, xx = np.mgrid[:480, :720]
        rgb = np.stack((xx%256, yy%256, (xx+yy)%256), axis=-1).astype(np.uint8)
        packet = sc.encode(rgb)
        decoder = sc.Decoder()
        for start in range(0, len(packet), 137):
            decoder.feed(packet[start:start+137])
        stats = decoder.finish()
        self.assertEqual(stats['peak_retained_sample_bytes'], 23040)
        self.assertEqual(stats['peak_coefficient_array_bytes'], 23040)
        self.assertEqual(stats['peak_idct_int64_input_bytes'], 92160)
        self.assertLessEqual(stats['peak_staged_bytes'], 23040+sc.CP_OVERHEAD+4)
        self.assertEqual(stats['validated_regions'], 90)
        self.assertFalse(decoder.chroma)
        self.assertIsNone(decoder.pending_y)

    def test_duplicate_region_and_trailing_bytes_and_reset(self):
        image = np.zeros((32, 32, 3), np.uint8)
        packet = sc.encode(image)
        at = sc.HEADER.size
        size = sc.REGION.unpack_from(packet, at)[-1]
        first = packet[at:at+sc.REGION.size+size+4]
        decoder = sc.Decoder()
        with self.assertRaisesRegex(ValueError, 'order'):
            decoder.feed(packet[:at]+first+first)
        decoder.reset()
        decoder.feed(packet)
        with self.assertRaisesRegex(ValueError, 'trailing'):
            decoder.feed(b'x')
        self.assertFalse(decoder.committed)
        decoder.reset()
        decoder.feed(packet)
        self.assertTrue(decoder.finish()['committed'])

    def test_exact_complete_callback_coverage_and_unpublished_partial_reset(self):
        rgb = np.random.default_rng(3).integers(0, 256, (34, 18, 3), dtype=np.uint8)
        packet = sc.encode(rgb, 8)
        out = np.zeros_like(rgb)
        seen = []
        def put(row, image):
            seen.append((row, len(image)))
            out[row:row+len(image)] = image
        decoder = sc.Decoder(put)
        decoder.feed(packet[:-4]); decoder.reset()
        seen.clear()
        decoder.feed(packet); decoder.finish()
        self.assertEqual(seen, [(0, 16), (16, 16), (32, 2)])
        self.assertTrue(np.array_equal(out, sc.ft.reconstruct(rgb, 8)))


if __name__ == '__main__':
    unittest.main()
