import struct
import unittest
import zlib
import numpy as np
import model as m


class EntropyTests(unittest.TestCase):
    def test_exact_patterns_layouts_and_raw(self):
        rng=np.random.default_rng(2626)
        cases=[np.zeros((6,8,8),np.int16),rng.integers(-2048,2049,(6,8,8),dtype=np.int16)]
        a=cases[1].copy();a[rng.random(a.shape)<.97]=0;cases.append(a)
        dc=cases[0].copy();dc[:,0,0]=[-2048,2048,0,1,-1,2048];cases.append(dc)
        for a in cases:
            for layout in (0,1):
                p=m.encode_coefficients(a,3,layout=layout)
                np.testing.assert_array_equal(m.decode_coefficients(p,6,3),a)
                self.assertLessEqual(len(p),m.COEFF.size+4+128*len(a))

    def test_long_runs_and_coefficient_boundaries(self):
        a=np.zeros((270,8,8),np.int16)
        for i in (0,1,128,269): a[i,7,7]=2048 if i%2 else -2048
        for layout in (0,1):
            np.testing.assert_array_equal(m.decode_coefficients(m.encode_coefficients(a,9,layout=layout),270,9),a)

    def test_four_cursor_block_decoder_matches_full_plane_oracle(self):
        rng=np.random.default_rng(2602)
        for sparse in (False,True):
            a=rng.integers(-2048,2049,(42,8,8),dtype=np.int16)
            if sparse:a[rng.random(a.shape)<.97]=0
            packet=m.encode_coefficients(a,7,layout=0)
            np.testing.assert_array_equal(np.stack(list(m.iter_block_major(packet,42,7))),a)
        a=np.zeros((42,8,8),np.int16)
        with self.assertRaises(ValueError):list(m.iter_block_major(m.encode_coefficients(a,7,layout=1),42,7))

    def test_rice_counter_matches_actual_all_escape_boundaries(self):
        a=np.array([0,14,15,16,127,1023,1<<20],np.int64)
        for maximum,escape in ((19,24),(11,12),(13,14)):
            v=a[a<(1<<escape)]
            actual=[sum(len(m.f._rice(int(x),k,escape)) for x in v) for k in range(maximum+1)]
            self.assertEqual(m._rice_cost(v,maximum,escape),actual.index(min(actual)))

    def test_malformed_crc_truncation_padding_domain(self):
        a=np.zeros((2,8,8),np.int16);p=m.encode_coefficients(a,1)
        for q in (p[:-1],p+b'\x00',p[:8]+bytes([p[8]^1])+p[9:]):
            with self.assertRaises(ValueError):m.decode_coefficients(q,2,1)
        # CRC-valid extra byte in final empty AC stream must reject.
        body=bytearray(p[:-4]);body.extend(b'\x01')
        values=list(m.COEFF.unpack_from(body));values[9]+=1
        body[:m.COEFF.size]=m.COEFF.pack(*values)
        with self.assertRaises(ValueError):m.decode_coefficients(m.seal(bytes(body)),2,1)
        with self.assertRaises(ValueError):m.encode_coefficients(a.astype(np.int32),1)
        with self.assertRaises(ValueError):m.decode_coefficients(p,3,2)

    def test_ge26_repack_closed_loop_and_reference_tag(self):
        rng=np.random.default_rng(26);ref=None
        mapped=m.roi.declared_map(64,64,(),8,16)
        for fid in range(3):
            source=tuple(m.ft.rgb_to_planes(rng.integers(0,256,(64,64,3),np.uint8)))
            original,expected,_=m.old.encode_planes(source,ref,mapped,frame_id=fid,reference_id=m.NO_REF if fid==0 else fid-1,motion_mode='zero')
            packet,work=m.repack(original);self.assertLessEqual(len(packet),len(original))
            output,meta=m.decode(packet,ref,expected_epoch=1,expected_reference_id=None if fid==0 else fid-1)
            for a,b in zip(expected,output):np.testing.assert_array_equal(a,b)
            if fid:
                with self.assertRaises(ValueError):m.decode(packet,None,expected_reference_id=fid-1)
            with self.assertRaises(ValueError):m.decode(packet,ref,expected_epoch=2,expected_reference_id=fid-1)
            ref=output


if __name__=='__main__':unittest.main()
