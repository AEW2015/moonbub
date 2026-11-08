from pathlib import Path
import os,subprocess,time,json,re,statistics
root=Path(__file__).resolve().parent;out=root/'benchmark01';out.mkdir(exist_ok=False)
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp');rows=[]
for v in ('control','candidate'):
 cmd=['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-fstack-usage','-I',str(root/v),str(root/'harness/benchmark.cpp'),str(root/v/'native/endpoint.cpp'),'-o',str(out/(v+'.exe'))]
 with(out/(v+'-compile.log')).open('w')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:print((out/(v+'-compile.log')).read_text());raise SystemExit(r.returncode)
for i in range(5):
 for v in (('control','candidate')if i%2==0 else('candidate','control')):
  cmd=[str(out/(v+'.exe')),'C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107/handheld/src/cu66/fixtures/prepare12/prepare0.bin','1000'];t=time.perf_counter();r=subprocess.run(cmd,env=env,capture_output=True,text=True);elapsed=time.perf_counter()-t
  (out/f'{i}-{v}.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
  row={'round':i,'variant':v,'command':cmd,'host_process_seconds':elapsed,'stdout':r.stdout.strip()};rows.append(row);(out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(i,v,r.stdout.strip(),flush=True)
summary={v:{'median_internal_us':statistics.median(int(re.search('elapsed_us=(\\d+)',x['stdout'])[1])for x in rows if x['variant']==v),'host_process_seconds':[x['host_process_seconds']for x in rows if x['variant']==v]}for v in ('control','candidate')};(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
