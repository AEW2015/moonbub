import unittest

import numpy as np

import fast_coeff as fast


class FastTests(unittest.TestCase):
    def test_coefficient_packets_are_byte_identical(self):
        rng = np.random.default_rng(20261103)
        for rows, width in ((1,1),(3,5),(2,90)):
            for density in (0, .02, .2, 1):
                a = rng.integers(-2048, 2049, (rows*width, 8, 8), dtype=np.int16)
                a[rng.random(a.shape) > density] = 0
                expected = fast.frozen.encode_coefficients(a, width)
                actual = fast.encode_coefficients(a, width)
                self.assertEqual(actual, expected)
                self.assertTrue(np.array_equal(fast.frozen.decode_coefficients(actual, len(a), width), a))

    def test_dc_endpoints_context_boundaries_and_raw(self):
        a = np.zeros((6,8,8), np.int16)
        a[:,0,0] = [-2048,2048,-2048,2048,-2048,2048]
        zz = fast.frozen.frozen.ZIGZAG
        for i in (1,5,6,20,21,63):
            a[1].ravel()[zz[i]] = -2048 if i%2 else 2048
        self.assertEqual(fast.encode_coefficients(a, 3), fast.frozen.encode_coefficients(a, 3))

    def test_complete_ft02_frames_are_byte_identical(self):
        rng = np.random.default_rng(3)
        for h,w in ((2,2),(18,34),(32,48)):
            rgb = rng.integers(0,256,(h,w,3),dtype=np.uint8)
            for scale in (1,8,16,32,128):
                actual = fast.encode(rgb, scale)
                expected = fast.frozen.encode(rgb, scale)
                self.assertEqual(actual, expected)
                self.assertTrue(np.array_equal(fast.frozen.decode(actual), fast.frozen.frozen.reconstruct(rgb, scale)))

    def test_temporal_wire_and_reference_state_are_identical(self):
        from fast_motion import Encoder, frozen
        old,new = frozen.Encoder(epoch=7),Encoder(epoch=7)
        rx = frozen.Receiver(epoch=7)
        rng = np.random.default_rng(6)
        for i in range(6):
            rgb = rng.integers(0,256,(48,64,3),dtype=np.uint8)
            a = old.prepare(rgb,i,quant_scale=8,force_key=i==4)
            b = new.prepare(rgb,i,quant_scale=8,force_key=i==4)
            self.assertEqual(a,b)
            actual,info = rx.receive(b)
            self.assertTrue(np.array_equal(actual,new.prepared_rgb()))
            if i==2:
                old.abort();new.abort()
            else:
                old.ack(i,epoch=info['epoch']);new.ack(i,epoch=info['epoch'])

    def test_fast_encoder_keeps_epoch_and_inflight_checks(self):
        from fast_motion import Encoder
        enc = Encoder(epoch=3)
        enc.prepare(np.zeros((16,16,3),np.uint8),0)
        with self.assertRaises(ValueError):
            enc.prepare(np.zeros((16,16,3),np.uint8),1)
        with self.assertRaises(ValueError):
            enc.ack(0,epoch=2)


if __name__ == '__main__':
    unittest.main()
