"""Boundary tests for the independent bounded JPEG budget prototype."""

import unittest
from unittest import mock

import numpy as np

from PIL import Image

import pacing
from budget import choose_jpeg


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new("RGB", (2, 2), (10, 20, 30))

    @staticmethod
    def mbps_for_budget(byte_budget):
        # Keep the floor unambiguous while landing exactly on this integer.
        return (byte_budget + 0.25) * 8 / 1_000_000

    def test_accepts_candidate_at_exact_wire_budget(self):
        packet = b"p" * 1024
        wire = pacing.wire_bytes(len(packet))
        result, report = choose_jpeg(self.image, fps=1, mbps=self.mbps_for_budget(wire),
                                     cap=2048, qualities=(80,), encoder=lambda _i, _q: packet)
        self.assertEqual(result, packet)
        self.assertEqual(report["wire_budget_bytes"], wire)
        self.assertEqual(report["attempts"][0]["wire_bytes"], wire)
        self.assertEqual(report["selected_quality"], 80)

    def test_rejects_candidate_one_wire_byte_over_budget(self):
        packet = b"p" * 1024
        wire = pacing.wire_bytes(len(packet))
        result, report = choose_jpeg(self.image, fps=1, mbps=self.mbps_for_budget(wire - 1),
                                     cap=2048, qualities=(80,), encoder=lambda _i, _q: packet)
        self.assertIsNone(result)
        self.assertTrue(report["dropped"])
        self.assertEqual(report["wire_budget_bytes"], wire - 1)

    def test_cap_is_inclusive_and_rejects_one_byte_over(self):
        at_cap = b"a" * 100
        result, report = choose_jpeg(self.image, fps=1, mbps=100, cap=100,
                                     qualities=(80,), encoder=lambda _i, _q: at_cap)
        self.assertEqual(result, at_cap)
        over_cap = b"b" * 101
        result, report = choose_jpeg(self.image, fps=1, mbps=100, cap=100,
                                     qualities=(80,), encoder=lambda _i, _q: over_cap)
        self.assertIsNone(result)
        self.assertTrue(report["dropped"])

    def test_tries_descending_qualities_then_whole_frame_drop(self):
        calls = []
        def encoder(_image, quality):
            calls.append(quality)
            return bytes([quality]) * 200
        result, report = choose_jpeg(self.image, fps=30, mbps=0.01, cap=100,
                                     qualities=(80, 60, 40), encoder=encoder)
        self.assertIsNone(result)
        self.assertEqual(calls, [80, 60, 40])
        self.assertEqual(report["bounded_attempts"], 3)
        self.assertIsNone(report["selected_quality"])
        self.assertEqual(len(report["attempts"]), 3)

    def test_stops_after_first_fit(self):
        calls = []
        def encoder(_image, quality):
            calls.append(quality)
            return b"x" * (100 if quality == 80 else 10)
        result, report = choose_jpeg(self.image, fps=1, mbps=0.01, cap=100,
                                     qualities=(80, 60), encoder=encoder)
        self.assertEqual(result, b"x" * 100)
        self.assertEqual(calls, [80])
        self.assertEqual(report["bounded_attempts"], 1)

    def test_rejects_invalid_parameters(self):
        encoder = lambda _i, _q: b"x"
        invalid_cases = [
            {"fps": 0}, {"fps": float("inf")}, {"mbps": -1}, {"mbps": float("nan")},
            {"cap": 0}, {"cap": 1.5}, {"qualities": ()},
            {"qualities": (80, 80)}, {"qualities": (50, 60)},
            {"qualities": (96,)}, {"qualities": (80, 60, 40, 20, 10, 1)},
        ]
        for kwargs in invalid_cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                choose_jpeg(self.image, encoder=encoder, **kwargs)
        with self.assertRaises(ValueError):
            choose_jpeg(Image.new("L", (2, 2)), encoder=encoder)

    def test_real_noise_retries_receiver_size_rejection_then_drops(self):
        image = Image.fromarray(np.random.default_rng(1).integers(0, 256, (480, 720, 3), dtype=np.uint8))
        packet, report = choose_jpeg(image, qualities=(95, 80, 65, 50, 35))
        self.assertIsNone(packet)
        self.assertEqual(report['bounded_attempts'], 5)
        self.assertEqual(report['attempts'][0]['reason'], 'receiver_frame_size_bound')
        self.assertTrue(report['dropped'])

    def test_unrelated_encoder_errors_propagate(self):
        with mock.patch('budget.encode_receiver_jpeg', side_effect=ValueError('bad JPEG markers')):
            with self.assertRaisesRegex(ValueError, 'bad JPEG markers'):
                choose_jpeg(self.image)


if __name__ == "__main__":
    unittest.main()
