import unittest
import numpy as np
import model
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('cadence_benchmark_under_test',Path(__file__).with_name('benchmark.py'))
benchmark=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(benchmark)
from test_model import TickClock

class ReportingTests(unittest.TestCase):
    def test_pair_uses_retained_commit_hashes_not_private_oracle_rows(self):
        frames=[np.full((16,32,3),40+i,np.uint8) for i in range(9)]
        cases=[]
        for mode in ('gm','exact','gated'):
            r=model.run(frames,config=model.Config(width=32,height=16,codec_mode=mode,promotion_period=4,ui_rectangles=((0,0,16,8),)),clock_ns=TickClock())
            self.assertNotIn('expected_base',r['packets'][0])
            cases.append(dict(source='unit',profile=mode,mode=mode,exact_ui=True,result=r))
        for case in cases[1:]:
            p=benchmark.exact_pair(cases[0],case)
            self.assertTrue(p['matched_reference_base_exact_ids'])
            self.assertEqual(p['matched_reference_base_mismatches'],0)
            self.assertEqual(len(benchmark.brief(case)['profile']),len(case['profile']))
