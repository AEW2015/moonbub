import dataclasses
import unittest

from model import Config, in_window, link_finish, simulate


class DeliveryTests(unittest.TestCase):
    def cfg(self, **kwargs):
        return dataclasses.replace(Config(steady_start_ms=100, steady_end_ms=800), **kwargs)

    def test_endpoint_is_half_open(self):
        self.assertTrue(in_window(0, 0, 1000))
        self.assertFalse(in_window(1000, 0, 1000))

    def test_link_pauses_preserve_remaining_service(self):
        self.assertEqual(link_finish(0, 20, ((5, 10), (20, 30))), 35)
        self.assertEqual(link_finish(7, 2, ((5, 10),)), 12)
        self.assertEqual(link_finish(0, 5, ((5, 10),)), 5)

    def test_baseline_distinct_presentation_and_ownership(self):
        r = simulate([26000]*30, self.cfg())
        self.assertEqual(r['presented_after_drain'], 30)
        self.assertEqual(len(set(x['id'] for x in r['presented'])), 30)
        self.assertLessEqual(r['peak_occupancy']['compressed_slots'], 2)
        self.assertLessEqual(r['peak_occupancy']['framebuffers'], 3)
        active = {}
        for event in r['allocation_events']:
            slot = event['slot']
            if event['kind'] == 'slot_acquire':
                self.assertNotIn(slot, active)
                active[slot] = event['id']
            else:
                self.assertEqual(active.pop(slot), event['id'])
        self.assertEqual(active, {})

    def test_overload_is_bounded_and_counted(self):
        r = simulate([26000]*90, self.cfg(decode_ms=60))
        self.assertTrue(r['drops_by_reason'])
        self.assertLess(r['presented_after_drain'], 90)
        self.assertLessEqual(r['peak_occupancy']['compressed_slots'], 2)
        self.assertLessEqual(r['peak_occupancy']['decode_wait'], 1)

    def test_loss_rejects_temporal_dependents_until_refresh(self):
        refs = [None, 0, 1, 2, 3, None, 5, 6, 7, 8]
        r = simulate([1000]*10, self.cfg(loss_ids=(1,)), refs)
        self.assertEqual(r['drops_by_reason']['network_loss'], 1)
        self.assertEqual(r['drops_by_reason']['missing_reference'], 3)
        self.assertEqual([x['id'] for x in r['decoded_events']], [0, 5, 6, 7, 8, 9])

    def test_caps_drop_before_allocating(self):
        r = simulate([49152, 49153], self.cfg(link_mbps=100))
        self.assertEqual(r['drops_by_reason']['cap'], 1)
        self.assertEqual([x['id'] for x in r['decoded_events']], [0])

    def test_all_cap_rejections_never_enter_host_queue(self):
        r = simulate([49153]*3, self.cfg())
        self.assertEqual(r['peak_occupancy']['host_waiting'], 0)
        self.assertEqual(r['peak_occupancy']['compressed_slots'], 0)

    def test_late_old_ready_preserves_newer_waiting_frame(self):
        # Seed0 gives readiness order0,2,1. The slow first transfer keeps
        # frame2 waiting when older frame1 appears; frame1 cannot replace it.
        r = simulate([1000]*3, self.cfg(seed=0, ready_jitter_ms=100,
                                      link_mbps=.01, max_age_before_send_ms=2000))
        self.assertEqual([x['id'] for x in r['decoded_events']], [0, 2])
        self.assertEqual(r['drops_by_reason']['stale_ready'], 1)

    def test_two_framebuffers_do_not_overwrite_front(self):
        r = simulate([1000]*30, self.cfg(framebuffers=2, decode_ms=0, link_mbps=100))
        self.assertEqual(r['presented_after_drain'], 30)
        self.assertLessEqual(r['peak_occupancy']['framebuffers'], 2)

    def test_jitter_reordering_does_not_regress_ids(self):
        r = simulate([1000]*90, self.cfg(ready_jitter_ms=100, link_mbps=100))
        ids = [x['id'] for x in r['presented']]
        self.assertEqual(ids, sorted(set(ids)))
        self.assertTrue(r['drops_by_reason'])

    def test_stall_forces_latest_drop_and_recovers(self):
        r = simulate([26000]*90, self.cfg(link_stalls=((200, 700),)))
        self.assertGreater(r['drops_by_reason'].get('host_latest_replaced', 0), 0)
        self.assertEqual(r['presented'][-1]['id'], 89)
        self.assertTrue(all(x is None for x in r['slots_at_end']))

    def test_invalid_input_fails(self):
        for kwargs in ({'link_mbps': 0}, {'decode_ms': -1}, {'ready_jitter_ms': float('nan')},
                       {'framebuffers': 1}, {'frame_cap': 0}, {'compressed_slots': 0},
                       {'link_stalls': ((10, 20), (15, 30))}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                simulate([1000], self.cfg(**kwargs))
        for sizes in ([], [0], [1.5]):
            with self.assertRaises(ValueError):
                simulate(sizes, self.cfg())
        with self.assertRaises(ValueError):
            simulate([1000], self.cfg(), [0])


if __name__ == '__main__':
    unittest.main()
