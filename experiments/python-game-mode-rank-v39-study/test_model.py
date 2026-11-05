import unittest
import numpy as np
import helpers as h
model=h.module('rank39_test_model',h.HERE/'model.py')
arithmetic=h.module('rank39_test_frozen_arithmetic',h.HERE.parent/'python-game-binary-v38-study/decoder.py')

class RankTests(unittest.TestCase):
    def test_stable_distinct_clipped_prediction_rank_and_noncanonical_rejection(self):
        a=np.full((2,8,8),128,np.int16);b=a.copy();b[0]=140;c=b.copy();c[1]=120;d=c.copy()
        n,r=model.ranks_from_predictions([a,b,c,d],np.array([1,2],np.uint8))
        np.testing.assert_array_equal(n,[2,2]);np.testing.assert_array_equal(r,[1,1])
        with self.assertRaises(ValueError):model.ranks_from_predictions([a,b,c,d],np.array([2,3],np.uint8))
        n,r=model.ranks_from_predictions([a,a,a,a],np.zeros(2,np.uint8));self.assertTrue(np.all(n==1));self.assertFalse(np.any(r))
    def test_rank_unary_arithmetic_roundtrip_all_menus_and_zero_decision_menu(self):
        events=[(count,rank,position)for position in(1,2,3)for count in(1,2,3,4)for rank in range(count)]*9
        coder=h.binary.BinaryEncoder()
        for count,rank,position in events:model.emit_rank(coder,rank,count,position)
        data,bits=coder.finish();reader=arithmetic.ArithmeticReader(data,bits)
        for count,rank,position in events:
            actual=0
            if count>1:
                for decision in range(count-1):
                    bit=reader.decode(position*12+(count-2)*3+decision)
                    if not bit:break
                    actual+=1
            self.assertEqual(actual,rank)
        reader.finish();self.assertEqual(bits,coder.renorm+18)
        empty=h.binary.BinaryEncoder();model.emit_rank(empty,0,1,0);self.assertEqual(empty.decisions,0)
        for rank,count in((1,1),(-1,2),(4,4),(0,0)):
            with self.assertRaises(ValueError):model.emit_rank(empty,rank,count,0)
    def test_plane_exact_output_and_hidden_zero_event(self):
        base=np.full((16,16),128,np.int16);coeff=np.zeros((4,8,8),np.int16);coeff[0,0,0]=16
        modes=np.zeros(4,np.uint8);safe=np.zeros((2,2),bool);tables=np.repeat(h.m.ft.qtable(16)[None],4,axis=0)
        packet,output,work,menus,ranks=model.encode_plane(base,coeff,modes,tables,safe)
        expected=h.f.reconstruct_plane(base,coeff,modes,tables,safe)
        np.testing.assert_array_equal(output,expected);self.assertEqual(menus[0],1);self.assertEqual(packet[0],3)
        safe[0,0]=True;coeff[0]=0
        packet,output,work,menus,ranks=model.encode_plane(base,coeff,modes,tables,safe)
        self.assertTrue(np.all(output[:8,:8]==128));self.assertEqual(menus[0],0);self.assertEqual(work['visible_blocks'],3)

if __name__=='__main__':unittest.main()
