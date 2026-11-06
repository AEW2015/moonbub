"""Explicit successor selection: one-cycle IDCT validation + safe staging."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2]
d=r/'fpga/experiments/cu66-v71/direct-system'
out=d/'validpipe-v003';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=d/'syncsafe-math-v002/sources.json'
assert sha(parent)=='8451653672247a3bad012c3bb90b0d76fdee4802768b5964d6a0a0bf61783b9f'
base=r/'fpga/experiments/cu66-v71/codec/math-v004/cu71_base_pipeline_math.sv'
assert sha(base)=='9befe8fe345a22c9c7d6f08ad8937a7e6cd3c1d07c9bef13ede29709f2391fc3'
t=base.read_text();assert t.count('cu71_idct_indexed inverse(')==1
newbase=out/'cu71_base_pipeline_math.sv'
newbase.write_text(t.replace('cu71_idct_indexed inverse(','cu71_idct_validpipe inverse('),newline='\n')
idct=r/'fpga/experiments/cu66-v71/inverse-validpipe/cu71_idct_validpipe.sv'
assert sha(idct)=='817c1b60b26c022c112c0a048418cd4867905210f1e91cc47afe1eb4ee49dba1'
replacements={base.relative_to(r).as_posix():newbase.relative_to(r).as_posix(),
 'fpga/experiments/cu66-v71/inverse-index/cu71_idct_indexed.sv':idct.relative_to(r).as_posix()}
proofnames=['inverse-validpipe/evidence/functional01/result.json',
 'inverse-validpipe/evidence/validation-cancel02/result.json',
 'inverse-validpipe/evidence/ooc01/execution.json',
 'staging-timing/inverse-validpipe-review-v002.json']
proofs={}
for name in proofnames:
 p=r/'fpga/experiments/cu66-v71'/name;assert p.is_file();proofs[p.relative_to(r).as_posix()]=sha(p)
s=json.loads(parent.read_text())
s['sources']=[replacements.get(n,n)for n in s['sources']]
s['sources_sha256']={n:sha(r/n)for n in s['sources']}
s['parent_manifest_sha256']=sha(parent)
s['derivation']='Only IDCT module implementation/name changes via explicit base source; top/ports/other DUT sources identical; +1 accepted-tile work cycle.'
(out/'sources.json').write_text(json.dumps(s,indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(parent_manifest_sha256=sha(parent),
 parent_base_sha256=sha(base),new_base_sha256=sha(newbase),replacements=replacements,
 source_proofs=proofs,full_system_pending=True,hardware=False),indent=2)+'\n')
boardparent=d/'syncsafe-math-v002/board-source-v004/selection.json'
assert sha(boardparent)=='5598e4a8ade9341ca8f834352431a37203ae2ef8eb1cffaa80edda9c5d7ba64d'
b=json.loads(boardparent.read_text());b['sources']=[replacements.get(n,n)for n in b['sources']]
b['sources_sha256']={n:sha(r/n)for n in b['sources']}
b['native_guard_references'].update(proofs)
b['native_guard_references'][boardparent.relative_to(r).as_posix()]=sha(boardparent)
b['native_guard_references'][(out/'sources.json').relative_to(r).as_posix()]=sha(out/'sources.json')
b['status']='LEAF_FUNCTIONAL_AND_SAFE_CONTROL_GATES_PASS_FULL_SYSTEM_AND_BOARD_PENDING'
b['idct_validation_latency']='One extra work cycle per accepted tile; valid results match one-clock delayed parent, invalid-time out_error not a contract.'
bo=d/'syncsafe-math-v002/board-source-v005';bo.mkdir(exist_ok=False)
(bo/'selection.json').write_text(json.dumps(b,indent=2)+'\n')
(bo/'derivation.json').write_text(json.dumps(dict(parent_selection_sha256=sha(boardparent),
 source_replacements=replacements,constraints_byte_identical=True,top_RTL_unchanged=True,
 full_system_pending=True,hardware=False,Vivado_started=False,BIT=False),indent=2)+'\n')
print(json.dumps(dict(system_manifest_sha256=sha(out/'sources.json'),board_selection_sha256=sha(bo/'selection.json'))))
