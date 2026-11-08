"""Compile and run actual V48 native/driver tests. No sockets or hardware."""
from pathlib import Path
import os, subprocess, json, hashlib, argparse, datetime
p=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(__doc__)
parser.add_argument('--output',type=Path,default=p/'evidence'/('host-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%fZ')))
out=parser.parse_args().output.resolve()
if not out.is_relative_to(Path('C:/moon').resolve()):raise ValueError('Output must stay under C:/moon')
out.mkdir(parents=True,exist_ok=False)
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+str(out)+';'+str(Path.home()/'.cargo/bin')+';'+os.environ['PATH'],TEMP='C:/moon/tmp',TMP='C:/moon/tmp')
(out/'hud.def').write_text('LIBRARY hud\nEXPORTS\nv34_hud_create\nv34_hud_destroy\nv34_hud_transact\nv34_hud_stats\nv41_hud_set_reserve\nv46_hud_set_largest_probe\nv46_hud_diagnostics\n')
steps=[]
def sources():
 result={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()for d in ('handheld/src','native','tests')for f in(p/d).rglob('*')if f.is_file()}
 fixtures=Path('C:/moon/publish/host/dy71-sequence-v3')
 for f in sorted(fixtures.glob('*.cu66')):result['host-fixture/'+f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
 if(fixtures/'manifest.json').exists():result['host-fixture/manifest.json']=hashlib.sha256((fixtures/'manifest.json').read_bytes()).hexdigest()
 return result
before=sources();(out/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
def run(label,command):
 with(out/(label+'.log')).open('w')as f:r=subprocess.run(command,env=env,cwd=p,stdout=f,stderr=subprocess.STDOUT)
 steps.append(dict(label=label,command=command,returncode=r.returncode));(out/'execution.json').write_text(json.dumps(steps,indent=2));print(label,r.returncode,flush=True)
 if r.returncode:print((out/(label+'.log')).read_text());raise SystemExit(r.returncode)
run('native',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',str(p/'native/endpoint.cpp'),'-o',str(out/'hud.dll')])
run('allocator-compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror',str(p/'tests/native_diagnostics.cpp'),str(p/'native/endpoint.cpp'),'-o',str(out/'allocator.exe')])
run('allocator-test',[str(out/'allocator.exe')])
run('hud-order-compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror',str(p/'tests/hud_order.cpp'),'-o',str(out/'hud-order.exe')])
run('hud-order-test',[str(out/'hud-order.exe'),str(p/'handheld/src/cu66/fixtures/prepare12')])
run('prepare12-compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-O2',str(p/'tests/prepare12_native.cpp'),'-o',str(out/'prepare12.exe')])
run('prepare12-test',[str(out/'prepare12.exe'),'150000','C:/moon/maintenance/v45-sequence/qualification'])
run('import',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(out/'hud.def'),'/OUT:'+str(out/'hud.lib'),'/MACHINE:X64'])
for name in ['stb_failure','stb1_driver','network_driver','network_batch','network_wire','telemetry','native_diagnostics','lab_control_line','usb_msos','lab_recovery_gate']:
 run(name+'-compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(p/'tests'/f'{name}.rs'),'-L','native='+str(out),'-l','dylib=hud','-o',str(out/f'{name}.exe')])
 run(name+'-test',[str(out/f'{name}.exe'),'--test-threads=1'])
after=sources();(out/'source-hashes.json').write_text(json.dumps(after,indent=2)+'\n');(out/'source-check.json').write_text(json.dumps({'unchanged':before==after,'files':len(before)},indent=2)+'\n');assert before==after,'Candidate sources changed during host execution'
print('V48_HOST_PASS')

