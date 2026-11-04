from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np

import cache_admission as c


class CacheAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((48, 64, 3), [40, 60, 80], np.uint8)
        self.cfg = c.normal.Config(policy='uniform')

    def pair(self):
        return c.normal.Controller(config=self.cfg), c.Controller(config=self.cfg)

    def prime(self, controller):
        d = controller.prepare(self.rgb, 0)
        self.assertTrue(d.accepted)
        controller.encoder.ack(0, epoch=1)
        return d

    def compare(self, a, b, rgb, frame_id, **kwargs):
        x, y = a.prepare(rgb, frame_id, **kwargs), b.prepare(rgb, frame_id, **kwargs)
        self.assertEqual(x.packet, y.packet)
        self.assertEqual(x.selected, y.selected)
        self.assertEqual([r['bytes'] for r in x.attempts], [r['bytes'] for r in y.attempts])
        self.assertEqual(a.encoder.last_issued, b.encoder.last_issued)
        self.assertEqual(a.encoder._generation, b.encoder._generation)
        self.assertEqual(a.encoder.anchor_id, b.encoder.anchor_id)
        self.assertEqual(set(a.encoder.pending), set(b.encoder.pending))
        if y.accepted:
            self.assertEqual(a.encoder.expected_hash(frame_id), b.encoder.expected_hash(frame_id))
        return x, y

    def test_exact_hits_use_commit_and_no_transform_or_entropy(self):
        a, b = self.pair()
        self.prime(a); self.prime(b)
        self.compare(a, b, self.rgb, 1)
        a.encoder.ack(1, epoch=1); b.encoder.ack(1, epoch=1)
        baseline = a.prepare(self.rgb, 2)
        with patch.object(c.gm.ft, 'forward', side_effect=AssertionError('hit transformed')):
            with patch.object(c.gm.token_coeff, 'encode_coefficients', side_effect=AssertionError('hit entropy')):
                d = b.prepare(self.rgb, 2)
        self.assertEqual(d.packet, baseline.packet)
        self.assertEqual(d.forward_calls, 0)
        self.assertEqual(d.analyze_calls, 0)
        self.assertTrue(d.attempts[0]['cache_hit'])
        self.assertIn(2, b.encoder.pending)
        self.assertEqual(b.encoder.anchor_id, 0)

    def test_cap_rejection_no_codec_commit_and_repeat_reject_cost_paid(self):
        a, b = self.pair()
        self.prime(a); self.prime(b)
        noise = np.random.default_rng(4).integers(0, 256, self.rgb.shape, dtype=np.uint8)
        a.config = b.config = replace(self.cfg, frame_cap=1)
        before = (b.encoder.last_issued, b.encoder._generation, b.encoder._anchor, dict(b.encoder.pending))
        x, y = self.compare(a, b, noise, 1)
        self.assertFalse(y.accepted)
        self.assertEqual(len(y.attempts), 2)
        self.assertTrue(all(not r['fits'] for r in y.attempts))
        self.assertEqual(before[:2], (b.encoder.last_issued, b.encoder._generation))
        self.assertIs(before[2], b.encoder._anchor)
        self.assertEqual(before[3], b.encoder.pending)
        with patch.object(c.gm.ft, 'forward', side_effect=AssertionError('cached rejection transformed')):
            y = b.prepare(noise, 2)
        self.assertFalse(y.accepted)
        self.assertTrue(all(r['cache_hit'] for r in y.attempts))
        self.assertEqual(y.forward_calls, 0)
        self.assertGreater(y.service_ms, 0)
        self.assertTrue(all(r['candidate_ms'] > 0 for r in y.attempts))
        self.assertFalse(b.encoder.pending)

    def test_cached_fallback_candidate_is_admitted_before_commit(self):
        a, b = self.pair()
        self.prime(a); self.prime(b)
        noise = np.random.default_rng(7).integers(0, 256, self.rgb.shape, dtype=np.uint8)
        # Populate both actual maps using a wholly rejected source first.
        a.config = b.config = replace(self.cfg, frame_cap=1)
        x, y = self.compare(a, b, noise, 1)
        n, f = [row['bytes'] for row in x.attempts]
        self.assertLess(f, n)
        a.config = b.config = replace(self.cfg, frame_cap=f)
        x, y = self.compare(a, b, noise, 2)
        self.assertTrue(y.accepted)
        self.assertEqual(y.selected, 'fallback')
        self.assertEqual(len(y.attempts), 2)
        self.assertTrue(all(r['cache_hit'] for r in y.attempts))
        self.assertEqual(y.forward_calls, 0)
        self.assertEqual(list(b.encoder.pending), [2])

    def test_credit_key_drain_and_stale_cached_preview(self):
        b = c.Controller(config=self.cfg)
        self.prime(b)
        b.prepare(self.rgb, 1); b.encoder.ack(1, epoch=1)
        payload = b._cache['payloads'][0]
        preview = b.encoder.preview_cached(payload, 2)
        b.prepare(self.rgb, 2)
        with self.assertRaises(ValueError):
            b.encoder.commit(preview)
        b.prepare(self.rgb, 3)
        with self.assertRaises(ValueError):
            b.prepare(self.rgb, 4)
        with self.assertRaises(ValueError):
            b.prepare(self.rgb, 4, force_key=True)
        b.encoder.expire(2); b.encoder.expire(3)
        b.prepare(self.rgb, 4, force_key=True)
        self.assertEqual(b.cache_bytes(), 0)
        with self.assertRaises(ValueError):
            b.encoder.preview_cached(payload, 5)
        b.encoder.ack(4, epoch=1)
        with self.assertRaises(ValueError):
            b.encoder.preview_cached(payload, 5)

    def test_map_mode_source_and_epoch_invalidations(self):
        a, b = self.pair()
        self.prime(a); self.prime(b)
        source = self.rgb.copy()
        for frame in range(1, 7):
            if frame == 3:
                source[0, 0] = [255, 0, 0]
            if frame == 4:
                a.config = b.config = replace(self.cfg, motion_mode='global')
            if frame == 5:
                a.config = b.config = replace(self.cfg, policy='priority', rectangles=((0, 0, 16, 16),))
            _, d = self.compare(a, b, source, frame)
            self.assertEqual(d.attempts[0]['cache_hit'], frame in (2, 6))
            a.encoder.ack(frame, epoch=1); b.encoder.ack(frame, epoch=1)
        with self.assertRaises(ValueError):
            b.encoder.ack(6, epoch=2)
        b.encoder.epoch = 2
        d = b.prepare(source, 7)
        self.assertFalse(d.attempts[0]['cache_hit'])
        self.assertEqual(c.gm.parse(d.packet, 2)['epoch'], 2)

    def test_expired_p_cache_valid_but_new_key_rebuilds(self):
        a, b = self.pair()
        self.prime(a); self.prime(b)
        self.compare(a, b, self.rgb, 1)
        a.encoder.expire(1); b.encoder.expire(1)
        _, d = self.compare(a, b, self.rgb, 2)
        self.assertTrue(d.attempts[0]['cache_hit'])
        a.encoder.ack(2, epoch=1); b.encoder.ack(2, epoch=1)
        self.compare(a, b, self.rgb, 3, force_key=True)
        a.encoder.expire(3); b.encoder.expire(3)
        _, d = self.compare(a, b, self.rgb, 4)
        self.assertFalse(d.attempts[0]['cache_hit'])
        self.assertEqual(b.cache_bytes(), 0)

    def test_registered_capabilities_reject_foreign_and_forged_previews(self):
        a, b = c.Controller(config=self.cfg), c.Controller(config=self.cfg)
        for ctrl in (a, b):
            self.prime(ctrl)
            ctrl.prepare(self.rgb, 1); ctrl.encoder.ack(1, epoch=1)
        payload = a._cache['payloads'][0]
        with self.assertRaises(ValueError):
            b.encoder.preview_cached(payload, 2)
        valid = a.encoder.preview_cached(payload, 2)
        with self.assertRaises(ValueError):
            a.encoder.commit(replace(valid, frame_id=9))
        self.assertFalse(a.encoder.pending)

    def test_sequence_byte_equality_with_bounded_two_map_cache(self):
        rng = np.random.default_rng(1303)
        a, b = self.pair()
        for i in range(16):
            if i % 3 == 0:
                frame = rng.integers(0, 256, self.rgb.shape, dtype=np.uint8)
            _, d = self.compare(a, b, frame, i, force_key=i in (0, 8))
            self.assertTrue(d.accepted)
            a.encoder.ack(i, epoch=1); b.encoder.ack(i, epoch=1)
            self.assertLessEqual(len(b._cache['payloads']) if b._cache else 0, 2)
            self.assertLess(b.cache_bytes(), self.rgb.nbytes + 2 * 128 * 72 + 4096)


if __name__ == '__main__':
    unittest.main()
