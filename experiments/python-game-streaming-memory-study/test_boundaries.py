from fractions import Fraction
import unittest
import analyze

class BoundaryTests(unittest.TestCase):
    def row(self,epochs,horizon=1100000):
        cfg=dict(clock_hz=1000000,scan_hz=60,panel_height=480)
        clean=[];presented=[]
        for fid,e in enumerate(epochs):
            start=round(Fraction(e*1000000,60));last=round(Fraction((e*480+479)*1000000,60*480))
            clean.append(dict(id=fid,epoch=e,buffer_index=1,epoch_frame_id=fid,epoch_start_cycle=start,validated_at_cycle=last))
            presented.append(dict(id=fid,at_cycle=start))
        return dict(status='simulated',config=cfg,capture_end_cycle=1000000,horizon_cycle=horizon,
                    clean_full_panel_epoch_presentations=clean,presented=presented)
    def test_exact_window_epoch_start_and_finish_are_separate(self):
        d=analyze.reconcile(self.row([58,59,60]))
        self.assertEqual(d['strict_logical_epoch_start_ids'],[0,1])
        self.assertEqual(d['strict_completed_clean_panel_epoch_ids'],[0])
        self.assertEqual(d['complete_clean_epoch_ids'],[0,1,2])
    def test_partial_last_panel_epoch_is_excluded(self):
        d=analyze.reconcile(self.row([60,61],horizon=1025000))
        self.assertEqual(d['complete_clean_epoch_ids'],[0])
        self.assertEqual(d['excluded_partial_epoch_ids'],[1])
    def test_last_line_validation_timestamp_must_match_actual_epoch(self):
        r=self.row([59]);r['clean_full_panel_epoch_presentations'][0]['validated_at_cycle']-=1
        with self.assertRaises(AssertionError):analyze.reconcile(r)
if __name__=='__main__':unittest.main()
