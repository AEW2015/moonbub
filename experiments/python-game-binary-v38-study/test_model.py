import unittest,struct,zlib
import numpy as np
import model,decoder

class BinaryTests(unittest.TestCase):
    def test_all_zero_DC_sparse_extreme_and_raw(self):
        rng=np.random.default_rng(3801)
        samples=[np.zeros((64,8,8),np.int16),rng.integers(-2048,2049,(64,8,8),dtype=np.int16)]
        a=samples[0].copy();a[:,0,0]=np.arange(64)-32;samples.append(a)
        a=rng.integers(-20,21,(64,8,8),dtype=np.int16);a[rng.random(a.shape)<.94]=0;samples.append(a)
        for a in samples:
            for bw in (1,8,64):
                packet,work=model.encode(a,bw);np.testing.assert_array_equal(decoder.decode(packet,64,bw),a)
                self.assertLessEqual(work['max_renorm_per_bit'],16)
    def test_padding_crc_and_resealed_geometry(self):
        packet,_=model.encode(np.zeros((64,8,8),np.int16),8)
        for bad in (bytearray(packet),packet[:-1],packet+b'\0',packet[:-1]+bytes([packet[-1]^1])):
            with self.assertRaises(ValueError):decoder.decode(bad,64,8)
        fields=list(model.HEADER.unpack_from(packet));fields[3]=63
        body=model.HEADER.pack(*fields)+packet[model.HEADER.size:-4];bad=body+struct.pack('<I',zlib.crc32(body))
        with self.assertRaises(ValueError):decoder.decode(bad,64,8)
    def test_domain_and_bad_arithmetic_stream(self):
        for a in (np.zeros((0,8,8),np.int16),np.zeros((1,8,8)),np.full((1,8,8),2049,np.int16)):
            with self.assertRaises(ValueError):model.encode(a,1)
        with self.assertRaises(ValueError):decoder.ArithmeticReader(b'\0\0\1',18)

if __name__=='__main__':unittest.main()
