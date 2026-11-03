"""Independent review coverage; does not alter measured implementations."""
import hashlib
import unittest

import numpy as np

from fast_anchor import Encoder, frozen


class FastAnchorReviewTests(unittest.TestCase):
    def image(self, seed, shape=(48, 64, 3)):
        return np.random.default_rng(seed).integers(0, 256, shape, dtype=np.uint8)

    def test_lazy_oracle_survives_other_p_ack_and_retains_named_anchor(self):
        old, new = frozen.AnchorEncoder(window=2), Encoder(window=2)
        key = self.image(1)
        self.assertEqual(old.prepare(key, 0), new.prepare(key, 0))
        old.ack(0, epoch=1)
        new.ack(0, epoch=1)
        anchor = new._anchor
        original = [a.copy() for a in anchor]
        pending = []
        for i in (1, 2):
            rgb = np.roll(key, i * 2, axis=1)
            a = old.prepare(rgb, i, quant_scale=8, mode='global')
            b = new.prepare(rgb, i, quant_scale=8, mode='global')
            self.assertEqual(a, b)
            pending.append((i, b, old.expected_hash(i)))
        with self.assertRaises(ValueError):
            new.prepare(key, 3, force_key=True)
        # Returning the second credit must not invalidate the first lazy oracle.
        self.assertTrue(new.ack(2, epoch=1))
        old.ack(2, epoch=1)
        first = pending[0]
        self.assertEqual(new.expected_hash(first[0]), first[2])
        self.assertEqual(new.expected_hash(first[0]), first[2])
        self.assertIs(new._anchor, anchor)
        for actual, expected in zip(anchor, original):
            self.assertTrue(np.array_equal(actual, expected))
            self.assertFalse(actual.flags.writeable)
        self.assertTrue(new.expire(1))
        old.expire(1)
        self.assertFalse(new.ack(1, epoch=1))
        self.assertEqual(new.anchor_id, 0)
        with self.assertRaises(KeyError):
            new.expected_hash(1)

    def test_global_motion_quantization_geometry_and_key_expiry(self):
        for scale in (1, 8, 128):
            old, new, rx = frozen.AnchorEncoder(), Encoder(), frozen.AnchorReceiver()
            for i, shape in enumerate(((48, 64, 3), (48, 64, 3), (18, 34, 3))):
                rgb = self.image(20 + i, shape)
                a = old.prepare(rgb, i, quant_scale=scale, mode='global')
                b = new.prepare(rgb, i, quant_scale=scale, mode='global')
                self.assertEqual(a, b)
                actual, _ = rx.receive(b)
                expected = hashlib.sha256(actual.tobytes()).hexdigest()
                self.assertEqual(expected, new.expected_hash(i))
                self.assertEqual(expected, old.expected_hash(i))
                old.ack(i, epoch=1)
                new.ack(i, epoch=1)
            replacement = self.image(100, (18, 34, 3))
            self.assertEqual(old.prepare(replacement, 3, force_key=True),
                             new.prepare(replacement, 3, force_key=True))
            old.expire(3)
            new.expire(3)
            self.assertIsNone(new._anchor)
            self.assertEqual(old.prepare(replacement, 4), new.prepare(replacement, 4))


if __name__ == '__main__':
    unittest.main()
