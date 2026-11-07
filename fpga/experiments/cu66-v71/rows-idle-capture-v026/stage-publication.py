from pathlib import Path
import hashlib,json,shutil
root=Path('C:/mb70');p=Path(__file__).resolve().parent;pub=Path('C:/mb70-publish-dy71-v40-20261107');b=root/'dy71-v026-20261107-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def cp(f,rel=None):
 dst=pub/(rel if rel is not None else f.relative_to(root));dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst);assert sha(f)==sha(dst)
for f in p.iterdir():
 if f.is_file()and f.suffix in ['.sv','.py','.md','.json']:cp(f)
for folder in ['pair01','proof01','proof02','xsim-full-synth01']:
 for f in(p/folder).rglob('*'):
  if f.is_file()and f.suffix in ['.sv','.json','.log','.ys']:cp(f)
for corner in ['fast','slow']:
 d=p/('integration-'+corner+'01')
 for n in ['execution.json','source-binding.json','comparison.json','native-integration.log','native-raster-comparison.log','verilated-build.log','compare-executed.py']:
  if(d/n).exists():cp(d/n)
bundle=p.relative_to(root)/'board-source-v001';freeze=json.loads((b/'source-freeze.json').read_text())
for n,h in freeze.items():
 assert sha(b/'inputs'/n)==h;cp(b/'inputs'/n,bundle/'inputs'/n)
for n in ['selection.json','source-freeze.json','parent-and-proof-binding.json','synth.tcl','implementation.tcl','run-phase.py','synth-execution.json','implementation-execution.json','timing-summary.rpt','route-status.rpt','drc.rpt','bulk-port-gate.json']:
 if(b/n).exists():cp(b/n,bundle/n)
print('V026_SOURCE_AND_EVIDENCE_STAGED_NO_HARDWARE')
