import ast
import struct
import zlib
import unittest
from pathlib import Path
import numpy as np
import model as m


def bits_data(mode, bits, ks=(0, 0)):
    bits += '0'*((-len(bits)) % 8)
    return bytes((mode, *ks)) + bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def explicit_rice(a, mode, ks):
    flat = a.reshape(-1, 2)
    streams = []
    for axis, k in enumerate(ks):
        streams.append(m.frozen._rice_axis(m.frozen._motion_deltas(flat, a.shape[1], axis, mode), k))
    bits = m.frozen._Bits()
    bits.bits = streams[0].bits+streams[1].bits
    return bytes((mode, *ks))+bits.finish()


def expanded_cases():
    zero = np.zeros((4, 4, 2), np.int8)
    dense = b'\x01'+zero.tobytes()
    split = b'\x02'+struct.pack('<HbbHbb', 8, 0, 0, 8, 0, 0)
    sparse = b'\x03\x00\x00'
    packed = m.frozen._Bits()
    for value in zero.reshape(-1):
        packed.put(int(value)+18, 6)
    return [('dense_global', dense, zero), ('split_rle', split, zero),
            ('sparse_global', sparse, zero), ('packed_global', b'\x04'+packed.finish(), zero),
            ('row_rice_nonoptimal_k', explicit_rice(zero, 5, (2, 1)), zero),
            ('median_rice_nonoptimal_k', explicit_rice(zero, 6, (2, 1)), zero)]


def negative_cases():
    return [
        ('empty', b'', 4, 4), ('mode', b'\x07', 4, 4),
        ('oversized', b'\x01'+bytes(33), 4, 4),
        ('global_length', b'\x00\x00', 4, 4),
        ('global_range', b'\x00\x13\x00', 4, 4),
        ('dense_length', b'\x01'+bytes(30), 4, 4),
        ('dense_range', b'\x01'+bytes((128,))+bytes(31), 4, 4),
        ('rle_record', b'\x02'+bytes(3), 4, 4),
        ('rle_zero', b'\x02'+struct.pack('<Hbb', 0, 0, 0), 4, 4),
        ('rle_overrun', b'\x02'+struct.pack('<Hbb', 17, 0, 0), 4, 4),
        ('rle_short', b'\x02'+struct.pack('<Hbb', 15, 0, 0), 4, 4),
        ('rle_range', b'\x02'+struct.pack('<Hbb', 16, 19, 0), 4, 4),
        ('sparse_short', b'\x03\x00', 4, 4),
        ('sparse_default_range', b'\x03\x00\x13', 4, 4),
        ('sparse_record', b'\x03'+bytes(5), 4, 4),
        ('sparse_redundant', b'\x03'+bytes(2)+struct.pack('<Hbb', 0, 0, 0), 4, 4),
        ('sparse_index', b'\x03'+bytes(2)+struct.pack('<Hbb', 16, 1, 0), 4, 4),
        ('sparse_range', b'\x03'+bytes(2)+struct.pack('<Hbb', 0, 19, 0), 4, 4),
        ('sparse_unsorted', b'\x03'+bytes(2)+struct.pack('<HbbHbb', 3, 1, 0, 2, 2, 0), 4, 4),
        ('sparse_duplicate', b'\x03'+bytes(2)+struct.pack('<HbbHbb', 3, 1, 0, 3, 2, 0), 4, 4),
        ('packed_domain', b'\x04\xfc\x00', 1, 1),
        ('packed_truncated', b'\x04\x00', 1, 1),
        ('packed_padding', b'\x04\x49\x21', 1, 1),
        ('rice_k', b'\x05\x07\x00', 4, 4),
        ('rice_truncated', b'\x06\x00\x00', 4, 4),
        ('rice_noncanonical_escape', bits_data(5, '1111111'+'0000000'+'0'*31), 4, 4),
        ('rice_escape_domain', bits_data(6, '1111111'+'1111111'+'0'*31), 4, 4),
        ('rice_reconstruction_range', bits_data(5, '1111111'+format(38,'07b')+'0'*31), 4, 4),
        ('rice_delta_domain', bits_data(5, '110111111'+'0'*31, (6, 0)), 4, 4),
        ('rice_padding', bits_data(5, '0'*32)[:-1]+b'\x01', 4, 4),
        ('rice_extra_byte', bits_data(5, '0'*32)+b'\x00', 4, 4),
    ]


class DecoderTests(unittest.TestCase):
    def test_valid_nonminimal_is_explicit_language_expansion(self):
        for name, packet, expected in expanded_cases():
            with self.subTest(name=name):
                np.testing.assert_array_equal(m.unpack_vectors(packet, 4, 4), expected)
                with self.assertRaises(ValueError):
                    m.frozen.unpack_vectors(packet, 4, 4)

    def test_malformed_syntax_rejects(self):
        for name, packet, mw, mh in negative_cases():
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.unpack_vectors(packet, mw, mh)

    def test_geometry_and_input_types(self):
        for mw, mh in [(0, 1), (-1, 1), (True, 1), (1.0, 1), (129, 1), (128, 128)]:
            with self.subTest(mw=mw, mh=mh), self.assertRaises(ValueError):
                m.unpack_vectors(b'\x00\x00\x00', mw, mh)
        for data in (bytearray(b'\x00\x00\x00'), memoryview(b'\x00\x00\x00'), None):
            with self.assertRaises(ValueError):
                m.unpack_vectors(data, 1, 1)

    def test_boundaries_all_modes(self):
        rng = np.random.default_rng(27)
        maps = [rng.integers(-18,19,(8,16,2),dtype=np.int8) for _ in range(8)]
        maps += [np.full((8,16,2), (-18,18), np.int8),
                 np.stack(np.meshgrid(np.arange(16)-8,np.arange(8)-4),axis=2).astype(np.int8),
                 rng.integers(-18,19,(1,16,2),dtype=np.int8).repeat(8,axis=0)]
        for a in maps:
            packet = m.frozen.pack_vectors(a)
            np.testing.assert_array_equal(m.unpack_vectors(packet,16,8), m.frozen.unpack_vectors(packet,16,8))
        for mode in (5, 6):
            for ks in ((0,0),(1,2),(3,3),(4,4)):
                a = np.zeros((4,4,2), np.int8)
                packet = explicit_rice(a, mode, ks)
                if len(packet)<=33:
                    np.testing.assert_array_equal(m.unpack_vectors(packet,4,4), a)

    def test_profile_decode_output_and_reference_guards(self):
        rng = np.random.default_rng(27)
        src = tuple(rng.integers(0,256,shape,dtype=np.int16) for shape in ((32,32),(16,16),(16,16)))
        q = m.frozen.roi.declared_map(32,32,(),8,16)
        reference = None
        for frame in range(2):
            packet, expected, _ = m.frozen.encode_planes(src, reference, q, frame_id=frame,
                reference_id=frame-1 if frame else m.frozen.NO_REF, motion_mode='zero')
            fields = list(m.HEADER.unpack_from(packet)); fields[:2] = [b'GM27',1]
            body = m.HEADER.pack(*fields)+packet[m.HEADER.size:-4]
            promoted = body+struct.pack('<I',zlib.crc32(body))
            got, _ = m.decode_frame(promoted, reference, expected_reference_id=frame-1 if frame else None)
            for a, b in zip(got, expected):
                np.testing.assert_array_equal(a,b)
            if frame:
                with self.assertRaises(ValueError):
                    m.decode_frame(promoted, reference, expected_reference_id=4)
                with self.assertRaises(ValueError):
                    m.decode_frame(promoted[:-1], reference, expected_reference_id=0)
            reference = expected

    def test_receiver_has_no_encoder_search_call(self):
        tree = ast.parse(Path(m.__file__).read_text())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertFalse(any((isinstance(n.func, ast.Name) and n.func.id in ('pack_vectors','_rice_axis','_motion_deltas'))
                             or (isinstance(n.func, ast.Attribute) and n.func.attr in ('pack_vectors','_rice_axis','_motion_deltas')) for n in calls))

    def test_new_profile_default_and_early_scope(self):
        src = tuple(np.full(shape,128,np.int16) for shape in ((32,32),(16,16),(16,16)))
        q = m.frozen.roi.declared_map(32,32,(),8,16)
        packet, _, _ = m.frozen.encode_planes(src,None,q)
        with self.assertRaises(ValueError):
            m.parse_frame(packet)
        with self.assertRaises(ValueError):
            m.replay_parse_gm26(packet, early=True)
        fields = list(m.HEADER.unpack_from(packet)); fields[:2] = [b'GM27',1]
        body = m.HEADER.pack(*fields)+packet[m.HEADER.size:-4]
        promoted = body+struct.pack('<I',zlib.crc32(body))
        np.testing.assert_array_equal(m.parse_frame(promoted)['vectors'],m.replay_parse_gm26(packet)['vectors'])

if __name__ == '__main__':
    unittest.main()
