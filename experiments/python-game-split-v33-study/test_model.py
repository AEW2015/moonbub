import unittest
import numpy as np
import helpers as h


class SplitMotionTests(unittest.TestCase):
    def test_parent_mapping_and_partial_edges(self):
        p=np.arange(15*23*2,dtype=np.int16).reshape(15,23,2)%37-18
        out=h.split.seed16(p.astype(np.int8),720,480)
        self.assertEqual(out.shape,(30,45,2))
        for y in range(30):
            for x in range(45):np.testing.assert_array_equal(out[y,x],p[y//2,x//2])
        self.assertEqual(h.split.seed16(np.zeros((2,2,2),np.int8),34,50).shape,(4,3,2))
        with self.assertRaises(ValueError):h.split.seed16(np.full((1,1,2),19,np.int8),32,32)

    def test_bounds_quiet_and_exact_sampler(self):
        rng=np.random.default_rng(3309)
        ref=tuple(rng.integers(0,256,s,dtype=np.int16) for s in ((50,34),(25,17),(25,17)))
        seed=np.full((2,2,2),18,np.int8)
        vec,work=h.split.refine(h.adaptive,ref,ref,seed)
        self.assertFalse(np.any(vec));self.assertEqual(work['candidate_maps'],1)
        src=tuple(np.roll(a,1,axis=1) for a in ref)
        vec,work=h.split.refine(h.adaptive,src,ref,seed)
        self.assertLessEqual(int(np.abs(vec.astype(np.int16)).max()),18)
        prediction=h.m.taps.predict(ref,vec,16)
        total=0
        for plane,(s,p) in enumerate(zip(src,prediction)):
            total+=(1 if plane==0 else 2)*int(np.abs(s[::2,::2].astype(np.int64)-p[::2,::2]).sum())
        self.assertEqual(total,work['selected_sampled_weighted_sad'])

    def test_owned_partial_geometry_key_and_p_decode(self):
        rng=np.random.default_rng(3310)
        source=tuple(rng.integers(0,256,s,dtype=np.int16) for s in ((50,34),(25,17),(25,17)))
        ref=None
        for fid in (0,1):
            p=h.adaptive.analyze_with(h.m.base,source,ref,epoch=25,frame_id=fid,
                reference_id=h.m.NO_REF if fid==0 else 0,block_size=32,motion_mode='block',motion_precision='half')
            child=h.split.analyze16(h.m,h.adaptive,p,ref)
            q=np.full((4,3),16,np.uint8)
            packet,pixels,_=h.band.encode_with(h.m,child,q,policy='band_strict')
            decoded,meta=h.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if fid==0 else 0)
            self.assertEqual(meta['block_size'],16)
            for a,b in zip(pixels,decoded):np.testing.assert_array_equal(a,b)
            ref=decoded


if __name__=='__main__':unittest.main()
