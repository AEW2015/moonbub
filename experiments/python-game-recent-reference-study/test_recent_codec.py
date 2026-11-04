import hashlib
import struct
import unittest
import numpy as np

import recent_codec as c


class RecentReferenceTests(unittest.TestCase):
    def image(self, value=60): return np.full((16,32,3),value,np.uint8)

    def pair(self, **kwargs): return c.Encoder(**kwargs), c.Receiver(frame_cap=kwargs.get('frame_cap',49152))

    def step(self, enc, rx, frame, *, rgb=None, **kwargs):
        d=enc.prepare(self.image(frame+50) if rgb is None else rgb,frame,**kwargs)
        self.assertTrue(d.accepted)
        rgb,info,ack=rx.receive(d.packet)
        self.assertEqual(hashlib.sha256(rgb.tobytes()).hexdigest(),enc.expected_hash(frame))
        self.assertTrue(enc.ack(ack))
        self.assertLessEqual(sum(v is not None for v in enc.banks.values()),2)
        self.assertLessEqual(sum(v is not None for v in rx.banks.values()),2)
        for slot in (0,1):
            if enc.banks[slot] is None:
                self.assertIsNone(rx.banks[slot]);continue
            self.assertEqual(enc.banks[slot].frame_id,rx.banks[slot].frame_id)
            self.assertEqual(enc.banks[slot].tag,rx.banks[slot].tag)
            self.assertIsNot(enc.banks[slot].planes,rx.banks[slot].planes)
            for a,b in zip(enc.banks[slot].planes,rx.banks[slot].planes):np.testing.assert_array_equal(a,b)
        return d,info,ack

    def test_key_recent_p_reconstruction_and_refresh_parity(self):
        enc,rx=self.pair()
        for i in range(10):
            d,_,_=self.step(enc,rx,i,promote=i%2==0,force_key=i==7)
            self.assertEqual(d.info['promotion_reconstruction_paid'],d.key or d.promoted)
            self.assertEqual(d.info['reference_read_array_bytes'],2*d.info['reference_read_bytes'])
        self.assertEqual(enc.banks[0].frame_id,7)
        self.assertEqual(enc.banks[1].frame_id,8)
        self.assertGreater(enc.reference_read_bytes,0)
        self.assertLessEqual(enc.peak_retained_banks,2)

    def test_immutable_wrapped_profile_matches_frozen_gm_pixels_and_inner_bytes(self):
        enc,rx=self.pair();gm=c.gm.Encoder();baseline=c.gm.Receiver()
        for i in range(8):
            source=self.image(60+i);d=enc.prepare(source,i,force_key=i==5)
            base=gm.prepare(source,i,force_key=i==5)
            self.assertEqual(c.identity(d.packet)['inner'],base)
            actual,_,ack=rx.receive(d.packet);expected,_=baseline.receive(base)
            np.testing.assert_array_equal(actual,expected)
            enc.ack(ack);gm.ack(i,epoch=1)

    def test_cap_rejection_before_state_commit_pays_promotion_work(self):
        enc,rx=self.pair(frame_cap=230)
        self.step(enc,rx,0,rgb=self.image())
        before=(enc.last_issued,enc.banks[0],enc.banks[1],enc._generation)
        noise=np.random.default_rng(14).integers(0,256,(16,32,3),dtype=np.uint8)
        d=enc.prepare(noise,1,promote=True)
        self.assertFalse(d.accepted);self.assertGreater(d.info['bytes'],230)
        self.assertGreater(d.service_ms,0);self.assertGreater(d.info['reconstruction_ms'],0)
        self.assertEqual(before,(enc.last_issued,enc.banks[0],enc.banks[1],enc._generation))
        self.assertFalse(enc.pending)

    def test_p_window_and_conservative_promotion_drain(self):
        enc,rx=self.pair();self.step(enc,rx,0)
        decisions=[enc.prepare(self.image(i+50),i) for i in (1,2,3)]
        self.assertFalse(enc.can_prepare());self.assertFalse(enc.can_prepare(promote=True))
        with self.assertRaises(ValueError):enc.prepare(self.image(),4,promote=True)
        feedbacks=[rx.receive(d.packet)[2] for d in decisions]
        for ack in reversed(feedbacks):self.assertTrue(enc.ack(ack))
        self.assertEqual(enc.banks[0].frame_id,0)
        self.step(enc,rx,4,promote=True)
        self.assertEqual(enc.banks[1].frame_id,4)

    def test_physical_leases_block_overwrite_and_have_owned_release(self):
        enc,rx=self.pair();self.step(enc,rx,0);self.step(enc,rx,1,promote=True)
        lease=enc.acquire(1)
        self.assertFalse(enc.can_prepare(promote=True))
        with self.assertRaises(ValueError):enc.prepare(self.image(),2,force_key=True)
        with self.assertRaises(ValueError):enc.release(c.Lease(enc._owner,1,enc.banks[1]))
        with self.assertRaises(ValueError):rx.release(lease)
        enc.release(lease)
        d=enc.prepare(self.image(),2,promote=True)
        receiver_lease=rx.acquire(1)
        with self.assertRaises(ValueError):rx.begin(d.packet)
        self.assertEqual(rx.last_frame_id,1)
        rx.release(receiver_lease)
        self.assertTrue(enc.ack(rx.receive(d.packet)[2]))

    def test_begin_complete_and_abort_hold_reader_without_early_publication(self):
        enc,rx=self.pair();self.step(enc,rx,0)
        d=enc.prepare(self.image(90),1,promote=True)
        old=dict(rx.banks);task=rx.begin(d.packet)
        self.assertEqual(rx.banks,old);self.assertEqual(rx.last_frame_id,0);self.assertEqual(rx.readers,1)
        with self.assertRaises(ValueError):rx.begin(d.packet)
        with self.assertRaises(TypeError):task.meta['destination_bank']=0
        with self.assertRaises(ValueError):task.rgb[0,0]=0
        rx.abort(task);self.assertIsNone(rx.active);self.assertEqual(rx.readers,0)
        self.assertEqual(rx.banks,old);self.assertGreater(rx.reconstruction_write_bytes,0)
        with self.assertRaises(ValueError):rx.complete(task)
        task=rx.begin(d.packet);_,_,ack=rx.complete(task);enc.ack(ack)
        self.assertEqual(rx.banks[1].frame_id,1)

    def test_lost_promotion_ack_disables_old_bank_and_falls_back_to_key(self):
        enc,rx=self.pair();self.step(enc,rx,0);self.step(enc,rx,1,promote=True)
        old=enc.banks[1]
        d=enc.prepare(self.image(75),2,promote=True)
        self.assertIsNone(enc.banks[1]);self.assertFalse(enc.can_prepare())
        _,_,lost_ack=rx.receive(d.packet)
        self.assertTrue(enc.expire(2));self.assertIsNone(enc.banks[1])
        next_frame=enc.prepare(self.image(76),3)
        self.assertEqual(next_frame.reference_bank,0)
        _,_,ack=rx.receive(next_frame.packet);self.assertTrue(enc.ack(ack))
        self.assertFalse(enc.ack(lost_ack));self.assertIsNone(enc.banks[1])
        self.step(enc,rx,4,promote=True)
        self.assertNotEqual(enc.banks[1].frame_id,old.frame_id)

    def test_lost_key_ack_requires_new_key_recovery(self):
        enc,rx=self.pair();d=enc.prepare(self.image(),0);_,_,ack=rx.receive(d.packet)
        self.assertTrue(enc.expire(0));self.assertTrue(all(b is None for b in enc.banks.values()))
        self.assertFalse(enc.ack(ack))
        recovered,_,_=self.step(enc,rx,1)
        self.assertTrue(recovered.key)

    def test_feedback_binds_outer_body_session_and_published_reference(self):
        enc,rx=self.pair();d=enc.prepare(self.image(),0);_,_,ack=rx.receive(d.packet)
        fields=list(c.FEEDBACK.unpack_from(ack))
        for index,value in ((3,2),(5,c.body_crc(c.identity(d.packet)['inner'])),(6,1),(7,9),(8,b'x'*16)):
            altered=fields.copy();altered[index]=value
            with self.assertRaises(ValueError):enc.ack(c.seal(c.FEEDBACK.pack(*altered)))
            self.assertIn(0,enc.pending);self.assertIsNone(enc.banks[0])
        self.assertTrue(enc.ack(ack));self.assertFalse(enc.ack(ack))
        d=enc.prepare(self.image(70),1,promote=True)
        self.assertTrue(enc.ack(c.feedback(c.identity(d.packet),c.NACK)))
        self.assertIsNone(enc.banks[1]);self.assertFalse(enc.pending)

    def test_malformed_reference_crc_and_publication_are_atomic_and_failed_work_paid(self):
        enc,rx=self.pair();self.step(enc,rx,0);d=enc.prepare(self.image(80),1,promote=True)
        old=dict(rx.banks);fields=list(c.HEADER.unpack_from(d.packet))
        for index,value in ((8,b'x'*16),(9,b'x'*16),(6,0)):
            changed=fields.copy();changed[index]=value
            packet=c.seal(c.HEADER.pack(*changed)+d.packet[c.HEADER.size:-4])
            before=rx.reconstruction_write_bytes
            with self.assertRaises(ValueError):rx.receive(packet)
            self.assertEqual(rx.banks,old);self.assertIsNone(rx.active);self.assertEqual(rx.readers,0)
            if index==9:self.assertGreater(rx.reconstruction_write_bytes,before)
        with self.assertRaises(ValueError):rx.receive(d.packet[:-1]+bytes([d.packet[-1]^1]))
        self.assertEqual(rx.last_frame_id,0)

    def test_reorder_replay_and_foreign_completions_are_rejected(self):
        enc,rx=self.pair();self.step(enc,rx,0)
        one=enc.prepare(self.image(61),1);two=enc.prepare(self.image(62),2)
        _,_,ack=rx.receive(two.packet);enc.ack(ack)
        with self.assertRaises(ValueError):rx.receive(one.packet)
        enc.expire(1)
        with self.assertRaises(ValueError):rx.receive(two.packet)
        other=c.Receiver();key=c.Encoder().prepare(self.image(),0)
        task=other.begin(key.packet)
        with self.assertRaises(ValueError):rx.complete(task)
        other.abort(task)

    def test_profile_bounds_and_bounded_reader_capacity(self):
        for kwargs in (dict(window=0),dict(epoch=c.gm.NO_REF),dict(frame_cap=49153)):
            with self.assertRaises(ValueError):c.Encoder(**kwargs)
        enc,rx=self.pair();self.step(enc,rx,0)
        leases=[enc.acquire(0) for _ in range(3)]
        with self.assertRaises(ValueError):enc.acquire(0)
        for lease in leases:enc.release(lease)
        with self.assertRaises(ValueError):enc.release(leases[0])


if __name__=='__main__':unittest.main()
