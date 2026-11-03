from dataclasses import replace
import hashlib
import struct
import sys
from pathlib import Path
import unittest
import zlib
import numpy as np
import game_codec as gc


def uniform(h,w,scale):
    mw,mh=gc.roi.geometry(w,h)
    return np.full((mh,mw),scale,np.uint8)


def crc(packet):return packet[:-4]+struct.pack('<I',zlib.crc32(packet[:-4]))


class CodecTests(unittest.TestCase):
    def test_uniform_keys_p_global_and_refresh_match_frozen_ma01(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"python-anchor-study"))
        import anchor_codec
        rng=np.random.default_rng(801)
        for scale in gc.roi.SCALES:
            enc=gc.Encoder();old=anchor_codec.AnchorEncoder();rx=gc.Receiver();gold=anchor_codec.AnchorReceiver()
            for i in range(7):
                source=rng.integers(0,256,(48,64,3),dtype=np.uint8)
                kwargs=dict(force_key=i==4,mode='global')
                p=enc.prepare(source,i,scale_map=uniform(48,64,scale),**kwargs)
                other=old.prepare(source,i,quant_scale=scale,**kwargs)
                actual,meta=rx.receive(p);expected,_=gold.receive(other)
                np.testing.assert_array_equal(actual,expected)
                self.assertEqual(hashlib.sha256(actual.tobytes()).hexdigest(),enc.expected_hash(i))
                self.assertEqual(meta['anchor_id'],gold.anchor_id)
                enc.ack(i,epoch=1);old.ack(i,epoch=1)
            self.assertEqual(enc.analysis_count,7);self.assertEqual(enc.forward_calls,21)

    def test_nonuniform_key_matches_rg01_and_p_manual_golden(self):
        rng=np.random.default_rng(802);enc=gc.Encoder();rx=gc.Receiver()
        source=rng.integers(0,256,(34,66,3),dtype=np.uint8)
        m=uniform(34,66,32);m[:2,:2]=8;m[-1,-1]=16
        packet=enc.prepare(source,0,scale_map=m);actual,_=rx.receive(packet)
        np.testing.assert_array_equal(actual,gc.roi.decode(gc.roi.encode(source,m)))
        enc.ack(0,epoch=1)
        source=rng.integers(0,256,source.shape,dtype=np.uint8)
        p=enc.analyze(source,1);c=enc.encode_candidate(p,m);packet=enc.commit(c)
        parsed=gc.parse(packet,1);planes=[]
        for i,(coeff,pred) in enumerate(zip(parsed['coefficients'],p.prediction)):
            h,w=pred.shape;ph,pw=((h+7)//8)*8,((w+7)//8)*8
            values=gc.ft.inverse(coeff.astype(np.int64)*gc.roi.block_tables(m,66,34,i))
            values=values.reshape(ph//8,pw//8,8,8).transpose(0,2,1,3).reshape(ph,pw)[:h,:w]
            planes.append(np.clip(values+pred,0,255).astype(np.int16))
        actual,_=rx.receive(packet)
        np.testing.assert_array_equal(actual,gc.ft.planes_to_rgb(planes))
        self.assertEqual(parsed['map_bytes'],4)

    def test_two_candidates_reuse_analysis_and_do_not_mutate_until_commit(self):
        enc=gc.Encoder();a=np.full((32,48,3),81,np.uint8)
        p=enc.analyze(a,0);a[:]=0
        c1=enc.encode_candidate(p,uniform(32,48,8));c2=enc.encode_candidate(p,uniform(32,48,32))
        self.assertEqual(enc.pending,{});self.assertIsNone(enc.anchor_id);self.assertEqual(enc.last_issued,-1)
        self.assertEqual(enc.forward_calls,3)
        packet=enc.commit(c1);self.assertEqual(packet,c1.packet)
        with self.assertRaises(ValueError):enc.commit(c2)
        with self.assertRaises(ValueError):enc.encode_candidate(p,uniform(32,48,16))
        expected=hashlib.sha256(gc.Receiver().receive(packet)[0].tobytes()).hexdigest()
        self.assertEqual(expected,enc.expected_hash(0))

    def test_foreign_forged_and_old_generation_candidates_rejected(self):
        a=np.full((16,16,3),50,np.uint8);one=gc.Encoder();two=gc.Encoder()
        p=one.analyze(a,0);c=one.encode_candidate(p,uniform(16,16,16))
        for candidate in (c,replace(c)):
            with self.assertRaises(ValueError):two.commit(candidate)
        with self.assertRaises(ValueError):one.commit(replace(c))
        with self.assertRaises(ValueError):one.encode_candidate(replace(p),uniform(16,16,8))
        one.commit(c);one.expire(0)
        with self.assertRaises(ValueError):one.commit(c)

    def test_window_drained_refresh_and_immutable_p_anchor(self):
        a=np.full((32,32,3),50,np.uint8);enc=gc.Encoder(window=2);rx=gc.Receiver()
        packet=enc.prepare(a,0);rx.receive(packet)
        with self.assertRaises(ValueError):enc.analyze(a,1)
        enc.ack(0,epoch=1)
        for i in (1,2):
            packet=enc.prepare(a+i,i);rx.receive(packet)
        self.assertEqual(enc.anchor_id,0);self.assertEqual(rx.anchor_id,0)
        with self.assertRaises(ValueError):enc.analyze(a,3)
        with self.assertRaises(ValueError):enc.analyze(a,3,force_key=True)
        enc.ack(2,epoch=1);enc.expire(1)
        packet=enc.prepare(a+5,4,force_key=True);rx.receive(packet);enc.ack(4,epoch=1)
        self.assertEqual(enc.anchor_id,4);self.assertEqual(rx.anchor_id,4)
        self.assertFalse(enc.ack(2,epoch=1))

    def test_ack_epoch_and_expired_key_require_new_independent_frame(self):
        a=np.full((16,16,3),55,np.uint8);enc=gc.Encoder();enc.prepare(a,0)
        with self.assertRaises(ValueError):enc.ack(0,epoch=2)
        self.assertTrue(enc.expire(0));self.assertFalse(enc.ack(0,epoch=1))
        p=enc.analyze(a,1);self.assertTrue(p.key)
        enc.commit(enc.encode_candidate(p,uniform(16,16,8)))
        with self.assertRaises(ValueError):enc.prepare(a,2)
        self.assertIsNone(enc.anchor_id)

    def test_crc_map_padding_nested_and_identity_reject_without_commit(self):
        source=np.full((2,2,3),70,np.uint8);enc=gc.Encoder();packet=enc.prepare(source,0)
        mutations=[]
        damaged=bytearray(packet);damaged[-1]^=1;mutations.append(bytes(damaged))
        for value in (0xc0,0x01):
            damaged=bytearray(packet);damaged[gc.HEADER.size]=value;mutations.append(crc(bytes(damaged)))
        damaged=bytearray(packet);damaged[gc.HEADER.size+1+gc.word_coeff.COEFF.size]^=1;mutations.append(crc(bytes(damaged)))
        for field,value in ((1,2),(2,0),(3,2),(4,gc.NO_REF),(5,0),(8,2),(10,2),(12,0),(13,1)):
            fields=list(gc.HEADER.unpack_from(packet));fields[field]=value
            mutations.append(crc(gc.HEADER.pack(*fields)+packet[gc.HEADER.size:]))
        for bad in mutations:
            receiver=gc.Receiver()
            with self.assertRaises(ValueError):receiver.receive(bad)
            self.assertEqual(receiver.last_frame_id,-1);self.assertIsNone(receiver._anchor)

    def test_missing_anchor_replay_geometry_and_session_reset(self):
        a=np.full((18,34,3),80,np.uint8);enc=gc.Encoder();rx=gc.Receiver()
        p=enc.prepare(a,0);rx.receive(p);enc.ack(0,epoch=1)
        p=enc.prepare(a+1,1)
        with self.assertRaises(ValueError):gc.Receiver().receive(p)
        rx.receive(p)
        with self.assertRaises(ValueError):rx.receive(p)
        with self.assertRaises(ValueError):gc.Receiver(epoch=2).receive(p)
        enc.ack(1,epoch=1)
        p=enc.prepare(np.zeros((2,2,3),np.uint8),2);_,meta=rx.receive(p)
        self.assertTrue(meta['key'])

    def test_map_domain_and_owned_analysis_arrays(self):
        enc=gc.Encoder();p=enc.analyze(np.zeros((18,34,3),np.uint8),0)
        for a in p.prediction+p.raw_coefficients:self.assertFalse(a.flags.writeable)
        for m in (np.zeros((2,3),np.uint8),np.full((2,2),16,np.uint8),np.full((2,3),16,np.int16)):
            with self.assertRaises(ValueError):enc.encode_candidate(p,m)
        self.assertEqual(enc.pending,{})
        m=uniform(18,34,8);c=enc.encode_candidate(p,m);m[:]=32
        self.assertTrue(np.all(c.scale_map==8));self.assertFalse(c.scale_map.flags.writeable)


if __name__=='__main__':unittest.main()
