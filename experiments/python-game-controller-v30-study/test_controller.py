import unittest
from controller import select_tier


def c(kind, size, sse):
    return dict(kind=kind, complete_bytes=size, hybrid=dict(active_squared_error=sse))


class AdmissionTests(unittest.TestCase):
    def test_band_compares_with_shadow_winner_not_looser_zero(self):
        a, b, d = c('zero', 400, 100), c('half32', 300, 50), c('zero_band', 200, 75)
        winner, shadow = select_tier([a, b, d], 'band_strict')
        self.assertIs(winner, b)
        self.assertIs(shadow, b)
        self.assertFalse(d['quality_eligible'])

    def test_exact_integer_one_percent_budget_and_stable_tie(self):
        a, b = c('zero', 400, 100), c('zero_band', 300, 101)
        self.assertIs(select_tier([a, b], 'band_budget')[0], b)
        self.assertIs(select_tier([a, b], 'band_strict')[0], a)
        b['hybrid']['active_squared_error'] = 102
        self.assertIs(select_tier([a, b], 'band_budget')[0], a)
        b.update(complete_bytes=400, hybrid=dict(active_squared_error=99))
        self.assertIs(select_tier([a, b], 'band_strict')[0], a)

    def test_capacity_and_no_shadow_rescue(self):
        self.assertIsNone(select_tier([c('zero', 49153, 100), c('zero_band', 100, 0)], 'band_strict')[0])
        a = c('zero', 49152, 100)
        self.assertIs(select_tier([a, c('zero_band', 49153, 0)], 'band_strict')[0], a)

    def test_invalid_inputs_and_zero_error_are_bounded(self):
        a, b = c('zero', 100, 0), c('zero_band', 90, 1)
        self.assertIs(select_tier([a, b], 'band_budget')[0], a)
        for group, policy in (([], 'band_strict'), ([c('zero', 10, -1)], 'band_strict'),
                              ([c('zero', 1, 0), c('zero_band', 1, 0)], 'adaptive_control'),
                              ([c('zero', 1, 0), c('zero', 2, 0)], 'band_strict')):
            with self.assertRaises(ValueError):
                select_tier(group, policy)


if __name__ == '__main__':
    unittest.main()
