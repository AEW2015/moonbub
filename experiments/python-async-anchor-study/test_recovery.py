"""Additional reset, unsent candidate and retirement-ACK recovery checks."""
import unittest
import numpy as np
from async_codec import Encoder,Receiver,parse


class RecoveryTests(unittest.TestCase):
    def image(self,v=50):return np.full((18,34,3),v,np.uint8)
    def install(self,e,r,capture=0,v=50):
        packet=e.prepare_key(self.image(v),capture)
        _,info=r.receive(packet);e.ack(info['tx'],info['epoch'])
        return packet,info['tx']

    def test_fresh_epoch_rejects_old_data_and_ack(self):
        e1,r1=Encoder(1),Receiver(1);old,_=self.install(e1,r1)
        e2,r2=Encoder(2),Receiver(2);new=e2.prepare_key(self.image(60),0)
        with self.assertRaises(ValueError):r2.receive(old)
        with self.assertRaises(ValueError):e2.ack(parse(new)['tx'],1)
        self.assertIsNone(e2.active);self.assertFalse(r2.anchors)
        _,info=r2.receive(new);self.assertTrue(e2.ack(info['tx'],2))

    def test_unsent_candidate_rejection_preserves_acked_anchor(self):
        e,r=Encoder(),Receiver();_,old=self.install(e,r)
        candidate=e.prepare_key(self.image(80),1)
        e.discard_unsent_key(parse(candidate)['tx'])
        self.assertEqual(e.active,old);self.assertEqual(set(e.anchors),{old})
        display=e.prepare_display(self.image(55),2)
        _,info=r.receive(display);self.assertTrue(info['display'])

    def test_retire_ack_loss_can_retry_without_third_anchor(self):
        e,r=Encoder(),Receiver();_,old=self.install(e,r)
        self.install(e,r,1,60)
        first=e.prepare_retire();_,info=r.receive(first)
        self.assertNotIn(old,r.anchors);self.assertIn(old,e.anchors)
        self.assertEqual(e.expire(info['tx']),'retire_retry')
        second=e.prepare_retire();_,again=r.receive(second)
        self.assertTrue(e.ack(again['tx'],1));self.assertNotIn(old,e.anchors)
        self.assertFalse(e.ack(info['tx'],1));self.assertTrue(e.can_key())


if __name__=='__main__':unittest.main()
