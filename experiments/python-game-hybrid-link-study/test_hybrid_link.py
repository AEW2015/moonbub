from dataclasses import replace
import hashlib
import struct
import unittest
import zlib
import numpy as np
import adapter as a
import model


def complete(packet,frame,epoch=1):
    ingress=a.transport.Reassembler(epoch)
    delivered=None
    for i,p in enumerate(reversed(a.transport.datagrams(packet,epoch,frame))):
        result=ingress.feed(p,i)
        if result is not None:delivered=result
    return ingress,delivered


def fixture(frame=0):
    rgb=np.full((32,64,3),[30,40,50],np.uint8)
    rgb[8:16,8:24]=[220,180,120]
    enc=a.hybrid.gm.Encoder();base=enc.prepare(rgb,frame,quant_scale=16)
    d=a.hybrid.select_frame(base,rgb,a.hybrid.Config(rectangles=((8,8,16,8),)))
    return rgb,base,d.packet


class HybridLinkTests(unittest.TestCase):
    def test_real_hg_chunks_and_outer_content_ack(self):
        rgb,base,packet=fixture();ingress,done=complete(packet,0)
        actual,info,feedback,error=a.receive_complete(ingress,done,a.DecoderState())
        self.assertIsNone(error);self.assertEqual(info['format'],'HG01')
        np.testing.assert_array_equal(a.hybrid.hp.corpus.rgb565(actual)[8:16,8:24],a.hybrid.hp.corpus.rgb565(rgb)[8:16,8:24])
        fb=a.transport.parse_feedback(feedback)
        self.assertTrue(a.transport.matches_feedback(fb,1,0,a.transport.content_crc(packet)))
        self.assertNotEqual(a.transport.content_crc(packet),a.transport.content_crc(base))
        self.assertFalse(a.transport.matches_feedback(fb,1,0,a.transport.content_crc(base)))
        self.assertFalse(ingress.pending)

    def test_outer_identity_mismatch_never_commits_inner_key(self):
        rgb,base,packet=fixture();ingress,done=complete(packet,3)
        decoder=a.DecoderState();actual,info,feedback,error=a.receive_complete(ingress,done,decoder)
        self.assertIsNotNone(error);self.assertIsNone(actual)
        self.assertEqual(decoder.last_frame_id,-1);self.assertIsNone(decoder._anchor)
        self.assertEqual(a.transport.parse_feedback(feedback).status,a.transport.NACK)
        self.assertFalse(ingress.pending)

    def test_valid_transport_invalid_nested_patch_is_atomic(self):
        rgb,base,packet=fixture()
        broken=bytearray(packet);broken[-5]^=1
        broken[-4:]=struct.pack('<I',zlib.crc32(broken[:-4]));broken=bytes(broken)
        ingress,done=complete(broken,0);decoder=a.DecoderState()
        actual,info,feedback,error=a.receive_complete(ingress,done,decoder)
        self.assertIsNotNone(error);self.assertIsNone(actual)
        self.assertEqual(decoder.last_frame_id,-1);self.assertIsNone(decoder._anchor)
        self.assertEqual(a.transport.parse_feedback(feedback).frame_crc,a.transport.content_crc(broken))
        self.assertFalse(ingress.pending)

    def test_conflicting_duplicate_retains_hg_decoder_pin(self):
        rgb,base,packet=fixture();ingress,done=complete(packet,0)
        forged=bytearray(a.transport.datagrams(packet,1,0)[0]);forged[-1]^=1
        with self.assertRaises(ValueError):ingress.feed(bytes(forged),100)
        self.assertIs(ingress.pending[0]['complete'],done)
        with self.assertRaises(ValueError):ingress.reset(2)
        self.assertIsNone(a.receive_complete(ingress,done,a.DecoderState())[3])
        self.assertFalse(ingress.pending)

    def test_mixed_gm_hg_preserves_immutable_reference(self):
        enc=a.hybrid.gm.Encoder();rx=a.DecoderState();plain=a.hybrid.gm.Receiver()
        rgb=np.full((32,64,3),40,np.uint8)
        for i in range(4):
            current=rgb.copy();current[8:16,8:24]=[150+i,170,190]
            base=enc.prepare(current,i,quant_scale=16)
            d=a.hybrid.select_frame(base,current,a.hybrid.Config(rectangles=((8,8,16,8),),max_attempts=0 if i%2 else 1))
            ingress,done=complete(d.packet,i)
            actual,info,fb,error=a.receive_complete(ingress,done,rx)
            self.assertIsNone(error);plain.receive(base)
            for x,y in zip(rx._anchor,plain._anchor):np.testing.assert_array_equal(x,y)
            self.assertTrue(enc.ack(i,epoch=1))
        self.assertEqual(rx.anchor_id,0)

    def test_finite_charged_hg_pipeline_with_ack_loss_recovers(self):
        frames=[np.full((32,64,3),50+i,np.uint8) for i in range(18)]
        factory=a.make_controller(rectangles=((0,0,16,16),),use_gate=False)
        cfg=model.Config(width=64,height=32,rectangles=((0,0,16,16),),decoder_service='python_wall',
                         feedback_loss_ids=(0,),frame_deadline_ms=500)
        r=model.run(frames,{},cfg,controller_factory=factory)
        self.assertTrue(all(v is None for v in r['unresolved_sender_slots']))
        self.assertFalse(r['unresolved_ingress_frames']);self.assertFalse(r['unresolved_credits'])
        self.assertTrue(all(v==0 for v in r['unresolved_cpu'].values()))
        self.assertTrue(r['commits']);self.assertTrue(all(c['selected_rgb565_mismatches']==0 for c in r['commits']))
        self.assertTrue(any(c['format']=='HG01' for c in r['commits']))
        self.assertTrue(any(f['kind']=='lost' for f in r['feedback']))
        self.assertTrue(r['timeout_events']);self.assertEqual(r['presented'][-1]['id'],17)


if __name__=='__main__':unittest.main()
