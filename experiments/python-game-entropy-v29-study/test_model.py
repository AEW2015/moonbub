import unittest
import numpy as np
import model as m


class CounterTests(unittest.TestCase):
    def check(self,a,bw):
        before=a.copy()
        for layout in (0,1):
            plan=m.plan_coefficients(a,bw,layout=layout)
            packet=m.ec.encode_coefficients(a,bw,layout=layout)
            self.assertEqual(plan['bytes'],len(packet))
            np.testing.assert_array_equal(m.ec.decode_coefficients(packet,len(a),bw),a)
        np.testing.assert_array_equal(a,before)

    def test_zero_and_dc_rows(self):
        for blocks,bw in ((1,1),(16,4),(90,90)):
            a=np.zeros((blocks,8,8),np.int16);self.check(a,bw)
            a[:,0,0]=np.where(np.arange(blocks)%2,2048,-2048);self.check(a,bw)

    def test_seeded_dense_sparse(self):
        rng=np.random.default_rng(29)
        for blocks,bw in ((1,1),(32,8),(90,45),(256,16)):
            for density in (0.01,0.2,1.):
                a=rng.integers(-2048,2049,(blocks,8,8),dtype=np.int16)
                a[rng.random(a.shape)>density]=0;self.check(a,bw)

    def test_dense_domain_and_long_run_escape(self):
        rng=np.random.default_rng(19)
        a=rng.integers(-2048,2049,(128,8,8),dtype=np.int16)
        self.check(a,16);self.assertEqual(m.plan_coefficients(a,16)['raw'], bool(m.ec.COEFF.unpack_from(m.ec.encode_coefficients(a,16))[2]&1))
        a=np.zeros((2048,8,8),np.int16);a[-1,7,7]=-2048;self.check(a,64)

    def test_bad_inputs(self):
        good=np.zeros((4,8,8),np.int16)
        for a,bw in ((good.astype(np.int32),2),(good,3),(good,True),(good,0),(good,257),
                     (good[:0],1),(np.zeros((4,7,8),np.int16),2),(np.full((4,8,8),2049,np.int16),2)):
            with self.assertRaises(ValueError):m.count_coefficients(a,bw)
        for mode in (-1,2,True,'0'):
            with self.assertRaises(ValueError):m.count_coefficients(good,2,layout=mode)

    def test_owned_prepared_and_source_error_guard(self):
        rng=np.random.default_rng(7);shape=((32,32),(16,16),(16,16))
        source=tuple(rng.integers(0,256,s,dtype=np.int16) for s in shape)
        ref=tuple(rng.integers(0,256,s,dtype=np.int16) for s in shape)
        q=np.full((2,2),16,np.uint8)
        p=m.m.base.analyze_planes(source,ref,epoch=25,frame_id=1,reference_id=0,block_size=32,motion_mode='zero',motion_precision='half',penalty=0)
        old,baseline,_=m.m.encode_prepared(p,q)
        packet,out,work=m.encode_prepared(p,q)
        self.assertLessEqual(len(packet),len(old))
        decoded,_=m.m.decode(packet,ref,expected_epoch=25,expected_reference_id=0)
        for src,a,b,c in zip(source,baseline,out,decoded):
            np.testing.assert_array_equal(b,c)
            self.assertLessEqual(int(((src.astype(np.int64)-b)**2).sum()),int(((src.astype(np.int64)-a)**2).sum()))
        self.assertGreaterEqual(work['ec26_size_counter_calls'],3)
        self.assertTrue(work['source_yuv_sse_guard'])
        with self.assertRaises(ValueError):m.encode_prepared(object(),q)
        for invalid in (True,float('nan'),-1):
            with self.assertRaises(ValueError):m.encode_prepared(p,q,invalid)

if __name__=='__main__':unittest.main()
