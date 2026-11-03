import unittest
import numpy as np
import roi_codec as rc


class LayoutCostTests(unittest.TestCase):
    def test_uniform_format_overhead_includes_map(self):
        rgb=np.full((32,48,3),100,np.uint8);mw,mh=rc.geometry(48,32)
        for scale in rc.SCALES:
            rg=rc.encode(rgb,np.full((mh,mw),scale,np.uint8))
            ft=rc.cc.encode(rgb,scale)
            np.testing.assert_array_equal(rc.decode(rg),rc.cc.decode(ft))
            # RG01 reuses exact CP02 coefficient payloads but replaces the
            # three FT02 plane descriptors with fixed outer lengths + map.
            self.assertEqual(len(rg)-len(ft),(mw*mh+3)//4-20)
        self.assertEqual((45*30+3)//4-20,318)


if __name__=='__main__':unittest.main()
