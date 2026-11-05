import unittest
from unittest.mock import patch
import numpy as np
import helpers as h
model=h.module('analysis37_test_model',h.HERE/'model.py')

class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=h.load(h.n.V24/'results.json')['inputs'][0]['rows'][0];cls.source=h.n.source(src)
        cls.reference=tuple(v.copy() for v in cls.source)

    def test_exact_key_and_zeroP_contract_owned_arrays_no_old_predict_or_analyze(self):
        for ref,fid,rid in ((None,0,h.m.NO_REF),(self.reference,1,0)):
            expected=h.m.analyze_planes(self.source,ref,epoch=25,frame_id=fid,reference_id=rid,block_size=32,motion_mode='zero',penalty=0,motion_precision='half')
            with patch.object(h.m,'analyze_planes',side_effect=AssertionError('oldanalyze forbidden')),patch.object(h.m.base.old,'predict',side_effect=AssertionError('slowpredict forbidden')):
                actual=model.analyze_planes(self.source,ref,frame_id=fid,reference_id=rid)
            self.assertIsInstance(actual,h.m.Prepared);self.assertIs(actual.owner,h.m._PREPARED_OWNER)
            for name in ('epoch','frame_id','reference_id','width','height','key','block_size','motion_mode','reference_tag','vector_bytes'):
                self.assertEqual(getattr(actual,name),getattr(expected,name))
            for name in ('prediction','raw_coefficients','source'):
                for a,b in zip(getattr(actual,name),getattr(expected,name)):
                    np.testing.assert_array_equal(a,b);self.assertFalse(a.flags.writeable)
            for a,b in zip(actual.source,self.source):self.assertFalse(np.shares_memory(a,b))
            if ref is not None:
                for a,b in zip(actual.prediction,ref):self.assertFalse(np.shares_memory(a,b))
            self.assertEqual(actual.work['old_analyze_calls'],0)
            self.assertEqual(actual.work['old_four_tap_prediction_calls'],0)

    def test_identity_geometry_policy_and_sample_rejections_do_not_mutate_source(self):
        saved=tuple(v.copy() for v in self.source)
        for kwargs in ({'epoch':26},{'epoch':True},{'frame_id':True},{'frame_id':h.m.NO_REF},
                       {'reference_id':0},{'block_size':16},{'penalty':True},{'penalty':1},
                       {'motion_mode':'block'},{'motion_precision':'integer'}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):model.analyze_planes(self.source,None,**kwargs)
        for rid in (h.m.NO_REF,1,True,-1):
            with self.assertRaises(ValueError):model.analyze_planes(self.source,self.reference,frame_id=1,reference_id=rid)
        for bad in (self.source[:2],tuple(v.astype(float) for v in self.source),
                    (self.source[0][:-2],self.source[1],self.source[2]),
                    tuple(np.zeros(s,np.int16) for s in ((16,16),(8,8),(8,8)))):
            with self.assertRaises(ValueError):model.analyze_planes(bad,None)
        for a,b in zip(saved,self.source):np.testing.assert_array_equal(a,b)

    def test_prepared_remains_owned_after_source_mutation(self):
        mutable=tuple(v.copy() for v in self.source)
        p=model.analyze_planes(mutable,None)
        saved=tuple(v.copy() for v in p.source)
        for v in mutable:v[:]=0
        for a,b in zip(saved,p.source):np.testing.assert_array_equal(a,b)

if __name__=='__main__':unittest.main()
