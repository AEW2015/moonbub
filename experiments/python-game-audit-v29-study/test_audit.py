import hashlib
import struct
import unittest
import zlib

import audit


def seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def sample_packet():
    rect = (0, 0, 220, 96)  # exactly 21,120 words
    hud_head = audit.HU25.pack(b'HU25', 1, 1, 25, 0, audit.NO_REF, 720, 480,
                               bytes(16), b'h' * 16, 1, 0, 0, 0, 1, 0, 0, 0,
                               *rect, *(0 for _ in range(12)))
    hud = seal(hud_head + b'X')
    gm_head = audit.GM27.pack(b'GM27', 1, 1, 25, 0, audit.NO_REF, 720, 480, 32, 18,
                              bytes(16), b'g' * 16, 1, 0, 1, 1, 1)
    base = seal(gm_head + b'QYCB')
    packet = audit.CP27.pack(b'CP27', 1, 3, 25, 0, 255, 0, len(base), len(hud),
                             hashlib.sha256(base).digest()[:16], hashlib.sha256(hud).digest()[:16])
    return seal(packet + base + hud)


class V29AuditTests(unittest.TestCase):
    def test_cp27_reconciles_complete_size_and_exact_hud_area(self):
        packet = sample_packet()
        parsed = audit.parse_pair(packet)
        self.assertEqual(parsed['bytes'], len(packet))
        self.assertEqual(len(packet), len(parsed['base']) + len(parsed['hud']) + 60)
        self.assertEqual(parsed['hud_meta']['patch_words'], 21_120)
        damaged = bytearray(packet)
        damaged[-5] ^= 1
        with self.assertRaises(ValueError):
            audit.parse_pair(bytes(damaged))

    def test_accepted_parser_rejects_oversize_packet(self):
        packet = sample_packet()
        oversized = packet[:-4] + bytes(49_153 - len(packet)) + packet[-4:]
        with self.assertRaises(ValueError):
            audit.parse_pair(oversized)
        self.assertGreater(len(oversized), audit.CAP)

    def test_metric_and_summary_recompute_integer_totals_and_hud_words(self):
        row = dict(body_bytes=1000, base_bytes=700, hud_bytes=240, binding_bytes=60,
                   hybrid=dict(active_squared_error=300, active_channel_samples=100,
                               active_mse=3.0, hud_word_errors=0), attempts=[], analyses={},
                   paid_base_encode_ms=0.0, base_policy_service_ms=0.0, receive_ms=2.0,
                   selected_background=16)
        self.assertEqual(audit.metric_totals([row]), (300, 100, 3.0, 0))
        summary = audit.summarize_rows([row])
        self.assertEqual(summary['complete_bytes'], 1000)
        self.assertEqual(summary['exact_hud_words'], 21_120)
        row['hybrid']['active_mse'] = 4.0
        with self.assertRaises(ValueError):
            audit.metric_totals([row])

    def test_replay_must_follow_its_own_prior_accepted_tag(self):
        case_rows = [
            dict(id=0, key=True, reference_tag=bytes(16).hex(), reconstructed_tag='aa',
                 hybrid_rgb565_sha256='ha'),
            dict(id=1, key=False, reference_tag='aa', reconstructed_tag='bb',
                 hybrid_rgb565_sha256='hb'),
        ]
        cases = {('s', 'p'): dict(rows=case_rows)}
        replay = dict(schema='gamebub-v29-replay', chains=[dict(scene='s', policy='p', rows=[
            dict(id=0, reference_tag=bytes(16).hex(), decoded_tag='aa', hybrid_rgb565_sha256='ha'),
            dict(id=1, reference_tag='aa', decoded_tag='bb', hybrid_rgb565_sha256='hb'),
        ])], accepted_pairs=384, exact_hud_words=384 * audit.HUD_WORDS, physical_30fps_proven=False)
        audit._verify_replay_chains(replay, cases)
        replay['chains'][0]['rows'][1]['reference_tag'] = 'other'
        with self.assertRaises(ValueError):
            audit._verify_replay_chains(replay, cases)


if __name__ == '__main__':
    unittest.main()
