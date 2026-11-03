import math
import unittest

from model import Scenario, evaluate, plane_fetch_samples, resource_inventory, transform_budget


class CapacityAndTraffic(unittest.TestCase):
    def test_reference_inventory_and_frame_sizes(self):
        expected = {1: 2419200, 2: 2937600, 4: 3974400, 8: 6048000}
        for refs, allocation in expected.items():
            r = evaluate(Scenario(references_stored=refs))
            self.assertEqual(r["pixels"], 345600)
            self.assertEqual(r["yuv420_frame_bytes"], 518400)
            self.assertEqual(r["rgb565_frame_bytes"], 691200)
            self.assertEqual(r["sram_yuv_spare_bytes"], 5888)
            self.assertEqual(r["frame_allocation_bytes"], allocation)
        inv = resource_inventory()
        self.assertEqual(inv["bram_nominal_bits_arithmetic_remaining"] // 8, 66816)

    def test_stored_references_do_not_multiply_reference_traffic(self):
        a = evaluate(Scenario(references_stored=1))
        b = evaluate(Scenario(references_stored=8))
        self.assertEqual(a["traffic_bytes_s"], b["traffic_bytes_s"])
        c = evaluate(Scenario(references_stored=2, prediction_sources=2))
        self.assertEqual(c["traffic_bytes_s"]["reference_no_halo_read"], 31104000)

    def test_separate_decode_and_scanout_frequencies(self):
        a = evaluate(Scenario())
        b = evaluate(Scenario(decode_fps=60))
        self.assertEqual(a["traffic_bytes_s"]["display_rgb565_read"], 41472000)
        self.assertEqual(a["traffic_bytes_s"]["display_rgb565_read"], b["traffic_bytes_s"]["display_rgb565_read"])
        self.assertEqual(a["total_no_halo_bytes_s"], 110864000)
        self.assertEqual(a["total_independent_halo_bytes_s"], 126537500)
        self.assertEqual(a["average_slack_no_halo_bytes_s"], 9136000)
        self.assertEqual(a["average_slack_independent_halo_bytes_s"], -6537500)

    def test_traffic_components_and_fused_output(self):
        r = evaluate(Scenario(full_yuv_filter_passes=3))
        self.assertEqual(r["traffic_bytes_s"]["filter_read_write"], 93312000)
        fused = evaluate(Scenario(separate_color_conversion=False))
        self.assertEqual(fused["total_no_halo_bytes_s"], 95312000)
        intra = evaluate(Scenario(references_stored=0, prediction_sources=0))
        self.assertEqual(intra["total_no_halo_bytes_s"], 95312000)

    def test_independent_halo_and_partial_blocks(self):
        # Two horizontal 4-wide outputs with a 1-sample total halo, h=2.
        self.assertEqual(plane_fetch_samples(6, 2, 4, 2), 5 * 3 + 3 * 3)
        r = evaluate(Scenario())
        self.assertEqual(r["halo_fetch_samples_per_predicted_frame_per_source"], 1040850)
        self.assertEqual(r["halo_amplification"], 771 / 384)
        no_halo = evaluate(Scenario(luma_taps=1, chroma_taps=1))
        self.assertEqual(no_halo["halo_amplification"], 1)

    def test_reduced_coded_size_retains_display_and_buffer_traffic(self):
        r = evaluate(Scenario(width=512, height=288))
        self.assertEqual(r["yuv420_frame_bytes"], 221184)
        self.assertEqual(r["rgb565_frame_bytes"], 691200)
        self.assertEqual(r["frame_allocation_bytes"], 1824768)
        self.assertEqual(r["traffic_bytes_s"]["display_rgb565_read"], 41472000)
        self.assertEqual(r["traffic_bytes_s"]["display_rgb565_write"], 20736000)
        self.assertEqual(r["total_no_halo_bytes_s"], 84114560)
        slow = evaluate(Scenario(width=512, height=288, decode_fps=20))
        self.assertEqual(slow["total_no_halo_bytes_s"], 70567040)
        self.assertEqual(slow["traffic_bytes_s"]["display_rgb565_read"], 41472000)
        wide = evaluate(Scenario(width=512, height=288, display_width=800))
        self.assertEqual(wide["traffic_bytes_s"]["display_rgb565_read"], 46080000)

    def test_invalid_inputs(self):
        for kw in ({"width": 719}, {"luma_block": 3}, {"efficiency": 0},
                   {"efficiency": 1.1}, {"decode_fps": math.inf},
                   {"compressed_mbps": math.nan}, {"references_stored": -1},
                   {"references_stored": 0}, {"predicted_fraction": -0.1},
                   {"bus_bits": 7}, {"width": 720.0},
                   {"separate_color_conversion": "false"}):
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                Scenario(**kw)


class ArithmeticBounds(unittest.TestCase):
    def test_hand_calculated_dense_transform(self):
        # 8x8 luma plus two 4x4 chroma planes: six 4x4 transforms.
        r = transform_budget(4, width=8, height=8, fps=1, mhz=1, mac_lanes=1)
        self.assertEqual(r["padded_blocks"], 6)
        self.assertEqual(r["mac_per_frame"], 6 * 128)
        self.assertEqual(r["ideal_lane_utilization"], 768 / 1e6)

    def test_padding_is_counted_and_rate_scales(self):
        r = transform_budget(8, width=10, height=10, fps=2)
        self.assertEqual(r["padded_blocks"], 6)
        self.assertEqual(r["mac_per_second"], 6 * 1024 * 2)
        with self.assertRaises(ValueError):
            transform_budget(12)


if __name__ == "__main__":
    unittest.main()
