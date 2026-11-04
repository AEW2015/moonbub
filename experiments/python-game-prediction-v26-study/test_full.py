import unittest,struct
import numpy as np
import full_benchmark as f

class FullTests(unittest.TestCase):
    def test_fast_counter_identical_packets_outputs_without_global_mutation(self):
        m=f.m;original=m.base._rdo_skip;src=tuple(m.ft.rgb_to_planes(np.random.default_rng(1).integers(0,256,(64,64,3),dtype=np.uint8)))
        q=m.roi.declared_map(64,64,(),8,16)
        _,ref,_=m.encode_planes(src,None,q)
        for kind in ('zero','block'):
            kw=dict(frame_id=1,reference_id=0,block_size=32,motion_mode=kind,motion_precision='half',rdo_lambda=1)
            a,x,_=m.encode_planes(src,ref,q,**kw);b,y,_=m.base.encode_planes(src,ref,q,**kw)
            self.assertEqual(a,b)
            for xx,yy in zip(x,y):np.testing.assert_array_equal(xx,yy)
        self.assertIs(m.base._rdo_skip,original)
    def test_cp2f_ja2f_actual_receiver_atomic_rejections(self):
        b=f.b;p=f.p;m=f.m
        prior=b.n.load(b.CAPPED/'results.json');case=next(c for c in prior['cases'] if c['profile']=='capped_key_zero_rdo1')
        old=b.n.load(b.n.V24/'results.json');inp=next(x for x in old['inputs'] if x['scene']==case['scene'])
        row=case['rows'][0];src=b.n.source(inp['rows'][0]);hud=b.n.raw(row['hud_packet'],b.CAPPED)
        q=m.roi.declared_map(720,480,b.n.ROIS,8,row['selected_background'])
        base,expected,_=m.encode_planes(src,None,q,epoch=25)
        pair=f.pair_bytes(base,hud,0,0,True);self.assertEqual(pair[:4],b'CP2F');self.assertLessEqual(len(pair),p.CAP)
        receiver=p.Receiver(epoch=25)
        for kwargs,bad in ((dict(write_drained=False),pair),({},pair[:-1]),({},pair+bytes(1))):
            with self.assertRaises(ValueError):receiver.receive(bad,**kwargs)
            self.assertEqual(receiver.last_frame_id,-1);self.assertEqual(receiver.banks,(None,None))
        got,patches,ack=receiver.receive(pair);self.assertEqual(ack[:4],b'JA2F');p.validate_ack(ack,pair)
        for x,y in zip(got,expected):np.testing.assert_array_equal(x,y)
        state=(receiver.last_frame_id,receiver.banks,receiver.last_ack)
        with self.assertRaises(ValueError):receiver.receive(pair)
        self.assertEqual(receiver.last_frame_id,state[0]);self.assertIs(receiver.banks,state[1]);self.assertEqual(receiver.last_ack,state[2])
        with self.assertRaises(ValueError):p.validate_ack(ack[:-1]+bytes((ack[-1]^1,)),pair)
        forged=p.seal(p.PAIR.pack(b'CP25',1,p.KEY|p.PUBLISH,25,0,255,0,len(base),len(hud),p.digest(base),p.digest(hud))+base+hud)
        with self.assertRaises(ValueError):p.parse_pair(forged)
if __name__=='__main__':unittest.main()
