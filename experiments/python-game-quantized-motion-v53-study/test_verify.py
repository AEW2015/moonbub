"""Independent MB geometry, hidden support, actual MV assembly and final guard."""
from dataclasses import replace
import json,unittest
import numpy as np
import verify as v

class QuantizedMotionProofTests(unittest.TestCase):
    def constant(self):
        source=tuple(np.full(s,128,np.int16)for s in((480,720),(240,360),(240,360)))
        prep=v.proof.preparation(source,None,0,v.m.NO_REF,'zero');q=v.m.roi.declared_map(720,480,v.n.ROIS,8,16)
        return source,prep,q
    def test_partial_right_macroblock_has_twelve_visible_blocks(self):
        source,prep,q=self.constant();cost=v.mb_costs(source,prep,q)
        self.assertEqual(v.fine.scalar_fine_bits(np.zeros((8,8),np.int16)),35)
        self.assertEqual(cost[14,0,1],24*35);self.assertEqual(cost[14,22,1],12*35)
        visible=sum(int((~safe).sum())for safe in v.f.f.safe_blocks())
        self.assertEqual(int(cost[...,1].sum()),visible*35);self.assertFalse(cost[...,0].any());self.assertFalse(cost[...,2].any())
    def test_hidden_sample_error_and_coefficients_are_excluded(self):
        source,prep,q=self.constant();baseline=v.mb_costs(source,prep,q);changed=[]
        for c,safe in zip(prep.raw_coefficients,v.f.f.safe_blocks(),strict=True):
            copied=c.copy();copied[safe.reshape(-1),0,0]=2040;changed.append(copied)
        np.testing.assert_array_equal(v.mb_costs(source,replace(prep,raw_coefficients=tuple(changed)),q),baseline)
    def test_MB_selectors_account_for_motion_charge_and_strict_ties(self):
        cost=np.zeros((15,23,2,3),np.int64);a,b=v.selectors(cost);self.assertFalse(a.any());self.assertFalse(b.any())
        cost[0,0,0,0]=100;cost[0,0,1,2]=16 # lambda4score64 beats100, but SSE/bitsPareto fails
        cost[0,1,0,0]=100;cost[0,1,0,1]=20;cost[0,1,1,0]=99;cost[0,1,1,1]=19
        cost[0,2,0,0]=10;cost[0,2,1,0]=10;cost[0,2,1,2]=16
        a,b=v.selectors(cost)
        self.assertEqual((int(a[0,0]),int(b[0,0])),(1,0));self.assertEqual((int(a[0,1]),int(b[0,1])),(1,1));self.assertEqual((int(a[0,2]),int(b[0,2])),(0,0))
        with self.assertRaises(ValueError):v.selectors(cost.astype(np.float64))
    def test_checkerboard_mixed_map_equals_real_prediction_and_forward(self):
        folder=v.proof.BINARY;gold=json.loads((folder/'results.json').read_text())['cases'][0]['rows'][0]
        rx=v.direct.Receiver();rx.receive(v.raw(gold['packet'],folder))
        manifest=json.loads((v.proof.SOURCE/'manifest.json').read_text());src=manifest['cases'][0]['frames'][1]
        canvas=np.frombuffer(v.raw(src['canvas_rgb24'],v.proof.SOURCE),np.uint8).reshape(480,720,3)
        source=tuple(np.asarray(p,np.int16)for p in v.m.ft.rgb_to_planes(canvas));zero=v.proof.preparation(source,rx.ref,1,0,'zero')
        vectors=np.full((15,23,2),4,np.int8);prediction=v.m.predict(rx.ref,vectors,32)
        grid=replace(zero,prediction=prediction,raw_coefficients=v.m.base.old._forward(source,prediction),vector_bytes=v.m.base.pack_vectors(vectors))
        y,x=np.indices((15,23));choice=((y+x)%2).astype(np.uint8)
        mixed,actual=v.materialize(source,rx.ref,zero,grid,choice)
        np.testing.assert_array_equal(actual,np.where(choice[...,None]!=0,vectors,0))
        np.testing.assert_array_equal(v.m.base.unpack_vectors(mixed.vector_bytes,23,15),actual)
        self.assertEqual(mixed.prediction[0].shape,(480,720));self.assertEqual(mixed.raw_coefficients[0].shape,(5400,8,8))
    def test_final_guard_ties_byte_SSE_and_stable_candidate_order(self):
        self.assertEqual(v.choose(dict(zero=(b'aaa',10),mixed_score4=(b'bbb',10),mixed_pareto=(b'ccc',10))),'zero')
        self.assertEqual(v.choose(dict(zero=(b'aaaa',10),mixed_score4=(b'bbb',9),mixed_pareto=(b'cc',10))),'mixed_pareto')
        self.assertEqual(v.choose(dict(zero=(b'aaaa',10),mixed_score4=(b'bb',9),mixed_pareto=(b'cc',8))),'mixed_pareto')
        self.assertEqual(v.choose(dict(zero=(b'aaaa',10),mixed_score4=(b'bb',8),mixed_pareto=(b'cc',8))),'mixed_score4')
        self.assertEqual(v.choose(dict(zero=(b'aaa',10),mixed_score4=(b'b',11),mixed_pareto=(b'cccc',9))),'zero')
    def test_final_cap_and_exact_integer_domain(self):
        self.assertIsNone(v.choose(dict(zero=(b'z'*49153,10),mixed_score4=(b'g'*49152,11),mixed_pareto=(b'g'*49153,9))))
        self.assertEqual(v.choose(dict(zero=(b'z'*49153,10),mixed_score4=(b'g'*49152,10),mixed_pareto=(b'g'*49153,9))),'mixed_score4')
        with self.assertRaises(ValueError):v.choose(dict(zero=(b'z',True),mixed_score4=(b'g',0),mixed_pareto=(b'g',0)))

if __name__=='__main__':unittest.main()
