import struct
import unittest
import zlib
import numpy as np
import model as m


def repair(packet):
    return packet[:-4] + struct.pack('<I', zlib.crc32(packet[:-4]))


class MotionTests(unittest.TestCase):
    def test_seeded_roundtrips_and_no_larger_than_hd22(self):
        rng = np.random.default_rng(25)
        for shape in ((1, 1), (7, 19), (16, 32), (24, 160)):
            for _ in range(4):
                current = rng.integers(0, 65536, shape, np.uint16)
                ref = rng.integers(0, 65536, shape, np.uint16)
                for previous in (None, ref):
                    packet, info = m.encode_with_info(current, previous)
                    np.testing.assert_array_equal(m.decode(packet, previous), current)
                    self.assertLessEqual(len(packet), len(m.old.encode(current, previous)))
                    self.assertLessEqual(len(packet), m.MAX_PACKET)

    def test_copy_exact_and_wrong_reference(self):
        a = np.arange(160 * 24, dtype=np.uint16).reshape(24, 160)
        p = m.encode(a, a)
        self.assertEqual((m.inspect(p)['mode'], len(p)), (m.COPY, 50))
        with self.assertRaises(ValueError): m.decode(p)
        b = a.copy(); b[0, 0] ^= 1
        with self.assertRaises(ValueError): m.decode(p, b)

    def test_translation_selects_motion_and_is_exact(self):
        reference = np.random.default_rng(1).integers(0, 65536, (24, 160), np.uint16)
        current = m.predict(reference, 2, -1)
        packet, info = m.encode_with_info(current, reference)
        self.assertIn(info['mode'], ('global_motion', 'tile_motion'))
        self.assertLess(len(packet), len(m.old.encode(current, reference)))
        np.testing.assert_array_equal(m.decode(packet, reference), current)

    def test_tiled_motion_and_partial_tiles(self):
        reference = np.random.default_rng(2).integers(0, 65536, (19, 35), np.uint16)
        prediction = reference.copy()
        prediction[:8, :16] = m.predict(reference, 2, 1)[:8, :16]
        prediction[8:16, :16] = m.predict(reference, -2, 0)[8:16, :16]
        packet, info = m.encode_with_info(prediction, reference)
        np.testing.assert_array_equal(m.decode(packet, reference), prediction)
        self.assertEqual(info['tile_vectors'], 9)
        self.assertGreater(info['motion_compared_words'], 0)

    def test_rice_component_domain_and_exact_addition(self):
        rng = np.random.default_rng(3)
        ref = rng.integers(0, 65536, (9, 17), np.uint16)
        components = m._components(ref)
        cur = [np.clip(a + rng.integers(-1, 2, a.shape), 0, maximum).astype(np.uint16)
               for a, maximum in zip(components, (31, 63, 31))]
        current = (cur[0] << 11) | (cur[1] << 5) | cur[2]
        payload = m._rice_encode(current, ref)
        np.testing.assert_array_equal(m._rice_decode(payload, 9, 17, ref), current)
        p = m._pack(m.COMPONENT, current, m._tag(ref), payload)
        np.testing.assert_array_equal(m.decode(p, ref), current)
        self.assertEqual(m.inspect(p)['mode_name'], 'component_delta')

    def test_intra_component_left_is_exact(self):
        current = np.tile(np.arange(19, dtype=np.uint16), (7, 1))
        payload = m._rice_encode(current, left=True)
        p = m._pack(m.INTRA_COMPONENT, current, m.ZERO, payload)
        np.testing.assert_array_equal(m.decode(p), current)
        self.assertTrue(m.inspect(p)['independent'])

    def test_byte_rle_literal_zero_repeat_and_bounds(self):
        rng = np.random.default_rng(4)
        for data in (bytes(21120), b'\1' * 200, bytes(range(256)) * 2,
                     rng.integers(0, 256, 21120, np.uint8).tobytes(), b'abc\0\0def\0\0\0ghi'):
            encoded = m.rle_encode(data)
            self.assertEqual(m.rle_decode(encoded, len(data)), data)
            self.assertLessEqual(len(encoded), len(data) + (len(data) + 127) // 128)
        for data, n in ((b'\0', 1), (b'\xff', 2), (b'\x80', 2), (b'\xc0\0', 1)):
            with self.assertRaises(ValueError): m.rle_decode(data, n)

    def test_truncation_crc_extra_and_bad_geometry_reject(self):
        a = np.arange(45, dtype=np.uint16).reshape(5, 9)
        packet = m.encode(a)
        for n in range(len(packet)):
            with self.assertRaises(ValueError): m.decode(packet[:n])
        for p in (packet + b'x', packet[:-1] + bytes([packet[-1] ^ 1])):
            with self.assertRaises(ValueError): m.decode(p)
        fields = list(m.HEADER.unpack_from(packet)); fields[3] = 0
        bad = m.HEADER.pack(*fields) + packet[m.HEADER.size:]
        with self.assertRaises(ValueError): m.decode(repair(bad))

    def test_invalid_motion_vector_after_repaired_crc(self):
        a = np.arange(128, dtype=np.uint16).reshape(8, 16)
        p = m._pack(m.GLOBAL, a, m._tag(a), struct.pack('<bb', 5, 0) + b'\0\0\0')
        with self.assertRaises(ValueError): m.decode(p, a)

    def test_tile_count_and_run_coverage_reject_atomically(self):
        a = np.arange(128, dtype=np.uint16).reshape(8, 16)
        for field, count, vector in ((0, 2, b'\0\0'), (1, 1, m.RUN.pack(0, 0, 0)),
                                      (1, 1, m.RUN.pack(2, 0, 0)), (0, 1, b'\x7f\0')):
            payload = m.TILE.pack(16, 8, 4, field, count) + struct.pack('<I', len(vector)) + vector + b'\0\0\0'
            p = m._pack(m.TILED, a, m._tag(a), payload)
            before = a.copy()
            with self.assertRaises(ValueError): m.decode(p, a)
            np.testing.assert_array_equal(a, before)

    def test_rice_parameter_padding_and_reconstruction_reject(self):
        a = np.zeros((1, 1), np.uint16)
        payload = bytearray(m._rice_encode(a, a))
        payload[0] = 6
        with self.assertRaises(ValueError): m._rice_decode(bytes(payload), 1, 1, a)
        payload = bytearray(m._rice_encode(a, a)); payload[-1] |= 1
        with self.assertRaises(ValueError): m._rice_decode(bytes(payload), 1, 1, a)
        # delta +1 red at predictor red31 is outside the RGB565 component domain.
        high = np.array([[0xf800]], np.uint16)
        invalid = m.RICE.pack(0, 0, 0, 3, 1, 1) + bytes([0x20, 0x80, 0x80])
        with self.assertRaises(ValueError): m._rice_decode(invalid, 1, 1, high)

    def test_endian_noncontiguous_and_no_mutation(self):
        a = np.arange(200, dtype='>u2').reshape(10, 20)[:, ::2]
        ref = a.copy(); before, before_ref = a.copy(), ref.copy()
        p = m.encode(a, ref)
        np.testing.assert_array_equal(m.decode(p, ref), a)
        np.testing.assert_array_equal(a, before); np.testing.assert_array_equal(ref, before_ref)

    def test_maximum_geometry_and_wrong_input_type(self):
        a = np.zeros((24, 880), np.uint16)
        with self.assertRaises(ValueError): m.encode(a)
        for bad in (np.zeros((5, 9), np.uint8), np.zeros((5, 9, 1), np.uint16), [[1]]):
            with self.assertRaises(ValueError): m.encode(bad)
        a = np.zeros((480, 44), np.uint16)
        p = m.encode(a); np.testing.assert_array_equal(m.decode(p), a)


if __name__ == '__main__': unittest.main()
