import unittest
import tempfile
from pathlib import Path
from correlate import analyze, read_jsonl


def event(session, seq, frame_id, stage, domain, timestamp, evidence='hardware'):
    return {'session_id': session, 'frame_seq': seq, 'frame_id': frame_id,
            'stage': stage, 'clock_domain': domain, 'timestamp_ns': timestamp,
            'evidence_kind': evidence}


class TelemetryCorrelationTests(unittest.TestCase):
    def test_explicit_calibration_computes_interval_and_no_calibration_does_not(self):
        rows = [event('h', 0, 7, 'capture', 'host_monotonic', 1_000_000_000),
                event('h', 0, 7, 'send', 'host_monotonic', 1_020_000_000),
                event('h', 0, 7, 'ingress', 'receiver', 5_030_000_000),
                event('h', 0, 7, 'presented', 'receiver', 5_050_000_000)]
        no_map = analyze(rows, frame_id_bits=3)['groups'][0]
        self.assertEqual(no_map['frames'][0]['latencies']['capture_to_ingress']['status'], 'not_computed')
        self.assertEqual(no_map['frames'][0]['latencies']['capture_to_presented']['status'], 'not_computed')
        calibrated = analyze(rows, {'h': {'hardware': {
            'receiver_minus_host_ns': 4_000_000_000, 'uncertainty_ns': 1_000_000}}}, 3)['groups'][0]
        frame = calibrated['frames'][0]
        self.assertEqual(frame['latencies']['capture_to_send']['estimate_ns'], 20_000_000)
        ingress = frame['latencies']['capture_to_ingress']
        self.assertEqual(ingress['estimate_ns'], 30_000_000)
        self.assertEqual((ingress['lower_bound_ns'], ingress['upper_bound_ns']), (29_000_000, 31_000_000))
        self.assertEqual(frame['latencies']['ingress_to_presented']['estimate_ns'], 20_000_000)

    def test_wrap_gaps_duplicates_and_stage_coverage(self):
        rows = []
        for seq, frame_id in ((0, 6), (1, 7), (2, 0), (4, 2)):
            rows.append(event('h', seq, frame_id, 'capture', 'host_monotonic', 100 + seq * 10))
        rows += [event('h', 0, 6, 'ingress', 'receiver', 1_000),
                 event('h', 2, 0, 'ingress', 'receiver', 1_020),
                 event('h', 2, 0, 'ingress', 'receiver', 1_021),
                 event('h', 4, 2, 'presented', 'receiver', 1_040)]
        group = analyze(rows, frame_id_bits=3)['groups'][0]
        self.assertEqual(group['frame_id_wrap_count'], 1)
        self.assertEqual(group['frame_id_wraps'][0]['to_frame_id'], 0)
        self.assertEqual(group['missing_capture_frame_seq_ranges'], [{'start': 3, 'end': 3}])
        self.assertEqual(group['stage_coverage']['ingress']['missing_for_captured_frame_seq_ranges'],
                         [{'start': 1, 'end': 1}, {'start': 4, 'end': 4}])
        self.assertEqual(group['duplicate_stage_events'][0]['stage'], 'ingress')
        self.assertEqual(group['duplicate_stage_events'][0]['extra_records'], 1)

    def test_negative_and_uncertain_latency_are_reported_not_clamped(self):
        rows = [event('h', 0, 1, 'capture', 'host_monotonic', 100),
                event('h', 0, 1, 'encode', 'host_monotonic', 90),
                event('h', 0, 1, 'send', 'host_monotonic', 110),
                event('h', 0, 1, 'ingress', 'receiver', 95)]
        group = analyze(rows, {'h': {'hardware': {
            'receiver_minus_host_ns': 0, 'uncertainty_ns': 20}}})['groups'][0]
        frame = group['frames'][0]
        same_clock = frame['latencies']['capture_to_encode']
        self.assertEqual(same_clock['estimate_ns'], -10)
        self.assertIn('ordering_warning', same_clock)
        cross_clock = frame['latencies']['capture_to_ingress']
        self.assertEqual(cross_clock['estimate_ns'], -5)
        self.assertIn('ordering_warning', cross_clock)
        overlap = frame['latencies']['send_to_ingress']
        self.assertEqual(overlap['estimate_ns'], -15)
        self.assertEqual(overlap['lower_bound_ns'], -35)
        self.assertEqual(overlap['upper_bound_ns'], 5)

    def test_join_is_scoped_by_session_and_evidence_kind(self):
        rows = [event('same', 0, 1, 'capture', 'simulation', 10, 'simulated'),
                event('same', 0, 1, 'presented', 'simulation', 20, 'simulated'),
                event('same', 0, 1, 'capture', 'host_monotonic', 100, 'hardware'),
                event('same', 0, 1, 'presented', 'receiver', 200, 'hardware')]
        calibration = {'same': {'hardware': {'receiver_minus_host_ns': 50, 'uncertainty_ns': 5}}}
        result = analyze(rows, calibration)
        self.assertEqual(len(result['groups']), 2)
        simulated = next(g for g in result['groups'] if g['evidence_kind'] == 'simulated')
        hardware = next(g for g in result['groups'] if g['evidence_kind'] == 'hardware')
        self.assertEqual(simulated['frames'][0]['latencies']['capture_to_presented']['status'], 'computed_same_clock')
        self.assertEqual(hardware['frames'][0]['latencies']['capture_to_presented']['estimate_ns'], 50)

    def test_frame_id_mismatch_and_duplicate_capture_are_not_used_for_latency(self):
        rows = [event('h', 1, 4, 'capture', 'host_monotonic', 100),
                event('h', 1, 4, 'capture', 'host_monotonic', 101),
                event('h', 1, 5, 'ingress', 'receiver', 500)]
        group = analyze(rows, {'h': {'hardware': {'receiver_minus_host_ns': 300,
                                                   'uncertainty_ns': 2}}})['groups'][0]
        self.assertEqual(group['frame_id_mismatches_within_frame_seq'], [{'frame_seq': 1, 'frame_ids': [4, 5]}])
        self.assertEqual(group['duplicate_stage_events'][0]['stage'], 'capture')
        self.assertNotIn('capture_to_ingress', group['frames'][0]['latencies'])

    def test_jsonl_read_rejects_unmarked_or_malformed_data(self):
        group = analyze([event('s', 0, 0, 'capture', 'host_monotonic', 1)])['groups'][0]
        self.assertEqual(group['captured_frame_count'], 1)
        with self.assertRaises(ValueError):
            analyze([{'session_id': 's', 'frame_id': 1}])
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'events.jsonl'
            path.write_text('{not json}\n')
            with self.assertRaisesRegex(ValueError, 'invalid JSON'):
                read_jsonl([path])


if __name__ == '__main__':
    unittest.main()
