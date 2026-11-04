import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zlib

import audit


class V26AuditPrimitiveTests(unittest.TestCase):
    def test_nominal_rate_uses_complete_bytes_and_id_rate(self):
        self.assertEqual(audit.projected_mbps(100_000, 48), 0.5)
        self.assertAlmostEqual(audit.projected_mbps(100_000, 48, 60), 1.0)
        with self.assertRaises(ValueError):
            audit.projected_mbps(100_000, 0)

    def test_body_composition_sums_all_declared_byte_classes(self):
        parts = {'video': 1000, 'hud': 211, 'binding': 60, 'outer': 17}
        self.assertEqual(audit.complete_body_bytes(parts), 1288)
        with self.assertRaises(ValueError):
            audit.complete_body_bytes({**parts, 'outer': -1})

    def test_packet_cap_accepts_exact_boundary_and_rejects_one_over(self):
        self.assertTrue(audit.enforce_packet_cap(49_152))
        self.assertFalse(audit.enforce_packet_cap(49_153))
        with self.assertRaises(ValueError):
            audit.enforce_packet_cap(-1)

    def test_thresholds_are_loaded_from_frozen_v25_json_without_rounding(self):
        thresholds = audit.frozen_thresholds()
        frozen = json.loads(audit.V25_AUDIT.read_text())
        for case in frozen['cases']:
            self.assertEqual(thresholds[case['scene']],
                             (case['complete_body_rate_target_Mbps'], case['active_mse_target']))
        self.assertIn('mass-effect-2600', thresholds)
        self.assertIn('mass-effect-7200', thresholds)

    def test_rate_and_quality_both_have_to_meet_the_frozen_pair(self):
        self.assertTrue(audit.passes_frozen_pair(2.0, 10.0, 2.0, 10.0))
        self.assertFalse(audit.passes_frozen_pair(2.0000001, 10.0, 2.0, 10.0))
        self.assertFalse(audit.passes_frozen_pair(2.0, 10.0000001, 2.0, 10.0))

    def test_hud_word_rectangles_total_exactly_21120_and_reject_overlap(self):
        rects = ((22, 54, 160, 24), (22, 82, 160, 24),
                 (168, 360, 320, 24), (168, 390, 240, 24))
        self.assertEqual(audit.exact_hud_words(rects), 21_120)
        with self.assertRaises(ValueError):
            audit.exact_hud_words(((0, 0, 10, 10), (9, 9, 5, 5)))

    def test_pairing_checks_ids_source_hashes_and_reference_tags(self):
        left = [dict(id=i, source_sha256=f's{i}', reference_id=i - 1) for i in range(2)]
        right = [dict(row) for row in left]
        self.assertEqual(audit.compare_lineage(left, right), [])
        right[1]['reference_id'] = 7
        with self.assertRaises(ValueError):
            audit.compare_lineage(left, right)
        self.assertEqual(audit.compare_lineage(left, right, allow_reference_change=True), [1])
        right[0]['source_sha256'] = 'wrong-source'
        with self.assertRaises(ValueError):
            audit.compare_lineage(left, right, allow_reference_change=True)

    def test_archive_check_verifies_stored_and_raw_length_and_hash(self):
        raw = b'bounded retained packet bytes'
        stored = zlib.compress(raw, 9)
        desc = dict(path='objects/packet.zlib', stored_bytes=len(stored),
                    stored_sha256=hashlib.sha256(stored).hexdigest(), raw_bytes=len(raw),
                    raw_sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / desc['path']
            path.parent.mkdir()
            path.write_bytes(stored)
            self.assertEqual(audit.read_object(desc, td), raw)
            desc['stored_bytes'] += 1
            with self.assertRaises(ValueError):
                audit.read_object(desc, td)
            desc['stored_bytes'] -= 1
            desc['raw_sha256'] = '0' * 64
            with self.assertRaises(ValueError):
                audit.read_object(desc, td)

    def test_source_hash_manifest_is_sorted_repo_relative_and_reproducible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'z.py').write_text('z')
            (root / 'a.py').write_text('a')
            first = audit.source_hashes([root / 'z.py', root / 'a.py'], root=root)
            second = audit.source_hashes([root / 'a.py', root / 'z.py'], root=root)
            self.assertEqual(first, second)
            self.assertEqual(list(first), ['a.py', 'z.py'])
            self.assertEqual(first['a.py'], hashlib.sha256(b'a').hexdigest())

    def test_source_pin_verification_rejects_changed_or_escaping_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'input.json').write_text('{}')
            pin = {'input.json': hashlib.sha256(b'{}').hexdigest()}
            self.assertEqual(audit.verify_source_pins(pin, root=root), 1)
            (root / 'input.json').write_text('{ }')
            with self.assertRaises(ValueError):
                audit.verify_source_pins(pin, root=root)
            with self.assertRaises(ValueError):
                audit.verify_source_pins({'../outside': '0' * 64}, root=root)


if __name__ == '__main__':
    unittest.main()
