#!/usr/bin/env python3
"""Read-only integrated candidate/packet/decoded-reference evidence checks."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def check_case(c,primary=True):
    r=c['result'];cfg=r['config'];packets={p['id']:p for p in r['packets']};commits={p['id']:p for p in r['commits']};f=r.get('frame_grants')
    stopped=f is not None and f['safe_stop']
    if primary:assert(cfg['width'],cfg['height'],cfg['fps'])==(720,480,30)
    if not stopped:
        assert not r['unresolved_ids'] and not r['unresolved_candidate'] and not r['unresolved_candidate_readers']
        assert not r['unresolved_encoder_pending'] and not r['unresolved_ingress'] and not r['unresolved_receiver_readers'] and not r['unresolved_decode']
        assert all(x is None for x in r['unresolved_sender_slots'])
        assert not r['gateway']['outstanding_tokens'] and not r['gateway']['control_outstanding']
    assert r['gateway']['peak_mailbox']<=6 and r['gateway']['peak_tokens']<=6 and r['gateway']['peak_control']<=1
    assert r['peak_sender']<=3 and r['peak_ingress']<=2 and r['peak_framebuffers']<=3 and r['peak_feedback']<=4
    if f is not None:
        assert f['peak_receiver']<=2 and f['peak_host']<=2 and r['gateway']['peak_tokens']<=5 and f['peak_feedback']<=4
        assert not any('GF03 busy' in p['feed_errors'] for p in r['packets'])
        if not stopped:assert not f['receiver_owned'] and not f['host_owned'] and not f['pending'] and f['feedback_owned']==0
    assert sorted([p['id'] for p in r['presented']]+[p['id'] for p in r['drops']]+r['unresolved_ids'])==list(range(r['capture_count']))
    for p in packets.values():
        i=p['info'];assert i['analyze_calls']==1 and i['forward_calls']==3
        assert i['bytes']==i['inner_bytes']+65+i['patch_bytes']
        if 'released_ms' in p:assert p['released_ms']>=p['encode_done_ms']>=p['build_done_ms']
        if p['committed']:
            assert p['admitted'] and p['bytes']<=cfg['frame_cap'] and p['commit_done_ms']<=p['encode_done_ms']
            if f is not None:
                g=p['frame_grant'];assert g['frame']==p['id'] and g['total']==p['bytes'] and g['crc']==p['route_crc']
                assert p['frame_grant_confirmed_before_commit_ms']<=p['commit_done_ms']
                assert any(h['event']=='sender_granted' and h['frame']==p['id'] and h['seq']==g['seq'] and h['slot']==g['slot'] and h['at_ms']<=p['frame_grant_confirmed_before_commit_ms'] for h in f['history'])
            if not p['key']:
                bank=p['source_banks'][str(p['reference_bank'])]
                assert bank and(bank['id'],bank['tag'])==(p['reference_id'],p['reference_tag'])
        else:
            assert 'packet_sha256' not in p
            assert not any(w['id']==p['id'] and not w['control'] for w in r['gateway']['wire'])
            assert not any(h['kind']=='ack_applied' and h['id']==p['id'] for h in r['feedback'])
    for row in commits.values():
        assert packets[row['id']]['committed'] and row['selected_ui_mismatches']==0
        if cfg['exact_ui']:
            selected=[tuple(p['rect']) for p in row['info']['patches']]
            assert len(set(selected))==len(selected) and all(p in map(tuple,cfg['ui_rectangles']) for p in selected)
            assert row['selected_exact_pixels']==sum(w*h for _,_,w,h in selected)
            assert row['selected_exact_pixels']<=sum(w*h for _,_,w,h in cfg['ui_rectangles'])
            if c.get('manifest',{}).get('path','').endswith('mass-effect-2600.mp4'):assert row['selected_exact_pixels']==21120
    for h in r['feedback']:
        if h['kind']=='ack_applied':
            p=packets[h['id']];assert h['at_ms']>=p['decode_done_ms'] and 'expiry_requested_ms' not in p
    assert r['forward_ipv4_udp_bytes']==sum(x['bytes'] for x in r['gateway']['wire'])
    assert r['reverse_ipv4_udp_bytes']==sum(x['bytes'] for x in r['feedback'] if x['kind']=='wire')
    for w in r['work']:assert w['service_ms']>=0 and abs(w['done_ms']-w['start_ms']-w['service_ms'])<1e-6

def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()==h,raw
    assert d['case_count']==len(d['cases'])==12
    assert sum(c['result']['capture_count'] for c in d['cases'])==790
    assert len([c for c in d['cases'] if c['source']=='native-regression'])==7
    for c in d['cases']:
        check_case(c,primary=c['source']=='native-regression')
        if c['source']=='native-regression':assert c['result']['capture_count']==90 and c['manifest']['unique_frame_count']==90
    pairs=d['fixed_cost_pairs']
    assert len(pairs)==2 and all(p['same_input_hashes'] and p['same_service_profile'] for p in pairs)
    assert all(p['grants_busy_rejections']==0 for p in pairs)
    print('PASS:actualFG19reserved-before-commit/FINISHdrain/cancel-safe-GF03-PC18-AF03;fixedcostpaired/fullresolution;paidcontrols/exactUI/bounds/drain-or-explicitsafestop;nohardwareproof')
if __name__=='__main__':main()
