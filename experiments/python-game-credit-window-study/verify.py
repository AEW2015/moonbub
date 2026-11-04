#!/usr/bin/env python3
"""Verify bounded PC credit sensitivity and retained actual-wall evidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def check_case(case, *, primary=True):
    r=case['result'];cfg=r['config'];window=case['credit_window']
    assert window in (2,3) and cfg['sender_slots']==cfg['credit_window']==window
    assert r['encoder_credit_window']==window
    assert r['receiver_ingress_slots']==2 and r['framebuffer_role_slots']==3
    assert len(r['unresolved_sender_slots'])==window and all(x is None for x in r['unresolved_sender_slots'])
    assert not r['unresolved_credits'] and not r['unresolved_ingress_frames'] and not r['pending_ids']
    assert all(x==0 for x in r['unresolved_cpu'].values()) and r['waiting_at_end'] is None
    assert r['peak_sender_slots']<=window and r['peak_credits']<=window
    assert r['peak_sender_packet_bytes']<=window*cfg['frame_cap']
    assert r['peak_ingress_slots']<=2 and r['peak_ingress_payload_bytes']<=2*cfg['frame_cap']
    assert r['peak_framebuffer_roles']<=3
    if primary:
        assert (cfg['width'],cfg['height'],cfg['fps'])==(720,480,30)
        assert r['service_tape'] is None and cfg['decoder_service']=='python_wall'
        assert cfg['transport_cpu'] and cfg['resize_cpu'] and cfg['frame_cap']==49152
        assert cfg['frame_deadline_ms']==150
    for p in r['packets']:
        if primary:assert p['encode_service_ms']==p['encode_wall_ms']
        if p['admitted']:
            assert p['bytes']<=cfg['frame_cap']
            assert p['hybrid']['cache_enabled'] and p['hybrid']['ui_cache_enabled']
            assert len(p['pending_at_prepare'])<window
            assert p['reference_id'] is None if p['key'] else p['reference_id']==p['acked_anchor_at_prepare']
            if p['key']:assert not p['pending_at_prepare']
        if 'decode_done_ms' in p:
            assert p['released_ms']>=p['decode_done_ms']
            assert p['read_pin_release_ms']==p['decode_done_ms']
            if primary:assert p['decode_service_ms']==p['decode_wall_ms']
        if p.get('ingress_error'):
            assert any(c['stage']=='feed' and c['id']==p['id'] and c['service_ms']>0 for c in r['cpu_services'])
    if primary:
        assert all(c['service_ms']==c['wall_ms'] for c in r['cpu_services'])
        assert all(c['service_ms']==c['wall_ms'] for c in r['resize_services'])
    assert all(c['selected_rgb565_mismatches']==0 for c in r['commits'])
    ids=[p['id'] for p in r['presented']];drops=[p['id'] for p in r['drops']]
    assert sorted(ids+drops)==list(range(r['capture_count']))
    assert len(set(ids))==len(ids) and not set(ids)&set(drops)
    assert r['presented_strict']==sum(p['at_ms']<r['capture_window_ms'][1] for p in r['presented'])
    assert r['presented_eventual']==len(ids)
    assert all(p['age_ms']<=cfg['frame_deadline_ms']+1000/cfg['refresh_hz']+1e-7 for p in r['presented'])
    assert r['forward_ipv4_udp_bytes']==sum(x['bytes'] for x in r['forward_wire'])
    assert r['feedback_ipv4_udp_bytes']==sum(x['bytes'] for x in r['feedback'] if x['kind']=='wire')


def main():
    d=json.loads((HERE/'results.json').read_text())
    for original,expected in d['source_sha256'].items():
        p=ROOT/original.split('/moonbub-30fps-study/',1)[1]
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,p
    assert len(d['cases'])==d['case_count']==7
    assert sum(c['result']['capture_count'] for c in d['cases'])==780
    for c in d['cases']:check_case(c)
    assert sum(c['refresh_period']==0 for c in d['cases'])==1
    print(json.dumps(dict(cases=7,capture_policy_events=780,
        prepared=sum(c['result']['prepared'] for c in d['cases']),
        decoded=sum(len(c['result']['commits']) for c in d['cases']),
        source_bindings=len(d['source_sha256']),actual_wall_paid=True,
        primary_canvas='720x480',receiver_ingress_slots=2,framebuffer_roles=3,
        physical_30fps_proven=False),indent=2))


if __name__=='__main__':main()
