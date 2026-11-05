import unittest
import model

def row(i,a,b,n=100):
    return dict(id=i,complete_bytes=9,identity=dict(active_squared_error=a,active_channel_samples=n),
                strong=dict(active_squared_error=b,active_channel_samples=n))

class Checks(unittest.TestCase):
    def test_weighted_mean_does_not_hide_regression(self):
        s=model.summarize([row(5,100,50,10),row(6,20,30,100)])
        self.assertEqual(s['regressed_frames'],1);self.assertEqual(s['improved_frames'],1)
        self.assertEqual(s['identity_MSE'],120/110);self.assertEqual(s['strong_MSE'],80/110)
        self.assertEqual(s['worst_relative_SSE_increase'],.5)
    def test_zero_error_and_tie(self):
        s=model.summarize([row(0,0,1),row(1,0,0)])
        self.assertEqual(s['zero_identity_error_regressed_frames'],1);self.assertEqual(s['tied_frames'],1)
        self.assertEqual(s['maximum_positive_frame_SSE_delta'],1)
    def test_reject_unpaired_samples_and_missing_frame(self):
        with self.assertRaises(ValueError):model.summarize([row(1,1,1),row(3,2,2)])
        r=row(0,1,2);r['strong']['active_channel_samples']=200
        with self.assertRaises(ValueError):model.summarize([r])

if __name__=='__main__':unittest.main()
