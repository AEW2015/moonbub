import struct
import unittest
import zlib
import numpy as np
import model as m


def source(seed=1, shape=(64, 64)):
    rgb = np.random.default_rng(seed).integers(0, 256, (*shape, 3), dtype=np.uint8)
    return tuple(m.ft.rgb_to_planes(rgb))


def mapped(w=64, h=64):
    return m.roi.declared_map(w, h, (), 8, 16)


def seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def scalar_prediction(reference, vectors, block_size):
    out = []
    for plane, ref in enumerate(reference):
        h, w = ref.shape
        bs = block_size if plane == 0 else block_size // 2
        p = np.empty_like(ref)
        for y in range(h):
            for x in range(w):
                dx, dy = (int(v) for v in vectors[y // bs, x // bs])
                if plane:
                    dx, dy = dx // 2, dy // 2
                p[y, x] = ref[min(max(y + dy, 0), h - 1), min(max(x + dx, 0), w - 1)]
        out.append(p)
    return tuple(out)


class MotionTests(unittest.TestCase):
    def test_key_and_p_roundtrip_and_immutable_inputs(self):
        a = source(); copies = [x.copy() for x in a]
        packet, reconstructed, _ = m.encode_planes(a, None, mapped())
        decoded, meta = m.decode(packet, expected_epoch=1)
        self.assertTrue(meta['key'])
        for expected, got, before, original in zip(reconstructed, decoded, copies, a):
            np.testing.assert_array_equal(expected, got)
            np.testing.assert_array_equal(original, before)
            self.assertFalse(got.flags.writeable)
        packet, reconstructed, _ = m.encode_planes(source(2), decoded, mapped(), frame_id=1, reference_id=0)
        got, _ = m.decode(packet, decoded, expected_epoch=1, expected_reference_id=0)
        for x, y in zip(got, reconstructed): np.testing.assert_array_equal(x, y)

    def test_zero_predictor_frozen_gm_coefficient_and_output_parity(self):
        a = source(); p, ref, _ = m.encode_planes(a, None, mapped())
        rgb = np.random.default_rng(5).integers(0, 256, (64, 64, 3), dtype=np.uint8)
        current = tuple(m.ft.rgb_to_planes(rgb))
        packet, output, _ = m.encode_planes(current, ref, mapped(), frame_id=1, reference_id=0, motion_mode='zero')
        frozen = m.gm.Encoder(); frozen.anchor_id, frozen._anchor = 0, ref
        prepared = frozen.analyze(rgb, 1, mode='zero')
        candidate = frozen.encode_candidate(prepared, mapped())
        decoded = m.parse(packet)
        for a, b in zip(candidate.coefficients, decoded['coefficients']): np.testing.assert_array_equal(a, b)
        expected = m.gm.reconstruct(candidate.coefficients, prepared.prediction, candidate.scale_map, 64, 64)
        for a, b in zip(output, expected): np.testing.assert_array_equal(a, b)

    def test_known_translation_is_exact_zero_residual_skip(self):
        _, ref, _ = m.encode_planes(source(), None, mapped())
        vectors = np.full((4, 4, 2), [2, -2], np.int8)
        current = m.predict(ref, vectors)
        packet, output, work = m.encode_planes(current, ref, mapped(), frame_id=1, reference_id=0)
        self.assertEqual(work['coefficient_bytes'], 3)
        self.assertEqual(work['vector_bytes'], 3)
        self.assertEqual(work['search']['candidate_vectors'], 81)
        for a, b in zip(current, output): np.testing.assert_array_equal(a, b)
        decoded, _ = m.decode(packet, ref, expected_reference_id=0)
        for a, b in zip(current, decoded): np.testing.assert_array_equal(a, b)

    def test_block_motion_and_border_chroma_match_scalar(self):
        ref = source(shape=(50, 66))
        for bs in (16, 32):
            mw, mh = m._grid(66, 50, bs)
            vectors = np.zeros((mh, mw, 2), np.int8)
            vectors[::2, ::2] = (-8, 8)
            vectors[1::2, 1::2] = (4, -6)
            a, b = m.predict(ref, vectors, bs), scalar_prediction(ref, vectors, bs)
            for x, y in zip(a, b): np.testing.assert_array_equal(x, y)

    def test_rle_dense_global_canonical_motion_maps(self):
        for vectors in (np.zeros((4, 4, 2), np.int8),
                        np.array([[[0, 0], [2, 0]] * 8], np.int8),
                        np.concatenate((np.zeros((1, 20, 2), np.int8), np.full((1, 20, 2), 2, np.int8)), axis=1)):
            h, w = vectors.shape[:2]
            data = m.pack_vectors(vectors)
            np.testing.assert_array_equal(m.unpack_vectors(data, w, h), vectors)
        with self.assertRaises(ValueError): m.unpack_vectors(b'\x02' + struct.pack('<Hbb', 15, 0, 0), 4, 4)
        with self.assertRaises(ValueError): m.unpack_vectors(b'\x01' + bytes(32), 4, 4)
        with self.assertRaises(ValueError): m.unpack_vectors(b'\x03', 4, 4)

    def test_vector_domain_and_geometry_bounds(self):
        ref = source()
        for bad in (np.full((4, 4, 2), 1, np.int16), np.full((4, 4, 2), 10, np.int16), np.full((4, 4, 2), 256, np.int16)):
            with self.assertRaises(ValueError): m.pack_vectors(bad)
            with self.assertRaises(ValueError): m.predict(ref, bad)
        with self.assertRaises(ValueError): m.predict(ref, np.zeros((4, 4, 2), np.int8), 24)
        with self.assertRaises(ValueError): m.encode_planes(source(), None, mapped(), motion_mode='unknown')
        with self.assertRaises(ValueError): m.encode_planes(source(), None, mapped(), epoch=True)

    def test_wrong_epoch_id_reference_bytes_and_crc_fail_closed(self):
        _, ref, _ = m.encode_planes(source(), None, mapped())
        packet, _, _ = m.encode_planes(source(2), ref, mapped(), frame_id=2, reference_id=0)
        old = [x.copy() for x in ref]
        for kwargs in (dict(expected_epoch=2, expected_reference_id=0), dict(expected_reference_id=1), {}):
            with self.assertRaises(ValueError): m.decode(packet, ref, **kwargs)
        changed = [p.copy() for p in ref]; changed[0][0, 0] ^= 1
        with self.assertRaises(ValueError): m.decode(packet, changed, expected_reference_id=0)
        for bad in (packet[:-1], packet + b'\0', packet[:-1] + bytes([packet[-1] ^ 1])):
            with self.assertRaises(ValueError): m.decode(bad, ref, expected_reference_id=0)
        for a, b in zip(ref, old): np.testing.assert_array_equal(a, b)

    def test_semantic_reconstruction_tag_failure_after_valid_crc(self):
        packet, _, _ = m.encode_planes(source(), None, mapped())
        values = list(m.HEADER.unpack_from(packet)); values[11] = b'x' * 16
        forged = seal(m.HEADER.pack(*values) + packet[m.HEADER.size:-4])
        with self.assertRaises(ValueError): m.decode(forged)

    def test_invalid_quant_map_and_plane_domain(self):
        with self.assertRaises(ValueError): m.encode_planes(source(), None, np.full((4, 4), 7, np.uint8))
        a = list(source()); a[1] = a[1].astype(np.float32)
        with self.assertRaises(ValueError): m.encode_planes(a, None, mapped())
        a = list(source()); a[0] = a[0].copy(); a[0][0, 0] = 256
        with self.assertRaises(ValueError): m.encode_planes(a, None, mapped())

    def test_structured_and_zero_plane_decoder_bounds(self):
        coeff = np.zeros((16, 8, 8), np.int16)
        for value in (-2, -1, 1, 2, 2047):
            coeff[3, 0, 0] = value
            packet, _ = m._encode_plane(coeff, 4)
            np.testing.assert_array_equal(m._decode_plane(packet, 16, 4), coeff)
        with self.assertRaises(ValueError): m._decode_plane(b'\x02\0', 16, 4)
        with self.assertRaises(ValueError): m._decode_plane(b'\x03', 16, 4)

    def test_shared_prepared_matches_repeated_analysis_for_every_map(self):
        a = source(); _, ref, _ = m.encode_planes(a, None, mapped())
        current = source(3)
        prepared = m.analyze_planes(current, ref, frame_id=1, reference_id=0)
        before = [p.copy() for p in prepared.raw_coefficients]
        self.assertEqual(prepared.work['forward_plane_calls'], 3)
        for q in (8, 16, 32):
            scale = np.full((4, 4), q, np.uint8)
            packet, planes, work = m.encode_prepared(prepared, scale)
            expected, expected_planes, _ = m.encode_planes(current, ref, scale, frame_id=1, reference_id=0)
            self.assertEqual(packet, expected)
            self.assertEqual(work['forward_plane_calls'], 0)
            self.assertTrue(work['analysis_paid_separately'])
            for a, b in zip(planes, expected_planes): np.testing.assert_array_equal(a, b)
        for a, b in zip(prepared.raw_coefficients, before): np.testing.assert_array_equal(a, b)

    def test_partial_macroblocks_actual_encode_decode(self):
        current = source(shape=(50, 66)); scale = mapped(66, 50)
        packet, ref, _ = m.encode_planes(current, None, scale, block_size=32)
        out, _ = m.decode(packet)
        for a, b in zip(ref, out): np.testing.assert_array_equal(a, b)
        packet, expected, _ = m.encode_planes(source(4, (50, 66)), ref, scale, frame_id=1, reference_id=0, block_size=32)
        out, _ = m.decode(packet, ref, expected_reference_id=0)
        for a, b in zip(expected, out): np.testing.assert_array_equal(a, b)

    def test_nibble_and_sparse_default_maps_are_minimal_and_bounded(self):
        vectors = np.array([[(x % 9 * 2 - 8, x // 9 % 9 * 2 - 8) for x in range(80)]], np.int8)
        packet = m.pack_vectors(vectors)
        self.assertEqual(packet[0], 3)
        self.assertEqual(len(packet), 81)
        np.testing.assert_array_equal(m.unpack_vectors(packet, 80, 1), vectors)
        sparse = np.zeros((10, 10, 2), np.int8)
        sparse[3, 5] = 2, -2
        packet = m.pack_vectors(sparse)
        self.assertEqual(packet[0], 4)
        self.assertEqual(len(packet), 5)
        np.testing.assert_array_equal(m.unpack_vectors(packet, 10, 10), sparse)
        for bad in (b'\x03' + b'\x94' * 80,
                    b'\x03' + b'\x49' * 80,
                    b'\x04\x44' + struct.pack('<HB', 100, 0x53),
                    b'\x04\x44' + struct.pack('<HB', 35, 0x44),
                    b'\x04\x44' + struct.pack('<HBHB', 35, 0x53, 35, 0x62)):
            with self.assertRaises(ValueError): m.unpack_vectors(bad, 10, 10)
        # A valid but more expensive dense representation is rejected.
        with self.assertRaises(ValueError): m.unpack_vectors(b'\x01' + sparse.tobytes(), 10, 10)

    def test_rdo_default_parity_key_is_unchanged_and_source_is_frozen(self):
        a = source()
        p = m.analyze_planes(a, None)
        original = [v.copy() for v in p.source]
        plain, _, _ = m.encode_prepared(p, mapped())
        explicit, _, work = m.encode_prepared(p, mapped(), rdo_lambda=0)
        strong, _, strong_work = m.encode_prepared(p, mapped(), rdo_lambda=1_000_000)
        self.assertEqual(plain, explicit)
        self.assertEqual(plain, strong)
        self.assertEqual(strong_work['rdo']['checked_blocks'], 0)
        self.assertEqual(work['rdo']['zeroed_blocks'], 0)
        self.assertEqual(p.work['source_array_bytes'], 64 * 64 * 3)
        a[0][0, 0] ^= 1
        for before, retained in zip(original, p.source):
            np.testing.assert_array_equal(before, retained)
            self.assertFalse(retained.flags.writeable)
        for value in (-1, float('nan'), float('inf'), True, 1_000_001):
            with self.assertRaises(ValueError): m.encode_prepared(p, mapped(), value)

    def test_rdo_skip_actual_decoder_loop_and_protected_priority(self):
        _, ref, _ = m.encode_planes(source(), None, mapped())
        p = m.analyze_planes(source(7), ref, frame_id=1, reference_id=0, motion_mode='zero')
        quant = np.full((4, 4), 16, np.uint8)
        quant[0, 0] = 8
        packet0, _, _ = m.encode_prepared(p, quant)
        packet, rebuilt, work = m.encode_prepared(p, quant, rdo_lambda=1_000_000)
        self.assertGreater(work['rdo']['zeroed_blocks'], 0)
        self.assertGreater(work['rdo']['cp02_probe_calls'], 0)
        self.assertLessEqual(len(packet), len(packet0))
        a, b = m.parse(packet0), m.parse(packet)
        for plane in range(3):
            protected = m.roi.block_scales(quant, 64, 64, plane) == 8
            np.testing.assert_array_equal(a['coefficients'][plane][protected], b['coefficients'][plane][protected])
        decoded, _ = m.decode(packet, ref, expected_reference_id=0)
        for a, b in zip(rebuilt, decoded): np.testing.assert_array_equal(a, b)
        mutated = [v.copy() for v in ref]; mutated[0][0, 0] ^= 1
        with self.assertRaises(ValueError): m.decode(packet, mutated, expected_reference_id=0)
        # Exact predictor has no nonzero coefficient to prune.
        p = m.analyze_planes(ref, ref, frame_id=2, reference_id=0, motion_mode='zero')
        packet, rebuilt, work = m.encode_prepared(p, quant, rdo_lambda=16)
        self.assertEqual(work['rdo']['zeroed_blocks'], 0)
        self.assertEqual(work['coefficient_bytes'], 3)


if __name__ == '__main__': unittest.main()
