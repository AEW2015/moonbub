#!/usr/bin/env python3
"""Check retained rate-motion evidence and source bindings without timed work."""
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
assert r['source_ids']==154 and r['decisions']==462 and len(r['scenes'])==7
admitted=rejected=candidates=0
for scene in r['scenes']:
    assert set(scene['profiles'])=={'gm_zero','bm_block','actual_rate'}
    for profile,rows in scene['profiles'].items():
        assert [row['frame_id'] for row in rows]==scene['indices']
        for row in rows:
            candidates+=len(row['attempts'])
            assert row['source_rgb_sha256']==scene['manifest']['frame_sha256'][row['source_index']]
            assert row['minimum_candidate_bytes']==min(a['bytes'] for a in row['attempts'])
            assert len(row['attempts'])==(2 if profile=='actual_rate' else 1)
            assert row['prepare_ms']>=row['internal_service_ms']>=row['preview_ms']
            assert row['preview_ms']>=sum(a['stages']['candidate_total_ms'] for a in row['attempts'])
            assert row['common_stages']['shared_key_reconstruction_count']==int(row['key'])
            assert row['pending_after_feedback']==0
            if not row['accepted']:
                rejected+=1;assert row['minimum_candidate_bytes']>49152 and row['pending_after_prepare']==0
                assert not any(a['selected'] for a in row['attempts']);continue
            admitted+=1;assert row['packet_bytes']<=49152 and row['pending_after_prepare']==1
            assert row['packet_bytes']==row['inner_bytes']+row['outer_header_crc_bytes']
            assert row['outer_header_crc_bytes']==30
            assert row['packet_bytes']==row['minimum_candidate_bytes']
            assert row['read_pins_after_prepare']==int(not row['key'])
            selected=[a for a in row['attempts'] if a['selected']];assert len(selected)==1
            assert selected[0]['mode']==row['selected_mode'] and selected[0]['packet_sha256']==row['packet_sha256']
            assert row['forward_size_accounting']==row['packet_bytes']+59*((row['packet_bytes']+1023)//1024)
            assert row['reverse_size_accounting']==52
    for i,c in enumerate(scene['comparisons']):
        assert c['same_canonical_reference'] and c['candidate_packets_match_controls']
        selected=scene['profiles']['actual_rate'][i]
        assert selected['minimum_candidate_bytes']==min(c['gm_bytes'],c['bm_bytes'])
        for control,mode in ((scene['profiles']['gm_zero'][i],'gm_zero'),(scene['profiles']['bm_block'][i],'bm_block')):
            candidate=next(a for a in selected['attempts'] if a['mode']==mode)
            assert candidate['packet_sha256']==control['attempts'][0]['packet_sha256']
        if c['accepted']:assert c['selected_bytes']==min(c['gm_bytes'],c['bm_bytes'])
assert candidates==616
assert sum(len(s['indices']) for s in r['scenes'] if s['cohort']=='temporal_real')==120
assert sum(len(s['indices']) for s in r['scenes'] if s['cohort']=='heldout_real')==16
print(json.dumps({'source_ids':154,'decisions':462,'actual_candidate_packets':candidates,
    'admitted':admitted,'all_cap_rejections_paid':rejected,'same_key_candidate_hashes_match_controls':True,
    'source_bindings':len(r['source_sha256']),'all_canvases':'720x480',
    'scope':'Retained software candidate/packet/ownership evidence; no physical read-drain or native30fps proof'},indent=2))
