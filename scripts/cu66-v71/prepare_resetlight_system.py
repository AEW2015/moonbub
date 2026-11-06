"""Explicit valid-payload reset-light bindings after independent four-state tests."""
from pathlib import Path
import hashlib,json,re

root=Path(__file__).resolve().parents[2]
parent=root/'fpga/experiments/cu66-v71/codec/timing-v001'
out=root/'fpga/experiments/cu66-v71/codec/resetlight-v002'
out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(root).as_posix()
proof=root/'fpga/experiments/cu66-v71/inverse-reset/evidence/regression01/result.json'
test=json.loads(proof.read_text())
assert test['status']=='PASS_FOUR_STATE_VALID_PAYLOAD_GOLDENS_AND_RESET_ABORT_REPLAY'
for name,expected in test['source_sha256'].items():assert sha(root/name)==expected,name
selection=json.loads((parent/'sources.json').read_text())
for name,expected in selection['sources_sha256'].items():assert sha(root/name)==expected,name
replacement={}
bindings=[]
jobs=[
 ('cu71_base_pipeline_timing.sv','cu71_base_pipeline_resetlight.sv',{
  'cu71_base_pipeline_timing':'cu71_base_pipeline_resetlight',
  'cu71_dequant_pipe':'cu71_dequant_resetlight',
  'cu66_idct8x8':'cu71_idct_resetlight',
  'cu66_reconstruct_tile':'cu71_reconstruct_resetlight'}),
 ('cu71_receiver_timing.sv','cu71_receiver_resetlight.sv',{
  'cu71_receiver_timing':'cu71_receiver_resetlight',
  'cu71_base_pipeline_timing':'cu71_base_pipeline_resetlight'}),
 ('cu71_system_timing.sv','cu71_system_resetlight.sv',{
  'cu71_system_timing':'cu71_system_resetlight','cu71_receiver_timing':'cu71_receiver_resetlight'}),
]
for oldname,newname,modules in jobs:
 source=parent/oldname;text=source.read_text()
 for old,new in modules.items():
  assert len(re.findall(r'\b'+old+r'\b',text))==1,(oldname,old)
  text=re.sub(r'\b'+old+r'\b',new,text)
 target=out/newname;target.write_text(text,newline='\n')
 replacement[rel(source)]=rel(target)
 bindings.append(dict(parent=rel(source),parent_sha256=sha(source),candidate=rel(target),candidate_sha256=sha(target),modules=modules))
for old,new in [
 ('fpga/experiments/cu66-v71/dequant/cu71_dequant_pipe.sv','cu71_dequant_resetlight.sv'),
 ('fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv','cu71_idct_resetlight.sv'),
 ('fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv','cu71_reconstruct_resetlight.sv')]:
 replacement[old]='fpga/experiments/cu66-v71/inverse-reset/'+new
sources=[replacement.get(name,name)for name in selection['sources']]
(out/'sources.json').write_text(json.dumps(dict(top='cu71_system_resetlight',sources=sources,
 include_dirs=selection['include_dirs'],sources_sha256={name:sha(root/name)for name in sources},SIMULATION=False,
 scope='Valid-fenced payload reset removal only versus timing-v001; same clocks/math/cycle latency; fullsystem/route pending'),indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(status='STRUCTURAL_RESETLIGHT_INTEGRATION_PENDING',bindings=bindings,
 proof_sha256=sha(proof),removed_payload_reset_bits=6603,handshake_and_valid_payload_contract_unchanged=True,
 invalid_payload='Unspecified while valid=false; no new INIT-zero assumption',hardware=False),indent=2)+'\n')
print(out)
