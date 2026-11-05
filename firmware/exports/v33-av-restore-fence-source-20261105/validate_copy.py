"""Fresh-copy integrity and host replay; external evidence only."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,re
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--cargo',default=str(Path.home()/'.cargo/bin/cargo.exe'));ap.add_argument('--rustc',default=str(Path.home()/'.cargo/bin/rustc.exe'));a=ap.parse_args()
out=Path(a.evidence).resolve(); assert not out.exists(); assert not out.is_relative_to(p) and not p.is_relative_to(out)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest(); before=sha(p/'manifest.json')
def integrity(root): subprocess.run([sys.executable,str(root/'verify_source.py')],check=True)
integrity(p);out.mkdir(parents=True);copy=out/'source-copy';shutil.copytree(p,copy);integrity(copy)
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';ev=copy/'evidence';ev.mkdir();shutil.copyfile(copy/'provenance/source-snapshot.json',ev/'source-snapshot.json')
steps=[]
def run(label,cmd):
 r=subprocess.run(cmd,cwd=copy,env=env,capture_output=True,text=True); log=out/(label+'.log');log.write_text(r.stdout+r.stderr);steps.append({'label':label,'command':cmd,'returncode':r.returncode,'log_sha256':sha(log)});r.check_returncode();return r.stdout+r.stderr
suites=[]
for name in ['cpl1','cpl1_sdk','trace_core','trace_usb','trace_protocol','trace_budget']:
 exe=ev/(name+'.exe');cmd=[a.rustc,'+stable','--edition=2021','--test',str(copy/'tests'/f'{name}.rs'),'-o',str(exe)]
 run(name+'-compile',cmd);text=run(name+'-run',[str(exe),'--test-threads=1','--nocapture']);n=int(re.search(r'test result: ok\. (\d+) passed',text)[1]);suites.append({'suite':name,'tests':n})
# Existing in-tree harness generates ownership tests in the disposable copied tree.
text=run('core-model',[sys.executable,str(copy/'run_core_tests.py')]);model=json.loads((ev/'core-results.json').read_text());assert model['tests']==39 and len(model['compiler_rejections'])==24
with tempfile.TemporaryDirectory(prefix='v33-sdk-host-') as td:
 cmd=[a.cargo,'+stable','test','--offline','--locked','--manifest-path',str(copy/'tests/sdk-host/Cargo.toml'),'--target','x86_64-pc-windows-msvc','--target-dir',td,'--','--test-threads=1','--nocapture'];text=run('sdk-host',cmd);assert 'test result: ok. 83 passed; 0 failed' in text
shutil.copytree(ev,out/'host-results');shutil.rmtree(ev);integrity(copy);integrity(p);assert sha(p/'manifest.json')==before
result={'status':'PASS','manifest_sha256':before,'selected_inputs':574,'original_and_clean_copy_integrity':'PASS','host_suites':suites,'model':39,'SDK_host':83,'expected_rejections':24,'target_build':'NOT_RUN','hardware':'NONE','steps':steps}
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
rows=[]
for f in sorted(out.rglob('*')):
 if f.is_file():rows.append({'path':f.relative_to(out).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
(out/'evidence-manifest.json').write_text(json.dumps({'files':rows},indent=2)+'\n')
print('V33_COPIED_EXPORT_HOST_REPLAY_PASS',sum(x['tests'] for x in suites),'Rust suite tests; 39 model; 83 SDK-host; 24 expected rejects')
