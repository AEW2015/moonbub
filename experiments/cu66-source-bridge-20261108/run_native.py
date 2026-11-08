"""Snapshot exact native-v69 sources and run the new packet/golden oracle checks."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'cu66-native-v69'
OUT=HERE/'native04'
if OUT.exists(): raise ValueError('fresh native output required')
OUT.mkdir()
pins={}
for p in sorted(SOURCE.glob('*.hpp')):
    shutil.copyfile(p,OUT/p.name);pins[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copyfile(SOURCE/'main.cpp',OUT/'main.cpp');pins['main.cpp']=hashlib.sha256((SOURCE/'main.cpp').read_bytes()).hexdigest()
shutil.copyfile(HERE/'negative.cpp',OUT/'negative.cpp')
commands=[]
env=os.environ.copy();env['TEMP']=env['TMP']='C:/moon/tmp';env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','')
def run(args,label):
    began=time.monotonic();r=subprocess.run(args,env=env,capture_output=True,text=True,timeout=180)
    (OUT/(label+'.stdout')).write_text(r.stdout);(OUT/(label+'.stderr')).write_text(r.stderr)
    commands.append(dict(args=list(map(str,args)),exit_code=r.returncode,wall_seconds=time.monotonic()-began))
    (OUT/'execution.json').write_text(json.dumps(dict(commands=commands,native_sources_sha256=pins,status='RUNNING' if not r.returncode else 'FAILED'),indent=2)+'\n')
    if r.returncode: raise RuntimeError(label+': '+r.stderr)
compiler='C:/msys64/ucrt64/bin/g++.exe'
run([compiler,'-std=c++17','-O2','-Wall','-Wextra','-Werror',str(OUT/'main.cpp'),'-o',str(OUT/'native_decoder.exe')],'build-oracle')
run([compiler,'-std=c++17','-O2','-Wall','-Wextra','-Werror',str(OUT/'negative.cpp'),'-o',str(OUT/'negative.exe')],'build-negative')
for sequence,count in (('synthetic03',3),('video02',3),('video12',12)):
    run([str(OUT/'native_decoder.exe'),(HERE/sequence/'index.tsv').as_posix(), '1'],sequence+'-oracle')
    run([str(OUT/'negative.exe'),str(HERE/sequence),str(count)],sequence+'-negative')
(OUT/'execution.json').write_text(json.dumps(dict(commands=commands,native_sources_sha256=pins,status='PASS'),indent=2)+'\n')
print(json.dumps(dict(status='PASS',sequences=3,frames=18,native_sources_sha256=pins)))
