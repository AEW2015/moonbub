"""Frozen control parity, exact analysis ownership and deferred cap behavior."""
import unittest
import numpy as np
import helpers as h
model=h.bound('motion47_owned_model',h.HERE/'model.py',h)

def fixture():
    m=h.load(h.SOURCE/'manifest.json');c=h.load(h.CONTROL/'results.json');g=h.load(h.GOLDEN/'results.json')
    frame=m['cases'][0]['frames'][0];canvas=np.frombuffer(h.raw(frame['canvas_rgb24'],h.SOURCE),np.uint8).reshape(480,720,3).copy()
    source=tuple(v.astype(np.int16)for v in h.m.ft.rgb_to_planes(canvas));hud=h.raw(c['cases'][0]['rows'][0]['hud_packets']['HX33_selected'],h.CONTROL)
    return source,hud,h.raw(g['cases'][0]['rows'][0]['packet'],h.GOLDEN)

class MotionTests(unittest.TestCase):
    def test_key_zero_and_grid_golden_same_exact_CS38_packet(self):
        source,hud,golden=fixture();q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        ps=[h.analysis.analyze_planes(source,None),h.global_search.analyze_with(h.m,source,None,policy='global_grid',avoid_rects=h.n.ROIS)]
        for p in ps:
            intermediate,norm,coeff,payloads,work=model.encode_proposal(p,q,hud);packet,options,aw=model.transcode(intermediate,coeff,payloads)
            self.assertEqual(packet,golden);self.assertEqual(aw['AB38_encode_calls'],6)
            got=h.rx.Receiver().receive(packet)
            for a,b in zip(got[0],norm,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(got[2]['coefficients'],coeff,strict=True):np.testing.assert_array_equal(a,b)
            for option in options:
                lengths=[option['old_bytes']]+[x['payload_bytes']for x in option['trials']]
                self.assertEqual(option['selected'],min(range(3),key=lambda i:lengths[i]))
    def test_grid_owned_preparation_source_unchanged_and_integer_chroma_vectors(self):
        source,hud,golden=fixture();reference=h.rx.Receiver().receive(golden)[0];moved=tuple(np.roll(v,4 if i==0 else 2,axis=1)for i,v in enumerate(source));before=tuple(v.copy()for v in moved)
        p=h.global_search.analyze_with(h.m,moved,reference,frame_id=1,reference_id=0,policy='global_grid',avoid_rects=h.n.ROIS)
        self.assertIs(p.owner,h.m._PREPARED_OWNER);self.assertIsInstance(p,h.m.Prepared)
        mw,mh=h.m.base._grid(720,480,32);vectors=h.m.base.unpack_vectors(p.vector_bytes,mw,mh)
        self.assertTrue(np.any(vectors));self.assertFalse(np.any(vectors%4));self.assertLessEqual(np.max(np.abs(vectors.astype(np.int16))),16)
        for a,b,retained in zip(moved,before,p.source,strict=True):
            np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,retained);self.assertFalse(np.shares_memory(a,retained));self.assertFalse(retained.flags.writeable)
    def test_intermediate_cap_is_deferred_and_final_receiver_still_bounded(self):
        source,hud,golden=fixture();p=h.analysis.analyze_planes(source,None);q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
        intermediate,norm,coeff,payloads,work=model.encode_proposal(p,q,hud+b'x'*49152)
        self.assertTrue(work['intermediate_overcap']);self.assertGreater(len(intermediate),49152)
        final,options,aw=model.transcode(intermediate,coeff,payloads);self.assertFalse(aw['final_cap_fit'])
        rx=h.rx.Receiver()
        with self.assertRaises(ValueError):rx.receive(final)
        self.assertIsNone(rx.ref);self.assertIsNone(rx.hud);self.assertEqual(rx.last,-1)

if __name__=='__main__':unittest.main()
