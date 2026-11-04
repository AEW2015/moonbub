import hashlib
import struct
from pathlib import Path
import tempfile
import unittest
import zlib

import numpy as np
import audit


def seal(data):
    return data + struct.pack('<I', zlib.crc32(data))


def sample_cp27():
    rects = ((22, 54, 160, 24), (22, 82, 160, 24), (168, 360, 320, 24), (168, 390, 240, 24))
    hud_head = audit.HU25.pack(b'HU25', 1, 4, 1, 0, audit.NO_REF, 720, 480,
                               bytes(16), b'h' * 16, 1, 1, 1, 1, 1, 1, 1, 1,
                               *(v for r in rects for v in r))
    hud = seal(hud_head + b'WXYZ')
    gm_head = audit.GM27.pack(b'GM27', 1, 1, 1, 0, audit.NO_REF, 720, 480, 32, 18,
                              bytes(16), b'g' * 16, 1, 0, 1, 1, 1)
    gm = seal(gm_head + b'Q' + b'YCB')
    head = audit.CP27.pack(b'CP27', 1, 3, 1, 0, 255, 0, len(gm), len(hud),
                           hashlib.sha256(gm).digest()[:16], hashlib.sha256(hud).digest()[:16])
    return seal(head + gm + hud)


class V28AuditArithmeticTests(unittest.TestCase):
    def test_actual_cp27_components_crc_and_hashes_reconcile(self):
        packet = sample_cp27()
        parsed = audit.parse_cp27(packet)
        self.assertEqual(parsed['bytes'], len(packet))
        self.assertEqual(parsed['base_meta']['bytes'], len(parsed['base']))
        self.assertEqual(parsed['hud_meta']['patch_words'], audit.HUD_WORDS)
        damaged = bytearray(packet)
        damaged[-5] ^= 1
        with self.assertRaises(ValueError):
            audit.parse_cp27(bytes(damaged))

    def test_rate_projection_uses_exact_nominal_frame_count(self):
        self.assertEqual(audit.projected_mbps(100_000, 48), 0.5)
        self.assertEqual(audit.projected_mbps(100_000, 48, 60), 1.0)
        with self.assertRaises(ValueError):
            audit.projected_mbps(100_000, 0)
        with self.assertRaises(ValueError):
            audit.projected_mbps(100_000, 48, True)

    def test_body_reconciliation_and_exact_complete_cap(self):
        self.assertEqual(audit.complete_body_bytes(10_000, 8_245, 60), 18_305)
        self.assertTrue(audit.under_cap(49_152))
        self.assertFalse(audit.under_cap(49_153))
        for parts in ((10, -1, 60), (True, 0, 60)):
            with self.assertRaises(ValueError):
                audit.complete_body_bytes(*parts)

    def test_quality_stats_are_recomputed_from_integer_totals(self):
        self.assertEqual(audit.quality_stats(dict(active_squared_error=14_383_660,
                                                  active_channel_samples=1_000_000)),
                         (14_383_660, 1_000_000, 14.38366))
        for metric in (dict(active_squared_error=-1, active_channel_samples=1),
                       dict(active_squared_error=1, active_channel_samples=0),
                       dict(active_squared_error=2, active_channel_samples=1, active_mse=1.9)):
            with self.assertRaises(ValueError):
                audit.quality_stats(metric)

    def test_motion_candidate_must_pass_same_reference_quality_and_cap(self):
        self.assertTrue(audit.candidate_eligible(49_152, 100, 100))
        self.assertFalse(audit.candidate_eligible(49_153, 1, 100))
        self.assertFalse(audit.candidate_eligible(10_000, 101, 100))
        with self.assertRaises(ValueError):
            audit.candidate_eligible(-1, 0, 0)

    def test_per_plane_tap_arithmetic_counts_partial_edge_blocks(self):
        # Three luma blocks across and two down; the chroma planes are halved.
        vectors = np.zeros((2, 3, 2), dtype=np.int8)
        vectors[0, 0] = (0, 0)   # one tap
        vectors[0, 1] = (1, 0)   # two taps
        vectors[0, 2] = (1, 1)   # four taps
        vectors[1, 0] = (-2, 0)  # one tap
        vectors[1, 1] = (0, 1)   # two taps
        vectors[1, 2] = (2, 1)   # four taps
        result = audit._tap_work_from_vectors(vectors, [(18, 34), (9, 17), (9, 17)], 16)
        self.assertEqual(result['plane_work'][0]['pixels_by_taps'], {'1': 288, '2': 292, '4': 32})
        self.assertEqual(result['plane_work'][1]['pixels_by_taps'], {'1': 64, '2': 80, '4': 9})
        self.assertEqual(result['reference_sample_fetches'], (288 + 2*292 + 4*32) +
                         2 * (64 + 2*80 + 4*9))

    def test_candidate_work_accounts_for_winners_and_losers(self):
        attempts = [dict(complete_bytes=100, selected=True, encode_ms=4.0, search_blocks=100),
                    dict(complete_bytes=140, selected=False, encode_ms=7.0, search_blocks=300),
                    dict(complete_bytes=49_153, selected=False, encode_ms=2.0, search_blocks=50)]
        result = audit.candidate_work(attempts)
        self.assertEqual(result['attempts'], 3)
        self.assertEqual(result['selected_attempts'], 1)
        self.assertEqual(result['paid_encode_ms'], 13.0)
        self.assertEqual(result['search_blocks'], 450)


class V28AuditProvenanceTests(unittest.TestCase):
    def test_bounded_archive_checks_both_hashes_and_exact_stream_end(self):
        raw = b'retained candidate packet bytes'
        stored = zlib.compress(raw, 9)
        desc = dict(path='objects/candidate.zlib', raw_bytes=len(raw),
                    raw_sha256=hashlib.sha256(raw).hexdigest(),
                    stored_sha256=hashlib.sha256(stored).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / 'objects').mkdir()
            (base / desc['path']).write_bytes(stored)
            self.assertEqual(audit.read_object(desc, base, enforce_repo_root=False), raw)
            for broken in (dict(desc, raw_bytes=1), dict(desc, raw_sha256='0' * 64),
                           dict(desc, stored_sha256='0' * 64)):
                with self.assertRaises(ValueError):
                    audit.read_object(broken, base, enforce_repo_root=False)
            appended = stored + zlib.compress(b'extra')
            (base / desc['path']).write_bytes(appended)
            bad = dict(desc, stored_sha256=hashlib.sha256(appended).hexdigest())
            with self.assertRaises(ValueError):
                audit.read_object(bad, base, enforce_repo_root=False)

    def test_archive_paths_cannot_escape_the_declared_root(self):
        desc = dict(path='../outside', raw_bytes=0, raw_sha256='0' * 64,
                    stored_sha256='0' * 64)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                audit.read_object(desc, Path(td), enforce_repo_root=False)
        with self.assertRaises(ValueError):
            audit.read_object(dict(desc, path='/tmp/outside'), Path('/tmp'), enforce_repo_root=False)

    def test_source_pairing_requires_same_ordered_ids_and_source_hashes(self):
        left = [dict(id=i, source_common_yuv_sha256=f'source-{i}', reference_id=max(i - 1, 0)) for i in range(3)]
        right = [dict(row) for row in left]
        audit.lineage(left, right, ref_field='reference_id')
        right[1]['source_common_yuv_sha256'] = 'different'
        with self.assertRaises(ValueError):
            audit.lineage(left, right, ref_field='reference_id')
        right = [dict(row) for row in left]
        right[2]['id'] = 1
        with self.assertRaises(ValueError):
            audit.lineage(left, right, ref_field='reference_id')

    def test_source_pin_map_is_sorted_repo_relative_and_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'a.py').write_bytes(b'a')
            (root / 'b.py').write_bytes(b'b')
            pins = audit.source_hashes([root / 'b.py', root / 'a.py'], root=root)
            self.assertEqual(list(pins), ['a.py', 'b.py'])
            self.assertEqual(pins['a.py'], hashlib.sha256(b'a').hexdigest())
            (root / 'a.py').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                audit.verify_source_hashes(pins, root=root)

    def test_audit_output_hash_inventory_excludes_its_own_outputs(self):
        paths = ['inputs.json', 'audit.py', 'audit.json', 'audit.log']
        self.assertEqual(audit.audit_input_paths(paths), ['audit.py', 'inputs.json'])


if __name__ == '__main__':
    unittest.main()
