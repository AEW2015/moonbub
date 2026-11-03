#!/usr/bin/env python3
"""Check recorded source bindings, service accounting, finite outcomes and metrics."""
import hashlib
import json
from pathlib import Path

import model

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def resolve_recorded(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    doc=json.loads((HERE/'results.json').read_text())
    for path,expected in doc['source_sha256'].items():
        assert hashlib.sha256(resolve_recorded(path).read_bytes()).hexdigest()==expected, path
    assert len(doc['cases'])==doc['case_count']==12
    packets=commits=0
    for case in doc['cases']:
        r=case['result'];n=r['capture_count'];end=n*1000/r['config']['fps']
        assert all(x is None for x in r['unresolved_slots']) and not r['unresolved_pending'] and not r['pending_ids'] and r['waiting_at_end'] is None
        assert r['peak_compressed_slots']<=2 and r['peak_pending_credits']<=2 and r['peak_framebuffers']<=3
        assert r['peak_retained_packet_bytes']<=2*49152
        captured=[dict(id=i,capture_ms=i*1000/r['config']['fps']) for i in range(n)]
        metrics=model.summarize_presentation(captured,r['presented'],end,(500,end-500))
        assert metrics==r['metrics']
        assert r['presented_strict']==metrics['presented_count']
        assert r['steady_fps']==metrics['steady_fps']
        model.validate_conservation(range(n),[x['id'] for x in r['presented']],[x['id'] for x in r['drops']],[])
        records={p['id']:p for p in r['packets']}
        packets+=len(records);commits+=len(r['commits'])
        for p in records.values():
            assert p['encode_service_ms']==p['encode_wall_ms'] and p['encode_wall_ms']>=0
            if 'decode_service_ms' in p:
                chosen=p['decode_wall_ms'] if r['config']['decoder_service']=='python_wall' else r['config']['decode_ms']
                assert p['decode_service_ms']==chosen
        for c in r['commits']:
            p=records[c['id']]
            assert abs(c['at_ms']-p['decode_started_ms']-p['decode_service_ms'])<1e-9
        source=Path(case['manifest']['source'])
        if source.exists():assert hashlib.sha256(source.read_bytes()).hexdigest()==case['manifest']['source_sha256']
    print(json.dumps({'source_bindings_checked':len(doc['source_sha256']),'cases':len(doc['cases']),
                      'actual_preparations':packets,'verified_commits':commits,'all_terminal_resources_drained':True,
                      'scope':'Checks stored model accounting; not another codec/real-time/hardware run'},indent=2))


if __name__=='__main__':main()
