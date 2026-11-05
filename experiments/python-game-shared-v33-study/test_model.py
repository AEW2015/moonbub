"""Small deterministic edge cases plus production encoder ownership checks."""
import unittest
import numpy as np
import helpers as h


class SharedPairTests(unittest.TestCase):
    def test_exact_packets_and_pixels(self):
        rng = np.random.default_rng(3307)
        for name in ('flat', 'dc', 'random', 'sparse'):
            if name == 'flat': source = tuple(np.full(shape,128,np.int16) for shape in ((32,32),(16,16),(16,16)))
            elif name == 'dc': source = tuple(np.full(shape,80,np.int16) for shape in ((32,32),(16,16),(16,16)))
            elif name == 'random': source = tuple(rng.integers(0,256,shape,dtype=np.int16) for shape in ((32,32),(16,16),(16,16)))
            else:
                source = tuple(np.full(shape,128,np.int16) for shape in ((32,32),(16,16),(16,16)))
                source[0][12:18,12:18] = 200
            ref = None
            for fid in (0,1):
                prepared = h.m.analyze_planes(source,ref,epoch=25,frame_id=fid,
                    reference_id=h.m.NO_REF if fid == 0 else 0,block_size=32,motion_mode='zero',motion_precision='half',penalty=0)
                for background in (8,16,32):
                    q = np.full((2,2),background,np.uint8)
                    for lam in (0,1,1000000):
                        with self.subTest(source=name,frame=fid,q=background,lam=lam):
                            old = (h.m.encode_prepared(prepared,q,lam),h.band.encode_with(h.m,prepared,q,lam,policy='band_strict'))
                            new = h.shared.encode_pair(h.m,prepared,q,lam)
                            for a,b in zip(old,new):
                                self.assertEqual(a[0],b[0])
                                for av,bv in zip(a[1],b[1]):
                                    np.testing.assert_array_equal(av,bv)
                                    self.assertFalse(bv.flags.writeable)
                            self.assertEqual(new[0][2]['shared_pair']['quantize_calls'],1)
                            self.assertEqual(new[1][2]['planes'],old[1][2]['planes'])
                            self.assertEqual(new[0][2]['rdo'],old[0][2]['rdo'])
                ref = new[0][1]

    def test_real_legacy_fallback_after_rdo_zero(self):
        # Both 129 and 130 quantize to DC=1 at q16. One 129 block can be
        # zeroed at no SSE cost, but its broken DC predictor raises legacy
        # bytes from 38 to 39. The original must win the fallback comparison.
        shapes = ((32,32),(16,16),(16,16))
        reference = tuple(np.full(shape,128,np.int16) for shape in shapes)
        source = tuple(np.full(shape,130,np.int16) for shape in shapes)
        source[0][:8,8:16] = 129
        p = h.m.analyze_planes(source,reference,epoch=25,frame_id=1,reference_id=0,
                              block_size=32,motion_mode='zero')
        q = np.full((2,2),16,np.uint8)
        old = h.old_pair(p,q)
        new = h.shared.encode_pair(h.m,p,q)
        self.assertTrue(old[0][2]['planes'][0]['rdo_reverted'])
        self.assertTrue(new[0][2]['planes'][0]['rdo_reverted'])
        for a,b in zip(old,new):
            self.assertEqual(a[0],b[0])
            for av,bv in zip(a[1],b[1]): np.testing.assert_array_equal(av,bv)
        self.assertEqual(new[0][2]['rdo'],old[0][2]['rdo'])

    def test_rejects_invalid_owner_lambda_and_map(self):
        q = np.full((2,2),16,np.uint8)
        with self.assertRaises(ValueError): h.shared.encode_pair(h.m,object(),q)
        source = tuple(np.full(shape,128,np.int16) for shape in ((32,32),(16,16),(16,16)))
        p = h.m.analyze_planes(source,None,epoch=25,frame_id=0,reference_id=h.m.NO_REF,block_size=32,motion_mode='zero')
        for lam in (True,-1,float('nan'),1000001):
            with self.assertRaises(ValueError): h.shared.encode_pair(h.m,p,q,lam)
        with self.assertRaises(ValueError): h.shared.encode_pair(h.m,p,q.astype(np.int16))


if __name__ == '__main__': unittest.main()
