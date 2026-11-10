#!/usr/bin/env python3
"""Read-only eighteen-source V122 identity and reversible V123 adapter checks."""
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
HANDOFF=ROOT/'experiments/python-gamebub-v120/handoff.json'
BASELINE=ROOT/'experiments/python-gamebub-v122/integration/results.json'
BASELINE_SHA='c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4'
SCRATCH_ALIAS='fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
SCRATCH=ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'
QUEUE_ALIAS='fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
QUEUE_SHA='69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())

def verify():
    assert sha(BASELINE)==BASELINE_SHA
    base=load(BASELINE)
    assert base['status']=='PASS_V122_BOUNDS_FULL_FUNCTIONAL'
    assert base['all_original_oracles_retained'] is True and base['exact_B_public_cycles'] is True
    for origin in base['source_origins'].values():assert sha(ROOT/origin['path'])==origin['sha256'],origin['path']
    assert base['source_origins'][QUEUE_ALIAS]['sha256']==QUEUE_SHA
    assert sha(SCRATCH)!=base['source_origins'][SCRATCH_ALIAS]['sha256']
    packaging=load(SCRATCH.parent/'packaging.json')
    assert packaging['production_sha256']==sha(SCRATCH) and packaging['split_byte_offsets']==[]
    assert packaging['fragments']==[dict(filename=SCRATCH.name,bytes=len(SCRATCH.read_bytes()),sha256=sha(SCRATCH))]
    admission=ROOT/'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'
    assert sha(admission)=='54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf'
    assert sha(admission)==load(admission.parent/'packaging.json')['production_sha256']
    recipe=load(HERE/'derivation.json')
    assert recipe['old_oracle_checks_removed']==0 and recipe['exact_source_B_cycle_delta']==0
    for record in recipe['sources']:
        original,candidate=ROOT/record['original'],ROOT/record['candidate']
        assert sha(original)==record['original_sha256'] and sha(candidate)==record['candidate_sha256']
        text=original.read_text()
        for edit in record['edits']:
            assert text.count(edit['before'])==edit['count'];text=text.replace(edit['before'],edit['after'])
        assert text==candidate.read_text()
        for edit in reversed(record['edits']):
            assert text.count(edit['after'])==edit['count'];text=text.replace(edit['after'],edit['before'])
        assert text==original.read_text()
    return recipe

def source_map(sources,origins):
    expected=load(BASELINE)['source_origins']
    assert len(sources)==len(origins)==18 and set(origins)==set(expected)
    assert {str(p.relative_to(ROOT)) for p in sources}=={m['path'] for m in origins.values()}
    for alias,original in expected.items():
        if alias==SCRATCH_ALIAS:assert origins[alias]==dict(path=str(SCRATCH.relative_to(ROOT)),sha256=sha(SCRATCH))
        else:assert origins[alias]==original,alias
    return origins

def baseline(stage):
    key={'control-peer':'peer','spatial':'spatial','live-guard':'parent'}[stage]
    pin=load(BASELINE)['stages'][key]
    selector=ROOT/pin['path'];assert sha(selector)==pin['sha256']
    chosen=load(selector);raw_path=ROOT/pin['receipt']['path'];assert sha(raw_path)==pin['receipt']['sha256']
    raw=load(raw_path)
    if 'selected_receipt' in chosen:assert raw=={k:v for k,v in chosen.items() if k!='selected_receipt'}
    else:assert sha(raw_path)==chosen.get('selected_report_sha256',chosen.get('sha256'))
    assert raw['status'].startswith('PASS') and raw['actual_RTL_run'] is True
    assert not raw.get('assertions_disabled_or_downgraded',False)
    for name,digest in raw['source_sha256'].items():assert sha(ROOT/name)==digest,name
    for name,digest in raw.get('artifact_sha256',raw.get('artifacts_sha256',{})).items():assert sha(raw_path.parent/name)==digest,name
    return raw_path,raw

def files():
    result=[HANDOFF,BASELINE,SCRATCH.parent/'packaging.json',SCRATCH.parent/'edit-recipes.json',ROOT/'docs/cu66-v123/verification-plan.md',ROOT/'scripts/cu66-v123/audit_functional.py',ROOT/'scripts/cu66-v123/audit_terminal.py']
    result+=list(HERE.glob('*.py'))+[HERE/'derivation.json',HERE/'live_guard/qualify.py']
    result += [ROOT/r['original'] for r in load(HERE/'derivation.json')['sources']]
    for key,stage in [('spatial','spatial'),('peer','control-peer'),('parent','live-guard')]:
        result+=[ROOT/load(BASELINE)['stages'][key]['path'],baseline(stage)[0]]
    return sorted(set(result))

if __name__=='__main__':verify();print('V123_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
