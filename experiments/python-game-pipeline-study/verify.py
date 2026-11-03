#!/usr/bin/env python3
"""Independent stored accounting/source/read-drain checks; no codec rerun."""
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(HERE.parent/'python-coupled-study'))
from validation import summarize_presentation,validate_conservation


def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    doc=json.loads((HERE/'results.json').read_text())
    for path,expected in doc['source_sha256'].items():
        assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==expected,path
    assert doc['case_count']==len(doc['cases'])==12
    prepared=committed=forward=reverse=timeout_waits=0
    for case in doc['cases']:
        r=case['result'];cfg=r['config'];rows={p['id']:p for p in r['packets']};prepared+=len(rows)
        assert all(x is None for x in r['unresolved_sender_slots'])
        assert not r['unresolved_ingress_frames'] and not r['unresolved_credits'] and not r['pending_ids']
        assert r['waiting_at_end'] is None
        assert r['peak_sender_slots']<=2 and r['peak_ingress_slots']<=2 and r['peak_credits']<=2
        assert r['peak_framebuffer_roles']<=3
        assert r['peak_sender_packet_bytes']<=2*49152 and r['peak_ingress_payload_bytes']<=2*49152
        assert r['forward_header_bytes']==31 and r['feedback_protocol_bytes']==24
        assert sum(w['bytes'] for w in r['forward_wire'])==r['forward_ipv4_udp_bytes']
        assert sum(f['bytes'] for f in r['feedback'] if f['kind']=='wire')==r['feedback_ipv4_udp_bytes']
        forward+=r['forward_ipv4_udp_bytes'];reverse+=r['feedback_ipv4_udp_bytes']
        assert all(f['bytes']==24 for f in r['feedback'] if f['kind']=='enqueue')
        assert all(f['bytes']==52 for f in r['feedback'] if f['kind']=='wire')
        enqueued=sum(2 if f['id'] in cfg['duplicate_feedback_ids'] else 1 for f in r['feedback'] if f['kind']=='enqueue')
        wired=[f for f in r['feedback'] if f['kind']=='wire']
        assert len(wired)==enqueued
        assert len([f for f in r['feedback'] if f['kind'] in ('received','lost','parse_rejected')])==len(wired)
        for wire in r['forward_wire']:
            p=rows[wire['id']];expected=31+28+min(1024,p['bytes']-wire['index']*1024)
            assert wire['bytes']==expected
        for p in rows.values():
            assert p['encode_service_ms']==p['encode_wall_ms']>=0
            assert p['released_ms']+1e-9>=p['encode_started_ms']+p['encode_service_ms']
            assert p['wire_pending']==0
            assert p['analyze_calls']==1 and p['forward_calls']==3
            assert 1<=len(p['attempts'])<=2
            assert not p.get('qspi_owned') and not p.get('decode_owned') and not p.get('queued_decode') and not p.get('queued_qspi')
            wire_times=[w['at_ms'] for w in r['forward_wire'] if w['id']==p['id']]
            if wire_times:assert p['released_ms']+1e-9>=max(wire_times)
            if 'decode_done_ms' in p:
                assert p['released_ms']+1e-9>=p['decode_done_ms']
                assert abs(p['decode_done_ms']-p['decode_started_ms']-p['decode_service_ms'])<1e-8
                chosen=p['decode_wall_ms'] if cfg['decoder_service']=='python_wall' else cfg['decode_ms']
                assert p['decode_service_ms']==chosen
            assert p['oracle_excluded']
        for f in r['feedback']:
            if f['kind']=='enqueue' and f['status']==0:
                assert f['at_ms']>=rows[f['id']]['decode_done_ms']
            if f['kind']=='received':
                assert any(abs(f['at_ms']-w['at_ms']-cfg['feedback_latency_ms'])<1e-8 for w in wired if w['id']==f['id'])
                if f['accepted']:
                    assert f['epoch']==1 and f['frame_crc']==rows[f['id']]['frame_crc']
        for timeout in r['timeout_events']:
            if not timeout['physical_drained']:
                timeout_waits+=1
                assert rows[timeout['id']]['released_ms']>=timeout['at_ms']
        ids=[p['id'] for p in r['presented']];drops=[p['id'] for p in r['drops']]
        assert len(ids)==len(set(ids)) and len(drops)==len(set(drops))
        validate_conservation(range(r['capture_count']),ids,drops,[])
        end=r['capture_count']*1000/cfg['fps']
        captures=[dict(id=i,capture_ms=i*1000/cfg['fps']) for i in range(r['capture_count'])]
        metrics=summarize_presentation(captures,r['presented'],end,(500,end-500) if end>=2000 else None)
        assert metrics==r['metrics'] and r['presented_strict']==metrics['presented_count']
        assert r['presented_eventual']==len(r['presented'])
        assert r['capture_count']==len(case['manifest']['frame_sha256'])
        for p in rows.values():assert p['bytes']<=cfg['frame_cap']
        committed+=len(r['commits'])
    print(json.dumps({'source_bindings':len(doc['source_sha256']),'cases':len(doc['cases']),
                      'actual_selected_preparations':prepared,'hash_checked_decodes':committed,
                      'forward_ipv4_udp_bytes':forward,'feedback_ipv4_udp_bytes':reverse,
                      'timeout_waiting_for_physical_drain':timeout_waits,'all_terminal_data_and_feedback_drained':True,
                      'scope':'Stored replay accounting only; physical ownership is a single-threaded software oracle'},indent=2))


if __name__=='__main__':main()
