import unittest
from model import qualifies
class Gates(unittest.TestCase):
 def test_mean_peak_not_everyframe(self):
  args=([20,10],[1,1],[10,10],[10,30],[1,1]);self.assertTrue(qualifies(*args,'mean'));self.assertTrue(qualifies(*args,'mean_and_peak'));self.assertFalse(qualifies(*args,'every_frame'))
 def test_cap_and_rational_ties(self):
  args=([2,8],[2,4],[49152,49152],[4,16],[4,8])
  for g in('mean','mean_and_peak','every_frame'):self.assertTrue(qualifies(*args,g));self.assertFalse(qualifies(args[0],args[1],[49153,1],args[3],args[4],g))
 def test_invalid(self):
  with self.assertRaises(ValueError):qualifies([],[],[],[],[],'mean')
  with self.assertRaises(ValueError):qualifies([0],[0],[1],[0],[1],'mean')
  with self.assertRaises(ValueError):qualifies([0],[1],[1],[0],[1],'unknown')
if __name__=='__main__':unittest.main()
