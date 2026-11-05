import copy
import unittest
import helpers as h
from controller import choose,complete,SCENES,POLICIES

class GuardTests(unittest.TestCase):
    def c(self,size,error):return dict(complete_bytes=size,hybrid=dict(active_squared_error=error))

    def test_guard_uses_actual_integer_error_cap_and_stable_ties(self):
        shadow=self.c(100,100);good=self.c(99,100);bad=self.c(80,101);tie=self.c(100,99)
        self.assertIs(choose(shadow,[bad,tie,good]),good)
        self.assertFalse(bad['qualified']);self.assertFalse(tie['qualified'])
        self.assertIs(choose(shadow,[self.c(49153,0)]),shadow)
        no=self.c(1,0);self.assertIsNone(choose(None,[no]));self.assertFalse(no['qualified'])
        zero=self.c(100,0);self.assertIs(choose(zero,[self.c(90,1)]),zero)
        for candidate in (self.c(0,1),self.c(90,-1),self.c(True,1)):
            with self.assertRaises(ValueError):choose(shadow,[candidate])

    def test_cohort_matrix_rejects_missing_duplicate_and_reordered_rows(self):
        cases=[dict(scene=s,policy=p,rows=[dict(id=i) for i in range(48)]) for s in SCENES for p in POLICIES]
        complete(cases)
        for invalid in (cases[:-1],cases+[cases[0]],cases[:-1]+[cases[0]]):
            with self.assertRaises(ValueError):complete(invalid)
        bad=copy.deepcopy(cases);bad[0]['rows'][1]['id']=0
        with self.assertRaises(ValueError):complete(bad)

    def test_actual_guarded_key_P_commit_mask_cost_and_source_metric(self):
        b=h.module('guard35_test_benchmark',h.HERE/'benchmark.py')
        inputs=h.load(h.n.V24/'results.json')['inputs'][0]
        hud=h.load(h.HUD/'results.json')['cases'][0]
        state=dict(rx=h.p.Receiver(),ref=None,rid=h.m.NO_REF,slot=0)
        for src,hu in zip(inputs['rows'][:2],hud['rows'][:2]):
            row=b.frame(src,hu,'guarded_core8',state)
            self.assertLessEqual(row['body_bytes'],row['shadow_complete_bytes'])
            self.assertLessEqual(row['hybrid']['active_squared_error'],row['shadow_source_sse'])
            self.assertGreater(row['mask_ms'],0)
            self.assertEqual(row['mask_work']['masked_blocks'],[256,19,19])
            self.assertGreaterEqual(row['paid_policy_ms'],row['mask_ms']+sum(g['wall_ms'] for g in row['encode_groups']))
            h.p.validate_ack(h.raw(row['ack']),h.raw(row['packet']))
            self.assertEqual(state['rx'].last_frame_id,src['id'])

if __name__=='__main__':unittest.main()
