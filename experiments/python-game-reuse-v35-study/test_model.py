import struct
import unittest
import numpy as np
import model as m

class ExactReuse(unittest.TestCase):
    def assert_exact(self, p, c, w, h):
        pb, cb = m.old.frozen.pack_vectors(p), m.old.frozen.pack_vectors(c)
        expected, oldinfo = m.old.pack(p, c, w, h, return_info=True)
        for kw in ({}, {'parent_bytes':pb}, {'child_bytes':cb}, {'parent_bytes':pb,'child_bytes':cb}):
            actual, info = m.pack(p,c,w,h,return_info=True,**kw)
            self.assertEqual(actual, expected)
            self.assertEqual(info['candidates'],oldinfo['candidates'])
            self.assertEqual(info['sparse_rice_parameters'],oldinfo['sparse_rice_parameters'])
            self.assertEqual(info['work']['hm34_candidates_costed'],3)
            self.assertEqual(info['work']['hm34_candidates_serialized'],1)
            np.testing.assert_array_equal(m.unpack(actual,w,h),c)
        return oldinfo

    def test_partial_empty_refinement_and_random_geometry(self):
        rng=np.random.default_rng(3501)
        for w,h in ((1,1),(16,16),(17,19),(32,32),(33,65),(720,480)):
            ps,cs=m.decoder.geometry(w,h)
            for style in range(3):
                p=rng.integers(-18,19,ps+(2,),dtype=np.int8)
                c=np.repeat(np.repeat(p,2,0),2,1)[:cs[0],:cs[1]].copy()
                if style==1:c=rng.integers(-18,19,cs+(2,),dtype=np.int8)
                if style==2:c[:]=0;p[:]=0
                self.assert_exact(p,c,w,h)

    def test_stable_ties(self):
        p=np.zeros((2,2,2),np.int8)
        c=np.zeros((3,3,2),np.int8);c[0,0]=2
        info=self.assert_exact(p,c,48,48)
        self.assertEqual([v['bytes'] for v in info['candidates']],[25,28,25])
        self.assertEqual(info['selected_mode'],0)

    def test_invalid_and_mismatched_caches(self):
        p=np.zeros((1,1,2),np.int8);c=np.zeros((2,2,2),np.int8)
        valid=m.old.frozen.pack_vectors(c)
        for data in (b'',b'\x07',bytearray(valid),valid+b'\0',b'\0\x7f\0',b'\x01'+bytes(8),b'\x03\0\0'+struct.pack('<Hbb',0,0,0)):
            with self.subTest(data=data):
                with self.assertRaises(ValueError):m.pack(p,c,32,32,child_bytes=data)
        c[0,0]=1
        with self.assertRaises(ValueError):m.pack(p,c,32,32,child_bytes=valid)

    def test_nonminimal_valid_and_equal_length_default(self):
        p=np.zeros((1,1,2),np.int8);c=np.zeros((2,2,2),np.int8)
        dense=b'\x01'+c.tobytes()
        np.testing.assert_array_equal(m.decoder.unpack_gm27(dense,2,2),c)
        with self.assertRaisesRegex(ValueError,'noncanonical'):m.pack(p,c,32,32,child_bytes=dense)
        # Same canonical mode and length but a noncanonical sparse default.
        c=np.zeros((8,8,2),np.int8);c[:4]=1;p=np.zeros((4,4,2),np.int8)
        # Split identical runs: syntax-valid, equality checked, mode/size rejected.
        run=b'\x02'+struct.pack('<Hbb',16,0,0)+struct.pack('<Hbb',16,0,0)+struct.pack('<Hbb',32,1,1)
        field=m.decoder.unpack_gm27(run,8,8)
        np.testing.assert_array_equal(field.reshape(-1,2)[:32],np.zeros((32,2),np.int8))
        with self.assertRaisesRegex(ValueError,'noncanonical'):m.pack(p,field,128,128,child_bytes=run)

    def test_field_and_geometry_validation(self):
        p=np.zeros((1,1,2),np.int8);c=np.zeros((2,2,2),np.int8)
        for w,h in ((0,32),(721,32),(32,481),(True,32)):
            with self.assertRaises(ValueError):m.pack(p,c,w,h)
        for a in (p.astype(np.int16),np.zeros((1,1,3),np.int8),np.full((1,1,2),19,np.int8)):
            with self.assertRaises(ValueError):m.pack(a,c,32,32)

    def test_canonical_planner_modes_and_rice_ties(self):
        rng=np.random.default_rng(3503)
        uniform=np.zeros((8,8,2),np.int8)
        runs=uniform.copy();runs[:4]=1;runs[4:]=2
        sparse=uniform.copy();sparse[3,3]=18
        packed=rng.integers(-18,19,(8,8,2),dtype=np.int8)
        left=np.cumsum(rng.integers(-1,2,(8,8,2)),axis=1).clip(-18,18).astype(np.int8)
        median=np.cumsum(rng.integers(-3,4,(8,8,2)),axis=0).clip(-18,18).astype(np.int8)
        modes=set()
        for field in (uniform,runs,sparse,packed,left,median):
            data,work=m.old.frozen.pack_vectors(field,return_work=True)
            _,plan=m._validated_cache(data,field,'test')
            modes.add(data[0]);self.assertEqual(plan['mode'],data[0])
            if data[0]:self.assertEqual(plan['costs'],[c['bytes'] for c in work['candidates']])
        self.assertEqual(modes,{0,2,3,4,5,6})
        canonical=m.old.frozen.pack_vectors(left)
        self.assertEqual(canonical[0],5)
        ks=[(canonical[1]+1)%7,canonical[2]]
        combined=m.old.frozen._Bits()
        for axis,k in enumerate(ks):
            delta=m.old.frozen._motion_deltas(left.reshape(-1,2),8,axis,5)
            combined.bits.extend(m.old.frozen._rice_axis(delta,k).bits)
        alternate=bytes((5,*ks))+combined.finish()
        np.testing.assert_array_equal(m.decoder.unpack_gm27(alternate,8,8),left)
        with self.assertRaisesRegex(ValueError,'Rice parameters'):
            m._validated_cache(alternate,left,'test')

    def test_cache_never_calls_frozen_pack(self):
        from unittest.mock import patch
        p=np.zeros((1,1,2),np.int8);c=np.zeros((2,2,2),np.int8)
        parent_bytes=m.old.frozen.pack_vectors(p)
        child_bytes=m.old.frozen.pack_vectors(c)
        expected=m.old.pack(p,c,32,32)
        original_pack=m.old.frozen.pack_vectors
        with patch.object(m.old.frozen,'pack_vectors',side_effect=AssertionError('cached pack called frozen encoder')):
            actual,info=m.pack(p,c,32,32,parent_bytes=parent_bytes,child_bytes=child_bytes,return_info=True)
        self.assertIs(m.old.frozen.pack_vectors,original_pack)
        self.assertEqual(actual,expected)
        self.assertEqual(info['work']['frozen_pack_vectors_calls'],0)

if __name__=='__main__':unittest.main()
