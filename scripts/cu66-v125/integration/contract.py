#!/usr/bin/env python3
"""Read-only eighteen-source V124 identity and reversible V125 integration contract."""
import hashlib
import json
import re
import sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
HANDOFF=ROOT/'experiments/python-gamebub-v120/handoff.json'
BASELINE=ROOT/'experiments/python-gamebub-v124/integration/results.json'
BASELINE_SHA='9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f'
ADMISSION_ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
ADMISSION=ROOT/'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
PRODUCER_ALIAS='fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
PRODUCER=ROOT/'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'
SCRATCH_ALIAS='fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
SCRATCH=ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'
QUEUE_ALIAS='fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
QUEUE_SHA='69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48'
INHERITED_INDEXES={
 'owner':('experiments/python-gamebub-v124/integration/results.json',BASELINE_SHA),
 'rank':('experiments/python-gamebub-v123/integration/results.json','0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00'),
 'bounds':('experiments/python-gamebub-v122/integration/results.json','c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4'),
 'queue':('experiments/python-gamebub-v121/integration/results.json','bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689')}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def strict_commands(raw):
    commands=[c if isinstance(c,list) else c['argv']for c in raw['commands']]
    compiles=[c for c in commands if 'verilator'in c and '--cc'in c]
    assert compiles and all('--assert'in c and '-Wall'in c and '-Wno-fatal'not in c for c in compiles)
    executable=[c for c in compiles if '--exe'in c]
    libraries=[c for c in compiles if '--exe'not in c]
    assert executable and all('-CFLAGS'in c and '-Werror'in c[c.index('-CFLAGS')+1]for c in executable)
    assert all('--build'in c and '--top-module'in c and c[c.index('--top-module')+1]=='v97_forward'for c in libraries)
    adapters=[c for c in commands if 'g++'in c]
    assert all(all(f in c for f in ('-std=c++17','-O2','-Wall','-Wextra','-Werror'))for c in adapters)
    assert (len(libraries)==len(adapters)==1)if raw.get('custom_transport_status')else(not libraries and not adapters)

def resolve_pin(pin):
    selector=ROOT/pin['path'];assert sha(selector)==pin['sha256']
    chosen=load(selector);raw_path=ROOT/pin['receipt']['path'];assert sha(raw_path)==pin['receipt']['sha256']
    raw=load(raw_path)
    if 'selected_receipt'in chosen:assert raw=={k:v for k,v in chosen.items()if k!='selected_receipt'}
    else:assert sha(raw_path)==chosen.get('selected_report_sha256',chosen.get('sha256'))
    assert raw['status'].startswith('PASS')and raw['actual_RTL_run']is True
    assert raw.get('assertions_disabled_or_downgraded',False)is False
    for name,digest in raw['source_sha256'].items():assert sha(ROOT/name)==digest,name
    artifacts=raw.get('artifact_sha256',raw.get('artifacts_sha256',{}));assert artifacts
    for name,digest in artifacts.items():assert sha(raw_path.parent/name)==digest,name
    strict_commands(raw)
    return raw_path,raw

def inherited_focused():
    result=[]
    for kind,(name,digest)in INHERITED_INDEXES.items():
        index=ROOT/name;assert sha(index)==digest
        pin=load(index)['stages']['focused'];raw,_=resolve_pin(pin)
        result+=[index,ROOT/pin['path'],raw]
    return result

def verify():
    assert sha(BASELINE)==BASELINE_SHA
    base=load(BASELINE)
    assert base['status']=='PASS_V124_OWNER_FULL_FUNCTIONAL'
    assert base['all_original_oracles_retained']is True and base['exact_B_public_cycles']is True
    for origin in base['source_origins'].values():assert sha(ROOT/origin['path'])==origin['sha256'],origin['path']
    assert base['source_origins'][QUEUE_ALIAS]['sha256']==QUEUE_SHA
    assert sha(PRODUCER)==base['source_origins'][PRODUCER_ALIAS]['sha256']=='963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53'
    assert sha(SCRATCH)==base['source_origins'][SCRATCH_ALIAS]['sha256']=='12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7'
    for source in (PRODUCER,SCRATCH):
        packaging=load(source.parent/'packaging.json')
        assert packaging['production_sha256']==sha(source)and packaging['split_byte_offsets']==[]
        assert packaging['fragments']==[dict(filename=source.name,bytes=len(source.read_bytes()),sha256=sha(source))]
    assert sha(ADMISSION)!=base['source_origins'][ADMISSION_ALIAS]['sha256']
    production_recipe=load(ADMISSION.parent/'edit-recipe.json')
    assert production_recipe['candidate']==str(ADMISSION.relative_to(ROOT))and production_recipe['candidate_sha256']==sha(ADMISSION)
    assert production_recipe['original']==base['source_origins'][ADMISSION_ALIAS]['path']and production_recipe['original_sha256']==base['source_origins'][ADMISSION_ALIAS]['sha256']
    assert production_recipe['added_source_payload_bits']==3
    assert production_recipe['added_public_cycles']==production_recipe['added_synthesis_attributes']==production_recipe['old_assertions_removed']==production_recipe['old_private_value_contract_changes']==0
    original_admission=ROOT/production_recipe['original'];text=original_admission.read_text()
    for edit in production_recipe['edits']:
        assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
    assert text==ADMISSION.read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original_admission.read_text(),re.S):assert block in text
    for edit in reversed(production_recipe['edits']):
        assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
    assert text==original_admission.read_text()

    packaging=load(ADMISSION.parent/'packaging.json');data=ADMISSION.read_bytes()
    assert packaging['production_sha256']==sha(ADMISSION)and len(packaging['fragments'])==3
    cuts=[0]+packaging['split_byte_offsets']+[len(data)]
    assert len(cuts)==4 and cuts==sorted(cuts)and packaging['fragments'][0]['filename']==ADMISSION.name
    assert len({f['filename']for f in packaging['fragments']})==3
    for i,fragment in enumerate(packaging['fragments']):
        assert Path(fragment['filename']).name==fragment['filename']and fragment['filename'].endswith('.sv')
        piece=data[cuts[i]:cuts[i+1]]
        assert len(piece)==fragment['bytes']and hashlib.sha256(piece).hexdigest()==fragment['sha256']
    recipe=load(HERE/'derivation.json');audit_recipe=load(HERE/'audit-derivation.json');focus_recipe=load(HERE/'focused-runner-derivation.json')
    assert recipe['old_oracle_checks_removed']==0 and recipe['exact_source_B_cycle_delta']==0
    assert audit_recipe['old_integrity_check_calls_removed']==0
    for record in recipe['sources']+audit_recipe['sources']+focus_recipe['sources']:
        original,candidate=ROOT/record['original'],ROOT/record['candidate']
        assert sha(original)==record['original_sha256']and sha(candidate)==record['candidate_sha256']
        text=original.read_text()
        for edit in record['edits']:
            assert text.count(edit['before'])==edit['count'];text=text.replace(edit['before'],edit['after'])
        assert text==candidate.read_text()
        for edit in reversed(record['edits']):
            assert text.count(edit['after'])==edit['count'];text=text.replace(edit['after'],edit['before'])
        assert text==original.read_text()
    inherited_focused()
    return recipe

def source_map(sources,origins):
    expected=load(BASELINE)['source_origins']
    assert len(sources)==len(origins)==18 and set(origins)==set(expected)
    assert {str(p.relative_to(ROOT))for p in sources}=={m['path']for m in origins.values()}
    for alias,original in expected.items():
        if alias==ADMISSION_ALIAS:assert origins[alias]==dict(path=str(ADMISSION.relative_to(ROOT)),sha256=sha(ADMISSION))
        else:assert origins[alias]==original,alias
    order=[str(ADMISSION.relative_to(ROOT))if p==expected[ADMISSION_ALIAS]['path']else p for p in load(BASELINE)['rtl_source_order']]
    assert [str(p.relative_to(ROOT))for p in sources]==order,'RTL/include source order changed'
    return origins

def baseline(stage):
    key={'control-peer':'peer','spatial':'spatial','live-guard':'parent'}[stage]
    return resolve_pin(load(BASELINE)['stages'][key])

def files():
    result=[HANDOFF,BASELINE,ADMISSION.parent/'packaging.json',ADMISSION.parent/'edit-recipe.json',PRODUCER.parent/'packaging.json',PRODUCER.parent/'edit-recipes.json',SCRATCH.parent/'packaging.json',SCRATCH.parent/'edit-recipes.json',ROOT/'docs/cu66-v125/verification-plan.md',ROOT/'scripts/cu66-v125/audit_functional.py',ROOT/'scripts/cu66-v125/audit_terminal.py']
    result+=list(HERE.glob('*.py'))+[HERE/'derivation.json',HERE/'audit-derivation.json',HERE/'focused-runner-derivation.json',HERE/'live_guard/qualify.py',ROOT/'scripts/cu66-v125/tile/qualify.py']
    result+=[ROOT/r['original']for r in load(HERE/'derivation.json')['sources']+load(HERE/'audit-derivation.json')['sources']]
    result+=inherited_focused()
    for key,stage in [('spatial','spatial'),('peer','control-peer'),('parent','live-guard')]:
        result+=[ROOT/load(BASELINE)['stages'][key]['path'],baseline(stage)[0]]
    return sorted(set(result))

if __name__=='__main__':verify();print('V125_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
