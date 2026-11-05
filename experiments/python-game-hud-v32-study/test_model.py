import struct,unittest,zlib
import numpy as np
import model as m

class HudTests(unittest.TestCase):
    def test_huffman_roundtrip_constant_sparse_dense_and_bounds(self):
        rng=np.random.default_rng(32)
        for a in (np.zeros(40,np.int32),np.full(40,252,np.int32),rng.integers(0,253,500),np.r_[np.zeros(200),np.arange(127)]):
            data,_=m._huff_encode(a);out,end=m._huff_decode(data,0,len(a),252)
            np.testing.assert_array_equal(out,a);self.assertEqual(end,len(data))
        with self.assertRaises(ValueError):m._codes({0:1,1:1,2:1})
        with self.assertRaises(ValueError):m._codes({0:17})
        with self.assertRaises(ValueError):m._huff_decode(struct.pack('<HI',254,0),0,1000,252)

    def test_patch_modes_exact_with_row_delta_and_motion(self):
        rng=np.random.default_rng(321);ref=rng.integers(0,65536,(8,32),dtype=np.uint16)
        current=(ref.astype(np.uint32)+1).astype(np.uint16)
        for mode,pred,prefix in ((0,None,b''),(1,ref,b''),(9,ref,b''),(2,m.h.predict(ref,1,0),struct.pack('<bb',1,0)),(10,m.h.predict(ref,-1,1),struct.pack('<bb',-1,1))):
            payload,_=m._encode_patch(current,pred,mode,prefix);packet=m._pack_patch(current,ref,mode,payload)
            np.testing.assert_array_equal(m._decode_patch(packet,None if mode==0 else ref),current)
            if mode:
                with self.assertRaises(ValueError):m._decode_patch(packet,ref^1)
            bad=bytearray(packet);bad[-1]^=1
            with self.assertRaises(ValueError):m._decode_patch(bytes(bad),ref)

    def test_outer_exact_fallback_reference_and_crc(self):
        rng=np.random.default_rng(322);ref=None
        for fid in range(3):
            a=rng.integers(0,65536,(8,32),dtype=np.uint16) if ref is None else ref[0]['words']^np.uint16(1)
            full=m.p.ui.hp.encode_patch(m.p.base.C.corpus.expand565(a),(0,0,32,8))
            old,_=m.p.encode_hud((full,),ref,epoch=25,frame_id=fid,reference_id=m.p.NO_REF if ref is None else fid-1,motion=False,width=720,height=480)
            new,work=m.encode_hud(old,ref,expected_reference_id=None if ref is None else fid-1)
            self.assertLessEqual(len(new),len(old));out,meta=m.decode_hud(new,ref,expected_epoch=25,expected_reference_id=None if ref is None else fid-1)
            np.testing.assert_array_equal(out[0]['words'],a)
            if fid:
                with self.assertRaises(ValueError):m.decode_hud(new,ref,expected_epoch=25,expected_reference_id=999)
            bad=bytearray(new);bad[-1]^=1
            with self.assertRaises(ValueError):m.decode_hud(bytes(bad),ref,expected_epoch=25,expected_reference_id=fid-1)
            ref=out

    def test_truncation_table_padding_and_trailing_rejected(self):
        a=np.array([0,1,2,0,1,0,0,2,0],np.int32);data,_=m._huff_encode(a)
        for n in range(len(data)):
            with self.assertRaises(ValueError):m._huff_decode(data[:n],0,len(a),252)
        data=bytearray(data);ns,bits=m.STREAM.unpack_from(data)
        if bits%8:
            data[-1]|=1
            with self.assertRaises(ValueError):m._huff_decode(bytes(data),0,len(a),252)

    def test_hx32_dispatch_semantic_errors_after_valid_outer_crc(self):
        a=np.full((8,32),0x39e7,np.uint16)
        full=m.p.ui.hp.encode_patch(m.p.base.C.corpus.expand565(a),(0,0,32,8))
        old,_=m.p.encode_hud((full,),epoch=25,frame_id=0,width=720,height=480)
        payload,_=m._encode_patch(a,None,0);hs=m._pack_patch(a,None,0,payload)
        fields=list(m.p.HUD.unpack_from(old));fields[0]=b'HX32';fields[10]=len(hs);fields[14]=3
        packet=m.p.seal(m.p.HUD.pack(*fields)+hs)
        out,_=m.decode_hud(packet,expected_epoch=25)
        np.testing.assert_array_equal(out[0]['words'],a)
        bad=bytearray(hs);bad[5]=255;bad[-4:]=struct.pack('<I',zlib.crc32(bad[:-4]))
        with self.assertRaises(ValueError):m.decode_hud(m.p.seal(m.p.HUD.pack(*fields)+bytes(bad)),expected_epoch=25)
        with self.assertRaises(ValueError):m.decode_hud(packet,expected_epoch=24)

if __name__=='__main__':unittest.main()
