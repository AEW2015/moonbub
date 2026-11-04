import unittest
from dataclasses import replace
import numpy as np
import model


def work(coeff):
    _,s=model.inverse(coeff)
    return {k:s[k] for k in ('blocks','zero','dc','general','first_mac','second_mac','nonzero_coeff','intermediate_nnz')}
def frame():
    rng=np.random.default_rng(19);a=rng.integers(-100,101,size=(4,8,8),dtype=np.int64);a[1:3]=0;a[1,0,0]=-999
    s=work(a)
    return dict(packet_bytes=2000,key=False,published=True,width=32,height=16,samples=768,selected_ui_pixels=32,
        stripes=[dict(plane=i%3,y=i*8,samples=256,blocks=4,refill_bytes=b,logical_bits=8*b,work=s) for i,b in enumerate([4,500,5,700,4,2])])

class StripeTests(unittest.TestCase):
    def test_sparse_exact_random_general_zero_dc_and_negative_rounding(self):
        rng=np.random.default_rng(19);a=rng.integers(-2048,2049,size=(200,8,8),dtype=np.int64)*rng.integers(1,256,size=(200,8,8))
        a[rng.random(a.shape)<.7]=0;a[:8]=0;a[1:8,0,0]=np.array([-522240,-16385,-8193,-1,1,8191,522240])
        got,s=model.inverse(a);np.testing.assert_array_equal(got,model.ft.inverse(a))
        self.assertGreater(s['zero'],0);self.assertGreater(s['dc'],0);self.assertGreater(s['general'],0)
        self.assertLess(sum(s['first_mac'])+sum(s['second_mac']),1024*s['general'])
    def test_all_dc_values_legal_quantizer_extreme(self):
        a=np.zeros((4097,8,8),np.int64);a[:,0,0]=np.arange(-2048,2049)*255
        got,s=model.inverse(a);np.testing.assert_array_equal(got,model.ft.inverse(a))
        self.assertEqual(s['zero'],1);self.assertEqual(s['dc'],4096);self.assertEqual(s['general'],0)
    def test_legal_width_bound_covers_bias_and_signed_products(self):
        b=model.legal_width_bounds();self.assertLessEqual(b['dequant_signed_bits'],32);self.assertLessEqual(b['intermediate_signed_bits'],32)
        self.assertLessEqual(b['accumulator_signed_bits'],40)
        a=np.full((2,8,8),522240,np.int64);a[1]*=-1
        _,s=model.inverse(a);self.assertLessEqual(s['rounding_bias_abs_upper'],b['second_biased_accumulator_abs_bound'])
    def test_invalid_geometry_and_no_remaining_memory_service(self):
        with self.assertRaises(ValueError):model.inverse(np.zeros((8,8),np.int64))
        for b in (replace(model.Budget(),effective_sdram_MBps=46.08),replace(model.Budget(),stripe_buffers=5),replace(model.Budget(),sparse=True,bypass=False)):
            with self.assertRaises(ValueError):b.validate()
    def test_existing_bypass_baseline_is_distinct_from_dense_diagnostic(self):
        a=np.zeros((4,8,8),np.int64);a[1,0,0]=100;a[2]=3;a[3,2,2]=4;s=work(a);b=model.Budget()
        old=model.block_cycles(s,replace(b,sparse=False));dense=model.block_cycles(s,replace(b,sparse=False,bypass=False));new=model.block_cycles(s,b)
        self.assertLess(old['total'],dense['total']);self.assertGreater(new['index_scan'],old['index_scan'])
        self.assertEqual(new['output'],old['output']);self.assertEqual(new['output'],256)
    def test_new_sparse_general_can_lose_when_dense_and_index_cost_paid(self):
        a=np.arange(64,dtype=np.int64).reshape(1,8,8)*31+5;s=work(a);b=replace(model.Budget(),wide_lanes=32)
        new=model.block_cycles(s,b);old=model.block_cycles(s,replace(b,sparse=False))
        self.assertGreaterEqual(new['total'],old['total'])
    def test_bounded_stripe_ownership_and_cost_order(self):
        r=model.schedule(frame());last={}
        for s in r['stripes']:
            if s['coefficient_slot'] in last:self.assertGreaterEqual(s['entropy_start_ms'],last[s['coefficient_slot']])
            last[s['coefficient_slot']]=s['done_ms']
            self.assertLessEqual(s['entropy_done_ms'],s['consumer_start_ms']);self.assertLessEqual(s['prediction_done_ms'],s['inverse_done_ms'])
            self.assertLessEqual(s['inverse_done_ms'],s['done_ms'])
        self.assertEqual(r['local_compressed_cache_bytes'],49152)
        self.assertEqual(r['local_buffer_total_bytes'],49152+r['local_coefficient_stripe_bytes']+r['local_reconstruction_stripe_bytes']+16+960+512+r['local_color_line_bytes']+r['local_ui_palette_bytes'])
        self.assertGreater(r['compressed_cache_load_ms'],0);self.assertEqual(r['compressed_cache_load_read_bytes'],2000)
    def test_memory_slowdown_and_prefetch_backpressure(self):
        f=frame();b=model.Budget();two=model.schedule(f,b);one=model.schedule(f,replace(b,stripe_buffers=1));slow=model.schedule(f,replace(b,effective_sdram_MBps=60))
        self.assertGreaterEqual(one['frame_done_ms'],two['frame_done_ms']);self.assertGreater(slow['frame_done_ms'],two['frame_done_ms'])
        self.assertGreater(two['entropy_backpressure_ms'],0)
    def test_uniform_counterfactual_conserves_each_plane_payload(self):
        f=frame();r=model.schedule(f,uniform=True)
        for p in range(3):self.assertAlmostEqual(sum(s['refill_bytes'] for s in f['stripes'] if s['plane']==p),sum(s['refill_bytes'] for s in r['stripes'] if s['plane']==p))
        self.assertNotEqual([s['refill_bytes'] for s in f['stripes']],[s['refill_bytes'] for s in r['stripes']])
    def test_baseline_false_boolean_configuration_is_valid(self):
        f=frame()
        for b in (replace(model.Budget(),sparse=False),replace(model.Budget(),sparse=False,bypass=False)):
            b.validate();r=model.schedule(f,b);self.assertGreater(r['frame_done_ms'],0)
    def test_compact_yuv_memory_preserves_canonical_tag_work(self):
        f=frame();base=model.schedule(f);compact=model.schedule(f,replace(model.Budget(),bytes_per_sample=1))
        self.assertEqual(compact['tag_canonical_hashed_bytes'],base['tag_canonical_hashed_bytes'])
        self.assertEqual(compact['reconstruction_write_bytes']*2,base['reconstruction_write_bytes'])
        self.assertEqual(compact['color_constant_multiplies'],base['color_constant_multiplies'])
        self.assertLess(compact['frame_done_ms'],base['frame_done_ms'])
    def test_display_only_ui_not_reference_traffic(self):
        f=frame();a=model.schedule(f);f['selected_ui_pixels']=64;b=model.schedule(f)
        self.assertEqual(a['tag_read_bytes'],b['tag_read_bytes']);self.assertEqual(a['prediction_read_bytes'],b['prediction_read_bytes'])
        self.assertEqual(a['reconstruction_write_bytes'],b['reconstruction_write_bytes']);self.assertEqual(b['ui_display_only_write_bytes']-a['ui_display_only_write_bytes'],64)
        self.assertGreater(b['frame_done_ms'],a['frame_done_ms'])

if __name__=='__main__':unittest.main()
