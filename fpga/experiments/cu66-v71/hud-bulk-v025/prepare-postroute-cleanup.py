"""One same-source physical cleanup of the measured 92ps setup miss; no hardware."""
from pathlib import Path
import hashlib,json,shutil
p=Path(__file__).resolve().parent;b=Path('C:/mb70/dy71-v025-20261107-v003');o=b/'postroute01';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
e=json.loads((b/'implementation-execution.json').read_text());assert e['returncode']==0 and e['completion_marker'] and e['inputs_unchanged'];o.mkdir();shutil.copytree(b/'inputs',o/'inputs')
for n in ['selection.json','source-freeze.json','synth-execution.json','constrained.dcp','bulk-funcsim.v','run-phase.py']:shutil.copyfile(b/n,o/n)
shutil.copyfile(b/'routed.dcp',o/'routed-input.dcp')
s=(b/'implementation.tcl').read_text();s=s.replace('open_checkpoint [file join $out constrained.dcp]','open_checkpoint [file join $out routed-input.dcp]')
start=s.index('\nopt_design\n');end=s.index('phys_opt_design -directive AggressiveExplore',start)
s=s[:start]+'\n# Targeted cleanup from the exact failed fully-routed parent.\n'+s[end:]
(o/'implementation.tcl').write_text(s)
(o/'lineage.json').write_text(json.dumps(dict(parent=str(b),routed_input_sha256=sha(b/'routed.dcp'),constrained_sha256=sha(b/'constrained.dcp'),source_freeze_sha256=sha(b/'source-freeze.json'),scope='Same RTL, constraints, synthesis and measured failed routed checkpoint. One additional native post-route physical optimization and cleanup route; not a resynthesis or timing waiver.',hardware=False),indent=2)+'\n')
print('POSTROUTE_CLEANUP_PREPARED',str(o))
