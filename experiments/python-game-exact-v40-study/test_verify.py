"""Exact state equality and strict integer serialized-size guard regressions."""
import unittest
import numpy as np
import verify as v

class ExactTests(unittest.TestCase):
    def test_strict_actual_integer_byte_guard_and_cap(self):
        self.assertTrue(v.candidate_wins(100,99))
        self.assertFalse(v.candidate_wins(100,100));self.assertFalse(v.candidate_wins(100,101))
        self.assertFalse(v.candidate_wins(49152,49153))
        for sizes in ((True,1),(2,True),(2.,1),(2,1.),(0,1),(1,0),(49153,1)):
            with self.assertRaises(ValueError):v.candidate_wins(*sizes)

    def test_same_SSE_is_not_full_block_equality(self):
        source=np.full((8,8),100,np.int16);control=source.copy();control[0,:2]=[99,101]
        alias=control.copy();alias[0,:2]=[101,99]
        self.assertEqual(int(np.square(source-control).sum()),int(np.square(source-alias).sum()))
        candidates=np.stack((control,alias,source,control.copy()))
        np.testing.assert_array_equal(v.exact_pixels(candidates,control),[True,False,False,True])
        with self.assertRaises(ValueError):v.exact_pixels(candidates[:3],control)

    def test_forked_loser_does_not_advance_committed_reference(self):
        folder=v.HERE.parent/'python-game-mode-rank-v39-study'
        rows=v.load(folder/'results.json')['cases'][0]['rows']
        receiver=v.rank.Receiver();receiver.receive(v.f.frozen.raw(rows[0]['packet'],folder))
        saved=(receiver.ref,receiver.hud,receiver.rid,receiver.last)
        packet=v.f.frozen.raw(rows[1]['packet'],folder)
        a=v.fork(receiver);b=v.fork(receiver)
        pa,_,_=a.receive(packet);pb,_,_=b.receive(packet)
        for x,y in zip(pa,pb):np.testing.assert_array_equal(x,y)
        self.assertIs(receiver.ref,saved[0]);self.assertIs(receiver.hud,saved[1]);self.assertEqual((receiver.rid,receiver.last),saved[2:])

if __name__=='__main__':unittest.main()
