"""Check newly encoded HUDs using exact V48 allocation-order endpoint at98,304."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,time
HERE=Path(__file__).resolve().parent
SOURCE=Path('C:/moon/publish/firmware/experiments/v48-dy71-selftest-control-20261107/native')
OUT=HERE/'endpoint04'
if OUT.exists():raise ValueError('fresh endpoint output required')
(OUT/'native').mkdir(parents=True)
pins={}
for p in sorted(SOURCE.iterdir()):
    if p.suffix not in ('.hpp','.h','.cpp'):continue
    shutil.copyfile(p,OUT/'native'/p.name);pins[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
shutil.copyfile(HERE/'endpoint_check.cpp',OUT/'endpoint_check.cpp')
env=os.environ.copy();env['TEMP']=env['TMP']='C:/moon/tmp';env['PATH']='C:/msys64/ucrt64/bin;'+env.get('PATH','')
commands=[]
def run(args,label):
    began=time.monotonic();r=subprocess.run(args,env=env,capture_output=True,text=True,timeout=180)
    (OUT/(label+'.stdout')).write_text(r.stdout);(OUT/(label+'.stderr')).write_text(r.stderr)
    commands.append(dict(args=list(map(str,args)),exit_code=r.returncode,wall_seconds=time.monotonic()-began))
    (OUT/'execution.json').write_text(json.dumps(dict(commands=commands,native_sources_sha256=pins,status='RUNNING' if not r.returncode else 'FAILED'),indent=2)+'\n')
    if r.returncode:raise RuntimeError(label+': '+r.stderr)
run(['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-I',str(OUT/'native'),str(OUT/'endpoint_check.cpp'),'-o',str(OUT/'endpoint_check.exe')],'build')
for sequence,count in (('synthetic03',3),('video02',3),('video12',12)):run([str(OUT/'endpoint_check.exe'),str(HERE/sequence),str(count)],sequence)
(OUT/'execution.json').write_text(json.dumps(dict(commands=commands,native_sources_sha256=pins,status='PASS'),indent=2)+'\n')
print(json.dumps(dict(status='PASS',sequences=3,frames=18,arena_cap=98304,identity='exact V48 native allocation-order endpoint,host64bit')))
