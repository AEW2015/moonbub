import unittest
import numpy as np
import model as m


def rgb(seed=0, noise=False):
    if noise:
        return np.random.default_rng(seed).integers(0, 256, (480, 720, 3), dtype=np.uint8)
    a = np.full((480, 720, 3), (20 + seed) % 256, np.uint8)
    for i, (x, y, w, h) in enumerate(m.RECTANGLES):
        a[y:y + h, x:x + w] = [40 + seed + i, 80 + i, 120 + i]
    return a


class JointTransactions(unittest.TestCase):
    def pair(self):
        return m.JointSender(), m.JointReceiver()

    def delivered(self, sender, receiver, image, frame, **kwargs):
        c = sender.build(image, frame, **kwargs)
        self.assertTrue(c.accepted)
        packet = sender.commit(c)
        before = receiver.published_snapshot()
        task = receiver.prepare(packet)
        self.assertEqual(receiver.published_snapshot(), before)
        receiver.mark_writes_drained(task)
        ack = receiver.present(task)
        sender.ack(ack)
        for x, y, w, h in m.RECTANGLES:
            expected = m.C.corpus.rgb565(image[y:y + h, x:x + w])
            np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], expected)
        self.assertEqual(sender.base.last_issued, frame)
        self.assertEqual(sender.hud.last_frame, frame)
        self.assertEqual(receiver.last_frame, frame)
        self.assertEqual(receiver.hud.last_frame, frame)
        return packet, ack, task

    def test_whole_pair_build_does_not_issue_identity(self):
        s, r = self.pair()
        before = s.snapshot()
        c = s.build(rgb(), 0)
        self.assertTrue(c.accepted)
        self.assertEqual(s.snapshot(), before)
        self.assertIsNone(s.hud.pending)
        self.assertEqual(c.info['complete_bytes'], len(c.packet))
        s.discard(c)
        self.assertEqual(s.snapshot(), before)
        self.delivered(s, r, rgb(), 0)

    def test_complete_pair_rejects_after_base_fits_and_reuses_id(self):
        s = m.JointSender(frame_cap=256)
        before = s.snapshot()
        c = s.build(rgb(), 0)
        self.assertFalse(c.accepted)
        self.assertEqual(len(c.info['attempts']), 4)
        self.assertTrue(all(a['base_accepted'] for a in c.info['attempts']))
        self.assertTrue(all(a['discard_ms'] > 0 for a in c.info['attempts']))
        self.assertEqual(s.snapshot(), before)
        s.frame_cap = m.FRAME_CAP
        self.assertTrue(s.build(rgb(), 0).accepted)
        s.discard(s.active_candidate)

    def test_all_actual_noisy_attempts_are_paid_and_unissued(self):
        s = m.JointSender()
        before = s.snapshot()
        c = s.build(rgb(9, noise=True), 0)
        self.assertFalse(c.accepted)
        self.assertEqual(len(c.info['attempts']), 4)
        self.assertTrue(all(a['build_ms'] > 0 and a['map_ms'] > 0 and a['discard_ms'] > 0 for a in c.info['attempts']))
        self.assertEqual(s.snapshot(), before)
        accepted = s.build(rgb(), 0)
        self.assertTrue(accepted.accepted)
        s.discard(accepted)

    def test_deadline_before_and_after_paid_preparation(self):
        s = m.JointSender()
        before = s.snapshot()
        a = s.build(rgb(), 0, now_ms=10, deadline_ms=10)
        self.assertFalse(a.accepted)
        self.assertEqual(a.info['attempts'], [])
        b = s.build(rgb(), 0, deadline_ms=0.000001)
        self.assertFalse(b.accepted)
        self.assertGreater(b.info['hud_prepare_ms'], 0)
        self.assertEqual(s.snapshot(), before)
        c = s.build(rgb(), 0, deadline_ms=1000)
        with self.assertRaises(ValueError): s.commit(c, now_ms=1000)
        self.assertEqual(s.snapshot(), before)
        s.discard(c)

    def test_private_hud_failure_never_changes_base_or_hud_identity(self):
        s = m.JointSender()
        before = s.snapshot()
        original = s.hud.selector.select
        def fail(*args, **kwargs): raise RuntimeError('injected patch failure')
        s.hud.selector.select = fail
        with self.assertRaises(RuntimeError): s.build(rgb(), 0)
        s.hud.selector.select = original
        self.assertEqual(s.snapshot(), before)
        self.assertIsNone(s.base.active_candidate)

    def test_sender_external_lease_survives_failed_attempts_and_commit(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        lease = s.base.acquire(0)
        s.frame_cap = 256
        before = s.snapshot()
        rejected = s.build(rgb(1), 1)
        self.assertFalse(rejected.accepted)
        self.assertEqual(s.snapshot(), before)
        s.frame_cap = m.FRAME_CAP
        candidate = s.build(rgb(1), 1)
        self.assertEqual(s.base.readers, 2)
        packet = s.commit(candidate)
        self.assertEqual(s.base.readers, 1)
        self.assertIn(lease, s.base._leases)
        task = r.prepare(packet)
        r.mark_writes_drained(task)
        s.ack(r.present(task))
        self.assertIn(lease, s.base._leases)
        s.base.release(lease)
        self.assertEqual(s.base.readers, 0)

    def test_commit_rechecks_late_destination_reader_without_half_commit(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        c = s.build(rgb(1), 1, force_key=True)
        lease = s.base.acquire(0)
        before = s.snapshot()
        with self.assertRaises(ValueError): s.commit(c)
        self.assertEqual(s.snapshot(), before)
        self.assertIsNone(s.hud.pending)
        s.base.release(lease)
        packet = s.commit(c)
        task = r.prepare(packet); r.mark_writes_drained(task); s.ack(r.present(task))

    def test_receiver_requires_explicit_fence_and_vblank_then_atomic_pair(self):
        s, r = self.pair()
        c = s.build(rgb(), 0); packet = s.commit(c)
        before = r.snapshot()
        task = r.prepare(packet)
        self.assertEqual(r.snapshot(), before)
        with self.assertRaises(ValueError): r.present(task)
        r.mark_writes_drained(task)
        with self.assertRaises(ValueError): r.present(task, vblank=False)
        self.assertEqual(r.snapshot(), before)
        ack = r.present(task)
        self.assertEqual((r.last_frame, r.hud.last_frame), (0, 0))
        self.assertEqual(len(ack), m.ACK_BYTES)
        s.ack(ack)

    def test_abort_before_or_after_fence_restores_private_source_ownership(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        c = s.build(rgb(1), 1); packet = s.commit(c)
        outside = r.acquire_base(0)
        before = r.snapshot()
        for fence in (False, True):
            task = r.prepare(packet)
            self.assertEqual(r.base.readers, 2)
            self.assertEqual(r.published_snapshot(), {k: v for k, v in before.items() if k not in ('base_readers', 'hud_readers', 'reader_tokens')})
            if fence: r.mark_writes_drained(task)
            r.abort(task)
            self.assertEqual(r.snapshot(), before)
        r.release(outside)
        task = r.prepare(packet); r.mark_writes_drained(task); s.ack(r.present(task))

    def test_receiver_rechecks_late_base_and_hud_destination_readers(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        self.delivered(s, r, rgb(1), 1, promote=True)
        c = s.build(rgb(2), 2, force_key=True); packet = s.commit(c)
        task = r.prepare(packet); r.mark_writes_drained(task)
        a, b = r.acquire_base(0), r.acquire_hud(0)
        before = r.snapshot()
        with self.assertRaises(ValueError): r.present(task)
        self.assertEqual(r.snapshot(), before)
        r.release(a)
        with self.assertRaises(ValueError): r.present(task)
        r.release(b)
        s.ack(r.present(task))

    def test_unchanged_reader_bank_survives_root_state_swap(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        a, b = r.acquire_base(0), r.acquire_hud(0)
        self.delivered(s, r, rgb(1), 1, promote=True)
        self.assertEqual((r.base.readers, r.hud.readers), (1, [1, 0]))
        r.release(a); r.release(b)
        with self.assertRaises(ValueError): r.release(b)
        self.assertEqual((r.base.readers, r.hud.readers), (0, [0, 0]))

    def test_bad_fourth_patch_after_private_base_decode_is_atomic(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        c = s.build(rgb(1), 1); packet = s.commit(c)
        base, hud = m.compose.unbind(packet)
        meta = m.hc.parse(hud)
        body = bytearray(hud[:-4])
        body[m.hc.HEADER.size + sum(meta['sizes'][:3])] ^= 1
        bad = m.compose.bind(base, m.hc.seal(bytes(body)))
        before = r.snapshot()
        with self.assertRaises(ValueError): r.prepare(bad)
        self.assertEqual(r.snapshot(), before)
        self.assertIsNone(r.active_candidate)
        task = r.prepare(packet); r.mark_writes_drained(task); s.ack(r.present(task))

    def test_corrupt_pair_cap_and_wrong_epoch_reject_without_publication(self):
        s, r = self.pair()
        packet = s.commit(s.build(rgb(), 0))
        before = r.snapshot()
        for bad in (packet[:-1] + bytes([packet[-1] ^ 1]), packet[:-1], packet + bytes(49152)):
            with self.assertRaises(ValueError): r.prepare(bad)
            self.assertEqual(r.snapshot(), before)
        other = m.JointReceiver(epoch=2)
        with self.assertRaises(ValueError): other.prepare(packet)
        self.assertEqual(other.last_frame, -1)

    def test_valid_other_base_geometry_rejects_before_private_decode(self):
        image = rgb()
        encoder = m.C.Encoder(mode='gm')
        base = encoder.prepare(image[:442], 0, force_key=True).packet
        hud, _ = m.hc.Sender().prepare(image, 0)
        packet = m.compose.bind(base, hud)
        self.assertEqual((m.C.identity(base)['width'], m.C.identity(base)['height']), (720, 442))
        receiver = m.JointReceiver()
        before = receiver.snapshot()
        with self.assertRaises(ValueError): receiver.prepare(packet)
        self.assertEqual(receiver.snapshot(), before)
        self.assertIsNone(receiver.active_candidate)

    def test_packet_loss_and_ack_loss_keep_exact_pending_pair(self):
        s, r = self.pair()
        packet = s.commit(s.build(rgb(), 0))
        with self.assertRaises(ValueError): s.build(rgb(1), 1)
        self.assertEqual(s.retry(), packet)
        task = r.prepare(s.retry()); r.mark_writes_drained(task); ack = r.present(task)
        before = r.snapshot()
        self.assertEqual(r.retry_ack(s.retry()), ack)
        self.assertEqual(r.snapshot(), before)
        s.ack(ack)
        with self.assertRaises(ValueError): s.ack(ack)
        with self.assertRaises(ValueError): r.retry_ack(packet[:-1] + bytes([packet[-1] ^ 1]))

    def test_mixed_ack_and_wrong_pair_digest_cannot_advance_one_component(self):
        s, r = self.pair()
        _, old_ack, _ = self.delivered(s, r, rgb(), 0)
        packet = s.commit(s.build(rgb(1), 1))
        task = r.prepare(packet); r.mark_writes_drained(task); ack = r.present(task)
        before = s.snapshot()
        old = m.parse_ack(old_ack)
        parsed = m.parse_ack(ack)
        header = ack[:m.ACK_HEADER.size]
        mixed = m.hc.seal(header + old['base_ack'] + parsed['hud_ack'])
        altered = bytearray(ack[:-4]); altered[13] ^= 1
        for bad in (mixed, m.hc.seal(bytes(altered)), old_ack):
            with self.assertRaises(ValueError): s.ack(bad)
            self.assertEqual(s.snapshot(), before)
        s.ack(ack)

    def test_candidate_tampering_and_stale_handles_fail_closed(self):
        s, r = self.pair()
        c = s.build(rgb(), 0)
        object.__setattr__(c, 'frame_id', 1)
        with self.assertRaises(ValueError): s.commit(c)
        s.discard(c)
        with self.assertRaises(ValueError): s.commit(c)
        packet = s.commit(s.build(rgb(), 0))
        task = r.prepare(packet)
        object.__setattr__(task, 'frame_id', 1)
        with self.assertRaises(ValueError): r.mark_writes_drained(task)
        r.abort(task)
        with self.assertRaises(ValueError): r.present(task)

    def test_published_bank_arrays_are_readonly_and_shared_without_deepcopy(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        old_s = s.base.banks[0]
        old_r = r.base.banks[0]
        self.delivered(s, r, rgb(1), 1)
        self.assertIs(s.base.banks[0], old_s)
        self.assertIs(r.base.banks[0], old_r)
        for p in (*old_s.planes, *old_r.planes, *r.hud.display['patches'], r.display):
            self.assertFalse(p.flags.writeable)
            with self.assertRaises(ValueError): p.flat[0] = 0

    def test_in_place_sender_component_change_cannot_half_commit(self):
        s = m.JointSender()
        c = s.build(rgb(), 0)
        s.hud.reset(2)
        before = s.snapshot()
        with self.assertRaises(ValueError): s.commit(c)
        self.assertEqual(s.snapshot(), before)
        self.assertEqual(s.base.last_issued, -1)
        s.discard(c)

    def test_in_place_receiver_component_change_invalidates_private_pair(self):
        s, r = self.pair()
        packet = s.commit(s.build(rgb(), 0))
        task = r.prepare(packet)
        r.mark_writes_drained(task)
        r.hud.reset(2)
        before = r.snapshot()
        with self.assertRaises(ValueError): r.present(task)
        self.assertEqual(r.snapshot(), before)
        self.assertEqual(r.last_frame, -1)
        r.abort(task)

    def test_bounded_unique_reader_tokens_and_local_reset(self):
        s, r = self.pair()
        self.delivered(s, r, rgb(), 0)
        a, b = r.acquire_hud(0), r.acquire_hud(0)
        r.release(a)
        with self.assertRaises(ValueError): r.release(a)
        self.assertEqual(r.hud.readers[0], 1)
        with self.assertRaises(ValueError): r.reset(2)
        r.release(b)
        r._next_lease = m.hc.INVALID - 1
        lease = r.acquire_hud(0); r.release(lease)
        with self.assertRaises(ValueError): r.acquire_hud(0)
        r.reset(2); s.reset(2)
        self.assertEqual(r.last_frame, -1)
        self.delivered(s, r, rgb(), 0)


if __name__ == '__main__': unittest.main()
