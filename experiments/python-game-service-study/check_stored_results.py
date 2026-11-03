#!/usr/bin/env python3
"""Recompute stored service causality/conservation; no codec or timing rerun."""
import collections
import hashlib
import json
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
    d=json.loads((HERE/'results.json').read_text());summaries=[]
    for path,h in d['source_sha256'].items():assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==h,path
    assert d['case_count']==len(d['cases'])==8
    for c in d['cases']:
        r=c['result'];cfg=r['config'];ps={p['id']:p for p in r['packets']}
        assert all(x is None for x in r['unresolved_sender_slots'])
        assert not r['unresolved_ingress_frames'] and not r['unresolved_credits'] and not r['pending_ids']
        assert r['waiting_at_end'] is None and all(n==0 for n in r['unresolved_cpu'].values())
        assert r['peak_sender_slots']<=2 and r['peak_ingress_slots']<=2 and r['peak_credits']<=2
        assert r['peak_framebuffer_roles']<=3 and r['peak_cpu_queues']['resize']<=2
        assert r['peak_cpu_queues']['feedback_inflight']<=cfg['feedback_slots']
        assert sum(w['bytes'] for w in r['forward_wire'])==r['forward_ipv4_udp_bytes']
        assert sum(f['bytes'] for f in r['feedback'] if f['kind']=='wire')==r['feedback_ipv4_udp_bytes']
        assert sum(f['copies'] for f in r['feedback'] if f['kind']=='enqueue')==sum(f['kind']=='wire' for f in r['feedback'])
        assert sum(f['kind'] in ('received','lost','parse_rejected') for f in r['feedback'])==sum(f['kind']=='wire' for f in r['feedback'])
        cpu_by_stage=collections.defaultdict(list)
        for cpu in r['cpu_services']:
            cpu_by_stage[cpu['stage']].append(cpu)
            assert cpu['wall_ms']>=0 and cpu['service_ms']==(cpu['wall_ms'] if cfg['transport_cpu'] else 0)
            assert abs(cpu['done_ms']-cpu['start_ms']-cpu['service_ms'])<1e-7
            if cpu['stage'] in ('packetize','feed','feedback_build'):
                assert ps[cpu['id']]['released_ms']+1e-8>=cpu['done_ms']
            if cpu['stage']=='feed':
                assert any(w['id']==cpu['id'] and w['index']==cpu['index'] and w['at_ms']<=cpu['start_ms']+1e-8
                           and w['bytes']==cpu['input_bytes']+28 for w in r['forward_wire'])
        for rows in cpu_by_stage.values():
            assert all(b['start_ms']+1e-8>=a['done_ms'] for a,b in zip(rows,rows[1:]))
        resize=r['resize_services']
        for p in resize:
            assert p['wall_ms']>=0 and p['service_ms']==(p['wall_ms'] if cfg['resize_cpu'] else 0)
            assert abs(p['done_ms']-p['start_ms']-p['service_ms'])<1e-7
        assert all(b['start_ms']+1e-8>=a['done_ms'] for a,b in zip(resize,resize[1:]))
        for p in ps.values():
            assert p['encode_service_ms']==p['encode_wall_ms']>=0
            assert p['released_ms']+1e-8>=p['encode_started_ms']+p['encode_service_ms']
            scaled=next(s for s in resize if s['id']==p['id'])
            assert p['encode_started_ms']+1e-8>=scaled['done_ms']
            assert p['wire_pending']==0 and p.get('rx_pending',0)==0
            assert p.get('feedback_build_pending',0)==0 and p.get('feedback_parse_pending',0)==0
            if p['admitted']:
                staged=next(x for x in r['encoder_states'] if x['id']==p['id'] and x['kind']=='staged')
                published=next(x for x in r['encoder_states'] if x['id']==p['id'] and x['kind']=='published')
                assert p['id'] not in staged['pending'] and staged['last_issued']<p['id']
                assert p['id'] in published['pending'] and published['last_issued']==p['id']
                assert abs(published['at_ms']-p['encode_started_ms']-p['encode_service_ms'])<1e-7
            if 'decode_done_ms' in p:
                assert p['read_pin_decode_start'] and p['read_pin_release_ms']==p['decode_done_ms']
                assert p['released_ms']+1e-8>=p['decode_done_ms']
                assert abs(p['decode_done_ms']-p['decode_started_ms']-p['decode_service_ms'])<1e-7
                assert p['decode_service_ms']==p['decode_wall_ms']
                assert p['decode_started_ms']>=max(x['done_ms'] for x in cpu_by_stage['feed'] if x['id']==p['id'])-1e-8
        for f in r['feedback']:
            if f['kind']=='received' and f['accepted']:
                assert f['epoch']==1 and f['frame_crc']==ps[f['id']]['frame_crc']
                assert any(x['id']==f['id'] and abs(x['done_ms']-f['at_ms'])<1e-8 for x in cpu_by_stage['feedback_parse'])
            if f['kind']=='enqueue' and f['status']==0:assert f['at_ms']>=ps[f['id']]['decode_done_ms']
        for w in r['forward_wire']:
            p=ps[w['id']]
            assert w['bytes']==31+28+min(1024,p['bytes']-w['index']*1024)
            stage=next(x for x in cpu_by_stage['packetize'] if x['id']==w['id'])
            assert w['at_ms']>=stage['done_ms']
        validate_conservation(range(r['capture_count']),(p['id'] for p in r['presented']),(p['id'] for p in r['drops']),[])
        end=r['capture_count']*1000/cfg['fps']
        cap=[dict(id=i,capture_ms=i*1000/cfg['fps']) for i in range(r['capture_count'])]
        assert summarize_presentation(cap,r['presented'],end,(500,end-500) if end>=2000 else None)==r['metrics']
        def stats(rows):
            return dict(n=len(rows),wall_sum_ms=sum(x['wall_ms'] for x in rows),
                        charged_sum_ms=sum(x['service_ms'] for x in rows),
                        mean_wall_ms=sum(x['wall_ms'] for x in rows)/len(rows) if rows else None)
        summaries.append(dict(name=c['name'],kind=c['kind'],charged=c['charged'],strict=r['presented_strict'],
                              eventual=r['presented_eventual'],diagnostic_ids_per_s=r['metrics']['steady_fps'],
                              prepared=r['prepared'],drops=r['drops_by_reason'],resize=stats(resize),
                              cpu={k:stats(v) for k,v in cpu_by_stage.items()},
                              rejected_preparation_ms=sum(p['encode_service_ms'] for p in ps.values() if not p['admitted'])))
    for pair in d['pairs']:
        cases=[c for c in d['cases'] if c['name']==pair['name'] and c['kind']=='baseline']
        assert len(cases)==2 and cases[0]['manifest']['frame_sha256']==cases[1]['manifest']['frame_sha256']
        assert cases[0]['manifest']['source_sha256']==cases[1]['manifest']['source_sha256']
    missing_media=[]
    for c in d['cases']:
        if c['manifest'].get('synthetic'):continue
        p=Path(c['manifest']['source'])
        if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==c['manifest']['source_sha256']
        else:missing_media.append(str(p))
    out=dict(cases=len(summaries),source_bindings=len(d['source_sha256']),summaries=summaries,
             all_data_feedback_cpu_drained=True,missing_external_media=sorted(set(missing_media)),scope='Independent stored record checks; no physical service or hardware rerun')
    if '--write-summary' in sys.argv:
        (HERE/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
