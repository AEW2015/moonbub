from pathlib import Path
import os,subprocess,json
p=Path('C:/mb70/firmware/experiments/v43-dy71-bulk-hud-20261107');e=p/'evidence'/('host-'+__import__('time').strftime('%Y%m%d-%H%M%S'));e.mkdir()
(e/'hud.def').write_text('LIBRARY hud\nEXPORTS\nv34_hud_create\nv34_hud_destroy\nv34_hud_transact\nv34_hud_stats\nv41_hud_set_reserve\n')
env=dict(os.environ,V43_ROOT=str(p),PATH='C:/msys64/ucrt64/bin;'+str(Path.home()/'.cargo/bin')+';'+os.environ['PATH'])
commands=[('native',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',str(p/'native/endpoint.cpp'),'-o',str(e/'hud.dll')]),('import',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(e/'hud.def'),'/OUT:'+str(e/'hud.lib'),'/MACHINE:X64'])]
for label in ['local','network_driver','network_loopback','network_batch']:
 commands.extend([(label+'-compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(p/'tests'/f'{label}.rs'),'-L','native='+str(e),'-l','dylib=hud','-o',str(e/f'{label}.exe')]),(label+'-test',[str(e/f'{label}.exe'),'--test-threads=1','--nocapture'])])
(p/'tests/network_wire.rs').write_text('#![allow(dead_code)]\n#[path="../handheld/src/cu66/framing.rs"]mod framing;\n#[path="../handheld/src/cu66/network_wire.rs"]mod network_wire;\n')
commands.extend([('wire-compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(p/'tests/network_wire.rs'),'-o',str(e/'wire.exe')]),('wire-test',[str(e/'wire.exe')])])
steps=[]
for label,cmd in commands:
 with(e/f'{label}.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 steps.append(dict(label=label,cmd=cmd,returncode=r.returncode));(e/'execution.json').write_text(json.dumps(steps,indent=2));print(label,r.returncode,flush=True)
 if r.returncode:print((e/f'{label}.log').read_text());raise SystemExit(1)

