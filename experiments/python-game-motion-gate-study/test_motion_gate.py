import unittest
from unittest.mock import patch
import numpy as np
import motion_gate as g


class GateTests(unittest.TestCase):
    def fixture(self):
        rng = np.random.default_rng(1303)
        return np.repeat(np.repeat(rng.integers(30, 226, (2, 4, 3), dtype=np.uint8)//16*16, 16, 0), 16, 1)

    def mapping(self):
        return np.full((2, 4), 16, np.uint8)

    def ack(self, enc, packet):
        identity = g.r.identity(packet)
        return enc.ack(identity['frame_id'], epoch=1, frame_crc=identity['body_tag'])

    def key(self, enc, rgb):
        d = enc.prepare(rgb, 0, scale_map=self.mapping())
        self.ack(enc, d.packet)
        return d

    def test_key_and_geometry_skip_screen_without_sampling_or_bm_work(self):
        enc = g.Encoder()
        self.key(enc, self.fixture())
        self.assertEqual(enc.last_gate['reason'], 'key')
        self.assertEqual(enc.last_gate['comparisons'], 0)
        self.assertEqual(len(enc.last_info.attempts), 1)
        changed = np.zeros((16, 32, 3), np.uint8)
        self.assertEqual(g.screen(changed, enc._anchor)['reason'], 'geometry_key')

    def test_static_screen_prevents_block_search_and_preserves_bytes(self):
        rgb = self.fixture(); gated = g.Encoder(); control = g.r.Encoder(modes=('gm_zero',))
        self.key(gated, rgb); self.key(control, rgb)
        with patch.object(g.r.bm, 'estimate_vectors', side_effect=AssertionError('unexpected full search')):
            actual = gated.prepare(rgb, 1, scale_map=self.mapping())
            expected = control.prepare(rgb, 1, scale_map=self.mapping())
        self.assertFalse(gated.last_gate['allow_block'])
        self.assertEqual(actual.packet, expected.packet)
        self.assertEqual(gated.last_gate['comparisons'], 25*8*4)
        self.assertEqual(actual.selected_mode, 'gm_zero')
        self.assertGreaterEqual(gated.last_total_service_ms, actual.service_ms + gated.last_gate['gate_ms'])

    def test_translation_passes_and_actual_candidate_bytes_match_controls(self):
        rgb = self.fixture(); current = np.roll(rgb, 2, axis=1)
        gated = g.Encoder(); control = g.r.Encoder()
        self.key(gated, rgb); self.key(control, rgb)
        actual = gated.prepare(current, 1, scale_map=self.mapping())
        expected = control.prepare(current, 1, scale_map=self.mapping())
        self.assertTrue(gated.last_gate['allow_block'])
        self.assertEqual(len(actual.attempts), 2)
        self.assertEqual(actual.packet, expected.packet)
        self.assertEqual([a['packet_sha256'] for a in actual.attempts], [a['packet_sha256'] for a in expected.attempts])
        self.assertGreater(sum(a['stages']['candidate_total_ms'] for a in actual.attempts), 0)

    def test_screen_is_deterministic_and_does_not_mutate_current_or_anchor(self):
        rgb = self.fixture(); enc = g.Encoder(); self.key(enc, rgb)
        current = np.roll(rgb, 2, axis=1); original = current.copy()
        anchors = tuple(p.copy() for p in enc._anchor)
        first = g.screen(current, enc._anchor); second = g.screen(current, enc._anchor)
        for result in (first, second):result.pop('gate_ms')
        self.assertEqual(first, second)
        np.testing.assert_array_equal(current, original)
        for before, after in zip(anchors, enc._anchor):np.testing.assert_array_equal(before, after)

    def test_rejection_pays_gate_and_codec_without_credit_or_reference_change(self):
        enc = g.Encoder(); rgb = self.fixture(); self.key(enc, rgb); anchor = enc._anchor
        d = enc.prepare(np.roll(rgb, 2, axis=1), 1, scale_map=self.mapping(), frame_cap=100)
        self.assertFalse(d.accepted); self.assertFalse(enc.pending)
        self.assertIs(enc._anchor, anchor); self.assertEqual(enc.last_issued, 0)
        self.assertGreater(enc.last_gate['gate_ms'], 0)
        self.assertGreater(enc.last_total_service_ms, d.service_ms)
        self.assertEqual(len(d.attempts), 2)
        self.assertTrue(all(not a['fits'] for a in d.attempts))

    def test_mixed_stream_credit_expiry_ack_and_decoder_are_unchanged(self):
        rgb = self.fixture(); enc = g.Encoder(); rx = g.r.Decoder()
        first = enc.prepare(rgb, 0, scale_map=self.mapping()); rx.receive(first.packet)
        self.ack(enc, first.packet); anchor = enc._anchor
        for frame in (1, 2):enc.prepare(np.roll(rgb, frame*2, axis=1), frame, scale_map=self.mapping())
        self.assertFalse(enc.can_prepare()); self.assertEqual(enc.read_pins, 2)
        with self.assertRaises(ValueError):enc.prepare(rgb, 3, scale_map=self.mapping(), force_key=True)
        self.assertEqual(enc.modes, ('gm_zero', 'bm_block'))
        enc.expire(1); enc.expire(2); self.assertIs(enc._anchor, anchor)
        fresh = enc.prepare(rgb, 3, scale_map=self.mapping(), force_key=True)
        info = g.r.identity(fresh.packet)
        with self.assertRaises(ValueError):enc.ack(3, epoch=1, frame_crc=info['body_tag']^1)
        actual, _ = rx.receive(fresh.packet)
        self.assertEqual(g.r.hashlib.sha256(actual.tobytes()).hexdigest(), enc.expected_hash(3))
        self.ack(enc, fresh.packet); self.assertEqual(enc.anchor_id, 3)

    def test_sample_bounds_and_config_validation(self):
        rgb = np.zeros((18, 34, 3), np.uint8)
        anchor = tuple(g.r.gm.ft.rgb_to_planes(rgb))
        result = g.screen(rgb, anchor)
        self.assertEqual(result['samples'], 2*3*4)
        self.assertFalse(result['allow_block'])
        for kwargs in ({'minimum_gain':float('nan')}, {'minimum_relative_gain':2}, {'search_range':3}):
            with self.assertRaises(ValueError):g.Config(**kwargs)


if __name__ == '__main__':
    unittest.main()
