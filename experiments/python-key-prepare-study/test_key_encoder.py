import hashlib
import unittest

import numpy as np

from key_encoder import Encoder, frozen


class KeyEncoderTests(unittest.TestCase):
    def test_key_and_p_packets_match_across_quantizers_and_geometry(self):
        rng = np.random.default_rng(34)
        old, new = frozen.AnchorEncoder(), Encoder()
        receiver = frozen.AnchorReceiver()
        for i, (shape, scale, force, mode) in enumerate([
            ((48, 64), 1, False, 'zero'), ((48, 64), 8, False, 'global'),
            ((48, 64), 128, True, 'global'), ((50, 66), 16, False, 'global'),
            ((50, 66), 32, False, 'zero')]):
            rgb = rng.integers(0, 256, (*shape, 3), dtype=np.uint8)
            options = dict(quant_scale=scale, force_key=force, mode=mode)
            a, b = old.prepare(rgb, i, **options), new.prepare(rgb, i, **options)
            self.assertEqual(a, b)
            self.assertIsNone(new.pending[i]['expected_rgb_sha256'])
            actual, _ = receiver.receive(b)
            expected = hashlib.sha256(actual.tobytes()).hexdigest()
            self.assertEqual(new.expected_hash(i), expected)
            self.assertEqual(old.expected_hash(i), expected)
            new.ack(i, epoch=1)
            old.ack(i, epoch=1)
            for a, b in zip(old._anchor, new._anchor):
                np.testing.assert_array_equal(a, b)
                self.assertFalse(b.flags.writeable)

    def test_anchor_owns_its_memory_and_oracle_is_lazy_pure(self):
        rgb = np.full((24, 32, 3), 25, np.uint8)
        encoder = Encoder()
        encoder.prepare(rgb, 0)
        before = [p.copy() for p in encoder.pending[0]['planes']]
        rgb[:] = 240
        value = encoder.expected_hash(0)
        self.assertEqual(value, encoder.expected_hash(0))
        for a, b in zip(before, encoder.pending[0]['planes']):
            np.testing.assert_array_equal(a, b)
            self.assertFalse(b.flags.writeable)
            self.assertFalse(np.shares_memory(rgb, b))
        self.assertEqual(encoder.oracle_packet_bytes(), 0)
        self.assertEqual(encoder.retained_reference_bytes(), 24 * 32 * 3)

    def test_credit_refresh_ack_and_expiry_match(self):
        old, new = frozen.AnchorEncoder(), Encoder()
        rgb = np.full((24, 32, 3), 50, np.uint8)
        for enc in (old, new):
            enc.prepare(rgb, 0)
            with self.assertRaises(ValueError):
                enc.prepare(rgb, 1)
            with self.assertRaises(ValueError):
                enc.ack(0, epoch=2)
            self.assertTrue(enc.ack(0, epoch=1))
            self.assertFalse(enc.ack(0, epoch=1))
            enc.prepare(rgb, 1)
            enc.prepare(rgb, 2)
            with self.assertRaises(ValueError):
                enc.prepare(rgb, 3)
            with self.assertRaises(ValueError):
                enc.prepare(rgb, 3, force_key=True)
            self.assertTrue(enc.ack(2, epoch=1))
            self.assertTrue(enc.expire(1))
        self.assertEqual(old.prepare(rgb, 3, force_key=True), new.prepare(rgb, 3, force_key=True))
        self.assertTrue(old.expire(3))
        self.assertTrue(new.expire(3))
        self.assertEqual(old.prepare(rgb, 4), new.prepare(rgb, 4))
        self.assertEqual(new.retained_reference_bytes(), old.retained_reference_bytes())
        self.assertEqual(new.peak_pending, 2)

    def test_rejected_inputs_leave_anchor_and_pending_unchanged(self):
        encoder = Encoder()
        rgb = np.zeros((16, 16, 3), np.uint8)
        encoder.prepare(rgb, 0)
        encoder.ack(0, epoch=1)
        anchor = encoder._anchor
        for options in ({'quant_scale': 0}, {'mode': 'nonsense'}, {'quant_scale': 129}):
            with self.assertRaises(ValueError):
                encoder.prepare(rgb, 1, force_key=True, **options)
            self.assertIs(encoder._anchor, anchor)
            self.assertEqual(encoder.pending, {})
            self.assertEqual(encoder.last_issued, 0)
        for bad in (-1, True, 0, frozen.mt.NO_REF):
            with self.assertRaises(ValueError):
                encoder.prepare(rgb, bad, force_key=True)

    def test_two_pending_p_oracles_survive_other_ack(self):
        encoder = Encoder()
        receiver = frozen.AnchorReceiver()
        rgb = np.full((32, 48, 3), 80, np.uint8)
        packet = encoder.prepare(rgb, 0)
        receiver.receive(packet)
        encoder.ack(0, epoch=1)
        packet1 = encoder.prepare(rgb + 1, 1)
        packet2 = encoder.prepare(rgb + 2, 2)
        a, _ = receiver.receive(packet1)
        b, _ = receiver.receive(packet2)
        encoder.ack(2, epoch=1)
        self.assertEqual(encoder.expected_hash(1), hashlib.sha256(a.tobytes()).hexdigest())
        self.assertGreater(encoder.oracle_packet_bytes(), 0)
        encoder.expire(1)
        self.assertEqual(encoder.oracle_packet_bytes(), 0)
        self.assertEqual(encoder.anchor_id, 0)


if __name__ == '__main__':
    unittest.main()
