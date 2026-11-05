"""Frozen-preset calibration, later-window inputs and exploratory anchor gates."""
import unittest
import numpy as np
import helpers as h
adapter=h.bound('filter62_owned_adapter_tests',h.HERE/'adapter.py',h)

class FilterTemporalTests(unittest.TestCase):
    def test_preset_and_later_source_identity_are_frozen(self):
        identity,strong=h.fixed_presets();self.assertEqual(strong,dict(name='strong',alpha=24,beta=12,strength=3))
        cases,anchors,missing=adapter.cases(False);case=next(c for c in cases if c['kind']=='custom'and c['policy']=='zero');words,rgb=adapter.originals(case['scene'])
        generator=adapter.presentations(case,words);p=next(generator);self.assertEqual(p['id'],24);self.assertIsNone(p['native_pts'])
        original=h.planes_digest(p['planes']);canon=h.canonical_digest(p['canonical']);Y,work=h.filt.filtered_luma(p['planes'][0],h.excluded(),strong)
        self.assertEqual(h.planes_digest(p['planes']),original);self.assertEqual(h.canonical_digest(p['canonical']),canon);self.assertFalse(Y.flags.writeable)
        self.assertEqual(h.io.equations(rgb[0],h.h.m.C.corpus.expand565(p['baseline']),None)[1]['active_SSE'],p['expected_quality']['active_squared_error'])
        generator.close()
    def test_native_PTS_is_mapped_to_global_source24_and_identity_matches(self):
        cases,anchors,missing=adapter.cases();case=next(c for c in cases if c['kind']=='native');words,rgb=adapter.originals(case['scene'])
        generator=adapter.presentations(case,words);p=next(generator)
        self.assertEqual((p['id'],p['native_pts']),(24,0));self.assertIsNone(p['canonical'])
        self.assertEqual(h.io.equations(rgb[0],h.h.m.C.corpus.expand565(p['baseline']),None)[1]['active_SSE'],p['expected_quality']['active_squared_error'])
        generator.close()
    def test_native_anchor_gate_uses_actual_cap_and_mean_before_filter(self):
        def p(i,bytes_,sse,cap=0):return dict(source='s',source_case=i,case=dict(codec='libx265',parameter=i,supported=True,summary=dict(complete_bytes=bytes_,active_squared_error=sse,active_channel_samples=100,cap_failures=cap)))
        chosen,rows=adapter.anchor([p(1,80,101),p(2,90,100,1),p(3,110,99),p(4,100,100)],100,100)
        self.assertEqual(chosen,3);self.assertEqual([r['eligible']for r in rows],[False,False,True,True])
        chosen,rows=adapter.anchor([p(1,80,101),p(2,90,100,1)],100,100);self.assertIsNone(chosen)
    def test_identity_filter_preserves_exact_luma_and_exclusion(self):
        identity,strong=h.fixed_presets();mask=h.excluded();Y=np.tile(np.arange(720,dtype=np.uint16)%256,(480,1)).astype(np.uint8);copy=Y.copy()
        out,work=h.filt.filtered_luma(Y,mask,identity);np.testing.assert_array_equal(out,Y);np.testing.assert_array_equal(Y,copy)
        filtered,work=h.filt.filtered_luma(Y,mask,strong);np.testing.assert_array_equal(filtered[mask],Y[mask])

if __name__=='__main__':unittest.main()
