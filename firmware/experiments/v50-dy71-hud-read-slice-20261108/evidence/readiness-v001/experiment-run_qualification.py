from pathlib import Path
import subprocess,os,json,time,hashlib
root=Path(__file__).resolve().parent;env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');steps=[]
for v in ('control','candidate'):
 cmd=['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-fstack-usage','-I',str(root/v),str(root/'harness/read_slice.cpp'),str(root/v/'native/endpoint.cpp'),'-o',str(root/v/'read_slice.exe')]
 with(root/(v+'-compile.log')).open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:print((root/(v+'-compile.log')).read_text());raise SystemExit(r.returncode)
 t=time.perf_counter();cmd=[str(root/v/'read_slice.exe'),'C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107/handheld/src/cu66/fixtures/prepare12','C:/moon/maintenance/v45-sequence/qualification']
 with(root/(v+'-qualification.log')).open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 steps.append({'variant':v,'command':cmd,'exit':r.returncode,'host_process_seconds':time.perf_counter()-t});(root/'qualification-execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(v,r.returncode,steps[-1]['host_process_seconds'],flush=True)
 if r.returncode:print((root/(v+'-qualification.log')).read_text());raise SystemExit(r.returncode)
a=(root/'control-qualification.log').read_text();b=(root/'candidate-qualification.log').read_text();assert a==b,'full-response aggregate mismatch';(root/'QUALIFICATION.json').write_text(json.dumps({'status':'PASS','response_aggregate':a.strip(),'target':'NOT_BUILT','hardware':'NOT_TOUCHED'},indent=2)+'\n');print(a)
