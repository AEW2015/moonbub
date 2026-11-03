import unittest
import numpy as np
import common_color as c


class CommonColorTests(unittest.TestCase):
    def test_padded_rows_preserve_full_range_sample_planes(self):
        rng=np.random.default_rng(1009)
        for w,h in ((34,18),(720,480)):
            planes=tuple(rng.integers(0,256,(ph,pw),dtype=np.uint8) for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2)))
            frame=c.frame_from_planes(planes,7)
            self.assertEqual(frame.pts,7);self.assertEqual(frame.color_range,2)
            for expected,actual in zip(planes,c.planes_from_frame(frame)):
                np.testing.assert_array_equal(actual,expected)

    def test_reject_chroma_layout_change(self):
        frame=c.av.VideoFrame(34,18,'yuv444p')
        with self.assertRaises(ValueError):c.planes_from_frame(frame)


if __name__=='__main__':unittest.main()
