#!/usr/bin/env python3
"""Read-only retained unified-codec candidate and reconstruction checks."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,expected in d['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        p=ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,raw
    assert d['source_ids']==328 and d['decisions']==1020
    admitted=rejected=selected_pixels=0
    for scene in d['scenes']:
        manifest=scene['manifest']
        for profile,rows in scene['profiles'].items():
            assert len(rows)==manifest['frame_count']
            for row in rows:
                assert row['input_sha256']==manifest['frame_sha256'][row['id']]
                assert row['actual_forward_calls']==3 and row['actual_analyze_calls']==1
                info=row['info'];attempts=info['inner_attempts']
                assert len(attempts)==(1 if profile.removesuffix('_ui')=='gm' else 2)
                assert info['minimum_complete_inner_bytes']==min(a['bytes'] for a in attempts)
                selected=[a for a in attempts if a['selected']]
                assert len(selected)==1 and selected[0]['bytes']==info['inner_bytes']==info['minimum_complete_inner_bytes']
                assert row['prepare_ms']>=row['internal_service_ms']
                assert row['pending_after_feedback']==0
                if not row['accepted']:
                    rejected+=1;assert info['bytes']>49152 and row['prepare_ms']>0;continue
                admitted+=1
                assert row['packet_bytes']==info['bytes']<=49152
                assert row['packet_bytes']==info['inner_bytes']+65+info['patch_bytes']
                assert row['decoded_rgb_sha256']==row['expected_rgb_sha256']
                assert row['base_rgb_sha256']==row['expected_base_rgb_sha256']
                assert row['max_yuv_delta_same_reference_gm']<=row['level']
                assert row['protected_gm_rgb565_mismatches']==0
                assert row['selected_source_rgb565_mismatches']==0
                assert row['same_reconstructed_banks']
                if row['attempted_key']:assert row['level']==0
                if row['attempted_key'] or row['promoted']:
                    assert info['promotion_reconstruction_paid'] and info['reconstruction_ms']>0 and info['reference_tag_ms']>0
                selected_pixels+=row['selected_pixels']
            s=scene['summary'][profile]
            assert s['admitted']==sum(r['accepted'] for r in rows)
    assert admitted+rejected==1020
    print(json.dumps(dict(source_ids=328,decisions=1020,admitted=admitted,rejected=rejected,
        selected_exact_source_pixels=selected_pixels,source_bindings=len(d['source_sha256']),
        one_analysis_three_forward_calls=True,full_inner_minimum=True,physical_30fps_proven=False),indent=2))


if __name__=='__main__':main()
