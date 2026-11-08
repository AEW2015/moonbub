"""Selected combined native endpoint: old3 and NEW12 source goldens, actual98304cap."""
from pathlib import Path
import hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence/native-oracles';NATIVE=ROOT/'native'
env=os.environ.copy();env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','');env['TEMP']=env['TMP']='C:/moon/tmp'
steps=[]
def run(label,cmd):
 began=time.monotonic();r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);(OUT/(label+'.stdout')).write_text(r.stdout);(OUT/(label+'.stderr')).write_text(r.stderr);steps.append(dict(label=label,command=cmd,exit_code=r.returncode,host_process_seconds=time.monotonic()-began));(OUT/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert r.returncode==0,r.stderr
run('compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-I',str(NATIVE),str(ROOT/'tools/endpoint_check.cpp'),'-o',str(OUT/'endpoint-check.exe')])
run('old3',[str(OUT/'endpoint-check.exe'),str(OUT/'old3'),'3'])
run('new12',[str(OUT/'endpoint-check.exe'),'C:/moon/dev/experiments/cu66-source-bridge-20261108/video12','12'])
results={name:json.loads((OUT/(name+'.stdout')).read_text()) for name in('old3','new12')}
assert all(r['arena_cap']==98304 and r['arena_peak']<=98304 and r['allocation_failures']==0 for r in results.values())
sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in list(NATIVE.glob('*'))+[ROOT/'tools/endpoint_check.cpp',ROOT/'tools/check_native_oracles.py']if p.is_file()}
inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for folder in(OUT/'old3',Path('C:/moon/dev/experiments/cu66-source-bridge-20261108/video12'))for p in folder.iterdir()if p.suffix in('.prepare','.hud')}
result=dict(status='PASS',results=results,unique_HUD_words=15*21120,full_and_256word_read_comparisons=15*21120*2,source_sha256=sources,input_sha256=inputs,scope='Exact combined nativeendpoint and realsourceHUDgoldens; host64bit98304arena; noSDKfragmentation,targetstack,FPGA,network orFPSclaim')
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
