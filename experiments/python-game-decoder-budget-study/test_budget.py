from dataclasses import replace
import unittest
import budget

def trace():
    return dict(width=720,height=480,key=False,publication=True,packet_bytes=20000,plane_payload_bytes=19000,ui_pixels=21120,
                planes=[dict(blocks=5400,general_inverse=100,dc_only=100,zero=5200),
                        dict(blocks=1350,general_inverse=50,dc_only=50,zero=1250),
                        dict(blocks=1350,general_inverse=50,dc_only=50,zero=1250)])
class BudgetTests(unittest.TestCase):
    def test_inverse_counts_match_two_dense_8x8_passes(self):
        op=budget.operations(trace())
        self.assertEqual(op['inverse_multiply_accumulates'],200*2*8**3+200*2)
        self.assertEqual(op['dequantization_multiplications'],200*64+200)
        self.assertEqual(op['rgb_matrix_multiplications'],4*720*480)
        self.assertEqual(op['canonical_tag_input_bytes'],1036804)
    def test_packed_reference_traffic_and_hash_widening(self):
        t=trace();moves=budget.traffic(t)
        self.assertEqual(moves['prediction_reference_read'],518400)
        self.assertEqual(moves['publication_yuv_tag_read'],518400)
        self.assertEqual(moves['rgb565_display_write'],691200)
        t['key']=True;t['publication']=False
        self.assertEqual(budget.traffic(t)['prediction_reference_read'],0)
        self.assertEqual(budget.traffic(t)['publication_yuv_tag_read'],0)
    def test_nominal_scanout_independent_of_video_geometry(self):
        e=budget.estimate(trace())
        self.assertEqual(e['scanout_bytes_per_second'],46_080_000)
        self.assertEqual(e['scanout_cycles_per_second'],43_200_000)
        self.assertEqual(e['background_available_cycles_per_second'],53_800_000)
    def test_monotone_compute_and_memory_service(self):
        a=budget.Architecture();base=budget.estimate(trace(),a)
        for fast in [replace(a,dsp_lanes=16),replace(a,entropy_bits_per_cycle=8),replace(a,samples_per_cycle=4),replace(a,clock_hz=120_000_000),replace(a,read_burst_cycles=8,write_burst_cycles=8)]:
            self.assertLess(budget.estimate(trace(),fast)['serialized_planning_frame_ms'],base['serialized_planning_frame_ms'])
    def test_dense_worse_than_bypass_and_serial_not_roofline(self):
        t=trace();base=budget.estimate(t)
        for p in t['planes']:p.update(general_inverse=p['blocks'],dc_only=0,zero=0)
        dense=budget.estimate(t)
        self.assertGreater(dense['compute_cycles'],base['compute_cycles'])
        self.assertLess(dense['serialized_planning_fps'],dense['throughput_ceiling_roofline_fps'])
        self.assertFalse(dense['line_deadline_proven']);self.assertFalse(dense['hardware_fit_proven'])
    def test_scanout_saturation_and_bad_config(self):
        self.assertIsNone(budget.estimate(trace(),replace(budget.Architecture(),clock_hz=10_000_000))['serialized_planning_frame_ms'])
        for bad in [replace(budget.Architecture(),dsp_lanes=0),replace(budget.Architecture(),refresh_fraction=1),replace(budget.Architecture(),clock_hz=1.5)]:
            with self.assertRaises(ValueError):budget.estimate(trace(),bad)
    def test_capacity_explicit_and_exceeds_old_2mib_model(self):
        cap=budget.capacity()
        self.assertEqual(cap['packed8bit_two_reference_banks'],1_036_800)
        self.assertEqual(cap['three_panel_rgb565_buffers'],2_304_000)
        self.assertEqual(cap['two_compressed_ingress_slots'],98_304)
        self.assertGreater(sum(cap.values()),2*1024*1024)
        self.assertGreater(cap['local_four_patch_decoded_words'],0)
if __name__=='__main__':unittest.main()
