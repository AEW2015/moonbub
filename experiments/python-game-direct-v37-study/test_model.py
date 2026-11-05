import unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.module('direct37_test_model',h.HERE/'model.py')

class DirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=h.load(h.n.V24/'results.json')['inputs'][0]['rows'][0]
        cls.source=h.n.source(src)
        cls.prepared=h.m.analyze_planes(cls.source,None,epoch=25,frame_id=0,reference_id=h.m.NO_REF,block_size=32,motion_mode='zero',motion_precision='half',penalty=0)
        cls.q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        hu=h.load(h.HUD/'results.json')['cases'][0]['rows'][0]
        cls.hud=h.raw(hu['packet'],h.HUD)

    def test_exact_archived_key_and_no_full_packet_encoder_or_syntax_decode(self):
        old=h.load(h.HERE.parent/'python-game-canonical-v36-study/results.json')['cases'][0]['rows'][0]
        expected=h.raw(old['skip']['packet'],h.HERE.parent/'python-game-canonical-v36-study')
        with patch.object(h.m,'encode_prepared',side_effect=AssertionError('full encode forbidden')),patch.object(h.m,'parse',side_effect=AssertionError('coeffparse forbidden')):
            wire,planes,work=model.encode_prepared(self.prepared,self.q,self.hud)
        self.assertEqual(wire,expected)
        self.assertEqual(work['full_packet_encode_calls'],0);self.assertEqual(work['coefficient_parse_calls'],0)
        self.assertEqual(work['output_inverse_reconstructions'],1)
        decoded,_=h.canonical.Receiver().receive(wire)
        for a,b in zip(planes,decoded):np.testing.assert_array_equal(a,b)

    def test_invalid_lambda_and_preparation_no_mutation(self):
        before=tuple(c.copy() for c in self.prepared.raw_coefficients)
        for value in (-1,float('nan'),1000001,None,True):
            with self.assertRaises(ValueError):model.encode_prepared(self.prepared,self.q,self.hud,value)
        with self.assertRaises(ValueError):model.encode_prepared(None,self.q,self.hud)
        for a,b in zip(self.prepared.raw_coefficients,before):np.testing.assert_array_equal(a,b)

    def test_quantized_plane_reversion_is_paid_before_hidden_suppression(self):
        # The real key frame exercises the exact unmasked decisions; compare
        # their visible coefficients after direct coding against frozen proof.
        full,_,_=h.m.encode_prepared(self.prepared,self.q)
        skip,_,_=h.canonical.skip_inner(full,self.prepared.prediction)
        wire,_,work=model.encode_prepared(self.prepared,self.q,self.hud)
        self.assertEqual(h.canonical.parse(wire)['inner'],skip)
        self.assertGreaterEqual(work['legacy_selection_plan_calls'],3)
        self.assertEqual(work['skip_entropy_plane_constructions'],3)
        # Retained frames happen to have no reversions. Force a visible RDO
        # change whose original plane wins the global legacy-size comparison;
        # exact sender behavior must revert BEFORE masking hidden blocks.
        original=h.m.base._quantize(self.prepared.raw_coefficients,self.q,720,480)
        forced=tuple(c.copy() for c in original)
        for c,mask in zip(forced,h.canonical.HIDDEN):
            index=int(np.flatnonzero(~mask)[0]);c[index,0,1]+=1
        _,rdo=h.m.counter.rdo_skip(self.prepared,original,self.q,1)
        real_plan=h.m.legacy_plan
        def controlled_plan(c,bw):
            answer=dict(real_plan(c,bw))
            if any(np.array_equal(c,v) for v in forced):answer['bytes']=100000000
            return answer
        def controlled_rdo(*args):return tuple(c.copy() for c in forced),dict(rdo)
        with patch.object(h.m.counter,'rdo_skip',side_effect=controlled_rdo),patch.object(h.m,'legacy_plan',side_effect=controlled_plan):
            full,_,_=h.m.encode_prepared(self.prepared,self.q)
            expected,_,_=h.canonical.skip_inner(full,self.prepared.prediction)
            wire,_,work=model.encode_prepared(self.prepared,self.q,self.hud)
        self.assertEqual(work['original_rdo_reversions'],[True,True,True])
        self.assertEqual(h.canonical.parse(wire)['inner'],expected)

if __name__=='__main__':unittest.main()
