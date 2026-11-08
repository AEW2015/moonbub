from pathlib import Path
import subprocess,os,json,collections
p=Path('C:/moon/maintenance/v47-fragmentation');os.environ['PATH']='C:/msys64/ucrt64/bin;'+os.environ['PATH'];fixtures='C:/moon/publish/firmware/experiments/v46-dy71-native-failure-20261107/handheld/src/cu66/fixtures/prepare12';rows=[];counts=collections.Counter()
for seed in range(1,61):
 row={'size':128000,'seed':seed}
 for v in ['v46','v47']:
  r=subprocess.run([str(p/(v+'.exe')),str(seed),'128000',fixtures],capture_output=True,text=True);row[v]={'exit':r.returncode,'result':r.stdout.strip(),'stderr':r.stderr}
 def kind(v):
  r=row[v];return 'invalid' if r['exit'] else 'pass' if 'stage=pass' in r['result'] else 'fail'
 counts[(kind('v46'),kind('v47'))]+=1;rows.append(row)
(p/'qualified-matrix.json').write_text(json.dumps({'pool_bytes':128000,'counts':{str(k):v for k,v in counts.items()},'rows':rows},indent=2));print(dict(counts))
