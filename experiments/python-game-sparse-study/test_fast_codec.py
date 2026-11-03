import struct
import unittest
import numpy as np
import fast_codec as f


class FastInverseTests(unittest.TestCase):
    def test_exhaustive_dc_coefficient_domain_all_scales_planes(self):
        c=np.zeros((4097,8,8),np.int64);c[:,0,0]=np.arange(-2048,2049)
        for chroma in (False,True):
            for scale in f.gm.roi.SCALES:
                raw=c*f.gm.ft.qtable(scale,chroma)
                expected=f.gm.ft.inverse(raw)
                actual=np.broadcast_to(f.dc_inverse(raw[:,0,0])[:,None,None],expected.shape)
                np.testing.assert_array_equal(actual,expected)
        self.assertTrue(all(not table.flags.writeable for table in f.TABLES))

    def test_zero_dc_general_partial_geometry_and_maps(self):
        rng=np.random.default_rng(1212)
        for w,h in ((2,2),(34,18),(720,480)):
            mw,mh=f.gm.roi.geometry(w,h);m=rng.choice(np.array(f.gm.roi.SCALES,np.uint8),size=(mh,mw))
            cs=[];ps=[]
            for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2)):
                n=((pw+7)//8)*((ph+7)//8)
                c=rng.integers(-2048,2049,(n,8,8),dtype=np.int16)
                c[::3]=0;c[1::3]=0;c[1::3,0,0]=511
                cs.append(c);ps.append(rng.integers(0,256,(ph,pw),dtype=np.int16))
            expected=f.gm.reconstruct(cs,ps,m,w,h);actual,stats=f.reconstruct(cs,ps,m,w,h,return_stats=True)
            for a,b in zip(actual,expected):np.testing.assert_array_equal(a,b)
            self.assertTrue(all(s['zero']+s['dc_only']+s['general_inverse']==s['blocks'] for s in stats))

    def test_actual_key_p_refresh_and_atomic_crc_rejection(self):
        rng=np.random.default_rng(12);enc=f.gm.Encoder();slow=f.gm.Receiver();fast=f.Receiver()
        for i in range(8):
            rgb=rng.integers(0,256,(32,64,3),dtype=np.uint8)
            packet=enc.prepare(rgb,i,quant_scale=16,force_key=(i%4==0))
            a,ai=slow.receive(packet);b,bi=fast.receive(packet)
            np.testing.assert_array_equal(a,b)
            for x,y in zip(slow._anchor,fast._anchor):np.testing.assert_array_equal(x,y)
            enc.ack(i,epoch=1)
        last=fast.last_frame_id;anchor=fast._anchor
        broken=packet[:-1]+bytes((packet[-1]^1,))
        with self.assertRaises(ValueError):fast.receive(broken)
        self.assertEqual(fast.last_frame_id,last);self.assertIs(fast._anchor,anchor)

    def test_hg_and_gm_mixed_dispatch_pixels_exact(self):
        rgb=np.full((32,64,3),[30,50,70],np.uint8)
        enc=f.gm.Encoder();slow=f.hybrid.Decoder();fast=f.HybridReceiver()
        for i in range(6):
            current=rgb.copy();current[8:16,8:24]=[190+i,210,230]
            base=enc.prepare(current,i,quant_scale=16)
            d=f.hybrid.select_frame(base,current,f.hybrid.Config(rectangles=((8,8,16,8),),max_attempts=i%2))
            a,ai=slow.receive(d.packet);b,bi=fast.receive(d.packet)
            np.testing.assert_array_equal(a,b)
            for x,y in zip(slow.base._anchor,fast.base._anchor):np.testing.assert_array_equal(x,y)
            enc.ack(i,epoch=1)

    def test_epoch_reference_and_replay_contract_unchanged(self):
        enc=f.gm.Encoder();rx=f.Receiver();rgb=np.zeros((16,32,3),np.uint8)
        packet=enc.prepare(rgb,0,quant_scale=16);rx.receive(packet);enc.ack(0,epoch=1)
        residual=enc.prepare(rgb,1,quant_scale=16)
        with self.assertRaises(ValueError):f.Receiver().receive(residual)
        with self.assertRaises(ValueError):f.Receiver(2).receive(packet)
        with self.assertRaises(ValueError):rx.receive(packet)
        self.assertEqual(rx.last_frame_id,0)


if __name__=='__main__':unittest.main()
