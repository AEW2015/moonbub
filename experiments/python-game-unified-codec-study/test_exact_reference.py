"""Supplemental untimed cross-profile YUV evidence; timed source stays frozen."""
import unittest
import numpy as np
import unified_codec as u


class CrossProfileTests(unittest.TestCase):
    def test_exact_gm_and_selected_sr_keep_identical_yuv_tags_across_promotions(self):
        rng=np.random.default_rng(1516)
        pairs=[(u.Encoder(mode=m),u.Receiver()) for m in ('gm','exact')]
        for i in range(14):
            source=(np.full((48,64,3),70+i,np.uint8) if i%2==0 else
                    rng.integers(50,180,(48,64,3),dtype=np.uint8))
            outputs=[]
            for enc,rx in pairs:
                d=enc.prepare(source,i,force_key=i==7,promote=i in (2,5,10))
                task=rx.begin(d.packet);outputs.append((task.planes,task.rgb))
                _,_,ack=rx.complete(task);enc.ack(ack)
            for left,right in zip(outputs[0][0],outputs[1][0]):np.testing.assert_array_equal(left,right)
            np.testing.assert_array_equal(outputs[0][1],outputs[1][1])
            for slot in (0,1):
                a,b=pairs[0][0].banks[slot],pairs[1][0].banks[slot]
                self.assertEqual(a is None,b is None)
                if a is not None:
                    self.assertEqual((a.frame_id,a.tag),(b.frame_id,b.tag))
                    for left,right in zip(a.planes,b.planes):np.testing.assert_array_equal(left,right)


if __name__=='__main__':unittest.main()
