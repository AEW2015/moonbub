"""Fresh key24/global-ID adapter and frozen-kernel temporal proof checks."""
import unittest
import numpy as np
import helpers as h
adapter=h.module('temporal59_owned_adapter_tests',h.HERE/'adapter.py')

class TemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=h.load(h.SOURCE/'manifest.json')['cases'][0];cls.control=h.load(h.CONTROL/'results.json')['cases'][0];cls.golden=h.load(h.GOLDEN/'results.json')['cases'][0]
    def test_window_preserves_global_ids_and_initial_key24_without_mutation(self):
        before=h.digest(str(self.source).encode());rows=adapter.triplets(self.source,self.control,self.golden)
        self.assertEqual([p[0]['id']for p in rows],list(range(24,48)));self.assertEqual(rows[0][1]['reference_id'],h.m.NO_REF)
        self.assertTrue(rows[0][1]['requested_key']);self.assertFalse(any(r[1]['requested_key']for r in rows[1:]));self.assertEqual(h.digest(str(self.source).encode()),before)
        self.assertEqual(h.kernel.__file__,str(h.HERE.parent/'python-game-quantized-motion-v53-study/model.py'))
    def test_bad_id_and_nonmatching_quantizer_are_rejected(self):
        source=dict(self.source);source['frames']=list(self.source['frames']);source['frames'][25]=dict(source['frames'][25],id=0)
        with self.assertRaises(ValueError):adapter.triplets(source,self.control,self.golden)
        control=dict(self.control);control['rows']=list(self.control['rows']);control['rows'][24]=dict(control['rows'][24],selected_background=32)
        with self.assertRaises(ValueError):adapter.triplets(self.source,control,self.golden)
    def test_frozen_kernel_encodes_fresh_key24_exactly_and_receives_initial_state(self):
        f,c,gold=adapter.triplets(self.source,self.control,self.golden)[0]
        canvas=np.frombuffer(h.raw(f['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy();source=tuple(v.astype(np.int16)for v in h.m.ft.rgb_to_planes(canvas))
        hud=h.raw(c['hud_packets']['HX33_selected'],h.CONTROL);zero,grid,q,costs,maps,vectors,work=h.kernel.prepare(source,None,frame_id=24,reference_id=h.m.NO_REF)
        self.assertFalse(any(m.any()for m in maps.values()));proposal=h.kernel.encode(zero,q,hud)
        self.assertEqual(proposal['packet'],h.raw(gold['packet'],h.GOLDEN));rx=h.rx.Receiver();rx.receive(proposal['packet'])
        self.assertEqual(rx.last,24);self.assertEqual(rx.rid,24);self.assertEqual(h.m.C.reference_tag(rx.ref).hex(),gold['normalized_tag'])

if __name__=='__main__':unittest.main()
