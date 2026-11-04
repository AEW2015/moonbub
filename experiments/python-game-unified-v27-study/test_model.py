"""GM27 wire, exact-coefficient isolation and atomic composition checks."""
from dataclasses import replace
import struct
import unittest
import zlib
import numpy as np
import model as m
import protocol as p


def source(seed=27, shape=(64, 64)):
    rng = np.random.default_rng(seed)
    return tuple(m.ft.rgb_to_planes(rng.integers(0, 256, (*shape, 3), np.uint8)))


def qmap(w=64, h=64):
    return m.roi.declared_map(w, h, (), 8, 16)


def seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def changed_header(packet, index, value):
    fields = list(m.HEADER.unpack_from(packet)); fields[index] = value
    return seal(m.HEADER.pack(*fields) + packet[m.HEADER.size:-4])


def scalar(ref, vectors, bs):
    out = []
    for plane, image in enumerate(ref):
        h, w = image.shape; step = bs if plane == 0 else bs // 2
        d = 2 if plane == 0 else 4; pred = np.empty_like(image)
        for y in range(h):
            for x in range(w):
                dx, dy = map(int, vectors[y // step, x // step])
                ix, fx = divmod(dx, d); iy, fy = divmod(dy, d)
                total = sum(wx * wy * int(image[min(max(y + iy + oy, 0), h - 1), min(max(x + ix + ox, 0), w - 1)])
                            for oy, wy in ((0, d - fy), (1, fy))
                            for ox, wx in ((0, d - fx), (1, fx)))
                pred[y, x] = (total + d*d//2) // (d*d)
        out.append(pred)
    return tuple(out)


class UnifiedTests(unittest.TestCase):
    def assert_planes(self, a, b):
        for x, y in zip(a, b): np.testing.assert_array_equal(x, y)

    def fixture(self, fid=0, ref=None):
        packet, rebuilt, work = m.encode_planes(source(27+fid), ref, qmap(), frame_id=fid,
                         reference_id=m.NO_REF if ref is None else fid-1, motion_mode='zero')
        hud, _ = p.encode_hud((), frame_id=fid, width=64, height=64)
        return packet, rebuilt, work, hud

    def test_01_prediction_scalar_zero_integer_fractional_and_clamp(self):
        ref = source(shape=(34, 50))
        for bs in (16, 32):
            mw, mh = m._grid(50, 34, bs)
            for vector in ((0, 0), (4, -4), (1, -1), (-18, 18)):
                vectors = np.full((mh, mw, 2), vector, np.int8)
                self.assert_planes(m.predict(ref, vectors, bs), scalar(ref, vectors, bs))

    def test_02_compact_map_roundtrip_bounds_and_canonical_oracle(self):
        rng = np.random.default_rng(17)
        maps = [rng.integers(-18, 19, (8, 16, 2), np.int8),
                np.stack(np.meshgrid(np.arange(16)-8, np.arange(8)-4), axis=2).astype(np.int8),
                np.zeros((8, 16, 2), np.int8)]
        for a in maps:
            data, work = m.pack_vectors(a, True)
            np.testing.assert_array_equal(m.unpack_vectors(data, 16, 8), a)
            np.testing.assert_array_equal(m.old.unpack_vectors(data, 16, 8), a)
            self.assertEqual(len(data), min(v['bytes'] for v in work['candidates']))
        # Valid redundant dense spelling is accepted by the GM27 receive
        # grammar; encoder minimality remains a sender policy.
        dense_zero = b'\x01' + bytes(24)
        np.testing.assert_array_equal(m.unpack_vectors(dense_zero, 4, 3), np.zeros((3, 4, 2), np.int8))
        with self.assertRaises(ValueError): m.unpack_vectors_strict(dense_zero, 4, 3)
        for bad in (b'\x07', b'\x00\x13\x00', b'\x04\xff\xff', b'\x05\x07\x00'):
            with self.assertRaises(ValueError): m.unpack_vectors(bad, 4, 3)

    def test_03_key_roundtrip_distinct_profile_and_prepared_owner(self):
        prepared = m.analyze_planes(source(), None)
        packet, rebuilt, work = m.encode_prepared(prepared, qmap())
        got, meta = m.decode(packet)
        self.assert_planes(got, rebuilt)
        self.assertEqual(m.HEADER.unpack_from(packet)[:2], (b'GM27', 1))
        self.assertTrue(meta['key']); self.assertEqual(work['ec26_construct_calls'], 3)
        self.assertEqual(work['decoder_reference_sample_reads'], 0)
        with self.assertRaises(ValueError): m.old.parse(packet)
        with self.assertRaises(ValueError): m.encode_prepared(replace(prepared, owner=object()), qmap())
        for invalid in (-1, float('nan'), True):
            with self.assertRaises(ValueError): m.encode_prepared(prepared, qmap(), invalid)

    def test_04_fractional_reference_roundtrip_and_four_tap_work(self):
        ref = source(); vectors = np.full((2, 2, 2), (1, -1), np.int8)
        translated = m.predict(ref, vectors, 32)
        prepared = m.analyze_planes(translated, ref, frame_id=2, reference_id=0,
                                    block_size=32, motion_mode='global', motion_precision='half')
        np.testing.assert_array_equal(m.unpack_vectors(prepared.vector_bytes, 2, 2), vectors)
        packet, expected, work = m.encode_prepared(prepared, qmap())
        got, meta = m.decode(packet, ref, expected_reference_id=0)
        self.assert_planes(got, expected); self.assert_planes(got, translated)
        self.assertEqual(work['decoder_reference_sample_reads'], 4*6144)
        np.testing.assert_array_equal(meta['vectors'], vectors)

    def test_05_frozen_selected_coefficients_and_rdo_counter_parity(self):
        ref = source(); rng = np.random.default_rng(81)
        src = tuple(np.clip(a + rng.integers(-12, 13, a.shape), 0, 255).astype(np.int16) for a in ref)
        prepared = m.analyze_planes(src, ref, frame_id=1, reference_id=0, motion_mode='zero')
        for scale in (16, 32):
            q = np.full((4, 4), scale, np.uint8)
            frozen, oldout, oldwork = m.old.encode_prepared(prepared, q, rdo_lambda=1)
            packet, out, work = m.encode_prepared(prepared, q, rdo_lambda=1)
            a, b = m.old.parse(frozen), m.parse(packet)
            self.assert_planes(a['coefficients'], b['coefficients']); self.assert_planes(out, oldout)
            self.assertLessEqual(len(packet), len(frozen))
            self.assertEqual(work['rdo']['zeroed_blocks'], oldwork['rdo']['zeroed_blocks'])
            self.assertEqual(work['rdo']['cp02_probe_calls'], 0)
            self.assertGreater(work['rdo']['cp02_size_counter_blocks'], 0)
            self.assertEqual(work['actual_entropy_candidates'], sum(x['actual_entropy_candidates'] for x in work['planes']))
            for info in work['planes']:
                self.assertEqual(info['actual_entropy_candidates'], 1 + sum(t['representations'] for t in info['legacy_trials']))
                self.assertEqual(info['legacy_cp02_encode_calls'], sum(t['cp02_encode_calls'] for t in info['legacy_trials']))

    def test_06_ec26_exact_coefficients_and_block_major_stream(self):
        rng = np.random.default_rng(22)
        a = np.zeros((12, 8, 8), np.int16)
        a[:, 0, 0] = rng.integers(-2048, 2049, 12)
        a[::2, 2, 1] = rng.integers(-100, 101, 6)
        for coeff in (a, rng.integers(-2048, 2049, (12, 8, 8), np.int16)):
            wire = m.ec.encode_coefficients(coeff, 4, layout=0)
            np.testing.assert_array_equal(m._decode_plane(b'\x03'+wire, 12, 4), coeff)
            np.testing.assert_array_equal(np.stack(list(m.ec.iter_block_major(wire, 12, 4))), coeff)

    def test_07_malformed_dispatch_ec_layout_crc_and_padding(self):
        a = np.zeros((12, 8, 8), np.int16); a[:, 0, 0] = 1
        wire = m.ec.encode_coefficients(a, 4, layout=1)
        for bad in (b'\x04', b'\x03', b'\x02x', b'\x03'+wire,
                    b'\x03'+wire[:-1]+bytes((wire[-1]^1,))):
            with self.assertRaises(ValueError): m._decode_plane(bad, 12, 4)
        wire = m.ec.encode_coefficients(a, 4, layout=0)
        fields = list(m.ec.COEFF.unpack_from(wire)); fields[6] += 1
        bad = seal(m.ec.COEFF.pack(*fields)+wire[m.ec.COEFF.size:-4]+b'\0')
        with self.assertRaises(ValueError): m._decode_plane(b'\x03'+bad, 12, 4)

    def test_08_magic_version_geometry_crc_and_output_tag_reject(self):
        packet, _, _, _ = self.fixture()
        for bad in (changed_header(packet, 0, b'GM26'), changed_header(packet, 1, 2),
                    changed_header(packet, 6, 0), packet[:-1], packet[:-1]+bytes((packet[-1]^1,))):
            with self.assertRaises(ValueError): m.parse(bad)
        wrong = changed_header(packet, 11, b'x'*16)
        m.parse(wrong)
        with self.assertRaises(ValueError): m.decode(wrong)

    def test_09_exact_reference_id_epoch_and_content(self):
        _, ref, _, _ = self.fixture()
        packet, _, _, _ = self.fixture(1, ref)
        for kw in ({}, {'expected_reference_id': 1}, {'expected_reference_id': 0, 'expected_epoch': 2}):
            with self.assertRaises(ValueError): m.decode(packet, ref, **kw)
        wrong = [a.copy() for a in ref]; wrong[0][0, 0] ^= 1
        with self.assertRaises(ValueError): m.decode(packet, wrong, expected_reference_id=0)

    def test_10_pair_ack_gates_and_semantic_failure_atomicity(self):
        base, _, _, hud = self.fixture(); pair = p.encode_pair(base, hud, epoch=1, frame_id=0)
        rx = p.Receiver(width=64, height=64)
        for gates in ({'write_drained': False}, {'vblank': False}):
            with self.assertRaises(ValueError): rx.receive(pair, **gates)
            self.assertEqual(rx.banks, (None, None)); self.assertEqual(rx.last_frame_id, -1)
        # Header/CRC and pair bindings may pass while entropy is invalid. Full
        # receive must finish semantics/output checks before any publication.
        fields = m.HEADER.unpack_from(base); pos = m.HEADER.size+fields[-5]+fields[-4]
        body = bytearray(base[:-4]); body[pos] = 99; badbase = seal(bytes(body))
        m.parse_metadata(badbase)
        badpair = p.encode_pair(badbase, hud, epoch=1, frame_id=0)
        with self.assertRaises(ValueError): rx.receive(badpair)
        self.assertEqual(rx.banks, (None, None)); self.assertEqual(rx.last_frame_id, -1)
        _, _, ack = rx.receive(pair)
        self.assertEqual(pair[:4], b'CP27'); self.assertEqual(ack[:4], b'JA27')
        self.assertEqual(p.validate_ack(ack, pair)['frame_id'], 0)
        self.assertEqual(len(ack), 65); self.assertEqual(p.PAIR.size+4, 60)
        with self.assertRaises(ValueError): rx.receive(pair)

    def test_11_wrong_source_and_ack_leave_published_state(self):
        b, _, _, h = self.fixture(); first = p.encode_pair(b, h, epoch=1, frame_id=0)
        rx = p.Receiver(width=64, height=64); ref, _, ack = rx.receive(first)
        b, _, _, h = self.fixture(1, ref)
        wrong = p.encode_pair(b, h, epoch=1, frame_id=1, source_slot=1, destination_slot=0, key=False)
        before = rx.banks, rx.hud_id, rx.last_ack
        with self.assertRaises(ValueError): rx.receive(wrong)
        self.assertEqual((rx.banks, rx.hud_id, rx.last_ack), before)
        with self.assertRaises(ValueError): p.validate_ack(ack, wrong)
        good = p.encode_pair(b, h, epoch=1, frame_id=1, source_slot=0, destination_slot=1, key=False)
        _, _, newack = rx.receive(good)
        self.assertEqual(p.validate_ack(newack, good)['destination_slot'], 1)
        self.assertEqual(rx.banks[1].frame_id, 1)

    def test_12_complete_cap_and_pair_bindings(self):
        b, _, _, h = self.fixture(); pair = p.encode_pair(b, h, epoch=1, frame_id=0)
        with self.assertRaises(ValueError): p.parse_pair(pair+bytes(p.CAP+1-len(pair)))
        damaged = bytearray(pair[:-4]); damaged[p.PAIR.size+10] ^= 1
        with self.assertRaises(ValueError): p.parse_pair(seal(bytes(damaged)))
        fields = list(p.PAIR.unpack_from(pair)); fields[0] = b'CP26'
        with self.assertRaises(ValueError): p.parse_pair(seal(p.PAIR.pack(*fields)+pair[p.PAIR.size:-4]))


if __name__ == '__main__': unittest.main()
