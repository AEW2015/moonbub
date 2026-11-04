import itertools
import struct
import unittest
import zlib
import numpy as np
import model as m


def reseal(packet):
    return packet[:-4] + m.CRC.pack(zlib.crc32(packet[:-4]))


class GapSpanTests(unittest.TestCase):
    def test_exhaustive_partition_optimum(self):
        # Every nonempty binary mask through10pixels; independently enumerate
        # every partition of its sorted changed pixels, including nonminimal
        # splits inside contiguous runs. No encoded-size oracle is reused.
        checked = 0
        for width in range(1, 11):
            for mask in range(1, 1 << width):
                positions = [i for i in range(width) if mask >> i & 1]
                best = None
                for cuts in range(1 << (len(positions) - 1)):
                    start = positions[0]
                    cost = 0
                    for i in range(len(positions) - 1):
                        if cuts >> i & 1:
                            cost += 6 + 2 * (positions[i] - start + 1)
                            start = positions[i+1]
                    cost += 6 + 2 * (positions[-1] - start + 1)
                    best = cost if best is None else min(best, cost)
                row = np.array([bool(mask >> i & 1) for i in range(width)], np.uint16)
                actual = sum(6 + 2 * (b-a) for a, b in m.optimal_row_spans(row))
                self.assertEqual(actual, best)
                checked += 1
        self.assertEqual(checked, 2036)

    def test_gap_ties_and_short_gaps(self):
        for gap, count in ((0,1),(1,1),(2,1),(3,2),(4,2)):
            row = np.zeros(gap+2, np.uint16);row[0]=1;row[-1]=2
            self.assertEqual(len(m.optimal_row_spans(row)), count)

    def test_seeded_roundtrips_and_inputs_unchanged(self):
        rng = np.random.default_rng(2205)
        for i in range(60):
            ref = rng.integers(0,65536,(4,80),np.uint16)
            cur = ref.copy()
            cur[rng.random(cur.shape)<i/120] ^= np.uint16(65535)
            a,b=cur.copy(),ref.copy()
            packet=m.encode(cur,ref)
            np.testing.assert_array_equal(m.decode(packet,ref),cur)
            np.testing.assert_array_equal(cur,a);np.testing.assert_array_equal(ref,b)

    def test_raw_copy_noise(self):
        rng=np.random.default_rng(2)
        ref=np.zeros((24,160),np.uint16)
        cur=rng.integers(0,65536,ref.shape,np.uint16)
        self.assertEqual(m.inspect(m.encode(cur,ref))['mode'],m.RAW)
        self.assertEqual(len(m.encode(cur)),cur.nbytes+50)
        self.assertEqual(m.inspect(m.encode(ref,ref))['mode'],m.COPY)
        self.assertEqual(len(m.encode(ref,ref)),50)

    def test_noncontiguous_big_endian(self):
        a=np.arange(500,dtype='>u2').reshape(10,50)[:,::2]
        np.testing.assert_array_equal(m.decode(m.encode(a)),a)

    def test_all_truncations_and_crc_atomic(self):
        ref=np.zeros((4,80),np.uint16);cur=ref.copy();cur[1,1:4]=8
        packet=m.encode(cur,ref)
        for i in range(len(packet)):
            with self.assertRaises(ValueError):m.decode(packet[:i],ref)
        bad=packet[:-1]+bytes([packet[-1]^1])
        with self.assertRaises(ValueError):m.decode(bad,ref)
        self.assertFalse(np.any(ref))

    def test_wrong_reference_and_current_tags(self):
        ref=np.zeros((4,80),np.uint16);cur=ref.copy();cur[1,1:4]=8
        packet=m.encode(cur,ref);wrong=ref.copy();wrong[0,0]=1
        with self.assertRaises(ValueError):m.decode(packet,wrong)
        bad=bytearray(packet);bad[m.HEADER.size-1]^=1
        with self.assertRaises(ValueError):m.decode(reseal(bytes(bad)),ref)

    def test_bounds_and_types(self):
        for a in (np.zeros((1,721),np.uint16),np.zeros((480,720),np.uint16),np.zeros((0,2),np.uint16),np.zeros((2,2),np.int16),np.zeros((2,),np.uint16)):
            with self.assertRaises(ValueError):m.encode(a)
        maximum=np.zeros((32,660),np.uint16)
        np.testing.assert_array_equal(m.decode(m.encode(maximum)),maximum)
        with self.assertRaises(ValueError):m.decode(bytearray(m.encode(maximum)))

    def test_noncanonical_zero_endpoint_and_long_gap(self):
        ref=np.zeros((4,80),np.uint16);cur=ref.copy();cur[0,1]=7;cur[0,4]=8
        packet=m.encode(cur,ref)
        self.assertEqual(m.inspect(packet)['span_count'],1)
        # Zero first payload endpoint, with repaired CRC; must reject grammar.
        bad=bytearray(packet);offset=m.HEADER.size+m.COUNT.size+m.SPAN.size
        bad[offset:offset+2]=b'\0\0'
        with self.assertRaises(ValueError):m.decode(reseal(bytes(bad)),ref)
        # A separate hand-built long interior gap is a byte-cost tie/worse and
        # rejected as noncanonical even when its final image tag is correct.
        cur=ref.copy();cur[0,1]=7;cur[0,5]=8
        xor=(cur^ref)[0,1:6].astype('<u2').tobytes()
        payload=m.COUNT.pack(1)+m.SPAN.pack(0,1,5)+xor
        with self.assertRaises(ValueError):m.decode(m._pack(m.SPAN_XOR,cur,m.content_tag(ref),payload),ref)

    def test_unknown_mode_and_impossible_count(self):
        ref=np.zeros((4,80),np.uint16);cur=ref.copy();cur[0,1]=8
        packet=m.encode(cur,ref)
        bad=bytearray(packet);bad[5]=99
        with self.assertRaises(ValueError):m.inspect(reseal(bytes(bad)))
        bad=bytearray(packet);bad[m.HEADER.size:m.HEADER.size+2]=m.COUNT.pack(65535)
        with self.assertRaises(ValueError):m.inspect(reseal(bytes(bad)))


if __name__=='__main__':unittest.main()
