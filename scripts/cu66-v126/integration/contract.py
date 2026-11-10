#!/usr/bin/env python3
"""Read-only V125 eighteen-source identity and reversible V126 producer contract."""
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
HANDOFF=ROOT/'experiments/python-gamebub-v120/handoff.json'
BASELINE=ROOT/'experiments/python-gamebub-v125/integration/results.json'
BASELINE_SHA='a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987'
PRODUCER_ALIAS='fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
PRODUCER=ROOT/'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'
ADMISSION_ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
ADMISSION=ROOT/'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
SCRATCH_ALIAS='fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
SCRATCH=ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'
QUEUE_ALIAS='fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
INHERITED_INDEXES={
 'tile':('experiments/python-gamebub-v125/integration/results.json',BASELINE_SHA),
 'owner':('experiments/python-gamebub-v124/integration/results.json','9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f'),
 'rank':('experiments/python-gamebub-v123/integration/results.json','0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00'),
 'bounds':('experiments/python-gamebub-v122/integration/results.json','c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4'),
 'queue':('experiments/python-gamebub-v121/integration/results.json','bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689')}
V125_CORRECTION_PINS={
 'scripts/cu66-v125/audit_functional_v2.py':'d32422e163a841f3114d891bca65054f70b82b4412d3ec4a294eca0c7456552d',
 'experiments/python-gamebub-v125/audit/full-independent-v2.json':'61c343b82cc12604e989380ffe415820e09ad0dfd5cfd71b7ebb91c7e5cf6a75',
 'experiments/python-gamebub-v125/audit/full-independent-v2-derivation.json':'a5c8be27f2307c84baa3b528879ed3495f67612ca5d084063cd4b8bb64afb3f6',
 'experiments/python-gamebub-v125/audit/full-independent-initial-failure.json':'b2e25c7122cc0b1535cd96565560f578a92038c37ac81617131b2fe8c00699ed',
 'experiments/python-gamebub-v125/audit/functional-v2-review.json':'4ba46a73552928e62d22349005f4310d75329fd04fccd36d71b5a4c8d8faca79'}

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

def verify_producer():
    production=load(PRODUCER.parent/'edit-recipe.json');base=load(BASELINE)
    assert production['schema']=='v126-producer-production-derivation-v1'
    assert production['candidate']==str(PRODUCER.relative_to(ROOT))and production['candidate_sha256']==sha(PRODUCER)
    assert production['original']==base['source_origins'][PRODUCER_ALIAS]['path']and production['original_sha256']==base['source_origins'][PRODUCER_ALIAS]['sha256']
    assert production['added_source_payload_bits']==24 and production['unchanged_other_origins']==17
    assert production['added_public_cycles']==production['added_synthesis_attributes']==production['old_assertions_removed']==production['old_private_value_contract_changes']==0
    original=(ROOT/production['original']).read_text();candidate=PRODUCER.read_text();text=original
    for edit in production['edits']:
        assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
    assert text==candidate
    for edit in reversed(production['edits']):
        assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
    assert text==original
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):assert block in candidate
    attrs=lambda text:re.findall(r'\(\*(.*?)\*\)',text,re.S)
    assert attrs(candidate)==attrs(original)
    assert 'logic [12:0] prepared_successor_tile;'in candidate and 'logic [10:0] prepared_successor_cell;'in candidate
    synth=re.sub(r'`ifndef SYNTHESIS.*?`endif','',candidate,flags=re.S)
    assert not re.search(r'\b(?:address_owner_|cell_owner_)',synth)
    packaging=load(PRODUCER.parent/'packaging.json')
    assert packaging['schema']=='v126-producer-single-module-packaging-v1'
    assert packaging['production_sha256']==sha(PRODUCER)and packaging['split_byte_offsets']==[]
    assert packaging['fragments']==[dict(filename=PRODUCER.name,bytes=len(PRODUCER.read_bytes()),sha256=sha(PRODUCER))]
    return production


def verify():
    assert sha(BASELINE)==BASELINE_SHA
    base=load(BASELINE)
    assert base['status']=='PASS_V125_TILE_FULL_FUNCTIONAL'
    assert base['all_original_oracles_retained']is True and base['exact_B_public_cycles']is True
    assert len(base['source_origins'])==18 and len(base['rtl_source_order'])==18
    for meta in base['source_origins'].values():assert sha(ROOT/meta['path'])==meta['sha256'],meta['path']
    expected_unchanged={ADMISSION_ALIAS:'2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb',SCRATCH_ALIAS:'12ad772136053d040d09770e0e98df6a49889757919993e3725c3ac70bafc5d7',QUEUE_ALIAS:'69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48'}
    for alias,digest in expected_unchanged.items():assert base['source_origins'][alias]['sha256']==digest
    for path,digest in V125_CORRECTION_PINS.items():assert sha(ROOT/path)==digest,path
    prior_audit=load(ROOT/'experiments/python-gamebub-v125/audit/full-independent-v2.json')
    assert prior_audit['status']=='PASS_INDEPENDENT_V125_FULL_FUNCTIONAL_AUDIT'and prior_audit['integration_index_sha256']==BASELINE_SHA
    assert prior_audit['exact_comparisons']==dict(spatial_stdout_event_and_canonical_streams=4,peer_stdout_event_and_canonical_streams=2,parent_stdout_and_terminal_stream_sets=4)
    assert load(ROOT/'experiments/python-gamebub-v125/audit/functional-v2-review.json')['status']=='PASS_STATIC_REVIEW'
    # Retain all old packaging byte-for-byte; only the new producer is a full-module addition.
    packaging=load(ADMISSION.parent/'packaging.json');data=ADMISSION.read_bytes()
    assert packaging['production_sha256']==sha(ADMISSION)and len(packaging['fragments'])==3
    cuts=[0]+packaging['split_byte_offsets']+[len(data)]
    assert len(cuts)==4 and cuts==sorted(cuts)
    for i,fragment in enumerate(packaging['fragments']):
        piece=data[cuts[i]:cuts[i+1]]
        assert fragment['bytes']==len(piece)and fragment['sha256']==hashlib.sha256(piece).hexdigest()
    packaging=load(SCRATCH.parent/'packaging.json')
    assert packaging['production_sha256']==sha(SCRATCH)and packaging['split_byte_offsets']==[]
    assert packaging['fragments']==[dict(filename=SCRATCH.name,bytes=len(SCRATCH.read_bytes()),sha256=sha(SCRATCH))]
    recipe=load(HERE/'derivation.json');audit_recipe=load(HERE/'audit-derivation.json');focus_recipe=load(HERE/'focused-runner-derivation.json')
    assert recipe['old_oracle_checks_removed']==recipe['exact_source_B_cycle_delta']==0
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
    verify_producer()
    return recipe


def source_map(sources,origins):
    base=load(BASELINE);expected=base['source_origins']
    assert len(sources)==len(origins)==18 and set(origins)==set(expected)
    assert {str(p.relative_to(ROOT))for p in sources}=={m['path']for m in origins.values()}
    for alias,meta in expected.items():
        if alias==PRODUCER_ALIAS:assert origins[alias]==dict(path=str(PRODUCER.relative_to(ROOT)),sha256=sha(PRODUCER))
        else:assert origins[alias]==meta,alias
    order=[str(PRODUCER.relative_to(ROOT))if p==expected[PRODUCER_ALIAS]['path']else p for p in base['rtl_source_order']]
    assert [str(p.relative_to(ROOT))for p in sources]==order,'Core18 RTL/include source order changed'
    return origins


def baseline(stage):
    key={'control-peer':'peer','spatial':'spatial','live-guard':'parent'}[stage]
    return resolve_pin(load(BASELINE)['stages'][key])


def files():
    result=[HANDOFF,BASELINE,ADMISSION.parent/'packaging.json',ADMISSION.parent/'edit-recipe.json',SCRATCH.parent/'packaging.json',SCRATCH.parent/'edit-recipes.json',PRODUCER.parent/'packaging.json',PRODUCER.parent/'edit-recipe.json',ROOT/'docs/cu66-v126/verification-plan.md',ROOT/'scripts/cu66-v126/audit_functional.py',ROOT/'scripts/cu66-v126/audit_terminal.py']
    result+=list(HERE.glob('*.py'))+[HERE/'derivation.json',HERE/'audit-derivation.json',HERE/'focused-runner-derivation.json',HERE/'live_guard/qualify.py',ROOT/'scripts/cu66-v126/producer/qualify.py']
    result+=[ROOT/r['original']for r in load(HERE/'derivation.json')['sources']+load(HERE/'audit-derivation.json')['sources']]
    result+=[ROOT/name for name in V125_CORRECTION_PINS]
    result+=inherited_focused()
    for key,stage in [('spatial','spatial'),('peer','control-peer'),('parent','live-guard')]:result+=[ROOT/load(BASELINE)['stages'][key]['path'],baseline(stage)[0]]
    return sorted(set(result))

if __name__=='__main__':verify();print('V126_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
