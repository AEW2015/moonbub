"""Small synthetic tests for phase-window boundaries and invalid timing."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('cadence',Path(__file__).with_name('analyze-cadence.py'))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def records():
    return [{'frame_id':i+1, 'arrival_cycle':i*10_000_000//3,
             'present_cycle':i*10_000_000//3+2_000_000} for i in range(1800)]


class CadenceTests(unittest.TestCase):
    def test_window_boundary_and_phase(self):
        rows=records(); rows[-1]['present_cycle']=module.WINDOW+1
        result=module.analyze(rows)
        self.assertEqual(result['capture_window_presentations'],1799)
        self.assertEqual(result['capture_window_last_lateness_cycles'],1)
        self.assertEqual(result['observation_window_start_offset_cycles_inclusive'],[1,1999999])
        rows[-1]['present_cycle']=module.WINDOW
        self.assertEqual(module.analyze(rows)['capture_window_presentations'],1800)

    def test_window_cannot_fit_all(self):
        rows=records(); rows[-1]['present_cycle']=module.WINDOW+rows[0]['present_cycle']
        result=module.analyze(rows)
        self.assertFalse(result['all_recorded_presentations_fit_some_60s_window'])
        self.assertIsNone(result['observation_window_start_offset_cycles_inclusive'])

    def test_reject_bad_cadence_or_repeated_presentation(self):
        rows=records(); rows[1]['arrival_cycle']+=1
        with self.assertRaises(ValueError): module.analyze(rows)
        rows=records(); rows[1]['present_cycle']=rows[0]['present_cycle']
        with self.assertRaises(ValueError): module.analyze(rows)

if __name__=='__main__': unittest.main()
