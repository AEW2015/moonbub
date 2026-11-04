from dataclasses import replace
import unittest
import model

class PacedGatewayTests(unittest.TestCase):
    def frames(self,n=30,size=23000):return [dict(id=i,bytes=size) for i in range(n)]
    def check(self,r):
        self.assertLessEqual(r['peak_host_active_frames'],1)
        self.assertLessEqual(r['peak_host_latest_frames'],1)
        self.assertLessEqual(r['peak_packet_credits'],r['policy']['window'])
        self.assertLessEqual(r['peak_receiver_mailbox'],6)
        self.assertLessEqual(r['peak_receiver_credit_ledger'],r['policy']['window'])
        self.assertLessEqual(r['peak_control_queries_pending'],r['policy']['window'])
        self.assertEqual(r['counters'].get('mailbox_full',0),0)
        self.assertEqual(r['counters'].get('control_mailbox_full',0),0)
        self.assertEqual(len({x['id'] for x in r['completed']}),r['eventual_complete'])
        self.assertEqual({x['id'] for x in r['completed']} & {x['id'] for x in r['drops']},set())
        self.assertEqual(r['eventual_complete']+len(r['drops']),r['input_frames'])
        self.assertTrue(all(x['predicted_complete_us']<=x['deadline_us'] for x in r['admissions']))
    def test_paced_nominal_no_aggregation_delivers_all(self):
        r=model.run(self.frames(),policy=replace(model.Policy(),aggregate_ms=0))
        self.check(r);self.assertEqual(r['eventual_complete'],30);self.assertTrue(r['all_admitted_packets_issued'])
    def test_packet_credit_bound_survives_aggregation_and_slow_worker(self):
        cfg=replace(model.frozen.Config(chunk=1008,header=56),cpu_fraction=.25,driver_call_us=100)
        r=model.run(self.frames(),cfg,replace(model.Policy(),aggregate_ms=8))
        self.check(r);self.assertLess(r['eventual_complete'],30);self.assertTrue(r['all_admitted_packets_issued'])
    def test_lost_credit_queried_and_stale_duplicate_ignored(self):
        p=replace(model.Policy(),aggregate_ms=2)
        a=model.run(self.frames(),policy=p)
        b=model.run(self.frames(),policy=replace(p,drop_first_feedback=True,inject_stale_feedback=True))
        self.check(b);self.assertEqual(b['eventual_complete'],a['eventual_complete'])
        self.assertGreater(b['counters'].get('credit_queries',0),0)
        self.assertGreater(b['counters'].get('stale_credit_ignored',0),0)
        self.assertEqual(b['outstanding_credit_slots'],[None]*6)
        self.assertTrue(b['all_admitted_packets_issued'])
    def test_foreign_session_reply_cannot_free_reused_slot(self):
        r=model.run(self.frames(),policy=replace(model.Policy(),aggregate_ms=2,inject_foreign_feedback=True))
        self.check(r);self.assertEqual(r['eventual_complete'],30)
        self.assertEqual(r['counters'].get('foreign_credit_ignored'),1)
        self.assertEqual(r['counters']['credits_applied'],len(r['packets']))
    def test_total_feedback_loss_stops_without_reclaiming_credit(self):
        r=model.run(self.frames(),policy=replace(model.Policy(),lose_all_feedback=True))
        self.check(r);self.assertEqual(r['eventual_complete'],0)
        self.assertEqual(r['counters'].get('credits_applied',0),0)
        self.assertEqual(len(r['packets']),6)
        self.assertEqual(sum(x is not None for x in r['outstanding_credit_slots']),6)
        self.assertIsNotNone(r['control_query_inflight']);self.assertFalse(r['all_admitted_packets_issued'])
    def test_cap_stress_bounds_host_backlog_and_reports_drops(self):
        r=model.run(self.frames(60,49152),policy=replace(model.Policy(),aggregate_ms=0))
        self.check(r);self.assertLess(r['eventual_complete'],60)
        self.assertTrue(r['all_admitted_packets_issued'])
        for a in r['admissions']:
            rows=[p for p in r['packets'] if p['frame']==a['id']]
            self.assertEqual(sum(x['payload'] for x in rows),49152)
            self.assertEqual([x['offset'] for x in rows],list(range(0,49152,1008)))
    def test_slow_fifo_waits_consume_credit_and_do_not_overflow_mailbox(self):
        cfg=replace(model.frozen.Config(chunk=1008,header=56),fifo_policy='bounded_fifo_wait',fifo_bytes=2048,fpga_drain_bytes_per_second=400000,maximum_fifo_wait_ms=10)
        r=model.run(self.frames(),cfg,replace(model.Policy(),aggregate_ms=2))
        self.check(r);self.assertGreater(r['counters'].get('fifo_waits',0),0)
        self.assertEqual(r['counters'].get('fifo_overflow',0),0)
    def test_capture_id_holes_not_compressed(self):
        f=[dict(id=i,bytes=1000) for i in [0,2,9]]
        r=model.run(f,policy=replace(model.Policy(),aggregate_ms=0))
        self.check(r);self.assertEqual(r['capture_id_denominator'],10)
        self.assertAlmostEqual(r['capture_window_us'],10*1e6/30)
    def test_deadline_rejection_issues_no_partial_packets(self):
        r=model.run(self.frames(3,49152),policy=replace(model.Policy(),deadline_ms=10))
        self.check(r);self.assertEqual(r['admissions'],[]);self.assertEqual(r['packets'],[])
        self.assertTrue(all(x['reason']=='pre_admission_deadline' for x in r['drops']))
    def test_long_feedback_stops_at_horizon_without_future_drop_timestamps(self):
        p=replace(model.Policy(),aggregate_ms=0,extra_feedback_delay_ms=1000,deadline_ms=10000,drain_ms=10)
        r=model.run(self.frames(2),policy=p)
        self.check(r)
        self.assertEqual(r['eventual_complete'],0)
        self.assertTrue(any(x is not None for x in r['outstanding_credit_slots']))
        self.assertTrue(all(d['at_us']<=r['horizon_us'] for d in r['drops']))
        self.assertEqual(max(d['at_us'] for d in r['drops']),r['horizon_us'])
    def test_invalid_limits(self):
        for p in [replace(model.Policy(),window=7),replace(model.Policy(),window=0),replace(model.Policy(),max_queries=6),replace(model.Policy(),deadline_ms=float('nan'))]:
            with self.assertRaises(ValueError):model.run(self.frames(2),policy=p)
        with self.assertRaises(ValueError):model.run([dict(id=0,bytes=49153)])
        with self.assertRaises(ValueError):model.run([dict(id=1,bytes=10),dict(id=0,bytes=10)])

if __name__=='__main__':unittest.main()
