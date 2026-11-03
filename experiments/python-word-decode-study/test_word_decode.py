import hashlib
from pathlib import Path
import struct
import sys
import unittest
import zlib

import numpy as np
import word_coeff as wc
from word_receiver import AnchorReceiver, Receiver, anchor

sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'python-token-entropy-study'))
from token_key_encoder import Encoder


F=wc.frozen_codec


def crc(body):return body+struct.pack('<I',zlib.crc32(body))


def packet(dc,ac,kd=0,ks=(0,0,0)):
    d=bytes([kd])+F._pack(dc)
    a=bytes(ks)+F._pack(ac)
    return crc(F.COEFF.pack(b'CP02',1,1,1,1,0,len(d),len(a))+d+a)


def result(dec,raw,n,bw):
    try:return ('ok',dec(raw,n,bw))
    except ValueError:return ('reject',None)


class WordTests(unittest.TestCase):
    def same(self,raw,n,bw):
        old,new=result(F.decode_coefficients,raw,n,bw),result(wc.decode_coefficients,raw,n,bw)
        self.assertEqual(old[0],new[0])
        if old[0]=='ok':np.testing.assert_array_equal(old[1],new[1])
        return old[0]

    def test_eighty_coefficient_families_and_dc_extremes(self):
        rng=np.random.default_rng(711)
        modes=set()
        for case in range(80):
            bw=(1,2,4,8)[case%4];n=bw*2
            a=rng.integers(-2048,2049,(n,8,8),dtype=np.int16)
            a[rng.random(a.shape)>((case%10)/9)]=0
            if case%5==0:a[:,0,0]=np.resize(np.array([-2048,2048],np.int16),n)
            raw=F.encode_coefficients(a,bw);modes.add(F.COEFF.unpack_from(raw)[2])
            self.assertEqual(self.same(raw,n,bw),'ok')
        self.assertEqual(modes,{0,1})

    def test_all_zigzag_positions(self):
        for pos in range(64):
            a=np.zeros((2,8,8),np.int16)
            a.reshape(2,64)[:,F.frozen.ZIGZAG[pos]]=[2048,-2048]
            self.assertEqual(self.same(F.encode_coefficients(a,2),2,2),'ok')

    def test_canonical_truncation_padding_and_run_rejections(self):
        good=packet('1','00')
        self.assertEqual(self.same(good,1,1),'ok')
        bad=[packet('0'*15+'0'*14,'00'), # noncanonical DC escape
             packet('1','10000'+'0'*15+'0'*12), # noncanonical AC escape
             packet(F._rice(4098,0,14),'00'), # reconstructed DC >2048
             packet('1','01'*4), # ZRL overrun
             packet('1','01'*3+'11111'), # target64
             packet('1','10000'+'001'+'0'*11,ks=(11,11,11)), # -2049
             packet('1','00'+'0'*8), # extra full padding byte
             packet('1','001'), # nonzero padding
             packet('0'*8,'00')] # truncated DC unary
        for raw in bad:self.assertEqual(self.same(raw,1,1),'reject')
        for i in range(len(good)):
            self.assertEqual(self.same(good[:i],1,1),'reject')
        damaged=good[:-1]+bytes([good[-1]^1])
        self.assertEqual(self.same(damaged,1,1),'reject')

    def test_valid_crc_mutation_campaign_and_geometry(self):
        a=np.zeros((4,8,8),np.int16);a[0,0,0]=10;a[1,1,2]=-9
        raw=F.encode_coefficients(a,2)
        for offset in range(len(raw)-4):
            for bit in (1,8,128):
                b=bytearray(raw[:-4]);b[offset]^=bit
                self.same(crc(bytes(b)),4,2)
        for n,bw in ((True,1),(0,1),(4,0),(4,3),(4,257),(65537,1)):
            self.assertEqual(self.same(raw,n,bw),'reject')

    def test_bit_reservoir_bounds_and_unary_matches(self):
        rng=np.random.default_rng(713)
        for k in range(14):
            vals=[0,1,14<<k,15<<k]
            for v in vals:
                if v>=1<<14:continue
                data=F._pack(F._rice(v,k,14))
                old,new=F._Bits(data),wc._Bits(data)
                self.assertEqual(old.rice(k,14),new.rice(k,14))
                old.finish();new.finish();self.assertLessEqual(new.peak_bits,64)
        data=rng.integers(0,256,1000,dtype=np.uint8).tobytes()
        old,new=F._Bits(data),wc._Bits(data)
        while old.position<len(data)*8:
            n=min(13,len(data)*8-old.position)
            self.assertEqual(old.get(n),new.get(n));self.assertLessEqual(new.peak_bits,64)

    def test_ma01_key_p_refresh_and_invalid_state_unchanged(self):
        rng=np.random.default_rng(714)
        enc=Encoder();old,new=anchor.AnchorReceiver(),AnchorReceiver()
        for i in range(7):
            rgb=rng.integers(0,256,(32,48,3),dtype=np.uint8)
            raw=enc.prepare(rgb,i,force_key=i==4,quant_scale=(1,8,32,128)[i%4],mode='global')
            a,info=old.receive(raw);b,ourinfo=new.receive(raw)
            np.testing.assert_array_equal(a,b);self.assertEqual(info,ourinfo)
            self.assertEqual(hashlib.sha256(b.tobytes()).hexdigest(),enc.expected_hash(i))
            before=(new.last_frame_id,new.anchor_id,[p.copy() for p in new._anchor])
            for bad in (raw,raw[:-1]+bytes([raw[-1]^1])):
                with self.assertRaises(ValueError):new.receive(bad)
                self.assertEqual((new.last_frame_id,new.anchor_id),before[:2])
                for x,y in zip(new._anchor,before[2]):np.testing.assert_array_equal(x,y)
            enc.ack(i,epoch=1)


if __name__=='__main__':unittest.main()
