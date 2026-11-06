"""Actual frozen v36 native HU -> safe DY71 CSR/stager/finalv008/group/SDRAM.

Reuses only a hash-bound completed actual-RTL control build. No physical SPI,
PLL, FreeRTOS device/lock or target CPU execution/timing is modeled.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/final-local-v008';v36=Path('C:/Users/lavat/codex/moonbub/firmware/experiments/v36-dual-local-fixture-20261106');v35=Path('C:/Users/lavat/codex/moonbub/firmware/experiments/v35-cu71-local-fixture-20261105')
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--server-evidence',default=str(d/'evidence/control01'));p.add_argument('--csr-cycles',type=int,default=8);p.add_argument('--build-only',action='store_true');a=p.parse_args()
o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);server=Path(a.server_evidence).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:]
snapshot=v36/'evidence/source-snapshot-v001.json';snap=json.loads(snapshot.read_text())
for name,h in snap['files'].items():assert sha(v36/name)==h,('V36source changed',name)
qualified=json.loads((server/'result.json').read_text());assert qualified['status']=='PASS_ACTUAL_DY71_LOCAL_CSR_STAGING_ABORT_AND_SDRAM_HUD_READBACK'
freeze=json.loads((server/'source-freeze.json').read_text())
for name,h in freeze['originals'].items():assert sha(Path(name))==h
for name,h in freeze['compiled'].items():assert sha(server/name)==h
for name,h in freeze['headers'].items():assert sha(server/name)==h
assert all(step['returncode']==0 for step in json.loads((server/'execution.json').read_text()))
exe=server/'build/Vdy71_platform_sim';exe_hash=sha(exe)
original=v35/'rtl-cosim/harness.rs';text=original.read_text();assert text.count(str(v35).replace('\\','/'))==3
text=text.replace(str(v35).replace('\\','/'),str(v36).replace('\\','/'))
assert text.count('local::run(&mut link,&mut endpoint)')==1
text=text.replace('local::run(&mut link,&mut endpoint)','local::run_with_profile(&mut link,&mut endpoint,local::Profile::Dy71)')
text=text.replace('actual_v35_core=1','actual_v36_core=1').replace('actual_CU71_CSR=1','actual_DY71_CSR=1')
(o/'harness.rs').write_text(text,newline='\n');shutil.copy2(v36/'evidence/hud.def',o/'hud.def')
pins={str(snapshot):sha(snapshot),str(original):sha(original),str(exe):exe_hash,str(server/'source-freeze.json'):sha(server/'source-freeze.json'),str(server/'result.json'):sha(server/'result.json'),str(v36/'native/endpoint.cpp'):sha(v36/'native/endpoint.cpp'),str(o/'harness.rs'):sha(o/'harness.rs'),str(o/'hud.def'):sha(o/'hud.def'),str(Path(__file__)):sha(Path(__file__))}
for f in(v36/'native').rglob('*'):
    if f.is_file():pins[str(f)]=sha(f)
(o/'source-freeze.json').write_text(json.dumps(dict(bindings=pins,v36_snapshot_sha256=sha(snapshot),actual_rtl_source_freeze_sha256=sha(server/'source-freeze.json'),server_executable_sha256=exe_hash,profile='EXPLICIT_DY71_ONLY',CSR_cycles_per_call=a.csr_cycles,scope='Actualv36core/nativeendpoint+actualDYtypedCSR/FinalV008Safe/group/SDRAMmodel, nativeCPUoutsideHDLclock; nohardware'),indent=2)+'\n')
env=dict(os.environ,PATH='C:/msys64/ucrt64/bin;'+str(Path.home()/'.cargo/bin')+';'+os.environ['PATH']);steps=[]
def run(label,command,timeout=1800):
    start=time.monotonic()
    with(o/(label+'.log')).open('wb')as f:q=subprocess.run(list(map(str,command)),cwd=o,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    steps.append(dict(label=label,command=list(map(str,command)),returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
run('native-HU-build',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',v36/'native/endpoint.cpp','-o',o/'hud.dll'])
run('native-import-library',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(o/'hud.def'),'/OUT:'+str(o/'hud.lib'),'/MACHINE:X64'])
run('v36-core-host-build',[Path.home()/'.cargo/bin/rustc.exe','+stable','--edition=2021',o/'harness.rs','-L','native='+str(o),'-l','dylib=hud','-o',o/'sdk-core.exe'])
if a.build_only:print('BUILD_ONLY_NO_FUNCTIONAL_PASS');raise SystemExit(0)
run('native-RTL-integration',[o/'sdk-core.exe',lin(exe),o/'rtl-stderr.log',str(a.csr_cycles)],7200)
log=(o/'native-RTL-integration.log').read_text();assert 'SDK_RTL_COSIM_PASS actual_v36_core=1 actual_native_HU_endpoint=1 actual_DY71_CSR=1'in log and 'SDK_RTL_COSIM_FAIL'not in log
assert 'HUD_words_written=42240 HUD_words_verified=42240'in log
for name,h in snap['files'].items():assert sha(v36/name)==h,name
assert all(sha(Path(name))==h for name,h in pins.items())
(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_V36_DY71_LOCAL_CORE_NATIVE_HU_REAL_CSR_SDRAM_KEY_P',profile='DY71magic44593731_ABI10000_cap0f',frames=2,accepted=2,presented=2,rejected=0,HUD_words_written=42240,HUD_words_verified=42240,source_freeze_sha256=sha(o/'source-freeze.json'),server_executable_sha256=exe_hash,hardware=False,BIT=False,physical_SPI=False,CPU_target_timing=False,scope='Actualnative semanticresults/ACKandallHUDwrites/readbacks throughrealCSR+FinalV008SafeOwner+groupedbackend+checkedSDRAMmodel. NativeCPUtime doesnotadvanceHDLclocks; noFreeRTOS/PLL/QSPIwire timing orhardwareproof.',report=log),indent=2)+'\n');print('DY71_ACTUAL_V36_NATIVE_RTL_KEY_P_PASS_NO_HARDWARE')
