import hashlib
import unittest
import numpy as np
from token_key_encoder import Encoder, frozen
import token_coeff as fast


class TokenTests(unittest.TestCase):
    def test_eighty_coefficient_families(self):
        rng=np.random.default_rng(5302026)
        for case in range(80):
            width=int(rng.integers(1,16)); rows=int(rng.integers(1,8))
            amplitude=(1,4,31,255,2048)[case%5]; density=(0,.001,.005,.01,.1,.5,1)[case%7]
            a=rng.integers(-amplitude,amplitude+1,(width*rows,8,8),dtype=np.int16)
            a[rng.random(a.shape)>density]=0
            if case%3==0:a[:,0,0]=rng.integers(-2048,2049,len(a),dtype=np.int16)
            packet=fast.encode_coefficients(a,width)
            self.assertEqual(packet,fast.frozen.encode_coefficients(a,width))
            np.testing.assert_array_equal(fast.frozen.decode_coefficients(packet,len(a),width),a)

    def test_key_p_quant_global_and_refresh_exact(self):
        rng=np.random.default_rng(901)
        old,new,rx=frozen.AnchorEncoder(),Encoder(),frozen.AnchorReceiver()
        for i,scale in enumerate((1,8,16,128,32)):
            rgb=rng.integers(0,256,(50,66,3),dtype=np.uint8)
            kwargs=dict(quant_scale=scale,force_key=i==3,mode='global')
            packet=new.prepare(rgb,i,**kwargs)
            self.assertEqual(packet,old.prepare(rgb,i,**kwargs))
            pixels,_=rx.receive(packet)
            expected=hashlib.sha256(pixels.tobytes()).hexdigest()
            self.assertEqual(expected,old.expected_hash(i))
            self.assertEqual(expected,new.expected_hash(i))
            old.ack(i,epoch=1);new.ack(i,epoch=1)

    def test_zero_zrl_and_raw_extremes(self):
        for position in range(64):
            a=np.zeros((4,8,8),np.int16)
            a.reshape(4,64)[:,fast.frozen.frozen.ZIGZAG[position]]=2048 if position%2 else -2048
            self.assertEqual(fast.encode_coefficients(a,2),fast.frozen.encode_coefficients(a,2))
        a=np.arange(640,dtype=np.int16).reshape(10,8,8)%4097-2048
        self.assertEqual(fast.encode_coefficients(a,5),fast.frozen.encode_coefficients(a,5))


if __name__=='__main__':unittest.main()
