import unittest
import numpy as np
import model as m


class ContextTests(unittest.TestCase):
    def test_deletions_first_middle_last_all_and_empty(self):
        for seq in (np.array([1,0,-2,0,0,4,0],np.int16),np.zeros(97,np.int16)):
            for kr,kv in ((0,0),(3,4),(19,11)):
                oracle=m.BandIndex(seq,kr,kv)
                for start,stop in ((0,0),(0,1),(0,3),(2,6),(5,7),(0,len(seq))):
                    if stop>len(seq):continue
                    result=oracle.delete_interval(start,stop);changed=seq.copy();changed[start:stop]=0
                    self.assertEqual(result['new_bits'],m.full_bits(changed,kr,kv))

    def test_seeded_random_and_padding(self):
        rng=np.random.default_rng(30)
        for length in (1,43,129,1024):
            seq=rng.integers(-20,21,length,dtype=np.int16);seq[rng.random(length)<.85]=0
            for kr,kv in ((0,0),(2,3),(19,11)):
                index=m.BandIndex(seq,kr,kv)
                for _ in range(12):
                    a,b=sorted(rng.integers(0,length+1,2).tolist());candidate=seq.copy();candidate[a:b]=0
                    r=index.delete_interval(a,b);bits=m.full_bits(candidate,kr,kv)
                    self.assertEqual(r['new_bits'],bits)
                    self.assertEqual(r['new_stream_bytes'],2+(bits+7)//8)

    def test_long_run_escape_and_last_token_no_eob(self):
        seq=np.zeros(200000,np.int16);seq[[0,150000,199999]]=[1,-2048,2048]
        index=m.BandIndex(seq,0,0)
        for a,b in ((0,1),(149999,150001),(199999,200000),(0,200000)):
            candidate=seq.copy();candidate[a:b]=0
            self.assertEqual(index.delete_interval(a,b)['new_bits'],m.full_bits(candidate,0,0))

    def test_reject_domain_and_interval_errors(self):
        for seq in (np.zeros(1,np.float32),np.zeros((1,1),np.int16),np.array([2049],np.int16),np.zeros(0,np.int16)):
            with self.assertRaises(ValueError):m.BandIndex(seq,0,0)
        for kr,kv in ((20,0),(0,12),(-1,0),(True,0)):
            with self.assertRaises(ValueError):m.BandIndex(np.zeros(3,np.int16),kr,kv)
        index=m.BandIndex(np.zeros(3,np.int16),0,0)
        for start,stop in ((-1,1),(2,1),(0,4),(0.,1)):
            with self.assertRaises(ValueError):index.delete_interval(start,stop)


if __name__=='__main__':unittest.main()
