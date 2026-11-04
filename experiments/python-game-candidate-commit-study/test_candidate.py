import dataclasses
import hashlib
import unittest
from unittest.mock import patch
import numpy as np
import candidate_codec as c
from ui_plugin import PatchSelector

class CandidateTests(unittest.TestCase):
    def image(self,i=70,w=64,h=48):return np.full((h,w,3),i,np.uint8)
    def semantic(self,e):
        return (dict(e.banks),dict(e.pending),e.last_issued,e._generation,e._geometry)
    def finish(self,e,r,decision):
        rgb,info,ack=r.receive(decision.packet)
        self.assertEqual(e.expected_hash(decision.frame_id),hashlib.sha256(rgb.tobytes()).hexdigest())
        self.assertTrue(e.ack(ack));return rgb,info,ack
    def initialized(self):
        e,r=c.Encoder(mode='gm'),c.Receiver();self.finish(e,r,e.prepare(self.image(),0));return e,r
    def test_build_discard_key_does_not_consume_or_reserve(self):
        e=c.Encoder(mode='gm');before=self.semantic(e)
        x=e.build(self.image(),0)
        self.assertTrue(x.accepted);self.assertEqual(before,self.semantic(e));self.assertIs(e.active_candidate,x)
        self.assertFalse(e.can_build())
        with self.assertRaises(ValueError):e.build(self.image(),1)
        self.assertTrue(e.discard(x));self.assertEqual(before,self.semantic(e));self.assertEqual(e.readers,0)
        x=e.build(self.image(),0);self.assertTrue(e.commit(x).accepted);self.assertEqual(e.last_issued,0)
    def test_cap_rejection_paid_no_lease_and_same_id_retry(self):
        e,r=self.initialized();e.frame_cap=128;before=self.semantic(e)
        x=e.build(np.random.default_rng(1801).integers(0,256,(48,64,3),dtype=np.uint8),1)
        self.assertFalse(x.accepted);self.assertGreater(x.service_ms,0);self.assertEqual(e.readers,0)
        self.assertEqual(before,self.semantic(e))
        with self.assertRaises(ValueError):e.commit(x)
        e.discard(x);e.frame_cap=49152;self.finish(e,r,e.prepare(self.image(71),1))
    def test_candidate_pins_source_until_commit_or_discard(self):
        e,r=self.initialized();x=e.build(self.image(71),1)
        self.assertEqual(e.readers,1);self.assertIs(x.source_lease.bank,e.banks[0])
        self.assertFalse(e._writable(0));e.discard(x);self.assertEqual(e.readers,0)
        x=e.build(self.image(71),1,promote=True);self.assertEqual(x.reference_bank,0)
        d=e.commit(x);self.assertEqual(e.readers,0);self.finish(e,r,d)
    def test_same_bank_promotion_ignores_only_its_own_read_pin(self):
        e,r=self.initialized();self.finish(e,r,e.prepare(self.image(71),1,promote=True))
        x=e.build(self.image(72),2,promote=True);self.assertEqual((x.reference_bank,x.destination_bank),(1,1))
        other=e.acquire(1);before=self.semantic(e)
        with self.assertRaises(ValueError):e.commit(x)
        self.assertEqual(before,self.semantic(e));e.release(other);self.finish(e,r,e.commit(x))
    def test_unrelated_ack_and_expiry_do_not_stale_candidate(self):
        e,r=self.initialized();pub=e.prepare(self.image(71),1,promote=True)
        # Bank1 reserved; a candidate using confirmed0 can coexist with ACK1.
        x=e.build(self.image(72),2,reference_bank=0);gen=e._generation
        _,_,ack=r.receive(pub.packet);e.ack(ack);self.assertGreater(e._generation,gen)
        self.finish(e,r,e.commit(x))
        ordinary=e.prepare(self.image(73),3);y=e.build(self.image(74),4)
        e.expire(3);self.finish(e,r,e.commit(y))
    def test_destination_read_acquired_after_build_blocks_key_commit(self):
        e,r=self.initialized();x=e.build(self.image(71),1,force_key=True)
        old=e.banks[0];lease=e.acquire(0);before=self.semantic(e)
        with self.assertRaises(ValueError):e.commit(x)
        self.assertEqual(before,self.semantic(e));self.assertIs(e.banks[0],old)
        e.release(lease);e.discard(x);self.assertIs(e.banks[0],old)
    def test_wrong_owner_double_use_and_public_tamper_fail_atomic(self):
        e,r=self.initialized();other=c.Encoder(mode='gm');x=e.build(self.image(71),1)
        with self.assertRaises(ValueError):other.commit(x)
        with self.assertRaises(ValueError):other.discard(x)
        with self.assertRaises(dataclasses.FrozenInstanceError):x.frame_id=9
        with self.assertRaises(TypeError):x.info['bytes']=1
        forged=dataclasses.replace(x,frame_id=9)
        with self.assertRaises(ValueError):e.commit(forged)
        before=self.semantic(e);object.__setattr__(x,'frame_id',9)
        with self.assertRaises(ValueError):e.commit(x)
        self.assertEqual(before,self.semantic(e));e.discard(x);self.assertEqual(e.readers,0)
        with self.assertRaises(ValueError):e.discard(x)
        y=e.build(self.image(71),1);d=e.commit(y)
        with self.assertRaises(ValueError):e.commit(y)
        self.finish(e,r,d)
    def test_mutated_service_metadata_and_source_lease_fail_atomic(self):
        e,r=self.initialized();x=e.build(self.image(71),1);before=self.semantic(e)
        object.__setattr__(x,'service_ms',0.)
        with self.assertRaises(ValueError):e.commit(x)
        self.assertEqual(before,self.semantic(e));e.discard(x)
        x=e.build(self.image(71),1);e.release(x.source_lease)
        with self.assertRaises(ValueError):e.commit(x)
        e.discard(x);self.assertEqual(e.readers,0)
    def test_changed_configuration_and_manual_stale_bank_reject(self):
        e,r=self.initialized();x=e.build(self.image(71),1);e.frame_cap=40000
        with self.assertRaises(ValueError):e.commit(x)
        e.discard(x);e.frame_cap=49152
        x=e.build(self.image(71),1);old=e.banks[0];e.banks[0]=c.Bank(old.frame_id,old.tag,old.planes)
        with self.assertRaises(ValueError):e.commit(x)
        e.discard(x);e.banks[0]=old
    def test_build_exception_releases_source_and_leaves_state(self):
        e,r=self.initialized();before=self.semantic(e)
        with patch.object(c.gm.Encoder,'analyze',side_effect=ValueError('injected')):
            with self.assertRaises(ValueError):e.build(self.image(71),1)
        self.assertEqual(before,self.semantic(e));self.assertEqual(e.readers,0);self.assertIsNone(e.active_candidate)
    def test_callback_reentry_and_reader_capacity_failure_unwind(self):
        e,r=self.initialized();before=self.semantic(e)
        class Reentry:
            def select(callback,rgb,budget):return e.build(rgb,99)
        e.patch_builder=Reentry()
        with self.assertRaises(ValueError):e.build(self.image(71),1)
        self.assertEqual(before,self.semantic(e));self.assertEqual(e.readers,0);self.assertFalse(e._building)
        e.patch_builder=None;leases=[e.acquire(0) for _ in range(e.max_readers)]
        with self.assertRaises(ValueError):e.build(self.image(71),1)
        self.assertFalse(e._building);self.assertIsNone(e.active_candidate)
        for lease in leases:e.release(lease)
    def test_full720_wire_matches_frozen_prepare_gm_exact_ui_and_lifecycle(self):
        yy,xx=np.indices((480,720));rgb=np.stack(((xx//8)%180+20,(yy//8)%180+20,np.full_like(xx,70)),axis=-1).astype(np.uint8)
        for mode in ('gm','exact'):
            controls=[(c.Encoder(mode=mode,patch_builder=PatchSelector()),c.Receiver()),
                      (c.frozen.Encoder(mode=mode,patch_builder=PatchSelector()),c.frozen.Receiver())]
            for i in range(5):
                outputs=[];packets=[]
                for e,r in controls:
                    if isinstance(e,c.Encoder):
                        x=e.build(rgb,i,promote=i==1,force_key=i==3);d=e.commit(x)
                    else:d=e.prepare(rgb,i,promote=i==1,force_key=i==3)
                    packets.append(d.packet);out,info,_=self.finish(e,r,d);outputs.append(out)
                    self.assertEqual(info['selected_pixels'],21120)
                self.assertEqual(packets[0],packets[1]);np.testing.assert_array_equal(*outputs)
    def test_discard_then_banklocal_refresh_and_geometry_lock(self):
        e,r=self.initialized();self.finish(e,r,e.prepare(self.image(71),1,promote=True));old=e.banks[1]
        key=e.build(self.image(72),2,force_key=True);e.discard(key)
        self.assertEqual(e.last_issued,1);self.assertIs(e.banks[1],old)
        key=e.build(self.image(72),2,force_key=True);d=e.commit(key);self.assertIs(e.banks[1],old)
        self.finish(e,r,d)
        with self.assertRaises(ValueError):e.build(self.image(w=66),3)

if __name__=='__main__':unittest.main()
