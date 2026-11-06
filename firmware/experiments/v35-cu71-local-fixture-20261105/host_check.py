from pathlib import Path
import subprocess,hashlib,json,os
p=Path(__file__).resolve().parent;e=p/'evidence';env=dict(os.environ);env['PATH']='C:/msys64/ucrt64/bin;'+str(Path.home()/'.cargo/bin')+';'+env['PATH'];steps=[]
def run(n,c):
 q=subprocess.run(c,capture_output=True,text=True,env=env);(e/(n+'-v007.log')).write_text(q.stdout+q.stderr);steps.append({'label':n,'command':c,'returncode':q.returncode});assert q.returncode==0,(n,q.stdout,q.stderr)
run('native-compile',['C:/msys64/ucrt64/bin/g++.exe','-std=c++17','-Os','-Wall','-Wextra','-Werror','-shared',str(p/'native/endpoint.cpp'),'-o',str(e/'hud.dll')])
lib='C:/Program Files (x86)/Microsoft Visual Studio/2019/Community/VC/Tools/MSVC/14.29.30133/bin/Hostx64/x64/lib.exe'
run('import-library',[lib,'/DEF:'+str(e/'hud.def'),'/OUT:'+str(e/'hud.lib'),'/MACHINE:X64'])
run('control-host-compile',[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(p/'tests/local.rs'),'-L','native='+str(e),'-l','dylib=hud','-o',str(e/'local-tests.exe')])
run('control-host-tests',[str(e/'local-tests.exe'),'--test-threads=1','--nocapture']);assert 'test result: ok. 12 passed; 0 failed'in(e/'control-host-tests-v007.log').read_text()
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();result={'status':'PASS_ACTUAL_NATIVE_ENDPOINT_LOCAL_CSR_MODEL','tests':12,'steps':steps,'source_hashes':{f.relative_to(p).as_posix():h(f)for folder in ['native','handheld/src/cu66','tests']for f in(p/folder).rglob('*')if f.is_file()},'scope':'Actual Rustlocaldriver+actualboundednativeHUendpoint linkedthroughCABI; explicit mailbox/SDRAMcontrolmodel. Not RTLcosimulation orphysicalSPI.','hardware':False};(e/'host-control-result-v007.json').write_text(json.dumps(result,indent=2)+'\n');print('HOST_CONTROL_PASS12_actual_nativeFFI_model_notRTL')
