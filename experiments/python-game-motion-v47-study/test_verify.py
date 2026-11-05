"""Independent policy/state/strict-byte-choice checks without the v47 encoder."""
import json,unittest
import numpy as np
import verify as v

def first_source(fid=0):
    manifest=json.loads((v.SOURCE/'manifest.json').read_text());row=manifest['cases'][0]['frames'][fid]
    canvas=np.frombuffer(v.raw(row['canvas_rgb24'],v.SOURCE),np.uint8).reshape(480,720,3).copy()
    return row,tuple(np.asarray(p,np.int16)for p in v.m.ft.rgb_to_planes(canvas))

class MotionProofTests(unittest.TestCase):
    def test_strict_actual_complete_payload_ties(self):
        self.assertEqual(v.actual_winner([b'aa',b'bb',b'cc']),0)
        self.assertEqual(v.actual_winner([b'aaa',b'bb',b'cc']),1)
        self.assertEqual(v.actual_winner([b'aaa',b'bbb',b'c']),2)
        for options in([], [b'a',b'b'], [b'a',b'b',bytearray(b'c')], [b'a',b'b',b'']):
            with self.subTest(options=options),self.assertRaises(ValueError):v.actual_winner(options)
    def test_fresh_key_rederivation_matches_frozen_complete_CS37(self):
        _,source=first_source();control=json.loads((v.CONTROL/'results.json').read_text())['cases'][0]['rows'][0]
        hud=v.raw(control['hud_packets']['HX33_selected'],v.CONTROL)
        q=v.m.roi.declared_map(720,480,v.n.ROIS,8,16)
        prep=v.preparation(source,None,0,v.m.NO_REF,'zero');coeff,rev=v.selected_coefficients(prep,q)
        packet,pixels,payloads,_=v.expected_intermediate(prep,q,coeff,hud)
        archived=v.raw(control['attempts'][0]['packet'],v.CONTROL)
        self.assertEqual(packet,archived)
        expected,_,_=v.f.Receiver().receive(archived);v.rxproof.equal_planes(pixels,expected)
        self.assertEqual(len(payloads),3);self.assertEqual(len(rev),3);v.no_new_encoder()
    def test_quiet_threshold_uses_all_three_sampled_planes(self):
        reference=tuple(np.full(s,128,np.int16)for s in((480,720),(240,360),(240,360)))
        source=tuple(p.copy()for p in reference)
        self.assertTrue(v.quiet_mask(source,reference).all())
        for p in source:p+=2
        self.assertTrue(v.quiet_mask(source,reference).all())
        for p in source:p+=1
        self.assertFalse(v.quiet_mask(source,reference).any())
    def test_grid_search_reads_the_actual_canonical_reference(self):
        folder=v.BINARY;row=json.loads((folder/'results.json').read_text())['cases'][0]['rows'][0]
        rx=v.direct.Receiver();rx.receive(v.raw(row['packet'],folder));saved=tuple(p.copy()for p in rx.ref)
        _,source=first_source(1);prep=v.preparation(source,rx.ref,1,0,'global_grid')
        self.assertEqual(prep.reference_tag,v.m.C.reference_tag(rx.ref));self.assertEqual(prep.reference_id,0)
        v.check_search(prep,source,rx.ref,'global_grid')
        vectors=v.m.base.unpack_vectors(prep.vector_bytes,23,15);self.assertFalse(np.any(vectors%4))
        v.rxproof.equal_planes(rx.ref,saved);self.assertEqual(rx.last,0)
    def test_final_cap_rejection_does_not_publish_or_advance_HUD(self):
        rx=v.direct.Receiver();before=v.rxproof.snapshot(rx)
        with self.assertRaises(ValueError),v.rxproof.no_reencode():rx.receive(b'\0'*49153)
        v.rxproof.unchanged(rx,before)
    def test_only_declared_frozen_policy_is_accepted(self):
        _,source=first_source()
        with self.assertRaises(ValueError):v.preparation(source,None,0,v.m.NO_REF,'global_cross')

if __name__=='__main__':unittest.main()
