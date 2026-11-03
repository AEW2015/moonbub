import hashlib
import unittest

import numpy as np

from anchor_codec import AnchorEncoder, AnchorReceiver


class AnchorTests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.random.default_rng(3).integers(0, 256, (32, 48, 3), dtype=np.uint8)
        self.enc, self.dec = AnchorEncoder(), AnchorReceiver()
        packet = self.enc.prepare(self.rgb, 0)
        self.dec.receive(packet); self.enc.ack(0, epoch=1)

    def test_two_pending_packets_share_anchor_and_out_of_order_is_safe(self):
        p1 = self.enc.prepare(self.rgb, 1)
        p2 = self.enc.prepare(self.rgb, 2)
        self.assertFalse(self.enc.can_prepare())
        actual, _ = self.dec.receive(p2)
        self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(), self.enc.expected_hash(2))
        self.enc.ack(2, epoch=1)
        with self.assertRaises(ValueError): self.dec.receive(p1)
        self.enc.expire(1)
        p3 = self.enc.prepare(self.rgb, 3)
        self.dec.receive(p3); self.enc.ack(3, epoch=1)
        self.assertEqual((self.enc.anchor_id, self.dec.anchor_id), (0, 0))

    def test_missing_p_does_not_poison_later_p(self):
        self.enc.prepare(self.rgb, 1); self.enc.expire(1)
        self.dec.receive(self.enc.prepare(self.rgb, 2))
        self.enc.ack(2, epoch=1)
        self.assertEqual(self.dec.last_frame_id, 2)
        self.assertEqual(self.dec.anchor_id, 0)

    def test_refresh_drains_and_lost_key_ack_requires_independent_recovery(self):
        self.enc.prepare(self.rgb, 1)
        self.assertFalse(self.enc.can_prepare(force_key=True))
        self.enc.expire(1)
        key = self.enc.prepare(self.rgb, 2, force_key=True)
        self.dec.receive(key)
        self.enc.expire(2)  # Lost ACK after receiver replaced its anchor.
        self.assertIsNone(self.enc.anchor_id)
        key2 = self.enc.prepare(self.rgb, 3)
        self.dec.receive(key2); self.enc.ack(3, epoch=1)
        self.assertEqual((self.enc.anchor_id, self.dec.anchor_id), (3, 3))
        self.assertFalse(self.enc.ack(2, epoch=1))

    def test_wrong_epoch_and_duplicate_ack_do_not_advance(self):
        self.enc.prepare(self.rgb, 1)
        with self.assertRaises(ValueError): self.enc.ack(1, epoch=2)
        self.assertIn(1, self.enc.pending)
        self.enc.ack(1, epoch=1)
        self.assertFalse(self.enc.ack(1, epoch=1))
        self.assertEqual(self.enc.anchor_id, 0)

    def test_corruption_preserves_anchor_and_returned_image_is_private(self):
        packet = self.enc.prepare(self.rgb, 1)
        with self.assertRaises(ValueError): self.dec.receive(packet[:-1]+bytes([packet[-1]^1]))
        self.assertEqual(self.dec.last_frame_id, 0)
        actual, _ = self.dec.receive(packet)
        actual[:] = 0
        self.enc.ack(1, epoch=1)
        actual, _ = self.dec.receive(self.enc.prepare(self.rgb, 2))
        self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(), self.enc.expected_hash(2))


if __name__ == '__main__': unittest.main()
