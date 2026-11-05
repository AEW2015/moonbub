import unittest
from controller import select_group


def candidate(kind, size, error):
    return dict(kind=kind, complete_bytes=size, hybrid=dict(active_squared_error=error))


class ControllerTests(unittest.TestCase):
    def test_cap_and_current_source_quality_both_required(self):
        zero = candidate('zero', 49152, 10)
        bad_quality = candidate('motion', 100, 11)
        self.assertIs(select_group([zero, bad_quality]), zero)
        self.assertFalse(bad_quality['quality_eligible'])
        overcap = candidate('zero', 49153, 0)
        self.assertIsNone(select_group([overcap]))

    def test_ties_are_stable_and_better_motion_can_win(self):
        a, b = candidate('zero', 200, 10), candidate('motion', 200, 9)
        self.assertIs(select_group([a, b]), a)
        b['complete_bytes'] = 199
        self.assertIs(select_group([a, b]), b)

    def test_reference_is_current_candidate_not_historical_average(self):
        self.assertEqual(select_group([candidate('zero', 300, 100), candidate('motion', 250, 99)])['kind'], 'motion')
        self.assertEqual(select_group([candidate('zero', 300, 50), candidate('motion', 250, 99)])['kind'], 'zero')

    def test_reject_invalid_or_duplicate_candidates(self):
        for group in ([], [candidate('motion', 1, 0)], [candidate('zero', 1, 0), candidate('zero', 2, 0)],
                      [candidate('zero', -1, 0)], [candidate('zero', 1, -1)]):
            with self.assertRaises(ValueError):
                select_group(group)


if __name__ == '__main__':
    unittest.main()
