#!/usr/bin/env python3
"""Read-only verification of retained exact-source encoder pairs."""
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    result = json.loads((HERE / 'results.json').read_text())
    for original, expected in result['source_sha256'].items():
        path = ROOT / ('experiments/' + original.split('/experiments/', 1)[1])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    ids = hits = failures = 0
    for case in result['cases']:
        rows = case['rows']
        assert len(rows) == case['manifest']['frame_count']
        assert [row['input_sha256'] for row in rows] == case['manifest']['frame_sha256']
        assert case['unique_source_rgb_hashes'] == len(set(r['input_sha256'] for r in rows))
        for row in rows:
            assert row['baseline_packet_sha256'] == row['memo_packet_sha256']
            assert row['cap_fit'] == (row['packet_bytes'] <= 49152)
            assert row['baseline_forward_calls'] == 3
            assert row['memo_forward_calls'] == row['memo']['forward_transform_calls']
            assert row['memo_forward_calls'] == (0 if row['memo']['hit'] else 3)
            assert not (row['key'] and row['memo']['hit'])
            assert row['reference_id'] is None if row['key'] else row['reference_id'] == row['anchor_id']
            hits += int(row['memo']['hit'])
            failures += int(not row['cap_fit'])
        for group, summary in case['summary'].items():
            chosen = [r for r in rows if group == 'all'
                      or (group in ('key', 'p') and r['key'] == (group == 'key'))
                      or (group in ('hit', 'miss') and r['memo']['hit'] == (group == 'hit'))]
            assert len(chosen) == summary['frames']
            for field in ('baseline_prepare_ms', 'memo_prepare_ms'):
                assert summary[field]['n'] == len(chosen)
                assert abs(summary[field]['mean'] - statistics.mean(r[field] for r in chosen)) < 1e-9
            for field in ('baseline_forward_calls', 'memo_forward_calls'):
                assert summary[field] == sum(r[field] for r in chosen)
        ids += len(rows)
    assert ids == result['paired_source_ids'] == result['decoded_packets'] == 156
    assert result['encoded_packets'] == 2 * ids == 312
    assert hits == 40 and failures == 8
    print(f'PASS: {ids} paired IDs, {hits} exact cache hits, {failures} oversized controls counted, {len(result["source_sha256"])} source pins')


if __name__ == '__main__':
    main()
