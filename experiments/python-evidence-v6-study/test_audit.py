import unittest

from audit import overlap_by_id, percentile


class AuditHelpersTest(unittest.TestCase):
    def test_linear_percentile_matches_interpolated_definition(self):
        self.assertEqual(percentile([1, 2, 3, 4], 50), 2.5)
        self.assertAlmostEqual(percentile([0, 10], 95), 9.5)

    def test_same_content_does_not_mean_same_emitted_ids(self):
        a = [{"id": 15, "hash": "same"}, {"id": 16, "hash": "same"}]
        b = [{"id": 16, "hash": "same"}, {"id": 17, "hash": "same"}]
        result = overlap_by_id(a, b, "id", "hash")
        self.assertEqual(result["shared_ids"], [16])
        self.assertFalse(result["same_id_sets"])
        self.assertTrue(result["same_hash_multisets"])

    def test_hash_mismatch_at_shared_id_is_reported(self):
        a = [{"id": "pts=100", "hash": "a"}]
        b = [{"id": "pts=100", "hash": "b"}]
        result = overlap_by_id(a, b, "id", "hash")
        self.assertEqual(result["shared_id_hash_mismatches"], ["pts=100"])
        self.assertTrue(result["same_id_sets"])
        self.assertFalse(result["same_id_hash_mapping"])


if __name__ == "__main__":
    unittest.main()
