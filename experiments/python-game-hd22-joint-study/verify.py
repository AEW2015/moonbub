#!/usr/bin/env python3
"""Offline actual-profile replay, old-profile rejection and work parity."""
from pathlib import Path
import json
import numpy as np
import benchmark as b
import model as m

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def fails(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('expected fail-closed operation')


def main():
    data = b.load(HERE / 'results.json')
    assert data['schema'] == 'gamebub-integrated-hd22-v23'
    for path, expected in data['source_sha256'].items():
        assert b.sha(ROOT / path) == expected, path
    old = {c['scene']: c for c in b.load(b.OLD / 'results.json')['cases'] if c['policy'] == 'mandatory'}
    v22 = b.load(b.V22 / 'results.json')
    previous = {(c['scene'], c['policy']): c for c in v22['cases']}
    older = b.load_module('joint23_old_profile_check', b.V22 / 'model.py')
    total = words = full_words = yuv_samples = negatives = gates = cross_profiles = quality_checks = spans = 0
    shared_contexts = shared_forwards = plain_contexts = plain_forwards = 0
    for case in data['cases']:
        receiver = m.JointReceiver()
        assert len(case['rows']) == 48
        for row in case['rows']:
            assert row['accepted']
            packet, ack = b.raw(row['packet']), b.raw(row['ack'])
            assert len(packet) == row['packet_bytes'] <= 49152
            assert len(ack) == row['ack_bytes'] == 134
            assert packet[:4] == b'CP23' and ack[:4] == b'JA23'
            base, hud = m.compose.unbind(packet)
            assert hud[:4] == b'HC22'
            assert len(base) == row['base_bytes'] and len(hud) == row['hud_bytes']
            assert row['wire'] == b.wire_counts(len(packet), len(ack))
            fails(lambda: older.compose.unbind(packet))
            fails(lambda: older.parse_ack(ack))
            cross_profiles += 2
            meta = m.hc.parse(hud)
            for kind, piece in zip(meta['modes'], meta['pieces']):
                if kind == m.hc.DELTA:
                    assert piece[:4] == b'HD22'
                    spans += m.hc.hd.inspect(piece)['mode'] == m.hc.hd.SPAN_XOR
            before = receiver.published_snapshot()
            corrupt = packet[:-1] + bytes([packet[-1] ^ 1])
            fails(lambda: receiver.prepare(corrupt))
            assert receiver.published_snapshot() == before
            negatives += 1
            task = receiver.prepare(packet)
            assert task.display.shape == (480, 720)
            assert receiver.published_snapshot() == before
            fails(lambda: receiver.present(task, vblank=True))
            assert receiver.published_snapshot() == before
            gates += 1
            receiver.mark_writes_drained(task)
            fails(lambda: receiver.present(task, vblank=False))
            assert receiver.published_snapshot() == before
            gates += 1
            assert b.digest(task.display) == row['display_rgb565_sha256']
            assert m.C.reference_tag(task.planes).hex() == row['canonical_yuv_tag']
            assert receiver.present(task, vblank=True) == ack
            assert receiver.retry_ack(packet) == ack
            assert b.digest(receiver.display) == row['display_rgb565_sha256']
            full_words += receiver.display.size
            yuv_samples += sum(p.size for p in task.planes)
            for rect, desc in zip(m.hc.RECTANGLES, row['source_original_hud']):
                x, y, w, h = rect
                original = np.frombuffer(b.raw(desc, b.OLD_CACHE), dtype='<u2').reshape(h, w)
                np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], original)
                words += w * h
            assert row['input_sha256'] == old[case['scene']]['rows'][row['id']]['input_sha256']
            assert row['active_rgb565_channel_mse'] == row['active_squared_channel_error'] / row['active_channel_samples']
            attempts = len(row['build_info']['attempts'])
            if case['policy'] == 'adaptive_shared':
                assert row['work'] == dict(analyze_calls=1, forward_plane_calls=3)
                shared_contexts += 1
                shared_forwards += 3
            else:
                assert row['work'] == dict(analyze_calls=attempts, forward_plane_calls=3 * attempts)
                if case['policy'] == 'adaptive_plain':
                    plain_contexts += attempts
                    plain_forwards += 3 * attempts
            if 'v20_source_vector_index' in row:
                vector = old[case['scene']]['vectors'][row['v20_source_vector_index']]
                src = vector['source']
                original = np.frombuffer(b.raw(src['blob'], b.OLD), dtype=src['dtype']).reshape(src['shape'])
                assert b.digest(original) == row['input_sha256']
                summed, count, mse = b.quality(m.C.corpus.rgb565(original), receiver.display)
                assert (summed, count, mse) == (row['active_squared_channel_error'], row['active_channel_samples'], row['active_rgb565_channel_mse'])
                quality_checks += 1
            if case['policy'] == 'fixed_v20_profiles':
                prior = previous[(case['scene'], 'fixed_v20_profiles')]['rows'][row['id']]
                assert row['display_rgb565_sha256'] == prior['display_rgb565_sha256']
                assert row['canonical_yuv_tag'] == prior['canonical_yuv_tag']
                assert row['active_rgb565_channel_mse'] == prior['active_rgb565_channel_mse']
            total += 1
        assert b.summary(case) == next(s for s in data['summary'] if (s['scene'], s['policy']) == (case['scene'], case['policy']))
    assert b.comparisons(data['cases']) == data['comparisons']
    assert total == 288 and words == 288 * 21120 and quality_checks == 30
    assert spans > 0 and shared_contexts == 96 and shared_forwards == 288
    print(json.dumps(dict(actual_joint_decisions=total, exact_original_hud_words=words,
                          sequential_display_hash_words=full_words, sequential_canonical_yuv_samples=yuv_samples,
                          independently_recomputed_quality_vectors=quality_checks, actual_hd22_span_patches=spans,
                          crc_negative_rejections=negatives, write_vblank_gate_rejections=gates,
                          old_profile_packet_ack_rejections=cross_profiles,
                          adaptive_plain_analysis_calls=plain_contexts, adaptive_shared_analysis_calls=shared_contexts,
                          adaptive_plain_forward_plane_calls=plain_forwards,
                          adaptive_shared_forward_plane_calls=shared_forwards,
                          paired_packet_ack_display_identical_decisions=96,
                          integrated_hd22_dispatch_implemented=True, physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
