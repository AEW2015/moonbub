import dataclasses
import unittest

from model import Config, SlotPool, allocation_report, simulate, within_window


class OwnershipTests(unittest.TestCase):
    def test_commit_release_require_drain_and_integrity(self):
        pool = SlotPool(1, 16)
        token = pool.acquire(7, 15)
        pool.issue(token, 0, 15)
        with self.assertRaises(ValueError):
            pool.commit(token, True)
        with self.assertRaises(ValueError):
            pool.release(token)
        self.assertIsNone(pool.acquire(8, 1))
        pool.drain(token)
        with self.assertRaises(ValueError):
            pool.commit(token, False)
        pool.commit(token, True)
        pool.release(token)
        successor = pool.acquire(8, 16)
        self.assertNotEqual(token, successor)
        with self.assertRaises(ValueError):
            pool.issue(token, 0, 1)

    def test_range_and_capacity_are_not_wrapped(self):
        pool = SlotPool(1, 16)
        with self.assertRaises(ValueError):
            pool.acquire(0, 17)
        token = pool.acquire(0, 16)
        for offset,count in ((-1,1),(16,1),(1,16),(0,0)):
            with self.assertRaises(ValueError):
                pool.issue(token,offset,count)
        pool.release(token)
        shorter = pool.acquire(1, 3)
        with self.assertRaises(ValueError):
            pool.issue(shorter, 0, 4)

    def test_proposal_assembly_conflict(self):
        row = allocation_report()
        self.assertEqual(row["proposed_split_bytes"],row["sram_bytes"])
        self.assertLess(row["proposed_assembly_bytes"],row["negotiated_cap_bytes"])
        self.assertFalse(row["assembly_supports_cap"])


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.cfg = Config(frames=3, drain_frames=3)

    def test_low_load_completes_with_refresh_and_no_line_miss(self):
        row = simulate(self.cfg)
        self.assertEqual(row["reconstructed_after_drain"],3)
        self.assertEqual(row["line_deadline_misses_during_run"],0)
        self.assertGreater(row["refresh_commands"],0)
        self.assertGreater(row["row_miss_requests"],0)
        self.assertGreater(row["service_cycles"]["compressed_write"],0)

    def test_exact_window_endpoint_is_excluded(self):
        self.assertTrue(within_window(0,100))
        self.assertTrue(within_window(99,100))
        self.assertFalse(within_window(100,100))
        self.assertFalse(within_window(-1,100))

    def test_negative_deadline_control_detects_miss(self):
        row = simulate(dataclasses.replace(self.cfg,line_deadline_scale=.1))
        self.assertGreater(row["line_deadline_misses_during_run"],0)

    def test_saturated_display_starves_background(self):
        row = simulate(dataclasses.replace(self.cfg,scan_hz=2000,frames=1,drain_frames=1))
        self.assertEqual(row["reconstructed_after_drain"],0)
        self.assertNotIn("compressed_write",row["service_cycles"])
        self.assertGreater(row["line_deadline_misses_during_run"],0)
        self.assertGreater(row["queue_high_water_jobs"]["display"],1)

    def test_bram_cap_rejects_large_frame(self):
        row = simulate(dataclasses.replace(self.cfg,storage="bram",frame_sizes=(262144,)))
        self.assertEqual(row["cap_drops"],3)
        self.assertEqual(row["admitted"],0)

    def test_external_storage_removes_only_compressed_sdram_work(self):
        row = simulate(dataclasses.replace(self.cfg,storage="sram"))
        self.assertEqual(row["reconstructed_after_drain"],3)
        self.assertNotIn("compressed_write",row["service_cycles"])
        self.assertNotIn("compressed_read",row["service_cycles"])
        self.assertGreater(row["service_cycles"]["pixels"],0)

    def test_fair_policy_still_measures_deadlines(self):
        row = simulate(dataclasses.replace(self.cfg,policy="deadline_rr",reference=True))
        self.assertEqual(row["reconstructed_after_drain"],3)
        self.assertEqual(row["line_deadline_misses_during_run"],0)
        self.assertIn("reference",row["service_cycles"])

    def test_drain_count_is_not_strict_count(self):
        cfg=dataclasses.replace(self.cfg,frames=2,frame_sizes=(262144,),
                                storage="sram",sram_cycles_per_word=30,drain_frames=10)
        row = simulate(cfg)
        self.assertEqual(row["reconstructed_after_drain"],2)
        self.assertLess(row["hypothetical_vblank_eligible_by_window"],2)

    def test_invalid_config_is_rejected(self):
        for fields in (dict(frame_sizes=()),dict(frame_sizes=(0,)),dict(memory_clock=0),
                       dict(line_words=0),dict(scan_lines=0),dict(frame_cap=0),
                       dict(sram_cycles_per_word=-1)):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                simulate(dataclasses.replace(self.cfg,**fields))


if __name__ == "__main__":
    unittest.main()
