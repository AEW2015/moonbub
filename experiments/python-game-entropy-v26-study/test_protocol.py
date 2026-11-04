import unittest
import numpy as np
import model as e
import protocol as p


class ProtocolTests(unittest.TestCase):
    def fixture(self,fid=0,ref=None):
        src=tuple(e.ft.rgb_to_planes(np.random.default_rng(26+fid).integers(0,256,(64,64,3),np.uint8)))
        q=e.roi.declared_map(64,64,(),8,16)
        old,_,_=e.old.encode_planes(src,ref,q,frame_id=fid,reference_id=e.NO_REF if ref is None else fid-1,motion_mode='zero')
        base,_=e.repack(old)
        hud,_=p.encode_hud((),epoch=1,frame_id=fid,width=64,height=64)
        return base,hud

    def test_pair_ack_and_protocol_discrimination(self):
        base,hud=self.fixture();pair=p.encode_pair(base,hud,epoch=1,frame_id=0)
        rx=p.Receiver(epoch=1,width=64,height=64);out,patches,ack=rx.receive(pair)
        self.assertEqual(pair[:4],b'CP26');self.assertEqual(ack[:4],b'JA26')
        self.assertEqual(p.validate_ack(ack,pair)['frame_id'],0)
        with self.assertRaises(ValueError):rx.receive(pair)
        with self.assertRaises(ValueError):e.old.parse(base)

    def test_failed_fence_and_bad_crc_never_publish(self):
        b,h=self.fixture();pair=p.encode_pair(b,h,epoch=1,frame_id=0)
        rx=p.Receiver(epoch=1,width=64,height=64)
        for kw in ({'write_drained':False},{'vblank':False}):
            with self.assertRaises(ValueError):rx.receive(pair,**kw)
            self.assertEqual(rx.last_frame_id,-1);self.assertEqual(rx.banks,(None,None))
        with self.assertRaises(ValueError):rx.receive(pair[:-1]+bytes([pair[-1]^1]))
        self.assertEqual(rx.last_frame_id,-1)

    def test_wrong_ref_and_ack_binding(self):
        b,h=self.fixture();pair=p.encode_pair(b,h,epoch=1,frame_id=0)
        rx=p.Receiver(epoch=1,width=64,height=64);ref,_,ack=rx.receive(pair)
        b,h=self.fixture(1,ref)
        second=p.encode_pair(b,h,epoch=1,frame_id=1,source_slot=1,destination_slot=0,key=False)
        # The packet references a bank that was never published.
        with self.assertRaises(ValueError):rx.receive(second)
        self.assertEqual(rx.last_frame_id,0)
        with self.assertRaises(ValueError):p.validate_ack(ack,second)


if __name__=='__main__':unittest.main()
