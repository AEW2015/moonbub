from pathlib import Path
import json
import unittest
import verify as v
class AdmissionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((Path(__file__).parent/'results.json').read_text())
 def test_frozen_source_closure(self):v.check_sources(self.data)
 def test_actual_pairs_ACKs_rejected_fine_and_reference_lineage(self):self.assertEqual(v.replay(self.data)['selected_pairs'],192)
if __name__=='__main__':unittest.main()
