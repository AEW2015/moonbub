"""Portable host checks; all output goes to a new external evidence directory."""
import argparse,hashlib,json,runpy,subprocess,tempfile,sys,os,re
from pathlib import Path
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--evidence',required=True);ap.add_argument('--cargo',default=str(Path.home()/'.cargo/bin/cargo.exe'));ap.add_argument('--rustc',default=str(Path.home()/'.cargo/bin/rustc.exe'));a=ap.parse_args()
os.environ['PYTHONDONTWRITEBYTECODE']='1'
out=Path(a.evidence).resolve();assert not out.is_relative_to(p) and not out.exists();out.mkdir(parents=True)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
b=json.loads((p/'source-bindings.json').read_text())
def guard():
 for x in b['source_files']:assert sha(p/x['path'])==x['sha256'],x['path']
 return {'status':'PASS','scope':'All568 selected input paths verified; no old checkout required'}
subprocess.run([sys.executable,str(p/'verify_source.py')],check=True);guard()
trace_suites=[]
for name in ['trace_core','trace_usb','trace_protocol','trace_budget']:
 command=[a.rustc,'+stable','--edition=2021','--test',str(p/'tests'/f'{name}.rs'),'-o',str(out/f'{name}.exe')]
 r=subprocess.run(command,capture_output=True,text=True);(out/f'{name}-compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
 r=subprocess.run([str(out/f'{name}.exe'),'--test-threads=1','--nocapture'],capture_output=True,text=True);log=r.stdout+r.stderr;(out/f'{name}-run.log').write_text(log);r.check_returncode()
 trace_suites.append({'suite':name,'tests':int(re.search(r'test result: ok\. (\d+) passed',log)[1])})
cmd=[sys.executable,'-m','unittest','discover','-s',str(p/'tests'),'-p','test_collect_gamebub_trace.py','-v']
r=subprocess.run(cmd,capture_output=True,text=True);log=r.stdout+r.stderr;(out/'collector-tests.log').write_text(log);r.check_returncode()
trace_suites.append({'suite':'collector','tests':int(re.search(r'Ran (\d+) tests',log)[1])})
model=out/'model';model.mkdir();ns=runpy.run_path(str(p/'provenance/run_core_tests.py'),run_name='selected_v31_model_body')
ns['main'].__globals__.update({'P':p,'O':model,'RUSTC':a.rustc,'parent_guard':guard});ns['main']()
core=json.loads((model/'core-results.json').read_text());assert core['tests']==39 and len(core['compiler_rejections'])==24
with tempfile.TemporaryDirectory(prefix='v31-sdk-host-') as temp:
 cmd=[a.cargo,'+stable','test','--offline','--locked','--manifest-path',str(p/'tests/sdk-host/Cargo.toml'),'--target','x86_64-pc-windows-msvc','--target-dir',temp,'--','--test-threads=1','--nocapture']
 r=subprocess.run(cmd,cwd=p,capture_output=True,text=True);log=r.stdout+r.stderr;(out/'sdk-host.log').write_text(log);r.check_returncode()
 assert 'test result: ok. 66 passed; 0 failed' in log
guard();subprocess.run([sys.executable,str(p/'verify_source.py')],check=True)
(out/'result.json').write_text(json.dumps({'status':'PASS','trace_suites':trace_suites,'model':39,'SDK_host':66,'expected_rejections':24,'SDK_command':cmd,'selected568_unchanged':True,'package_manifest_sha256':sha(p/'manifest.json'),'target_build':'NOT_RUN','hardware':'NONE','limits':'FakeSDK/host layout is not ESPABI,physical stack,heap or delivery proof'},indent=2)+'\n')
print('V31_RELOCATED_HOST_PASS39_66_24; package unchanged; output external')
