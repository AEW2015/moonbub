import unittest
import memory_budget as m
class Traffic(unittest.TestCase):
 def test_common_traffic_cancels_in_path_difference(self):
  expected=45388800
  for taps in(1,2,4):
   for packet in(0,20000,49152):
    a=m.traffic(30,60,taps,packet,1/24,'materialize_RGB565');b=m.traffic(30,60,taps,packet,1/24,'scan_YUV420');self.assertAlmostEqual(a['total_bytes_per_second']-b['total_bytes_per_second'],expected)
 def test_key_and_tap_bytes(self):
  for key_fraction in(0,.5,1):
   d=m.traffic(30,60,4,0,key_fraction,'scan_YUV420');self.assertEqual(d['bytes_per_second_by_operation']['reference_YUV_reads'],(1-key_fraction)*518400*30*4)
 def test_storage_and_domain(self):
  self.assertEqual(m.YUV,518400);self.assertEqual(m.RGB,691200);self.assertEqual(m.HUD,42240)
  for args in((0,60,1,0,0,'scan_YUV420'),(30,60,3,0,0,'scan_YUV420'),(30,60,1,0,2,'scan_YUV420'),(30,60,1,0,0,'invalid')):
   with self.assertRaises(ValueError):m.traffic(*args)
if __name__=='__main__':unittest.main()
