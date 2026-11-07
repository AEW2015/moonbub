from pathlib import Path
import hashlib,json,shutil
root=Path('C:/mb70');p=Path(__file__).resolve().parent;pub=Path('C:/mb70-publish-dy71-v40-20261107');b=root/'dy71-v027-20261107-v001';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def cp(f,rel=None):
 dst=pub/(rel if rel is not None else f.relative_to(root));dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst);assert sha(f)==sha(dst)
for f in p.iterdir():
 if f.is_file()and f.suffix in ['.sv','.py','.md','.json']:cp(f)
for folder in ['reset01','xsim-full-synth01']:
 for f in(p/folder).glob('*'):
  if f.is_file()and f.suffix in ['.json','.log']:cp(f)
for f in(b/'reset-mapping01').glob('*'):
 if f.is_file()and f.suffix in ['.json','.log','.rpt','.tsv','.tcl']:cp(f,p.relative_to(root)/'reset-mapping01'/f.name)
bundle=p.relative_to(root)/'board-source-v001'
for n,h in json.loads((b/'source-freeze.json').read_text()).items():assert sha(b/'inputs'/n)==h;cp(b/'inputs'/n,bundle/'inputs'/n)
for n in ['selection.json','source-freeze.json','synth.tcl','implementation.tcl','run-phase.py','synth-execution.json','implementation-execution.json','timing-summary.rpt','route-status.rpt','drc.rpt','bulk-port-gate.json']:
 if(b/n).exists():cp(b/n,bundle/n)
for folder in ['audit01','image01','image-flow']:
 for f in (b/folder).glob('*'):
  if f.is_file() and f.suffix in ['.json','.rpt','.tsv','.tcl','.log']:
   cp(f,p.relative_to(root)/'routed-image-evidence'/folder/f.name)
cp(root/'docs/cu66-v71/V43-V027-HARDWARE-COMPARISON-20261107.md')
print('V027_SOURCE_STAGED_NO_HARDWARE')
