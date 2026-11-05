import hashlib
import struct
import unittest

import numpy as np
import model

SHAPES = ((480, 720), (240, 360), (240, 360))


def fixture_planes():
    # Independent deterministic full-frame data with different plane patterns.
    out = []
    for p, shape in enumerate(SHAPES):
        y, x = np.indices(shape, dtype=np.uint16)
        out.append(((x * 13 + y * 7 + p * 53 + (x ^ y)) & 255).astype(np.uint8))
    return out


def oracle(planes, domain):
    h = hashlib.sha256(struct.pack('<HH', 720, 480))
    for plane in planes:
        if domain == 'CS66_i16':
            h.update(plane.astype('<i2').tobytes())
        else:
            h.update(plane.tobytes())
    return h.digest()[:16]


class FullOracle(unittest.TestCase):
    def test_tile_stream_matches_full_plane_hashlib_both_domains(self):
        planes = fixture_planes()
        for domain in model.DOMAINS:
            subject = model.TileHash(domain)
            for p, plane in enumerate(planes):
                for y in range(0, plane.shape[0], 8):
                    for x in range(0, plane.shape[1], 8):
                        subject.feed(p, y, x, plane[y:y + 8, x:x + 8])
            self.assertEqual(subject.finish(), oracle(planes, domain))
            self.assertEqual(subject.work()['tiles'], 8100)
            self.assertEqual(subject.work()['canonical_samples'], 518400)
            self.assertEqual(subject.work()['rows_serialized'], 960)
            self.assertEqual(subject.work()['maximum_strip_data_bytes'], 5760)

    def test_tile_input_is_copied_and_paused_state_is_stable(self):
        subject = model.TileHash('CU66_u8')
        tile = np.full((8, 8), 37, dtype=np.uint8)
        subject.feed(0, 0, 0, tile)
        before = subject.work().copy()
        retained = subject.strip[:, :8].copy()
        tile[:] = 99
        self.assertEqual(subject.work(), before)
        np.testing.assert_array_equal(subject.strip[:, :8], retained)
        self.assertTrue(np.all(subject.strip[:, :8] == 37))
        self.assertEqual(subject.domain, 'CU66_u8')
        with self.assertRaises(AttributeError):
            subject.domain = 'CS66_i16'


class Poison(unittest.TestCase):
    def test_misorder_and_duplicate_poison_frame(self):
        zero = np.zeros((8, 8), dtype=np.uint8)
        out_of_order = model.TileHash('CU66_u8')
        with self.assertRaises(ValueError):
            out_of_order.feed(0, 0, 8, zero)
        self.assertTrue(out_of_order.failed)
        with self.assertRaises(ValueError):
            out_of_order.feed(0, 0, 0, zero)
        with self.assertRaises(ValueError):
            out_of_order.finish()

        duplicate = model.TileHash('CU66_u8')
        duplicate.feed(0, 0, 0, zero)
        with self.assertRaises(ValueError):
            duplicate.feed(0, 0, 0, zero)
        self.assertTrue(duplicate.failed)
        with self.assertRaises(ValueError):
            duplicate.finish()

    def test_early_finish_poison_and_rejects_later_data(self):
        subject = model.TileHash('CS66_i16')
        with self.assertRaises(ValueError):
            subject.finish()
        self.assertTrue(subject.failed)
        with self.assertRaises(ValueError):
            subject.feed(0, 0, 0, np.zeros((8, 8), dtype=np.uint8))

    def test_only_normalized_u8_tiles_are_accepted(self):
        subject = model.TileHash('CU66_u8')
        for dtype in (np.int16, np.float32):
            with self.subTest(dtype=dtype):
                s = model.TileHash('CU66_u8')
                with self.assertRaises(ValueError):
                    s.feed(0, 0, 0, np.zeros((8, 8), dtype=dtype))
                self.assertTrue(s.failed)


if __name__ == '__main__':
    unittest.main()
