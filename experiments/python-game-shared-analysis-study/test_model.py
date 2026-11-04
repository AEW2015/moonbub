import unittest
import numpy as np
import model as m
C = m.C


def image(seed=1):
    return np.random.default_rng(seed).integers(0, 256, (64, 64, 3), np.uint8)


def settle(e, c):
    before = e.banks.copy()
    packet = e.commit(c).packet
    rx = C.Receiver()
    rx.banks.update(before)
    out, _, ack = rx.receive(packet)
    e.ack(ack)
    return packet, out, ack


def seed_key(e, a):
    return settle(e, e.build(a, 0, quant_scale=16, force_key=True))


def semantic(e):
    return (e.last_issued, e._generation, tuple(e.pending),
            tuple((s, None if b is None else (b.frame_id, b.tag)) for s, b in e.banks.items()))


class SharedTests(unittest.TestCase):
    def test_no_context_is_exact_dropin(self):
        a = image(); plain, shared = C.Encoder(mode='gm'), m.SharedEncoder(mode='gm')
        x, y = plain.build(a, 0), shared.build(a, 0)
        self.assertEqual(x.packet, y.packet)
        self.assertEqual((plain.analysis_count, plain.forward_calls), (shared.analysis_count, shared.forward_calls))
        shared.discard(y); plain.discard(x)

    def test_key_retry_bytes_analysis_counts_and_storage(self):
        a = image(); plain, shared = C.Encoder(mode='gm'), m.SharedEncoder(mode='gm')
        shared.begin_source(a, 0, force_key=True)
        for scale in (8, 16, 32):
            x = plain.build(a, 0, quant_scale=scale, force_key=True)
            y = shared.build(a, 0, quant_scale=scale, force_key=True)
            self.assertEqual(x.packet, y.packet)
            self.assertEqual(C.plain_info(y)['analyze_calls'], 0)
            if scale != 32:
                plain.discard(x); shared.discard(y)
        info = shared.end_source()
        self.assertEqual((plain.analysis_count, plain.forward_calls), (3, 9))
        self.assertEqual((shared.analysis_count, shared.forward_calls), (1, 3))
        self.assertEqual((info['cached_attempts'], info['eliminated_analysis_calls']), (3, 2))
        self.assertEqual(info['retained_analysis_array_bytes'], 64 * 64 * 3 // 2 * (2 + 8))
        self.assertEqual(info['source_guard_calls'], 4)
        self.assertEqual(info['source_guard_bytes'], 4 * a.nbytes)
        self.assertEqual(info['retained_source_copy_bytes'], 0)
        xp, xo, xa = settle(plain, x); yp, yo, ya = settle(shared, y)
        self.assertEqual((xp, xa), (yp, ya)); np.testing.assert_array_equal(xo, yo)

    def test_p_retry_bytes_and_external_lease_preserved(self):
        a = image(); plain, shared = C.Encoder(mode='gm'), m.SharedEncoder(mode='gm')
        seed_key(plain, a); seed_key(shared, a)
        lp, ls = plain.acquire(0), shared.acquire(0)
        before = semantic(shared); b = image(2)
        shared.begin_source(b, 1)
        for scale in (8, 16, 32):
            x, y = plain.build(b, 1, quant_scale=scale), shared.build(b, 1, quant_scale=scale)
            self.assertEqual(x.packet, y.packet); self.assertEqual(semantic(shared), before)
            if scale != 32:
                plain.discard(x); shared.discard(y)
        self.assertEqual(shared.readers, 3)
        shared.end_source(); self.assertEqual(shared.readers, 2)
        xp, xo, xa = settle(plain, x); yp, yo, ya = settle(shared, y)
        self.assertEqual((xp, xa), (yp, ya)); np.testing.assert_array_equal(xo, yo)
        self.assertEqual(shared.readers, 1); self.assertIn(ls, shared._leases)
        plain.release(lp); shared.release(ls)

    def test_promotions_include_source_equals_destination(self):
        a = image(); plain, shared = C.Encoder(mode='gm'), m.SharedEncoder(mode='gm')
        seed_key(plain, a); seed_key(shared, a)
        for fid in (1, 2):
            b = image(2 + fid); shared.begin_source(b, fid, promote=True)
            for scale in (8, 32):
                x = plain.build(b, fid, quant_scale=scale, promote=True)
                y = shared.build(b, fid, quant_scale=scale, promote=True)
                self.assertEqual(x.packet, y.packet)
                if scale == 8:
                    plain.discard(x); shared.discard(y)
            shared.end_source()
            xp, xo, xa = settle(plain, x); yp, yo, ya = settle(shared, y)
            self.assertEqual((xp, xa), (yp, ya)); np.testing.assert_array_equal(xo, yo)

    def test_four_cap_failures_preserve_identity_and_retry_same_id(self):
        e = m.SharedEncoder(frame_cap=512, mode='gm'); a = image(); before = semantic(e)
        e.begin_source(a, 0)
        for scale in (8, 16, 32, 32):
            c = e.build(a, 0, quant_scale=scale)
            self.assertFalse(c.accepted); e.discard(c); self.assertEqual(semantic(e), before)
        info = e.end_source(); self.assertEqual(info['eliminated_analysis_calls'], 3)
        self.assertEqual(e.last_issued, -1); self.assertEqual(e.readers, 0)
        a = np.full((64, 64, 3), 128, np.uint8)
        e.begin_source(a, 0); c = e.build(a, 0, quant_scale=32); e.end_source()
        self.assertTrue(c.accepted); settle(e, c); self.assertEqual(e.last_issued, 0)

    def test_mutated_input_rejected_without_candidate_leak(self):
        e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0); a[0, 0, 0] ^= 1
        with self.assertRaises(ValueError): e.build(a, 0)
        self.assertIsNone(e.active_candidate); e.end_source(); self.assertEqual(e.readers, 0)

    def test_distinct_equal_input_is_not_borrowed_source(self):
        e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0)
        with self.assertRaises(ValueError): e.build(a.copy(), 0)
        e.end_source(); self.assertIsNone(e.active_candidate)

    def test_epoch_config_and_frame_guards(self):
        for field, value in (('epoch', 2), ('frame_cap', 45000), ('window', 2), ('mode', 'exact')):
            e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0); setattr(e, field, value)
            with self.assertRaises(ValueError): e.build(a, 0)
            e.end_source(); self.assertIsNone(e.active_candidate)
        e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0)
        with self.assertRaises(ValueError): e.build(a, 1)
        e.end_source()

    def test_stale_reference_object_rejects_and_releases_only_context(self):
        e = m.SharedEncoder(mode='gm'); a = image(); seed_key(e, a)
        external = e.acquire(0); old = e.banks[0]; b = image(2); e.begin_source(b, 1)
        e.banks[0] = C.Bank(old.frame_id, old.tag, old.planes)
        with self.assertRaises(ValueError): e.build(b, 1)
        e.end_source(); self.assertEqual(e.readers, 1); self.assertIn(external, e._leases); e.release(external)

    def test_callback_failure_keeps_external_baseline(self):
        class Fault:
            def select(self, rgb, budget): raise RuntimeError('injected callback failure')
        e = m.SharedEncoder(mode='gm'); a = image(); seed_key(e, a)
        external = e.acquire(0); e.patch_builder = Fault(); b = image(3); before = semantic(e); e.begin_source(b, 1)
        with self.assertRaises(RuntimeError): e.build(b, 1)
        self.assertEqual(e.readers, 2); self.assertIsNone(e.active_candidate)
        e.end_source(); self.assertEqual(e.readers, 1); self.assertEqual(semantic(e), before); e.release(external)

    def test_end_source_retains_winning_candidate_lease(self):
        e = m.SharedEncoder(mode='gm'); a = image(); seed_key(e, a); b = image(4)
        e.begin_source(b, 1); c = e.build(b, 1)
        self.assertEqual(e.readers, 2); e.end_source(); self.assertEqual(e.readers, 1)
        self.assertIs(e.active_candidate, c); e.discard(c); self.assertEqual(e.readers, 0)

    def test_double_context_and_end_rejected(self):
        e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0)
        with self.assertRaises(ValueError): e.begin_source(a, 0)
        e.end_source()
        with self.assertRaises(ValueError): e.end_source()

    def test_invalid_map_and_invalid_reference_cleanup(self):
        e = m.SharedEncoder(mode='gm'); a = image(); e.begin_source(a, 0)
        with self.assertRaises(ValueError): e.build(a, 0, quant_scale=7)
        self.assertIsNone(e.active_candidate); e.end_source()
        with self.assertRaises(ValueError): e.begin_source(a, 0, reference_bank=0)
        self.assertIsNone(e._shared_context)

    def test_exact_and_pruned_modes_keep_packet_and_decode_parity(self):
        for mode in ('exact', 'prune2', 'prune4'):
            a = image(41); p, s = C.Encoder(mode=mode), m.SharedEncoder(mode=mode)
            seed_key(p, a); seed_key(s, a); b = image(42)
            s.begin_source(b, 1)
            for scale in (8, 32):
                x, y = p.build(b, 1, quant_scale=scale), s.build(b, 1, quant_scale=scale)
                self.assertEqual(x.packet, y.packet)
                if scale == 8: p.discard(x); s.discard(y)
            s.end_source()
            xp, xo, xa = settle(p, x); yp, yo, ya = settle(s, y)
            self.assertEqual((xp, xa), (yp, ya)); np.testing.assert_array_equal(xo, yo)

    def test_context_must_end_before_semantic_commit(self):
        a = image(); e = m.SharedEncoder(mode='gm'); before = semantic(e)
        e.begin_source(a, 0); c = e.build(a, 0)
        with self.assertRaises(ValueError): e.commit(c)
        self.assertEqual(semantic(e), before)
        e.end_source(); settle(e, c); self.assertEqual(e.last_issued, 0)

    def test_explicit_extra_reader_descriptor_bound(self):
        a = image(); e = m.SharedEncoder(mode='gm'); e.max_readers = 8; seed_key(e, a)
        leases = [e.acquire(0) for _ in range(7)]; before = semantic(e); calls = e.analysis_count
        b = image(3)
        with self.assertRaises(ValueError): e.begin_source(b, 1)
        self.assertEqual(e.readers, 7); self.assertEqual(e.analysis_count, calls)
        self.assertIsNone(e._shared_context); self.assertEqual(semantic(e), before)
        e.release(leases.pop()); e.begin_source(b, 1); c = e.build(b, 1)
        self.assertEqual(e.readers, 8)
        info = e.end_source(); self.assertEqual(info['additional_context_reader_descriptors'], 1)
        e.discard(c); self.assertEqual(e.readers, 6)
        for lease in leases: e.release(lease)


if __name__ == '__main__': unittest.main()
