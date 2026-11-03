"""Focused checks for the pure stop-and-wait capacity schedule."""
import unittest

from feedback_bound import simulate


class FeedbackBoundTests(unittest.TestCase):
    def test_zero_delay_keeps_periodic_ideal_frames(self):
        result = simulate([1] * 60, fps=30, link_mbps=1000, qspi_mbps=1000,
                          decode_ms=0, feedback_ms=0, encode_ms=0)
        self.assertEqual(result["sent_ids"], list(range(60)))
        self.assertEqual(result["dropped_ids"], [])
        self.assertEqual(result["decoded_strict_window"], 60)

    def test_feedback_reduces_stop_and_wait_rate(self):
        immediate = simulate([1] * 100, fps=100, link_mbps=1000, qspi_mbps=1000,
                             decode_ms=0, feedback_ms=0, encode_ms=0)
        delayed = simulate([1] * 100, fps=100, link_mbps=1000, qspi_mbps=1000,
                           decode_ms=0, feedback_ms=20, encode_ms=0)
        self.assertEqual(immediate["sent_count"], 100)
        self.assertLess(delayed["sent_count"], immediate["sent_count"])
        self.assertLess(delayed["theoretical_mean_service_fps"],
                        immediate["theoretical_mean_service_fps"])

    def test_strict_window_is_half_open(self):
        result = simulate([1, 1], fps=1, link_mbps=1000, qspi_mbps=1000,
                          decode_ms=0, feedback_ms=0, encode_ms=1000)
        self.assertEqual(result["decoded_eventual"], 2)
        self.assertEqual(result["decoded_strict_window"], 1)

    def test_latest_waiting_slot_replaces_old_frames_under_overload(self):
        result = simulate([10_000] * 20, fps=30, link_mbps=1, qspi_mbps=160,
                          decode_ms=8, feedback_ms=5, encode_ms=2)
        self.assertLess(result["sent_count"], 20)
        self.assertGreater(len(result["dropped_ids"]), 0)
        self.assertEqual(result["sent_ids"][0], 0)
        self.assertEqual(len(set(result["sent_ids"] + result["dropped_ids"])), 20)

    def test_empty_and_invalid_inputs(self):
        empty = simulate([])
        self.assertEqual(empty["sent_count"], 0)
        self.assertIsNone(empty["steady_5_to_55_seconds_fps"])
        for sizes, kwargs in [([-1], {}), ([1], {"fps": 0}), ([1], {"feedback_ms": -1})]:
            with self.assertRaises(ValueError):
                simulate(sizes, **kwargs)

    def test_steady_window_must_be_covered(self):
        result = simulate([100]*1800, fps=60, link_mbps=1000, qspi_mbps=1000,
                          encode_ms=0, decode_ms=0)
        self.assertIsNone(result['steady_5_to_55_seconds_fps'])
        self.assertFalse(result['steady_window_covered_by_capture'])


if __name__ == "__main__":
    unittest.main()
