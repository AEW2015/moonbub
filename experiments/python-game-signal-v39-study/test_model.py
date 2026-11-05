import unittest
import numpy as np
import helpers as h
model=h.module('signal39_test_model',h.HERE/'model.py')

class SignalTests(unittest.TestCase):
    def test_unrounded_proxy_distinguishes_DC_hidden_by_packet_byte_rounding(self):
        coefficients=np.zeros((2,8,8),np.int16);coefficients[1,0,0]=-29
        packet_bytes=h.m.counter.isolated_packet_bytes(coefficients)
        self.assertEqual(packet_bytes[0],packet_bytes[1])
        bits=model.coefficient_bits(coefficients)
        self.assertEqual(bits.tolist(),[35,41]);self.assertLess(bits[0],bits[1])
    def test_bit_proxy_reference_scalar_Rice_minimum(self):
        rng=np.random.default_rng(3901);values=rng.integers(-8,9,(12,8,8),dtype=np.int16)
        def rice(v,k,escape):return (v>>k)+1+k if(v>>k)<15 else 15+escape
        expected=[]
        for coeff in values:
            zig=coeff.reshape(-1)[h.m.counter.ZIGZAG];dc=int(zig[0]);mapped=2*dc if dc>=0 else-2*dc-1
            bits=32+min(rice(mapped,k,14)for k in range(14));terms=[[],[],[]];position=1
            for target in range(1,64):
                value=int(zig[target])
                if not value:continue
                run=target-position;bits+=2*(run//16)+5;position=target+1
                level=(2*value if value>=0 else-2*value-1)-1
                band=0 if target<=5 else 1 if target<=20 else 2;terms[band].append(level)
            if position<64:bits+=2
            for terms_in_band in terms:bits+=min(sum(rice(v,k,12)for v in terms_in_band)for k in range(12))
            expected.append(min(1024,bits))
        np.testing.assert_array_equal(model.coefficient_bits(values),expected)
    def test_distinct_alias_rank_counts_and_hidden_immediate_output(self):
        a=np.full((1,8,8),128,np.int16);b=np.full_like(a,96)
        canonical,menus,ranks,bits=model.menu_metadata([a,b,a,b])
        self.assertEqual(canonical.tolist(),[[True,True,False,False]])
        self.assertEqual(menus.tolist(),[2]);self.assertEqual(ranks.tolist(),[[0,1,0,1]])
        self.assertEqual(bits.tolist(),[[1,1,1,1]])
        source=np.full((16,16),96,np.int16);base=np.full_like(source,128);safe=np.array([True,False,False,False]);tables=np.repeat(h.m.ft.qtable(16)[None],4,0)
        for policy in('mode0control','lambda1','lambda4','lambda16'):
            coeff,out,modes,costs=model.encode_plane(source,base,tables,safe,policy)
            self.assertTrue(np.all(out[:8,:8]==128));self.assertFalse(np.any(coeff[0]));self.assertEqual(modes[0],0);self.assertFalse(np.any(costs[0]))
    def test_flat_fixture_fine_bits_choose_nonzero_prediction_without_source_mutation(self):
        source=np.full((16,16),96,np.int16);base=np.full_like(source,128);safe=np.zeros(4,bool);tables=np.repeat(h.m.ft.qtable(16)[None],4,0)
        saved=source.copy();ref=base.copy();_,_,control,_=model.encode_plane(source,base,tables,safe,'mode0control')
        _,_,spatial,_=model.encode_plane(source,base,tables,safe,'lambda1')
        self.assertFalse(np.any(control));self.assertGreater(np.count_nonzero(spatial),0)
        np.testing.assert_array_equal(source,saved);np.testing.assert_array_equal(base,ref)

if __name__=='__main__':unittest.main()
