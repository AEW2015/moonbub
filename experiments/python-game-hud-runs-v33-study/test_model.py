import struct,unittest
import numpy as np
import model as m
import decoder as d

class HudTests(unittest.TestCase):
    def channel(self,a,scheme,k=None):
        a=np.asarray(a,np.uint16)
        if scheme==0:symbols=a;runs=[]
        elif scheme==1:
            nz=np.flatnonzero(a);symbols=a[nz];runs=np.diff(np.r_[-1,nz,len(a)])-1
        else:
            starts=np.r_[0,np.flatnonzero(a[1:]!=a[:-1])+1];symbols=a[starts];runs=np.diff(np.r_[starts,len(a)])-1
        stream,_=m.old._huff_encode(symbols) if len(symbols) else (b'',{})
        rk,nb,bits=m._rice_encode(runs)
        if k is not None:
            rk=k;text=''.join('0'*(int(x)>>k)+'1'+(format(int(x)&((1<<k)-1),f'0{k}b') if k else '') for x in runs)
            nb=len(text);bits=m._bits_blob(text)
        return m.CHANNEL.pack(scheme,rk,len(symbols),len(stream),nb)+stream+bits

    def test_all_channel_schemes_and_rice_parameters(self):
        rng=np.random.default_rng(33)
        fixtures=[np.zeros(21120,np.uint16),np.full(21120,252,np.uint16),rng.integers(0,253,1000),np.r_[np.zeros(600),[1,2,1],np.zeros(131),[3]]]
        for a in fixtures:
            for scheme in (0,1,2):
                data=self.channel(a,scheme);out,end=d.decode_channel(data,0,len(a),252)
                np.testing.assert_array_equal(out,a);self.assertEqual(end,len(data))
            selected,work=m._channel_encode(a);out,end=d.decode_channel(selected,0,len(a),252);np.testing.assert_array_equal(out,a)
        for k in range(15):
            a=np.r_[np.zeros(120),[4],np.zeros(140)]
            data=self.channel(a,1,k);out,_=d.decode_channel(data,0,len(a),252);np.testing.assert_array_equal(out,a)

    def test_malformed_channel_lengths_order_coverage_padding(self):
        a=np.r_[np.zeros(43),[1,3],np.zeros(40),[2]];data=self.channel(a,1)
        for n in range(len(data)):
            with self.assertRaises(ValueError):d.decode_channel(data[:n],0,len(a),252)
        fields=list(m.CHANNEL.unpack_from(data))
        for index,value in ((0,3),(1,15),(2,len(a)+1),(3,0),(4,16*len(a)+2)):
            bad=fields.copy();bad[index]=value
            with self.assertRaises(ValueError):d.decode_channel(m.CHANNEL.pack(*bad)+data[m.CHANNEL.size:],0,len(a),252)
        # Exact run coverage rejects decoding either fewer or more output words.
        for count in (len(a)-1,len(a)+1):
            with self.assertRaises(ValueError):d.decode_channel(data,0,count,252)
        # Truncated constant symbol declaration, duplicate/oversubscribed trees.
        for stream in (struct.pack('<HI',1,0)+bytes([1,2]),struct.pack('<HI',3,3)+bytes([1,1,2,1,3,1])+b'\x00',struct.pack('<HI',2,2)+bytes([1,1,1,1])+b'\x00'):
            with self.assertRaises(ValueError):d._huffman(stream,3,252)
        constant=self.channel(np.zeros(40,np.uint16),1)
        bad=bytearray(constant);bad[-1]|=1
        if m.CHANNEL.unpack_from(constant)[4]%8:
            with self.assertRaises(ValueError):d.decode_channel(bytes(bad),0,40,252)
        for scheme,symbols,runs in ((1,[0],[0,2]),(2,[2,2],[0,1])):
            stream,_=m.old._huff_encode(symbols);k,nb,bits=m._rice_encode(runs)
            bad=m.CHANNEL.pack(scheme,k,len(symbols),len(stream),nb)+stream+bits
            with self.assertRaises(ValueError):d.decode_channel(bad,0,3,252)
        # Unterminated unary is checked before any unbounded expansion.
        bad=m.CHANNEL.pack(1,0,0,0,8)+b'\x00'
        with self.assertRaises(ValueError):d.decode_channel(bad,0,3,252)

    def test_patch_modes_and_crc_reference_range(self):
        rng=np.random.default_rng(333);ref=rng.integers(0,65536,(8,32),dtype=np.uint16);a=ref^np.uint16(1)
        for mode,pred,prefix in ((0,None,b''),(1,ref,b''),(9,ref,b''),(2,m.h.predict(ref,1,0),struct.pack('<bb',1,0)),(10,m.h.predict(ref,-1,1),struct.pack('<bb',-1,1))):
            payload,_=m._encode_patch(a,pred,mode,prefix);packet=m._pack_patch(a,ref,mode,payload)
            np.testing.assert_array_equal(d.decode_patch(packet,None if mode==0 else ref),a)
            if mode:
                for wrong in (None,ref^1):
                    with self.assertRaises(ValueError):d.decode_patch(packet,wrong)
            bad=bytearray(packet);bad[-1]^=1
            with self.assertRaises(ValueError):d.decode_patch(bytes(bad),ref)
        # Tiled motion prefix is parsed using the unchanged bounded HD25 grammar.
        count=2;prefix=m.h.TILE.pack(16,8,4,0,count)+struct.pack('<I',4)+bytes(4)
        pred,n=m.old._motion_reference(ref,3,prefix,32,8)
        payload,_=m._encode_patch(a,pred,11,prefix);packet=m._pack_patch(a,ref,11,payload)
        np.testing.assert_array_equal(d.decode_patch(packet,ref),a)
        bad=bytearray(packet);bad[m.h.HEADER.size]=15;bad=m.p.seal(bytes(bad[:-4]))
        with self.assertRaises(ValueError):d.decode_patch(bad,ref)

    def test_outer_dispatch_and_exact_v32_fallback(self):
        ref=None
        for fid in range(3):
            a=np.full((8,32),0x39e7,np.uint16) if ref is None else ref[0]['words']^np.uint16(1)
            full=m.p.ui.hp.encode_patch(m.p.base.C.corpus.expand565(a),(0,0,32,8))
            old,_=m.p.encode_hud((full,),ref,epoch=25,frame_id=fid,reference_id=m.p.NO_REF if ref is None else fid-1,motion=False,width=720,height=480)
            old32,_=m.old.encode_hud(old,ref,expected_reference_id=None if ref is None else fid-1)
            packet,work=m.encode_hud(old,old32,ref,expected_reference_id=None if ref is None else fid-1)
            self.assertLessEqual(len(packet),len(old32));out,_=m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=None if ref is None else fid-1)
            np.testing.assert_array_equal(out[0]['words'],a)
            if len(packet)==len(old32):self.assertEqual(packet,old32)
            if fid:
                with self.assertRaises(ValueError):m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=999)
                wrong=[dict(rect=ref[0]['rect'],words=ref[0]['words']^np.uint16(1))]
                with self.assertRaises(ValueError):m.decode_hud(packet,wrong,expected_epoch=25,expected_reference_id=fid-1)
            # Force explicit HX33 so semantic rejection occurs after valid CRC.
            payload,_=m._encode_patch(a,None,0);hs=m._pack_patch(a,None,0,payload)
            fields=list(m.p.HUD.unpack_from(old));fields[0]=b'HX33';fields[10]=len(hs);fields[14]=4
            explicit=m.p.seal(m.p.HUD.pack(*fields)+hs)
            out,_=m.decode_hud(explicit,ref,expected_epoch=25,expected_reference_id=None if ref is None else fid-1);np.testing.assert_array_equal(out[0]['words'],a)
            with self.assertRaises(ValueError):m.decode_hud(explicit,ref,expected_epoch=24,expected_reference_id=fid-1)
            bad=bytearray(hs);bad[5]=255;bad=m.p.seal(bytes(bad[:-4]))
            with self.assertRaises(ValueError):m.decode_hud(m.p.seal(m.p.HUD.pack(*fields)+bad),ref,expected_epoch=25,expected_reference_id=fid-1)
            fields[14]=5
            with self.assertRaises(ValueError):m.decode_hud(m.p.seal(m.p.HUD.pack(*fields)+hs),ref,expected_epoch=25,expected_reference_id=fid-1)
            ref=out

if __name__=='__main__':unittest.main()
