import unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.module('integrated38_test_model',h.HERE/'model.py')
analysis=h.module('integrated38_test_analysis',h.HERE.parent/'python-game-analysis-v37-study/model.py')
direct=h.module('integrated38_test_direct',h.HERE.parent/'python-game-direct-v37-study/model.py')
implicit=h.module('integrated38_test_implicit',h.HERE.parent/'python-game-implicit-v37-study/model.py')

class IntegratedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=h.load(h.n.V24/'results.json')['inputs'][0]['rows'][0];cls.source=h.n.source(src)
        cls.prepared=analysis.analyze_planes(cls.source,None)
        cls.q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        hu=h.load(h.HUD/'results.json')['cases'][0]['rows'][0];cls.hud=h.raw(hu['packet'],h.HUD)
    def test_exact_key_no_CN36_encode_parse_or_transcode(self):
        old=h.load(h.HERE.parent/'python-game-implicit-v37-study/results.json')['cases'][0]['rows'][0]
        expected=h.raw(old['packet'],h.HERE.parent/'python-game-implicit-v37-study')
        with patch.object(h.m,'encode_prepared',side_effect=AssertionError('fullencode forbidden')),patch.object(h.m,'parse',side_effect=AssertionError('parse forbidden')),patch.object(h.canonical,'wrap',side_effect=AssertionError('CN36wrapper forbidden')),patch.object(h.canonical,'parse',side_effect=AssertionError('CN36parse forbidden')),patch.object(h.entropy,'_construct',wraps=h.entropy._construct)as constructions:
            packet,planes,work=model.encode_prepared(self.prepared,self.q,self.hud)
            self.assertEqual(constructions.call_count,3)
        self.assertEqual(packet,expected)
        self.assertEqual(work['selected_plane_constructions'],3);self.assertEqual(work['discarded_plane_constructions'],0)
        self.assertEqual(work['CN36_intermediate_packets'],0);self.assertEqual(work['output_inverse_reconstructions'],1)
    def test_forced_global_RDO_reversion_before_hidden_and_exact_transcoder_parity(self):
        original=h.m.base._quantize(self.prepared.raw_coefficients,self.q,720,480);forced=tuple(c.copy()for c in original)
        for c,mask in zip(forced,h.canonical.HIDDEN):c[int(np.flatnonzero(~mask)[0]),0,1]+=1
        _,stats=h.m.counter.rdo_skip(self.prepared,original,self.q,1);real_plan=h.m.legacy_plan
        def plan(c,bw):
            answer=dict(real_plan(c,bw))
            if any(np.array_equal(c,v)for v in forced):answer['bytes']=100000000
            return answer
        with patch.object(h.m.counter,'rdo_skip',side_effect=lambda*args:(tuple(v.copy()for v in forced),dict(stats))),patch.object(h.m,'legacy_plan',side_effect=plan):
            cn36,_,_=direct.encode_prepared(self.prepared,self.q,self.hud);expected,_=implicit.transcode(cn36)
            packet,_,work=model.encode_prepared(self.prepared,self.q,self.hud)
        self.assertEqual(packet,expected);self.assertEqual(work['original_rdo_reversions'],[True,True,True])
    def test_complete_payload_ties_retain_fullgrid_without_losing_serialization(self):
        real=h.entropy._plane_plan;pending=[]
        def tie_plan(coeff,bw,m):
            plan=dict(real(coeff,bw,m))
            if bw!=1:pending.append(plan['bytes'])
            else:plan['bytes']=pending.pop(0)-1
            return plan
        with patch.object(h.entropy,'_plane_plan',side_effect=tie_plan),patch.object(h.entropy,'_construct',wraps=h.entropy._construct)as constructions:
            _,_,work=model.encode_prepared(self.prepared,self.q,self.hud)
            self.assertEqual(constructions.call_count,3)
        self.assertTrue(all(not p['implicit_selected']for p in work['planes']))
        self.assertTrue(all(p['fullgrid_payload_bytes']==p['compact_payload_bytes']for p in work['planes']))
    def test_invalid_inputs_and_source_ownership(self):
        before=tuple(c.copy()for c in self.prepared.raw_coefficients)
        for value in(-1,True,None,float('nan'),1000001):
            with self.assertRaises(ValueError):model.encode_prepared(self.prepared,self.q,self.hud,value)
        for hud in(b'',bytearray(self.hud),None):
            with self.assertRaises(ValueError):model.encode_prepared(self.prepared,self.q,hud)
        with self.assertRaises(ValueError):model.encode_prepared(None,self.q,self.hud)
        for a,b in zip(before,self.prepared.raw_coefficients):np.testing.assert_array_equal(a,b)

if __name__=='__main__':unittest.main()
