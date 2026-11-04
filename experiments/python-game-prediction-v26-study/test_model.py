import unittest, struct, zlib
import numpy as np
import model as m


def source(seed=1,shape=(34,50)):
    return tuple(m.ft.rgb_to_planes(np.random.default_rng(seed).integers(0,256,(*shape,3),dtype=np.uint8)))


def scalar(ref,vectors,bs):
    out=[]
    for plane,image in enumerate(ref):
        h,w=image.shape; step=bs if plane==0 else bs//2; d=2 if plane==0 else 4
        p=np.empty_like(image)
        for y in range(h):
            for x in range(w):
                dx,dy=map(int,vectors[y//step,x//step]); ix,fx=divmod(dx,d); iy,fy=divmod(dy,d)
                total=0
                for oy,wy in ((0,d-fy),(1,fy)):
                    for ox,wx in ((0,d-fx),(1,fx)):
                        total+=wx*wy*int(image[min(max(y+iy+oy,0),h-1),min(max(x+ix+ox,0),w-1)])
                p[y,x]=(total+d*d//2)//(d*d)
        out.append(p)
    return tuple(out)

class Tests(unittest.TestCase):
    def test_scalar_negative_clamp_round_chroma_partial_edges(self):
        ref=source()
        for bs in (16,32):
            mw,mh=m._grid(50,34,bs)
            v=np.random.default_rng(6).integers(-18,19,(mh,mw,2),dtype=np.int8)
            for a,b in zip(m.predict(ref,v,bs),scalar(ref,v,bs)): np.testing.assert_array_equal(a,b)
    def test_coarse_even_parity(self):
        ref=source(); mw,mh=m._grid(50,34,16)
        v=np.random.default_rng(4).integers(-4,5,(mh,mw,2),dtype=np.int8)*2
        for a,b in zip(m.predict(ref,v*2),m.v25.predict(ref,v)): np.testing.assert_array_equal(a,b)
    def test_maps_canonical_bounds(self):
        for shape in ((3,4),(1,500)):
            a=np.random.default_rng(4).integers(-18,19,(*shape,2),dtype=np.int8)
            for v in (a,np.zeros_like(a),np.concatenate((a[:,:1],np.zeros_like(a[:,1:])),axis=1)):
                np.testing.assert_array_equal(v,m.unpack_vectors(m.pack_vectors(v),shape[1],shape[0]))
        for bad in (b'\x04',b'\x01'+bytes(24),b'\x00\x13\x00'):
            with self.assertRaises(ValueError): m.unpack_vectors(bad,4,3)
    def test_packet_modes_exact_tags_crc_and_frozen_coeffs(self):
        src=source(shape=(64,64)); q=m.roi.declared_map(64,64,(),8,16)
        packet,ref,_=m.encode_planes(src,None,q)
        got,_=m.decode(packet)
        for a,b in zip(ref,got): np.testing.assert_array_equal(a,b)
        for mode in ('zero','global','block'):
            for precision in ('coarse','integer','half'):
                packet,expected,work=m.encode_planes(source(2,(64,64)),ref,q,frame_id=1,reference_id=0,motion_mode=mode,motion_precision=precision)
                got,meta=m.decode(packet,ref,expected_reference_id=0)
                for a,b in zip(got,expected):np.testing.assert_array_equal(a,b)
                self.assertEqual(work['decoder_reference_sample_reads'],4*6144)
                if mode=='zero':
                    old,oldout,_=m.v25.encode_planes(source(2,(64,64)),ref,q,frame_id=1,reference_id=0,motion_mode='zero')
                    for a,b in zip(meta['coefficients'],m.v25.parse(old)['coefficients']):np.testing.assert_array_equal(a,b)
                with self.assertRaises(ValueError):m.decode(packet,ref,expected_reference_id=1)
                changed=list(ref);changed[0]=changed[0].copy();changed[0][0,0]^=1
                with self.assertRaises(ValueError):m.decode(packet,changed,expected_reference_id=0)
                with self.assertRaises(ValueError):m.decode(packet[:-1],ref,expected_reference_id=0)
        with self.assertRaises(ValueError):m._decode_plane(b'\x03',16,4)
    def test_synthetic_half_translation(self):
        ref=source(shape=(32,32)); v=np.full((2,2,2),(1,-1),np.int8); src=m.predict(ref,v)
        chosen,work=m.estimate_vectors(src,ref,16,'global',0,'half')
        np.testing.assert_array_equal(chosen,v)
        self.assertEqual(work['candidate_vectors'],106)
        self.assertEqual(work['sad_sample_operations'],106*1536)
        self.assertEqual(work['reference_sample_fetches'],(81+25*4)*1536)

if __name__=='__main__':unittest.main()


def scalar_compact(data,mw,mh):
    # Independent string-bit oracle: no production bit reader or predictor calls.
    bits=''.join(format(v,'08b') for v in data[1 if data[0]==4 else 3:]); at=0
    out=np.zeros((mh,mw,2),np.int16)
    if data[0]==4:
        values=[int(bits[i:i+6],2)-18 for i in range(0,12*mw*mh,6)]
        return np.array(values,np.int16).reshape(mh,mw,2)
    for axis,k in enumerate(data[1:3]):
        for y in range(mh):
            for x in range(mw):
                q=0
                while q<7 and bits[at]=='1':q+=1;at+=1
                if q==7:z=int(bits[at:at+7],2);at+=7
                else:
                    at+=1; z=(q<<k)+(int(bits[at:at+k],2) if k else 0);at+=k
                left=int(out[y,x-1,axis]) if x else 0
                if data[0]==5:pred=left
                else:
                    top=int(out[y-1,x,axis]) if y else 0
                    tr=int(out[y-1,min(x+1,mw-1),axis]) if y else 0
                    pred=sorted((left,top,tr))[1]
                out[y,x,axis]=pred+(z//2 if z%2==0 else -(z+1)//2)
    assert len(bits)-at<8 and not bits[at:].strip('0')
    return out

class CompactTests(unittest.TestCase):
    def test_compact_modes_scalar_and_canonical(self):
        rng=np.random.default_rng(16); observed=set()
        maps=[rng.integers(-18,19,(8,16,2),dtype=np.int8) for _ in range(12)]
        maps += [np.stack(np.meshgrid(np.arange(16)-8,np.arange(8)-4),axis=2).astype(np.int8),
                 rng.integers(-18,19,(1,16,2),dtype=np.int8).repeat(8,axis=0)]
        for a in maps:
            data,work=m.pack_vectors(a,True);observed.add(data[0])
            np.testing.assert_array_equal(m.unpack_vectors(data,16,8),a)
            if data[0] in (4,5,6):np.testing.assert_array_equal(scalar_compact(data,16,8),a)
            self.assertEqual(work['rice_axis_trials'],28)
            self.assertEqual(work['rice_value_encode_trials'],28*128)
            self.assertEqual(len(work['candidates']),6)
            self.assertEqual(len(data),min(c['bytes'] for c in work['candidates']))
        self.assertTrue({4,5,6}<=observed,observed)
    def test_compact_malformed_fields_bounds_padding_escape(self):
        for data in (b'\x04\xff\xff\xff',b'\x05\x07\x00',b'\x06\x00\x07',b'\x05\x00\x00\xfe\x00',b'\x07',b'\x04'+bytes(200)):
            with self.assertRaises(ValueError):m.unpack_vectors(data,4,3)
        a=np.stack(np.meshgrid(np.arange(16)-8,np.arange(8)-4),axis=2).astype(np.int8)
        data=m.pack_vectors(a)
        self.assertEqual(data[0],5)
        for bad in (data[:-1],data+bytes(1),data[:-1]+bytes((data[-1]|1,))):
            with self.assertRaises(ValueError):m.unpack_vectors(bad,16,8)
    def test_new_header_version_and_policy_validation(self):
        q=m.roi.declared_map(50,34,(),8,16);packet,_,_=m.encode_planes(source(),None,q)
        self.assertEqual(m.HEADER.unpack_from(packet)[1],2)
        old=list(m.HEADER.unpack_from(packet));old[1]=1
        body=m.HEADER.pack(*old)+packet[m.HEADER.size:-4]
        forged=body+struct.pack('<I',zlib.crc32(body))
        with self.assertRaises(ValueError):m.parse(forged)
        with self.assertRaises(ValueError):m.encode_planes(source(),None,q,motion_precision='unknown')
