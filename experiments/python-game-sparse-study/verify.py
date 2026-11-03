#!/usr/bin/env python3
"""Read-only verification of retained paired decoder evidence."""
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def check_pins(pins):
    for original, expected in pins.items():
        path = ROOT / ('experiments/' + original.split('/experiments/', 1)[1])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path


def main():
    result = json.loads((HERE / 'results.json').read_text())
    check_pins(result['source_sha256'])
    ids = 0
    for case in result['cases']:
        manifest, rows = case['manifest'], case['rows']
        assert (manifest['target_width'], manifest['target_height']) == (720, 480)
        assert len(rows) == manifest['frame_count'] == 60
        assert [row['input_sha256'] for row in rows] == manifest['frame_sha256']
        for row in rows:
            assert row['baseline_gm_rgb_sha256'] == row['fast_gm_rgb_sha256']
            assert row['baseline_hg_rgb_sha256'] == row['fast_hg_rgb_sha256']
            assert row['baseline_reconstructed_yuv_sha256'] == row['fast_reconstructed_yuv_sha256']
            assert row['all_pixels_and_yuv_exact'] and row['selected_rgb565_mismatches'] == 0
            for count in row['inverse_blocks']:
                assert count['zero'] + count['dc_only'] + count['general_inverse'] == count['blocks']
                assert count['bypass_blocks'] == count['zero'] + count['dc_only']
                assert count['baseline_inverse_blocks'] == count['blocks']
        for group, summary in case['summary'].items():
            chosen = [r for r in rows if group == 'all' or r['key'] == (group == 'key')]
            assert summary['frames'] == len(chosen)
            for field, expected in summary['block_counts'].items():
                assert expected == sum(p[field] for row in chosen for p in row['inverse_blocks'])
            for name, stats in summary['receive_ms'].items():
                assert stats['n'] == len(chosen)
                assert abs(stats['mean'] - statistics.mean(r['whole_receive_ms'][name] for r in chosen)) < 1e-9
            for name in ('core_baseline_ms', 'core_fast_ms'):
                assert abs(summary[name]['mean'] - statistics.mean(r[name] for r in chosen)) < 1e-9
        ids += len(rows)
    assert ids == result['source_frames'] == 120
    assert result['whole_decoder_calls'] == 4 * ids == 480
    assert result['core_reconstruction_calls'] == 2 * ids == 240
    distinct = sum(len(set(c['manifest']['frame_sha256'])) for c in result['cases'])
    assert distinct == 92
    print(f'PASS: {ids} source IDs ({distinct} per-clip distinct images), 480 full decodes, exact pixels/YUV, {len(result["source_sha256"])} source pins')


if __name__ == '__main__':
    main()
