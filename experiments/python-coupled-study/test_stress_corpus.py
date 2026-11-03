import unittest

import numpy as np

from stress_corpus import make_stress_frames


class StressCorpusTests(unittest.TestCase):
    def test_repeatable_arrays_hashes_and_metadata(self):
        first, manifest_a = make_stress_frames(width=32, height=24, count=12)
        second, manifest_b = make_stress_frames(width=32, height=24, count=12)
        self.assertEqual(len(first), 12)
        self.assertEqual(manifest_a, manifest_b)
        for frame_a, frame_b, metadata in zip(first, second, manifest_a["frames"]):
            self.assertEqual(frame_a.shape, (24, 32, 3))
            self.assertEqual(frame_a.dtype, np.uint8)
            self.assertTrue(np.array_equal(frame_a, frame_b))
            self.assertEqual(metadata["active_rect"], [0, 0, 32, 24])
            self.assertEqual(len(metadata["sha256"]), 64)
        self.assertEqual(manifest_a["source"], "synthetic")
        self.assertEqual(manifest_a["timing"], "synthetic_30_hz_schedule")
        self.assertEqual(manifest_a["frames"][0]["selected_time_s"], 0)
        self.assertEqual(manifest_a["frames"][-1]["selected_time_s"], 11 / 30)
        self.assertEqual(manifest_a["unique_frame_count"], len({row["sha256"] for row in manifest_a["frames"]}))

    def test_noise_and_recovery_labels_are_present(self):
        _, manifest = make_stress_frames(width=32, height=24, count=12)
        labels = [row["label"] for row in manifest["frames"]]
        self.assertEqual(labels.count("noise_burst"), 5)
        self.assertIn("flat_pattern", labels)
        self.assertIn("moving_gradient", labels)
        self.assertIn("recovery_flat", labels)
        burst_end = max(i for i, label in enumerate(labels) if label == "noise_burst")
        self.assertTrue(all(label == "recovery_flat" for label in labels[burst_end + 1:]))

    def test_empty_corpus_and_invalid_dimensions(self):
        frames, manifest = make_stress_frames(width=32, height=24, count=0)
        self.assertEqual(frames, [])
        self.assertEqual(manifest["frames"], [])
        self.assertEqual(manifest["unique_frame_count"], 0)
        for args in ((0, 24, 1), (32, -1, 1), (32, 24, -1)):
            with self.assertRaises(ValueError):
                make_stress_frames(*args)


if __name__ == "__main__":
    unittest.main()
