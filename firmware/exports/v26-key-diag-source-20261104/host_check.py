"""Portable selected host tests; target SDK code is mocked, never flashed."""
import argparse,hashlib,json,os,runpy,shutil,subprocess,tempfile,time,re
from pathlib import Path
p=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--cargo');ap.add_argument('--rustc');a=ap.parse_args()
cargo=a.cargo or shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo.exe');rustc=a.rustc or shutil.which('rustc') or str(Path.home()/'.cargo/bin/rustc.exe')
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
b=json.loads((p/'source-bindings.json').read_text());before={x['path']:sha(p/x['path']) for x in b['source_files']}
def guard():
 for x in b['source_files']:assert sha(p/x['path'])==x['sha256'],x['path']
 return {'status':'PASS','scope':'Local575-selected-input integrity guard; external parent-v25 checkout not required'}
guard();out=p/'checks/host';out.mkdir(parents=True,exist_ok=True);start=time.time()
with tempfile.TemporaryDirectory(prefix='v26-source-host-') as temp:
 t=Path(temp);ns=runpy.run_path(str(p/'provenance/selected-inputs/run_core_tests.py'),run_name='selected_v26_test_body')
 ns['main'].__globals__.update({'P':p,'O':t,'RUSTC':rustc,'parent_guard':guard})
 ns['main']()
 core=json.loads((t/'core-results.json').read_text());assert core['tests']==39 and len(core['compiler_rejections'])==24
 for x in t.iterdir():
  if x.suffix in {'.log','.json','.rs'}:shutil.copyfile(x,out/x.name)
 cmd=[cargo,'+stable','test','--offline','--locked','--manifest-path',str(p/'tests/sdk-host/Cargo.toml'),'--target','x86_64-pc-windows-msvc','--target-dir',str(t/'sdk-target'),'--','--test-threads=1','--nocapture']
 r=subprocess.run(cmd,cwd=p,capture_output=True,text=True);(out/'sdk-host.log').write_text(r.stdout+r.stderr);r.check_returncode()
 assert re.search(r'test result: ok\. 66 passed; 0 failed',r.stdout+r.stderr)
guard();assert before=={x:sha(p/x) for x in before}
versions={}
for name,command in [('rustc',[rustc,'+stable','-Vv']),('cargo',[cargo,'+stable','-V'])]:versions[name]=subprocess.run(command,capture_output=True,text=True,check=True).stdout
(out/'result.json').write_text(json.dumps({'status':'PASS','model_tests':39,'SDK_host_tests':66,'expected_compiler_rejections':24,'wall_seconds':time.time()-start,'SDK_command':cmd,'tool_versions':versions,'selected_input_hashes_unchanged':True,'guard_adaptation':'Reused exactselectedtestbody; onlyP/O/toolpaths and localintegrityguard injected; no externalv25 checkout','target_build':'NOT_RUN','hardware':'NONE','limits':'FakeSDK/host64 layout is not ESPABI,physicaldrain or stack/heap proof'},indent=2)+'\n')
print('RELOCATED_HOST_PASS39_MODEL_66_SDK_24_EXPECTED_REJECTIONS; source unchanged')
