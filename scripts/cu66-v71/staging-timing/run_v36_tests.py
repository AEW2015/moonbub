"""Rerun unchanged eighteen v36 SDK/native endpoint tests in unique snapshot."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parents[3];p=r/'firmware/experiments/v36-dual-local-fixture-20261106';o=r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/evidence/v36-tests01';o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();pins={}
for sub in ['native','tests','handheld/src/cu66']:
 for f in(p/sub).rglob('*'):
  if f.is_file():
   dest=o/'inputs'/f.relative_to(p);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);pins[f.relative_to(p).as_posix()]=sha(f)
(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n');e=o/'bin';e.mkdir();(e/'hud.def').write_text('LIBRARY hud\nEXPORTS\nv34_hud_create\nv34_hud_destroy\nv34_hud_transact\nv34_hud_stats\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+str(Path.home()/'.cargo/bin')+';'+os.environ['PATH']);steps=[]
commands=[('native',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',str(o/'inputs/native/endpoint.cpp'),'-o',str(e/'hud.dll')]),('import',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(e/'hud.def'),'/OUT:'+str(e/'hud.lib'),'/MACHINE:X64']),('compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(o/'inputs/tests/local.rs'),'-L','native='+str(e),'-l','dylib=hud','-o',str(e/'local-tests.exe')]),('test',[str(e/'local-tests.exe'),'--test-threads=1','--nocapture'])]
for label,cmd in commands:
 with(o/(label+'.log')).open('w')as log:q=subprocess.run(cmd,cwd=e,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 steps.append(dict(label=label,command=cmd,returncode=q.returncode));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0
assert 'test result: ok. 18 passed; 0 failed'in(o/'test.log').read_text()
(o/'result.json').write_text(json.dumps({'status':'PASS_UNCHANGED_V36_SDK_NATIVE_ENDPOINT_MODEL_TESTS','tests':18,'RTL':False,'hardware':False,'scope':'Actual unchanged SDK/native endpoint, software CSR model; separate safe RTL tests prove binding semantics','source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
