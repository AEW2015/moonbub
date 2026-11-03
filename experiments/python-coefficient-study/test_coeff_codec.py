import struct
import unittest
import zlib

import numpy as np

import coeff_codec as c


def crc(body):
    return bytes(body)+struct.pack('<I', zlib.crc32(body))


class CoefficientTests(unittest.TestCase):
    def test_extremes_and_row_reset(self):
        a = np.zeros((6, 8, 8), np.int16)
        a[:, 0, 0] = [-2048, 2048, -2048, 2048, -2048, 2048]
        a[0, 3, 3], a[1, 7, 7] = -2048, 2048
        packet = c.encode_coefficients(a, 3)
        self.assertTrue(np.array_equal(c.decode_coefficients(packet, 6, 3), a))
        self.assertLessEqual(len(packet), 128*6+c.PAYLOAD_OVERHEAD)
        self.assertNotEqual(packet, c.encode_coefficients(a, 2))

    def test_random_sparse_raw_and_padding(self):
        rng = np.random.default_rng(26)
        for n, width in ((1, 1), (6, 3), (10, 5), (90, 45)):
            for sparse in (True, False):
                a = rng.integers(-2048, 2049, (n, 8, 8), dtype=np.int16)
                if sparse:
                    a[rng.random(a.shape) < .9] = 0
                p = c.encode_coefficients(a, width)
                self.assertTrue(np.array_equal(c.decode_coefficients(p, n, width), a))
                self.assertLessEqual(len(p), n*128+26)
        self.assertEqual(c.COEFF.unpack_from(c.encode_coefficients(a, width))[2], 0)

    def test_rice_boundary_scalar_vectors(self):
        for escape, maximum in ((12, 4095), (14, 8192)):
            for k in range(12 if escape == 12 else 14):
                for value in sorted(set((0, 1, 14 << k, min(15 << k, maximum), maximum))):
                    if value > maximum:
                        continue
                    bits = c._Bits(c._pack(c._rice(value, k, escape)))
                    self.assertEqual(bits.rice(k, escape), value)
                    bits.finish()

    def test_input_bounds(self):
        a = np.zeros((2, 8, 8), np.int16)
        for bad, width in ((a.astype(np.int32), 1), (a, 3), (a, 0)):
            with self.assertRaises(ValueError):
                c.encode_coefficients(bad, width)
        a[0, 0, 0] = 2049
        with self.assertRaises(ValueError):
            c.encode_coefficients(a, 1)

    def test_malformed_crc_header_ranges_and_padding(self):
        a = np.zeros((2, 8, 8), np.int16)
        packet = c.encode_coefficients(a, 2)
        for length in range(len(packet)):
            with self.assertRaises(ValueError):
                c.decode_coefficients(packet[:length], 2, 2)
        for i in range(len(packet)):
            changed = bytearray(packet); changed[i] ^= 1
            with self.assertRaises(ValueError):
                c.decode_coefficients(changed, 2, 2)
        for field, value in ((2, 9), (3, 3), (4, 1), (5, 1), (6, 999)):
            header = list(c.COEFF.unpack_from(packet)); header[field] = value
            body = c.COEFF.pack(*header)+packet[c.COEFF.size:-4]
            with self.assertRaises(ValueError):
                c.decode_coefficients(crc(body), 2, 2)
        bad = bytearray(packet[:-4]); bad[-1] |= 1
        with self.assertRaises(ValueError):
            c.decode_coefficients(crc(bad), 2, 2)
        # Force three ZRLs then a fourth: 64 zero positions cannot fit63 AC.
        dc = b'\x00'+c._pack('11')
        ac = b'\x00\x00\x00'+c._pack('01'*4)
        body = c.COEFF.pack(b'CP02', 1, 1, 1, 1, 0, 2, len(ac))+b'\x00\x80'+ac
        with self.assertRaises(ValueError):
            c.decode_coefficients(crc(body), 1, 1)
        # Reconstructed DC beyond +2048 must fail even with a valid packet CRC.
        dc = b'\x00'+c._pack(c._rice(4098, 0, 14))
        ac = b'\x00\x00\x00'+c._pack('00')
        body = c.COEFF.pack(b'CP02', 1, 1, 1, 1, 0, len(dc), len(ac))+dc+ac
        with self.assertRaises(ValueError):
            c.decode_coefficients(crc(body), 1, 1)

    def test_frozen_rgb_reconstruction_edges(self):
        rng = np.random.default_rng(7)
        for h, w in ((2, 2), (18, 34), (32, 48)):
            rgb = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
            for scale in (1, 8, 16, 32, 128):
                packet = c.encode(rgb, scale)
                self.assertTrue(np.array_equal(c.decode(packet), c.frozen.reconstruct(rgb, scale)))

    def test_frame_semantic_mutations(self):
        packet = c.encode(np.zeros((18, 34, 3), np.uint8))
        rng = np.random.default_rng(20261103)
        for _ in range(100):
            body = bytearray(packet[:-4])
            index = int(rng.integers(0, len(body)))
            body[index] ^= 1 << int(rng.integers(0, 8))
            try:
                result = c.decode(crc(body))
                self.assertEqual(result.shape, (18, 34, 3))
            except ValueError:
                pass


if __name__ == '__main__':
    unittest.main()
