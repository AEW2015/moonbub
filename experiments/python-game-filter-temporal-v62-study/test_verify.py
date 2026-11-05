"""Normative threshold/rounding/order/exclusion and preset-selection checks."""
import copy,unittest
import numpy as np
import verify as v
frozen=v.module('filter62_frozen60_subject',v.FILTER/'model.py')

class DisplayFilterProofTests(unittest.TestCase):
    def guard(self):return np.zeros((480,720),bool)
    def test_edge_rounding_and_blocked_four_sample_footprint(self):
        plane=np.full((480,720),108,np.uint8);plane[:,:8]=100;original=plane.copy()
        out,work=v.oracle_filter(plane,self.guard(),v.STRONG)
        np.testing.assert_array_equal(plane,original);self.assertEqual((int(out[4,7]),int(out[4,8])),(102,106));self.assertEqual(work['vertical_changed_edges'],480)
        excluded=self.guard();excluded[4,6]=True;out,work=v.oracle_filter(plane,excluded,v.STRONG)
        self.assertEqual((int(out[4,7]),int(out[4,8])),(100,108));self.assertEqual(work['vertical_changed_edges'],479)
    def test_inclusive_threshold_and_signed_floor_rounding(self):
        p=np.full((480,720),148,np.uint8);p[:,:7]=100;p[:,7]=112;p[:,8]=136
        out,_=v.oracle_filter(p,self.guard(),v.STRONG);self.assertEqual((int(out[0,7]),int(out[0,8])),(115,133))
        p[:,6]=99;out,_=v.oracle_filter(p,self.guard(),v.STRONG);self.assertEqual((int(out[0,7]),int(out[0,8])),(112,136))
        p=np.full((480,720),102,np.uint8);p[:,:8]=110
        out,_=v.oracle_filter(p,self.guard(),v.STRONG);self.assertEqual((int(out[0,7]),int(out[0,8])),(108,104))
    def test_full_plane_oracle_matches_frozen_model_on_dense_edges(self):
        rng=np.random.default_rng(62000);plane=rng.integers(90,115,(480,720),np.uint8);excluded=rng.random(plane.shape)<.05
        before=plane.copy();a,aw=v.oracle_filter(plane,excluded,v.STRONG);b,bw=frozen.filtered_luma(plane,excluded,v.STRONG)
        np.testing.assert_array_equal(a,b);self.assertEqual(aw,bw);np.testing.assert_array_equal(plane,before);self.assertFalse(a.flags.writeable)
    def test_identity_and_exact_preset_domain(self):
        plane=np.arange(480*720,dtype=np.uint32).reshape(480,720).astype(np.uint8)
        result,work=v.oracle_filter(plane,self.guard(),v.IDENTITY);np.testing.assert_array_equal(result,plane);self.assertEqual(work['changed_luma_samples'],0)
        changed=dict(v.STRONG,strength=4)
        with self.assertRaises(ValueError):v.oracle_filter(plane,self.guard(),changed)
        with self.assertRaises(ValueError):v.oracle_filter(plane.astype(np.int16),self.guard(),v.STRONG)
    def test_only_four_zero_prefixes_select_the_frozen_preset(self):
        calibration=v.check_calibration();self.assertEqual(calibration['selected_preset'],v.STRONG);self.assertEqual(calibration['source_IDs'],list(range(24)))
    def test_native_choice_is_cap_fit_matched_SSE_then_bytes_SSE_parameter(self):
        def case(q,b,sse,cap=0):return dict(scene='scene',codec='codec',parameter=q,supported=True,summary=dict(cap_failures=cap,active_channel_samples=100,active_squared_error=sse,complete_bytes=b))
        cases=[case(1,100,100),case(2,90,101),case(3,80,90,1),case(4,100,90),case(5,100,90)]
        self.assertEqual(v.select_native(cases,'scene','codec',100,100)['parameter'],4)
        before=copy.deepcopy(cases);v.select_native(cases,'scene','codec',100,100);self.assertEqual(cases,before)
        with self.assertRaises(ValueError):v.select_native(cases,'scene','codec',0,100)

if __name__=='__main__':unittest.main()
