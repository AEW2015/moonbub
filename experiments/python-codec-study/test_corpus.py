"""Small independent checks for corpus pixel helpers (no video decoding)."""

import unittest

import numpy as np

from corpus import _letterbox, expand565, metrics, rgb565, synthetic_frames


class CorpusTests(unittest.TestCase):
    def test_rgb565_known_vectors_use_truncation(self):
        rgb = np.array([[[255, 255, 255], [248, 252, 248], [255, 0, 0],
                         [0, 255, 0], [0, 0, 255], [7, 3, 7]]], dtype=np.uint8)
        expected = np.array([[0xFFFF, 0xFFFF, 0xF800, 0x07E0, 0x001F, 0x0000]], dtype=np.uint16)
        np.testing.assert_array_equal(rgb565(rgb), expected)

    def test_expand565_known_vectors_replicate_bits(self):
        words = np.array([[0x0000, 0xFFFF, 0xF800, 0x07E0, 0x001F, 0x8410]], dtype=np.uint16)
        expected = np.array([[[0, 0, 0], [255, 255, 255], [255, 0, 0],
                              [0, 255, 0], [0, 0, 255], [132, 130, 132]]], dtype=np.uint8)
        np.testing.assert_array_equal(expand565(words), expected)

    def test_letterbox_preserves_aspect_and_active_crop(self):
        source = np.full((2, 4, 3), (10, 20, 30), dtype=np.uint8)
        canvas, rect = _letterbox(source, 4, 4)
        self.assertEqual(rect, (0, 1, 4, 2))
        np.testing.assert_array_equal(canvas[1:3], source)
        np.testing.assert_array_equal(canvas[[0, 3]], np.zeros((2, 4, 3), dtype=np.uint8))
        comparison = canvas.copy()
        comparison[0, 0] = (255, 0, 0)
        result = metrics(canvas, comparison, rect)
        self.assertFalse(result["exact"])
        self.assertTrue(result["active"]["exact"])
        self.assertEqual(result["active"]["mse"], 0.0)

    def test_synthetic_fixtures_are_labeled_and_deterministic(self):
        first = synthetic_frames(8, 6, 6)
        second = synthetic_frames(8, 6, 6)
        self.assertEqual([name for name, _ in first], [name for name, _ in second])
        for (name_a, image_a), (name_b, image_b) in zip(first, second):
            self.assertEqual(name_a, name_b)
            self.assertEqual(image_a.shape, (6, 8, 3))
            np.testing.assert_array_equal(image_a, image_b)


if __name__ == "__main__":
    unittest.main()
