"""Bounded fresh-RGB, refresh and full-stream checks for the historical control."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import custom_controls as control


class CustomControlTests(unittest.TestCase):
    def test_fresh_rgb_scene_cut_all_scales_and_exact_sender_reconstruction(self):
        rng = np.random.default_rng(9801)
        first = rng.integers(0, 256, (18, 34, 3), dtype=np.uint8)
        cut = np.full_like(first, (245, 25, 90))
        frames = [first, np.roll(first, 2, axis=1), cut, cut.copy()]
        saved = [x.copy() for x in frames]
        for scale in (8, 16, 32):
            with tempfile.TemporaryDirectory() as directory:
                decoded, info = control.run(frames, scale, output_dir=directory)
                self.assertEqual(len(decoded), 4)
                stream = Path(info['stream']['path']).read_bytes()
                self.assertEqual(len(stream), info['total_bytes'])
                self.assertEqual(hashlib.sha256(stream).hexdigest(), info['stream']['sha256'])
                receiver = control.gm.Receiver()
                for i, row in enumerate(info['packets']):
                    packet = stream[row['offset']:row['offset'] + row['bytes']]
                    actual, _ = receiver.receive(packet)
                    np.testing.assert_array_equal(actual, decoded[i])
                    self.assertEqual(row['expected_rgb_sha256'], row['decoded_rgb_sha256'])
                    self.assertEqual(row['source_rgb_sha256'], hashlib.sha256(frames[i]).hexdigest())
                    self.assertEqual(row['bytes'], row['outer_header_bytes'] + row['map_bytes'] +
                                     sum(row['nested_plane_bytes']) + row['outer_crc32_bytes'])
                self.assertFalse(np.array_equal(decoded[1], decoded[2]))
                self.assertEqual(info['key_ids'], [0])
                self.assertIsNone(info['byte_cap'])
                self.assertEqual(info['reference_memory']['peak_pending_credits'], 1)
                json.dumps(info, allow_nan=False)
        for actual, expected in zip(frames, saved):
            np.testing.assert_array_equal(actual, expected)

    def test_refresh_30_is_independent_and_scene_cut_has_no_implicit_refresh(self):
        a = np.full((16, 16, 3), 30, np.uint8)
        frames = [a.copy() for _ in range(31)]
        frames[7][:] = 240
        with tempfile.TemporaryDirectory() as directory:
            decoded, info = control.run(frames, 16, output_dir=directory)
            self.assertEqual(info['key_ids'], [0, 30])
            self.assertEqual(info['packets'][7]['reference_id'], 0)
            row = info['packets'][30]
            stream = Path(info['stream']['path']).read_bytes()
            actual, _ = control.gm.Receiver().receive(stream[row['offset']:row['offset'] + row['bytes']])
            np.testing.assert_array_equal(actual, decoded[30])

    def test_global_motion_and_color_helper_identity(self):
        rng = np.random.default_rng(9802)
        source = rng.integers(0, 256, (48, 64, 3), dtype=np.uint8)
        with tempfile.TemporaryDirectory() as directory:
            decoded, info = control.run([source, np.roll(source, 2, axis=1)], 'global16', output_dir=directory)
            self.assertEqual(info['motion_mode'], 'global')
            self.assertEqual(len(decoded), 2)
            self.assertEqual(len(info['encode_calls']), 2)
            self.assertEqual(len(info['decode_calls']), 2)
            self.assertEqual(control.gm.ft.__file__, control.gm.roi.ft.__file__)
            common_color = control.HERE.parent / 'python-game-standard-study/common_color.py'
            self.assertIn('planes=b.gm.ft.rgb_to_planes(rgb)', common_color.read_text())
            self.assertIn('b.gm.ft.planes_to_rgb(planes_from_frame(frame))', common_color.read_text())

    def test_invalid_inputs_are_rejected(self):
        frame = np.zeros((16, 16, 3), np.uint8)
        for parameter in (True, 7, 'CU66'):
            with self.assertRaises(ValueError):
                control.run([frame], parameter)
        with self.assertRaises(ValueError):
            control.run([], 16)
        with self.assertRaises(ValueError):
            control.run([frame], 16, fps=0)
        with self.assertRaises(ValueError):
            control.run([frame, np.zeros((18, 16, 3), np.uint8)], 16)


if __name__ == '__main__':
    unittest.main()
