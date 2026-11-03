"""Independent-IQ01 wrapper correctness and malformed-input tests."""
import struct
import unittest
import zlib
import numpy as np
import codec
import index_codec


def wrap(inner,q=2):
    body=index_codec.HEADER.pack(b'IQ01',1,q,len(inner))+inner
    return body+struct.pack('<I',zlib.crc32(body))


def recalc(data):
    return bytes(data[:-4])+struct.pack('<I',zlib.crc32(data[:-4]))


class IndexCodecTests(unittest.TestCase):
    def test_quantized_roundtrip_random_edges_and_endpoints(self):
        rng=np.random.default_rng(20261103)
        random=rng.integers(0,65536,(33,47),dtype=np.uint16)
        endpoints=np.array([[0,31,0x07e0,0xf800,65535]],np.uint16)
        for q in (1,2,3,4,7,8,16,32):
            for words in (random,endpoints):
                with self.subTest(q=q,shape=words.shape):
                    expected=codec.quantize(words,q)
                    np.testing.assert_array_equal(index_codec.decode(index_codec.encode(words,q)),expected)
    def test_q1_preserves_exact_original_words(self):
        words=np.arange(1024,dtype=np.uint16).reshape(32,32)
        encoded=index_codec.encode(words,quant_step=1)
        np.testing.assert_array_equal(index_codec.decode(encoded),words)
    def test_crc_truncation_and_trailing_data(self):
        packet=index_codec.encode(np.full((16,16),65535,np.uint16))
        for n in range(len(packet)):
            with self.assertRaises(ValueError): index_codec.decode(packet[:n])
        for at in range(len(packet)):
            corrupted=bytearray(packet);corrupted[at]^=1
            with self.assertRaises(ValueError): index_codec.decode(corrupted)
        with self.assertRaises(ValueError): index_codec.decode(packet+b'\0')
    def test_valid_crc_header_and_outofrange_indices(self):
        packet=index_codec.encode(np.zeros((16,16),np.uint16))
        for at,value in ((0,0),(4,2),(5,0),(6,255)):
            corrupted=bytearray(packet);corrupted[at]=value
            with self.assertRaises(ValueError): index_codec.decode(recalc(corrupted))
        for words in (np.full((16,16),31<<11,np.uint16),
                      np.full((16,16),63<<5,np.uint16),
                      np.full((16,16),31,np.uint16)):
            with self.assertRaises(ValueError): index_codec.decode(wrap(codec.encode(words),q=2))
        # q3 cannot produce the clipped R31 value: its terminal index is unused.
        with self.assertRaises(ValueError):
            index_codec.decode(wrap(codec.encode(np.full((16,16),11<<11,np.uint16)),q=3))
    def test_rejects_nested_quantizer_and_inner_crc(self):
        words=np.tile(np.arange(16,dtype=np.uint16),(16,1))
        with self.assertRaises(ValueError): index_codec.decode(wrap(codec.encode(words,quant_step=2)))
        inner=bytearray(codec.encode(words));inner[-1]^=1
        with self.assertRaises(ValueError): index_codec.decode(wrap(inner))
    def test_input_bounds(self):
        for q in (0,33,1.5):
            with self.assertRaises(ValueError): index_codec.encode(np.zeros((1,1),np.uint16),q)
        with self.assertRaises(ValueError): index_codec.encode(np.zeros((1,1),np.uint8))
    def test_smooth_fixture_exactness_and_measured_size(self):
        yy,xx=np.mgrid[:32,:48]
        words=(((xx%32)<<11)|((yy%64)<<5)|(xx%32)).astype(np.uint16)
        original=codec.encode(words,quant_step=4)
        compact=index_codec.encode(words,quant_step=4)
        np.testing.assert_array_equal(index_codec.decode(compact),codec.decode(original))
        # This verifies an observed fixture advantage, not universal compression.
        self.assertLess(len(compact),len(original))
        print(f'smooth q4 fixture original={len(original)} index={len(compact)} bytes')


if __name__=='__main__': unittest.main()
