import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np
import roi_codec as rc

spec=importlib.util.spec_from_file_location('roi_benchmark_under_test',Path(__file__).with_name('benchmark.py'))
bench=importlib.util.module_from_spec(spec);sys.modules[spec.name]=bench;spec.loader.exec_module(bench)


class BudgetPolicyTests(unittest.TestCase):
    def test_real_candidates_respect_cap_and_charge_search(self):
        yy,xx=np.mgrid[:64,:80]
        rgb=np.stack(((xx*3+yy)%256,(yy*4+xx)%256,(xx+yy*3)%256),axis=-1).astype(np.uint8)
        rects=((0,0,16,16),);active=(0,0,80,64);mw,mh=rc.geometry(80,64)
        base=bench.evaluate(rgb,np.full((mh,mw),16,np.uint8),rects,active,False)
        finer=bench.evaluate(rgb,rc.declared_map(80,64,rects,8,16),rects,active,False)
        coarse=bench.evaluate(rgb,rc.declared_map(80,64,rects,8,32),rects,active,False)
        selected,record=bench.budget_policy(rgb,base,finer,coarse,rects,active,False)
        self.assertTrue(record['admitted'])
        self.assertIsNotNone(selected)
        self.assertLessEqual(selected['bytes'],base['bytes'])
        self.assertLessEqual(record['attempts'],bench.MAX_MIDPOINT_TRIALS+2)
        self.assertEqual(record['attempts'],len(record['candidates']))
        self.assertAlmostEqual(record['total_charged_encode_ms'],sum(r['encode_wall_ms'] for r in record['candidates']))
        self.assertAlmostEqual(record['total_reference_and_search_encode_ms'],record['total_charged_encode_ms']+base['encode_wall_ms'])
        self.assertEqual(int(selected['map'][0,0]),8)


if __name__=='__main__':unittest.main()
