from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v025-20261107-v003');old=b/'postroute01';out=b/'postroute02';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
e=json.loads((old/'implementation-execution.json').read_text());assert e['returncode']==0 and e['completion_marker'] and e['inputs_unchanged'];out.mkdir();shutil.copytree(old/'inputs',out/'inputs')
for n in ['selection.json','source-freeze.json','synth-execution.json','constrained.dcp','bulk-funcsim.v','run-phase.py']:shutil.copyfile(old/n,out/n)
shutil.copyfile(old/'routed.dcp',out/'routed-input.dcp');s=(old/'implementation.tcl').read_text();assert s.count('phys_opt_design -directive AggressiveExplore')==1
s=s.replace('phys_opt_design -directive AggressiveExplore','phys_opt_design -critical_pin_opt -routing_opt -clock_opt');(out/'implementation.tcl').write_text(s)
(out/'lineage.json').write_text(json.dumps(dict(parent=str(old),routed_input_sha256=sha(old/'routed.dcp'),root_synthesis=str(b),constrained_sha256=sha(b/'constrained.dcp'),source_freeze_sha256=sha(b/'source-freeze.json'),measured_parent_setup_ns=-0.006,measured_parent_hold_ns=0.027,target='joint_core_reset_reg[3]/C to entropy/tile_reg[24][10]/R',scope='Same RTL/constraints; native critical-pin/routing/clock-skew optimization only, followed by strict routed timing gates. Clock periods and phases remain unchanged.',hardware=False),indent=2)+'\n')
print('POSTROUTE02_PREPARED')
