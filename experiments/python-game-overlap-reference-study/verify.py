#!/usr/bin/env python3
"""Read-only verification of AR01 bank-specific overlap evidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def near(a,b):assert abs(a-b)<1e-6,(a,b)


def check_case(case):
    r=case['result'];cfg=r['config'];packets={p['id']:p for p in r['packets']}
    assert (cfg['width'],cfg['height'],cfg['fps'])==(720,480,30)
    assert not r['unresolved_ids'] and all(x is None for x in r['unresolved_sender_slots'])
    assert not r['unresolved_encoder_pending'] and not r['unresolved_ingress']
    assert r['unresolved_receiver_readers']==0 and not r['unresolved_decode']
    assert r['peak_sender']<=cfg['window'] and r['peak_pending']<=cfg['window']
    assert r['peak_ingress']<=2 and r['peak_framebuffers']<=3 and r['peak_feedback']<=4
    for work in r['work']:
        near(work['wall_ms'],work['service_ms']);near(work['done_ms']-work['start_ms'],work['service_ms'])
    for p in packets.values():
        assert p['encode_done'] and p['released_ms']>=p['encode_done_ms']
        near(p['encode_done_ms']-p['encode_started_ms'],p['encode_service_ms'])
        charges=[w for w in r['work'] if w['id']==p['id'] and w['stage'] in ('map','encode')]
        near(p['encode_service_ms'],sum(w['service_ms'] for w in charges))
        if p['admitted']:
            if cfg['reference_policy']=='overlap':
                if p['promoted']:
                    assert p['info']['pending_bank1_consumers']==0
                    assert p['info']['bank1_readers_before']==0
                    assert p['info']['pending_writers_before']==0
                if p['bank0_fallback']:
                    assert p['promotion_due'] and not p['promoted'] and p['reference_bank']==0
                    assert p['info']['reference_choice_explicit']
            assert 0<p['bytes']<=cfg['frame_cap']
            if not p['key']:
                ref=p['source_banks'][str(p['reference_bank'])]
                assert ref is not None and ref['id']==p['reference_id'] and ref['tag']==p['reference_tag']
            if p['key'] or p['promoted']:
                assert p['info']['promotion_reconstruction_paid']
                assert p['info']['reconstruction_ms']>0 and p['info']['reference_tag_ms']>0
        else:
            assert p['info']['bytes']>cfg['frame_cap'] and p['encode_service_ms']>0
        if 'read_pin_release_ms' in p:
            assert p['read_pin_at_decode_start'] and p['released_ms']>=p['read_pin_release_ms']
        if 'decode_done_ms' in p and not p['key']:
            ref=p['receiver_banks_before'][str(p['reference_bank'])]
            assert ref['id']==p['reference_id'] and ref['tag']==p['reference_tag']
    commits={c['id']:c for c in r['commits']}
    assert len(commits)==len(r['publications'])
    for pub in r['publications']:
        assert pub['at_ms']==commits[pub['id']]['at_ms']
        assert all(b is None or b['array_bytes']==2*b['logical_yuv8_bytes'] for b in pub['banks'].values())
    for f in r['feedback']:
        if f['kind']=='ack_applied':
            p=packets[f['id']]
            assert f['at_ms']>=p['decode_done_ms'] and 'expiry_requested_ms' not in p
            if p['key'] or p['promoted']:
                bank=f['sender_banks'][str(p['destination_bank'])]
                assert bank['id']==p['id']
    presented=[p['id'] for p in r['presented']];drops=[d['id'] for d in r['drops']]
    assert len(set(presented))==len(presented) and sorted(presented+drops)==list(range(r['capture_count']))
    assert r['presented_eventual']==len(presented)
    assert r['presented_strict']==sum(p['at_ms']<r['capture_window_ms'][1] for p in r['presented'])
    assert all(p['age_ms']<=cfg['decode_age_ms']+1000/cfg['refresh_hz']+1e-6 for p in r['presented'])
    assert r['forward_ipv4_udp_bytes']==sum(w['bytes'] for w in r['wire'])
    assert r['reverse_ipv4_udp_bytes']==sum(w['bytes'] for w in r['feedback'] if w['kind']=='wire')


def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,expected in d['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        p=ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,raw
    assert d['case_count']==len(d['cases'])==9
    for c in d['cases']:check_case(c)
    assert sum(c['result']['capture_count'] for c in d['cases'])==828
    for pair in d['pairs']:
        assert pair['same_choice_packet_hashes_exact']
        assert set(pair['same_reference_and_promotion_ids'])<=set(pair['common_admitted_ids'])
    assert len(d['pairs'])==5
    print('PASS:9cases828captureevents;AR01wireunchanged;bank1drain/key0fallback;allstagecosts,pools,refs,publicationverified;nohardwaretiming')


if __name__=='__main__':main()
