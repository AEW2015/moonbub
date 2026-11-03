#!/usr/bin/env python3
"""Lightweight persisted-result and pinned-source consistency checks."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)

r=json.loads((HERE/'results.json').read_text())
assert r['source_inputs']==20 and r['records']==60 and len(r['scenes'])==20
for path,digest in r['source_sha256'].items():assert hashlib.sha256(resolve(path).read_bytes()).hexdigest()==digest,path
rows=[]
for scene in r['scenes']:
    assert len(scene['policies'])==3
    for name,row in scene['policies'].items():
        rows.append(row);assert len(row['attempts'])<=4
        assert row['selected_pixels']<=row['requested_pixels']
        assert row['selected_pixels']==sum(p['rect'][2]*p['rect'][3] for p in row['selected'])
        assert abs(sum(a['encode_ms'] for a in row['attempts'])-row['attempt_encode_ms'])<1e-8
        assert row['selector_ms']>=row['selector_internal_ms']
        assert row['prepare_ms']>=row['attempt_encode_ms']+row['attempt_validate_ms']
        assert row['base_packet_sha256']==scene['control']['packet_sha256']
        if not row['accepted']:
            assert row['reason']=='base_over_cap' and row['base_bytes']>49152 and not row['attempts'];continue
        assert row['bytes']<=49152 and row['selected_rgb565_mismatches']==row['unselected_base_rgb565_mismatches']==0
        assert row['base_rgb_sha256']==scene['control']['base_rgb_sha256']
        if row['format']=='GM01':
            assert row['bytes']==row['base_bytes'] and row['packet_sha256']==row['base_packet_sha256'] and not row['selected']
        else:
            assert row['format']=='GH01' and row['bytes']==22+row['base_bytes']+sum(4+p['bytes'] for p in row['selected'])
        assert row['forward_bytes']==row['bytes']+59*((row['bytes']+1023)//1024) and row['reverse_bytes']==52
        if row['deadline_hit']:assert row['format']=='GM01'
assert len(rows)==60
sequence=r['temporal']['frames'];assert len(sequence)==12
for i,row in enumerate(sequence):
    assert row['frame_id']==i and row['accepted'] and row['anchor_id']==0 and row['bytes']<=49152
    assert row['selected_rgb565_mismatches']==row['unselected_base_rgb565_mismatches']==0
    if i%3==1:assert row['format']=='GM01' and row['max_attempts']==0
assert r['temporal']['GH01']+r['temporal']['GM01']==12
print('PASS: pinned sources, 60 bounded decisions, actual whole-packet accounting, paid rejected work, exact selected RGB565, 12 mixed-format unchanged-anchor frames')
