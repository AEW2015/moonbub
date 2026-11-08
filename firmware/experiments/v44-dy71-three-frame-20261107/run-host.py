"""Compile and run actual V44 native/driver tests. No sockets or hardware."""
from pathlib import Path
import os, subprocess, json, hashlib, argparse, datetime
p=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(__doc__)
parser.add_argument('--output',type=Path,default=p/'evidence'/('host-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%fZ')))
out=parser.parse_args().output.resolve()
if not out.is_relative_to(Path('C:/moon').resolve()):raise ValueError('Output must stay under C:/moon')
out.mkdir(parents=True,exist_ok=False)
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+str(out)+';'+str(Path.home()/'.cargo/bin')+';'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp')
(out/'hud.def').write_text('LIBRARY hud\nEXPORTS\nv34_hud_create\nv34_hud_destroy\nv34_hud_transact\nv34_hud_stats\nv41_hud_set_reserve\n')
steps=[]
def run(label,command):
 with(out/(label+'.log')).open('w')as f:r=subprocess.run(command,env=env,stdout=f,stderr=subprocess.STDOUT)
 steps.append(dict(label=label,command=command,returncode=r.returncode));(out/'execution.json').write_text(json.dumps(steps,indent=2));print(label,r.returncode,flush=True)
 if r.returncode:print((out/(label+'.log')).read_text());raise SystemExit(r.returncode)
run('native',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',str(p/'native/endpoint.cpp'),'-o',str(out/'hud.dll')])
run('import',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(out/'hud.def'),'/OUT:'+str(out/'hud.lib'),'/MACHINE:X64'])
for name in ['network_driver','network_batch','network_wire']:
 run(name+'-compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(p/'tests'/f'{name}.rs'),'-L','native='+str(out),'-l','dylib=hud','-o',str(out/f'{name}.exe')])
 run(name+'-test',[str(out/f'{name}.exe'),'--test-threads=1'])
(out/'source-hashes.json').write_text(json.dumps({str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()for d in ('handheld/src/cu66','native','tests')for f in(p/d).rglob('*')if f.is_file()},indent=2))
print('V44_HOST_PASS')
