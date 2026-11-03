from dataclasses import replace
import unittest
import numpy as np
import chunks
import harness


class HarnessTests(unittest.TestCase):
    def source(self):
        return np.random.default_rng(808).integers(0,256,(64,80,3),dtype=np.uint8)

    def test_only_complete_decode_publishes_reference_and_ack_credit(self):
        gc=harness.codec;enc=gc.Encoder();rx=gc.Receiver();ingress=chunks.Reassembler()
        packet=enc.prepare(self.source(),0)
        wire=chunks.datagrams(packet,1,0);self.assertGreater(len(wire),1)
        result=None
        for i,p in enumerate(reversed(wire)):
            result=ingress.feed(p,i)
            self.assertEqual(rx.last_frame_id,-1)
        self.assertIsNotNone(result);self.assertIsNone(enc.anchor_id)
        rgb,info=harness.decode_complete(result,ingress,rx)
        self.assertEqual(gc.hashlib.sha256(rgb.tobytes()).hexdigest(),enc.expected_hash(0))
        self.assertEqual(rx.anchor_id,0);self.assertIsNone(enc.anchor_id)
        enc.ack(0,epoch=1);self.assertEqual(enc.anchor_id,0)
        self.assertEqual(ingress.payload_bytes(),0)

    def test_outer_identity_mismatch_and_inner_crc_rejection_are_atomic(self):
        gc=harness.codec;packet=gc.Encoder().prepare(self.source(),0)
        for data,frame in ((packet,7),(packet[:-1]+bytes([packet[-1]^1]),0)):
            ingress=chunks.Reassembler();rx=gc.Receiver();result=None
            for i,p in enumerate(chunks.datagrams(data,1,frame)):result=ingress.feed(p,i)
            with self.assertRaises(ValueError):harness.decode_complete(result,ingress,rx)
            self.assertEqual(rx.last_frame_id,-1);self.assertIsNone(rx._anchor)
            self.assertEqual(ingress.committed,-1);self.assertEqual(ingress.payload_bytes(),0)

    def test_unowned_complete_cannot_mutate_codec(self):
        gc=harness.codec;packet=gc.Encoder().prepare(self.source(),0)
        ingress=chunks.Reassembler();rx=gc.Receiver();result=None
        for i,p in enumerate(chunks.datagrams(packet,1,0)):result=ingress.feed(p,i)
        with self.assertRaises(ValueError):harness.decode_complete(replace(result),ingress,rx)
        self.assertEqual(rx.last_frame_id,-1)
        harness.decode_complete(result,ingress,rx)

    def test_missing_chunk_times_out_without_codec_or_credit_commit(self):
        gc=harness.codec;enc=gc.Encoder();packet=enc.prepare(self.source(),0)
        ingress=chunks.Reassembler(timeout_ms=10);rx=gc.Receiver()
        first=chunks.datagrams(packet,1,0)[0]
        self.assertIsNone(ingress.feed(first,0));self.assertEqual(ingress.expire(10),[0])
        self.assertEqual(rx.last_frame_id,-1);self.assertIsNone(enc.anchor_id);self.assertIn(0,enc.pending)
        enc.expire(0)
        self.assertTrue(enc.analyze(self.source(),1).key)


if __name__=='__main__':unittest.main()
