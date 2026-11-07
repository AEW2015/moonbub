"""Prepare (do not launch) a second implementation of the same qualified synthesis."""
from pathlib import Path
import hashlib,json,runpy,shutil
root=Path('C:/mb70');b=root/'dy71-v025-20261107-v003';o=b/'incremental01';p=Path(__file__).resolve().parent
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((p/'xsim-full-synth02/result.json').read_text())['status']=='PASS_XSIM_POST_SYNTH_BULK_NATIVE_WORDS'
assert json.loads((b/'synth-execution.json').read_text())['returncode']==0
ref=root/'dy71-v023-20261106-v001';rb=json.loads((ref/'image01/binding.json').read_text());assert sha(ref/'routed.dcp')==rb['checkpoint_sha256']
m=runpy.run_path(str(root/'scripts/cu66-v71/image_dy71_candidate.py'));rt=m['timing_metrics']((ref/'timing-summary.rpt').read_text())
o.mkdir();shutil.copytree(b/'inputs',o/'inputs')
for n in ['selection.json','source-freeze.json','synth-execution.json','constrained.dcp','run-phase.py','bulk-funcsim.v']:
 shutil.copyfile(b/n,o/n);assert sha(b/n)==sha(o/n)
shutil.copyfile(ref/'routed.dcp',o/'reference-v023-routed.dcp');assert sha(o/'reference-v023-routed.dcp')==rb['checkpoint_sha256']
s=(b/'implementation.tcl').read_text();assert s.count('\nopt_design\n')==1
s=s.replace('\nopt_design\n','\nopt_design\nread_checkpoint -incremental [file join $out reference-v023-routed.dcp]\nreport_incremental_reuse -file [file join $out incremental-reuse-postload.rpt]\n')
s=s.replace('write_checkpoint -force [file join $out routed.dcp]','report_incremental_reuse -file [file join $out incremental-reuse-routed.rpt]\nwrite_checkpoint -force [file join $out routed.dcp]')
(o/'implementation.tcl').write_text(s)
(o/'synthesis-lineage.json').write_text(json.dumps(dict(parent=str(b),parent_constrained_sha256=sha(b/'constrained.dcp'),parent_bulk_export_sha256=sha(b/'bulk-funcsim.v'),reference=str(ref/'routed.dcp'),reference_sha256=sha(ref/'routed.dcp'),reference_timing=rt,source_freeze_identical=sha(b/'source-freeze.json')==sha(o/'source-freeze.json'),scope='Same synthesized candidate and constraints; incremental placement/routing reuse only. No new RTL synthesis or changed I/O budgets.',guide='https://docs.amd.com/r/2025.1-English/ug904-vivado-implementation/Using-Incremental-Implementation-in-Non-Project-Mode'),indent=2)+'\n')
print('INCREMENTAL_OPTION_PREPARED_NOT_LAUNCHED',str(o))
