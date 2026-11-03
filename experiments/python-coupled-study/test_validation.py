import unittest

from validation import summarize_presentation, validate_conservation


class SummaryTests(unittest.TestCase):
    def test_half_open_endpoint_drain_and_statistics(self):
        captures = [{"id": i, "capture_ms": i * 1000 / 30} for i in range(31)]
        presented = [{"id": i, "at_ms": 5 + i * 1000 / 30} for i in range(30)]
        presented.append({"id": 30, "at_ms": 1000})
        result = summarize_presentation(captures, presented, 1000, (0, 1000))
        self.assertEqual(result["capture_count"], 31)
        self.assertEqual(result["presented_count"], 30)
        self.assertEqual(result["drain_count"], 1)
        self.assertAlmostEqual(result["age_p50_ms"], 5)
        self.assertAlmostEqual(result["age_p95_ms"], 5)
        self.assertAlmostEqual(result["max_gap_ms"], 1000 / 30)
        self.assertEqual(result["steady_fps"], 30)

    def test_empty_counts_and_uncovered_steady_window(self):
        result = summarize_presentation([], [], 100, (50, 101))
        self.assertEqual(result["presented_count"], 0)
        self.assertEqual(result["drain_count"], 0)
        self.assertIsNone(result["age_p50_ms"])
        self.assertIsNone(result["age_p95_ms"])
        self.assertIsNone(result["age_max_ms"])
        self.assertIsNone(result["max_gap_ms"])
        self.assertIsNone(result["steady_fps"])
        self.assertFalse(result["steady_window_covered"])

    def test_duplicate_ids_and_ordering_rejected(self):
        with self.assertRaises(ValueError):
            summarize_presentation([{"id": 1, "capture_ms": 0}] * 2, [], 10, None)
        cap = [{"id": i, "capture_ms": 0} for i in (1, 2)]
        with self.assertRaises(ValueError):
            summarize_presentation(cap, [{"id": 1, "at_ms": 1}, {"id": 1, "at_ms": 2}], 10, None)
        with self.assertRaises(ValueError):
            summarize_presentation(cap, [{"id": 2, "at_ms": 1}, {"id": 1, "at_ms": 2}], 10, None)
        with self.assertRaises(ValueError):
            summarize_presentation(cap, [{"id": 1, "at_ms": 1}, {"id": 2, "at_ms": 1}], 10, None)

    def test_missing_capture_invalid_times_and_invalid_windows(self):
        with self.assertRaises(ValueError):
            summarize_presentation([], [{"id": 1, "at_ms": 1}], 10, None)
        for bad in (-1, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                summarize_presentation([], [], bad, None)
        with self.assertRaises(ValueError):
            summarize_presentation([{"id": 1, "capture_ms": 5}], [{"id": 1, "at_ms": 4}], 10, None)
        with self.assertRaises(ValueError):
            summarize_presentation([], [], 10, (5, 5))


class ConservationTests(unittest.TestCase):
    def test_exact_disjoint_partition(self):
        self.assertTrue(validate_conservation({1, 2, 3}, {1}, {2}, {3}))

    def test_overlap_missing_and_unknown_rejected(self):
        cases = [
            ({1}, {1}, {1}, set()),
            ({1, 2}, {1}, set(), set()),
            ({1}, {2}, set(), set()),
        ]
        for groups in cases:
            with self.assertRaises(ValueError):
                validate_conservation(*groups)


if __name__ == "__main__":
    unittest.main()
