#!/usr/bin/env python3
"""Read-only validation of measured-stage finite execution evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def near(a, b):
    assert abs(a-b) < 1e-7, (a, b)


def check_case(case, primary=True):
    r = case['result']; cfg = r['config']
    if primary:
        assert (cfg['width'], cfg['height'], cfg['fps']) == (720, 480, 30)
    assert r['service_tape'] is None and cfg['decoder_service'] == 'python_wall'
    assert cfg['resize_cpu'] and cfg['transport_cpu'] and cfg['controller'] == 'normal'
    assert all(x is None for x in r['unresolved_sender_slots'])
    assert not r['pending_ids'] and not r['unresolved_ingress_frames'] and not r['unresolved_credits']
    assert r['waiting_at_end'] is None and all(x == 0 for x in r['unresolved_cpu'].values())
    assert r['peak_sender_slots'] <= 2 and r['peak_ingress_slots'] <= 2 and r['peak_credits'] <= 2
    assert r['peak_framebuffer_roles'] <= 3
    assert r['peak_sender_packet_bytes'] <= 2*49152 and r['peak_ingress_payload_bytes'] <= 2*49152
    packets = {p['id']: p for p in r['packets']}
    admitted = 0
    for p in packets.values():
        near(p['encode_service_ms'], p['encode_wall_ms'])
        assert p['encode_done']
        assert p['released_ms'] >= p['encode_started_ms']+p['encode_service_ms']
        hits = [a for a in p['attempts'] if a.get('cache_hit')]
        assert case['cache'] or not hits
        if p['admitted']:
            admitted += 1
            assert 0 < p['bytes'] <= cfg['frame_cap']
            assert p['reference_id'] is None if p['key'] else p['reference_id'] == p['acked_anchor_at_prepare']
            if 'decode_done_ms' in p:
                near(p['decode_service_ms'], p['decode_wall_ms'])
                near(p['decode_done_ms']-p['decode_started_ms'], p['decode_service_ms'])
                assert p['read_pin_decode_start']
                near(p['read_pin_release_ms'], p['decode_done_ms'])
                assert p['released_ms'] >= p['decode_done_ms']
        else:
            assert p['encode_wall_ms'] > 0 and p['bytes'] == 0
            assert not hits or p['forward_calls'] == 0
    for stage in r['resize_services']+r['cpu_services']:
        near(stage['wall_ms'], stage['service_ms'])
        near(stage['done_ms']-stage['start_ms'], stage['service_ms'])
    ids = [p['id'] for p in r['presented']]; dropped = [d['id'] for d in r['drops']]
    assert sorted(ids+dropped) == list(range(r['capture_count']))
    assert len(set(ids)) == len(ids) and not set(ids) & set(dropped)
    assert r['presented_eventual'] == len(ids)
    assert r['presented_strict'] == sum(p['at_ms'] < r['capture_window_ms'][1] for p in r['presented'])
    assert all(c['selected_rgb565_mismatches'] == 0 for c in r['commits'])
    assert r['forward_ipv4_udp_bytes'] == sum(w['bytes'] for w in r['forward_wire'])
    assert r['feedback_ipv4_udp_bytes'] == sum(w['bytes'] for w in r['feedback'] if w['kind'] == 'wire')
    for feedback in r['feedback']:
        if feedback['kind'] == 'received' and feedback['accepted']:
            p = packets[feedback['id']]
            assert feedback['at_ms'] >= p['decode_done_ms']
            assert not any(t['id'] == feedback['id'] and t['at_ms'] < feedback['at_ms'] for t in r['timeout_events'])
    return admitted


def main():
    result = json.loads((HERE/'results.json').read_text())
    for original, expected in result['source_sha256'].items():
        marker = '/moonbub-30fps-study/'
        local = ROOT/original.split(marker, 1)[1] if marker in original else Path(original)
        assert hashlib.sha256(local.read_bytes()).hexdigest() == expected, original
    assert result['case_count'] == len(result['cases']) == 16
    for case in result['cases']:
        check_case(case)
    assert sum(c['result']['capture_count'] for c in result['cases']) == 1104
    for pair in result['pairs']:
        assert set(pair['same_packet_ids']) <= set(pair['common_prepared_ids'])
    assert len(result['pairs']) == 6
    print('PASS:16 measured-stage720x480@30 cases,1104capture events, exact packet/ownership/cost accounting; no physical timing proof')


if __name__ == '__main__':
    main()
