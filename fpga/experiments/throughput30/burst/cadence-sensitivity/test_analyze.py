import unittest
from pathlib import Path
from analyze import read_frames,replay,build_comparison
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'cadence-study'
LOG65=BASE/'verilator-65hz.log'
LOG60=BASE/'verilator-60hz-hypothetical.log'
class SensitivityTests(unittest.TestCase):
    def test_fixed_window_counts_and_phase_effect(self):
        rows=read_frames(LOG65)
        a=replay(rows,17.029,0,0,0,1800)
        b=replay(rows,17.029,0,0,.5,1800)
        self.assertEqual(a['captures_in_window'],1800)
        self.assertEqual(a['capture_window_seconds'],60)
        self.assertNotEqual(a['max_arrival_to_presentation_age_ms'],b['max_arrival_to_presentation_age_ms'])
        self.assertGreater(a['long_gap_count_in_window'],0)
    def test_paired_same_grid_compares_both_clocks(self):
        result=build_comparison(read_frames(LOG65),read_frames(LOG60),[0],4,1800)
        self.assertEqual(result['paired_case_count'],4)
        self.assertGreater(result['nominal_65hz_summary']['long_gap_count_range'][0],0)
        self.assertLessEqual(result['hypothetical_60hz_summary']['long_gap_count_range'][1],result['nominal_65hz_summary']['long_gap_count_range'][1])
        self.assertIn(result['nominal_65hz_summary']['presentation_count_in_60s_range'][0],(1799,1800))
        self.assertIn(result['hypothetical_60hz_summary']['presentation_count_in_60s_range'][0],(1799,1800))
        p=result['paired_cases'][0]
        self.assertEqual(p['nominal_65hz']['phase_fraction'],p['hypothetical_60hz']['phase_fraction'])
        self.assertEqual(p['nominal_65hz']['source_ppm'],p['hypothetical_60hz']['source_ppm'])
        self.assertEqual(p['nominal_65hz']['display_ppm'],p['hypothetical_60hz']['display_ppm'])
    def test_bad_trace_rejected(self):
        with self.assertRaises(FileNotFoundError): read_frames(HERE/'missing.log')
if __name__=='__main__': unittest.main()
