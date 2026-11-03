#!/usr/bin/env python3
"""Verify stored hybrid records and source pins without rerunning timing work."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
r=json.loads((HERE/'results.json').read_text())
for path,expected in r['source_sha256'].items():
    p=Path(path)
    if '/moonbub-30fps-study/' in path:p=ROOT/path.split('/moonbub-30fps-study/',1)[1]
    assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,path
assert r['source_inputs']==len(r['records'])==140
assert r['selector_decisions']==sum(len(s['policies']) for s in r['records'])
assert sum(s['cohort']=='temporal_real' for s in r['records'])==120
assert sum(s['cohort']=='heldout_real' for s in r['records'])==16
assert sum(s['cohort']=='synthetic_noisy' for s in r['records'])==2
assert sum(s['cohort']=='synthetic_flat' for s in r['records'])==2
admitted=0;rejected=0;rows=0
for scene in r['records']:
    if scene['controller_rejected']:
        assert not scene['policies'];continue
    assert len(scene['policies'])==4
    for policy,row in scene['policies'].items():
        rows+=1
        assert len(row['attempts'])<=4
        assert row['selected_pixels']==sum(p['rect'][2]*p['rect'][3] for p in row['selected'])<=row['requested_pixels']
        assert row['base_packet_sha256']==scene['control']['packet_sha256']
        assert row['selector_ms']>=row['selector_internal_ms']
        assert row['selector_internal_ms']>=row['candidate_encode_ms']+row['candidate_validate_ms']
        assert abs(row['charged_prepare_ms']-row['base_prepare_ms_reused']-row['selector_ms'])<1e-8
        for a in row['attempts']:
            d=a['candidate_details']
            if policy.endswith('_adaptive_row'):
                assert a['patch_bytes']==min(d['hp01_bytes'],d['hr01_bytes'])
                assert d['hr01_bytes']==min(c['bytes'] for c in d['attempts'])
                assert 2<=d['candidate_count']<=3
            else:assert d['candidate_count']==1 and a['format']=='HP01'
        if not row['accepted']:
            rejected+=1;assert row['base_bytes']>49152 and row['reason']=='base_over_cap' and not row['attempts'];continue
        admitted+=1
        assert row['packet_bytes']<=49152
        assert row['selected_rgb565_mismatches']==row['unselected_base_rgb565_mismatches']==0
        assert row['base_rgb_sha256']==scene['control']['base_rgb_sha256']
        assert row['identity']['frame_id']==scene['frame_id']
        assert row['identity']['epoch']==1
        assert row['identity']['key']==scene['control']['identity']['key']
        if row['format']=='GM01':
            assert row['packet_bytes']==row['base_bytes'] and row['packet_sha256']==row['base_packet_sha256'] and not row['selected']
        else:
            assert row['format']=='HG01'
            assert row['packet_bytes']==22+row['base_bytes']+sum(4+p['bytes'] for p in row['selected'])
        assert row['forward_accounting_bytes']==row['packet_bytes']+59*((row['packet_bytes']+1023)//1024)
        assert row['reverse_accounting_bytes']==52
        if scene['cohort']=='temporal_real':assert row['anchor_id']==scene['control']['identity']['reference_id'] or scene['control']['identity']['key']
    for region in ('broad','compact'):
        hp=scene['policies'][region+'_hp01'];hr=scene['policies'][region+'_adaptive_row']
        if hp['accepted'] and hr['accepted'] and [p['rect'] for p in hp['selected']]==[p['rect'] for p in hr['selected']]:
            assert hr['packet_bytes']<=hp['packet_bytes']
assert rows==r['selector_decisions']
print(json.dumps({'sources':140,'selector_decisions':rows,'admitted_cap_bounded':admitted,'base_rejected':rejected,
    'all_selected_rgb565_exact':True,'all_unselected_match_base':True,'source_bindings':len(r['source_sha256']),
    'scope':'Stored real-byte temporal software evidence only; no target FPS or finite-link proof'},indent=2))
