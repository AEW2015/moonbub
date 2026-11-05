"""Independent frame-adapter rejection and state-publication tests."""
import unittest,struct
import helpers as h
f=h.module('binary38_test_frame',h.HERE/'frame_verify.py')
d=h.module('binary38_test_decoder',h.HERE/'decoder.py')

class FrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=h.load(h.HERE/'results.json');cls.packet=h.raw(data['cases'][0]['rows'][0]['packet'])
    def test_valid_selected_frame_and_replay_failure(self):
        rx=f.Receiver();planes,patches,meta,count=rx.receive(self.packet)
        self.assertEqual(count,3);self.assertEqual(sum(p['words'].size for p in patches),21120)
        with self.assertRaises(ValueError):rx.receive(self.packet)
    def test_corruption_and_resealed_identity_no_publication(self):
        fields=list(f.HEADER.unpack_from(self.packet));fields[8]=bytes(16)
        malformed=f.seal(f.HEADER.pack(*fields)+self.packet[f.HEADER.size:-4])
        for packet in (malformed,self.packet[:-1],bytearray(self.packet)):
            rx=f.Receiver()
            with self.assertRaises(ValueError):rx.receive(packet)
            self.assertIsNone(rx.frozen.ref);self.assertEqual(rx.frozen.last,-1)
    def test_valid_crc_wrong_arithmetic_bitcount_fails(self):
        data=h.load(h.HERE/'results.json');trial=data['cases'][0]['rows'][0]['attempts'][0]['trials'][0]
        packet=h.raw(trial['packet']);body=bytearray(packet[:-4]);k0,k1,bits=struct.unpack_from('<BBI',body,d.FRAME.size)
        struct.pack_into('<BBI',body,d.FRAME.size,k0,k1,bits+8);bad=f.seal(bytes(body))
        with self.assertRaises(ValueError):d.decode(bad,5400,90)

if __name__=='__main__':unittest.main()
