"""Structural canonical-storage integration after exact-cycle/target inference gates."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2];o=r/'fpga/experiments/cu66-v71/codec';o.mkdir(parents=True,exist_ok=True)
assert not any(o.iterdir()),'Preserve an already derived hierarchy'
rows=r/'fpga/experiments/cu66-v71/rows';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=rows/'evidence/equivalence03/result.json';m=json.loads(proof.read_text())
assert m['status']=='PASS_EXACT_CYCLE_ROWS_AND_INDEPENDENT_FULL_STREAM'
assert {name.replace('\\','/'):value for name,value in m['source_sha256'].items()}['fpga/experiments/cu66-v71/rows/cu71_tile_rows.sv']==sha(rows/'cu71_tile_rows.sv')
inference=rows/'evidence/ooc01/result.json';n=json.loads(inference.read_text());assert n['status']=='PASS_EXACT_TARGET_BRAM_INFERENCE'
assert n['source_sha256']==sha(rows/'cu71_tile_rows.sv')
jobs=[
 ('fpga/experiments/cu66-v69/rows/cu66_rows_sha256.sv','cu71_rows_sha256_bram.sv',{'cu66_rows_sha256':'cu71_rows_sha256_bram','cu66_tile_rows':'cu71_tile_rows'}),
 ('fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv','cu71_base_pipeline_bram.sv',{'cu66_base_pipeline':'cu71_base_pipeline_bram','cu66_rows_sha256':'cu71_rows_sha256_bram'}),
 ('fpga/experiments/cu66-v70/receiver/cu70_receiver.sv','cu71_receiver_bram.sv',{'cu70_receiver':'cu71_receiver_bram','cu66_base_pipeline':'cu71_base_pipeline_bram'})]
bindings=[]
for source,target,replacements in jobs:
 p=r/source;s=p.read_text()
 for old,new in replacements.items():assert old in s;s=s.replace(old,new)
 f=o/target;f.write_text(s,newline='\n');bindings.append(dict(parent=source,parent_sha256=sha(p),candidate=target,candidate_sha256=sha(f),replacements=replacements))
(o/'derivation.json').write_text(json.dumps(dict(status='STRUCTURAL_MODULE_REBIND_ONLY_FULL_REGRESSION_PENDING',bindings=bindings,rows_proof_sha256=sha(proof),inference_sha256=sha(inference)),indent=2)+'\n')
print(o)
