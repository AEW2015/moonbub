#!/usr/bin/env python3
"""Retained owned-source cohort replay and exact v23 stream parity."""
from pathlib import Path
import json
import numpy as np
import benchmark as b
import model as owned
m = owned.m
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def fails(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('expected rejection')


def main():
    data = b.load(HERE / 'results.json')
    assert data['schema'] == 'gamebub-owned-lazy-v24'
    for name, expected in data['source_sha256'].items():
        assert b.sha(ROOT / name) == expected, name
    originals = {c['scene']: c for c in b.load(b.OLD / 'results.json')['cases'] if c['policy'] == 'mandatory'}
    count = words = gates = negatives = quality_checks = copied = owned_guards = 0
    for case in data['cases']:
        receiver = m.JointReceiver()
        for row in case['rows']:
            packet, ack = b.raw(row['packet']), b.raw(row['ack'])
            assert len(packet) == row['packet_bytes'] <= 49152
            assert len(ack) == row['ack_bytes'] == 134
            assert row['wire'] == b.wire_counts(len(packet), len(ack))
            before = receiver.published_snapshot()
            fails(lambda: receiver.prepare(packet[:-1] + bytes([packet[-1] ^ 1])))
            assert receiver.published_snapshot() == before
            negatives += 1
            task = receiver.prepare(packet)
            assert receiver.published_snapshot() == before
            fails(lambda: receiver.present(task))
            assert receiver.published_snapshot() == before
            gates += 1
            receiver.mark_writes_drained(task)
            fails(lambda: receiver.present(task, vblank=False))
            assert receiver.published_snapshot() == before
            gates += 1
            assert b.digest(task.display) == row['display_rgb565_sha256']
            assert m.C.reference_tag(task.planes).hex() == row['canonical_yuv_tag']
            assert receiver.present(task) == ack and receiver.retry_ack(packet) == ack
            for rect, desc in zip(m.hc.RECTANGLES, row['source_original_hud']):
                x, y, w, h = rect
                source = np.frombuffer(b.raw(desc, b.OLD_CACHE), dtype='<u2').reshape(h, w)
                np.testing.assert_array_equal(receiver.display[y:y + h, x:x + w], source)
                words += w * h
            attempts = len(row['build_info']['attempts'])
            actual = attempts if case['policy'] == 'plain' else 1
            assert row['work'] == dict(analyze_calls=actual, forward_plane_calls=3 * actual)
            if case['policy'] == 'owned_lazy':
                capture = row['build_info']['capture']
                assert capture['released'] and capture['active_readers_after'] == 0
                assert capture['retained_pool_pixel_bytes_after'] == 0
                assert capture['copied_bytes'] == 1036800 and capture['peak_pool_slots'] <= 2
                assert row['shared_source_info']['source_guard_calls'] == 0
                assert row['shared_source_info']['source_guard_bytes'] == 0
                copied += capture['copied_bytes']
                owned_guards += row['shared_source_info']['source_guard_bytes']
            assert row['active_rgb565_channel_mse'] == row['active_squared_channel_error'] / row['active_channel_samples']
            if 'v20_source_vector_index' in row:
                v = originals[case['scene']]['vectors'][row['v20_source_vector_index']]
                src = v['source']
                source = np.frombuffer(b.raw(src['blob'], b.OLD), dtype=src['dtype']).reshape(src['shape'])
                summed, n, mse = b.quality(m.C.corpus.rgb565(source), receiver.display)
                assert (summed, n, mse) == (row['active_squared_channel_error'], row['active_channel_samples'], row['active_rgb565_channel_mse'])
                quality_checks += 1
            count += 1
        assert b.summary(case) == next(s for s in data['summary'] if (s['scene'], s['policy']) == (case['scene'], case['policy']))
    assert b.comparisons(data['cases']) == data['comparisons']
    assert count == 288 and words == 6082560 and copied == 99532800 and quality_checks == 30 and owned_guards == 0
    print(json.dumps(dict(decisions=count, exact_hud_words=words, crc_negatives=negatives,
                          write_vblank_gate_negatives=gates, original_quality_checks=quality_checks,
                          paired_plain_eager_owned_streams_identical=96,
                          owned_snapshot_copy_bytes=copied, owned_source_guard_bytes=owned_guards,
                          physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
