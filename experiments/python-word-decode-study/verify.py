#!/usr/bin/env python3
"""Check stored paired decoder and finite service artifacts, not another run."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    docs=[json.loads((HERE/name).read_text()) for name in ('results.json','scheduler-results.json')]
    checked=0
    for doc in docs:
        for path,expected in doc['source_sha256'].items():
            assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==expected,path
            checked+=1
    paired,scheduler=docs
    assert paired['paired_packets']==sum(s['paired_packets'] for s in paired['scenes'])==72
    assert paired['paired_planes']==sum(len(r['planes']) for s in paired['scenes'] for r in s['records'])==216
    for scene in paired['scenes']:
        for row in scene['records']:
            assert row['input_sha256']==scene['manifest']['frame_sha256'][row['frame']]
    count=preps=commits=0
    for case in scheduler['cases']:
        r=case['result'];end=r['capture_count']*1000/r['config']['fps']
        assert all(slot is None for slot in r['unresolved_slots'])
        assert not r['unresolved_pending'] and not r['pending_ids'] and r['waiting_at_end'] is None
        assert r['peak_compressed_slots']<=2 and r['peak_pending_credits']<=2 and r['peak_framebuffers']<=3
        assert r['peak_retained_packet_bytes']<=2*49152
        p={x['id'] for x in r['presented']};d={x['id'] for x in r['drops']}
        assert not p&d and p|d==set(range(r['capture_count']))
        assert len(p)==r['presented_eventual']
        assert sum(x['at_ms']<end-1e-9 for x in r['presented'])==r['presented_strict']
        steady=sum(500<=x['at_ms']<end-500 for x in r['presented'])
        assert steady==r['steady_count'] and steady*1000/(end-1000)==r['metrics']['steady_fps']
        rows={x['id']:x for x in r['packets']}
        for row in rows.values():assert row['encode_service_ms']==row['encode_wall_ms']>=0
        for c in r['commits']:
            row=rows[c['id']]
            assert abs(c['at_ms']-row['decode_started_ms']-row['decode_service_ms'])<1e-9
            expected=row['decode_wall_ms'] if r['config']['decoder_service']=='python_wall' else r['config']['decode_ms']
            assert row['decode_service_ms']==expected
        count+=1;preps+=len(rows);commits+=len(r['commits'])
    assert count==4
    print(json.dumps({'source_bindings_checked':checked,'paired_packets':72,'paired_planes':216,
                      'service_cases':count,'actual_preparations':preps,'hash_checked_commits':commits,
                      'all_resources_drained':True,'scope':'Stored evidence checks only, not codec rerun or physical proof'},indent=2))


if __name__=='__main__':main()
