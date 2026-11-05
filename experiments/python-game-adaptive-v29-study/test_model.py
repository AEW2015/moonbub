import unittest
import numpy as np
import model as s


def source(seed=29,shape=(34,50)):
    rng=np.random.default_rng(seed);h,w=shape
    return tuple(rng.integers(0,256,size=sh,dtype=np.int16) for sh in ((h,w),(h//2,w//2),(h//2,w//2)))


class AdaptiveTests(unittest.TestCase):
    def test_compact_full_matches_existing_partial_edge(self):
        src,ref=source(),source(30);rng=np.random.default_rng(31)
        for stride in (2,4):
            active=np.array(((True,False),(False,True)))
            vectors=rng.integers(-18,19,size=(2,2,2),dtype=np.int8)
            got=s.compact_cost(s.compact_samples(src,ref,32,stride,active),vectors)
            expected=s.oldsearch._sampled_cost(s.oldsearch._samples(src,ref,32,stride),vectors)
            np.testing.assert_array_equal(got[active],expected[active]);self.assertFalse(np.any(got[~active]))
            vectors=(vectors//4*4).clip(-16,16).astype(np.int8)
            got=s.compact_cost(s.compact_samples(src,ref,32,stride,active),vectors,True)
            expected=s.oldsearch._sampled_cost(s.oldsearch._samples(src,ref,32,stride),vectors,integer=True)
            np.testing.assert_array_equal(got[active],expected[active])

    def test_quiet_threshold_and_screen_counts(self):
        ref=tuple(np.full_like(v,100) for v in source())
        for delta,quiet in ((0,True),(2,True),(3,False)):
            src=tuple(v+delta for v in ref);vec,work=s.estimate_vectors(src,ref,32,search_policy='adaptive_zero2')
            self.assertFalse(np.any(vec));self.assertEqual(work['quiet_blocks'],4 if quiet else 0)
            expected=sum(v[::4,::4].size for v in src)
            self.assertEqual(work['screen_sample_operations'],expected)
            if quiet:self.assertEqual(work['sad_sample_operations'],expected)
            else:self.assertEqual(work['sad_sample_operations'],82*expected+25*sum(v[::2,::2].size for v in src))

    def test_active_all_matches_mixed_vectors_and_work(self):
        src,ref=source(),source(30)
        got,work=s.estimate_vectors(src,ref,32)
        expected,old=s.oldsearch.estimate_vectors(src,ref,32,search_policy='sample4_refine2')
        self.assertEqual(work['quiet_blocks'],0);np.testing.assert_array_equal(got,expected)
        self.assertEqual(work['sad_sample_operations'],old['sad_sample_operations']+work['screen_sample_operations'])

    def test_key_zero_decode_and_input_immutability(self):
        src,ref=source(shape=(64,64)),source(30,shape=(64,64));before=tuple(v.copy() for v in src+ref)
        q=s.m.roi.declared_map(64,64,(),8,16)
        for key in (False,True):
            p=s.analyze_with(s.m,src,None if key else ref,frame_id=2,reference_id=s.m.NO_REF if key else 1,block_size=32)
            packet,expected,_=s.m.encode_prepared(p,q)
            got,_=s.m.decode(packet,None if key else ref,expected_reference_id=None if key else 1)
            for a,b in zip(got,expected):np.testing.assert_array_equal(a,b)
            self.assertTrue(all(not v.flags.writeable for v in p.source+p.prediction+p.raw_coefficients))
        for a,b in zip(src+ref,before):np.testing.assert_array_equal(a,b)
        with self.assertRaises(ValueError):s.estimate_vectors(src,ref,32,search_policy='unknown')


if __name__=='__main__':unittest.main()
