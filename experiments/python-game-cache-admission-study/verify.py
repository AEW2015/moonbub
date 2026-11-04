#!/usr/bin/env python3
"""Read-only retained candidate/commit cache evidence verification."""
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    result = json.loads((HERE / 'results.json').read_text())
    for original, expected in result['source_sha256'].items():
        marker = '/moonbub-30fps-study/'
        path = ROOT / original.split(marker, 1)[1] if marker in original else Path(original)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    ids = admitted = rejected = hits = 0
    for case in result['cases']:
        rows = case['rows']
        assert len(rows) == case['manifest']['frame_count']
        assert case['distinct_source_rgb_images'] == len(set(case['manifest']['frame_sha256']))
        assert [r['source_rgb_sha256'] for r in rows] == case['manifest']['frame_sha256']
        for r in rows:
            assert (r['width'], r['height']) == (720, 480)
            assert r['whole_packets_equal'] and r['baseline_packet_sha256'] == r['cached_packet_sha256']
            assert [a['bytes'] for a in r['baseline_attempts']] == [a['bytes'] for a in r['cached_attempts']]
            assert r['cached_prepare_wall_ms'] >= r['cached_service_ms'] > 0
            assert r['baseline_prepare_wall_ms'] >= r['baseline_service_ms'] > 0
            assert r['cache']['admission_before_commit']
            assert r['cache']['hits'] == sum(a['cache_hit'] for a in r['cached_attempts'])
            if r['accepted']:
                admitted += 1
                assert r['packet_bytes'] <= case['frame_cap']
                assert r['decoded_rgb_sha256'] is not None
                assert r['after_prepare_state']['last_issued'] == r['id']
                assert r['after_prepare_state']['generation'] == r['before_prepare_state']['generation'] + 1
                assert r['after_prepare_state']['pending_ids'] == [r['id']]
            else:
                rejected += 1
                assert r['before_prepare_state'] == r['after_prepare_state']
                assert r['packet_bytes'] is None
                assert all(not a['fits'] and a['bytes'] > case['frame_cap'] for a in r['cached_attempts'])
            for a in r['cached_attempts']:
                assert a['fits'] == (a['bytes'] <= case['frame_cap'])
                assert a['cache_lookup_ms'] > 0 and a['candidate_ms'] > 0
                assert a['cache_copy_ms'] >= 0
                if a['cache_hit']:
                    assert a['analyze_ms'] == a['cache_copy_ms'] == 0
                hits += int(a['cache_hit'])
            if all(a['cache_hit'] for a in r['cached_attempts']):
                assert r['cached_forward_calls'] == 0
            else:
                assert r['cached_forward_calls'] == 3
            ids += 1
        for group, summary in case['summary'].items():
            selected = [r for r in rows if group == 'all'
                        or (group in ('admitted', 'rejected') and r['accepted'] == (group == 'admitted'))
                        or (group in ('cache_hit', 'cache_miss') and bool(r['cache']['hits']) == (group == 'cache_hit'))]
            assert len(selected) == summary['rows']
            for label in ('baseline', 'cached'):
                key = label + '_prepare_wall_ms'
                assert abs(summary[key]['mean'] - statistics.mean(r[key] for r in selected)) < 1e-9
                assert summary[label + '_forward_calls'] == sum(r[label + '_forward_calls'] for r in selected)
    assert ids == result['paired_source_ids'] == 172
    assert admitted == result['admitted_pairs'] and rejected == result['rejected_pairs']
    print(f'PASS: {ids} paired720x480 IDs, {admitted} admitted/{rejected} rejected before commit, {hits} cached candidate attempts, exact GM01 bytes, {len(result["source_sha256"])} source pins')


if __name__ == '__main__':
    main()
