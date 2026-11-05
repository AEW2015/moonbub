"""Focused independent framing/publication/support regression tests."""
import struct
import unittest
import zlib

import numpy as np

import verify as v


def seal(body):
    return body+struct.pack('<I', zlib.crc32(body))


class IndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = v.HERE.parent/'python-game-controller-v35-study'
        data = v.frozen.load(folder/'results.json')
        row = next(c for c in data['cases'] if c['policy'] == 'control')['rows'][0]
        pair = v.frozen.raw(row['packet'], folder)
        parsed = v.frozen.p.parse_pair(pair)
        planes, _ = v.m.decode(parsed['base'], expected_epoch=25)
        tag = v.m.C.reference_tag(v.normalize(planes))
        cls.packet = seal(v.HEADER.pack(b'CN36', 1, 1, 25, 0, v.m.NO_REF,
                                       720, 480, v.PROFILE, bytes(16), tag,
                                       len(parsed['base']), len(parsed['hud']))
                          + parsed['base']+parsed['hud'])

    def mutate(self, index, value):
        fields = list(v.HEADER.unpack_from(self.packet))
        fields[index] = value
        return seal(v.HEADER.pack(*fields)+self.packet[v.HEADER.size:-4])

    def test_fixed_geometry_scalar_support_and_exact_visible_normalization(self):
        self.assertEqual([int(a.sum()) for a in v.safe_blocks()], [256, 19, 19])
        rng = np.random.default_rng(36)
        planes = tuple(rng.integers(0, 256, shape, dtype=np.int16)
                       for shape in ((480, 720), (240, 360), (240, 360)))
        out = v.normalize(planes)
        covered = np.zeros((480, 720), bool)
        for x, y, w, h in v.n.RECTS:
            covered[y:y+h, x:x+w] = True
        np.testing.assert_array_equal(v.m.ft.planes_to_rgb(planes)[~covered],
                                      v.m.ft.planes_to_rgb(out)[~covered])
        for a, b in zip(planes, out):
            self.assertFalse(np.shares_memory(a, b))

    def test_real_frozen_key_payload_normalized_publication_and_replay_rejection(self):
        rx = v.Receiver()
        planes, patches, meta = rx.receive(self.packet)
        self.assertEqual(v.m.C.reference_tag(planes), meta['output_tag'])
        self.assertEqual(sum(p['words'].size for p in patches), 21120)
        self.assertEqual(rx.last_id, 0)
        with self.assertRaises(ValueError):
            rx.receive(self.packet)

    def test_crc_truncation_trailing_and_bounded_type_fail(self):
        for bad in (bytearray(self.packet), self.packet[:-1], self.packet+b'\0',
                    self.packet[:-1]+bytes([self.packet[-1]^1]), bytes(49153)):
            with self.assertRaises(ValueError):
                v.parse(bad)

    def test_resealed_profile_identity_and_length_corruption_fail(self):
        for index, value in ((0, b'CP34'), (1, 2), (2, 4), (3, 36), (4, 1),
                             (5, 0), (6, 718), (8, bytes(16)),
                             (9, bytes([1])*16), (11, 1), (12, 1)):
            with self.subTest(index=index), self.assertRaises(ValueError):
                v.parse(self.mutate(index, value))

    def test_wrong_normalized_output_tag_cannot_publish(self):
        rx = v.Receiver()
        with self.assertRaises(ValueError):
            rx.receive(self.mutate(10, bytes([1])*16))
        self.assertIsNone(rx.reference)
        self.assertIsNone(rx.patches)
        self.assertEqual(rx.last_id, -1)


if __name__ == '__main__':
    unittest.main()
