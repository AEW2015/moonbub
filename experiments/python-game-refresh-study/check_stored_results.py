#!/usr/bin/env python3
"""Portable read-only verification of the frozen refresh evidence. Original verify.py is retained unchanged."""
import json
from pathlib import Path

from replay import ServiceTape, sha

HERE = Path(__file__).resolve().parent


def near(a, b):
    assert abs(a - b) < 1e-7, (a, b)


def check_case(case, *, primary=True):
    r = case['result']; cfg = r['config']; packets = {p['id']: p for p in r['packets']}
    if primary:assert (cfg['width'], cfg['height'], cfg['fps']) == (720, 480, 30)
    assert cfg['frame_cap'] == 49152 and cfg['frame_deadline_ms'] == 150
    assert r['forward_header_bytes'] == 31 and r['feedback_protocol_bytes'] == 24
    assert all(x is None for x in r['unresolved_sender_slots'])
    assert not r['unresolved_ingress_frames'] and not r['unresolved_credits'] and not r['pending_ids']
    assert r['waiting_at_end'] is None and all(v == 0 for v in r['unresolved_cpu'].values())
    assert r['peak_sender_slots'] <= 2 and r['peak_ingress_slots'] <= 2 and r['peak_credits'] <= 2
    assert r['peak_sender_packet_bytes'] <= 2 * 49152 and r['peak_ingress_payload_bytes'] <= 2 * 49152
    assert r['peak_framebuffer_roles'] <= 3
    tape = r['service_tape']
    service = ServiceTape(tuple(sorted(tape['entries_ms'].items())), tape['provenance'], tape['scale'])
    assert service.describe() == tape
    assert case['service_scale'] == tape['scale']
    policy = r['key_policy']; assert policy['mode'] == case['policy']
    assert all(o['observed_max_id'] == o['id'] and
               (o['prior_observed_id'] is None or o['prior_observed_id'] < o['id']) and
               (o['latest_scene_id'] is None or o['latest_scene_id'] <= o['id'])
               for o in policy['observations'])
    assert all(d['source_observed_through'] == d['id'] for d in policy['decisions'])
    for row in r['resize_services']:
        near(row['service_ms'], service.charge('resize', row['id'], None))
        near(row['done_ms'] - row['start_ms'], row['service_ms'])
        assert row['wall_ms'] >= 0
    for row in r['cpu_services']:
        near(row['service_ms'], service.charge(row['stage'], row['id'], packets[row['id']]['key']))
        near(row['done_ms'] - row['start_ms'], row['service_ms'])
        assert row['wall_ms'] >= 0
    for frame, p in packets.items():
        stage = 'encode' if p['admitted'] else 'encode_rejected'
        near(p['encode_service_ms'], service.charge(stage, frame, p['attempted_key']))
        assert p['encode_wall_ms'] >= 0
        assert p['released_ms'] >= p['encode_started_ms'] + p['encode_service_ms'] - 1e-7
        if not p['admitted']:
            assert p['bytes'] == 0 and not p.get('packet_sha256')
            near(p['encode_service_ms'], 120 * tape['scale'])
            continue
        assert p['bytes'] <= 49152 and p['attempted_key'] == p['key']
        if p['key']:
            assert not p['pending_at_prepare'] and p['reference_id'] is None
        else:
            ref = p['reference_id']
            assert ref is not None and ref == p['acked_anchor_at_prepare']
            assert any(a['id'] == ref and a.get('accepted') and a['at_ms'] <= p['encode_started_ms']
                       for a in r['feedback'] if a['kind'] == 'received')
        pub = next(e for e in r['encoder_states'] if e['id'] == frame and e['kind'] == 'published')
        near(pub['at_ms'], p['encode_started_ms'] + p['encode_service_ms'])
        assert frame in pub['pending']
        if 'decode_service_ms' in p:
            near(p['decode_service_ms'], service.charge('decode', frame, p['key']))
            near(p['decode_done_ms'] - p['decode_started_ms'], p['decode_service_ms'])
            near(p['read_pin_release_ms'], p['decode_done_ms'])
            assert p['read_pin_decode_start'] and p['released_ms'] >= p['decode_done_ms']
            assert p['decode_started_ms'] >= max(c['done_ms'] for c in r['cpu_services']
                                                if c['stage'] == 'feed' and c['id'] == frame)
    assert all(c['selected_rgb565_mismatches'] == 0 for c in r['commits'])
    ids = [p['id'] for p in r['presented']]
    drops = [p['id'] for p in r['drops']]
    assert len(set(ids)) == len(ids) and not set(ids) & set(drops)
    assert sorted(ids + drops) == list(range(r['capture_count']))
    assert r['presented_eventual'] == len(ids)
    assert r['presented_strict'] == sum(p['at_ms'] < r['capture_window_ms'][1] for p in r['presented'])
    assert all(p['age_ms'] <= 150 + 1000 / 60 + 1e-7 for p in r['presented'])
    assert r['forward_ipv4_udp_bytes'] == sum(w['bytes'] for w in r['forward_wire'])
    assert r['feedback_ipv4_udp_bytes'] == sum(f['bytes'] for f in r['feedback'] if f['kind'] == 'wire')
    for reason, duration in r['encoder_admission_wait_ms'].items():
        near(duration, sum(w['duration_ms'] for w in r['encoder_admission_waits'] if w['reason'] == reason))
    for a in r['feedback']:
        if a['kind'] == 'received' and a['accepted']:
            assert a['at_ms'] >= packets[a['id']]['decode_done_ms']
            assert not any(t['id'] == a['id'] and t['at_ms'] < a['at_ms'] for t in r['timeout_events'])


def main():
    data = json.loads((HERE / 'results.json').read_text())
    assert data['case_count'] == len(data['cases'])
    for path, expected in data['source_sha256'].items():
        original = str(path)
        marker = '/moonbub-30fps-study/'
        local = HERE.parent.parent / original.split(marker, 1)[1] if marker in original else Path(original)
        assert sha(local) == expected, path
    groups = {}
    for case in data['cases']:
        check_case(case)
        key = (case['source'], case['mode'], case['service_scale'])
        identity = (case['result']['service_tape']['table_sha256'], case['manifest']['frame_sha256'])
        assert groups.setdefault(key, identity) == identity, 'paired source/table mismatch'
    print(f"PASS: {len(data['cases'])} retained720x480@30 cases, paired tables/source hashes, charged timing, actual packet/reference/reader/ownership traces")


if __name__ == '__main__':
    main()
