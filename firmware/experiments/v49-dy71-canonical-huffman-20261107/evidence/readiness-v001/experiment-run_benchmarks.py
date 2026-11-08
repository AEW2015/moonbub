from pathlib import Path
import subprocess,os,time,json,statistics,re
root=Path(__file__).resolve().parent
out=root/'benchmark02';out.mkdir(exist_ok=False)
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp')
rows=[]
for variant in ('control','candidate'):
 for name in ('corpus','microbench'):
  cmd=['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-fstack-usage','-I',str(root/variant),str(root/'harness'/f'{name}.cpp'),'-o',str(out/(variant+'-'+name+'.exe'))]
  r=subprocess.run(cmd,env=env,capture_output=True,text=True);(out/(variant+'-'+name+'-compile.log')).write_text(r.stdout+r.stderr);assert r.returncode==0,(r.stdout,r.stderr)
for i in range(5):
 for variant in (('control','candidate')if i%2==0 else('candidate','control')):
  for name,args in [('corpus',['C:/moon/maintenance/v44-localhost/native-corpus.tsv']),('microbench',['100'])]:
   start=time.perf_counter();r=subprocess.run([str(out/(variant+'-'+name+'.exe')),*args],env=env,capture_output=True,text=True);elapsed=time.perf_counter()-start
   (out/f'{i}-{variant}-{name}.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
   rows.append({'round':i,'variant':variant,'benchmark':name,'seconds':elapsed,'stdout':r.stdout.strip()});(out/'runs.json').write_text(json.dumps(rows,indent=2)+'\n');print(i,variant,name,elapsed,flush=True)
result={f'{v}-{n}':{'median_process_seconds':statistics.median(x['seconds']for x in rows if x['variant']==v and x['benchmark']==n)}for v in ('control','candidate')for n in ('corpus','microbench')}
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
