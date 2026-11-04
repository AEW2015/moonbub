import unittest
from unittest.mock import patch
import numpy as np
import model
C=model.codec
class Tests(unittest.TestCase):
    def policy(self,**kw):return model.Policy(rectangles=((0,0,16,8),),base_regions=((0,0,16,8),),**kw)
    def rgb(self):return np.random.default_rng(10).integers(0,256,(16,32,3),dtype=np.uint8)
    def test_success_has_complete_original_words_and_exact_reference_ack(self):
        p=self.policy();rx=C.Receiver();a=self.rgb();x=p.prepare(a,0);self.assertTrue(x.accepted)
        d=p.commit(x);rgb,info,ack=rx.receive(d.packet);self.assertTrue(p.encoder.ack(ack))
        np.testing.assert_array_equal(C.corpus.rgb565(a[:8,:16]),C.corpus.rgb565(rgb[:8,:16]))
        self.assertEqual(info['selected_pixels'],128);self.assertFalse(p.encoder.readers)
    def test_impossible_ui_reservation_skips_base_and_state(self):
        p=self.policy(frame_cap=128);prior=model.state(p.encoder);x=p.prepare(self.rgb(),0)
        self.assertFalse(x.accepted);self.assertEqual(x.info['reason'],'mandatory_ui_exceeds_complete_cap')
        self.assertFalse(x.info['attempts']);self.assertEqual(model.state(p.encoder),prior);self.assertFalse(p.encoder.readers)
    def test_losing_actual_base_attempts_are_paid_and_discarded(self):
        p=self.policy(frame_cap=700);prior=model.state(p.encoder);x=p.prepare(self.rgb(),0)
        self.assertEqual(len(x.info['attempts']),4);self.assertTrue(x.accepted)
        self.assertEqual(sum(not a['accepted'] for a in x.info['attempts']),3)
        for a in x.info['attempts']:
            self.assertGreater(a['build_ms'],0);self.assertEqual(a['forward_calls'],3)
            if not a['accepted']:self.assertGreater(a['discard_ms'],0)
        if x.accepted:p.discard(x)
        self.assertEqual(model.state(p.encoder),prior);self.assertFalse(p.encoder.readers)
    def test_all_maps_exhausted_discard_without_burning_id_then_reuse(self):
        p=self.policy(frame_cap=500);prior=model.state(p.encoder);a=self.rgb();x=p.prepare(a,0)
        self.assertFalse(x.accepted);self.assertEqual(len(x.info['attempts']),4)
        self.assertTrue(all(not v['accepted'] and v['discard_ms']>0 for v in x.info['attempts']))
        self.assertEqual(model.state(p.encoder),prior);self.assertIsNone(p.encoder.active_candidate);self.assertFalse(p.encoder.readers)
        p.encoder.frame_cap=1000;x=p.prepare(a,0);self.assertTrue(x.accepted);p.discard(x)
        self.assertEqual(model.state(p.encoder),prior)
    def test_external_lease_survives_rejected_retry_then_commit_or_discard(self):
        for action in ('commit','discard'):
            with self.subTest(action=action):
                p=self.policy();rx=C.Receiver();x=p.prepare(np.full((16,32,3),70,np.uint8),0)
                d=p.commit(x);_,_,ack=rx.receive(d.packet);p.encoder.ack(ack)
                p.encoder.frame_cap=700;lease=p.encoder.acquire(0);bank=lease.bank;prior=model.state(p.encoder)
                x=p.prepare(self.rgb(),1)
                self.assertTrue(x.accepted);self.assertEqual(len(x.info['attempts']),4)
                self.assertEqual(sum(not a['accepted'] for a in x.info['attempts']),3)
                self.assertEqual(x.info['readers_before'],1);self.assertEqual(x.info['readers_after_builds'],2)
                self.assertIn(lease,p.encoder._leases);self.assertIs(p.encoder.banks[0],bank)
                if action=='commit':
                    d=p.commit(x);_,_,ack=rx.receive(d.packet);self.assertTrue(p.encoder.ack(ack))
                else:
                    p.discard(x);self.assertEqual(model.state(p.encoder),prior)
                self.assertEqual(p.encoder.readers,1);self.assertIn(lease,p.encoder._leases);self.assertIs(p.encoder.banks[0],bank)
                p.encoder.release(lease);self.assertFalse(p.encoder.readers)
    def test_unresolved_candidate_forbids_next_source(self):
        p=self.policy();x=p.prepare(self.rgb(),0)
        with self.assertRaises(ValueError):p.prepare(self.rgb(),1)
        p.discard(x);self.assertFalse(p.encoder.readers)
    def test_build_exception_unwinds_candidate_and_source_lease(self):
        p=self.policy();rx=C.Receiver();x=p.prepare(self.rgb(),0);d=p.commit(x);_,_,ack=rx.receive(d.packet);p.encoder.ack(ack)
        prior=model.state(p.encoder);lease=p.encoder.acquire(0)
        with patch.object(p.patches,'select',side_effect=ValueError('injected callback')):
            with self.assertRaises(ValueError):p.prepare(self.rgb(),1)
        self.assertEqual(p.encoder.readers,1);self.assertIn(lease,p.encoder._leases)
        self.assertIsNone(p.encoder.active_candidate);self.assertEqual(model.state(p.encoder),prior)
        p.encoder.release(lease);self.assertFalse(p.encoder.readers)
    def test_stale_candidate_commit_fails_and_explicit_discard_cleans(self):
        p=self.policy();rx=C.Receiver();x=p.prepare(self.rgb(),0);d=p.commit(x);_,_,ack=rx.receive(d.packet);p.encoder.ack(ack)
        x=p.prepare(self.rgb(),1);self.assertEqual(p.encoder.readers,1);p.encoder.frame_cap=1000
        with self.assertRaises(ValueError):p.commit(x)
        p.discard(x);self.assertFalse(p.encoder.readers)
    def test_patch_source_validation_rejects_mutated_preparation(self):
        p=self.policy();a=self.rgb();p.patches.prepare(a);b=a.copy();b[0,0]^=255
        with self.assertRaises(ValueError):p.encoder.build(b,0)
        self.assertIsNone(p.encoder.active_candidate);self.assertFalse(p.encoder.readers)
    def test_declared_profile_bounds(self):
        for profiles in ((),((8,64),),((8,16),)*5):
            with self.assertRaises(ValueError):self.policy(profiles=profiles)
if __name__=='__main__':unittest.main()
