import unittest,struct,zlib
import numpy as np
import helpers as h
model=h.module('implicit37_test_encoder',h.HERE/'model.py')
decoder=h.module('implicit37_test_decoder',h.HERE/'verify.py')

class ImplicitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=h.HERE.parent/'python-game-canonical-v36-study';data=h.load(folder/'results.json')
        cls.rows=data['cases'][0]['rows'];cls.folder=folder
        cls.old=h.raw(cls.rows[0]['skip']['packet'],folder);cls.packet,_=model.transcode(cls.old)

    def test_actual_key_and_fractional_motion_roundtrip(self):
        folder=self.folder;old=h.load(folder/'results.json')
        rx=decoder.Receiver();baseline=decoder.f.Receiver()
        for row in old['motion_probe']['rows']:
            packet=h.raw(row['skip']['packet'],folder);new,work=model.transcode(packet)
            a,ap,meta=rx.receive(new);b,bp,_=baseline.receive(packet)
            for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
            self.assertLessEqual(len(new),len(packet))

    def test_crc_types_lengths_and_profile_reject(self):
        for bad in (b'',bytearray(self.packet),self.packet+b'\0',self.packet[:-1],self.packet[:-1]+bytes([self.packet[-1]^1])):
            with self.assertRaises(ValueError):decoder.parse(bad)
        fields=list(decoder.HEADER.unpack_from(self.packet));fields[8]=bytes(16)
        bad=decoder.seal(decoder.HEADER.pack(*fields)+self.packet[decoder.HEADER.size:-4])
        with self.assertRaises(ValueError):decoder.parse(bad)

    def test_invalid_output_tag_cannot_publish_and_replay_rejected(self):
        fields=list(decoder.HEADER.unpack_from(self.packet));fields[10]=bytes([1])*16
        bad=decoder.seal(decoder.HEADER.pack(*fields)+self.packet[decoder.HEADER.size:-4])
        rx=decoder.Receiver()
        with self.assertRaises(ValueError):rx.receive(bad)
        self.assertIsNone(rx.ref);self.assertEqual(rx.last,-1)
        rx.receive(self.packet)
        with self.assertRaises(ValueError):rx.receive(self.packet)

    def test_non_skip_input_rejected(self):
        data=h.load(self.folder/'results.json');packet=h.raw(data['cases'][0]['rows'][0]['full']['packet'],self.folder)
        with self.assertRaises(ValueError):model.transcode(packet)

if __name__=='__main__':unittest.main()
