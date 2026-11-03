import unittest
from audit import compare_shared_pts_hashes, covered_metric_window, nonoverlap_max_frames
class AuditHelpersTests(unittest.TestCase):
    def test_nonoverlap_counts_observed_pts_before_boundary(self): self.assertEqual(nonoverlap_max_frames([1.0, 1.04, 4.0, 4.04], 4.0), 2)
    def test_nonoverlap_rejects_missing_pts(self):
        with self.assertRaises(ValueError): nonoverlap_max_frames([1.0, None], 4.0)
    def test_repeated_hashes_at_distinct_pts_are_compared_per_pts(self):
        result = compare_shared_pts_hashes([10, 11, 12], ["same", "same", "other"],
                                           [11, 12, 13], ["same", "other", "same"])
        self.assertEqual(result["shared_pts"], [11, 12])
        self.assertEqual(result["mismatch_count"], 0)
        self.assertEqual(len(set(["same", "same", "other"]) & set(["same", "other", "same"])), 2)

    def test_metric_window_requires_complete_coverage(self):
        self.assertIsNone(covered_metric_window([1, 2], 3)); self.assertEqual(covered_metric_window([1, 2, 3, 4], 3), [1, 2, 3])
if __name__ == "__main__": unittest.main()
