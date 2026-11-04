import unittest
import numpy as np
import model as r


def endpoints():
    h, t = r.Host(101), r.Target(202)
    h.transport_drained = t.transport_drained = True
    return h, t


def data(h, t, frame=0):
    rgb = np.full((480, 720, 3), [44, 96, 156], dtype=np.uint8)
    c = h.build(rgb, frame)
    if not c.accepted:
        raise AssertionError('flat frame did not fit')
    packet = h.commit(c)
    task = t.prepare_data(packet)
    t.receiver.mark_writes_drained(task)
    ack = t.receiver.present(task)
    h.acknowledge_data(ack)
    return packet, ack


class RecoveryTests(unittest.TestCase):
    def test_nominal_exact_sizes_and_independent_refresh(self):
        h, t = endpoints(); trace, done = r.exchange(h, t)
        self.assertTrue(done)
        self.assertEqual((h.phase, t.phase, h.ledger.last, t.ledger.last), ('RUNNING', 'RUNNING', 1, 1))
        self.assertEqual(len(trace), 8)
        self.assertTrue(all(len(bytes.fromhex(x['bytes'])) == 46 for x in trace))
        packet, _ = data(h, t)
        base, hud = r.m.compose.unbind(packet)
        self.assertTrue(r.m.C.identity(base)['key'])
        self.assertEqual(r.m.hc.parse(hud)['refslot'], r.m.hc.NO_REF)

    def test_every_single_control_loss_recovers_with_identical_retry(self):
        for kind in range(r.HELLO, r.GO_ACK + 1):
            with self.subTest(kind=kind):
                h, t = endpoints(); trace, done = r.exchange(h, t, drop_once=kind)
                self.assertTrue(done)
                lost = [x for x in trace if not x['delivered']]
                self.assertEqual(len(lost), 1)
                forwards = [x['bytes'] for x in trace if x['direction'] == 'forward']
                self.assertLess(len(set(forwards)), len(forwards))
                data(h, t)

    def test_exhausted_go_ack_stops_host_without_fabricating_ack(self):
        h, t = endpoints(); trace, done = r.exchange(h, t, drop_all=r.GO_ACK)
        self.assertFalse(done)
        self.assertEqual((h.phase, t.phase), ('SAFE_STOP', 'RUNNING'))
        self.assertEqual(sum(not x['delivered'] for x in trace), 5)
        with self.assertRaises(ValueError): h.build(np.zeros((480, 720, 3), np.uint8), 0)

    def test_capability_crc_and_scalar_errors_do_not_start_session(self):
        h, t = endpoints(); hello = h.start()
        bad = hello[:-1] + bytes([hello[-1] ^ 1])
        for packet in (bad, hello[:-1], r.encode(r.HELLO, 0, 101, 0, b'x' * 16)):
            with self.assertRaises(ValueError): t.accept(packet)
        self.assertEqual(t.phase, 'STOPPED')
        for host, target in ((True, 0), (1, 0.0), (0, 0), (1, -1)):
            with self.assertRaises(ValueError): r.encode(r.HELLO, 0, host, target)

    def test_target_and_host_reboot_get_new_epoch_and_reject_old_data(self):
        h, t = endpoints(); r.exchange(h, t); old_packet, old_ack = data(h, t)
        new_t = r.Target(303, ledger=t.ledger); new_t.transport_drained = True
        with self.assertRaises(ValueError): new_t.prepare_data(old_packet)
        r.exchange(h, new_t)
        self.assertEqual(h.ledger.last, 2)
        with self.assertRaises(ValueError): new_t.prepare_data(old_packet)
        new_packet, _ = data(h, new_t)
        self.assertNotEqual(old_packet, new_packet)
        with self.assertRaises(ValueError): h.acknowledge_data(old_ack)
        new_h = r.Host(404, ledger=h.ledger); new_h.transport_drained = True
        r.exchange(new_h, new_t)
        self.assertEqual(new_h.ledger.last, 3)
        with self.assertRaises(ValueError): new_t.prepare_data(new_packet)
        data(new_h, new_t)

    def test_target_held_and_late_readers_block_reset(self):
        h, t = endpoints(); r.exchange(h, t); data(h, t)
        hold = t.receiver.acquire_hud(0)
        offer = h.accept(t.accept(h.start()))
        busy = t.accept(offer)
        self.assertEqual(r.parse(busy)['kind'], r.BUSY)
        self.assertEqual(t.phase, 'QUIESCING')
        t.receiver.release(hold)
        ready = t.accept(h.accept(busy))
        commit = h.accept(ready)
        late = t.receiver.acquire_base(0)
        with self.assertRaises(ValueError): t.accept(commit)
        t.receiver.release(late)
        go = h.accept(t.accept(commit)); h.accept(t.accept(go))
        self.assertEqual(h.phase, 'RUNNING')

    def test_host_late_reader_blocks_discard_of_old_source_bank(self):
        h, t = endpoints(); r.exchange(h, t); data(h, t)
        offer = h.accept(t.accept(h.start())); ready = t.accept(offer)
        lease = h.sender.base.acquire(0)
        with self.assertRaises(ValueError): h.accept(ready)
        h.sender.base.release(lease)
        commit = h.accept(ready)
        response = t.accept(commit)
        late = h.sender.base.acquire(0)
        with self.assertRaises(ValueError): h.accept(response)
        h.sender.base.release(late)
        h.accept(t.accept(h.accept(response)))
        self.assertEqual(h.phase, 'RUNNING')

    def test_delayed_commit_and_go_never_clear_live_new_banks(self):
        h, t = endpoints(); trace, _ = r.exchange(h, t); data(h, t)
        before = t.receiver.published_snapshot()
        for item in trace:
            if item['direction'] == 'forward' and item['kind'] in (r.OFFER, r.COMMIT, r.GO):
                t.accept(bytes.fromhex(item['bytes']))
                self.assertEqual(t.receiver.published_snapshot(), before)

    def test_new_boot_nonce_and_wrong_kind_reject_stale_control(self):
        h, t = endpoints(); hello = h.start(); reply = t.accept(hello)
        offer = h.accept(reply)
        new_t = r.Target(303); new_t.transport_drained = True
        with self.assertRaises(ValueError): new_t.accept(offer)
        with self.assertRaises(ValueError): t.accept(r.encode(r.GO, *h.proposal))
        with self.assertRaises(ValueError): h.accept(reply)

    def test_drain_permission_and_epoch_exhaustion_fail_closed(self):
        h, t = r.Host(101), r.Target(202)
        with self.assertRaises(ValueError): h.start()
        h.transport_drained = True
        offer = h.accept(t.accept(h.start()))
        self.assertEqual(r.parse(t.accept(offer))['kind'], r.BUSY)
        h, t = endpoints(); h.ledger.last = r.MAX_EPOCH
        with self.assertRaises(ValueError): h.accept(t.accept(h.start()))
        self.assertNotEqual(h.phase, 'RUNNING')
        self.assertEqual(h.ledger.last, r.MAX_EPOCH)

    def test_repeated_busy_also_exhausts_bounded_attempts(self):
        h, t = endpoints()
        t.transport_drained = False
        offer = h.accept(t.accept(h.start()))
        for _ in range(h.max_retries):
            self.assertEqual(h.accept(t.accept(offer)), offer)
        with self.assertRaises(ValueError): h.accept(t.accept(offer))
        self.assertEqual(h.phase, 'SAFE_STOP')


if __name__ == '__main__':
    unittest.main()
