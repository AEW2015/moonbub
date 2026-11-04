#!/usr/bin/env python3
"""Offline complete-sequence transaction and original-HUD replay."""
from pathlib import Path
import json
import numpy as np
import benchmark as b
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def expect_failure(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('expected fail-closed operation')


def main():
    data = b.read_json(HERE / 'results.json')
    assert data['schema'] == 'gamebub-joint-commit-v22'
    for path, digest in data['source_sha256'].items():
        assert b.sha(ROOT / path) == digest, path
    old = {c['scene']: c for c in b.read_json(b.OLD / 'results.json')['cases'] if c['policy'] == 'mandatory'}
    fixed_bytes = {c['scene']: c for c in b.read_json(b.OLD_COMPOSE / 'results.json')['budgets']}
    total = hud_words = full_display_words = yuv_samples = crc_negatives = gate_negatives = quality_vectors = 0
    for case in data['cases']:
        receiver = m.JointReceiver()
        assert len(case['rows']) == 48
        for row in case['rows']:
            assert row['accepted']
            packet, ack = b.raw(row['packet']), b.raw(row['ack'])
            assert len(packet) == row['packet_bytes'] <= 49152
            assert len(ack) == row['ack_bytes']
            base, hud = m.compose.unbind(packet)
            assert len(base) == row['base_bytes'] and len(hud) == row['hud_bytes']
            assert row['wire'] == b.wire_counts(len(packet), len(ack))
            before = receiver.published_snapshot()
            bad = packet[:-1] + bytes([packet[-1] ^ 1])
            expect_failure(lambda: receiver.prepare(bad))
            assert receiver.published_snapshot() == before
            crc_negatives += 1
            task = receiver.prepare(packet)
            assert task.display.shape == (480, 720)
            assert receiver.published_snapshot() == before
            expect_failure(lambda: receiver.present(task, vblank=True))
            assert receiver.published_snapshot() == before
            gate_negatives += 1
            receiver.mark_writes_drained(task)
            expect_failure(lambda: receiver.present(task, vblank=False))
            assert receiver.published_snapshot() == before
            gate_negatives += 1
            assert b.digest(task.display) == row['display_rgb565_sha256']
            assert m.C.reference_tag(task.planes).hex() == row['canonical_yuv_tag']
            assert receiver.present(task, vblank=True) == ack
            assert receiver.retry_ack(packet) == ack
            assert b.digest(receiver.display) == row['display_rgb565_sha256']
            full_display_words += receiver.display.size
            yuv_samples += sum(p.size for p in task.planes)
            for rect, desc in zip(m.hc.RECTANGLES, row['source_original_hud']):
                x, y, w, h = rect
                expected = np.frombuffer(b.raw(desc, b.OLD_CACHE), dtype='<u2').reshape(h, w)
                np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], expected)
                hud_words += w * h
            previous = old[case['scene']]['rows'][row['id']]
            assert row['input_sha256'] == previous['input_sha256']
            assert row['active_rgb565_channel_mse'] == row['active_squared_channel_error'] / row['active_channel_samples']
            if case['policy'] == 'fixed_v20_profiles':
                assert row['packet_bytes'] == fixed_bytes[case['scene']]['rows'][row['id']]['cb21_complete_bytes']
                assert row['active_rgb565_channel_mse'] == previous['active_rgb565_mse']
            if 'v20_source_vector_index' in row:
                vector = old[case['scene']]['vectors'][row['v20_source_vector_index']]
                src = vector['source']
                original = np.frombuffer(b.raw(src['blob'], b.OLD), dtype=src['dtype']).reshape(src['shape'])
                assert b.digest(original) == row['input_sha256']
                error_sum, count, mse = b.mse(m.C.corpus.rgb565(original), receiver.display)
                assert (error_sum, count, mse) == (row['active_squared_channel_error'], row['active_channel_samples'], row['active_rgb565_channel_mse'])
                if case['policy'] == 'fixed_v20_profiles':
                    d = vector['display_rgb565']
                    expected = np.frombuffer(b.raw(d['blob'], b.OLD), dtype=d['dtype']).reshape(d['shape'])
                    np.testing.assert_array_equal(receiver.display, expected)
                quality_vectors += 1
            total += 1
        assert b.summary(case) == next(s for s in data['summary'] if (s['scene'], s['policy']) == (case['scene'], case['policy']))
    assert b.comparisons(data['cases']) == data['comparisons']
    assert total == 192 and hud_words == 192 * 21120 and quality_vectors == 20
    print(json.dumps(dict(actual_joint_decisions=total, exact_original_hud_words=hud_words,
                          sequential_display_hash_words=full_display_words,
                          sequential_canonical_yuv_samples=yuv_samples,
                          independently_recomputed_quality_vectors=quality_vectors,
                          crc_negative_rejections=crc_negatives, write_vblank_gate_rejections=gate_negatives,
                          synchronous_joint_publication_implemented=True,
                          physical_dma_or_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
