#!/usr/bin/env python3
"""Read-only validation of finite unified codec, reference and UI evidence."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def near(a,b):assert abs(a-b)<1e-6,(a,b)


def check_case(case,*,primary=True):
    r=case['result'];cfg=r['config'];packets={p['id']:p for p in r['packets']}
    if primary:assert (cfg['width'],cfg['height'],cfg['fps'])==(720,480,30)
    assert cfg['reference_policy']=='overlap'
    assert cfg['codec_mode'] in ('gm','exact','gated')
    assert not r['unresolved_ids'] and all(x is None for x in r['unresolved_sender_slots'])
    assert not r['unresolved_encoder_pending'] and not r['unresolved_ingress']
    assert not r['unresolved_receiver_readers'] and not r['unresolved_decode']
    assert r['peak_sender']<=cfg['window'] and r['peak_pending']<=cfg['window']
    assert r['peak_ingress']<=2 and r['peak_framebuffers']<=3 and r['peak_feedback']<=4
    for w in r['work']:
        near(w['wall_ms'],w['service_ms']);near(w['done_ms']-w['start_ms'],w['service_ms'])
    for p in packets.values():
        info=p['info'];attempts=info['inner_attempts']
        assert info['analyze_calls']==1 and info['forward_calls']==3
        gate=info['gate']
        if cfg['codec_mode']=='gated':
            assert gate['evaluated'] and gate['threshold']==0.90 and gate['sample_blocks_per_plane']==64
            assert gate['total_sampled_blocks']<=192 and len(gate['planes'])==3
            assert gate['allow_sr']==all(p['zero_or_dc_fraction']>=0.90 for p in gate['planes'])
            for plane in gate['planes']:
                assert plane['sampled_blocks']==len(plane['sample_indices'])<=64
                assert plane['sampled_blocks']<=plane['blocks']
                assert plane['zero_or_dc_fraction']==plane['zero_or_dc_blocks']/plane['sampled_blocks']
            assert len(attempts)==(2 if gate['allow_sr'] else 1)
            assert info['gate_ms']>0
        else:
            assert not gate['evaluated'] and gate['total_sampled_blocks']==0
            assert len(attempts)==(1 if cfg['codec_mode']=='gm' else 2)
        chosen=[a for a in attempts if a['selected']]
        assert len(chosen)==1 and chosen[0]['bytes']==info['inner_bytes']
        assert chosen[0]['bytes']==min(a['bytes'] for a in attempts)==info['minimum_complete_inner_bytes']
        assert info['bytes']==info['inner_bytes']+65+info['patch_bytes']
        assert p['encode_done'] and p['released_ms']>=p['encode_done_ms']
        near(p['encode_done_ms']-p['encode_started_ms'],p['encode_service_ms'])
        near(p['encode_service_ms'],sum(w['service_ms'] for w in r['work'] if w['id']==p['id'] and w['stage'] in ('map','encode')))
        if p['admitted']:
            assert p['bytes']==info['bytes']<=cfg['frame_cap']
            if not p['key']:
                source=p['source_banks'][str(p['reference_bank'])]
                assert source is not None and source['id']==p['reference_id'] and source['tag']==p['reference_tag']
            if p['key'] or p['promoted']:
                assert info['promotion_reconstruction_paid'] and info['reconstruction_ms']>0 and info['reference_tag_ms']>0
        else:assert info['bytes']>cfg['frame_cap'] and p['encode_service_ms']>0
        if 'read_pin_release_ms' in p:
            assert p['read_pin_at_decode_start'] and p['released_ms']>=p['read_pin_release_ms']
        if not cfg['exact_ui']:assert info['patch_count']==0 and info['selected_pixels']==0
    for c in r['commits']:
        p=packets[c['id']]
        assert c['selected_ui_mismatches']==0
        assert c['selected_exact_pixels']==c['info']['selected_pixels']==p['info']['selected_pixels']
        assert c['base_rgb_sha256']==c['info']['base_rgb_sha256']
        if not cfg['exact_ui']:assert c['selected_exact_pixels']==0
    for pub in r['publications']:
        assert all(b is None or b['array_bytes']==2*b['logical_yuv8_bytes'] for b in pub['banks'].values())
    for f in r['feedback']:
        if f['kind']=='ack_applied':
            p=packets[f['id']]
            assert f['at_ms']>=p['decode_done_ms'] and 'expiry_requested_ms' not in p
            if p['key'] or p['promoted']:assert f['sender_banks'][str(p['destination_bank'])]['id']==p['id']
    displayed=[p['id'] for p in r['presented']];dropped=[p['id'] for p in r['drops']]
    assert len(set(displayed))==len(displayed) and sorted(displayed+dropped)==list(range(r['capture_count']))
    assert r['presented_eventual']==len(displayed)
    assert r['presented_strict']==sum(p['at_ms']<r['capture_window_ms'][1] for p in r['presented'])
    assert all(p['age_ms']<=cfg['decode_age_ms']+1000/cfg['refresh_hz']+1e-6 for p in r['presented'])
    assert r['forward_ipv4_udp_bytes']==sum(w['bytes'] for w in r['wire'])
    assert r['reverse_ipv4_udp_bytes']==sum(w['bytes'] for w in r['feedback'] if w['kind']=='wire')


def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,expected in d['source_sha256'].items():
        marker='/moonbub-30fps-study/'
        path=ROOT/raw.split(marker,1)[1] if marker in raw else Path(raw)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,raw
    assert d['case_count']==len(d['cases'])==9
    for c in d['cases']:check_case(c)
    assert sum(c['result']['capture_count'] for c in d['cases'])==540
    old=set(d['validation_scope']['prior_selected_pts'])
    new=set(d['validation_scope']['new_selected_pts'])
    assert not old & new and len(new)==60
    scope=d['validation_scope']
    assert min(new)>max(old)==119600
    assert scope['prior_source_sha256']==scope['new_source_sha256']
    assert scope['new_window_start_seconds']==10.04
    for pair in d['pairs']:
        a=next(c for c in d['cases'] if c['source']==pair['source'] and c['profile']==pair['left_profile'])
        b=next(c for c in d['cases'] if c['source']==pair['source'] and c['profile']==pair['right_profile'])
        aa={p['id']:p for p in a['result']['packets']};bb={p['id']:p for p in b['result']['packets']}
        for i in pair['matched_reference_base_exact_ids']:
            assert all(aa[i][k]==bb[i][k] for k in ('key','promoted','reference_bank','reference_id','reference_tag'))
        ca={c['id']:c for c in a['result']['commits']};cb={c['id']:c for c in b['result']['commits']}
        for i in pair['matched_reference_base_exact_ids']:
            assert ca[i]['base_rgb_sha256']==cb[i]['base_rgb_sha256']
        for i in pair['matched_reference_same_ui_exact_display_ids']:
            assert ca[i]['info']['patches']==cb[i]['info']['patches']
            assert ca[i]['rgb_sha256']==cb[i]['rgb_sha256']
        assert pair['matched_reference_base_mismatches']==0
    assert d['gate_config']['threshold']==0.90 and d['gate_config']['sample_blocks_per_plane']==64
    print('PASS:9cases540events;fixed0.90screen64blocks/plane;newvalidationPTSdisjoint;exactUI/ref/cap/cost/bankbounds;nohardwareclaim')


if __name__=='__main__':main()
