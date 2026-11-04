import json
from pathlib import Path
import unittest
import verify as v

class RetainedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((Path(__file__).parent/'results.json').read_text())
 def test_source_closure(self):v.check_sources(self.data)
 def test_key_reference_and_slot_lineage(self):v.check_lineage(self.data)
 def test_all_retained_packets_quality_and_fine_key_maps(self):self.assertEqual(v.replay(self.data)['replayed_packets'],288)
if __name__=='__main__':unittest.main()
