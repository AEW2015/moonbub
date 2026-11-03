import struct
import unittest
import zlib
import numpy as np
import tile_codec as c


def crc(packet):return packet[:-4]+struct.pack('<I',zlib.crc32(packet[:-4]))


class DirtyTileTests(unittest.TestCase):
    def test_exact_source_skip_ack_and_no_mutable_alias(self):
        a=np.full((34,66,3),80,np.uint8);enc=c.Encoder();rx=c.Receiver()
        p,info=enc.prepare(a,0);actual,_=rx.receive(p)
        np.testing.assert_array_equal(actual,enc.expected_rgb());enc.ack(0,epoch=1)
        actual[:]=0
        p,info=enc.prepare(a,1)
        self.assertEqual(info['changed_tiles'],0)
        actual,meta=rx.receive(p)
        np.testing.assert_array_equal(actual,enc.expected_rgb())
        self.assertEqual(meta['logical_skip_rgb565_read_bytes'],34*66*2)
        with self.assertRaises(ValueError):enc.prepare(a,2)
        with self.assertRaises(ValueError):enc.ack(1,epoch=0)

    def test_only_changed_tile_is_encoded_and_abort_forces_key(self):
        rng=np.random.default_rng(710);a=rng.integers(0,256,(64,64,3),dtype=np.uint8)
        enc=c.Encoder();rx=c.Receiver();p,_=enc.prepare(a,0);rx.receive(p);enc.ack(0,epoch=1)
        b=a.copy();b[2,2]^=255
        p,info=enc.prepare(b,1);self.assertEqual(info['changed_tiles'],1)
        rgb,_=rx.receive(p);np.testing.assert_array_equal(rgb,enc.expected_rgb())
        enc.abort();p,info=enc.prepare(b,2);self.assertTrue(info['key']);rx.receive(p)

    def test_corruption_missing_reference_and_replay_do_not_commit(self):
        a=np.full((32,34,3),60,np.uint8);enc=c.Encoder();rx=c.Receiver()
        p,_=enc.prepare(a,0);rx.receive(p);enc.ack(0,epoch=1)
        p,_=enc.prepare(a+1,1)
        with self.assertRaises(ValueError):rx.receive(p[:-1]+bytes([p[-1]^1]))
        self.assertEqual(rx.reference_id,0)
        with self.assertRaises(ValueError):c.Receiver().receive(p)
        rx.receive(p)
        with self.assertRaises(ValueError):rx.receive(p)

    def test_key_map_padding_and_nested_geometry_validate_before_commit(self):
        a=np.full((2,2,3),42,np.uint8);enc=c.Encoder();p,_=enc.prepare(a,0)
        for value in (0,129):
            b=bytearray(p);b[c.HEADER.size]=value
            with self.assertRaises(ValueError):c.Receiver().receive(crc(bytes(b)))
        b=bytearray(p);start=c.HEADER.size+1+4
        fields=list(c.cc.FRAME.unpack_from(b,start));fields[3]=4
        b[start:start+c.cc.FRAME.size]=c.cc.FRAME.pack(*fields)
        with self.assertRaises(ValueError):c.Receiver().receive(crc(bytes(b)))

    def test_quantizer_change_refreshes_even_identical_static_source(self):
        a=np.full((32,32,3),81,np.uint8);enc=c.Encoder();rx=c.Receiver()
        p,_=enc.prepare(a,0,quant_scale=32);rx.receive(p);enc.ack(0,epoch=1)
        p,info=enc.prepare(a,1,quant_scale=8)
        self.assertTrue(info['key']);self.assertEqual(info['changed_tiles'],1)
        actual,_=rx.receive(p);np.testing.assert_array_equal(actual,enc.expected_rgb())
        enc.ack(1,epoch=1);self.assertEqual(enc.quant_scale,8)

    def test_roundtrip_scales_geometry_and_bounds(self):
        rng=np.random.default_rng(711)
        for scale in (1,8,32,128):
            enc=c.Encoder();rx=c.Receiver()
            for i,shape in enumerate(((2,2,3),(18,34,3),(64,80,3))):
                a=rng.integers(0,256,shape,dtype=np.uint8)
                p,_=enc.prepare(a,i,quant_scale=scale)
                actual,_=rx.receive(p);np.testing.assert_array_equal(actual,enc.expected_rgb())
                self.assertLessEqual(len(p),c.bound(shape[1],shape[0]));enc.ack(i,epoch=1)


if __name__=='__main__':unittest.main()
