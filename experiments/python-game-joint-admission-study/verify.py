#!/usr/bin/env python3
"""Read-only integrated candidate/packet/decoded-reference evidence checks."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def check_case(c,primary=True):
    r=c['result'];cfg=r['config'];packets={p['id']:p for p in r['packets']};commits={p['id']:p for p in r['commits']}
    if primary:assert(cfg['width'],cfg['height'],cfg['fps'])==(720,480,30)
    assert not r['unresolved_ids'] and not r['unresolved_candidate'] and not r['unresolved_candidate_readers']
    assert not r['unresolved_encoder_pending'] and not r['unresolved_ingress'] and not r['unresolved_receiver_readers'] and not r['unresolved_decode']
    assert all(x is None for x in r['unresolved_sender_slots'])
    assert r['gateway']['peak_mailbox']<=6 and r['gateway']['peak_tokens']<=6 and r['gateway']['peak_control']<=1
    assert not r['gateway']['outstanding_tokens'] and not r['gateway']['control_outstanding']
    assert r['peak_sender']<=3 and r['peak_ingress']<=2 and r['peak_framebuffers']<=3 and r['peak_feedback']<=4
    assert sorted([p['id'] for p in r['presented']]+[p['id'] for p in r['drops']])==list(range(r['capture_count']))
    for p in packets.values():
        i=p['info'];assert i['analyze_calls']==1 and i['forward_calls']==3
        assert i['bytes']==i['inner_bytes']+65+i['patch_bytes']
        assert p['released_ms']>=p['encode_done_ms']>=p['build_done_ms']
        if p['committed']:
            assert p['admitted'] and p['bytes']<=cfg['frame_cap'] and p['commit_done_ms']<=p['encode_done_ms']
            if not p['key']:
                bank=p['source_banks'][str(p['reference_bank'])]
                assert bank and(bank['id'],bank['tag'])==(p['reference_id'],p['reference_tag'])
        else:
            assert not p['admitted'] and 'packet_sha256' not in p and p['discard_service_ms']>=0
            assert not any(w['id']==p['id'] for w in r['gateway']['wire'])
            assert not any(f['kind']=='ack_applied' and f['id']==p['id'] for f in r['feedback'])
    for c in commits.values():
        assert packets[c['id']]['committed'] and c['selected_ui_mismatches']==0
        if cfg['exact_ui']:assert c['selected_exact_pixels']==sum(w*h for _,_,w,h in cfg['ui_rectangles'])
    for f in r['feedback']:
        if f['kind']=='ack_applied':
            p=packets[f['id']];assert f['at_ms']>=p['decode_done_ms'] and 'expiry_requested_ms' not in p
    assert r['forward_ipv4_udp_bytes']==sum(x['bytes'] for x in r['gateway']['wire'])
    assert r['reverse_ipv4_udp_bytes']==sum(x['bytes'] for x in r['feedback'] if x['kind']=='wire')
    for w in r['work']:assert w['service_ms']>=0 and abs(w['done_ms']-w['start_ms']-w['service_ms'])<1e-6

def main():
    d=json.loads((HERE/'results.json').read_text())
    for raw,h in d['source_sha256'].items():assert hashlib.sha256((ROOT/raw).read_bytes()).hexdigest()==h,raw
    assert d['case_count']==len(d['cases'])==8
    assert sum(c['result']['capture_count'] for c in d['cases'])==636
    assert len([c for c in d['cases'] if c['source']=='native-regression'])==6
    for c in d['cases']:
        check_case(c,primary=c['source']=='native-regression')
        if c['source']=='native-regression':
            assert c['result']['capture_count']==90 and c['manifest']['unique_frame_count']==90
    print('PASS:actualcandidate-admission-commit/wrappedGF03/PC18-QC18/AR03decode-AF03refs;exactUI/paidrejects/boundedmailbox/drains;nohardwareproof')
if __name__=='__main__':main()
