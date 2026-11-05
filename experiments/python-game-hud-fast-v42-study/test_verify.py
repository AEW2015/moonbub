"""Exact wire, immutable accepted state and timing-evidence regressions."""
import unittest
import numpy as np
import verify as v

class HudTests(unittest.TestCase):
    def old_rows(self):
        folder=v.HERE.parent/'python-game-hud-runs-v33-study'
        return folder,v.load(folder/'results.json')['cases'][0]['rows']

    def test_equal_words_do_not_imply_equal_wire(self):
        folder,rows=self.old_rows();row=rows[0]
        a=v.raw(row['v32'],v.HERE.parent/'python-game-hud-v32-study');b=v.raw(row['packet'],folder)
        aw,_=v.hud.decode_hud(a,expected_epoch=25);bw,_=v.hud.decode_hud(b,expected_epoch=25)
        for x,y in zip(aw,bw):np.testing.assert_array_equal(x['words'],y['words'])
        with self.assertRaises(ValueError):v.exact_wire(a,b)
        v.exact_wire(b,b)

    def test_failed_or_forked_HUD_does_not_advance_accepted_state(self):
        folder,rows=self.old_rows();state=v.HudState();state.receive(v.raw(rows[0]['packet'],folder))
        saved=(state.reference,state.rid,state.last);snapshot=tuple(p['words'].copy() for p in state.reference)
        packet=v.raw(rows[1]['packet'],folder);bad=packet[:-1]+bytes([packet[-1]^1])
        with self.assertRaises(ValueError):state.receive(bad)
        branch=state.fork();branch.receive(packet)
        self.assertIs(state.reference,saved[0]);self.assertEqual((state.rid,state.last),saved[1:])
        for a,b in zip(state.reference,snapshot):np.testing.assert_array_equal(a['words'],b)
        with self.assertRaises(ValueError):state.receive(v.raw(rows[0]['packet'],folder))

    def test_timing_shape_medians_and_alternating_order(self):
        row=dict(id=0,paired_timing_ms={'slow':[3.,5.,4.],'fast':[2.,4.,3.]},
            paired_median_ms={'slow':4.,'fast':3.},paired_order=[['slow','fast'],['fast','slow'],['slow','fast']])
        self.assertEqual(v.paired_timings(row),{'slow':4.,'fast':3.})
        for values in ({'slow':[1.],'fast':[1.]},{'slow':[1.,2.,3.],'fast':[1.,True,3.]},
                       {'slow':[1.,2.,3.],'fast':[1.,float('nan'),3.]},{'slow':[1.,2.,3.],'fast':[1.,0.,3.]}):
            with self.assertRaises(ValueError):v.paired_timings(dict(row,paired_timing_ms=values))
        with self.assertRaises(AssertionError):v.paired_timings(dict(row,paired_order=[['fast','slow']]*3))

    def test_metadata_checker_retains_ties_rejections_and_sizes(self):
        old={'patches':[{'selected':0,'trials':[{'bytes':10},{'rejected':'code-depth'}]}],'encode_ms':100.}
        new={'patches':[{'selected':0,'trials':[{'bytes':10},{'rejected':'code-depth'}]}],'encode_ms':1.,'constructs':1}
        v.check_reference_metadata(old,new)
        wrong={'patches':[{'selected':1,'trials':[{'bytes':10},{'rejected':'code-depth'}]}]}
        with self.assertRaises(AssertionError):v.check_reference_metadata(old,wrong)

    def test_histogram_depth_limit_and_constant_bit_semantics(self):
        size,stats=v.huffman_plan(np.zeros(20,np.uint16))
        self.assertEqual(size,8);self.assertEqual(stats,dict(symbols=1,maximum_code_bits=1,coded_bits=0,values=20))
        fibonacci=[1,1]
        while len(fibonacci)<18:fibonacci.append(sum(fibonacci[-2:]))
        values=np.repeat(np.arange(18,dtype=np.uint16),fibonacci)
        with self.assertRaises(ValueError):v.huffman_plan(values)

    def test_rice_k_ties_and_empty_nonzero_channel(self):
        self.assertEqual(v.rice_plan(np.array([0,1,2,3])),(0,10))
        self.assertEqual(v.rice_plan(np.empty(0,np.int64)),(0,0))
        plan=v.channel_plan(np.zeros(16,np.uint16))
        self.assertEqual(plan['selected']['scheme'],1)
        self.assertEqual(plan['selected']['events'],0)
        self.assertEqual(plan['selected']['bytes'],15)

if __name__=='__main__':unittest.main()
