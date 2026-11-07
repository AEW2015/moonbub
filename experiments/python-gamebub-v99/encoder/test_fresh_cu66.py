import importlib.util
import gzip
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location('v99_test_fresh', Path(__file__).with_name('fresh_cu66.py'))
encoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(encoder)


class FreshCurrentCU66Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = [np.full((480, 720, 3), v, np.uint8) for v in (40, 45, 220)]
        # A visible local discontinuity exercises non-DC reconstruction too.
        cls.frames[2][170:245, 211:297] = (240, 30, 100)
        cls.report = encoder.encode_sequence(cls.frames, quant_scale=16, clip_id='fresh-scene-change')
        cls.deps = encoder.dependencies()

    def test_causal_scene_change_and_exact_expected(self):
        rows = self.report['records']
        self.assertEqual([r['key'] for r in rows], [True, False, False])
        self.assertEqual([r['reference_id'] for r in rows], [0xffffffff, 0, 1])
        self.assertTrue(all(r['accepted'] and r['ack_verified'] for r in rows))
        self.assertTrue(all(r['adapter_exact_checked'] for r in rows))
        self.assertEqual(len(set(r['expected']['canonical_tag'] for r in rows)), 3)
        for row, source in zip(rows, self.frames, strict=True):
            self.assertEqual(row['packet'][:4], b'CU66')
            self.assertEqual(row['source_rgb_sha256'], encoder.digest(source.tobytes()))
            self.assertEqual(row['expected']['canonical_sha256'], encoder.digest(row['canonical_bytes']))
            self.assertEqual(row['expected']['rgb565_sha256'], encoder.digest(row['rgb565_bytes']))
            self.assertEqual(len(row['canonical_bytes']), 518400)
            self.assertEqual(len(row['rgb565_bytes']), 691200)
            self.assertEqual(row['rtl_components']['operations'].shape, (8100,))
            self.assertTrue(set(row['rtl_components']['operations']) <= {0, 1, 2})

    def test_header_crc_rejection(self):
        packet = bytearray(self.report['records'][0]['packet'])
        packet[10] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC'):
            encoder.validate_native_packet(bytes(packet))

    def test_output_tag_rejection_does_not_publish(self):
        receiver = self.deps['receiver'].Receiver('CU66')
        wire = self.deps['wire']
        packet = self.report['records'][0]['packet']
        outer = list(wire.OUTER.unpack_from(packet))
        outer[10] = b'\x01' * 16
        changed = encoder.seal(wire.OUTER.pack(*outer) + packet[wire.OUTER.size:-4])
        with self.assertRaisesRegex(ValueError, 'output tag'):
            receiver.receive(changed)
        self.assertIsNone(receiver.ref)
        self.assertEqual(receiver.last, -1)
        receiver.receive(packet)
        self.assertEqual(receiver.last, 0)

    def test_nonzero_motion_capability_reject(self):
        with self.assertRaisesRegex(ValueError, 'zero-motion'):
            encoder.encode_candidate(self.frames[0], motion_mode='global')
        wire = self.deps['wire']
        packet = self.report['records'][1]['packet']
        outer = list(wire.OUTER.unpack_from(packet))
        inner = bytearray(packet[wire.OUTER.size:wire.OUTER.size+outer[11]])
        fields = wire.INNER.unpack_from(inner)
        self.assertEqual(fields[12], 3)
        inner[wire.INNER.size+fields[11]+1] = 1
        inner = encoder.seal(bytes(inner[:-4]))
        changed = encoder.seal(wire.OUTER.pack(*outer)+inner+packet[wire.OUTER.size+outer[11]:-4])
        with self.assertRaisesRegex(ValueError, 'zero-motion'):
            encoder.validate_native_packet(changed)

    def test_supported_quantizers_and_native_bounds(self):
        for q in (8, 32):
            row = encoder.encode_candidate(self.frames[0], quant_scale=q)
            self.assertTrue(row['cap_fit'])
            encoder.validate_native_packet(row['packet'])
        for q in (True, 64, '16'):
            with self.assertRaisesRegex(ValueError, 'scales8/16/32'):
                encoder.encode_candidate(self.frames[0], quant_scale=q)

    def test_disk_ledger_has_full_exact_golden_blobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = encoder.encode_sequence(self.frames[:1], output_dir=temporary)
            row = report['records'][0]
            self.assertTrue(Path(report['ledger_path']).is_file())
            for kind in ('canonical', 'hud', 'rgb565'):
                self.assertEqual(gzip.decompress(Path(row[kind+'_path']).read_bytes()), row[kind+'_bytes'])
                self.assertEqual(row[kind+'_compression'], 'gzip-mtime0')
            with np.load(row['rtl_components_path'], allow_pickle=False) as components:
                self.assertEqual(components['qmap'].shape, (338,))
                self.assertEqual(components['coefficients_y'].shape, (5400, 64))
                self.assertEqual(components['hud'].tobytes(), row['rtl_components']['hud_envelope'])

    def test_cap_failure_is_accounted_and_forces_new_key(self):
        noisy = np.random.default_rng(66).integers(0, 256, (480, 720, 3), dtype=np.uint8)
        report = encoder.encode_sequence([self.frames[0], noisy, self.frames[1]], quant_scale=8)
        self.assertEqual(report['input_frames'], 3)
        self.assertEqual(report['rejected_frames'], 1)
        self.assertFalse(report['records'][1]['accepted'])
        self.assertGreater(report['records'][1]['bytes'], encoder.CAP)
        self.assertEqual(report['records'][1]['packet'][:4], b'CU66')
        self.assertFalse(report['records'][1]['ack_verified'])
        self.assertIsNone(report['outputs_rgb565'][1])
        self.assertTrue(report['records'][2]['key'])
        self.assertEqual(report['records'][2]['reference_id'], 0xffffffff)
        self.assertTrue(report['records'][2]['ack_verified'])


if __name__ == '__main__':
    unittest.main()
