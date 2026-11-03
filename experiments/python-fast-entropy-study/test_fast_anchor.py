import hashlib
import unittest

import numpy as np

from fast_anchor import Encoder,frozen


class FastAnchorTests(unittest.TestCase):
    def test_lazy_host_reconstruction_keeps_packets_and_anchor_identical(self):
        old,new=frozen.AnchorEncoder(),Encoder()
        rx=frozen.AnchorReceiver()
        rng=np.random.default_rng(11)
        for i in range(6):
            rgb=rng.integers(0,256,(48,64,3),dtype=np.uint8)
            kwargs=dict(quant_scale=8,force_key=i==4,mode='zero')
            a=old.prepare(rgb,i,**kwargs);b=new.prepare(rgb,i,**kwargs)
            self.assertEqual(a,b)
            if not new.pending[i]['key']:
                self.assertIsNone(new.pending[i]['expected_rgb_sha256'])
            actual,_=rx.receive(b)
            expected=hashlib.sha256(actual.tobytes()).hexdigest()
            self.assertEqual(expected,old.expected_hash(i))
            self.assertEqual(expected,new.expected_hash(i))
            old.ack(i,epoch=1);new.ack(i,epoch=1)
            self.assertEqual(old.anchor_id,new.anchor_id)

    def test_no_p_oracle_needed_to_release_credit(self):
        enc=Encoder(window=2)
        rgb=np.full((16,16,3),50,np.uint8)
        enc.prepare(rgb,0);enc.ack(0,epoch=1)
        enc.prepare(rgb+1,1);enc.prepare(rgb+2,2)
        with self.assertRaises(ValueError):enc.prepare(rgb,3)
        enc.ack(1,epoch=1);enc.expire(2)
        self.assertEqual(enc.pending,{})
        self.assertEqual(enc.anchor_id,0)


if __name__=='__main__':unittest.main()
