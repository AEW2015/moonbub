import unittest
import importlib.util
from pathlib import Path
import numpy as np

import adapter
import model
_spec = importlib.util.spec_from_file_location('execution_evidence_check', Path(__file__).with_name('verify.py'))
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)


class TickClock:
    """Declared unit-test clock, never used by performance benchmark."""
    def __init__(self, tick_ms=1):
        self.value = 0
        self.tick_ns = int(tick_ms * 1e6)

    def __call__(self):
        old = self.value
        self.value += self.tick_ns
        return old


class ExecutionTests(unittest.TestCase):
    def run_case(self, *, cache=False, fast=False, faults=None, frames=None, cap=49152):
        images = frames if frames is not None else [np.full((16, 32, 3), 50+i//4, np.uint8) for i in range(18)]
        config = model.Config(width=32, height=16, rectangles=((0, 0, 16, 16),),
                              decoder_service='python_wall', refresh_period=6,
                              frame_cap=cap, **(faults or {}))
        result = model.run(images, {}, config,
                           controller_factory=adapter.make_controller(cache=cache, ui=True,
                                                                      rectangles=((0, 0, 16, 8),)),
                           receiver_factory=lambda: adapter.DecoderState(frame_cap=cap, fast=fast),
                           clock_ns=TickClock(), service_tape=None)
        self.assertFalse(result['pending_ids'])
        self.assertTrue(all(x is None for x in result['unresolved_sender_slots']))
        self.assertFalse(result['unresolved_ingress_frames'])
        self.assertFalse(result['unresolved_credits'])
        self.assertTrue(all(x == 0 for x in result['unresolved_cpu'].values()))
        self.assertIsNone(result['waiting_at_end'])
        self.assertLessEqual(result['peak_credits'], 2)
        for p in result['packets']:
            self.assertEqual(p['encode_service_ms'], p['encode_wall_ms'])
            if 'decode_service_ms' in p:
                self.assertEqual(p['decode_service_ms'], p['decode_wall_ms'])
            if p['admitted']:
                self.assertLessEqual(p['bytes'], cap)
                if 'decode_done_ms' in p:
                    self.assertGreaterEqual(p['released_ms'], p['decode_done_ms'])
        self.assertTrue(all(c['selected_rgb565_mismatches'] == 0 for c in result['commits']))
        verify.check_case({'result': result, 'cache': cache}, primary=False)
        return result

    def test_all_four_paths_keep_same_packets_on_fixed_test_clock(self):
        baseline = self.run_case()
        trace = [(p['id'], p.get('packet_sha256'), p['key']) for p in baseline['packets']]
        for cache, fast in ((True, False), (False, True), (True, True)):
            row = self.run_case(cache=cache, fast=fast)
            self.assertEqual(trace, [(p['id'], p.get('packet_sha256'), p['key']) for p in row['packets']])
            self.assertEqual(baseline['presented'], row['presented'])
            if cache:
                self.assertTrue(any(a.get('cache_hit') for p in row['packets'] for a in p['attempts']))

    def test_optimized_actual_fault_packets_drain_and_recover(self):
        for faults in (dict(data_loss_ids=(0,)), dict(feedback_loss_ids=(0,)),
                       dict(corruption_ids=(3,), duplicate_chunk_ids=(6,),
                            duplicate_feedback_ids=(8,), reverse_chunks=True)):
            row = self.run_case(cache=True, fast=True, faults=faults)
            self.assertGreater(row['presented_eventual'], 0)

    def test_failed_admission_pays_cost_and_never_sends_or_commits(self):
        rng = np.random.default_rng(1304)
        frames = [rng.integers(0, 256, (16, 32, 3), dtype=np.uint8) for _ in range(3)]
        row = self.run_case(cache=True, fast=True, frames=frames, cap=60)
        self.assertFalse(row['commits'])
        self.assertEqual(row['forward_ipv4_udp_bytes'], 0)
        self.assertTrue(row['packets'])
        for p in row['packets']:
            self.assertFalse(p['admitted'])
            self.assertGreater(p['encode_service_ms'], 0)
            self.assertEqual(p['pending_at_prepare'], [])

    def test_frozen_scheduler_copy_preserves_requested_expiry_guard(self):
        from pathlib import Path
        import hashlib
        source = Path(model.__file__)
        frozen = source.parent.parent/'python-game-refresh-study/model.py'
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), hashlib.sha256(frozen.read_bytes()).digest())


if __name__ == '__main__':
    unittest.main()
