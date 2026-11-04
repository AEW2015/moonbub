"""Independent coordinate/cost oracle and frozen receiver checks."""
import unittest
import numpy as np
import model as s


def source(seed=28, shape=(34,50)):
    rng = np.random.default_rng(seed)
    h,w = shape
    return tuple(rng.integers(0,256,shape,np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))


def scalar_cost(src, ref, vectors, bs, stride):
    out = np.zeros(vectors.shape[:2],np.int64)
    for plane,(a,b) in enumerate(zip(src,ref)):
        den = 2 if plane==0 else 4; block = bs if plane==0 else bs//2
        h,w = a.shape
        for y in range(0,h,stride):
            for x in range(0,w,stride):
                bx,by = x//block,y//block
                qx,qy = map(int,vectors[by,bx]); ix,fx = divmod(qx,den); iy,fy = divmod(qy,den)
                total = 0
                for ox,wx in ((0,den-fx),(1,fx)):
                    for oy,wy in ((0,den-fy),(1,fy)):
                        total += wx*wy*int(b[min(max(y+iy+oy,0),h-1),min(max(x+ix+ox,0),w-1)])
                pred = (total+den*den//2)//(den*den)
                out[by,bx] += (1 if plane==0 else 2)*abs(int(a[y,x])-pred)
    return out


class SearchTests(unittest.TestCase):
    def test_scalar_sampled_cost_partial_blocks_negative_clamp(self):
        src,ref = source(),source(29)
        rng = np.random.default_rng(30)
        for bs in (16,32):
            mw,mh = s.m.old._grid(50,34,bs)
            for stride in (2,4):
                vectors = rng.integers(-18,19,(mh,mw,2),np.int8)
                got = s._sampled_cost(s._samples(src,ref,bs,stride),vectors)
                np.testing.assert_array_equal(got,scalar_cost(src,ref,vectors,bs,stride))
                vectors = (vectors//4*4).clip(-16,16).astype(np.int8)
                got = s._sampled_cost(s._samples(src,ref,bs,stride),vectors,integer=True)
                np.testing.assert_array_equal(got,scalar_cost(src,ref,vectors,bs,stride))

    def test_tie_zero_bounds_work_and_no_input_mutation(self):
        src = tuple(np.full_like(v,128) for v in source())
        before = tuple(v.copy() for v in src)
        for policy,(cs,rs) in s.POLICIES.items():
            got,work = s.estimate_vectors(src,src,32,search_policy=policy)
            self.assertFalse(np.any(got))
            self.assertEqual(work['sad_sample_operations'],81*sum(v[::cs,::cs].size for v in src)+25*sum(v[::rs,::rs].size for v in src))
            self.assertEqual(work['reference_sample_fetches'],81*sum(v[::cs,::cs].size for v in src)+100*sum(v[::rs,::rs].size for v in src))
            self.assertEqual(work['candidate_block_cost_evaluations'],106*4)
        for a,b in zip(src,before): np.testing.assert_array_equal(a,b)
        src,ref = source(),source(29)
        for policy in s.POLICIES:
            got,_ = s.estimate_vectors(src,ref,32,search_policy=policy)
            self.assertLessEqual(int(np.max(np.abs(got))),18)

    def test_known_translation_and_half_translation(self):
        ref = source(shape=(64,64))
        for vector in ((4,-4),(1,-1),(-18,18)):
            expected = np.full((2,2,2),vector,np.int8)
            src = s.m.predict(ref,expected,32)
            for policy in s.POLICIES:
                got,work = s.estimate_vectors(src,ref,32,mode='global',search_policy=policy)
                np.testing.assert_array_equal(got,expected)

    def test_frozen_prepared_owner_decode_and_retained_immutable(self):
        src,ref = source(shape=(64,64)),source(29,shape=(64,64))
        saved = tuple(v.copy() for v in src+ref)
        qmap = s.m.roi.declared_map(64,64,(),8,16)
        for policy in s.POLICIES:
            prepared = s.analyze_with(s.m,src,ref,frame_id=2,reference_id=1,block_size=32,search_policy=policy)
            packet,expected,work = s.m.encode_prepared(prepared,qmap)
            got,meta = s.m.decode(packet,ref,expected_reference_id=1)
            for a,b in zip(got,expected): np.testing.assert_array_equal(a,b)
            self.assertTrue(all(not v.flags.writeable for v in prepared.prediction+prepared.raw_coefficients+prepared.source))
            for a,b in zip(src+ref,saved): np.testing.assert_array_equal(a,b)
            self.assertLessEqual(max(abs(int(v)) for v in s.m.unpack_vectors(prepared.vector_bytes,2,2).flat),18)
        for key in (True,False):
            p = s.analyze_planes(src,None if key else ref,frame_id=2,reference_id=s.m.NO_REF if key else 1,motion_mode='zero')
            self.assertEqual(p.work['search']['sad_sample_operations'],0)
            self.assertEqual(p.work['search']['reference_sample_fetches'],0)


if __name__=='__main__': unittest.main()
