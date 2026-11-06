"""New DY71 source selection with exact legal legacy bundle endpoints."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[2]
base=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002'
parent=base/'board-source-v003/selection.json'
candidate=r/'fpga/experiments/cu66-v71/direct-system/constraint-exact-bundles-v001'
out=base/'board-source-v004';out.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(parent)=='fc35be057e180b37199b6c9c568cf2475f25fd0f3285d43cc87853f56f00e190'
assert sha(candidate/'timing-dy71-reviewed.tcl')=='8ef08b1ba7b7afd819307ac99b0148abdb2cd5cc0e017fe7f37756ffa54c31ae'
assert sha(candidate/'bundle-registers-exact.tcl')=='0dd885e324fcbd3a461ab70fe8fe6aa291f8afa7b35fb6c41abebaa382672346'
s=json.loads(parent.read_text());oldconstraints=parent.parent/'constraints'
shutil.copytree(oldconstraints,out/'constraints')
changed=[]
for name in ['timing-dy71-reviewed.tcl','bundle-registers-exact.tcl']:
 shutil.copyfile(candidate/name,out/'constraints'/name);changed.append(name)
for path in oldconstraints.iterdir():
 if path.name not in changed:assert sha(path)==sha(out/'constraints'/path.name)
s['constraints_sha256']={p.relative_to(r).as_posix():sha(p)for p in sorted((out/'constraints').iterdir())if p.is_file()}
s['constraint_entry']=(out/'constraints/timing-dy71-reviewed.tcl').relative_to(r).as_posix()
s['status']='FUNCTIONAL_SOURCE_GATES_PASS_EXACT_BUNDLE_CONSTRAINT_AUDIT_PENDING'
s['native_guard_references'].update({parent.relative_to(r).as_posix():sha(parent),
 (candidate/'derivation.json').relative_to(r).as_posix():sha(candidate/'derivation.json')})
s['legacy_parent_constraint_warning']='Prior response_reg.* matched LUT response_reg[17]_i_2: Constraints18-402 invalid startpoint. Parent timing is diagnostic, not a qualified constraints set.'
s['exact_legacy_bundle_bounds']='12 FF C ->12 FF D and32 FF C ->32 FF D, unchanged10ns, exact source/destination clocks; no non-register startpoint'
s['root_pending_gates']=['Fresh unconstrained-DCP exact bundle/object/coverage audit',
 'Full-board setup/hold/pulse/route/DRC/CDC signoff',
 'Actual v36 safe-staging RTL co-simulation pairing','Final BIT and physical qualification']
(out/'selection.json').write_text(json.dumps(s,indent=2)+'\n')
(out/'derivation.json').write_text(json.dumps(dict(parent_selection_sha256=sha(parent),
 source_RTL_changes=False,changed_constraints=changed,numeric_bounds_changed=False,
 obsolete_broad_bundle_selectors_removed=True,expected_primitive_counts=[12,12,32,32],
 hardware=False,BIT=False,Vivado_started=False),indent=2)+'\n')
print(json.dumps(dict(selection=str(out/'selection.json'),sha256=sha(out/'selection.json'))))
