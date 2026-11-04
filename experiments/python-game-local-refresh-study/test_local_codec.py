import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest
import numpy as np
import local_codec as u

spec=importlib.util.spec_from_file_location('frozen_ar02',Path(__file__).resolve().parents[1]/'python-game-unified-codec-study/unified_codec.py')
legacy=importlib.util.module_from_spec(spec);import sys;sys.modules[spec.name]=legacy;spec.loader.exec_module(legacy)

class LocalTests(unittest.TestCase):
    def image(self,i=70):return np.full((16,32,3),i,np.uint8)
    def step(self,e,r,i,**kw):
        d=e.prepare(self.image(70+i),i,**kw);self.assertTrue(d.accepted)
        rgb,info,ack=r.receive(d.packet)
        self.assertEqual(e.expected_hash(i),hashlib.sha256(rgb.tobytes()).hexdigest());self.assertTrue(e.ack(ack))
        for b in (0,1):
            self.assertEqual(e.banks[b] is None,r.banks[b] is None)
            if e.banks[b] is not None:self.assertEqual(e.banks[b].tag,r.banks[b].tag)
        return d,ack
    def setup_pair(self):
        e,r=u.Encoder(mode='gm'),u.Receiver();self.step(e,r,0);self.step(e,r,1,promote=True);return e,r
    def test_initial_gm_syntax_has_same_reconstruction_as_ar02(self):
        pairs=[(u.Encoder(mode='gm'),u.Receiver()),(legacy.Encoder(mode='gm'),legacy.Receiver())]
        for i in range(5):
            outputs=[]
            for e,r in pairs:
                d=e.prepare(self.image(70+i),i,promote=i==2)
                rgb,_,ack=r.receive(d.packet);e.ack(ack);outputs.append(rgb)
                self.assertEqual(d.info['analyze_calls'],1);self.assertEqual(d.info['forward_calls'],3)
            np.testing.assert_array_equal(outputs[0],outputs[1])
    def test_key0_refresh_preserves_bank1_and_overlaps_its_consumers(self):
        e,r=self.setup_pair();old=e.banks[1]
        user=e.prepare(self.image(72),2)
        self.assertEqual(user.reference_bank,1);self.assertTrue(e.can_prepare(True))
        key=e.prepare(self.image(73),3,force_key=True)
        self.assertIsNone(e.banks[0]);self.assertIs(e.banks[1],old)
        self.assertTrue(e.can_prepare());other=e.prepare(self.image(74),4)
        self.assertEqual(other.reference_bank,1)
        for d in (user,key,other):
            _,_,ack=r.receive(d.packet);self.assertTrue(e.ack(ack))
        self.assertIs(e.banks[1],old);self.assertEqual(r.banks[1].tag,old.tag)
        self.assertEqual(e.banks[0].frame_id,3)
    def test_default_uses_newest_confirmed_key_after_refresh_ack(self):
        e,r=self.setup_pair();key,_=self.step(e,r,2,force_key=True)
        p=e.prepare(self.image(73),3)
        self.assertEqual((p.reference_bank,p.reference_id),(0,2))
    def test_only_destination0_users_block_refresh(self):
        e,r=self.setup_pair();lease1=e.acquire(1)
        self.assertTrue(e.can_prepare(True));e.release(lease1)
        lease0=e.acquire(0);self.assertFalse(e.can_prepare(True));e.release(lease0)
        user=e.prepare(self.image(72),2,reference_bank=0);self.assertFalse(e.can_prepare(True))
        _,_,ack=r.receive(user.packet);e.ack(ack);self.assertTrue(e.can_prepare(True))
    def test_receiver_otherbank_lease_survives_key0_and_writerblocks_only_zero(self):
        e,r=self.setup_pair();reader=r.acquire(1);old=reader.bank
        key=e.prepare(self.image(72),2,force_key=True);task=r.begin(key.packet)
        self.assertEqual(r.readers,1)
        other=r.acquire(1)
        with self.assertRaises(ValueError):r.acquire(0)
        _,_,ack=r.complete(task);e.ack(ack)
        self.assertIs(r.banks[1],old);r.release(other);r.release(reader)
    def test_lost_key_ack_invalidates_only_zero_and_correct_old_ack_cannot_resurrect(self):
        e,r=self.setup_pair();old=e.banks[1];key=e.prepare(self.image(72),2,force_key=True)
        _,_,ack=r.receive(key.packet);self.assertTrue(e.expire(2))
        self.assertFalse(e.ack(ack));self.assertIsNone(e.banks[0]);self.assertIs(e.banks[1],old)
        p=e.prepare(self.image(73),3);self.assertFalse(p.key);self.assertEqual(p.reference_bank,1)
        _,_,pa=r.receive(p.packet);self.assertTrue(e.ack(pa))
        self.step(e,r,4,force_key=True)
    def test_wrong_feedback_crc_tag_and_legacy_versions_reject_atomically(self):
        e,r=self.setup_pair();d=e.prepare(self.image(72),2,force_key=True);_,_,ack=r.receive(d.packet)
        values=list(u.FEEDBACK.unpack_from(ack));values[8]=b'X'*16
        bad=u.seal(u.FEEDBACK.pack(*values));before=dict(e.banks)
        with self.assertRaises(ValueError):e.ack(bad)
        self.assertEqual(before,e.banks);self.assertIn(2,e.pending);self.assertTrue(e.ack(ack))
        with self.assertRaises(ValueError):legacy.identity(d.packet)
        ld=legacy.Encoder(mode='gm').prepare(self.image(),0)
        with self.assertRaises(ValueError):u.identity(ld.packet)
        with self.assertRaises(ValueError):legacy.parse_feedback(ack)
    def test_cap_and_bad_ui_never_reserve_key_bank(self):
        e,r=self.setup_pair();old=dict(e.banks);e.frame_cap=128
        noise=np.random.default_rng(1701).integers(0,256,(16,32,3),dtype=np.uint8)
        d=e.prepare(noise,2,force_key=True);self.assertFalse(d.accepted);self.assertEqual(old,e.banks);self.assertFalse(e.pending)
    def test_admitted_geometry_survives_bank_expiry_and_rejection_does_not_lock(self):
        e=u.Encoder(mode='gm');d=e.prepare(self.image(),0);e.expire(0)
        with self.assertRaises(ValueError):e.prepare(np.full((18,32,3),70,np.uint8),1,force_key=True)
        tiny=u.Encoder(mode='gm',frame_cap=128)
        d=tiny.prepare(np.random.default_rng(1710).integers(0,256,(16,32,3),dtype=np.uint8),0)
        self.assertFalse(d.accepted);self.assertIsNone(tiny._geometry)
    def test_geometry_requires_fresh_epoch_and_aborted_key_does_not_publish(self):
        e,r=self.setup_pair()
        with self.assertRaises(ValueError):e.prepare(np.full((18,32,3),70,np.uint8),2,force_key=True)
        d=e.prepare(self.image(72),2,force_key=True);old=dict(r.banks);task=r.begin(d.packet);r.abort(task)
        self.assertEqual(old,r.banks);self.assertEqual(r.readers,0)
        with self.assertRaises(ValueError):r.complete(task)
        _,_,ack=r.receive(d.packet);self.assertTrue(e.ack(ack))

if __name__=='__main__':unittest.main()
