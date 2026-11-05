"""Replay source/host/path checks in a fresh copy, with outputs outside it."""
import argparse,hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--cargo',default=str(Path.home()/'.cargo/bin/cargo.exe'));ap.add_argument('--rustc',default=str(Path.home()/'.cargo/bin/rustc.exe'));a=ap.parse_args()
out=Path(a.evidence).resolve();assert not out.is_relative_to(p) and not p.is_relative_to(out) and not out.exists()
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(p/'verify_source.py')],check=True)
before=sha(p/'manifest.json');out.mkdir(parents=True);copy=out/'source-copy';shutil.copytree(p,copy)
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';steps=[]
for label,cmd in [('integrity',[sys.executable,str(copy/'verify_source.py')]),('paths',[sys.executable,str(copy/'inspect_sources.py'),'--evidence',str(out/'paths')]),('host',[sys.executable,str(copy/'host_check.py'),'--evidence',str(out/'host'),'--cargo',a.cargo,'--rustc',a.rustc]),('metadata',[sys.executable,str(copy/'check_metadata.py'),'--evidence',str(out/'metadata'),'--cargo',a.cargo])]:
 r=subprocess.run(cmd,env=env,capture_output=True,text=True);f=out/(label+'.log');f.write_text(r.stdout+r.stderr);steps.append({'label':label,'command':cmd,'returncode':r.returncode,'log_sha256':sha(f)});r.check_returncode()
for root in [p,copy]:subprocess.run([sys.executable,str(root/'verify_source.py')],env=env,check=True)
assert sha(p/'manifest.json')==sha(copy/'manifest.json')==before
(out/'result.json').write_text(json.dumps({'status':'PASS','manifest_sha256':before,'original_export_unchanged':True,'copied_export_unchanged':True,'all558_input_paths_verified':True,'steps':steps,'outputs':{f.relative_to(out).as_posix():sha(f)for f in out.rglob('*')if f.is_file() and not f.is_relative_to(copy)},'target_build':'NOT_RUN','hardware':'NONE'},indent=2)+'\n')
print('V27_COPY_VALIDATION_PASS; all558 source paths and complete exports unchanged')
