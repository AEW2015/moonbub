#!/usr/bin/env python3
"""Reconcile stored controller decisions, cap/ROI rules and paid stage work."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    doc=json.loads((HERE/'results.json').read_text())
    for path,expected in doc['source_sha256'].items():
        assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==expected,path
    assert doc['causality']['future_frames_used']==0
    assert not doc['causality']['oracle_used_for_selection'] and not doc['causality']['quality_metrics_used_for_selection']
    captures=admitted=rejected=attempts=forwards=0
    for scene in doc['scenes']:
        for policy,case in scene['cases'].items():
            rows=case['rows'];assert len(rows)==case['capture_count']
            assert case['admitted']==sum(r['accepted'] for r in rows)
            assert case['dropped']==sum(not r['accepted'] for r in rows)
            assert case['analysis_calls']==len(rows) and case['forward_calls']==len(rows)*3
            assert len({r['id'] for r in rows})==len(rows)
            assert case['packet_bytes']==sum(r.get('bytes',0) for r in rows)
            assert case['wire_bytes']==sum(r.get('wire_bytes',0) for r in rows)
            for row in rows:
                assert row['input_sha256']==scene['manifest']['frame_sha256'][row['id']]
                assert row['analyze_calls']==1 and row['forward_calls']==3
                assert 1<=len(row['attempts'])<=2
                assert row['service_ms']>=row['internal_service_ms']>=0
                paid=row['map_build_ms']+row['commit_ms']+sum(a['analyze_ms']+a['candidate_ms'] for a in row['attempts'])
                assert row['internal_service_ms']+1e-9>=paid
                assert row['attempts'][0]['label']=='normal'
                for attempt in row['attempts']:
                    assert attempt['fits']==(attempt['bytes']<=row['cap_bytes'])
                    assert attempt['candidate_ms']>=0 and attempt['analyze_ms']>=0
                if len(row['attempts'])==2:
                    assert not row['attempts'][0]['fits']
                    assert row['attempts'][1]['label']=='fallback' and row['attempts'][1]['analyze_ms']==0
                if row['accepted']:
                    selected=row['attempts'][-1]
                    assert selected['fits'] and row['bytes']==selected['bytes']<=row['cap_bytes']
                    assert row['selected']==selected['label']
                    assert row['selected_scale_counts']==row['verified_selected_scale_counts']
                    if policy=='priority':assert row['verified_roi_scale_min']==row['verified_roi_scale_max']==8
                else:
                    assert all(not r['fits'] for r in row['attempts']) and row['selected'] is None and row['commit_ms']==0
                captures+=1;admitted+=row['accepted'];rejected+=not row['accepted'];attempts+=len(row['attempts']);forwards+=row['forward_calls']
            common=scene['comparison']['common_admitted_ids']
            left={r['id']:r for r in scene['cases']['uniform']['rows'] if r['accepted']}
            right={r['id']:r for r in scene['cases']['priority']['rows'] if r['accepted']}
            assert common==sorted(set(left)&set(right))
    pairs=two_attempts=0
    for case in doc['paired_keys']:
        assert len(case['records'])==case['checks']
        for row in case['records']:
            assert row['input_sha256']==case['manifest']['frame_sha256'][row['source_index']]
            assert row['cap_bytes']==28672
            assert row['shared_forward_calls']==3 and row['naive_forward_calls']==3*row['attempts']
            assert 1<=row['attempts']<=2
            if row['accepted']:assert row['bytes']<=row['cap_bytes'] and row['packet_sha256']
            else:assert row['packet_sha256'] is None
            pairs+=1;two_attempts+=row['attempts']==2
    print(json.dumps({'source_bindings':len(doc['source_sha256']),'sequence_cases':sum(len(s['cases']) for s in doc['scenes']),
                      'sequence_captures':captures,'admitted':admitted,'cap_rejected':rejected,'candidate_evaluations':attempts,
                      'sequence_forward_plane_transforms':forwards,'paired_independent_keys':pairs,
                      'paired_two_attempt_branches':two_attempts,
                      'scope':'Stored finite-controller accounting; not a live/network/hardware run'},indent=2))


if __name__=='__main__':main()
