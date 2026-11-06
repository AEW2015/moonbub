"""Actual sealed v35 core/native HU against CU71 CSR+decoder+checked DRAM pins.
No hardware, SDK installation, physical SPI or PLL model. Native CPU outside HDL.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shlex,shutil,subprocess,time
root=Path(__file__).resolve().parents[3];platform=root/'fpga/experiments/cu66-v71/platform-sim'
v35=Path('C:/Users/lavat/codex/moonbub/firmware/experiments/v35-cu71-local-fixture-20261105')
a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--csr-cycles',type=int,default=8);a.add_argument('--build-only',action='store_true');args=a.parse_args()
o=Path(args.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();linux=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
manifest=json.loads((root/'fpga/experiments/cu66-v71/system/sources-burst.json').read_text());assert manifest['SIMULATION']is False
for n,h in manifest['sources_sha256'].items():assert sha(root/n)==h,n
sealed=json.loads((v35/'evidence/build-manifest.json').read_text())if(v35/'evidence/build-manifest.json').exists()else None
snapshot=json.loads((v35/'evidence/source-snapshot-v004.json').read_text())
for n,h in snapshot['files'].items():assert sha(v35/n)==h,n
if sealed:
 for n,item in sealed['artifacts'].items():assert sha(v35/n)==item['sha256'],n
sources=[root/n for n in manifest['sources']]
sources += [root/'fpga/experiments/cu66-v71/system'/n for n in ['cu71_local_control.sv','cu71_packet_staging.sv','cu71_packet_arbiter.sv']]
sources += [platform/'cu71_platform_sim.sv',platform/'model-verilator.sv',root/'fpga/experiments/cu66-v71/memory/evidence/lookahead-fast01/primitives.sv']
frozen=root/'fpga/experiments/cu66-v71/system/evidence/burst-oldmap-three01/model-verilator.sv';assert sha(platform/'model-verilator.sv')==sha(frozen)
origins={};compiled=[]
for f in sources:
 t=o/'inputs'/f.relative_to(root);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,t);compiled.append(t);origins[f.relative_to(root).as_posix()]=sha(f)
includes=[]
for d in manifest['include_dirs']:
 q=o/'inputs'/d;q.mkdir(parents=True,exist_ok=True);includes.append(q)
 for f in(root/d).glob('*.svh'):shutil.copyfile(f,q/f.name);origins[f.relative_to(root).as_posix()]=sha(f)
shutil.copyfile(platform/'server.cpp',o/'server.cpp');shutil.copyfile(v35/'rtl-cosim/harness.rs',o/'harness.rs');origins['platform/server.cpp']=sha(platform/'server.cpp');origins['sealed_v35/local.rs']=sha(v35/'handheld/src/cu66/local.rs');origins['sealed_v35/hud.rs']=sha(v35/'handheld/src/cu66/hud.rs');origins['sealed_v35/framing.rs']=sha(v35/'handheld/src/cu66/framing.rs');origins['sealed_v35/manifest']=sha(v35/'evidence/build-manifest.json')if sealed else'NOT_YET_SEALED';origins['harness.rs']=sha(o/'harness.rs')
(o/'source-freeze.json').write_text(json.dumps(origins,indent=2)+'\n')
(o/'scope.json').write_text(json.dumps({'actual':'Sealedv35Rustlocalcore+boundednativeHUendpoint; actualCU71CSR, receiver/decoder, stagedoriginalCU66bytes, actualSDRAMcommands/DQ checkedmodel','omitted':['PhysicalSPI/QSPIendpoint and CDC','VendorPLLs/jitter','FreeRTOSDeviceadapter/locks','NativeCPUtargettime advances no HDL clocks','2stateVerilator is not independentX proof'],'clock_period_ps':10000,'read_phase_degrees':274.5,'panel_half_ps':17029,'flight_access_hold':[0.757,2.223,2.223],'model':'Byteexactfrozenburst-oldmap-three01 model with disclosed1ps monitorcompatibility','hardware':False,'throughput_claim':False},indent=2)+'\n')
steps=[]
def run(label,cmd,env=None,timeout=3600):
 start=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:r=subprocess.run(list(map(str,cmd)),cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 steps.append({'label':label,'command':list(map(str,cmd)),'returncode':r.returncode,'seconds':time.monotonic()-start,'log_sha256':sha(o/(label+'.log'))});(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,r.returncode,flush=True);assert r.returncode==0,(label,str(o/(label+'.log')))
cmd=['verilator','--cc','--exe','--build','-j','2','--timing','--assert','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','cu71_platform_sim','--Mdir',linux(o/'build'),'-CFLAGS','-O1 -std=c++20',*['-I'+linux(d)for d in includes],*[linux(f)for f in compiled],linux(o/'server.cpp')]
run('rtl-build',['wsl','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(cmd)],timeout=2400)
env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+str(Path.home()/'.cargo/bin')+';'+env['PATH'];run('native-hud-build',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',v35/'native/endpoint.cpp','-o',o/'hud.dll'],env)
shutil.copyfile(v35/'evidence/hud.def',o/'hud.def');run('import-library',['C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe','/DEF:'+str(o/'hud.def'),'/OUT:'+str(o/'hud.lib'),'/MACHINE:X64'],env)
run('sdk-core-host-build',[Path.home()/'.cargo/bin/rustc.exe','+stable','--edition=2021',o/'harness.rs','-L','native='+str(o),'-l','dylib=hud','-o',o/'sdk-core.exe'],env)
if args.build_only:print('BUILD_ONLY_NO_FUNCTIONAL_PASS');raise SystemExit(0)
run('integration',[o/'sdk-core.exe',linux(o/'build/Vcu71_platform_sim'),o/'rtl-stderr.log',str(args.csr_cycles)],env,timeout=7200)
text=(o/'integration.log').read_text();assert 'SDK_RTL_COSIM_PASS'in text and'SDK_RTL_COSIM_FAIL'not in text
for n,h in snapshot['files'].items():assert sha(v35/n)==h,n
(o/'result.json').write_text(json.dumps({'status':'PASS_ACTUAL_V35_CORE_NATIVE_HU_CU71_RTL_SDRAM_PIN_MODEL','source_freeze_sha256':sha(o/'source-freeze.json'),'host_native_CPU_outside_HDltime':True,'physical_SPI':False,'hardware':False,'throughput_claim':False,'report':text},indent=2)+'\n');print('PLATFORM_INTEGRATION_PASS_NOT_PHYSICAL_SPI')
