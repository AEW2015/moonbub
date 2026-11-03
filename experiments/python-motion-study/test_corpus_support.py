"""Small checks for motion-study corpus and JPEG summary helpers."""
import unittest
from unittest import mock

import numpy as np

import corpus_support as support


class CorpusSupportTests(unittest.TestCase):
    def test_pooled_psnr_uses_pooled_mse_not_mean_of_frame_db(self):
        source = [np.zeros((1, 1, 3), dtype=np.uint8),
                  np.zeros((1, 1, 3), dtype=np.uint8)]
        recon = [np.ones((1, 1, 3), dtype=np.uint8),
                 np.full((1, 1, 3), 3, dtype=np.uint8)]
        mse, psnr = support._pooled_active_mse(source, recon, [(0, 0, 1, 1)] * 2)
        self.assertEqual(mse, 5.0)
        self.assertAlmostEqual(psnr, 10 * np.log10(255**2 / 5))
        per_frame_db = [10 * np.log10(255**2 / 1), 10 * np.log10(255**2 / 9)]
        self.assertNotAlmostEqual(psnr, sum(per_frame_db) / 2)

    def test_wire_accounting_packet_boundary(self):
        self.assertEqual(support.pacing.wire_bytes(1024, payload=1024, application_header=40), 1092)
        self.assertEqual(support.pacing.wire_bytes(1025, payload=1024, application_header=40), 1161)

    def test_loader_requests_bounded_nonrepeated_windows(self):
        blank = np.zeros((support.HEIGHT, support.WIDTH, 3), dtype=np.uint8)
        manifest = {"frame_count": 1, "frame_sha256": ["x"], "active_rects": [(0, 0, support.WIDTH, support.HEIGHT)]}
        with mock.patch.object(support.corpus, "load_video", return_value=([blank], manifest)) as load_video, \
                mock.patch.object(support, "_measure_jpeg", return_value={"35": {}}):
            scenes = support.load_scenes(frames_per_scene=1)
        self.assertEqual(len(scenes), 4)
        self.assertTrue(all(len(scene["frames"]) <= 1 for scene in scenes))
        self.assertEqual([call.kwargs["start_seconds"] for call in load_video.call_args_list], [1.0, 1.0, 4.0, 4.0])
        self.assertTrue(all(call.kwargs["max_frames"] == 1 for call in load_video.call_args_list))


if __name__ == "__main__":
    unittest.main()
