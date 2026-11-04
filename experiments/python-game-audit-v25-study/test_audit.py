import hashlib
import math
from pathlib import Path
import tempfile
import unittest
import zlib

import audit


class IndependentAuditTests(unittest.TestCase):
    def test_pooled_mse_uses_sse_over_samples(self):
        rows = [dict(hybrid=dict(active_squared_error=10, active_channel_samples=2, hud_word_errors=0)),
                dict(hybrid=dict(active_squared_error=90, active_channel_samples=18, hud_word_errors=0))]
        m = audit.pooled_metric(rows, 'hybrid')
        self.assertEqual(m['active_squared_error'], 100)
        self.assertEqual(m['active_channel_samples'], 20)
        self.assertEqual(m['active_mse'], 5)

    def test_zero_error_psnr_is_infinite_marker(self):
        m = audit.pooled_metric([dict(bare=dict(active_squared_error=0, active_channel_samples=3, hud_word_errors=0))], 'bare')
        self.assertIsNone(m['active_psnr_db'])

    def test_rate_projects_complete_bytes_at_nominal_30(self):
        self.assertEqual(audit.projected_mbps(100_000, 48), 0.5)

    def test_descriptor_verifies_both_hashes_and_exact_length(self):
        raw = b'packet-bytes'
        stored = zlib.compress(raw, 9)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'a.zlib'; p.write_bytes(stored)
            desc = dict(path='a.zlib', raw_bytes=len(raw), raw_sha256=hashlib.sha256(raw).hexdigest(), stored_sha256=hashlib.sha256(stored).hexdigest())
            self.assertEqual(audit.read_object(desc, td), raw)
            desc['raw_bytes'] += 1
            with self.assertRaises(ValueError): audit.read_object(desc, td)

    def test_pairing_rejects_frame_mismatch_and_discloses_reference_change(self):
        old = [dict(id=0, source_sha256='s', reference_id=0)]
        new = [dict(id=0, source_sha256='s', reference_id=0)]
        self.assertEqual(audit.compare_pairing(old, new), [])
        with self.assertRaises(ValueError): audit.compare_pairing(old, [dict(id=1, source_sha256='s', reference_id=0)])
        new[0]['reference_id'] = 3
        self.assertEqual(audit.compare_pairing(old, new, allow_reference_policy_change=True), [0])

    def test_hud_word_count_is_exact_and_overlap_is_rejected(self):
        rects = [(22, 54, 160, 24), (22, 82, 160, 24), (168, 360, 320, 24), (168, 390, 240, 24)]
        self.assertEqual(audit.exact_hud_words(rects), audit.HUD_WORDS)
        with self.assertRaises(ValueError): audit.exact_hud_words([(0, 0, 2, 2), (1, 1, 2, 2)])

    def test_complete_packet_composition_accounts_all_bytes(self):
        row = dict(base_packet=dict(raw_bytes=100), hud_packet=dict(raw_bytes=200),
                   complete_packet=dict(raw_bytes=340), base_bytes=100, hud_bytes=200,
                   complete_bytes=340, outer_overhead_bytes=40)
        self.assertEqual(audit.assert_packet_composition(row)['complete_bytes'], 340)
        row['complete_bytes'] = 339
        with self.assertRaises(ValueError): audit.assert_packet_composition(row)

    def test_active_sample_count_matches_720_by_405_rgb(self):
        rows = [dict(hybrid=dict(active_squared_error=7, active_channel_samples=720*405*3, hud_word_errors=0))]
        self.assertEqual(audit.quality_from_samples(rows, 'hybrid')['active_channel_samples'], 874800)
        rows[0]['hybrid']['active_channel_samples'] = 3
        with self.assertRaises(ValueError): audit.quality_from_samples(rows, 'hybrid')


if __name__ == '__main__': unittest.main()
