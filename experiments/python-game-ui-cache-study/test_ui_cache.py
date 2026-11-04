from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np

import ui_cache as u


class UICacheTests(unittest.TestCase):
    def setUp(self):
        self.rgb = np.full((48, 64, 3), [40, 60, 80], np.uint8)
        self.rect = (4, 4, 16, 16)
        self.cfg = u.hybrid.Config(rectangles=(self.rect,))
        self.base = u.hybrid.gm.Encoder().prepare(self.rgb, 0)

    def test_exact_hit_keeps_full_frame_bytes_and_validation(self):
        cache = u.PatchCache()
        a = u.hybrid.select_frame(self.base, self.rgb, self.cfg)
        b = u.select(self.base, self.rgb, cache, self.cfg)
        self.assertEqual(a.packet, b.packet)
        with patch.object(u.hybrid, '_encode_patch', side_effect=AssertionError('hit re-encoded')):
            b = u.select(self.base, self.rgb, cache, self.cfg)
        self.assertEqual(a.packet, b.packet)
        d = b.attempts[0]['candidate_details']
        self.assertTrue(d['cache_hit'])
        self.assertEqual(d['current_candidate_count'], 0)
        self.assertEqual(d['current_attempts'], [])
        self.assertEqual(d['current_encoder_ms'], 0)
        self.assertIsNotNone(d['reused_candidate_details'])
        self.assertGreater(b.attempts[0]['validate_ms'], 0)

    def test_changed_background_hits_but_changed_words_miss(self):
        cache = u.PatchCache()
        first, _ = cache(self.rgb, self.rect, 'adaptive_row')
        source = self.rgb.copy()
        source[30:40] = 255
        second, info = cache(source, self.rect, 'adaptive_row')
        self.assertTrue(info['cache_hit'])
        self.assertEqual(first, second)
        source[4, 4] = 255
        _, info = cache(source, self.rect, 'adaptive_row')
        self.assertFalse(info['cache_hit'])
        source[4, 4] = 0
        _, info = cache(source, self.rect, 'adaptive_row')
        self.assertFalse(info['cache_hit'])

    def test_rgb888_difference_inside_same565_word_hits(self):
        cache = u.PatchCache()
        original, _ = cache(self.rgb, self.rect, 'adaptive_row')
        changed = self.rgb.copy()
        changed[4:20, 4:20] += np.array([1, 1, 1], np.uint8)
        self.assertFalse(np.array_equal(changed, self.rgb))
        actual, info = cache(changed, self.rect, 'adaptive_row')
        self.assertTrue(info['cache_hit'])
        expected, _ = u.hybrid._encode_patch(changed, self.rect, 'adaptive_row')
        self.assertEqual(actual, original)
        self.assertEqual(actual, expected)

    def test_rect_canvas_policy_and_four_entry_bounds(self):
        for bad in (-1, 5, True):
            with self.assertRaises(ValueError):
                u.PatchCache(bad)
        cache = u.PatchCache()
        for x in (0, 8, 16, 24, 32):
            cache(self.rgb, (x, 0, 8, 8), 'adaptive_row')
        self.assertEqual(len(cache._entries), 4)
        self.assertEqual(cache.evictions, 1)
        _, info = cache(self.rgb, (0, 0, 8, 8), 'adaptive_row')
        self.assertFalse(info['cache_hit'])
        _, info = cache(self.rgb, (0, 0, 8, 8), 'hp01')
        self.assertFalse(info['cache_hit'])
        wider = np.full((48, 66, 3), [40, 60, 80], np.uint8)
        _, info = cache(wider, (0, 0, 8, 8), 'hp01')
        self.assertFalse(info['cache_hit'])
        self.assertLessEqual(len(cache._entries), 4)

    def test_reused_payload_cap_fallthrough_and_base_rejection(self):
        cache = u.PatchCache()
        u.select(self.base, self.rgb, cache, self.cfg)
        cfg = replace(self.cfg, frame_cap=len(self.base))
        d = u.select(self.base, self.rgb, cache, cfg)
        self.assertEqual(d.packet, self.base)
        self.assertTrue(d.attempts[0]['candidate_details']['cache_hit'])
        self.assertFalse(d.attempts[0]['fits'])
        hits = cache.hits
        d = u.select(self.base, self.rgb, cache, replace(cfg, frame_cap=len(self.base)-1))
        self.assertFalse(d.accepted)
        self.assertEqual(cache.hits, hits)

    def test_budget_keeps_lookup_validation_paid_and_can_drop_wrapper(self):
        cache = u.PatchCache()
        u.select(self.base, self.rgb, cache, self.cfg)
        ticks = iter(range(0, 100_000_000, 1_000_000))
        d = u.select(self.base, self.rgb, cache, replace(self.cfg, work_budget_ms=5), clock_ns=lambda: next(ticks))
        self.assertTrue(d.deadline_hit)
        self.assertEqual(d.packet, self.base)
        self.assertEqual(len(d.attempts), 1)
        self.assertTrue(d.attempts[0]['candidate_details']['cache_hit'])
        self.assertGreater(d.attempts[0]['encode_ms'], 0)
        self.assertGreater(d.attempts[0]['validate_ms'], 0)


if __name__ == '__main__':
    unittest.main()
