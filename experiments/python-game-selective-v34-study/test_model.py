import unittest
import numpy as np
import helpers as h


def planes(height=64,width=96,seed=34):
    rng=np.random.default_rng(seed)
    return tuple(rng.integers(0,256,s,dtype=np.int16) for s in
                 ((height,width),(height//2,width//2),(height//2,width//2)))


class SelectiveTests(unittest.TestCase):
    def test_parent_mapping_partial_edges(self):
        p=(np.arange(15*23*2).reshape(15,23,2)%37-18).astype(np.int8)
        out=h.selective.seed16(p,720,480)
        self.assertEqual(out.shape,(30,45,2))
        for y in range(30):
            for x in range(45):np.testing.assert_array_equal(out[y,x],p[y//2,x//2])
        self.assertEqual(h.selective.seed16(np.zeros((2,2,2),np.int8),34,50).shape,(4,3,2))
        with self.assertRaises(ValueError):h.selective.seed16(np.full((1,1,2),19,np.int8),32,32)

    def test_quota_quiet_determinism_and_parent_inheritance(self):
        ref=planes(64,96)
        p=np.full((2,3,2),2,np.int8)
        source=h.m.taps.predict(ref,p,32)
        for budget,expected in ((25,2),(50,3)):
            out,w=h.selective.refine(h.adaptive,source,ref,p,budget=budget)
            np.testing.assert_array_equal(out,h.selective.seed16(p,96,64))
            self.assertEqual(w['selected_groups'],expected)
            self.assertEqual(w['active_groups'],0)
            self.assertEqual(w['candidate_maps'],1)
            self.assertEqual(np.flatnonzero(np.array(w['selected_group_mask'])).tolist(),list(range(expected)))
            out2,w2=h.selective.refine(h.adaptive,source,ref,p,budget=budget)
            self.assertEqual(w['group_scores'],w2['group_scores'])
            np.testing.assert_array_equal(out,out2)

    def test_known_shift_and_explicit_mask(self):
        ref=planes(64,96)
        p=np.zeros((2,3,2),np.int8)
        target=np.full((4,6,2),1,np.int8)
        source=h.m.taps.predict(ref,target,16)
        mask=np.array([[True,False,False],[False,False,False]])
        out,w=h.selective.refine(h.adaptive,source,ref,p,mask=mask)
        np.testing.assert_array_equal(out[:2,:2],target[:2,:2])
        childmask=np.repeat(np.repeat(mask,2,axis=0),2,axis=1)
        self.assertFalse(np.any(out[~childmask]))
        self.assertEqual(w['active_groups'],1)
        self.assertEqual(w['candidate_maps'],26)
        self.assertGreater(w['reference_sample_fetches'],w['source_sample_fetches'])

    def test_unselected_inheritance_bounded_edges(self):
        ref=planes(50,34)
        src=planes(50,34,35)
        p=np.full((2,2,2),18,np.int8)
        out,w=h.selective.refine(h.adaptive,src,ref,p,budget=25)
        selected=np.array(w['selected_group_mask'],bool)
        child=np.repeat(np.repeat(selected,2,axis=0),2,axis=1)[:4,:3]
        np.testing.assert_array_equal(out[~child],h.selective.seed16(p,34,50)[~child])
        self.assertLessEqual(int(np.abs(out.astype(np.int16)).max()),18)

    def test_invalid_inputs(self):
        ref=planes();p=np.zeros((2,3,2),np.int8)
        for budget in (0,24,26,100,25.,True,None):
            with self.assertRaises(ValueError):h.selective.refine(h.adaptive,ref,ref,p,budget=budget)
        for mask in (np.ones((2,3),np.int8),np.zeros((1,3),bool)):
            with self.assertRaises(ValueError):h.selective.refine(h.adaptive,ref,ref,p,mask=mask)
        with self.assertRaises(ValueError):h.selective.analyze16(h.m,h.adaptive,object(),None)

    def test_owned_partial_key_p_actual_decode(self):
        src=planes(50,34);ref=None
        for fid in (0,1):
            parent=h.adaptive.analyze_with(h.m.base,src,ref,epoch=25,frame_id=fid,
                reference_id=h.m.NO_REF if fid==0 else 0,block_size=32,motion_mode='block',motion_precision='half')
            for budget in (25,50):
                child=h.selective.analyze16(h.m,h.adaptive,parent,ref,budget=budget)
                self.assertIs(child.owner,h.m._PREPARED_OWNER)
                self.assertTrue(all(not a.flags.writeable for a in child.prediction+child.raw_coefficients))
                q=np.full((4,3),16,np.uint8)
                for encode in (lambda:h.m.encode_prepared(child,q),lambda:h.band.encode_with(h.m,child,q,policy='band_strict')):
                    packet,pixels,work=encode()
                    decoded,meta=h.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if fid==0 else 0)
                    self.assertEqual(meta['block_size'],16)
                    for a,b in zip(pixels,decoded):np.testing.assert_array_equal(a,b)
            if fid:
                with self.assertRaises(ValueError):h.selective.analyze16(h.m,h.adaptive,parent,tuple(a+1 for a in ref))
            ref=decoded


if __name__=='__main__':unittest.main()
