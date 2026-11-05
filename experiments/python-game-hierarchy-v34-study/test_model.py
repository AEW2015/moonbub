import importlib.util
from pathlib import Path
import struct
import unittest
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hm34_test_encoder', HERE/'model.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
d = m.decoder


def seal(mode, w, h, parent, payload):
    body = d.HEADER.pack(d.MAGIC, d.VERSION, mode, w, h, len(parent), len(payload))+parent+payload
    return body+struct.pack('<I', zlib.crc32(body))


class HM34Tests(unittest.TestCase):
    def test_full_geometry_sparse_dense_and_bounds(self):
        rng = np.random.default_rng(340)
        modes = set()
        for w, h in ((720, 480), (34, 50), (17, 33), (719, 479), (1, 1)):
            ps, cs = d.geometry(w, h)
            parent = rng.integers(-18, 19, ps+(2,), dtype=np.int8)
            child = np.repeat(np.repeat(parent, 2, 0), 2, 1)[:cs[0], :cs[1]].copy()
            for kind in range(3):
                if kind == 1:
                    child.reshape(-1, 2)[::61] = 0
                elif kind == 2:
                    child = rng.integers(-18, 19, cs+(2,), dtype=np.int8)
                packet, work = m.pack(parent, child, w, h, return_info=True)
                decoded, info = d.unpack(packet, w, h, return_info=True)
                np.testing.assert_array_equal(decoded, child)
                self.assertEqual(decoded.dtype, np.int8)
                self.assertEqual(len(packet), min(c['bytes'] for c in work['candidates']))
                self.assertEqual(work['selected_mode'], min(range(3), key=lambda i: work['candidates'][i]['bytes']))
                if info['parent'] is not None:
                    np.testing.assert_array_equal(info['parent'], parent)
                modes.add(info['mode'])
        self.assertEqual(modes, {0, 1, 2})
        # Flat and parent-mask both cost 30 actual bytes; stable ties choose flat.
        parent = np.array([[[1, -1], [-1, 1]], [[1, 1], [1, -1]]], np.int8)
        child = np.array([[[1, 1], [1, -1], [-1, 1]],
                          [[-1, 1], [1, -1], [-1, 1]],
                          [[1, 1], [1, 1], [1, -1]],
                          [[-1, -1], [1, 1], [1, -1]]], np.int8)
        packet, info = m.pack(parent, child, 34, 50, return_info=True)
        self.assertEqual([c['bytes'] for c in info['candidates']], [30, 33, 30])
        self.assertEqual(info['selected_mode'], 0)
        np.testing.assert_array_equal(d.unpack(packet, 34, 50), child)
        bad = np.zeros((1, 1, 2), np.int8)
        for w, h in ((0, 1), (721, 480), (720, 481), (True, 16)):
            with self.assertRaises(ValueError):
                m.pack(bad, bad, w, h)
        for values in (bad.astype(np.int16), np.full_like(bad, 19), np.zeros((2, 1, 2), np.int8)):
            with self.assertRaises(ValueError):
                m.pack(values, bad, 1, 1)

    def test_crc_exact_lengths_geometry_and_atomicity(self):
        parent = np.zeros((15, 23, 2), np.int8)
        child = np.zeros((30, 45, 2), np.int8)
        packet = m.pack(parent, child, 720, 480)
        before = (parent.tobytes(), child.tobytes())
        for i in range(len(packet)):
            damaged = bytearray(packet)
            damaged[i] ^= 1
            with self.assertRaises(ValueError):
                d.unpack(bytes(damaged), 720, 480)
        for cut in range(len(packet)):
            with self.assertRaises(ValueError):
                d.unpack(packet[:cut], 720, 480)
        for bad in (packet+b'\0', seal(3, 720, 480, b'', b'\0\0\0'),
                    seal(0, 718, 480, b'', b'\0\0\0'),
                    seal(0, 720, 480, b'\0', b'\0\0\0')):
            with self.assertRaises(ValueError):
                d.unpack(bad, 720, 480)
        self.assertEqual(before, (parent.tobytes(), child.tobytes()))

    def test_syntax_only_nonminimal_gm27_and_run_validation(self):
        # Dense zeros and split adjacent equal runs are structurally legal.
        w, h = 64, 32
        n = 8
        packets = (b'\x01'+bytes(2*n),
                   b'\x02'+struct.pack('<HbbHbb', 4, 0, 0, 4, 0, 0))
        original = m.frozen.pack_vectors
        m.frozen.pack_vectors = lambda *a, **k: (_ for _ in ()).throw(AssertionError('encoder called'))
        try:
            for payload in packets:
                np.testing.assert_array_equal(d.unpack(seal(0, w, h, b'', payload), w, h), np.zeros((2, 4, 2), np.int8))
        finally:
            m.frozen.pack_vectors = original
        for payload in (b'\x02'+struct.pack('<Hbb', 0, 0, 0),
                        b'\x02'+struct.pack('<Hbb', 9, 0, 0),
                        b'\x02'+struct.pack('<Hbb', 7, 0, 0),
                        b'\x00\x13\0', b'\x07',
                        b'\x03\0\0'+struct.pack('<Hbb', 8, 1, 0),
                        b'\x03\0\0'+struct.pack('<Hbb', 0, 0, 0)):
            with self.assertRaises(ValueError):
                d.unpack(seal(0, w, h, b'', payload), w, h)

    def test_sparse_refinement_escape_domain_padding_and_order(self):
        # A large geometry keeps hand-built malformed modes inside the cap.
        w, h, parent = 720, 480, b'\0\0\0'
        def sparse(count, kg, kx, ky, values):
            b = m.Bits()
            for value, n in values:
                b.put(value, n)
            return seal(1, w, h, parent, struct.pack('<HBBB', count, kg, kx, ky)+b.finish())
        # gap0, dx+1, dy0 => 0 | 110 | 0 using k=0.
        good = sparse(1, 0, 0, 0, [(0, 1), (6, 3), (0, 1)])
        child = d.unpack(good, w, h)
        self.assertEqual(child[0, 0].tolist(), [1, 0])
        bads = [sparse(1351, 0, 0, 0, []), sparse(1, 11, 0, 0, []),
                sparse(1, 0, 7, 0, []), sparse(1, 0, 0, 0, [(0, 3)]),
                sparse(1, 0, 0, 0, [(127, 7), (0, 11)]),
                sparse(1, 0, 0, 0, [(127, 7), (1350, 11)]),
                sparse(1, 0, 0, 0, [(0, 1), (127, 7), (73, 7), (0, 1)]),
                sparse(1, 0, 0, 0, [(0, 1), (127, 7), (38, 7), (0, 1)]),
                sparse(1, 0, 0, 0, [(0, 1), (6, 3), (0, 1), (1, 1)]),
                sparse(2, 10, 0, 0, [(0, 1), (1349 & 1023, 10), (6, 3), (0, 1)])]
        for packet in bads:
            with self.assertRaises(ValueError):
                d.unpack(packet, w, h)
        with self.assertRaises(ValueError):
            d.unpack(seal(1, w, h, parent, struct.pack('<HBBB', 0, 0, 0, 0)+b'\0'), w, h)

    def test_masks_partial_edges_and_gm27_packed_padding(self):
        w, h = 34, 50
        # Child (x=3,y=0) is outside ceil(34/16)=3. Parent group 1 mask bit1.
        b = m.Bits()
        b.put(0, 1)
        b.put(1, 1)
        b.put(2, 4)
        with self.assertRaises(ValueError):
            d.unpack(seal(2, w, h, b'\0\0\0', b'\0\0'+b.finish()), w, h)
        b = m.Bits()
        b.put(1, 1)
        b.put(0, 4)
        with self.assertRaises(ValueError):
            d.unpack(seal(2, w, h, b'\0\0\0', b'\0\0'+b.finish()), w, h)
        # Packed code 63 is forbidden even though it fits six bits.
        b = m.Bits()
        for value in [63]+[18]*23:
            b.put(value, 6)
        with self.assertRaises(ValueError):
            d.unpack(seal(0, w, h, b'', b'\4'+b.finish()), w, h)
        for values in ([(127, 7), (0, 7)], [(127, 7), (73, 7)]):
            b = m.Bits()
            for value, n in values:
                b.put(value, n)
            with self.assertRaises(ValueError):
                d.unpack_gm27(b'\5\0\0'+b.finish(), 3, 4)


if __name__ == '__main__':
    unittest.main()
