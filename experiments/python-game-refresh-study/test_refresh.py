import copy
from dataclasses import FrozenInstanceError
import unittest

import numpy as np

import adapter
import model
from replay import RefreshPolicy, ServiceTape, baseline_tape


def fixed_tape(**changes):
    costs = {'resize': 1.0}
    for kind in ('key', 'p'):
        for stage, value in dict(encode=4.0, decode=5.0, packetize=0.2,
                                 feed=0.1, feedback_build=0.2, feedback_parse=0.2,
                                 encode_rejected=120.0).items():
            costs[stage + '_' + kind] = value
    costs.update(changes)
    return ServiceTape(tuple(sorted(costs.items())), 'declared_test_table')


class TickClock:
    def __init__(self, tick_ms):
        self.value = 0; self.tick_ns = int(tick_ms * 1e6)

    def __call__(self):
        value = self.value; self.value += self.tick_ns
        return value


def timeline(result):
    """Omit separately observed host timings and diagnostic timer internals."""
    return dict(presented=result['presented'], drops=result['drops'],
                feedback=result['feedback'], allocations=result['allocations'],
                packets=[{k: p.get(k) for k in ('id', 'packet_sha256', 'reference_id', 'key',
                    'attempted_key', 'encode_started_ms', 'encode_service_ms', 'decode_started_ms',
                    'decode_service_ms', 'decode_done_ms', 'released_ms', 'release_reason')}
                    for p in result['packets']],
                cpu=[{k: c[k] for k in ('stage', 'id', 'start_ms', 'service_ms', 'done_ms')}
                     for c in result['cpu_services']])


class ReplayTests(unittest.TestCase):
    def frames(self, n=18):
        return [np.full((16, 32, 3), 40 + i, np.uint8) for i in range(n)]

    def config(self, **changes):
        values = dict(width=32, height=16, rectangles=((0, 0, 16, 16),),
                      decoder_service='python_wall', refresh_period=0)
        values.update(changes)
        return model.Config(**values)

    def run_case(self, *, frames=None, tape=None, policy='periodic30', clock=None, **changes):
        factory = adapter.make_controller(rectangles=((0, 0, 16, 8),), max_attempts=4)
        cfg = self.config(**changes)
        return model.run(self.frames() if frames is None else frames, {}, cfg,
                         controller_factory=factory,
                         receiver_factory=lambda: adapter.DecoderState(frame_cap=cfg.frame_cap),
                         service_tape=tape or fixed_tape(), key_policy=RefreshPolicy(policy),
                         **({} if clock is None else {'clock_ns': clock}))

    def drained(self, row):
        self.assertTrue(all(v is None for v in row['unresolved_sender_slots']))
        self.assertFalse(row['unresolved_ingress_frames'])
        self.assertFalse(row['unresolved_credits']); self.assertFalse(row['pending_ids'])
        self.assertIsNone(row['waiting_at_end'])
        self.assertTrue(all(v == 0 for v in row['unresolved_cpu'].values()))
        self.assertLessEqual(row['peak_credits'], 2)
        self.assertLessEqual(row['peak_ingress_payload_bytes'], 2 * 49152)

    def test_immutable_table_and_exact_timeline_ignore_wall_remeasurement(self):
        tape = fixed_tape()
        with self.assertRaises(FrozenInstanceError):
            tape.scale = 2
        a = self.run_case(tape=tape, clock=TickClock(1))
        b = self.run_case(tape=tape, clock=TickClock(500))
        self.drained(a); self.drained(b)
        self.assertEqual(timeline(a), timeline(b))
        self.assertNotEqual(a['packets'][0]['encode_wall_ms'], b['packets'][0]['encode_wall_ms'])
        self.assertEqual(a['service_tape']['table_sha256'], b['service_tape']['table_sha256'])

    def test_source_observations_and_latched_scene_do_not_use_future(self):
        policy = RefreshPolicy('bounded_scene', min_gap=3, max_gap=10, scene_threshold=20)
        image = np.zeros((16, 32, 3), np.uint8)
        policy.observe(0, image)
        with self.assertRaises(KeyError):
            policy.due(1, 0)
        policy.observe(1, image + 100)
        self.assertFalse(policy.due(1, 0))
        policy.observe(3, image + 100)
        self.assertTrue(policy.due(3, 0))
        snapshot = copy.deepcopy(policy.decisions[3])
        policy.observe(99, image)
        self.assertTrue(policy.due(3, 0))
        self.assertEqual(snapshot, policy.decisions[3])
        self.assertLess(policy.observations[3]['prior_observed_id'], 3)
        with self.assertRaises(ValueError):
            policy.observe(4, image)

    def test_failed_preparation_pays_full_declared_budget_and_drain(self):
        row = self.run_case(frame_cap=1, frames=self.frames(24))
        self.drained(row)
        self.assertEqual(row['forward_ipv4_udp_bytes'], 0)
        self.assertTrue(all(p['attempted_key'] and not p['admitted'] for p in row['packets']))
        self.assertTrue(all(p['encode_service_ms'] == 120 for p in row['packets']))
        for p in row['packets']:
            self.assertAlmostEqual(p['released_ms'] - p['encode_started_ms'], 120)
        self.assertGreater(row['drops_by_reason'].get('latest_replaced', 0), 0)

    def test_ack_after_timeout_cannot_install_key_reference(self):
        row = self.run_case(frames=self.frames(1), ack_timeout_ms=20, feedback_latency_ms=80)
        self.drained(row)
        received = [f for f in row['feedback'] if f['kind'] == 'received']
        self.assertTrue(received)
        self.assertTrue(all(not f['accepted'] and f['sender_anchor_after'] is None for f in received))
        self.assertEqual(row['packets'][0]['release_reason'], 'ack_timeout')

    def test_timeout_during_parse_pays_reader_drain_and_rejects_late_ack(self):
        row = self.run_case(frames=self.frames(1), ack_timeout_ms=35,
                            tape=fixed_tape(feedback_parse_key=90))
        self.drained(row)
        parse = next(x for x in row['cpu_services'] if x['stage'] == 'feedback_parse')
        self.assertTrue(row['timeout_events'])
        self.assertFalse(row['timeout_events'][0]['physical_drained'])
        self.assertGreaterEqual(row['packets'][0]['released_ms'], parse['done_ms'])
        received = next(f for f in row['feedback'] if f['kind'] == 'received')
        self.assertFalse(received['accepted'])
        self.assertIsNone(received['sender_anchor_after'])

    def test_periodic_keys_wait_for_credit_and_everything_drains(self):
        row = self.run_case(frames=self.frames(65), policy='periodic30',
                            tape=fixed_tape(decode_p=29, feedback_parse_p=7))
        self.drained(row)
        keys = [p for p in row['packets'] if p.get('key')]
        self.assertGreaterEqual(len(keys), 2)
        self.assertTrue(all(not p['pending_at_prepare'] for p in keys))
        self.assertTrue(all(p.get('reference_id') == p['acked_anchor_at_prepare']
                            for p in row['packets'] if p.get('admitted') and not p['key']))
        self.assertTrue(all(c['selected_rgb565_mismatches'] == 0 for c in row['commits']))

    def test_loss_corruption_feedback_duplicate_paths_are_paid_and_drained(self):
        row = self.run_case(frames=self.frames(60), policy='periodic30',
                            data_loss_ids=(0,), corruption_ids=(14,), feedback_loss_ids=(24,),
                            duplicate_chunk_ids=(35,), duplicate_feedback_ids=(42,))
        self.drained(row)
        self.assertTrue(row['timeout_events'])
        self.assertTrue(any(c['stage'] == 'feed' and c['id'] == 14 for c in row['cpu_services']))
        self.assertTrue(any(f['kind'] == 'lost' for f in row['feedback']))
        self.assertTrue(all(c['service_ms'] > 0 for c in row['cpu_services']))
        self.assertEqual(row['presented'][-1]['id'], 59)

    def test_pinned_baseline_table_uses_means_and_declared_reject_cost(self):
        a = baseline_tape('mass-effect-combat', 'gm_only')
        b = baseline_tape('mass-effect-combat', 'gm_only')
        self.assertEqual(a.describe(), b.describe())
        self.assertEqual(a.charge('encode_rejected', 17, False), 120)
        self.assertAlmostEqual(a.charge('encode', 17, True), 32.9904905)

    def test_stored_trace_verifier_on_actual_small_packet_run(self):
        import importlib.util
        from pathlib import Path
        spec = importlib.util.spec_from_file_location('refresh_trace_verifier', Path(__file__).with_name('verify.py'))
        verifier = importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
        row = self.run_case(frames=self.frames(18), policy='initial_only')
        verifier.check_case(dict(result=row, service_scale=1.0, policy='initial_only'), primary=False)


if __name__ == '__main__':
    unittest.main()
