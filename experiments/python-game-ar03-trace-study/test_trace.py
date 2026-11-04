import importlib.util
from pathlib import Path
import struct
import unittest
import zlib
import numpy as np
import trace_codec as t
cp=t.cp;f=t.codec.gm.token_coeff.frozen

def seal(p):return p+struct.pack('<I',zlib.crc32(p))
def rice_packet(dc,ac,blocks=1,bw=1):
    return seal(cp.COEFF.pack(b'CP02',1,1,blocks,bw,0,len(dc),len(ac))+dc+ac)
class TraceTests(unittest.TestCase):
    def test_exact_random_sparse_dense_and_partial_rows(self):
        for n,bw in [(1,1),(6,3),(90,45)]:
            for dense in (False,True):
                a=np.random.default_rng(1810+n+int(dense)).integers(-2048,2049,(n,8,8),dtype=np.int16)
                if not dense:a[np.random.default_rng(5).random(a.shape)>.05]=0
                p=t.codec.gm.token_coeff.encode_coefficients(a,bw);out,rows=t.decode_cp02(p,n,bw)
                np.testing.assert_array_equal(a,out);self.assertEqual(len(rows),n)
                for r in rows:self.assertLessEqual(r['reservoir_peak_bits'],64)
    def test_zero_dc_and_signed_escape_extremes(self):
        a=np.zeros((6,8,8),np.int16);a[:,0,0]=[-2048,2048,0,1,-1,2048]
        p=t.codec.gm.token_coeff.encode_coefficients(a,3);out,rows=t.decode_cp02(p,6,3)
        np.testing.assert_array_equal(a,out);self.assertTrue(all(r['dc_bits'] for r in rows))
    def test_truncation_bad_crc_and_bounds(self):
        p=t.codec.gm.token_coeff.encode_coefficients(np.zeros((1,8,8),np.int16),1)
        for bad in [p[:-1],p[:20],p[:-1]+bytes([p[-1]^1])]:
            with self.assertRaises(ValueError):t.decode_cp02(bad,1,1)
        with self.assertRaises(ValueError):t.decode_cp02(p,1,0)
        raw=np.zeros((1,8,8),np.int16);raw[0,0,0]=2049
        badraw=seal(cp.COEFF.pack(b'CP02',1,0,1,1,0,128,0)+raw.astype('<i2').tobytes())
        with self.assertRaises(ValueError):t.decode_cp02(badraw,1,1)
    def test_noncanonical_escape_and_truncated_unary(self):
        # k=0; escape value1 would fit a short unary code and must reject.
        dc=bytes([0])+f._pack('0'*15+format(1,'014b'))
        with self.assertRaises(ValueError):t.decode_cp02(rice_packet(dc,b'\0\0\0\0'),1,1)
        with self.assertRaises(ValueError):t.Bits(b'\0').rice(0,14)
    def test_zrl_run_and_padding_fail(self):
        dc=b'\0'+f._pack('1')
        for acbits in ['01'*4,'01'*3+'1'+'1111'+'1','00'+'1']:
            p=rice_packet(dc,b'\0\0\0'+f._pack(acbits))
            with self.assertRaises(ValueError):t.decode_cp02(p,1,1)
    def test_sr_split_dense_and_actual_stream_cursor_monotonicity(self):
        a=np.zeros((12,8,8),np.int16);a[2,0,0]=5;a[7,2,3]=3;a[11,0,0]=-7
        for structured in (False,True):
            p,_=t.codec.sr.encode_plane(a,4,structured=structured);out,rows,info=t.plane_trace(p,12,4,True)
            np.testing.assert_array_equal(a,out);self.assertEqual(len(rows),12)
        p=t.codec.gm.token_coeff.encode_coefficients(a,4);_,rows=t.decode_cp02(p,12,4)
        for field in ('dc_bits','ac_bits','dc_read_range','ac_read_range'):
            for left,right in zip(rows,rows[1:]):self.assertEqual(left[field][1],right[field][0])
    def test_actual_ar03_partial_geometry_trace(self):
        rgb=np.full((18,34,3),129,np.uint8)
        d=t.codec.Encoder(epoch=18,mode='exact').prepare(rgb,0)
        trace=t.parse_packet(d.packet)
        self.assertEqual((trace['width'],trace['height']),(34,18))
        self.assertEqual(sum(p['blocks_w']*p['blocks_h'] for p in trace['planes']),27)
        bad=d.packet[:-1]+bytes([d.packet[-1]^1])
        with self.assertRaises(ValueError):t.parse_packet(bad)
    def test_yielded_block_does_not_require_future_tokens(self):
        a=np.zeros((4,8,8),np.int16);p=t.codec.gm.token_coeff.encode_coefficients(a,4)
        iterator=t.iter_cp02(p,4,4);block,row=next(iterator)
        self.assertEqual(row['block'],0);self.assertEqual(row['dc_bits'],[0,1]);self.assertEqual(row['ac_bits'],[0,2])
        np.testing.assert_array_equal(block,a[0])
if __name__=='__main__':unittest.main()
