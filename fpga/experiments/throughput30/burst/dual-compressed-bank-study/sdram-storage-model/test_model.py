import unittest
from fractions import Fraction
import model

class Budget(unittest.TestCase):
 def test_layout_contains_256k_banks_without_overlap(self):
  r={x['name']:x for x in model.layout(262144)}
  self.assertEqual(r['framebuffer0']['end_word_exclusive'],384000)
  self.assertEqual(r['compressed0']['start_word'],0x60000)
  self.assertEqual(r['compressed0']['end_word_exclusive'],0x80000)
  self.assertEqual(r['framebuffer1']['start_word'],0x80000)
  self.assertEqual(r['framebuffer1']['end_word_exclusive'],0x80000+384000)
  self.assertEqual(r['compressed1']['end_word_exclusive'],1<<20)
  with self.assertRaises(ValueError):model.layout(262160)
  with self.assertRaises(ValueError):model.layout(262145)

 def test_ideal_traffic_arithmetic(self):
  r=model.calculate(jpeg_bytes=30000,refresh=Fraction(60))
  self.assertEqual(r['scan_bursts_per_lcd_frame'],43200)
  self.assertEqual(r['pixel_requests_per_video_frame'],43200)
  self.assertEqual(r['jpeg_read_bursts_per_video_frame'],1875)
  self.assertEqual(r['payload_bytes_per_second']['scan_read'],41_472_000)
  self.assertEqual(r['payload_bytes_per_second']['pixel_write'],20_736_000)
  self.assertEqual(r['payload_bytes_per_second']['jpeg_read'],900_000)
  self.assertEqual(r['payload_bytes_per_second']['jpeg_write'],900_000)
  self.assertEqual(r['aggregate_payload_bytes_per_second'],64_008_000)
  self.assertAlmostEqual(r['hypothetical_controller_utilization'],64_008_000/200_000_000)

 def test_partial_jpeg_padded_to_full_bursts(self):
  r=model.calculate(jpeg_bytes=17)
  self.assertEqual(r['padded_jpeg_bytes_each_direction'],32)
  self.assertEqual(r['jpeg_write_requests_per_video_frame'],2)
  s=model.calculate(jpeg_bytes=17,pixel_burst=False,jpeg_write_burst=False,pixel_cycles=6,jpeg_write_cycles=6)
  self.assertEqual(s['jpeg_write_requests_per_video_frame'],16)
  self.assertEqual(s['payload_bytes_per_second']['jpeg_write'],32*30)
  self.assertEqual(s['payload_bytes_per_second']['pixel_write'],720*480*2*30)

 def test_capacity_and_invalid_rates_rejected(self):
  with self.assertRaises(ValueError):model.calculate(jpeg_bytes=262145)
  with self.assertRaises(ValueError):model.calculate(jpeg_bytes=0)
  with self.assertRaises(ValueError):model.calculate(fps=0)
  with self.assertRaises(ValueError):model.calculate(scan_cycles=7)
  with self.assertRaises(ValueError):model.calculate(jpeg_write_cycles=1)
  with self.assertRaises(ValueError):model.calculate(pixel_cycles=7)

 def test_hypothetical_scheduling_is_not_payload_fraction(self):
  r=model.calculate(jpeg_bytes=262144,scan_cycles=15,pixel_cycles=13,jpeg_read_cycles=15,jpeg_write_cycles=13)
  self.assertLess(r['raw_payload_fraction'],1)
  self.assertGreater(r['hypothetical_controller_utilization'],r['raw_payload_fraction'])
  self.assertGreater(r['hypothetical_controller_utilization'],0)
  # Huge cost demonstrates rate budget can fail despite raw payload <100%.
  fail=model.calculate(jpeg_bytes=262144,scan_cycles=40,pixel_cycles=40,jpeg_read_cycles=40,jpeg_write_cycles=40)
  self.assertGreater(fail['hypothetical_controller_utilization'],1)
  self.assertLess(fail['raw_payload_fraction'],1)

 def test_baseline_mmcm_exact_rational(self):
  self.assertAlmostEqual(float(model.BASELINE_REFRESH),65.076174,places=5)

if __name__=='__main__':unittest.main()
