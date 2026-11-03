import unittest
import numpy as np
from async_codec import Encoder,Receiver,parse,pack,KEY,DISPLAY,RETIRE,NONE


class AsyncCodecTests(unittest.TestCase):
    def image(self,v=50):return np.full((18,34,3),v,np.uint8)

    def install(self,e,r,capture=0,v=50):
        packet=e.prepare_key(self.image(v),capture)
        rgb,info=r.receive(packet);e.ack(info['tx'],info['epoch'])
        return info['tx']

    def test_reference_only_key_cannot_regress_display(self):
        e,r=Encoder(),Receiver();old=self.install(e,r)
        candidate=e.prepare_key(self.image(60),1)
        p=e.prepare_display(self.image(52),5)
        _,info=r.receive(p);e.mark_drained(info['tx']);e.ack(info['tx'],info['epoch'])
        rgb,info=r.receive(candidate)
        self.assertFalse(info['display']);self.assertEqual(r.last_capture,5)
        e.ack(info['tx'],info['epoch']);self.assertNotEqual(e.active,old)

    def test_old_anchor_retirement_requires_ack_and_read_drain(self):
        e,r=Encoder(),Receiver();old=self.install(e,r)
        p=e.prepare_display(self.image(51),1);pid=parse(p)['tx']
        k=e.prepare_key(self.image(52),2);_,ki=r.receive(k);e.ack(ki['tx'],ki['epoch'])
        self.assertFalse(e.can_retire())
        e.expire(pid);self.assertFalse(e.can_retire())
        r.receive(p);e.mark_drained(pid);self.assertTrue(e.can_retire())
        retire=e.prepare_retire();_,ri=r.receive(retire);e.ack(ri['tx'],ri['epoch'])
        self.assertNotIn(old,e.anchors);self.assertNotIn(old,r.anchors)

    def test_lost_key_ack_exact_retry_and_bounded_cache(self):
        e,r=Encoder(),Receiver();self.install(e,r)
        k=e.prepare_key(self.image(80),3);_,info=r.receive(k)
        self.assertEqual(e.expire(info['tx']),'retry_key')
        retry=e.retry_key();self.assertEqual(retry,k)
        rgb,again=r.receive(retry);self.assertIsNone(rgb);self.assertTrue(again['duplicate'])
        e.ack(again['tx'],again['epoch'])
        self.assertEqual(len(e.anchors),2);self.assertEqual(len(r.anchors),2)
        with self.assertRaises(ValueError):e.prepare_key(self.image(),4)

    def test_p_loss_does_not_poison_anchor_and_credit_bound(self):
        e,r=Encoder(),Receiver();self.install(e,r)
        lost=e.prepare_display(self.image(52),1);a=parse(lost)['tx']
        good=e.prepare_display(self.image(53),2)
        with self.assertRaises(ValueError):e.prepare_display(self.image(54),3)
        e.expire(a);e.mark_drained(a)
        rgb,info=r.receive(good);self.assertTrue(info['display'])
        e.mark_drained(info['tx']);e.ack(info['tx'],info['epoch'])
        nextp=e.prepare_display(self.image(54),3);r.receive(nextp)
        self.assertEqual(r.last_capture,3)

    def test_wrong_epoch_corruption_retired_key_and_duplicate_ack(self):
        e,r=Encoder(),Receiver();old=self.install(e,r)
        p=e.prepare_display(self.image(52),1);tx=parse(p)['tx']
        with self.assertRaises(ValueError):e.ack(tx,2)
        with self.assertRaises(ValueError):r.receive(p[:-1]+bytes([p[-1]^1]))
        self.assertEqual(r.last_capture,-1)
        rgb,info=r.receive(p);e.mark_drained(tx);self.assertTrue(e.ack(tx,1));self.assertFalse(e.ack(tx,1))
        k=e.prepare_key(self.image(60),2);_,info=r.receive(k);e.ack(info['tx'],1)
        retire=e.prepare_retire();_,info=r.receive(retire);e.ack(info['tx'],1)
        with self.assertRaises(ValueError):r.receive(p)

    def test_forged_retirement_cannot_remove_newer_anchor(self):
        e,r=Encoder(),Receiver();old=self.install(e,r)
        p=e.prepare_key(self.image(60),1);_,info=r.receive(p);new=info['tx'];e.ack(new,1)
        bad=pack(RETIRE,1,new+1,new,NONE,old)
        before=set(r.anchors)
        with self.assertRaises(ValueError):r.receive(bad)
        self.assertEqual(set(r.anchors),before)

    def test_ack_alone_does_not_release_physical_reader(self):
        e,r=Encoder(),Receiver();self.install(e,r)
        p=e.prepare_display(self.image(55),1);pid=parse(p)['tx']
        k=e.prepare_key(self.image(60),2);_,info=r.receive(k);e.ack(info['tx'],1)
        e.ack(pid,1)
        self.assertFalse(e.can_retire())
        e.mark_drained(pid);self.assertTrue(e.can_retire())


if __name__=='__main__':unittest.main()
