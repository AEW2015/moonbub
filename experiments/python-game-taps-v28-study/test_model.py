import unittest
import struct
import zlib
import numpy as np
import model as m


def scalar(reference, vectors, block_size):
    out=[]
    for plane,image in enumerate(reference):
        ph,pw=image.shape;bs=block_size if plane==0 else block_size//2;den=2 if plane==0 else 4
        got=np.empty((ph,pw),np.int16)
        for y in range(ph):
            for x in range(pw):
                dx,dy=map(int,vectors[y//bs,x//bs]);ix,fx=divmod(dx,den);iy,fy=divmod(dy,den)
                s=0
                for oy,wy in ((0,den-fy),(1,fy)):
                    for ox,wx in ((0,den-fx),(1,fx)):
                        s+=wx*wy*int(image[min(max(y+iy+oy,0),ph-1),min(max(x+ix+ox,0),pw-1)])
                got[y,x]=(s+den*den//2)//(den*den)
        out.append(got)
    return tuple(out)


def planes(h,w):
    rng=np.random.default_rng(h*w)
    return tuple(rng.integers(0,256,s,dtype=np.int16) for s in ((h,w),(h//2,w//2),(h//2,w//2)))


class Tests(unittest.TestCase):
    def test_scalar_all_fractions_negative_clamps_partial(self):
        # Every chroma fractional pair also covers every luma fractional pair.
        for h,w in ((2,2),(18,34),(34,50)):
            ref=planes(h,w)
            for bs in (16,32):
                mw,mh=m.frozen._grid(w,h,bs)
                for dy in (-18,-17,-16,-15,0,1,2,3,18):
                    for dx in (-18,-17,-16,-15,0,1,2,3,18):
                        v=np.full((mh,mw,2),(dx,dy),np.int8)
                        actual,work=m.predict_with_info(ref,v,bs)
                        for a,b in zip(actual,scalar(ref,v,bs)):np.testing.assert_array_equal(a,b)
                        expected=sum(p.size*(1+(dx%d!=0))*(1+(dy%d!=0)) for p,d in zip(ref,(2,4,4)))
                        self.assertEqual(work['reference_sample_fetches'],expected)

    def test_random_mixed_bounds_full_resolution(self):
        for h,w in ((34,50),(480,720),(270,1280)):
            ref=planes(h,w)
            for bs in (16,32):
                mw,mh=m.frozen._grid(w,h,bs)
                v=np.random.default_rng(19).integers(-18,19,(mh,mw,2),dtype=np.int8)
                for a,b in zip(m.predict(ref,v,bs),m.frozen.predict(ref,v,bs)):np.testing.assert_array_equal(a,b)

    def test_zero_copies_and_integer_axes(self):
        ref=planes(34,50);v=np.zeros((3,4,2),np.int8)
        got,work=m.predict_with_info(ref,v)
        self.assertTrue(work['whole_map_zero_shortcut'])
        for a,b in zip(got,ref):
            np.testing.assert_array_equal(a,b);self.assertFalse(np.shares_memory(a,b))
        for dx,dy in ((4,0),(0,-4),(4,4),(1,0),(0,-1)):
            v[:]=(dx,dy)
            for a,b in zip(m.predict(ref,v),m.frozen.predict(ref,v)):np.testing.assert_array_equal(a,b)

    def test_validation_matches_frozen(self):
        ref=planes(34,50);v=np.zeros((3,4,2),np.int8)
        invalid=[(ref,v,8),(ref,v,True),(ref,v[:2],16),(ref,v.astype(float),16),
                 (ref,np.full_like(v,19),16),
                 ((ref[0].astype(float),*ref[1:]),v,16),((ref[0],ref[1][:-1],ref[2]),v,16),
                 ((np.full_like(ref[0],256),*ref[1:]),v,16)]
        for args in invalid:
            for fn in (m.predict,m.frozen.predict):
                with self.assertRaises(ValueError):fn(*args)
        # Preserve the frozen validator's uint64-to-int64 behavior too; this
        # API deliberately shares the exact old validator rather than widening
        # or narrowing its source/vector acceptance while changing prediction.
        unusual=np.full(v.shape,2**64-1,np.uint64)
        for a,b in zip(m.predict(ref,unusual),m.frozen.predict(ref,unusual)):np.testing.assert_array_equal(a,b)

    def test_decode_keys_P_tags_and_no_mutation(self):
        ref=planes(34,50);q=m.frozen.roi.declared_map(50,34,(),8,16)
        old_predict=m.frozen.predict
        packet,expected,_=m.frozen.encode_planes(ref,None,q,epoch=25,block_size=32)
        got,_=m.decode(packet,expected_epoch=25)
        for a,b in zip(got,expected):np.testing.assert_array_equal(a,b)
        packet,expected,_=m.frozen.encode_planes(planes(34,50),got,q,epoch=25,frame_id=1,reference_id=0,block_size=32,motion_mode='zero')
        new,_=m.decode(packet,got,expected_epoch=25,expected_reference_id=0)
        for a,b in zip(new,expected):np.testing.assert_array_equal(a,b)
        self.assertIs(m.frozen.predict,old_predict)
        for opts in ({'expected_reference_id':1},{'expected_reference_id':0,'expected_epoch':26},{}):
            with self.assertRaises(ValueError):m.decode(packet,got,**opts)
        changed=[x.copy() for x in got];changed[0][0,0]^=1
        with self.assertRaises(ValueError):m.decode(packet,changed,expected_reference_id=0)
        body=bytearray(packet[:-4]);body[39]^=1
        bad=bytes(body)+struct.pack('<I',zlib.crc32(body))
        with self.assertRaises(ValueError):m.decode(bad,got,expected_reference_id=0)


if __name__=='__main__':unittest.main()
