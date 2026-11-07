"""Small sequential native round trips; no corpus benchmark is run here."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import standard_controls as sc


class NativeControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v98-controls-test-')
        yy, xx = np.indices((480, 720))
        base = np.stack(((xx // 3) % 256, (yy // 2) % 256,
                         ((xx + yy) // 5) % 256), axis=-1).astype(np.uint8)
        cls.frames = [np.roll(base, i * 6, axis=1).copy() for i in range(3)]
        for i, frame in enumerate(cls.frames):
            frame[100:180, 220:300] = [230 - i * 40, 20 + i * 60, 70]
        cls.results = {}
        # Serialize encoders: x265 pools=none/frame-threads=1; SVT lp=1.
        for codec, parameter in (('hevc', 36), ('av1', 38), ('jpeg', 6)):
            cls.results[codec] = sc.run(cls.frames, codec, parameter,
                                       fps=Fraction(30000, 1001),
                                       output_dir=Path(cls.temp.name) / codec)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_complete_ordered_outputs_and_no_future_input_buffering(self):
        for codec, (outputs, info) in self.results.items():
            with self.subTest(codec=codec):
                self.assertEqual(len(outputs), 3)
                self.assertEqual(info['output_pts'], [0, 1, 2])
                self.assertTrue(all(o.shape == (480, 720, 3) and o.dtype == np.uint8 for o in outputs))
                self.assertTrue(all(c['emitted_pts'] == [c['id']] for c in info['frame_calls']))
                self.assertEqual([p['pts'] for p in info['packets']], [0, 1, 2])
                self.assertTrue(all(p['pts'] == p['dts'] for p in info['packets']))
                self.assertTrue(all(a['pts'] == a['after_input_index'] and a['input_lag_frames'] == 0
                                    and a['phase'] == 'input' for a in info['output_availability']))
                self.assertEqual(info['packets_returned_only_at_flush'], 0)
                self.assertEqual(info['decoded_frames_only_at_flush'], 0)
                self.assertEqual(info['first_packet']['after_input_index'], 0)
                self.assertEqual(info['first_decoded_output']['after_input_index'], 0)
                self.assertGreater(info['first_packet_elapsed_ms'], 0)
                self.assertGreaterEqual(info['first_decoded_output_elapsed_ms'], info['first_packet_elapsed_ms'])
                self.assertGreaterEqual(info['sequence_processing_ms'], info['first_decoded_output_elapsed_ms'])
                self.assertGreaterEqual(info['first_decoded_output']['decode_call_start_to_rgb_ready_ms'],
                                        info['decode_calls'][0]['decode_ms'])
                self.assertEqual(info['time_base'], '1001/30000')

    def test_encoded_byte_ledger_retained_syntax_and_json_evidence(self):
        for codec, (_, info) in self.results.items():
            with self.subTest(codec=codec):
                stream = Path(info['stream_path']).read_bytes()
                extra = Path(info['extradata_path']).read_bytes()
                self.assertEqual(info['coded_bytes'], len(stream) + len(extra))
                self.assertEqual(len(stream), sum(p['bytes'] for p in info['packets']))
                self.assertEqual(info['elementary_stream_sha256'], hashlib.sha256(stream).hexdigest())
                cursor = 0
                for packet in info['packets']:
                    data = stream[cursor:cursor + packet['bytes']]
                    self.assertEqual(packet['sha256'], hashlib.sha256(data).hexdigest())
                    cursor += packet['bytes']
                self.assertFalse(info['unconsumed_options'])
                self.assertEqual(info['inspection_returncode'], 0)
                self.assertTrue(Path(info['syntax_log_path']).read_text())
                self.assertTrue((Path(info['stream_path']).parent / 'ffmpeg-version.txt').exists())
                self.assertTrue(all(c['decode_ms'] >= 0 for c in info['decode_calls']))
                self.assertTrue(all(c['encode_call_ms'] >= 0 for c in info['frame_calls']))
                json.dumps(info, allow_nan=False)

    def test_common_sample_planes_are_copied_without_color_matrix_conversion(self):
        planes = sc.gm.ft.rgb_to_planes(self.frames[0])
        for pixel_format in ('yuv420p', 'yuvj420p'):
            native = sc.frame_from_planes(planes, 7, Fraction(1, 30), pixel_format)
            restored = sc.planes_from_frame(native)
            for expected, actual in zip(planes, restored):
                np.testing.assert_array_equal(actual, expected)
            self.assertEqual(native.pts, 7)
            self.assertEqual(native.color_range, 2)
        pins = {info['color_implementation_sha256'] for _, info in self.results.values()}
        self.assertEqual(len(pins), 1)

    def test_emitted_syntax_matches_tested_low_delay_and_jpeg_subsampling(self):
        hevc = self.results['hevc'][1]['inspection']['observed_syntax']
        self.assertEqual(hevc['sps_max_num_reorder_pics']['values'], [0])
        self.assertEqual(hevc['slice_type']['values'], [1, 2])
        av1 = self.results['av1'][1]['inspection']['observed_syntax']
        self.assertEqual(av1['show_existing_frame']['values'], [0])
        self.assertEqual(av1['show_frame']['values'], [1])
        self.assertEqual(av1['frame_type']['values'], [0, 1])
        jpeg = self.results['jpeg'][1]['inspection']['frames']
        self.assertEqual(len(jpeg), 3)
        for header in jpeg:
            self.assertEqual(header['sof_marker'], 'SOF0 baseline sequential')
            self.assertEqual((header['width'], header['height'], header['precision']), (720, 480, 8))
            self.assertEqual([(p['h'], p['v']) for p in header['sampling']], [(2, 2), (1, 1), (1, 1)])
            self.assertTrue(header['quantization_tables'])

    def test_reject_invalid_inputs_before_opening_encoder(self):
        for frames, codec, parameter, fps in (([], 'hevc', 32, 30),
                (self.frames, 'unknown', 32, 30), (self.frames, 'hevc', 32, 0),
                ([np.zeros((2, 2, 3), np.uint8)], 'hevc', 32, 30),
                (self.frames, 'jpeg', 0, 30), (self.frames, 'av1', 64, 30)):
            with self.subTest(codec=codec, parameter=parameter, fps=fps):
                with self.assertRaises(ValueError):
                    sc.run(frames, codec, parameter, fps=Fraction(fps))


if __name__ == '__main__':
    unittest.main()
