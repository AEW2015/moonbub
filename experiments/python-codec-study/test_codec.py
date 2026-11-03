"""Round-trip and hostile-input tests; no throughput/hardware qualification."""
import struct
import unittest
import zlib
import numpy as np
import codec


def recalc(b):
    return bytes(b[:-4])+struct.pack('<I',zlib.crc32(b[:-4]))


class CodecTests(unittest.TestCase):
    def setUp(self): self.rng = np.random.default_rng(20261103)
    def test_lossless_families_and_edges(self):
        yy,xx = np.mgrid[:33,:47]
        families = [np.zeros((33,47),np.uint16),np.full((1,1),65535,np.uint16),
                    self.rng.integers(0,65536,(33,47),dtype=np.uint16),
                    ((xx%32)<<11|((yy%64)<<5)|((xx+yy)%32)).astype(np.uint16),
                    np.where((xx+yy)%2,0xFFFF,0).astype(np.uint16)]
        for a in families:
            for dpcm in (False,True):
                for palette in (False,True):
                    with self.subTest(shape=a.shape,dpcm=dpcm,palette=palette):
                        p=codec.encode(a,use_dpcm=dpcm,use_palette=palette)
                        np.testing.assert_array_equal(codec.decode(p),a)
                        self.assertLessEqual(len(p),codec.stats(p)['raw_bound_bytes'])
    def test_quantized_expected_channels(self):
        a=self.rng.integers(0,65536,(31,18),dtype=np.uint16)
        for q in (1,2,3,4,7,16,32):
            r=np.minimum(((a.astype(np.uint32)>>11)+q//2)//q*q,31)
            g=np.minimum((((a.astype(np.uint32)>>5)&63)+q//2)//q*q,63)
            b=np.minimum(((a.astype(np.uint32)&31)+q//2)//q*q,31)
            expected=((r<<11)|(g<<5)|b).astype(np.uint16)
            np.testing.assert_array_equal(codec.decode(codec.encode(a,quant_step=q)),expected)
    def test_all_modes_selected(self):
        cases=[(codec.RAW,self.rng.integers(0,65536,(16,16),dtype=np.uint16),{}),
               (codec.FILL,np.zeros((16,16),np.uint16),{}),
               (codec.RLE,np.repeat(np.arange(16,dtype=np.uint16),16).reshape(16,16),dict(use_dpcm=False,use_palette=False)),
               (codec.PALETTE,np.indices((16,16)).sum(axis=0).astype(np.uint16)%2,{}),
               (codec.DPCM,np.tile(np.arange(16,dtype=np.uint16),(16,1)),dict(use_palette=False))]
        for mode,a,kwargs in cases:
            p=codec.encode(a,**kwargs)
            self.assertEqual(p[codec.HEADER.size],mode)
            np.testing.assert_array_equal(codec.decode(p),a)
    def test_bit_flips_and_truncation(self):
        p=codec.encode(self.rng.integers(0,65536,(17,19),dtype=np.uint16))
        for pos in range(len(p)):
            b=bytearray(p);b[pos]^=1
            with self.assertRaises(ValueError): codec.decode(b)
        for n in range(len(p)):
            with self.assertRaises(ValueError): codec.decode(p[:n])
        with self.assertRaises(ValueError): codec.decode(p+b'\0')
    def test_valid_crc_hostile_headers_and_tiles(self):
        p=codec.encode(np.zeros((16,16),np.uint16))
        for pos,val in ((4,2),(5,8),(6,0),(7,1),(8,0),(10,0),(codec.HEADER.size,255)):
            b=bytearray(p);b[pos]=val
            with self.assertRaises(ValueError): codec.decode(recalc(b))
        # Zero RLE count must not create an unbounded loop or incomplete tile.
        payload=codec.TILE_HEADER.pack(codec.RLE,4)+struct.pack('<HH',0,1)
        h=codec.HEADER.pack(codec.MAGIC,1,16,1,0,16,16,1,len(payload))
        with self.assertRaises(ValueError): codec.decode(recalc(h+payload+b'\0'*4))
        # DPCM out-of-range channels, bad Rice k, extra bytes/padding.
        for data in (bytes([7,0,0])+bytes(96),bytes([0,0,0])+bytes(96)):
            payload=codec.TILE_HEADER.pack(codec.DPCM,len(data))+data
            h=codec.HEADER.pack(codec.MAGIC,1,16,1,0,16,16,1,len(payload))
            with self.assertRaises(ValueError): codec.decode(recalc(h+payload+b'\0'*4))
    def test_wire_golden_raw_and_bounded_rice(self):
        a=np.array([[0x1234,0xABCD]],np.uint16)
        p=codec.encode(a,use_dpcm=False,use_palette=False)
        payload=b'\x00\x04\x00\x34\x12\xCD\xAB'
        header=codec.HEADER.pack(b'GBT1',1,16,1,0,2,1,1,len(payload))
        self.assertEqual(p,recalc(header+payload+b'\0'*4))
        # Explicit small codes and the escape-boundary code, MSB first.
        for code,k,expected in [('1',0,0),('01',0,1),('001',0,2),
                                ('0'*14+'1',0,14),('0'*15+'0001111',0,15),
                                ('0'*15+'1111110',0,126)]:
            bits=codec._Bits(codec._pack_bits_string(code))
            self.assertEqual(bits.rice(k),expected);bits.finish()
        for k in range(7):
            for value in range(127):
                bits=codec._Bits(codec._pack_bits_string(codec._RICE_STRINGS[k][value]))
                self.assertEqual(bits.rice(k),value);bits.finish()
        with self.assertRaises(ValueError): codec._Bits(bytes(2)).rice(0)
        with self.assertRaises(ValueError): codec._Bits(b'\xFF').finish()
    def test_valid_crc_fuzz_is_bounded(self):
        a=np.tile(np.arange(16,dtype=np.uint16),(16,1))
        p=codec.encode(a,use_palette=False)
        for _ in range(200):
            b=bytearray(p)
            pos=int(self.rng.integers(0,len(b)-4));b[pos]^=int(self.rng.integers(1,256))
            try:
                result=codec.decode(recalc(b))
                self.assertEqual(result.shape,a.shape)
            except ValueError:
                pass
    def test_input_validation(self):
        for a in (np.zeros((2,2),np.uint8),np.zeros((0,2),np.uint16),np.zeros((1,1,1),np.uint16)):
            with self.assertRaises(ValueError): codec.encode(a)
        for q in (0,33,1.5):
            with self.assertRaises(ValueError): codec.encode(np.zeros((1,1),np.uint16),quant_step=q)


if __name__=='__main__': unittest.main()
