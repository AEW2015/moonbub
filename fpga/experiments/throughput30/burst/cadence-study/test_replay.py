#!/usr/bin/env python3
import unittest
from pathlib import Path
from replay import read_frames,run

HERE=Path(__file__).resolve().parent

class ReplayTests(unittest.TestCase):
    def test_known_boundaries_and_overflow(self):
        for path,half in ((HERE/'verilator-65hz.log',17.029),(HERE/'verilator-60hz-hypothetical.log',18.470)):
            rows=read_frames(path)
            model=run(rows,half,1800)
            self.assertLessEqual(model['baseline_max_abs_error_cycles'],1)
            self.assertEqual(model['hypothetical_queue_overflow_count'],0)
            self.assertEqual(model['modeled_frames'],1800)
        slow=read_frames(HERE/'verilator-65hz.log')
        for row in slow:
            row['pending_cycle']=row['commit_cycle']+9000000
        self.assertGreater(run(slow,17.029,100)['hypothetical_queue_overflow_count'],0)

if __name__ == '__main__':unittest.main()
