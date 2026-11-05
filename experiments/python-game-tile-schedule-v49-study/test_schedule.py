import unittest
import schedule as s
class Banks(unittest.TestCase):
 def test_one_bank_serial_and_two_overlap(self):
  a=s.simulate([10,10,10],[20,20,20],1);b=s.simulate([10,10,10],[20,20,20],2);self.assertEqual(a['component_finish_cycles'],90);self.assertEqual(b['component_finish_cycles'],70);self.assertEqual(a['coefficient_output_bank_bytes'],128);self.assertEqual(b['coefficient_output_bank_bytes'],256)
 def test_entropy_bottleneck_and_boundaries(self):
  for e,v in(([0,0],[0,0]),([100,1,1],[1,1,1]),([1,1,1],[100,1,1])):
   a=s.simulate(e,v,1);b=s.simulate(e,v,2);self.assertEqual(a['component_finish_cycles'],sum(e)+sum(v));self.assertLessEqual(b['component_finish_cycles'],a['component_finish_cycles']);self.assertGreaterEqual(b['component_finish_cycles'],max(sum(e),sum(v)))
 def test_invalid(self):
  for e,v,b in(([],[],1),([1],[1,2],1),([-1],[1],1),([1],[1],3)):
   with self.assertRaises(ValueError):s.simulate(e,v,b)
if __name__=='__main__':unittest.main()
