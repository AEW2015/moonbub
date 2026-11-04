import struct
import unittest
import numpy as np
import model as m


def rgb(seed=1):
    return np.random.default_rng(seed).integers(0, 256, (64, 64, 3), dtype=np.uint8)


def patches(seed=1):
    return (m.ui.hp.encode_patch(rgb(seed), (0, 0, 32, 16)),)


def key(frame=0):
    b, ref, _ = m.base.encode_planes(m.base.ft.rgb_to_planes(rgb()), None,
                                    np.full((4, 4), 16, np.uint8), frame_id=frame)
    h, _ = m.encode_hud(patches(), frame_id=frame, width=64, height=64)
    return m.encode_pair(b, h, epoch=1, frame_id=frame), ref


def following(receiver, frame=1, publish=True, source=0):
    bank = receiver.banks[source]
    b, _, _ = m.base.encode_planes(m.base.ft.rgb_to_planes(rgb(frame + 3)), bank.planes,
                                   np.full((4, 4), 16, np.uint8), frame_id=frame,
                                   reference_id=bank.frame_id, motion_mode='zero')
    h, _ = m.encode_hud(patches(), receiver.hud, frame_id=frame,
                        reference_id=receiver.hud_id, width=64, height=64)
    return m.encode_pair(b, h, epoch=1, frame_id=frame, source_slot=source,
                         destination_slot=1-source if publish else 255,
                         publish=publish, key=False)


def snapshot(r):
    return r.banks, r.hud, r.hud_id, r.hud_tag, r.last_frame_id, r.last_ack


class CombinedTests(unittest.TestCase):
    def receiver(self):
        return m.Receiver(width=64, height=64)

    def test_key_real_sizes_roundtrip_and_ack(self):
        pair, reference = key(); r = self.receiver()
        base, hud, ack = r.receive(pair)
        self.assertEqual(m.PAIR.size + 4, 60)
        self.assertEqual(m.ACK.size + 4, 65)
        self.assertEqual(len(ack), 65)
        self.assertTrue(m.validate_ack(ack, pair)['published'])
        self.assertEqual(r.banks[0].frame_id, 0)
        self.assertIsNone(r.banks[1])
        expected = m.ui.validate_patches(patches(), 64, 64)
        np.testing.assert_array_equal(hud[0]['words'], expected[0]['words'])
        for a, b in zip(base, reference): np.testing.assert_array_equal(a, b)
        self.assertFalse(hud[0]['words'].flags.writeable)

    def test_exact_temporal_hud_selects_hd25_and_binds_content(self):
        h, info = m.encode_hud(patches(), width=64, height=64)
        current, _ = m.decode_hud(h)
        p, info = m.encode_hud(patches(), current, frame_id=1, reference_id=0,
                              width=64, height=64)
        self.assertEqual(info['patches'][0]['selected'], 'HD25')
        self.assertGreater(info['patches'][0]['hd25_work']['encode_ms'], 0)
        decoded, _ = m.decode_hud(p, current, expected_reference_id=0)
        np.testing.assert_array_equal(decoded[0]['words'], current[0]['words'])
        with self.assertRaises(ValueError): m.decode_hud(p, current, expected_reference_id=2)
        changed = [dict(rect=current[0]['rect'], words=current[0]['words'].copy())]
        changed[0]['words'][0, 0] ^= 1
        with self.assertRaises(ValueError): m.decode_hud(p, changed, expected_reference_id=0)

    def test_alternate_publication_and_display_only_nonpublication(self):
        pair, _ = key(); r = self.receiver(); r.receive(pair)
        p = following(r); _, _, ack = r.receive(p)
        self.assertEqual(r.banks[1].frame_id, 1)
        self.assertEqual(r.banks[0].frame_id, 0)
        self.assertEqual(m.validate_ack(ack, p)['destination_slot'], 1)
        banks = r.banks
        p = following(r, frame=2, publish=False, source=1)
        _, _, ack = r.receive(p)
        self.assertEqual(r.banks, banks)
        self.assertEqual(r.hud_id, 2)
        self.assertFalse(m.validate_ack(ack, p)['published'])

    def test_crc_truncation_cap_and_replay_leave_state_untouched(self):
        pair, _ = key(); r = self.receiver(); r.receive(pair); old = snapshot(r)
        for bad in (pair[:-1], pair + b'\0', pair[:-1] + bytes([pair[-1] ^ 1]),
                    bytes(m.CAP + 1), pair):
            with self.assertRaises(ValueError): r.receive(bad)
            self.assertEqual(snapshot(r), old)

    def test_write_and_vblank_gates_never_publish_or_ack(self):
        pair, _ = key(); r = self.receiver(); old = snapshot(r)
        for kw in (dict(write_drained=False), dict(vblank=False), dict(vblank=1)):
            with self.assertRaises(ValueError): r.receive(pair, **kw)
            self.assertEqual(snapshot(r), old)
        r.receive(pair)

    def test_bad_hud_after_valid_base_is_atomic(self):
        pair, _ = key(); r = self.receiver(); r.receive(pair); old = snapshot(r)
        p = following(r); meta = m.parse_pair(p)
        values = list(m.HUD.unpack_from(meta['hud'])); values[9] = b'x' * 16
        forged_hud = m.seal(m.HUD.pack(*values) + meta['hud'][m.HUD.size:-4])
        forged = m.encode_pair(meta['base'], forged_hud, epoch=1, frame_id=1,
                               source_slot=0, destination_slot=1, key=False)
        with self.assertRaises(ValueError): r.receive(forged)
        self.assertEqual(snapshot(r), old)

    def test_source_bank_and_previous_hud_id_both_required(self):
        pair, _ = key(); r = self.receiver(); r.receive(pair)
        p = following(r); meta = m.parse_pair(p)
        wrong = m.encode_pair(meta['base'], meta['hud'], epoch=1, frame_id=1,
                              source_slot=1, destination_slot=0, key=False)
        old = snapshot(r)
        with self.assertRaises(ValueError): r.receive(wrong)
        self.assertEqual(snapshot(r), old)
        # Structurally valid HUD points to frame1 while current accepted HUD0.
        b, _, _ = m.base.encode_planes(m.base.ft.rgb_to_planes(rgb(5)), r.banks[0].planes,
                                      np.full((4, 4), 16, np.uint8), frame_id=2,
                                      reference_id=0, motion_mode='zero')
        h, _ = m.encode_hud(patches(), r.hud, frame_id=2, reference_id=1, width=64, height=64)
        p = m.encode_pair(b, h, epoch=1, frame_id=2, source_slot=0, destination_slot=1, key=False)
        with self.assertRaises(ValueError): r.receive(p)
        self.assertEqual(snapshot(r), old)

    def test_ack_crc_pair_hash_outputs_and_cross_pair_binding(self):
        pair, _ = key(); r = self.receiver(); _, _, ack = r.receive(pair)
        for index in (3, 9, 22, 42, 60):
            bad = bytearray(ack); bad[index] ^= 1
            with self.assertRaises(ValueError): m.validate_ack(bytes(bad), pair)
            forged = m.seal(bytes(bad[:-4]))
            with self.assertRaises(ValueError): m.validate_ack(forged, pair)
        other = following(r)
        with self.assertRaises(ValueError): m.validate_ack(ack, other)

    def test_inner_identity_slots_and_hashes_reject(self):
        pair, _ = key(); meta = m.parse_pair(pair)
        with self.assertRaises(ValueError): m.encode_pair(meta['base'], meta['hud'], epoch=2, frame_id=0)
        with self.assertRaises(ValueError): m.encode_pair(meta['base'], meta['hud'], epoch=1, frame_id=0, source_slot=0)
        with self.assertRaises(ValueError): m.encode_pair(meta['base'], meta['hud'], epoch=1, frame_id=0, publish=False)
        values = list(m.PAIR.unpack_from(pair)); values[9] = b'x' * 16
        bad = m.seal(m.PAIR.pack(*values) + pair[m.PAIR.size:-4])
        with self.assertRaises(ValueError): m.parse_pair(bad)

    def test_empty_hud_and_padding_geometry_and_overlap(self):
        h, _ = m.encode_hud((), width=64, height=64)
        current, _ = m.decode_hud(h)
        self.assertEqual(current, ())
        h, _ = m.encode_hud((), current, frame_id=1, reference_id=0, width=64, height=64)
        self.assertEqual(m.decode_hud(h, current, expected_reference_id=0)[0], ())
        vals = list(m.HUD.unpack_from(h)); vals[17] = 1
        forged = m.seal(m.HUD.pack(*vals))
        with self.assertRaises(ValueError): m.decode_hud(forged, current, expected_reference_id=0)
        with self.assertRaises(ValueError): m.encode_hud(patches() * 2, width=64, height=64)
        pair, _ = key()
        with self.assertRaises(ValueError): m.Receiver(width=32, height=32).receive(pair)


if __name__ == '__main__': unittest.main()
