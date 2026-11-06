"""Retain a fully instrumented model; rebuild only the corrected C++ driver."""
from pathlib import Path
import argparse,hashlib,json,shlex,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--bench',required=True);p.add_argument('--output',required=True);a=p.parse_args()
r=Path(__file__).resolve().parents[3];old=Path(a.model).resolve();bench=Path(a.bench).resolve();out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
linux=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
oldpins=json.loads((old/'source-freeze.json').read_text());newpins=json.loads((bench/'source-freeze.json').read_text())
for n,h in oldpins.items():
 if n.startswith('scripts/'):continue
 if '/system/evidence/' in n:continue
 assert newpins[n]==h,n
assert sha(old/'model-verilator.sv')==sha(bench/'model-verilator.sv')
assert sha(old/'cu71_system_sim.sv')==sha(bench/'cu71_system_sim.sv')
build=old/'build';objects=[build/n for n in ['Vcu71_system_sim__ALL.a','verilated.o','verilated_timing.o','verilated_threads.o']]
assert all(x.is_file()for x in objects)
assert 'return 0;}catch' in (bench/'tb.cpp').read_text()
(out/'tb.cpp').write_bytes((bench/'tb.cpp').read_bytes())
bindings={str(f):sha(f)for f in [old/'source-freeze.json',old/'execution.json',bench/'source-freeze.json',bench/'tb.cpp',*objects,build/'Vcu71_system_sim.h']}
(out/'reuse-binding.json').write_text(json.dumps({'scope':'Sameexactgenerated/instrumentedmodelobjects; onlycorrectedC++driverrecompiled','bindings':bindings,'old_model_source':str(old),'new_driver_source':str(bench),'hardware':False},indent=2)+'\n')
env='/opt/gamebub-openxc7-20261021/oss-cad-suite'
cmd=['g++','-std=c++20','-O1','-fsanitize=address,undefined','-fno-omit-frame-pointer','-g','-fcoroutines','-DVM_TIMING=1','-DVM_TRACE=0','-I'+linux(build),'-I'+env+'/share/verilator/include','-I'+env+'/share/verilator/include/vltstd',linux(out/'tb.cpp'),*[linux(f)for f in objects],'-pthread','-latomic','-o',linux(out/'test')]
steps=[]
def run(label,cmd,timeout):
 argv=['wsl','-d','MRS-HDL-Research','--','bash','-lc','source '+env+'/environment; '+shlex.join(cmd)]
 t=time.monotonic()
 with(out/(label+'.log')).open('wb')as f:q=subprocess.run(argv,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append({'label':label,'command':argv,'returncode':q.returncode,'seconds':time.monotonic()-t,'log_sha256':sha(out/(label+'.log'))})
 (out/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True)
 assert q.returncode==0,(label,out)
run('relink',cmd,300)
index=r/'experiments/cu66-native-v69/index.tsv';fixture=index.parent/index.read_text().splitlines()[0].split('\t')[2]
run('control',[linux(out/'test'),'--control',linux(fixture)],600)
assert 'SYSTEM_CONTROL_PASS' in(out/'control.log').read_text()
assert not any(x in(out/'control.log').read_text()for x in ['runtime error:','AddressSanitizer','LeakSanitizer'])
for n,h in bindings.items():assert sha(Path(n))==h,n
(out/'result.json').write_text(json.dumps({'status':'PASS_SANITIZED_CONTROL_WITH_CORRECTED_DRIVER','hardware':False,'scope':'Controlonly; exactASANmodelobjectreusebindingsretained; doesnotqualifycompleteframeorcadence'},indent=2)+'\n')
