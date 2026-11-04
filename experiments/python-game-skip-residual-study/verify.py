#!/usr/bin/env python3
"""Read-only retained SR01 evidence verification."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    d=json.loads((HERE/'results.json').read_text())
    for original,expected in d['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        p=ROOT/original.split(marker,1)[1] if marker in original else Path(original)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,original
    ids=decisions=admitted=rejected=0
    for c in d['cases']:
        count=len(c['manifest']['frame_sha256']);ids+=count
        assert set(c['profiles'])=={'gm','sr_dense','sr_exact','sr_prune2','sr_prune4'}
        for profile,rows in c['profiles'].items():
            assert len(rows)==count
            for r in rows:
                decisions+=1;assert (r['width'],r['height'])==(720,480)
                assert r['source_rgb_sha256']==c['manifest']['frame_sha256'][r['id']]
                assert r['pending_after_feedback']==0 and r['prepare_ms']>0
                assert r['accepted']==(r['candidate_bytes']<=49152)
                if r['accepted']:
                    admitted+=1;assert r['packet_bytes']==r['candidate_bytes']<=r['frame_cap']
                    assert r['baseline_yuv_max_delta']<=r['level']
                    assert r['protected_rgb565_mismatches']==0
                    if r['level']==0:assert r['decoded_rgb_sha256']==r['baseline_rgb_sha256']
                    if r['key']:assert r['level']==0
                else:
                    rejected+=1;assert r['packet_bytes'] is None and r['pending_after_prepare']==0
                for p in r['pruning']:
                    assert p['max_reconstructed_yuv_delta']<=r['level']
                for p in r['plane_choices']:
                    assert p['selected_bytes']==(p['dense_bytes'] if p['split_bytes'] is None else min(p['dense_bytes'],p['split_bytes']))
            summary=c['summary'][profile]
            assert summary['source_ids']==len(rows)
            assert summary['admitted']==sum(r['accepted'] for r in rows)
            assert summary['rejected']==sum(not r['accepted'] for r in rows)
        for i in range(count):
            controls=[c['profiles'][p][i] for p in c['profiles']]
            assert len({r['reference_yuv_sha256'] for r in controls})==1
            assert len({r['reference_before'] for r in controls})==1
    assert ids==d['source_ids']==154 and decisions==d['decisions']==770
    print(json.dumps(dict(source_ids=ids,decisions=decisions,admitted=admitted,rejected=rejected,
                         source_bindings=len(d['source_sha256']),primary_canvas='720x480',
                         protected_words_exact_to_GM=True,physical_30fps_proven=False),indent=2))


if __name__=='__main__':main()
