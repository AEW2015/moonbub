"""Independent fine-bit scalar oracle, duplicate menu, and byte-tie regressions."""
import unittest
import numpy as np
import verify as v

class SignalTests(unittest.TestCase):
    def test_independent_scalar_and_vectorized_bits(self):
        rng=np.random.default_rng(39004)
        blocks=np.concatenate((np.zeros((1,8,8),np.int16),np.full((1,8,8),2048,np.int16),
                               rng.integers(-2048,2049,(11,8,8),dtype=np.int16)))
        blocks[2:8]*=rng.integers(0,2,blocks[2:8].shape,dtype=np.int16)
        expected=np.array([v.scalar_fine_bits(block) for block in blocks])
        np.testing.assert_array_equal(v.fine_bits(blocks),expected)
        self.assertEqual(int(expected[0]),35);self.assertEqual(int(expected[1]),1024)

    def test_old_packet_byte_tie_is_distinguished(self):
        blocks=np.zeros((2,8,8),np.int16);blocks[0,0,0]=-29
        packet_sizes=v.m.counter.isolated_packet_bytes(blocks)
        self.assertEqual(int(packet_sizes[0]),int(packet_sizes[1]))
        fine=v.fine_bits(blocks)
        self.assertEqual(fine.tolist(),[41,35])
        self.assertLess(int(fine[1])+1,int(fine[0]))

    def test_duplicate_flags_stable_rank_decisions_and_domains(self):
        a=np.zeros((8,8),np.int16);b=a+1;c=a+2
        flags,bits=v.predictor_menu([a,a,b,c])
        np.testing.assert_array_equal(flags,[1,0,1,1]);np.testing.assert_array_equal(bits,[1,1,2,2])
        flags,bits=v.predictor_menu([a,a,a,a])
        np.testing.assert_array_equal(flags,[1,0,0,0]);np.testing.assert_array_equal(bits,[0,0,0,0])
        for bad in (np.zeros((8,8),np.int16),np.zeros((0,8,8),np.int16),np.full((1,8,8),2049,np.int16),np.zeros((1,8,8),float)):
            with self.assertRaises(ValueError):v.fine_bits(bad)

if __name__=='__main__':unittest.main()
