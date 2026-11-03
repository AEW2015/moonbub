"""Arithmetic goldens, complete pixel reconstructions and hostile FT01 packets."""
import math
import struct
import unittest
import zlib

import numpy as np

import fixed_codec as ft


def recalc(data):
    return bytes(data[:-4])+struct.pack('<I',zlib.crc32(data[:-4]))


def make_frame(data, *, mode=1, scale=16):
    plane = ft.PLANE.pack(2,2,1,64,mode,len(data))+data
    # Chroma plane dimensions are1x1 but still one8x8coefficientblock.
    chroma = ft.PLANE.pack(1,1,1,64,mode,len(data))+data
    payload = plane+chroma+chroma
    body = ft.HEADER.pack(ft.MAGIC,1,scale,2,2,len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


class FixedArithmeticTests(unittest.TestCase):
    def test_constant_and_impulse_dct_known_math(self):
        constant = np.full((1,8,8),64,np.int64)
        coeff = ft.forward(constant)
        want = np.zeros((1,8,8),np.int64);want[0,0,0]=512
        np.testing.assert_array_equal(coeff,want)
        np.testing.assert_array_equal(ft.inverse(want),constant)
        impulse = np.zeros((8,8),np.int64);impulse[0,0]=127
        basis = np.array([[((1/math.sqrt(8)) if u==0 else .5)*math.cos((2*x+1)*u*math.pi/16)
                           for x in range(8)] for u in range(8)])
        floating = basis@impulse@basis.T
        # Quantized basis/pass rounding is deliberately differentfromfloating.
        self.assertLessEqual(float(np.max(np.abs(ft.forward(impulse)-floating))),1.2)

    def test_scalar_two_pass_rounding_golden(self):
        rng = np.random.default_rng(11)
        block = rng.integers(-128,128,(8,8),dtype=np.int64)
        first = [[(sum(int(ft.Q14[y,k])*int(block[k,x]) for k in range(8))+8192)>>14
                  for x in range(8)] for y in range(8)]
        second = [[(sum(first[y][k]*int(ft.Q14[x,k]) for k in range(8))+8192)>>14
                   for x in range(8)] for y in range(8)]
        np.testing.assert_array_equal(ft.forward(block),second)
        a = ft.forward(block)
        first_i = [[(sum(int(a[y,k])*int(ft.Q14[k,x]) for k in range(8))+8192)>>14
                    for x in range(8)] for y in range(8)]
        second_i = [[(sum(int(ft.Q14[k,y])*first_i[k][x] for k in range(8))+8192)>>14
                     for x in range(8)] for y in range(8)]
        np.testing.assert_array_equal(ft.inverse(a),second_i)

    def test_signed_quantizer_ties_and_tables(self):
        a = np.array([-5,-4,-3,-2,-1,0,1,2,3,4,5])
        np.testing.assert_array_equal(ft.round_quantize(a,2),[-3,-2,-2,-1,-1,0,1,1,2,2,3])
        np.testing.assert_array_equal(ft.qtable(16),ft.QY)
        np.testing.assert_array_equal(ft.qtable(16,True),ft.QC)
        self.assertEqual(int(ft.qtable(1).min()),1)
        self.assertEqual(int(ft.qtable(128).max()),255)

    def test_neutral_color_and_rgb565_output(self):
        for value in (0,100,128,255):
            rgb = np.full((16,16,3),value,np.uint8)
            y,cb,cr = ft.rgb_to_planes(rgb)
            self.assertTrue(np.all(y==value));self.assertTrue(np.all(cb==128));self.assertTrue(np.all(cr==128))
            result = ft.decode(ft.encode(rgb,16))
            # Frozenintegerpassrounding maps255to254 atstandardq16;
            # RGB565outputstillmapsboth toexactwhite.
            expected = 254 if value==255 else value
            np.testing.assert_array_equal(result,np.full_like(rgb,expected))
            # Independent explicitRGB565knownconstantword calculation.
            packed = ((result[...,0].astype(np.uint16)>>3)<<11)|((result[...,1].astype(np.uint16)>>2)<<5)|(result[...,2].astype(np.uint16)>>3)
            self.assertTrue(np.all(packed==((value>>3)<<11)|((value>>2)<<5)|(value>>3)))


class PacketTests(unittest.TestCase):
    def test_reconstruction_families_all_scales_padding(self):
        rng = np.random.default_rng(20261103)
        yy,xx = np.mgrid[:18,:30]
        images = [np.zeros((2,2,3),np.uint8),np.full((16,16,3),255,np.uint8),
                  rng.integers(0,256,(18,30,3),dtype=np.uint8),
                  np.stack((xx*8,yy*14,(xx+yy)*5),axis=-1).astype(np.uint8)]
        for scale in (1,8,16,32,128):
            for image in images:
                packet = ft.encode(image,scale)
                np.testing.assert_array_equal(ft.decode(packet),ft.reconstruct(image,scale))
                self.assertLessEqual(len(packet),ft.stats(packet)['raw_bound_bytes'])
                self.assertEqual(ft.decode(packet).dtype,np.uint8)

    def test_rice_all_values_and_zero_run_boundaries(self):
        for k in range(12):
            for value in (0,1,14,15,16,255,1024,4095):
                bits = ft._Bits(ft._pack_bits(ft._rice_string(value,k)))
                self.assertEqual(bits.rice(k),value)
                bits.finish()
        values = np.zeros(257,np.int32);values[0]=2048;values[-1]=-2048
        np.testing.assert_array_equal(ft._decode_entropy(ft._entropy(values),len(values)),values)
        zero64 = bytes([0])+ft._pack_bits('0'+format(63,'08b'))
        np.testing.assert_array_equal(ft.decode(make_frame(zero64)),np.full((2,2,3),128,np.uint8))

    def test_crc_trailing_truncation_header_and_plane_bounds(self):
        packet = ft.encode(np.full((2,2,3),128,np.uint8))
        for at in range(len(packet)):
            bad = bytearray(packet);bad[at] ^= 1
            with self.assertRaises(ValueError):ft.decode(bad)
        for n in range(len(packet)):
            with self.assertRaises(ValueError):ft.decode(packet[:n])
        with self.assertRaises(ValueError):ft.decode(packet+b'\0')
        for at,value in ((0,0),(4,2),(5,0),(6,3),(ft.HEADER.size,3),(ft.HEADER.size+4,0),(ft.HEADER.size+12,2)):
            bad = bytearray(packet);bad[at]=value
            with self.assertRaises(ValueError):ft.decode(recalc(bad))

    def test_entropy_overshoot_coefficients_padding_and_raw(self):
        for data in (bytes([12]),bytes([0]),bytes([0])+ft._pack_bits('0'+'11111111'),
                     bytes([0])+ft._pack_bits('1'+'0'*15+'000000000000')):
            with self.assertRaises(ValueError):ft.decode(make_frame(data))
        zeros = bytes([0])+ft._pack_bits('0'+format(63,'08b'))
        bad = bytearray(zeros);bad[-1]|=1
        with self.assertRaises(ValueError):ft.decode(make_frame(bad))
        with self.assertRaises(ValueError):ft.decode(make_frame(zeros+b'\0'))
        with self.assertRaises(ValueError):ft.decode(make_frame(np.full(64,2049,dtype='<i2').tobytes(),mode=0))
        with self.assertRaises(ValueError):ft.decode(make_frame(bytes(127),mode=0))
        raw = np.zeros(64,dtype='<i2').tobytes()
        np.testing.assert_array_equal(ft.decode(make_frame(raw,mode=0)),np.full((2,2,3),128,np.uint8))

    def test_invalid_inputs(self):
        for image in (np.zeros((3,4,3),np.uint8),np.zeros((4,3,3),np.uint8),np.zeros((2,2),np.uint8),
                      np.zeros((2,2,3),np.float32),np.zeros((720,480,4),np.uint8)):
            with self.assertRaises(ValueError):ft.encode(image)
        for q in (0,129,1.5,True):
            with self.assertRaises(ValueError):ft.encode(np.zeros((2,2,3),np.uint8),q)

    def test_valid_crc_mutations_bounded(self):
        rng = np.random.default_rng(9)
        packet = ft.encode(rng.integers(0,256,(16,16,3),dtype=np.uint8))
        for _ in range(200):
            bad = bytearray(packet);at=int(rng.integers(0,len(bad)-4));bad[at]^=int(rng.integers(1,256))
            try:
                out = ft.decode(recalc(bad))
                self.assertEqual(out.dtype,np.uint8)
                self.assertLessEqual(out.shape[0]*out.shape[1],ft.MAX_PIXELS)
            except ValueError:
                pass


if __name__ == '__main__':
    unittest.main()
