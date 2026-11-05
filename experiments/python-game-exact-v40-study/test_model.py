import unittest
import numpy as np
import helpers as h
model=h.module('exact40_test_model',h.HERE/'model.py')

class ExactTests(unittest.TestCase):
    def test_full_output_equality_rejects_equal_scalar_source_error(self):
        zero=np.full((1,8,8),128,np.int16);control=zero.copy();control[0,0,0]=127
        alternate=zero.copy();alternate[0,0,0]=129
        self.assertEqual(int(np.square(control-zero).sum()),int(np.square(alternate-zero).sum()))
        canonical=np.ones((1,4),bool);exact,eligible=model.exact_eligibility([control,alternate,control.copy(),alternate.copy()],canonical)
        self.assertEqual(exact.tolist(),[[True,False,True,False]]);self.assertEqual(eligible.tolist(),exact.tolist())
    def test_duplicate_alias_cannot_win_even_if_proxy_is_artificially_lower(self):
        a=np.ones((1,8,8),np.int16);canonical=np.array([[True,False,True,False]])
        exact,eligible=model.exact_eligibility([a,a,a,a],canonical)
        choice=model.choose_modes(np.array([[50,1,60,0]]),np.zeros((1,4),np.int64),eligible)
        self.assertEqual(choice.tolist(),[0])
    def test_complete_packet_strict_guard_and_caps(self):
        self.assertEqual(model.choose_packet(b'abc',b'xyz'),'control')
        self.assertEqual(model.choose_packet(b'abc',b'xy'),'candidate')
        self.assertEqual(model.choose_packet(b'abc',bytes(49153)),'control')
        for control,candidate in((b'',b'x'),(bytearray(b'abc'),b'x'),(b'abc',b''),(b'abc',bytearray(b'x'))):
            with self.assertRaises(ValueError):model.choose_packet(control,candidate)
    def test_directional_flat_block_exactness_hidden_commit_and_ownership(self):
        source=np.full((16,16),96,np.int16);base=np.full_like(source,128);tables=np.repeat(h.m.ft.qtable(16)[None],4,0)
        for safe in(np.zeros(4,bool),np.array([True,False,False,False])):
            coeff,out,modes,costs,eligible=model.encode_plane(source,base,tables,safe)
            oldcoeff,expected,_,_,_=h.spatial.encode_plane(source,base,tables,safe,'mode0control')
            np.testing.assert_array_equal(out,expected);self.assertTrue(np.all(costs[~safe,0,5]==1))
            for block in np.flatnonzero(~safe):self.assertEqual(eligible[block,int(modes[block])],1)
            if safe[0]:self.assertTrue(np.all(out[:8,:8]==128));self.assertFalse(np.any(coeff[0]))
        self.assertTrue(np.all(source==96));self.assertTrue(np.all(base==128))

if __name__=='__main__':unittest.main()
