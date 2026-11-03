import struct
import unittest
import zlib

import numpy as np

import motion_codec as mc


class MotionTests(unittest.TestCase):
    def test_key_matches_frozen_transform_and_repeat_reconstructs_exactly(self):
        rgb = np.random.default_rng(1).integers(0, 256, (32, 48, 3), dtype=np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        for i in range(4):
            packet = enc.prepare(rgb, i, quant_scale=16)
            expected = enc.prepared_rgb()
            actual, info = dec.receive(packet)
            self.assertTrue(np.array_equal(actual, expected))
            if i == 0:
                self.assertTrue(np.array_equal(actual, mc.ft.reconstruct(rgb, 16)))
                self.assertTrue(info['key'])
            else:
                self.assertFalse(info['key'])
            enc.ack(i, epoch=enc.epoch)

    def test_ack_loss_requires_key_and_recovers(self):
        rgb = np.full((16, 16, 3), 80, np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        dec.receive(enc.prepare(rgb, 0))
        enc.abort()  # Receiver committed but ACK was lost.
        packet = enc.prepare(rgb+1, 1)
        _, info = dec.receive(packet)
        self.assertTrue(info['key'])
        enc.ack(1, epoch=enc.epoch)
        with self.assertRaises(ValueError):
            enc.ack(0, epoch=enc.epoch)

    def test_no_advance_without_ack_and_private_references(self):
        rgb = np.full((16, 16, 3), 70, np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        packet = enc.prepare(rgb, 0)
        with self.assertRaises(ValueError):
            enc.prepare(rgb, 1)
        actual, _ = dec.receive(packet)
        actual[:] = 0
        enc.ack(0, epoch=enc.epoch)
        packet = enc.prepare(rgb, 1)
        rebuilt, _ = dec.receive(packet)
        self.assertTrue(np.array_equal(rebuilt, enc.prepared_rgb()))

    def test_loss_corruption_replay_and_session_reset(self):
        rgb = np.full((16, 32, 3), 80, np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        p0 = enc.prepare(rgb, 0)
        dec.receive(p0); enc.ack(0, epoch=enc.epoch)
        packet = bytearray(enc.prepare(rgb+2, 1))
        packet[-1] ^= 1
        with self.assertRaises(ValueError):
            dec.receive(bytes(packet))
        self.assertEqual(dec.reference_id, 0)
        enc.abort()
        p2 = enc.prepare(rgb+3, 2)
        dec.receive(p2); enc.ack(2, epoch=enc.epoch)
        with self.assertRaises(ValueError):
            dec.receive(p0)
        with self.assertRaises(ValueError):
            mc.Receiver(epoch=2).receive(p2)
        # An undelivered packet cannot create a reference.
        enc.prepare(rgb+4, 3); enc.abort()
        packet = enc.prepare(rgb+5, 4)
        _, info = dec.receive(packet)
        self.assertTrue(info['key'])

    def test_motion_search_and_border_rule(self):
        reference = np.random.default_rng(2).integers(0, 256, (80, 96), dtype=np.int16)
        current = np.roll(reference, 4, axis=1)
        self.assertEqual(mc.estimate_motion(current, reference), (-4, 0))
        predicted = mc.predict([reference, reference[::2, ::2], reference[::2, ::2]], -4, 0)
        self.assertTrue(np.array_equal(predicted[0][:, :4], np.repeat(reference[:, :1], 4, axis=1)))

    def test_valid_crc_bad_vector_and_identity(self):
        enc = mc.Encoder()
        packet = enc.prepare(np.zeros((16, 16, 3), np.uint8), 0)
        fields = list(mc.HEADER.unpack_from(packet))
        fields[8] = 1  # Invalid odd motion vector, even if CRC is repaired.
        body = mc.HEADER.pack(*fields)+packet[mc.HEADER.size:-4]
        with self.assertRaises(ValueError):
            mc.Receiver().receive(body+struct.pack('<I', zlib.crc32(body)))
        for frame_id in (-1, mc.NO_REF):
            with self.assertRaises(ValueError):
                mc.Encoder().prepare(np.zeros((16, 16, 3), np.uint8), frame_id)

    def test_prediction_uses_reconstructed_reference(self):
        rgb = np.random.default_rng(7).integers(0, 256, (18, 34, 3), dtype=np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        packet = enc.prepare(rgb, 0, quant_scale=32)
        dec.receive(packet); enc.ack(0, epoch=enc.epoch)
        source = mc.ft.rgb_to_planes(rgb)
        self.assertTrue(any(np.any(a != b) for a, b in zip(source, enc._reference)))
        packet = enc.prepare(rgb, 1, quant_scale=32, mode='zero')
        count = mc.LENGTH.unpack_from(packet, mc.HEADER.size)[0]
        payload = packet[mc.HEADER.size+4:mc.HEADER.size+4+count]
        c = mc.cc.decode_coefficients(payload, ((18+7)//8)*((34+7)//8), (34+7)//8)
        self.assertTrue(np.any(c != 0))  # Repeating the original is not a zero residual against its lossy reconstruction.
        actual, _ = dec.receive(packet)
        self.assertTrue(np.array_equal(actual, enc.prepared_rgb()))

    def test_missing_reference_rejects_without_commit(self):
        rgb = np.full((18, 34, 3), 250, np.uint8)
        enc, dec = mc.Encoder(), mc.Receiver()
        packet = enc.prepare(rgb, 0); dec.receive(packet); enc.ack(0, epoch=enc.epoch)
        delta = enc.prepare(rgb-230, 1)
        empty = mc.Receiver()
        with self.assertRaises(ValueError):
            empty.receive(delta)
        self.assertIsNone(empty.reference_id)
        actual, _ = dec.receive(delta)
        self.assertTrue(np.array_equal(actual, enc.prepared_rgb()))

    def test_stale_ack_from_previous_epoch_cannot_commit(self):
        enc = mc.Encoder(epoch=2)
        enc.prepare(np.zeros((16, 16, 3), np.uint8), 0)
        with self.assertRaises(ValueError):
            enc.ack(0, epoch=1)
        self.assertIsNone(enc.reference_id)
        self.assertIsNotNone(enc._pending)

    def test_perfect_frame_benchmark_is_defined(self):
        import importlib.util
        from pathlib import Path
        spec = importlib.util.spec_from_file_location('motion_benchmark_test', Path(__file__).with_name('benchmark.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rgb = np.zeros((16, 16, 3), np.uint8)
        scene = {'frames': [rgb], 'manifest': {'frame_sha256': ['fixture'], 'active_rects': [[0, 0, 16, 16]]},
                 'jpeg': {'50': {'pooled_active_psnr_db': None}}}
        row = module.run_profile(scene, 16, 'intra', 1)
        self.assertTrue(row['exact_committed_frames'])
        self.assertIsNone(row['pooled_active_psnr_db_committed_frames'])
        self.assertIsNone(row['nearest_jpeg_quality_by_psnr'])

    def test_encoded_motion_compensates_known_pan(self):
        from PIL import Image
        base = np.random.default_rng(5).integers(30, 220, (10, 12), dtype=np.uint8)
        gray = np.asarray(Image.fromarray(base).resize((96, 80), Image.Resampling.BILINEAR))
        first = np.repeat(gray[..., None], 3, axis=2)
        second = np.concatenate((np.repeat(first[:, :1], 4, axis=1), first[:, :-4]), axis=1)
        sizes = {}
        for mode in ('zero', 'global'):
            enc, dec = mc.Encoder(), mc.Receiver()
            packet = enc.prepare(first, 0, quant_scale=8)
            dec.receive(packet); enc.ack(0, epoch=1)
            packet = enc.prepare(second, 1, quant_scale=8, mode=mode)
            actual, info = dec.receive(packet)
            self.assertTrue(np.array_equal(actual, enc.prepared_rgb()))
            sizes[mode] = len(packet)
            if mode == 'global':
                self.assertEqual((info['dx'], info['dy']), (-4, 0))
        self.assertLess(sizes['global'], sizes['zero'])


if __name__ == '__main__':
    unittest.main()
