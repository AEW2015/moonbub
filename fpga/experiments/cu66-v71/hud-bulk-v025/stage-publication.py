"""Copy a bounded, hash-checked development snapshot into the clean publish tree.

Does not commit, push, flash, program or copy local credentials/build caches.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('C:/mb70');pub=Path('C:/mb70-publish-dy71-v40-20261107')
assert subprocess.check_output(['git','-C',str(pub),'branch','--show-current'],text=True).strip()=='feature/dy71-network-lab-v40-20261107'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def cp(src,rel):
 dst=pub/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(src,dst);assert sha(src)==sha(dst)
fw=root/'firmware/experiments/v43-dy71-bulk-hud-20261107'
snap=json.loads((fw/'evidence/source-snapshot-v002.json').read_text())['files']
for n,h in snap.items():
 assert sha(fw/n)==h,n
 cp(fw/n,fw.relative_to(root)/n)
for n in ['README.md','run-host.py','build-local-v002.py','package-local-v002.py','parent-v42.json']:
 cp(fw/n,fw.relative_to(root)/n)
for d in ['evidence/host-20261107-121621','evidence/package-v002']:
 for f in (fw/d).iterdir():
  if f.is_file() and f.suffix in ['.json','.log','.h','.def']:
   cp(f,f.relative_to(root))
for n in ['evidence/source-snapshot-v002.json','evidence/target-build-v002.json','evidence/target-check-v002.json','release-bulk-hud-v002/hashes.json','release-bulk-hud-v002/moonshine-rev4.json']:
 cp(fw/n,fw.relative_to(root)/n)
p=root/'fpga/experiments/cu66-v71/hud-bulk-v025'
for f in p.iterdir():
 if f.is_file() and f.suffix in ['.sv','.py','.md']:
  cp(f,f.relative_to(root))
for d in ['functional04','pins05','legacy05','xsim-vendor04','xsim-boundary01','xsim-full-synth02','mapping04','native-gold','boundary01']:
 if not(p/d).exists():continue
 for f in (p/d).iterdir():
  if f.is_file() and f.suffix in ['.json','.log','.rpt','.hex']:
   cp(f,f.relative_to(root))
build=root/'dy71-v025-20261107-v003'
bundle=p.relative_to(root)/'board-source-v003'
freeze=json.loads((build/'source-freeze.json').read_text())
for n,h in freeze.items():
 assert sha(build/'inputs'/n)==h,n
 cp(build/'inputs'/n,bundle/'inputs'/n)
for n in ['selection.json','source-freeze.json','synth.tcl','implementation.tcl','run-phase.py']:
 cp(build/n,bundle/n)
for n in ['synth-execution.json','implementation-execution.json','timing-summary.rpt','route-status.rpt','drc.rpt','bulk-port-gate.json']:
 if (build/n).exists():cp(build/n,bundle/n)
baseline=root/'dy71-v023-20261106-v001'
baseline_bundle=p.relative_to(root)/'baseline-source-v023'
bf=json.loads((baseline/'source-freeze.json').read_text())
for n,h in bf.items():
 assert sha(baseline/'inputs'/n)==h,n
 cp(baseline/'inputs'/n,baseline_bundle/'inputs'/n)
for n in ['selection.json','source-freeze.json']:cp(baseline/n,baseline_bundle/n)
if(p/'development-manifest.json').exists():cp(p/'development-manifest.json',p.relative_to(root)/'development-manifest.json')
note=root/'docs/cu66-v71/V43-BULK-HUD-DEVELOPMENT-20261107.md';cp(note,note.relative_to(root))
print('STAGED_SOURCE_AND_EXECUTED_EVIDENCE_NO_IMAGES_OR_HARDWARE')
