#!/usr/bin/env python3
"""Read-only verification of retained causal-screen candidate evidence."""
import hashlib
import json
from pathlib import Path
import benchmark as bench

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main():
    result = json.loads((HERE/'results.json').read_text())
    for original, expected in result['source_sha256'].items():
        path = ROOT/original.split('/moonbub-30fps-study/', 1)[1]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, path
    assert result['source_ids'] == 154 and result['decisions'] == 616
    cfg = result['policy']['gate_config']
    admitted = rejected = candidates = gates = 0
    for scene in result['scenes']:
        assert set(scene['profiles']) == {'gm_zero', 'bm_block', 'actual_rate', 'gated_rate'}
        assert scene['summary'] == bench.summarize(scene)
        if scene['cohort'] != 'synthetic':
            assert (scene['manifest']['target_width'], scene['manifest']['target_height']) == (720, 480)
        for profile, rows in scene['profiles'].items():
            assert [row['frame_id'] for row in rows] == scene['indices']
            for row in rows:
                attempts = row['attempts']
                candidates += len(attempts)
                assert row['source_rgb_sha256'] == scene['manifest']['frame_sha256'][row['source_index']]
                assert row['minimum_candidate_bytes'] == min(a['bytes'] for a in attempts)
                assert row['pending_after_feedback'] == 0
                assert row['prepare_ms'] >= row['internal_service_ms']
                if profile == 'gated_rate':
                    gate = row['gate']
                    assert row['gate_included_in_prepare_timer']
                    assert row['prepare_ms'] >= row['internal_service_ms'] + gate['gate_ms']
                    assert len(attempts) == (2 if gate['allow_block'] else 1)
                    if row['key']:
                        assert gate['comparisons'] == gate['samples'] == 0
                        assert not gate['allow_block']
                    else:
                        assert gate['samples'] == 45*30*4
                        assert gate['comparisons'] == 25*gate['samples']
                        expected = (gate['gain'] >= cfg['minimum_gain']
                                    and gate['relative_gain'] >= cfg['minimum_relative_gain']
                                    and gate['moving_fraction'] >= cfg['minimum_moving_fraction']
                                    and gate['best_mae'] <= cfg['maximum_best_error'])
                        assert gate['allow_block'] == expected
                    gates += int(gate['allow_block'])
                else:
                    assert row['gate'] is None
                    assert len(attempts) == (2 if profile == 'actual_rate' else 1)
                if row['accepted']:
                    admitted += 1
                    assert row['packet_bytes'] <= 49152 and row['pending_after_prepare'] == 1
                    assert row['packet_bytes'] == row['inner_bytes'] + row['outer_header_crc_bytes']
                    assert row['packet_bytes'] == min(a['bytes'] for a in attempts)
                    assert sum(a['selected'] for a in attempts) == 1
                    assert row['forward_size_accounting'] == row['packet_bytes'] + 59*((row['packet_bytes']+1023)//1024)
                else:
                    rejected += 1
                    assert not row['pending_after_prepare']
                    assert all(a['bytes'] > 49152 and not a['selected'] for a in attempts)
                    assert row['prepare_ms'] > 0
        for i, comparison in enumerate(scene['comparisons']):
            assert comparison['same_canonical_reference'] and comparison['candidate_packets_match_controls']
            assert comparison['gate_candidates_match_controls']
            controls = {mode: scene['profiles'][mode][i] for mode in ('gm_zero', 'bm_block')}
            gated = scene['profiles']['gated_rate'][i]
            for attempt in gated['attempts']:
                assert attempt['packet_sha256'] == controls[attempt['mode']]['attempts'][0]['packet_sha256']
            if gated['accepted']:
                assert gated['decoded_rgb_sha256'] == controls[gated['selected_mode']]['decoded_rgb_sha256']
    assert admitted + rejected == 616
    print(json.dumps(dict(source_ids=154, decisions=616, admitted=admitted, rejected=rejected,
                          actual_candidates=candidates, screened_bm_allowed=gates,
                          source_bindings=len(result['source_sha256']), all_canvases='720x480',
                          physical_30fps_proven=False), indent=2))


if __name__ == '__main__':
    main()
