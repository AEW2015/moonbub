import unittest
import numpy as np
import model as m


class LazyTests(unittest.TestCase):
    def test_legacy_exact_sizes_and_bytes_all_modes(self):
        rng=np.random.default_rng(28)
        zero=np.zeros((8,8,8),np.int16);dc=zero.copy();dc[:,0,0]=np.arange(-4,4)
        sparse=rng.integers(-20,21,zero.shape,dtype=np.int16);sparse[rng.random(zero.shape)<.95]=0
        dense=rng.integers(-2048,2049,zero.shape,dtype=np.int16)
        for coeff in (zero,dc,sparse,dense):
            old,_=m.base.old._encode_plane(coeff,4);plan=m.legacy_plan(coeff,4);new,_,_=m.build_legacy(coeff,4,plan)
            self.assertEqual(plan['bytes'],len(old));self.assertEqual(new,old)

    def test_same_prepared_exact_gm27_wire_and_references(self):
        rng=np.random.default_rng(2801);ref=None;original_skip=m.base._rdo_skip
        for fid in range(4):
            src=tuple(m.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),dtype=np.uint8)))
            q=m.roi.declared_map(64,64,(),8,16)
            p=m.base.analyze_planes(src,ref,frame_id=fid,reference_id=m.NO_REF if fid==0 else fid-1,block_size=32,motion_mode='zero' if fid==0 else 'block')
            a,x,_=m.base.encode_prepared(p,q,rdo_lambda=1);b,y,_=m.encode_prepared(p,q,rdo_lambda=1)
            self.assertEqual(a,b)
            for c,d in zip(x,y):np.testing.assert_array_equal(c,d)
            ref=y
        self.assertIs(m.base._rdo_skip,original_skip)

    def test_nonzero_sparse_crc_raw_bounds(self):
        a=np.zeros((3,8,8),np.int16);a[0,0,0]=1;a[2,7,7]=-1
        p=m.legacy_plan(a,1);data,_,_=m.build_legacy(a,1,p)
        np.testing.assert_array_equal(m.base.old._decode_plane(data,3,1),a)
        with self.assertRaises(ValueError):m.legacy_plan(a.astype(np.float64),1)

    def test_tap_counts_equal_instrumented_prediction_and_decode(self):
        src=tuple(m.ft.rgb_to_planes(np.random.default_rng(282).integers(0,256,(64,64,3),dtype=np.uint8)))
        q=m.roi.declared_map(64,64,(),8,16)
        key,ref,_=m.base.encode_planes(src,None,q)
        for mode in ('zero','block'):
            p=m.base.analyze_planes(src,ref,epoch=1,frame_id=1,reference_id=0,block_size=32,motion_mode=mode)
            vectors=m.base.unpack_vectors(p.vector_bytes,2,2)
            _,work=m.taps.predict_with_info(ref,vectors,32)
            self.assertEqual(m.decoder_tap_counts(p)['reference_sample_fetches'],work['reference_sample_fetches'])
            packet,expected,_=m.encode_prepared(p,q)
            actual,_=m.decode(packet,ref,expected_epoch=1,expected_reference_id=0)
            for a,b in zip(actual,expected):np.testing.assert_array_equal(a,b)


if __name__=='__main__':unittest.main()
