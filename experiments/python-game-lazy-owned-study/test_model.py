import unittest
from dataclasses import replace
import numpy as np
import model as x


def small(seed=1):
    return np.random.default_rng(seed).integers(0, 256, (64, 64, 3), np.uint8)


def canvas(seed=1):
    rgb = np.full((480, 720, 3), (20 + seed) % 255, np.uint8)
    for i, (a, b, w, h) in enumerate(x.m.RECTANGLES):
        rgb[b:b + h, a:a + w] = (40 + i + seed, 80 + i, 120 + i)
    return rgb


def settle(e, c):
    banks = e.banks.copy()
    packet = e.commit(c).packet
    rx = x.C.Receiver()
    rx.banks.update(banks)
    output, _, ack = rx.receive(packet)
    e.ack(ack)
    return packet, ack, output


def begin(e, image, frame, **kwargs):
    pool = x.CapturePool()
    lease = pool.capture(image)
    e.bind_capture(pool, lease)
    e.begin_source(lease.array, frame, **kwargs)
    return pool, lease


def end(e, pool, lease):
    info = e.end_source()
    e.unbind_capture()
    pool.release(lease)
    return info


class CaptureTests(unittest.TestCase):
    def test_private_bytes_backing_survives_external_mutation(self):
        source = small(); original = source.copy(); pool = x.CapturePool(); a = pool.capture(source)
        source[:] = 0
        np.testing.assert_array_equal(a.array, original)
        with self.assertRaises(ValueError): a.array[0, 0, 0] = 3
        with self.assertRaises(ValueError): a.array.setflags(write=True)
        with self.assertRaises(ValueError): a.array.base.setflags(write=True)
        self.assertEqual(pool.copied_bytes, source.nbytes)
        pool.release(a); self.assertEqual(pool.pixel_bytes, 0)

    def test_two_slots_and_eight_readers_are_bounded(self):
        pool = x.CapturePool(); a = pool.capture(small()); b = pool.capture(small(2))
        with self.assertRaises(ValueError): pool.capture(small(3))
        leases = [a, b]
        for _ in range(6): leases.append(pool.acquire(a))
        with self.assertRaises(ValueError): pool.acquire(a)
        self.assertEqual(pool.active_readers, 8)
        for lease in leases: pool.release(lease)
        self.assertEqual((pool.active_readers, pool.pixel_bytes), (0, 0))

    def test_release_identity_generation_reset_and_no_aba(self):
        pool = x.CapturePool(); a = pool.capture(small()); b = pool.acquire(a)
        with self.assertRaises(ValueError): pool.release(replace(a))
        pool.release(a)
        with self.assertRaises(ValueError): pool.release(a)
        self.assertEqual(pool.active_readers, 1)
        with self.assertRaises(ValueError): pool.replace(b.slot, small(2))
        with self.assertRaises(ValueError): pool.reset(2)
        pool.release(b); c = pool.replace(b.slot, small(3))
        self.assertGreater(c.generation, b.generation)
        with self.assertRaises(ValueError): pool.validate(b)
        pool.release(c); pool.reset(2)
        d = pool.capture(small())
        with self.assertRaises(ValueError): pool.validate(a)
        self.assertEqual(d.epoch, 2); pool.release(d)

    def test_token_and_generation_exhaustion_fail_before_copy(self):
        pool = x.CapturePool(); pool._next_token = x.LIMIT
        with self.assertRaises(ValueError): pool.capture(small())
        self.assertEqual(pool.copies, 0)
        pool.reset(2); pool._generations[0] = x.LIMIT
        with self.assertRaises(ValueError): pool.capture(small(), slot=0)
        self.assertEqual(pool.copies, 0)


class LazyTests(unittest.TestCase):
    def test_context_is_lazy_and_first_call_is_honestly_counted(self):
        e = x.LazyEncoder(mode='gm'); pool, lease = begin(e, small(), 0)
        self.assertEqual((e.analysis_count, e.forward_calls), (0, 0))
        self.assertEqual(e.last_source_info['retained_analysis_array_bytes'], 0)
        c = e.build(lease.array, 0)
        self.assertEqual((e.analysis_count, e.forward_calls), (1, 3))
        self.assertEqual((x.C.plain_info(c)['analyze_calls'], x.C.plain_info(c)['forward_calls']), (1, 3))
        info = end(e, pool, lease)
        self.assertEqual((info['source_guard_calls'], info['source_guard_bytes']), (0, 0))
        self.assertEqual(info['cached_attempts'], 1)
        settle(e, c)

    def test_exact_packet_ack_output_parity_across_modes_and_retries(self):
        for mode in ('gm', 'exact', 'prune2', 'prune4'):
            plain, lazy = x.C.Encoder(mode=mode), x.LazyEncoder(mode=mode)
            for fid, promoted in ((0, False), (1, False), (2, True), (3, True)):
                source = small(9 + fid); pool, lease = begin(lazy, source, fid, promote=promoted)
                before = lazy.analysis_count
                for q in (8, 16, 32):
                    a = plain.build(source, fid, quant_scale=q, promote=promoted)
                    b = lazy.build(lease.array, fid, quant_scale=q, promote=promoted)
                    self.assertEqual(a.packet, b.packet)
                    if q != 32: plain.discard(a); lazy.discard(b)
                self.assertEqual(lazy.analysis_count - before, 1)
                info = end(lazy, pool, lease)
                self.assertEqual((info['cached_attempts'], info['eliminated_analysis_calls']), (3, 2))
                pa, aa, oa = settle(plain, a); pb, ab, ob = settle(lazy, b)
                self.assertEqual((pa, aa), (pb, ab)); np.testing.assert_array_equal(oa, ob)

    def test_context_rejects_arbitrary_borrowed_array(self):
        e = x.LazyEncoder(mode='gm')
        with self.assertRaises(ValueError): e.begin_source(small(), 0)
        pool, lease = begin(e, small(), 0)
        with self.assertRaises(ValueError): e.build(lease.array.copy(), 0)
        self.assertIsNone(e.active_candidate); end(e, pool, lease)

    def test_external_input_change_does_not_change_frozen_analysis(self):
        source = small(); original = source.copy(); e = x.LazyEncoder(mode='gm')
        pool, lease = begin(e, source, 0); source[:] = 0
        c = e.build(lease.array, 0)
        control = x.C.Encoder(mode='gm'); baseline = control.build(original, 0)
        self.assertEqual(c.packet, baseline.packet)
        end(e, pool, lease); e.discard(c); control.discard(baseline)

    def test_four_cap_rejections_reuse_unissued_id(self):
        e = x.LazyEncoder(mode='gm', frame_cap=512); pool, lease = begin(e, small(), 0)
        for q in (8, 16, 32, 32):
            c = e.build(lease.array, 0, quant_scale=q); self.assertFalse(c.accepted); e.discard(c)
        info = end(e, pool, lease)
        self.assertEqual(info['eliminated_analysis_calls'], 3)
        self.assertEqual((e.last_issued, e.readers, pool.active_readers), (-1, 0, 0))
        pool, lease = begin(e, np.full((64, 64, 3), 128, np.uint8), 0)
        c = e.build(lease.array, 0, quant_scale=32); end(e, pool, lease)
        self.assertTrue(c.accepted); settle(e, c)

    def test_stale_capture_and_config_fail_before_analysis(self):
        e = x.LazyEncoder(mode='gm'); pool, lease = begin(e, small(), 0); pool.release(lease)
        with self.assertRaises(ValueError): e.build(lease.array, 0)
        e.end_source(); e.unbind_capture(); self.assertEqual(e.analysis_count, 0)
        e = x.LazyEncoder(mode='gm'); pool, lease = begin(e, small(), 0); e.epoch = 2
        with self.assertRaises(ValueError): e.build(lease.array, 0)
        end(e, pool, lease)

    def test_bank_and_capture_owners_survive_failure_and_winner(self):
        e = x.LazyEncoder(mode='gm'); a = small()
        settle(e, e.build(a, 0)); external = e.acquire(0)
        pool, lease = begin(e, small(2), 1)
        c = e.build(lease.array, 1); self.assertEqual(e.readers, 3)
        end(e, pool, lease); self.assertEqual(e.readers, 2)
        e.discard(c); self.assertEqual(e.readers, 1); self.assertIn(external, e._leases)
        e.release(external)

    def test_callback_failure_and_end_before_commit(self):
        class Broken:
            def select(self, rgb, budget): raise RuntimeError('callback')
        e = x.LazyEncoder(mode='gm'); pool, lease = begin(e, small(), 0)
        c = e.build(lease.array, 0)
        with self.assertRaises(ValueError): e.commit(c)
        e.discard(c); end(e, pool, lease)
        e.patch_builder = Broken(); pool, lease = begin(e, small(), 0)
        with self.assertRaises(RuntimeError): e.build(lease.array, 0)
        self.assertIsNone(e.active_candidate); end(e, pool, lease)
        self.assertEqual(e.readers, 0)


class OwnedJointTests(unittest.TestCase):
    def test_complete_joint_packet_ack_display_parity_and_capture_release(self):
        plain, owned = x.m.JointSender(), x.OwnedJointSender()
        rp, ro = x.m.JointReceiver(), x.m.JointReceiver()
        for fid in (0, 1, 2):
            source = canvas(fid)
            a = plain.build(source, fid, promote=fid == 2)
            b = owned.build(source, fid, promote=fid == 2)
            self.assertEqual(a.packet, b.packet)
            self.assertEqual(b.info['capture']['copied_bytes'], source.nbytes)
            self.assertEqual(b.info['capture']['active_readers_after'], 0)
            self.assertEqual(b.info['capture']['retained_pool_pixel_bytes_after'], 0)
            pa, pb = plain.commit(a), owned.commit(b)
            ta, tb = rp.prepare(pa), ro.prepare(pb)
            rp.mark_writes_drained(ta); ro.mark_writes_drained(tb)
            aa, ab = rp.present(ta), ro.present(tb)
            self.assertEqual(aa, ab); plain.ack(aa); owned.ack(ab)
            np.testing.assert_array_equal(rp.display, ro.display)

    def test_capture_precedes_hud_and_original_mutation_cannot_split_pair(self):
        source = canvas(); original = source.copy(); owned = x.OwnedJointSender()
        select = owned.hud.selector.select
        def mutating(rgb, budget):
            source[:] = 0
            self.assertFalse(rgb.flags.writeable)
            return select(rgb, budget)
        owned.hud.selector.select = mutating
        b = owned.build(source, 0)
        a = x.m.JointSender().build(original, 0)
        self.assertEqual(a.packet, b.packet)
        owned.discard(b)

    def test_cap_deadline_callback_pool_pressure_cleanup(self):
        s = x.OwnedJointSender(frame_cap=256); before = s.snapshot()
        c = s.build(canvas(), 0); self.assertFalse(c.accepted); self.assertEqual(s.snapshot(), before)
        self.assertEqual(s.capture_pool.active_readers, 0)
        c = s.build(canvas(), 0, now_ms=1, deadline_ms=1)
        self.assertFalse(c.accepted); self.assertEqual(c.info['capture']['copied_bytes'], 0)
        s.frame_cap = 49152
        original = s.hud.selector.select
        def broken(rgb, budget): raise RuntimeError('HUD callback')
        s.hud.selector.select = broken
        with self.assertRaises(RuntimeError): s.build(canvas(), 0)
        self.assertEqual((s.capture_pool.active_readers, s.capture_pool.pixel_bytes), (0, 0))
        self.assertEqual(s.snapshot(), before)
        s.hud.selector.select = original
        p, q = s.capture_pool.capture(canvas()), s.capture_pool.capture(canvas(2))
        with self.assertRaises(ValueError): s.build(canvas(), 0)
        self.assertEqual(s.capture_pool.active_readers, 2)
        s.capture_pool.release(p); s.capture_pool.release(q)
        c = s.build(canvas(), 0); self.assertTrue(c.accepted); s.discard(c)

    def test_reset_requires_drained_capture_and_preserves_bound_pool(self):
        s = x.OwnedJointSender(); pool = s.capture_pool; lease = pool.capture(canvas())
        with self.assertRaises(ValueError): s.reset(2)
        pool.release(lease); s.reset(2)
        self.assertIs(s.capture_pool, pool); self.assertEqual(s.epoch, 2)


if __name__ == '__main__': unittest.main()
