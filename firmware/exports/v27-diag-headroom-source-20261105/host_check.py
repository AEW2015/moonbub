"""Portable host checks; all output goes to a new external evidence directory."""
import argparse,hashlib,json,runpy,subprocess,tempfile,sys
from pathlib import Path
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--cargo',default=str(Path.home()/'.cargo/bin/cargo.exe'));ap.add_argument('--rustc',default=str(Path.home()/'.cargo/bin/rustc.exe'));a=ap.parse_args()
out=Path(a.evidence).resolve();assert not out.is_relative_to(p) and not out.exists();out.mkdir(parents=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
b=json.loads((p/'source-bindings.json').read_text())
def guard():
 for x in b['source_files']:assert sha(p/x['path'])==x['sha256'],x['path']
 return {'status':'PASS','scope':'All558 selected input paths verified; no old checkout required'}
subprocess.run([sys.executable,str(p/'verify_source.py')],check=True);guard()
model=out/'model';model.mkdir();ns=runpy.run_path(str(p/'provenance/run_core_tests.py'),run_name='selected_v27_model_body')
ns['main'].__globals__.update({'P':p,'O':model,'RUSTC':a.rustc,'parent_guard':guard});ns['main']()
core=json.loads((model/'core-results.json').read_text());assert core['tests']==39 and len(core['compiler_rejections'])==24
with tempfile.TemporaryDirectory(prefix='v27-sdk-host-') as temp:
 cmd=[a.cargo,'+stable','test','--offline','--locked','--manifest-path',str(p/'tests/sdk-host/Cargo.toml'),'--target','x86_64-pc-windows-msvc','--target-dir',temp,'--','--test-threads=1','--nocapture']
 r=subprocess.run(cmd,cwd=p,capture_output=True,text=True);log=r.stdout+r.stderr;(out/'sdk-host.log').write_text(log);r.check_returncode()
 assert 'test result: ok. 66 passed; 0 failed' in log
guard();subprocess.run([sys.executable,str(p/'verify_source.py')],check=True)
(out/'result.json').write_text(json.dumps({'status':'PASS','model':39,'SDK_host':66,'expected_rejections':24,'SDK_command':cmd,'selected558_unchanged':True,'package_manifest_sha256':sha(p/'manifest.json'),'target_build':'NOT_RUN','hardware':'NONE','limits':'FakeSDK/host layout is not ESPABI,physical stack,heap or delivery proof'},indent=2)+'\n')
print('V27_RELOCATED_HOST_PASS39_66_24; package unchanged; output external')
