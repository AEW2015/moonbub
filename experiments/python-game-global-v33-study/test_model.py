import unittest
import copy
import numpy as np
import model
from controller import select_tier

class CameraTests(unittest.TestCase):
    def planes(self,n=64):
        rng=np.random.default_rng(3301)
        return tuple(rng.integers(0,256,(n//s,n//s),dtype=np.int16) for s in (1,2,2))

    def test_quiet_has_no_search_or_fractional_fetch(self):
        ref=self.planes()
        for policy in model.POLICIES:
            v,w=model.estimate(ref,ref,32,policy)
            self.assertFalse(np.any(v));self.assertEqual(w['candidate_vectors'],1)
            self.assertEqual(w['quiet_blocks'],4);self.assertEqual(w['coarse_candidate_vectors'],0)

    def test_known_translation_grid_and_paid_score_calls(self):
        ref=self.planes(96)
        src=tuple(np.roll(v,-(2 if i==0 else 1),axis=1) for i,v in enumerate(ref))
        for policy in model.POLICIES:
            v,w=model.estimate(src,ref,32,policy)
            self.assertTrue(np.all(np.abs(v.astype(np.int16))<=18))
            self.assertEqual(w['candidate_vectors'],len(w['score_calls']))
            self.assertEqual(w['sad_sample_operations'],sum(c['samples'] for c in w['score_calls']))
            self.assertEqual(w['reference_sample_fetches'],sum(c['reference_gathers'] for c in w['score_calls']))
            if policy=='global_grid':self.assertFalse(np.any(v%4))
            self.assertGreater(np.count_nonzero(v[...,0]==4),4)

    def test_ui_mask_fallback_and_edges_are_bounded(self):
        ref=self.planes(64);src=tuple(np.roll(v,1,axis=0) for v in ref)
        v,w=model.estimate(src,ref,32,'global_cross',((0,0,64,64),))
        self.assertEqual(v.shape,(2,2,2));self.assertGreater(w['global_score_blocks'],0)
        with self.assertRaises(ValueError):model.estimate(src,ref,32,'unknown')
        with self.assertRaises(ValueError):model.estimate(src,ref,32,'global_grid',((0,0,65,64),))

    def test_quiet_input_still_checks_invalid_mask(self):
        ref=self.planes()
        with self.assertRaises(ValueError):model.estimate(ref,ref,32,'global_cross',((0,0,65,64),))

    def test_replay_requires_complete_unique_cohorts_and_ordered_ids(self):
        from controller import complete_cases,SCENES
        cases=[dict(scene=s,policy=k,rows=[dict(id=i) for i in range(48)]) for s in SCENES for k in ('band_control','global_cross','global_grid')]
        complete_cases(cases)
        for altered in (cases[:-1],cases+[cases[0]],cases[:-1]+[cases[0]]):
            with self.assertRaises(ValueError):complete_cases(altered)
        altered=copy.deepcopy(cases);altered[0]['rows'][1]['id']=0
        with self.assertRaises(ValueError):complete_cases(altered)

    def test_selector_requires_shadow_and_protects_actual_rgb_error(self):
        def c(kind,size,error):return dict(kind=kind,complete_bytes=size,hybrid=dict(active_squared_error=error))
        z,m,b=c('zero',100,100),c('half32',90,101),c('half32_band',80,99)
        winner,shadow=select_tier([z,m,b]);self.assertIs(winner,b);self.assertIs(shadow,z)
        z['complete_bytes']=49153
        self.assertIsNone(select_tier([z,m,b])[0])

if __name__=='__main__':unittest.main()
