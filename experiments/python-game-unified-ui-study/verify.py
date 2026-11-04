#!/usr/bin/env python3
"""Read-only retained unified UI selector/framing comparison."""
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,expected in d['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        p=ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,raw
    assert d['case_count']==len(d['cases'])==6
    count=hits=changed_hits=attempts=0
    for case in d['cases']:
        rows=case['rows'];manifest=case['manifest'];s=case['summary']
        assert len(rows)==manifest['frame_count'] and [r['input_sha256'] for r in rows]==manifest['frame_sha256']
        assert (manifest['target_width'],manifest['target_height'])==(720,480)
        for r in rows:
            assert r['cached_section_sha256']==r['uncached_section_sha256']
            assert r['cached_display_sha256']==r['uncached_display_sha256']
            assert r['selected_word_mismatches']==r['unselected_base_word_mismatches']==0
            assert r['framed_ui_bytes']==r['cached']['used_bytes']<=r['byte_budget']==32768
            assert r['cached']['cache_entries']<=4
            for label in ('cached','uncached'):
                details=r[label]
                assert len(details['attempts'])<=4
                assert sum(a['framed_bytes'] for a in details['attempts'] if a['selected_in_output'])==details['used_bytes']
                for a in details['attempts']:
                    assert a['framed_bytes']==4+a['patch_bytes'] and a['encode_ms']>=0 and a['validate_ms']>=0
                    c=a['candidate_details']
                    if c['cache_hit']:
                        assert c['current_candidate_count']==0 and c['current_attempts']==[] and c['current_encoder_ms']==0
                        assert c['reused_candidate_details'] is not None
                    else:
                        assert c['current_candidate_count']==len(c['current_attempts'])>0
            attempts+=len(r['cached']['attempts'])
            hits+=sum(a['candidate_details']['cache_hit'] for a in r['cached']['attempts'])
            if r['source_changed']:changed_hits+=sum(a['candidate_details']['cache_hit'] for a in r['cached']['attempts'])
        assert s['max_cache_entries']<=4
        assert s['rows']==len(rows)
        for label in ('cached','uncached'):
            for key in ('selector_wall_ms','ui_receive_wall_ms'):
                assert abs(s[key][label]['mean']-statistics.mean(r[key][label] for r in rows))<1e-9
        count+=len(rows)
    assert count==d['paired_ids']==160
    print(json.dumps(dict(paired_ids=count,patch_attempts=attempts,cache_hits=hits,
                         hits_on_changed_source=changed_hits,source_pins=len(d['source_sha256']),
                         exact_selected_words=True,complete_AR02_or_FPS_proven=False),indent=2))


if __name__=='__main__':main()
