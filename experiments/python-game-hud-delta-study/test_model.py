import struct
import unittest
import zlib

import numpy as np
import model as m


def packet(mode, width, height, payload, reference=m.ZERO_TAG, current=m.ZERO_TAG):
    b = m.HEADER.pack(m.MAGIC, m.VERSION, mode, width, height, len(payload), reference, current) + payload
    return b + m.CRC.pack(zlib.crc32(b) & 0xFFFFFFFF)


class DeltaTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(2104)
        self.base = self.rng.integers(0, 65536, (24, 160), dtype=np.uint16)

    def test_raw_exact_and_independent_copy(self):
        p = m.encode(self.base)
        self.assertEqual(m.inspect(p)["mode"], m.RAW)
        self.assertEqual(len(p), 50 + self.base.size * 2)
        actual = m.decode(p)
        np.testing.assert_array_equal(actual, self.base)
        actual[0, 0] ^= 1
        self.assertNotEqual(actual[0, 0], self.base[0, 0])

    def test_copy_exact_and_bound(self):
        p = m.encode(self.base, self.base)
        self.assertEqual(len(p), 50)
        self.assertEqual(m.inspect(p)["mode"], m.COPY)
        np.testing.assert_array_equal(m.decode(p, self.base), self.base)
        with self.assertRaises(ValueError):
            m.decode(p)
        wrong = self.base.copy()
        wrong[0, 0] ^= 1
        with self.assertRaises(ValueError):
            m.decode(p, wrong)

    def test_sparse_row_spans_exact_cost(self):
        current = self.base.copy()
        current[0, :3] ^= 1
        current[0, 5] ^= 65535
        current[23, 159] ^= 32768
        p = m.encode(current, self.base)
        self.assertEqual(m.inspect(p)["mode"], m.SPAN_XOR)
        self.assertEqual(m.inspect(p)["span_count"], 3)
        self.assertEqual(len(p), 50 + 2 + 3 * 6 + 5 * 2)
        np.testing.assert_array_equal(m.decode(p, self.base), current)
        self.assertEqual(m.encode(current, self.base), p)

    def test_noisy_candidate_falls_back_to_raw(self):
        current = np.bitwise_xor(self.base, np.uint16(1))
        p = m.encode(current, self.base)
        self.assertEqual(m.inspect(p)["mode"], m.RAW)
        self.assertEqual(m.inspect(p)["reference_tag"], m.ZERO_TAG.hex())
        np.testing.assert_array_equal(m.decode(p), current)

    def test_seeded_random_roundtrips_and_no_mutation(self):
        for i in range(60):
            h, w = int(self.rng.integers(1, 31)), int(self.rng.integers(1, 121))
            a = self.rng.integers(0, 65536, (h, w), dtype=np.uint16)
            b = a.copy()
            changes = int(self.rng.integers(0, b.size + 1))
            inds = self.rng.choice(b.size, changes, replace=False)
            b.flat[inds] ^= self.rng.integers(1, 65536, changes, dtype=np.uint16)
            old_a, old_b = a.copy(), b.copy()
            p = m.encode(b, a)
            np.testing.assert_array_equal(m.decode(p, a), b)
            np.testing.assert_array_equal(a, old_a)
            np.testing.assert_array_equal(b, old_b)
            self.assertLessEqual(len(p), 50 + 2 * b.size)

    def test_big_endian_noncontiguous_inputs(self):
        a = self.base.astype(">u2")[:, ::2]
        p = m.encode(a)
        np.testing.assert_array_equal(m.decode(p), a)
        self.assertEqual(p[m.HEADER.size:-4], a.astype("<u2").tobytes())
        self.assertEqual(m.content_tag(a), m.content_tag(a.astype("<u2")))

    def test_geometry_in_tag_and_reference(self):
        a = np.arange(24, dtype=np.uint16).reshape(4, 6)
        self.assertNotEqual(m.content_tag(a), m.content_tag(a.reshape(3, 8)))
        with self.assertRaises(ValueError):
            m.encode(a, a.reshape(3, 8))
        p = m.encode(a, a)
        with self.assertRaises(ValueError):
            m.decode(p, a.reshape(3, 8))

    def test_maximum_patch_and_extreme_words(self):
        a = np.full((32, 660), 65535, dtype=np.uint16)
        p = m.encode(a)
        self.assertEqual(len(p), m.MAX_PACKET)
        np.testing.assert_array_equal(m.decode(p), a)
        b = a.copy()
        b[31, 659] = 0
        np.testing.assert_array_equal(m.decode(m.encode(b, a), a), b)

    def test_bad_array_types_and_bounds(self):
        for a in (None, [[1]], np.zeros((1, 1), dtype=np.int16), np.zeros((1, 1), dtype=np.uint32),
                  np.zeros(4, dtype=np.uint16), np.zeros((1, 1, 1), dtype=np.uint16),
                  np.zeros((0, 10), dtype=np.uint16), np.zeros((1, 721), dtype=np.uint16),
                  np.zeros((481, 1), dtype=np.uint16), np.zeros((100, 220), dtype=np.uint16)):
            with self.assertRaises(ValueError):
                m.encode(a)

    def test_every_truncation_rejected(self):
        current = self.base.copy()
        current[1, 1:3] ^= 1
        p = m.encode(current, self.base)
        for i in range(len(p)):
            with self.assertRaises(ValueError):
                m.decode(p[:i], self.base)
        with self.assertRaises(ValueError):
            m.decode(p + b"x", self.base)

    def test_crc_and_header_corruption_rejected(self):
        p = m.encode(self.base)
        for index in (0, 4, 5, 6, 8, 10, 14, 30, 46, len(p) - 1):
            changed = bytearray(p)
            changed[index] ^= 1
            with self.assertRaises(ValueError):
                m.decode(bytes(changed))
        for mode, w, h, body in ((9, 1, 1, b""), (m.RAW, 0, 1, b""),
                                  (m.RAW, 1, 1, b""), (m.COPY, 1, 1, b"x")):
            with self.assertRaises(ValueError):
                m.inspect(packet(mode, w, h, body))
        with self.assertRaises(ValueError):
            m.inspect(bytearray(p))

    def test_reference_and_current_tags_rejected_without_input_mutation(self):
        current = self.base.copy()
        current[0, 0] ^= 1
        p = m.encode(current, self.base)
        wrong = self.base.copy()
        wrong[-1, -1] ^= 1
        snapshot = wrong.copy()
        with self.assertRaises(ValueError):
            m.decode(p, wrong)
        np.testing.assert_array_equal(wrong, snapshot)
        header = list(m.HEADER.unpack_from(p))
        header[-1] = bytes(16)
        body = m.HEADER.pack(*header) + p[m.HEADER.size:-4]
        bad = body + m.CRC.pack(zlib.crc32(body) & 0xFFFFFFFF)
        original_reference = self.base.copy()
        with self.assertRaises(ValueError):
            m.decode(bad, self.base)
        np.testing.assert_array_equal(self.base, original_reference)

    def test_span_grammar_rejections(self):
        def span(row, start, words, data):
            return m.SPAN.pack(row, start, words) + np.array(data, dtype="<u2").tobytes()
        cases = [b"", b"\0\0", b"\xff\xff", m.COUNT.pack(1) + b"x",
                 m.COUNT.pack(1) + span(2, 0, 1, [1]),
                 m.COUNT.pack(1) + span(0, 4, 1, [1]),
                 m.COUNT.pack(1) + span(0, 3, 2, [1, 1]),
                 m.COUNT.pack(1) + span(0, 0, 0, []),
                 m.COUNT.pack(1) + span(0, 0, 2, [1]),
                 m.COUNT.pack(1) + span(0, 0, 1, [0]),
                 m.COUNT.pack(1) + span(0, 0, 1, [1]) + b"x",
                 m.COUNT.pack(2) + span(0, 0, 1, [1]) + span(0, 0, 1, [1]),
                 m.COUNT.pack(2) + span(0, 0, 1, [1]) + span(0, 1, 1, [1]),
                 m.COUNT.pack(2) + span(1, 0, 1, [1]) + span(0, 0, 1, [1])]
        for body in cases:
            with self.assertRaises(ValueError):
                m.decode(packet(m.SPAN_XOR, 4, 2, body), np.ones((2, 4), dtype=np.uint16))

    def test_raw_wrong_reference_and_current_digest(self):
        a = np.ones((2, 2), dtype=np.uint16)
        with self.assertRaises(ValueError):
            m.decode(packet(m.RAW, 2, 2, a.tobytes(), reference=bytes([1]) * 16, current=m.content_tag(a)))
        with self.assertRaises(ValueError):
            m.decode(packet(m.RAW, 2, 2, a.tobytes()))


if __name__ == "__main__":
    unittest.main()
