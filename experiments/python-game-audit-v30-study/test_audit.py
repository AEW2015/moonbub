import unittest

import audit


class V30AuditTests(unittest.TestCase):
    def test_strict_and_one_percent_guards_use_integer_comparison(self):
        self.assertTrue(audit.band_guard_passes(100, 100, 'band_strict'))
        self.assertFalse(audit.band_guard_passes(101, 100, 'band_strict'))
        self.assertTrue(audit.band_guard_passes(101, 100, 'band_budget'))
        self.assertFalse(audit.band_guard_passes(102, 100, 'band_budget'))
        with self.assertRaises(ValueError):
            audit.band_guard_passes(100, 100, 'adaptive_control')

    def test_summary_uses_integer_sse_and_recomputes_nominal_rate(self):
        row = dict(body_bytes=1000, base_bytes=700, hud_bytes=240, binding_bytes=60,
                   hybrid=dict(active_squared_error=300, active_channel_samples=100,
                               active_mse=3.0, hud_word_errors=0), attempts=[], analyses={},
                   paid_base_encode_ms=0.0, base_policy_service_ms=0.0,
                   receive_ms=2.0, selected_background=16,
                   selected_kind='zero', baseline_complete_bytes=1000, baseline_source_sse=300)
        summary = audit.summarize([row])
        self.assertEqual(summary['complete_bytes'], 1000)
        self.assertEqual(summary['exact_hud_words'], audit.HUD_WORDS)
        self.assertEqual(summary['active_mse'], 3.0)
        self.assertAlmostEqual(summary['coded_body_Mbps_at30'], 0.24)
        row['hybrid']['active_mse'] = 4.0
        with self.assertRaises(ValueError):
            audit.summarize([row])

    def test_decoded_reference_replay_follows_each_policy_own_prior_output(self):
        rows, checks, previous = [], [], None
        for fid in range(48):
            key = fid % 24 == 0
            ref = bytes(16).hex() if key else previous
            decoded, image = f'tag-{fid}', f'image-{fid}'
            rows.append(dict(id=fid, key=key, reference_tag=ref,
                             reconstructed_tag=decoded, hybrid_rgb565_sha256=image))
            checks.append(dict(id=fid, reference_tag=ref, decoded_tag=decoded,
                               hybrid_rgb565_sha256=image))
            previous = decoded
        cases = {('scene', 'policy'): dict(rows=rows)}
        replay = dict(chains=[dict(scene='scene', policy='policy', rows=[
            *checks,
        ])])
        audit.verify_replay_chains(replay, cases)
        replay['chains'][0]['rows'][1]['reference_tag'] = 'wrong'
        with self.assertRaises(ValueError):
            audit.verify_replay_chains(replay, cases)


if __name__ == '__main__':
    unittest.main()
