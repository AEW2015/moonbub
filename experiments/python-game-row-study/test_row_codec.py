import struct
import unittest
import numpy as np
import row_codec as rc


class RowCodecTests(unittest.TestCase):
    def words(self,words):
        return rc.hp.corpus.expand565(np.asarray(words,np.uint16))

    def test_all_selected_modes_roundtrip(self):
        rng=np.random.default_rng(1010)
        fixtures=[rng.integers(0,65536,(32,128),dtype=np.uint16),
                  np.repeat(np.arange(1024,dtype=np.uint16).reshape(32,32),4,axis=1),
                  np.full((32,128),129,np.uint16)]
        selected=[]
        for words in fixtures:
            rgb=self.words(words);packet,info=rc.encode_modes(rgb,(0,0,128,32))
            selected.append(info['selected_mode'])
            np.testing.assert_array_equal(rc.decode(packet,128,32)['words'],words)
            self.assertEqual(len(packet),min(a['bytes'] for a in info['attempts']))
        self.assertEqual(selected,[rc.RAW,rc.WORD_RUNS,rc.INDEX_RUNS])

    def test_odd_crop_edge_and_word_exact_not_rgb888(self):
        rgb=np.random.default_rng(100).integers(0,256,(32,64,3),dtype=np.uint8)
        packet,_=rc.encode_modes(rgb,(13,7,51,25))
        decoded=rc.decode(packet,64,32)
        self.assertEqual(decoded['rect'],(13,7,51,25))
        np.testing.assert_array_equal(decoded['words'],rc.hp.corpus.rgb565(rgb[7:,13:]))

    def test_row_tokens_boundaries_and_malformed(self):
        for width in (1,2,3,127,128,129,255,256,257,720):
            for unit in (1,2):
                values=[(i//3)%251 for i in range(width)]
                for sequence in (values,[7]*width,list(range(min(width,128)))+values[128:]):
                    packet=rc._tokens(sequence,unit)
                    self.assertEqual(rc._decode_row(packet,len(sequence),unit),sequence)
        for bad,width,unit in ((b'\x80',1,1),(b'\xff\x01',127,1),(b'\x00',1,2),(b'\x00\x01',2,1)):
            with self.assertRaises(ValueError):rc._decode_row(bad,width,unit)

    def test_crc_trailing_and_allocation_fields(self):
        rgb=self.words(np.full((16,32),8,np.uint16));packet,_=rc.encode_modes(rgb,(0,0,32,16))
        with self.assertRaises(ValueError):rc.decode(packet[:-1]+bytes((packet[-1]^1,)),32,16)
        with self.assertRaises(ValueError):rc.decode(packet+b'\0',32,16)
        fields=list(rc.HEADER.unpack_from(packet));fields[-2]+=1
        bad=rc._seal(rc.HEADER.pack(*fields)+packet[rc.HEADER.size:-4])
        with self.assertRaises(ValueError):rc.decode(bad,32,16)
        fields=list(rc.HEADER.unpack_from(packet));fields[7]=257
        bad=rc._seal(rc.HEADER.pack(*fields)+packet[rc.HEADER.size:-4])
        with self.assertRaises(ValueError):rc.decode(bad,32,16)

    def test_palette_range_unused_and_order(self):
        def packet(palette,payload):
            return rc._seal(rc.HEADER.pack(b'HR01',1,2,0,0,2,2,len(palette),4,len(payload))+
                            np.asarray(palette,dtype='<u2').tobytes()+payload)
        valid=struct.pack('<H',3)+b'\x01\x00\x01'
        np.testing.assert_array_equal(rc.decode(packet([1,2],valid+valid),2,2)['words'],[[1,2],[1,2]])
        for colors,row in (([2,1],valid),([1,1],valid),([1,2],struct.pack('<H',2)+b'\x81\x00'),
                           ([1,2],struct.pack('<H',3)+b'\x01\x00\x02')):
            with self.assertRaises(ValueError):rc.decode(packet(colors,row+row),2,2)

    def test_min_choice_and_stateless_repeat(self):
        words=np.tile(np.arange(128,dtype=np.uint16)%2,(32,1));rgb=self.words(words)
        packet,info=rc.choose_patch(rgb,(0,0,128,32))
        self.assertEqual(info['chosen_format'],'HP01')
        self.assertEqual(len(packet),min(info['hp01_bytes'],info['hr01_bytes']))
        np.testing.assert_array_equal(rc.decode_any(packet,128,32)['words'],words)
        rgb=self.words(np.full((32,128),32,np.uint16))
        packet,info=rc.choose_patch(rgb,(0,0,128,32))
        self.assertEqual(info['chosen_format'],'HR01')
        self.assertEqual(packet,rc.choose_patch(rgb,(0,0,128,32))[0])
        np.testing.assert_array_equal(rc.decode_any(packet,128,32)['words'],np.full((32,128),32,np.uint16))




class WrapperTests(unittest.TestCase):
    def test_temporal_patch_does_not_change_anchor_and_bad_patch_is_atomic(self):
        rgb=np.full((32,64,3),(30,40,50),np.uint8)
        enc=rc.hp.gm.Encoder();m=np.full((2,4),16,np.uint8)
        key=enc.prepare(rgb,0,scale_map=m)
        patch,_=rc.choose_patch(rgb,(1,1,31,15))
        wrapper=rc.wrap(key,[patch],64,32)
        rx=rc.Receiver();decoded,_=rx.receive(wrapper)
        reference=rc.hp.gm.Receiver();reference.receive(key)
        for a,b in zip(rx.base._anchor,reference._anchor):np.testing.assert_array_equal(a,b)
        enc.ack(0,epoch=1)
        rgb[8:16,8:16]=[180,170,160]
        residual=enc.prepare(rgb,1,scale_map=m)
        p,_=rc.choose_patch(rgb,(1,1,31,15))
        actual,_=rx.receive(rc.wrap(residual,[p],64,32));reference.receive(residual)
        for a,b in zip(rx.base._anchor,reference._anchor):np.testing.assert_array_equal(a,b)
        np.testing.assert_array_equal(rc.hp.corpus.rgb565(actual)[1:16,1:32],rc.hp.corpus.rgb565(rgb)[1:16,1:32])
        bad=patch[:-1]+bytes((patch[-1]^1,))
        fresh=rc.Receiver()
        with self.assertRaises(ValueError):fresh.receive(rc.wrap(key,[bad],64,32))
        self.assertEqual(fresh.base.last_frame_id,-1)
        bad_base=key[:-1]+bytes((key[-1]^1,))
        with self.assertRaises(ValueError):fresh.receive(rc.wrap(bad_base,[patch],64,32))
        self.assertEqual(fresh.base.last_frame_id,-1)
        self.assertIsNone(fresh.base._anchor)

    def test_overlap_rejected_before_patch_decode(self):
        rgb=np.zeros((16,32,3),np.uint8);enc=rc.hp.gm.Encoder()
        base=enc.prepare(rgb,0,quant_scale=16);patch,_=rc.choose_patch(rgb,(0,0,16,16))
        section=b''.join(struct.pack('<I',len(patch))+patch for _ in range(2))
        packet=rc._seal(rc.FRAME.pack(b'HG01',1,2,len(base),32,16,len(section))+base+section)
        from unittest.mock import patch as mockpatch
        with mockpatch.object(rc,'decode_any',side_effect=AssertionError('must not allocate patches')):
            with self.assertRaises(ValueError):rc.parse_frame(packet,1)

if __name__=='__main__':unittest.main()
