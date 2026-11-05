"""Directed audit of weighted summaries and full-plane source-error oracles."""
import unittest
import numpy as np
import verify as v

def row(i,a,b,n=100):
    return dict(id=i,complete_bytes=11,identity=dict(active_squared_error=a,active_channel_samples=n),strong=dict(active_squared_error=b,active_channel_samples=n))

class ExtendedFilterProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.subject=v.module('filter67_summary_subject',v.HERE/'model.py')
    def test_weighted_summary_keeps_local_regression(self):
        rows=[row(2,100,50,10),row(3,20,30,100)]
        actual=self.subject.summarize(rows);self.assertEqual(actual,v.aggregate(rows));self.assertEqual(actual['identity_MSE'],120/110)
        self.assertEqual(actual['strong_MSE'],80/110);self.assertEqual(actual['regressed_frames'],1);self.assertEqual(actual['worst_relative_SSE_increase'],.5)
    def test_zero_error_regression_has_explicit_count_not_infinite_average(self):
        rows=[row(0,0,1),row(1,0,0),row(2,20,10)]
        actual=self.subject.summarize(rows);self.assertEqual(actual,v.aggregate(rows));self.assertEqual(actual['zero_identity_error_regressed_frames'],1)
        self.assertEqual(actual['worst_relative_SSE_increase'],0);self.assertEqual(actual['maximum_positive_frame_SSE_delta'],1)
    def test_window_boundaries_cover_each_id_once(self):
        rows=[row(i,100+i,99+i)for i in range(65)]
        parts=self.subject.partitions(rows)
        for name,lo,hi in(('calibration_0_23',0,24),('later_24_47',24,48),('remaining_48_plus',48,65)):
            self.assertEqual(parts[name],v.aggregate(rows[lo:hi]))
        self.assertEqual(sum(p['frames']for p in parts.values()),65)
    def test_identity_zero_error_can_be_worsened_by_fixed_filter(self):
        # Perfect low-contrast source; the fixed filter has no universal quality guarantee.
        Y=np.full((480,720),100,np.uint8);Y[:,8:]=104;C=np.full((240,360),128,np.uint8)
        mask=np.zeros(Y.shape,bool);mask.setflags(write=False)
        filtered,work=v.oracle.oracle_filter(Y,mask,v.oracle.STRONG)
        original=v.m.C.corpus.rgb565(v.m.ft.planes_to_rgb((Y,C,C)))
        shown=v.m.C.corpus.rgb565(v.m.ft.planes_to_rgb((filtered,C,C)))
        self.assertEqual(v.quality(original,original)['active_squared_error'],0)
        self.assertGreater(v.quality(original,shown)['active_squared_error'],0)
        self.assertGreater(work['changed_luma_samples'],0)
    def test_protected_footprint_and_readonly_source(self):
        Y=np.full((480,720),100,np.uint8);Y[:,8:]=104;Y.setflags(write=False)
        mask=np.ones(Y.shape,bool);mask.setflags(write=False);before=Y.copy()
        filtered,work=v.oracle.oracle_filter(Y,mask,v.oracle.STRONG)
        np.testing.assert_array_equal(filtered,before);np.testing.assert_array_equal(Y,before)
        self.assertFalse(filtered.flags.writeable);self.assertEqual(work['changed_luma_samples'],0)
    def test_hud_word_metric_counts_exact_words(self):
        a=np.zeros((480,720),np.uint16);b=a.copy();x,y,w,hh=v.n.RECTS[0];b[y,x]=1
        q=v.quality(a,b);self.assertEqual(q['hud_word_errors'],1);self.assertEqual(q['hud_squared_channel_error'],64)

if __name__=='__main__':unittest.main()
