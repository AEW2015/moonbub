import hashlib
import struct
import unittest
import zlib
import numpy as np
import hud_codec as h


def crc(data):return data[:-4]+struct.pack('<I',zlib.crc32(data[:-4]))


class HudTests(unittest.TestCase):
    def rgb(self,hgt=32,wid=48):
        return np.random.default_rng(901).integers(0,256,(hgt,wid,3),dtype=np.uint8)

    def test_modes_and_exact_rgb565_rectangles(self):
        for count,mode in ((1,1),(2,1),(3,2),(4,2),(5,4),(16,4),(17,8),(256,8),(257,0)):
            words=(np.arange(512,dtype=np.uint16)%count).reshape(16,32)
            rgb=h.corpus.expand565(words)
            packet=h.encode_patch(rgb,(0,0,32,16));p=h.decode_patch(packet,32,16)
            self.assertEqual(p['mode'],mode);np.testing.assert_array_equal(p['words'],words)
            self.assertEqual(p['bytes'],p['header_crc_bytes']+p['palette_bytes']+p['payload_bytes'])

    def test_patch_padding_mode_index_and_raw_checks(self):
        rgb=np.zeros((2,2,3),np.uint8);rgb[0,0]=255
        good=h.encode_patch(rgb,(0,0,1,1))
        bad=bytearray(good);bad[-5]|=1
        with self.assertRaises(ValueError):h.decode_patch(crc(bytes(bad)),2,2)
        for field,value in ((2,8),(7,257),(8,2),(9,3)):
            fields=list(h.PATCH.unpack_from(good));fields[field]=value
            bad=h.PATCH.pack(*fields)+good[h.PATCH.size:]
            with self.assertRaises(ValueError):h.decode_patch(crc(bad),2,2)
        # Canonical2bit palette of3 colors: index3 is forbidden even after CRC repair.
        words=np.array([[0,1,2,0],[0,1,2,0]],np.uint16)
        packet=h.encode_patch(h.corpus.expand565(words),(0,0,4,2))
        bad=bytearray(packet);bad[h.PATCH.size+6]|=0xc0
        with self.assertRaises(ValueError):h.decode_patch(crc(bytes(bad)),4,2)
        words=np.arange(512,dtype=np.uint16).reshape(16,32)
        raw=h.encode_patch(h.corpus.expand565(words),(0,0,32,16));fields=list(h.PATCH.unpack_from(raw));fields[7]=1
        with self.assertRaises(ValueError):h.decode_patch(crc(h.PATCH.pack(*fields)+raw[h.PATCH.size:]),32,16)

    def test_temporal_patch_does_not_advance_or_pollute_yuv_anchor(self):
        enc=h.gm.Encoder();plain=h.gm.Receiver();rx=h.Receiver();rgb=self.rgb()
        for frame in range(3):
            source=(rgb+frame*3).astype(np.uint8)
            packet=enc.prepare(source,frame)
            expected,info=plain.receive(packet)
            wrapped=h.encode_frame(packet,source,((0,0,16,16),))
            displayed,meta=rx.receive(wrapped)
            self.assertEqual(meta['base_rgb_sha256'],hashlib.sha256(expected.tobytes()).hexdigest())
            self.assertEqual(enc.expected_hash(frame),meta['base_rgb_sha256'])
            for a,b in zip(plain._anchor,rx.base._anchor):np.testing.assert_array_equal(a,b)
            np.testing.assert_array_equal(h.corpus.rgb565(displayed)[:16,:16],h.corpus.rgb565(source)[:16,:16])
            np.testing.assert_array_equal(h.corpus.rgb565(displayed)[16:],h.corpus.rgb565(expected)[16:])
            self.assertEqual(rx.base.anchor_id,0);enc.ack(frame,epoch=1)

    def test_malformed_patch_cannot_commit_valid_base(self):
        enc=h.gm.Encoder();rgb=self.rgb();base=enc.prepare(rgb,0)
        wrapper=h.encode_frame(base,rgb,((0,0,16,16),));bad=bytearray(wrapper)
        bad[-5]^=1;bad=crc(bytes(bad))
        rx=h.Receiver()
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertIsNone(rx.base._anchor);self.assertEqual(rx.base.last_frame_id,-1)
        rx.receive(wrapper);self.assertEqual(rx.base.anchor_id,0)

    def test_valid_crc_duplicate_palette_and_overlap_reject_atomically(self):
        words=np.array([[0,1],[0,1]],np.uint16)
        packet=h.encode_patch(h.corpus.expand565(words),(0,0,2,2))
        bad=bytearray(packet);bad[h.PATCH.size+2:h.PATCH.size+4]=bad[h.PATCH.size:h.PATCH.size+2]
        with self.assertRaises(ValueError):h.decode_patch(crc(bytes(bad)),2,2)
        rgb=self.rgb();base=h.gm.Encoder().prepare(rgb,0)
        wrapper=h.encode_frame(base,rgb,((0,0,16,16),))
        fields=list(h.FRAME.unpack_from(wrapper));fields[2]=2;fields[6]*=2
        section=wrapper[h.FRAME.size+len(base):-4]
        body=h.FRAME.pack(*fields)+base+section+section
        rx=h.Receiver()
        with self.assertRaises(ValueError):rx.receive(body+struct.pack('<I',zlib.crc32(body)))
        self.assertEqual(rx.base.last_frame_id,-1);self.assertIsNone(rx.base._anchor)

    def test_overlap_geometry_wrapper_and_patch_limits(self):
        rgb=self.rgb(18,34);base=h.gm.Encoder().prepare(rgb,0)
        with self.assertRaises(ValueError):h.encode_frame(base,rgb,((0,0,16,16),(8,8,16,8)))
        with self.assertRaises(ValueError):h.encode_frame(base,rgb,((33,0,2,2),))
        with self.assertRaises(ValueError):h.encode_frame(base,rgb,((0,0,1,1),)*5)
        wrapped=h.encode_frame(base,rgb,((33,17,1,1),))
        out,_=h.Receiver().receive(wrapped)
        self.assertEqual(int(h.corpus.rgb565(out)[17,33]),int(h.corpus.rgb565(rgb)[17,33]))
        for field,value in ((1,2),(2,5),(3,0),(4,32),(6,0)):
            fields=list(h.FRAME.unpack_from(wrapped));fields[field]=value
            bad=h.FRAME.pack(*fields)+wrapped[h.FRAME.size:]
            with self.assertRaises(ValueError):h.Receiver().receive(crc(bad))


if __name__=='__main__':unittest.main()
