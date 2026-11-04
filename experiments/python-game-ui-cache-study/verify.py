#!/usr/bin/env python3
"""Read-only retained exact RGB565 UI-cache evidence checks."""
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
    ids = hits = attempts = changed_hits = 0
    for case in result['cases']:
        rows = case['rows']
        assert len(rows) == case['manifest']['frame_count']
        assert [r['source_rgb_sha256'] for r in rows] == case['manifest']['frame_sha256']
        assert case['distinct_source_rgb_images'] == len(set(case['manifest']['frame_sha256']))
        local_hits = local_changed = 0
        for row in rows:
            assert (row['width'], row['height']) == (720, 480)
            assert row['accepted'] and row['format'] == 'HG01'
            assert row['baseline_packet_sha256'] == row['cached_packet_sha256']
            assert row['packet_bytes'] <= case['frame_cap'] == 49152
            assert row['selected_rgb565_mismatches'] == 0 and row['decoded_rgb_sha256'] is not None
            assert row['selected_pixels'] == 21120
            assert row['cache_entries'] <= case['max_entries'] == 4
            assert [a['patch_bytes'] for a in row['baseline_attempts']] == [a['patch_bytes'] for a in row['cached_attempts']]
            assert row['cached_wall_ms'] >= row['cached_service_ms'] > 0
            assert row['baseline_wall_ms'] >= row['baseline_service_ms'] > 0
            for attempt in row['cached_attempts']:
                assert attempt['validate_ms'] > 0 and attempt['encode_ms'] > 0
                d = attempt['candidate_details']
                assert d['conversion_ms'] > 0 and d['compare_ms'] > 0
                assert d['cache_entries'] <= 4
                assert d['current_candidate_count'] == len(d['current_attempts'])
                if d['cache_hit']:
                    assert d['current_candidate_count'] == d['current_encoder_ms'] == 0
                    assert d['current_attempts'] == [] and d['current_encoder_details'] == {}
                    assert d['reused_candidate_details'] is not None
                    local_hits += 1
                    local_changed += int(row['whole_source_changed'])
                else:
                    assert d['current_candidate_count'] >= 3
                    assert d['current_encoder_ms'] > 0 and d['reused_candidate_details'] is None
                attempts += 1
            ids += 1
        assert local_hits == case['hit_attempts']
        assert local_changed == case['hits_on_changed_whole_source']
        assert case['max_persistent_cache_bytes'] == max(r['persistent_cache_bytes'] for r in rows)
        for label in ('baseline', 'cached'):
            assert abs(case['summary'][label]['mean'] - statistics.mean(r[label + '_wall_ms'] for r in rows)) < 1e-9
        hits += local_hits
        changed_hits += local_changed
    assert ids == result['paired_source_ids'] == 160 and attempts == 640
    assert hits == 292 and changed_hits == 176
    synthetic = {c['name']: c for c in result['cases'] if c['cohort'] == 'synthetic'}
    assert synthetic['moving-background-static-ui']['distinct_source_rgb_images'] == 12
    assert synthetic['moving-background-static-ui']['hits_on_changed_whole_source'] == 44
    assert synthetic['moving-background-changing-ui']['hit_attempts'] == 0
    print(f'PASS: {ids} exact HG01 pairs, {hits}/{attempts} cached patches ({changed_hits} on changed full sources), 4-entry bound, {len(result["source_sha256"])} source pins; standalone only')


if __name__ == '__main__':
    main()
