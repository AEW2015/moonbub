import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / 'baseline.json').read_text())


def guarded(candidate_bytes, candidate_sse, shadow_bytes, shadow_sse, cap=49152):
    return (type(candidate_bytes) is int and type(candidate_sse) is int
            and type(shadow_bytes) is int and type(shadow_sse) is int
            and candidate_bytes <= cap and candidate_bytes < shadow_bytes
            and candidate_sse <= shadow_sse)


def complete_cohorts(cases, scenes, policies, frames=48):
    keys = [(c['scene'], c['policy']) for c in cases]
    expected = {(s, p) for s in scenes for p in policies}
    return (len(keys) == len(expected) and len(set(keys)) == len(keys) and set(keys) == expected
            and all([r['id'] for r in c['rows']] == list(range(frames)) for c in cases))


class V35BaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import audit
        cls.report = audit.audit()

    def test_control_integer_mse_and_inclusive_cap(self):
        accounting = BASE['accounting']
        self.assertTrue(accounting['control_packets_are_actual_CP34_HX33_host_model_outputs'])
        samples = accounting['frames_per_scene'] * 720 * 405 * 3
        for scene in BASE['scenes'].values():
            for name in ('custom_control', 'av1', 'hevc'):
                point = scene[name]
                self.assertEqual(point['samples'], samples)
                self.assertAlmostEqual(point['sse'] / samples, point['mse'], places=14)
                self.assertLessEqual(point['max_frame_bytes'], accounting['cap_bytes_per_frame'])
        self.assertEqual(23321, BASE['scenes']['mass-effect-2600']['custom_control']['max_frame_bytes'])

    def test_actual_shadow_guard_requires_saving_cap_and_no_sse_regression(self):
        shadow_bytes, shadow_sse = 1000, 4000
        self.assertTrue(guarded(999, 4000, shadow_bytes, shadow_sse))
        self.assertFalse(guarded(1000, 4000, shadow_bytes, shadow_sse))
        self.assertFalse(guarded(999, 4001, shadow_bytes, shadow_sse))
        self.assertFalse(guarded(49153, 0, shadow_bytes, shadow_sse))
        self.assertFalse(guarded(999, 4000, shadow_bytes, shadow_sse, cap=998))

    def test_cohort_matrix_rejects_duplicates_missing_or_reordered_ids(self):
        scenes, policies = ('s0', 's1'), ('control', 'core8', 'other')
        cases = [dict(scene=s, policy=p, rows=[dict(id=i) for i in range(48)])
                 for s in scenes for p in policies]
        self.assertTrue(complete_cohorts(cases, scenes, policies))
        self.assertFalse(complete_cohorts(cases[:-1], scenes, policies))
        self.assertFalse(complete_cohorts(cases + [cases[0]], scenes, policies))
        broken = [dict(c) for c in cases]
        broken[0] = dict(broken[0], rows=[dict(id=i) for i in range(47)] + [dict(id=46)])
        self.assertFalse(complete_cohorts(broken, scenes, policies))

    def test_guarded_core8_saves_bytes_but_not_aggregate_quality(self):
        self.assertEqual(self.report['accepted_frames'], 192)
        self.assertEqual(self.report['actual_candidate_frames'], 1128)
        self.assertEqual(self.report['exact_v34_control_CP34_parity_rows'], 96)
        for scene in ('mass-effect-2600', 'mass-effect-7200'):
            delta = self.report['quality_comparison'][scene]
            self.assertEqual(delta['strict_guarded_candidates_selected'], 48)
            self.assertGreater(delta['complete_byte_saving'], 0)
            self.assertGreater(delta['active_mse_delta'], 0)
            self.assertFalse(delta['quality_neutral_or_better'])

    def test_fresh_native_cases_use_exact_core8_trace_and_hx33(self):
        self.assertEqual(len(self.report['actual_same_processed_native_points']), 4)
        for point in self.report['actual_same_processed_native_points'].values():
            self.assertTrue(point['exact_AU_anchor_parity'])
            self.assertTrue(point['same_actual_HX33_and_60B'])
            self.assertTrue(point['meets_custom_quality_and_cap'])


if __name__ == '__main__':
    unittest.main()
