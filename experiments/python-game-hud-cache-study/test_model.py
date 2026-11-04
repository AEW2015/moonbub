import unittest
import numpy as np
import model as m

def rgb(seed=0):
    a=np.zeros((480,720,3),np.uint8)
    for i,(x,y,w,h) in enumerate(m.RECTANGLES):a[y:y+h,x:x+w]=np.array([12+seed+i,20+i,40+i],np.uint8)
    return a

def state(rx):
    return (rx.last_frame,rx.last_generation,rx.last_bodytag,tuple(None if b is None else(b['frame'],b['generation'],b['newtag'])for b in rx.banks),tuple(rx.readers))

class Cache(unittest.TestCase):
    def pair(self):return m.Sender(),m.Receiver()
    def deliver(self,s,r,a,f):
        p,i=s.prepare(a,f);ack=r.receive(p);s.accept_ack(ack)
        for q,e in zip(r.display['patches'],m.extract(a)):np.testing.assert_array_equal(q,e)
        return p,i,ack
    def test_static_reference_and_independent_banks(self):
        s,r=self.pair();_,a,_=self.deliver(s,r,rgb(),0);_,b,_=self.deliver(s,r,rgb(),1)
        self.assertLess(b['sidecar_bytes'],a['sidecar_bytes']);self.assertEqual(b['changed_words_vs_confirmed'],0)
        self.assertEqual(s.confirmed['newtag'],r.display['newtag'])
        self.assertFalse(any(q.flags.writeable for q in r.display['patches']))
    def test_packet_loss_does_not_issue_next(self):
        s,r=self.pair();p,_=s.prepare(rgb(),0)
        with self.assertRaises(ValueError):s.prepare(rgb(1),1)
        self.assertIsNone(s.confirmed);self.assertIsNone(r.display)
        s.accept_ack(r.receive(s.retry()));self.deliver(s,r,rgb(1),1)
    def test_ack_loss_exact_retry_no_new_generation(self):
        s,r=self.pair();p,_=s.prepare(rgb(),0);ack=r.receive(p);before=state(r)
        self.assertIsNone(s.confirmed);self.assertEqual(r.receive(s.retry()),ack);self.assertEqual(state(r),before)
        s.accept_ack(ack)
        with self.assertRaises(ValueError):s.accept_ack(ack)
    def test_corruption_and_wrong_reference_atomic(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);p,_=s.prepare(rgb(1),1);before=state(r)
        for q in(p[:-1]+bytes([p[-1]^1]),p[:-1],p+b'x'):
            with self.assertRaises(ValueError):r.receive(q)
            self.assertEqual(state(r),before)
        empty=m.Receiver()
        with self.assertRaises(ValueError):empty.receive(p)
        self.assertIsNone(empty.display)
        s.accept_ack(r.receive(p))
    def test_stale_and_reordered_packets(self):
        s,r=self.pair();p0,_,_=self.deliver(s,r,rgb(),0);self.deliver(s,r,rgb(1),2);before=state(r)
        with self.assertRaises(ValueError):r.receive(p0)
        with self.assertRaises(ValueError):s.prepare(rgb(),2)
        self.assertEqual(state(r),before)
    def test_held_lease_blocks_overwrite_and_reset(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);lease=r.acquire(0);self.deliver(s,r,rgb(1),1)
        p,_=s.prepare(rgb(2),2);before=state(r)
        with self.assertRaises(ValueError):r.receive(p)
        self.assertEqual(state(r),before)
        with self.assertRaises(ValueError):r.reset(2)
        r.release(lease);s.accept_ack(r.receive(p));self.assertEqual(r.last_frame,2)
    def test_unique_leases_duplicate_release_cannot_drain_other(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);a,b=r.acquire(0),r.acquire(0);self.assertNotEqual(a,b)
        r.release(a)
        with self.assertRaises(ValueError):r.release(a)
        self.assertEqual(r.readers,[1,0]);r.release(b);self.assertEqual(r.readers,[0,0])
    def test_bounded_lease_descriptors(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);leases=[r.acquire(0)for _ in range(8)]
        with self.assertRaises(ValueError):r.acquire(0)
        for a in leases:r.release(a)
    def test_lease_token_exhaustion_requires_epoch_reset(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);r._next_lease=m.INVALID-1
        lease=r.acquire(0);self.assertEqual(lease[-1],m.INVALID)
        r.release(lease)
        with self.assertRaises(ValueError):r.acquire(0)
        r.reset(2);self.assertEqual(r._next_lease,0)
    def test_decoded_tag_mismatch_is_atomic(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);p,_=s.prepare(rgb(1),1);before=state(r)
        fields=list(m.HEADER.unpack_from(p));fields[10]=bytes([fields[10][0]^1])+fields[10][1:]
        changed=m.seal(m.HEADER.pack(*fields)+p[m.HEADER.size:-4])
        with self.assertRaises(ValueError):r.receive(changed)
        self.assertEqual(state(r),before);s.accept_ack(r.receive(p))
    def test_fourth_patch_failure_does_not_publish_first_three(self):
        s,r=self.pair();self.deliver(s,r,rgb(),0);p,_=s.prepare(rgb(1),1);before=state(r)
        meta=m.parse(p);start=m.HEADER.size+sum(meta['sizes'][:3])
        body=bytearray(p[:-4]);body[start]^=1;changed=m.seal(bytes(body))
        with self.assertRaises(ValueError):r.receive(changed)
        self.assertEqual(state(r),before);s.accept_ack(r.receive(p))
    def test_reset_invalidates_old_data_and_ack(self):
        s,r=self.pair();p,_=s.prepare(rgb(),0);ack=r.receive(p);s.reset(2);r.reset(2);before=state(r)
        with self.assertRaises(ValueError):r.receive(p)
        p2,_=s.prepare(rgb(1),0)
        with self.assertRaises(ValueError):s.accept_ack(ack)
        self.assertEqual(state(r),before);s.accept_ack(r.receive(p2))
    def test_forged_ack_does_not_publish(self):
        s,r=self.pair();p,_=s.prepare(rgb(),0);ack=r.receive(p)
        f=list(m.ACK.unpack(ack[:-4]));f[-1]=bytes([f[-1][0]^1])+f[-1][1:]
        with self.assertRaises(ValueError):s.accept_ack(m.seal(m.ACK.pack(*f)))
        self.assertIsNone(s.confirmed);s.accept_ack(ack)
    def test_changed_duplicate_body_rejected(self):
        s,r=self.pair();p,_,_=self.deliver(s,r,rgb(),0);fields=list(m.HEADER.unpack_from(p));fields[9]=bytes([fields[9][0]^1])+fields[9][1:]
        # A different, CRC-correct body for the same identity cannot be accepted.
        changed=m.seal(m.HEADER.pack(*fields)+p[m.HEADER.size:-4]);before=state(r)
        with self.assertRaises(ValueError):r.receive(changed)
        self.assertEqual(state(r),before)
    def test_canvas_geometry_and_bad_ids(self):
        s,r=self.pair()
        for frame in(-1,True,0xffffffff):
            with self.assertRaises(ValueError):s.prepare(rgb(),frame)
        with self.assertRaises(ValueError):s.prepare(np.zeros((4,4,3),np.uint8),0)
        self.assertIsNone(s.pending)

if __name__=='__main__':unittest.main()
