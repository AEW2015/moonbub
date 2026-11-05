"""Exact mixed-Prepared assembly, partial cells, fine proxy and final guard."""
import unittest
import numpy as np
import helpers as h
model=h.bound('quantmotion53_owned_tests',h.HERE/'model.py',h)

def fixture():
    frames=h.load(h.SOURCE/'manifest.json')['cases'][0]['frames'];golden=h.load(h.GOLDEN/'results.json')['cases'][0]['rows'][0]
    reference=h.rx.Receiver().receive(h.raw(golden['packet'],h.GOLDEN))[0]
    canvas=np.frombuffer(h.raw(frames[1]['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy()
    return tuple(v.astype(np.int16)for v in h.m.ft.rgb_to_planes(canvas)),reference

class QuantizedMotionTests(unittest.TestCase):
    def test_mixed_raw_and_prediction_equal_materialized_MV_analysis_including_right_edge(self):
        source,reference=fixture();zero,grid,q,costs,maps,vectors,work=model.prepare(source,reference,frame_id=1,reference_id=0)
        yy,xx=np.mgrid[:15,:23];choice=((yy+xx)%2).astype(bool);mixed,actual,mw=model.mix(zero,grid,choice,vectors)
        expected=h.m.predict(reference,actual,32);raw=h.m.base.old._forward(source,expected)
        for a,b in zip(mixed.prediction,expected,strict=True):np.testing.assert_array_equal(a,b);self.assertFalse(a.flags.writeable)
        for a,b in zip(mixed.raw_coefficients,raw,strict=True):np.testing.assert_array_equal(a,b);self.assertFalse(a.flags.writeable)
        for a,b,c in zip(mixed.source,zero.source,source,strict=True):np.testing.assert_array_equal(a,c);self.assertFalse(np.shares_memory(a,b));self.assertFalse(a.flags.writeable)
        self.assertIs(mixed.owner,h.m._PREPARED_OWNER);self.assertEqual(mw['repeated_forward_plane_calls'],0)
        blocks=sum(int(np.count_nonzero(model.geometry(axis)[1]==5*23+22))for axis in range(3));self.assertEqual(blocks,12)
        np.testing.assert_array_equal(maps['mixed_score4'],costs[:,:,1,0]+4*costs[:,:,1,1:].sum(2)<costs[:,:,0,0]+4*costs[:,:,0,1:].sum(2))
    def test_proxy_distinguishes_coarse_byte_tie_and_motion_charge(self):
        a=np.zeros((2,8,8),np.int16);a[0,0,0]=-29
        self.assertEqual(model.fine.coefficient_bits(a).tolist(),[41,35])
        source,reference=fixture();z,g,q,costs,maps,vectors,work=model.prepare(source,reference,frame_id=1,reference_id=0)
        np.testing.assert_array_equal(costs[:,:,0,2],0);np.testing.assert_array_equal(costs[:,:,1,2],16*np.any(vectors!=0,axis=2))
        b=costs[:,:,1];a=costs[:,:,0];xb=b[:,:,1:].sum(2);xa=a[:,:,1:].sum(2)
        np.testing.assert_array_equal(maps['mixed_pareto'],(b[:,:,0]<=a[:,:,0])&(xb<=xa)&((b[:,:,0]<a[:,:,0])|(xb<xa)))
    def test_actual_whole_guard_and_stable_order_ties(self):
        with self.assertRaises(ValueError):model.choose({'zero':(100.,50),'mixed_score4':(99,50),'mixed_pareto':(99,50)})
        self.assertEqual(model.choose({'zero':(100,50),'mixed_score4':(99,50),'mixed_pareto':(99,50)}),'mixed_score4')
        self.assertEqual(model.choose({'zero':(100,50),'mixed_score4':(99,51),'mixed_pareto':(100,50)}),'zero')
        self.assertEqual(model.choose({'zero':(100,50),'mixed_score4':(100,49),'mixed_pareto':(99,50)}),'mixed_pareto')
        self.assertIsNone(model.choose({'zero':(49153,50),'mixed_score4':(49152,51),'mixed_pareto':(49153,49)}))

if __name__=='__main__':unittest.main()
