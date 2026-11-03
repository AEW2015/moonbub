"""Independent quantizer/edge fixtures and adversarial MP01 packet tests."""
import struct
import unittest
import zlib

import numpy as np

import med_codec as med
import codec


def frame(data, *, w=16, h=16, q=1, mode=5, predictor=1):
    payload = codec.TILE_HEADER.pack(mode,len(data))+data
    body = med.HEADER.pack(med.MAGIC,1,q,predictor,w,h,1,len(payload))+payload
    return body+struct.pack('<I',zlib.crc32(body))


def recalc(data):
    return bytes(data[:-4])+struct.pack('<I',zlib.crc32(data[:-4]))


class PredictorTests(unittest.TestCase):
    def test_exact_all_families_quantizers_edges(self):
        rng = np.random.default_rng(20261103)
        yy,xx = np.mgrid[:33,:47]
        images = [np.zeros((33,47),np.uint16),np.full((1,1),65535,np.uint16),
                  rng.integers(0,65536,(33,47),dtype=np.uint16),
                  (((xx%32)<<11)|((yy%64)<<5)|(xx%32)).astype(np.uint16),
                  np.where((xx+yy)%2,65535,0).astype(np.uint16),
                  np.full((1,47),0xf800,np.uint16),np.full((33,1),0x07e0,np.uint16)]
        for predictor in ('above','med'):
            for q in (1,2,3,4,7,8,16,32):
                for image in images:
                    with self.subTest(predictor=predictor,q=q,shape=image.shape):
                        packet = med.encode(image,q,predictor)
                        np.testing.assert_array_equal(med.decode(packet),codec.quantize(image,q))
                        h,w = image.shape
                        self.assertLessEqual(len(packet),med.HEADER.size+4+2*w*h+3*((w+15)//16)*((h+15)//16))

    def test_predictor_known_values_and_selected_mode(self):
        # MED cases upperleft>=max ->min, <=min ->max, interior a+b-c.
        for a,b,c,want in ((2,4,5,2),(2,4,1,4),(2,4,3,3)):
            channel = np.array([[c,b],[a,0]],np.int16)
            self.assertEqual(int(med._predict_all(channel,1)[1,1]),want)
        yy,xx = np.mgrid[:16,:16]
        image = ((np.minimum(xx+yy,31)<<11)|((xx+yy)<<5)|np.minimum(xx+yy,31)).astype(np.uint16)
        packet = med.encode(image,1,'med')
        self.assertEqual(packet[med.HEADER.size],5)
        np.testing.assert_array_equal(med.decode(packet),image)
        self.assertEqual(med.stats(packet)['modes'],{'predicted_zero_run':1})

    def test_zero_runs_cross_rows_with_predictor_state(self):
        # Red first pixel+1, remaining255 residuals0; above/left propagates1
        # through the full tile, unlike rowzero predictor, which would clear.
        bits = '1'+'01'+'0'+format(254,'08b')+('0'+format(255,'08b'))*2
        data = b'\0\0\0'+codec._pack_bits_string(bits)
        for predictor in (0,1):
            out = med.decode(frame(data,predictor=predictor))
            np.testing.assert_array_equal(out,np.full((16,16),1<<11,np.uint16))
        zeros = b'\0\0\0'+codec._pack_bits_string(('0'+'11111111')*3)
        np.testing.assert_array_equal(med.decode(frame(zeros)),np.zeros((16,16),np.uint16))

    def test_hostile_runs_channels_padding_and_rice(self):
        for data,w,h in ((b'\0\0\0'+codec._pack_bits_string('0'+'11111111'),2,2),
                         (b'\0\0\0'+codec._pack_bits_string('11'),16,16),
                         (bytes([7,0,0])+bytes(8),16,16),
                         (b'\0\0\0'+codec._pack_bits_string('1'+'0'*15+'0000000'),16,16)):
            with self.assertRaises(ValueError):
                med.decode(frame(data,w=w,h=h))
        valid = b'\0\0\0'+codec._pack_bits_string(('0'+'11111111')*3)
        bad = bytearray(valid); bad[-1] |= 1
        with self.assertRaises(ValueError):med.decode(frame(bad))
        with self.assertRaises(ValueError):med.decode(frame(valid+b'\0'))

    def test_crc_profile_lengths_and_indices(self):
        packet = med.encode(np.zeros((16,16),np.uint16))
        for at in range(len(packet)):
            bad = bytearray(packet);bad[at] ^= 1
            with self.assertRaises(ValueError):med.decode(bad)
        for n in range(len(packet)):
            with self.assertRaises(ValueError):med.decode(packet[:n])
        with self.assertRaises(ValueError):med.decode(packet+b'\0')
        for at,value in ((0,0),(4,2),(5,0),(6,2),(7,0),(11,0),(med.HEADER.size,6)):
            bad = bytearray(packet);bad[at]=value
            with self.assertRaises(ValueError):med.decode(recalc(bad))
        with self.assertRaises(ValueError):
            med.decode(frame(np.full((16,16),31<<11,dtype='<u2').tobytes(),q=2,mode=0))
        with self.assertRaises(ValueError):med.encode(np.zeros((1,1),np.uint16),predictor='bad')

    def test_valid_crc_mutations_are_bounded(self):
        rng = np.random.default_rng(17)
        yy,xx = np.mgrid[:16,:16]
        packet = med.encode(((yy<<5)|xx).astype(np.uint16),2)
        for _ in range(200):
            bad = bytearray(packet)
            at = int(rng.integers(0,len(bad)-4));bad[at] ^= int(rng.integers(1,256))
            try:
                out = med.decode(recalc(bad))
                self.assertLessEqual(out.size,codec.MAX_DIM**2)
                self.assertEqual(out.dtype,np.uint16)
            except ValueError:
                pass


if __name__ == '__main__':
    unittest.main()
