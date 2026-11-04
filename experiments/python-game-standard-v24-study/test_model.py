import unittest
import av
import numpy as np
import model as m


class StandardComparisonTests(unittest.TestCase):
    def test_common_planes_preserve_padding_and_extremes(self):
        planes = (np.arange(6400, dtype=np.int16).reshape(64, 100) % 256,
                  np.zeros((32, 50), np.int16), np.full((32, 50), 255, np.int16))
        frame = m.frame_from_planes(planes, 0)
        restored = m.planes_from_frame(frame)
        for a, b in zip(planes, restored):
            np.testing.assert_array_equal(a, b)
        self.assertEqual(frame.color_range, 2)

    def test_invalid_planes_and_decoded_layout_fail(self):
        planes = (np.zeros((64, 128), np.int16),) * 3
        with self.assertRaises(ValueError):
            m.frame_from_planes(planes, 0)
        with self.assertRaises(ValueError):
            m.planes_from_frame(av.VideoFrame(128, 64, 'yuv420p10le'))
        planes = (np.zeros((64, 128), np.int16), np.zeros((32, 64), np.int16), np.full((32, 64), 256, np.int16))
        with self.assertRaises(ValueError):
            m.frame_from_planes(planes, 0)

    def test_metric_and_exact_overlay(self):
        source = np.zeros((480, 720), np.uint16)
        changed = source.copy()
        for x, y, w, h in m.RECTANGLES:
            changed[y:y+h, x:x+w] = 65535
        before = m.metric(source, changed)
        self.assertEqual(before['hud_word_errors'], 21120)
        patches = tuple(np.zeros((h, w), np.uint16) for x, y, w, h in m.RECTANGLES)
        after = m.overlay(changed, patches)
        self.assertEqual(m.metric(source, after)['active_mse'], 0)
        self.assertEqual(m.metric(source, after)['hud_word_errors'], 0)
        self.assertEqual(before['active_channel_samples'], 874800)

    def test_options_and_quality_domains(self):
        self.assertIn('zerolatency', m.options('libx265', 28)['tune'])
        self.assertIn('pred-struct=1', m.options('libsvtav1', 38)['svtav1-params'])
        for name, q in (('bad', 28), ('libx265', 52), ('libx265', -1), ('libsvtav1', True)):
            with self.assertRaises(ValueError):
                m.options(name, q)

    def test_full_accounting_and_cap(self):
        a = m.accounting(1008)
        self.assertEqual((a['fragments'], a['forward_data_ip_udp_bytes']), (1, 1083))
        hybrid = m.accounting(1008, 200, binding=True)
        self.assertEqual(hybrid['body_bytes'], 1265)
        self.assertEqual(hybrid['fragments'], 2)
        self.assertTrue(m.accounting(49152)['under_complete_cap'])
        self.assertFalse(m.accounting(49153)['under_complete_cap'])

    def test_native_hevc_association_and_immediate_emission(self):
        self._native('libx265', 28)

    def test_native_av1_association_and_immediate_emission(self):
        self._native('libsvtav1', 38)

    def _native(self, name, q):
        rgb = [np.full((64, 128, 3), 60 + i, np.uint8) for i in range(3)]
        planes = [m.C.gm.ft.rgb_to_planes(a) for a in rgb]
        packets, extra, info = m.encode(planes, name, q)
        outputs, dec = m.decode(packets, extra, name)
        self.assertEqual(sorted(outputs), [0, 1, 2])
        self.assertEqual([p['pts'] for p in packets], [0, 1, 2])
        self.assertEqual([p['dts'] for p in packets], [0, 1, 2])
        self.assertEqual([p['pts'] for p in packets if p['is_key']], [0])
        self.assertEqual(info['packets_only_at_flush'], 0)
        self.assertEqual(dec['frames_only_at_decode_flush'], 0)
        self.assertEqual([c['emitted_pts'] for c in info['frame_calls']], [[0], [1], [2]])


if __name__ == '__main__':
    unittest.main()
