"""Portable offline source-only rebuild; never reads old checkpoints or writes BIT."""
import argparse,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--vivado',default=os.getenv('VIVADO_BIN'));ap.add_argument('--out',default='build-clean-001');ap.add_argument('--threads',type=int,default=4);a=ap.parse_args()
if not re.fullmatch(r'build-[A-Za-z0-9_.-]+',a.out) or '..' in a.out:raise SystemExit('--out must be a fresh build-* directory name')
if not 1<=a.threads<=16:raise SystemExit('--threads must be1..16')
exe=a.vivado or shutil.which('vivado') or shutil.which('vivado.bat')
if not exe:raise SystemExit('Provide --vivado /path/to/vivado or VIVADO_BIN; Vivado2025.2 is required')
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
binding=json.loads((p/'design-inputs.json').read_text())
assert binding['RTL_count']==21
for b in binding['files']:assert sha(p/b['path'])==b['sha256'],b['path']
inputs=[p/b['path'] for b in binding['files']]+[p/x for x in ['design-inputs.json','sources.tcl','build.tcl','build.py','proofs/overlay_reset_gate.tcl']]
before={x.relative_to(p).as_posix():sha(x) for x in inputs}
out=p/a.out;out.mkdir()
(out/'pre-source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
cmd=[exe,'-mode','batch','-source',str(p/'build.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(out),str(a.threads)]
start=time.time()
with (out/'launcher.log').open('wb') as f:r=subprocess.run(cmd,cwd=p,stdout=f,stderr=subprocess.STDOUT)
after={x.relative_to(p).as_posix():sha(x) for x in inputs}
(out/'post-source-hashes.json').write_text(json.dumps(after,indent=2)+'\n')
record={'returncode':r.returncode,'wall_seconds':time.time()-start,'command':cmd,'inputs_unchanged':before==after,'flow':'CLEAN_FULL_SOURCE_NO_INPUT_CHECKPOINT','threads':a.threads,'image_generation':'NOT_RUN','hardware':'NOT_ACCESSED'}
(out/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
assert before==after,'Clean build inputs changed'
print('Clean source build exit',r.returncode,'inputs unchanged; selected BIT was not read or replaced')
r.check_returncode()
