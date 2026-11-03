import struct
import unittest
from dataclasses import replace
import chunks as c


class ChunkTests(unittest.TestCase):
    def test_reorder_identical_duplicate_and_decode_commit(self):
        data=bytes(range(256))*13;packets=c.datagrams(data,1,7);r=c.Reassembler()
        self.assertIsNone(r.feed(packets[-1],0));self.assertIsNone(r.feed(packets[-1],1))
        got=None
        for i,p in enumerate(packets[:-1]):got=r.feed(p,i+2)
        self.assertEqual(got.data,data);self.assertEqual(r.committed,-1)
        r.commit(got);self.assertEqual(r.committed,7);self.assertEqual(r.payload_bytes(),0)
        with self.assertRaises(ValueError):r.feed(packets[0],10)

    def test_two_slot_capacity_and_timeout_do_not_extend_for_duplicates(self):
        a=c.datagrams(bytes(2048),1,1);b=c.datagrams(bytes(2048),1,2);d=c.datagrams(bytes(2048),1,3)
        r=c.Reassembler(timeout_ms=10)
        r.feed(a[0],0);r.feed(b[0],1);self.assertEqual(r.payload_bytes(),4096)
        with self.assertRaises(ValueError):r.feed(d[0],2)
        r.feed(a[0],9);self.assertEqual(r.expire(10),[1]);self.assertEqual(r.expire(11),[2])
        self.assertEqual(r.payload_bytes(),0);self.assertLessEqual(r.peak_slots,2)

    def test_conflicting_duplicate_and_corrupt_complete_never_return(self):
        a=c.datagrams(bytes(1500),1,2);r=c.Reassembler();r.feed(a[0],0)
        bad=a[0][:-1]+b'\x01'
        with self.assertRaises(ValueError):r.feed(bad,1)
        self.assertFalse(r.pending);r.feed(a[0],2)
        with self.assertRaises(ValueError):r.feed(a[1][:-1]+b'\x01',3)
        self.assertEqual(r.committed,-1);self.assertFalse(r.pending)

    def test_header_length_session_and_metadata_bounds(self):
        packet=c.datagrams(bytes(1400),1,1)[0]
        for index,value in ((0,b'BAD!'),(1,2),(2,2),(4,49153),(5,2),(6,3),(7,1023)):
            fields=list(c.HEADER.unpack_from(packet));fields[index]=value
            bad=c.HEADER.pack(*fields)+packet[c.HEADER.size:]
            r=c.Reassembler()
            with self.assertRaises(ValueError):r.feed(bad,0)
            self.assertEqual(r.payload_bytes(),0)
        r=c.Reassembler();r.feed(packet,0)
        fields=list(c.HEADER.unpack_from(packet));fields[-1]^=1
        with self.assertRaises(ValueError):r.feed(c.HEADER.pack(*fields)+packet[c.HEADER.size:],1)
        self.assertFalse(r.pending)

    def test_later_decode_commit_reclaims_older_partial_and_reset_epoch(self):
        r=c.Reassembler();r.feed(c.datagrams(bytes(2000),1,2)[0],0)
        done=r.feed(c.datagrams(b'frame',1,3)[0],1)
        self.assertEqual(r.commit(done),[2]);self.assertEqual(r.payload_bytes(),0)
        r.reset(2)
        with self.assertRaises(ValueError):r.commit(done)
        with self.assertRaises(ValueError):r.feed(c.datagrams(b'old',1,4)[0],2)
        self.assertIsNotNone(r.feed(c.datagrams(b'new',2,0)[0],3))

    def test_delivered_slots_stay_pinned_until_read_finish(self):
        r=c.Reassembler(timeout_ms=10)
        a=r.feed(c.datagrams(b'older',1,1)[0],0)
        b=r.feed(c.datagrams(b'newer',1,2)[0],1)
        self.assertEqual(r.payload_bytes(),10)
        self.assertEqual(r.expire(20),[])
        with self.assertRaises(ValueError):r.feed(c.datagrams(b'third',1,3)[0],21)
        with self.assertRaises(ValueError):r.reset(2)
        r.commit(b)
        self.assertIn(1,r.pending)
        with self.assertRaises(ValueError):r.commit(a)
        r.reject(a);self.assertEqual(r.payload_bytes(),0)
        r.reset(2)

    def test_forged_or_cross_instance_completion_cannot_release_credit(self):
        r=c.Reassembler();other=c.Reassembler()
        packet=c.datagrams(b'one',1,1)[0]
        done=r.feed(packet,0);foreign=other.feed(packet,0)
        for forged in (replace(done),foreign,c.Complete(1,1,b'one')):
            with self.assertRaises(ValueError):r.commit(forged)
        self.assertEqual(r.payload_bytes(),3)
        r.commit(done)
        with self.assertRaises(ValueError):r.commit(done)

    def test_full_two_slot_payload_bound_before_decode(self):
        r=c.Reassembler()
        for frame in (0,1):
            r.feed(c.datagrams(bytes(49152),1,frame)[0],frame)
        self.assertEqual(r.payload_bytes(),98304)
        self.assertEqual(r.peak_payload_bytes,98304)
        with self.assertRaises(ValueError):r.feed(c.datagrams(b'third',1,2)[0],2)
        self.assertEqual(sorted(r.expire(151)),[0,1])
        self.assertEqual(r.payload_bytes(),0)

    def test_payload_and_configuration_bounds(self):
        with self.assertRaises(ValueError):c.datagrams(bytes(49153),1,0)
        for kwargs in ({'slots':3},{'max_frame':49153},{'timeout_ms':0}):
            with self.assertRaises(ValueError):c.Reassembler(**kwargs)
        r=c.Reassembler();r.expire(1)
        with self.assertRaises(ValueError):r.expire(0)
        self.assertEqual(sum(len(x) for x in c.datagrams(bytes(49152),1,0)),49152+48*c.HEADER.size)


if __name__=='__main__':unittest.main()
