import unittest
import model
import hashlib
import json
import zlib
import numpy as np


def fixture():
    folder = model.HERE.parent / 'python-game-mandatory-hud-study'
    data = json.loads((folder / 'results.json').read_text())
    selected = next(c for c in data['cases'] if c['policy'] == 'mandatory')['vectors'][0]
    def raw(desc):
        data = zlib.decompress((folder / desc['path']).read_bytes())
        if hashlib.sha256(data).hexdigest() != desc['raw_sha256']:
            raise AssertionError('fixture hash')
        return data
    source = selected['source']
    return raw(selected['packet']), np.frombuffer(raw(source['blob']), dtype=source['dtype']).reshape(source['shape'])


class BudgetTests(unittest.TestCase):
    def test_fragment_boundaries_and_controls(self):
        a, b = model.transport_counts(1008, 53), model.transport_counts(1009, 53)
        self.assertEqual(a['fragments'], 1)
        self.assertEqual(b['fragments'], 2)
        self.assertEqual(a['data_forward_bytes'], 1083)
        self.assertEqual(a['packet_credit_reverse_bytes'], 57)
        self.assertEqual(a['frame_forward_control_bytes'], 128)
        self.assertEqual(a['frame_reverse_control_bytes'], 192)
        self.assertEqual(a['hud_ack_reverse_bytes'], 81)

    def test_invalid_budget(self):
        for bad in (0, -1, 1.1, True):
            with self.assertRaises(ValueError):
                model.transport_counts(bad)
        for rate, delay in ((0, 0), (-1, 0), (float('nan'), 1), (8, -1), (8, float('inf'))):
            with self.assertRaises(ValueError):
                model.necessary_network_bound(model.transport_counts(100), rate, delay)

    def test_delay_and_rate_monotonicity(self):
        c = model.transport_counts(40000, 54)
        a = model.necessary_network_bound(c, 8, 0)
        b = model.necessary_network_bound(c, 16, 0)
        d = model.necessary_network_bound(c, 16, 40)
        self.assertLess(b['network_only_stop_wait_ms'], a['network_only_stop_wait_ms'])
        self.assertFalse(d['necessary_30fps_condition'])

    def test_offline_container_rejects_early(self):
        for bad in (b'', bytes(model.OVERHEAD), bytes(2 * model.MAX_COMPONENT + model.OVERHEAD + 1), bytearray(100)):
            with self.assertRaises(ValueError):
                model.unbind(bad)
        self.assertEqual(model.OVERHEAD, 57)

    def test_strip_preserves_exact_inner_and_reference_tags(self):
        original, _ = fixture()
        a = model.codec.identity(original)
        b = model.codec.identity(model.strip_patches(original))
        self.assertEqual(b['patch_count'], 0)
        self.assertEqual(b['patch_bytes'], 0)
        for name in ('inner', 'reference_tag', 'stored_tag', 'frame_id'):
            self.assertEqual(a[name], b[name])
        self.assertNotEqual(a['body_crc'], b['body_crc'])

    def test_pair_identity_and_repaired_outer_crc(self):
        original, rgb = fixture()
        base = model.strip_patches(original)
        packet, _ = model.cache.Sender().prepare(rgb, 0)
        pair = model.bind(base, packet)
        self.assertEqual(model.unbind(pair, enforce_frame_cap=False), (base, packet))
        bad = bytearray(pair)
        bad[model.HEADER.size] ^= 1
        with self.assertRaises(ValueError):
            model.unbind(model.cache.seal(bytes(bad[:-4])), enforce_frame_cap=False)
        other, _ = model.cache.Sender().prepare(rgb, 1)
        with self.assertRaises(ValueError):
            model.bind(base, other)

    def test_over_cap_is_a_separate_admission_gate(self):
        # A valid diagnostic fixture may be inspected with an explicit opt-out;
        # the default cap must reject before any component decoder receives it.
        original, rgb = fixture()
        base = model.strip_patches(original)
        packet, _ = model.cache.Sender().prepare(rgb, 0)
        pair = model.bind(base, packet)
        saved = model.FRAME_CAP
        try:
            model.FRAME_CAP = len(pair) - 1
            with self.assertRaises(ValueError):
                model.unbind(pair)
            self.assertEqual(model.unbind(pair, enforce_frame_cap=False), (base, packet))
        finally:
            model.FRAME_CAP = saved


if __name__ == '__main__':
    unittest.main()
