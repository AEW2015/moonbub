"""Bounded zero-run mode roundtrip, fallback, and hostile-input tests."""
import struct
import unittest
import zlib
import numpy as np
import codec
import zero_run_codec as zr


def packet(data,*,w=16,h=16,q=1,mode=5):
    payload=codec.TILE_HEADER.pack(mode,len(data))+data
    body=zr.HEADER.pack(b'ZR01',1,q,w,h,1,len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


def recalc(b):return bytes(b[:-4])+struct.pack('<I',zlib.crc32(b[:-4]))


class ZeroRunTests(unittest.TestCase):
    def test_families_quantizers_edges_and_bounds(self):
        rng=np.random.default_rng(20261103);yy,xx=np.mgrid[:33,:47]
        families=[np.zeros((33,47),np.uint16),np.full((1,1),65535,np.uint16),
                  rng.integers(0,65536,(33,47),dtype=np.uint16),
                  (((xx%32)<<11)|((yy%64)<<5)|(xx%32)).astype(np.uint16),
                  np.where((xx+yy)%2,65535,0).astype(np.uint16)]
        for q in (1,2,3,4,7,8,16,32):
            for words in families:
                encoded=zr.encode(words,q)
                np.testing.assert_array_equal(zr.decode(encoded),codec.quantize(words,q))
                h,w=words.shape
                self.assertLessEqual(len(encoded),zr.HEADER.size+4+2*w*h+3*((w+15)//16)*((h+15)//16))
    def test_zero_run_selected_and_row_reset_exact(self):
        # Sparse first-column values leave long zero-residual runs.
        words=np.zeros((16,16),np.uint16);words[:,0]=np.arange(16,dtype=np.uint16)
        encoded=zr.encode(words,1)
        self.assertEqual(encoded[zr.HEADER.size],zr.ZERO_RUN)
        np.testing.assert_array_equal(zr.decode(encoded),words)
        print('zero-run fixture bytes',len(encoded))
        # A zero run crossing row1 resets its predictor to0, not prior row's last.
        bits='1'+'01'+'0'+format(254,'08b')+'0'+format(255,'08b')+'0'+format(255,'08b')
        # Firstred sample+1; subsequent255redresiduals zero, G/B allzero.
        out=zr.decode(packet(b'\0\0\0'+codec._pack_bits_string(bits)))
        self.assertTrue(np.all(out[0]==1<<11));self.assertTrue(np.all(out[1:]==0))
    def test_max_zero_run_and_small_tiles(self):
        #3complete channels, each represented by one maximal256residualrun.
        data=b'\0\0\0'+codec._pack_bits_string(('0'+'11111111')*3)
        np.testing.assert_array_equal(zr.decode(packet(data)),np.zeros((16,16),np.uint16))
        # A ZR tile must obey the same RAW payload bound; use 2x2, where
        # the three short run tokens fit within eight raw payload bytes.
        data=b'\0\0\0'+codec._pack_bits_string(('0'+'00000011')*3)
        np.testing.assert_array_equal(zr.decode(packet(data,w=2,h=2)),np.zeros((2,2),np.uint16))
    def test_malformed_runs_rice_channel_padding(self):
        # A256run cannot fit a4sample channel.
        data=b'\0\0\0'+codec._pack_bits_string('0'+'11111111')
        with self.assertRaises(ValueError):zr.decode(packet(data,w=2,h=2))
        # Nonzero token+Rice(0,k0) maps to -1 frominitial0:invalidchannel.
        data=b'\0\0\0'+codec._pack_bits_string('11')
        with self.assertRaises(ValueError):zr.decode(packet(data))
        for data in (bytes([7,0,0])+bytes(8),b'\0\0\0',
                     b'\0\0\0'+codec._pack_bits_string('1'+'0'*15+'0000000')):
            with self.assertRaises(ValueError):zr.decode(packet(data))
        valid=b'\0\0\0'+codec._pack_bits_string(('0'+'11111111')*3)
        bad=bytearray(valid);bad[-1]|=1
        with self.assertRaises(ValueError):zr.decode(packet(bad))
        with self.assertRaises(ValueError):zr.decode(packet(valid+b'\0'))
    def test_crc_headers_counts_modes_and_inner_index_range(self):
        encoded=zr.encode(np.zeros((16,16),np.uint16))
        for at,value in ((0,0),(4,2),(5,0),(6,0),(10,0),(zr.HEADER.size,6)):
            bad=bytearray(encoded);bad[at]=value
            with self.assertRaises(ValueError):zr.decode(recalc(bad))
        # RAW virtualR31isnotvalidwhenq2'smaximumRindexis16.
        with self.assertRaises(ValueError):
            zr.decode(packet(np.full((16,16),31<<11,dtype='<u2').tobytes(),q=2,mode=0))
        for at in range(len(encoded)):
            bad=bytearray(encoded);bad[at]^=1
            with self.assertRaises(ValueError):zr.decode(bad)
        for n in range(len(encoded)):
            with self.assertRaises(ValueError):zr.decode(encoded[:n])
        with self.assertRaises(ValueError):zr.decode(encoded+b'\0')


if __name__=='__main__':unittest.main()
