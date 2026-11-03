import dataclasses
import unittest
import numpy as np

from model import Config,run
import model


def fixture(count=12):
    rgb=np.random.default_rng(6).integers(0,256,(18,34,3),dtype=np.uint8)
    frames=[np.roll(rgb,i%4,axis=1).copy() for i in range(count)]
    manifest={'active_rects':[[0,0,34,18]]*count}
    return frames,manifest


class CoupledTests(unittest.TestCase):
    def test_actual_packets_commit_and_present_exactly(self):
        frames,m=fixture()
        r=run(frames,m,Config())
        self.assertEqual(r['committed'],len(frames))
        self.assertEqual(r['presented_after_drain'],len(frames))
        self.assertTrue(all('reconstructed_hash' in x for x in r['records']))
        self.assertLessEqual(r['max_waiting'],1)

    def test_feedback_skips_and_reencodes_against_available_reference(self):
        frames,m=fixture(30)
        r=run(frames,m,Config(feedback_ms=70,max_age_ms=200))
        self.assertLess(r['attempted'],len(frames))
        self.assertGreater(r['drop_counts'].get('latest_replaced',0),0)
        previous=None
        for record in r['records']:
            if not record['key']:self.assertEqual(record['reference_id'],previous)
            previous=record['id']
        self.assertEqual(r['presentations'][-1]['id'],29)

    def test_data_ack_and_crc_faults_recover_to_keys(self):
        frames,m=fixture(30)
        for kwargs in ({'loss_ids':(1,)},{'ack_loss_ids':(1,)},{'corrupt_ids':(1,)}):
            r=run(frames,m,Config(**kwargs))
            self.assertGreater(r['drop_counts'].get('timeout',0),0)
            after=next(x for x in r['records'] if x['id']>1)
            self.assertTrue(after['key'])
            self.assertEqual(r['presentations'][-1]['id'],29)

    def test_timeout_drain_and_stale_ack_cannot_advance_wrong_reference(self):
        frames,m=fixture(15)
        r=run(frames,m,Config(ack_timeout_ms=5,feedback_ms=20))
        self.assertGreater(r['stale_ack_count'],0)
        self.assertTrue(all(x['key'] for x in r['records']))
        self.assertEqual(r['observed_max_pipeline_transactions'],1)

    def test_duplicate_ack_is_ignored(self):
        frames,m=fixture()
        r=run(frames,m,Config(duplicate_ack_ms=20))
        self.assertGreater(r['stale_ack_count'],0)
        self.assertEqual(r['committed'],12)

    def test_caps_and_age_do_not_create_commits(self):
        frames,m=fixture()
        r=run(frames,m,Config(frame_cap=1))
        self.assertEqual(r['committed'],0)
        self.assertEqual(r['drop_counts']['cap'],12)
        r=run(frames,m,Config(max_age_ms=1,encode_ms=2))
        self.assertEqual(r['committed'],0)
        self.assertEqual(r['drop_counts']['stale_after_encode'],12)

    def test_bad_parameters_fail(self):
        f,m=fixture()
        for kwargs in ({'fps':0},{'frame_cap':0},{'encode_ms':-1},{'feedback_ms':float('nan')},{'key_period':0}):
            with self.assertRaises(ValueError):run(f,m,Config(**kwargs))

    def test_failures_are_not_terminal_drop_partition(self):
        frames,m=fixture(15)
        r=run(frames,m,Config(ack_loss_ids=(1,)))
        self.assertGreater(r['drop_counts']['ACK_loss'],0)
        outcome=next(x for x in r['terminal_outcomes'] if x['id']==1)
        self.assertEqual(outcome['state'],'presented')
        self.assertEqual(sum(r['terminal_counts'].values()),15)
        self.assertTrue(r['disposition_conserved'])

    def test_timeout_with_undrained_physical_work_remains_visible(self):
        frames,m=fixture(2)
        r=run(frames,m,Config(link_mbps=.001,ack_timeout_ms=5,drain_ms=0))
        self.assertIsNone(r['pending_at_horizon'])
        self.assertEqual([x['id'] for x in r['physical_transactions_at_horizon']],[0])
        self.assertEqual(r['host_waiting_at_horizon'],1)
        self.assertGreater(r['physical_busy_until_ms'],r['capture_window_ms'][1])
        self.assertEqual(r['terminal_counts'],{'pending':2})

    def test_next_capture_backoff_recovers_without_same_frame_retry(self):
        f,m=fixture(12)
        p8=model.mc.Encoder().prepare(f[0],0,quant_scale=8)
        p16=model.mc.Encoder().prepare(f[1],0,quant_scale=16)
        self.assertGreater(len(p8),len(p16))
        cap=(len(p8)+len(p16))//2
        r=run(f,m,Config(frame_cap=cap,cap_backoff_scales=(8,16,32)))
        self.assertEqual(r['records'][0]['quant_scale'],8)
        self.assertEqual(r['records'][0]['status'],'cap_drop')
        self.assertEqual(r['records'][1]['id'],1)
        self.assertEqual(r['records'][1]['quant_scale'],16)
        self.assertTrue(r['records'][1]['key'])
        self.assertGreater(r['committed'],0)
        self.assertLessEqual(max(r['attempt_scale_histogram']),32)


if __name__=='__main__':unittest.main()
