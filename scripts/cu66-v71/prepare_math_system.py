"""Bind cycle-preserving hash/index successors after isolated functional proofs."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[2]
out=root/'fpga/experiments/cu66-v71/codec/math-v004';out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(root).as_posix()
hash_source=root/'fpga/experiments/cu66-v71/hash/cu71_sha256_bytes_lookahead.sv'
idct_source=root/'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv'
assert sha(hash_source)=='f29332de9fe41ba679bef91fba71698e4efb4a05860221ab0ea3268e19c28006'
assert sha(idct_source)=='fe1d7f3684ac7e8c15bc80e5a9b4734863103510faa2087d75b00a6b94d2d41d'
index_proof=root/'fpga/experiments/cu66-v71/inverse-index/evidence/regression01/result.json'
assert json.loads(index_proof.read_text())['status']=='PASS_EXACT_CYCLE_PARENT_AND_3471_GOLDENS_TWO_SEEDS'
parent=root/'fpga/experiments/cu66-v71/codec/address-v003'
selection=json.loads((parent/'sources.json').read_text())
for n,h in selection['sources_sha256'].items():assert sha(root/n)==h,n
v71=root/'fpga/experiments/cu66-v71'
jobs=[
 (v71/'codec/cu71_rows_sha256_bram.sv','cu71_rows_sha256_fast.sv',{'cu71_rows_sha256_bram':'cu71_rows_sha256_fast','cu66_sha256_bytes':'cu71_sha256_bytes_lookahead'}),
 (v71/'codec/resetlight-v002/cu71_base_pipeline_resetlight.sv','cu71_base_pipeline_math.sv',{'cu71_base_pipeline_resetlight':'cu71_base_pipeline_math','cu71_rows_sha256_bram':'cu71_rows_sha256_fast','cu71_idct_resetlight':'cu71_idct_indexed'}),
 (v71/'codec/resetlight-v002/cu71_receiver_resetlight.sv','cu71_receiver_math.sv',{'cu71_receiver_resetlight':'cu71_receiver_math','cu71_base_pipeline_resetlight':'cu71_base_pipeline_math'}),
 (parent/'cu71_system_addresspipe.sv','cu71_system_math.sv',{'cu71_system_addresspipe':'cu71_system_math','cu71_receiver_resetlight':'cu71_receiver_math'}),
]
replacements={};bindings=[]
for source,name,modules in jobs:
 text=source.read_text()
 for old,new in modules.items():
  assert len(re.findall(r'\b'+old+r'\b',text))==1,(source,old)
  text=re.sub(r'\b'+old+r'\b',new,text)
 target=out/name;target.write_text(text,newline='\n');replacements[rel(source)]=rel(target)
 bindings.append(dict(parent=rel(source),parent_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),modules=modules))
replacements.update({'fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv':rel(hash_source),
 'fpga/experiments/cu66-v71/inverse-reset/cu71_idct_resetlight.sv':rel(idct_source)})
sources=[replacements.get(n,n)for n in selection['sources']]
(out/'sources.json').write_text(json.dumps(dict(top='cu71_system_math',sources=sources,include_dirs=selection['include_dirs'],
 sources_sha256={n:sha(root/n)for n in sources},SIMULATION=False,scope='Cycle-preserving hash-lookahead/carry-save and bounded IDCT indices vs address-v003; whole integration/routed gates pending'),indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(status='STRUCTURAL_MATH_BINDING_INTEGRATION_PENDING',bindings=bindings,
 hash_source_sha256=sha(hash_source),idct_source_sha256=sha(idct_source),index_proof_sha256=sha(index_proof),
 added_public_latency_cycles=0,hardware=False,BIT=False),indent=2)+'\n')
print(out)
