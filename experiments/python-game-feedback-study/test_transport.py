from dataclasses import replace
import struct
import unittest
import zlib
import transport as t


class FeedbackTransportTests(unittest.TestCase):
    def test_delivered_pin_survives_conflicting_metadata_and_duplicate(self):
        payload=bytes(range(256))*5;r=t.Reassembler();wire=t.datagrams(payload,1,3)
        done=None
        for i,p in enumerate(wire):done=r.feed(p,i)
        self.assertIsNotNone(done);self.assertEqual(r.payload_bytes(),len(payload))
        fields=list(t.HEADER.unpack_from(wire[0]));fields[-1]^=1
        bad=t.HEADER.pack(*fields)+wire[0][t.HEADER.size:]
        for error_packet in (bad,wire[0][:-1]+bytes([wire[0][-1]^1])):
            with self.assertRaises(ValueError):r.feed(error_packet,10)
            self.assertIs(r.pending[3]['complete'],done)
            self.assertEqual(r.payload_bytes(),len(payload))
            with self.assertRaises(ValueError):r.reset(2)
        r.commit(done);self.assertEqual(r.payload_bytes(),0)

    def test_undelivered_conflict_releases_only_partial_buffer(self):
        wire=t.datagrams(bytes(3000),1,0);r=t.Reassembler();r.feed(wire[0],0)
        with self.assertRaises(ValueError):r.feed(wire[0][:-1]+b'\x01',1)
        self.assertFalse(r.pending)

    def test_content_specific_tag_does_not_use_constant_inner_crc_residue(self):
        frames=[]
        for body in (b'GM01 one body',b'GM01 another body'):
            frames.append(body+struct.pack('<I',zlib.crc32(body)))
        self.assertEqual(zlib.crc32(frames[0]),zlib.crc32(frames[1]))
        self.assertNotEqual(t.content_crc(frames[0]),t.content_crc(frames[1]))
        for data in frames:
            r=t.Reassembler();done=r.feed(t.datagrams(data,1,0)[0],0)
            self.assertEqual(done.frame_crc,t.content_crc(data));r.commit(done)

    def test_feedback_crc_identity_tag_and_status(self):
        for status,reason in ((t.ACK,0),(t.NACK,1),(t.NACK,7)):
            wire=t.feedback_datagram(1,2,status,12345,reason)
            self.assertEqual(len(wire),24)
            f=t.parse_feedback(wire)
            self.assertTrue(t.matches_feedback(f,1,2,12345))
            for expected in ((2,2,12345),(1,3,12345),(1,2,54321)):
                self.assertFalse(t.matches_feedback(f,*expected))
            with self.assertRaises(ValueError):t.parse_feedback(wire[:-1]+bytes([wire[-1]^1]))
        for args in ((1,2,t.ACK,3,1),(1,2,t.NACK,3,0),(1,2,2,3,0),(True,2,t.ACK,3,0)):
            with self.assertRaises(ValueError):t.feedback_datagram(*args)

    def test_reorder_duplicate_body_tag_and_full_crc_mismatch(self):
        data=bytes(range(256))*20;wire=t.datagrams(data,1,1);r=t.Reassembler();done=None
        self.assertIsNone(r.feed(wire[-1],0));self.assertIsNone(r.feed(wire[-1],1))
        for i,p in enumerate(wire[:-1]):done=r.feed(p,i+2)
        self.assertEqual(done.data,data);self.assertEqual(done.frame_crc,t.content_crc(data));r.reject(done)
        r=t.Reassembler()
        for i,p in enumerate(wire):
            altered=p if i<len(wire)-1 else p[:-1]+bytes([p[-1]^1])
            if i==len(wire)-1:
                with self.assertRaises(ValueError):r.feed(altered,i)
            else:r.feed(altered,i)
        self.assertFalse(r.pending)

    def test_two_full_slots_are_pinned_timeout_and_stale_feedback(self):
        r=t.Reassembler(timeout_ms=5)
        for frame in (1,2):r.feed(t.datagrams(bytes(49152),1,frame)[0],frame)
        self.assertEqual(r.payload_bytes(),98304)
        with self.assertRaises(ValueError):r.feed(t.datagrams(b'other',1,3)[0],3)
        self.assertEqual(sorted(r.expire(7)),[1,2]);self.assertEqual(r.payload_bytes(),0)
        r.reset(2)
        with self.assertRaises(ValueError):r.feed(t.datagrams(b'old',1,0)[0],8)
        done=r.feed(t.datagrams(b'new-data',2,0)[0],9)
        with self.assertRaises(ValueError):r.commit(replace(done))
        r.commit(done)
        with self.assertRaises(ValueError):r.commit(done)


if __name__=='__main__':unittest.main()
