from pathlib import Path
import hashlib,json,os,shutil,subprocess
HERE=Path(__file__).resolve().parent;CANDIDATE=HERE.parent;OUT=CANDIDATE/'evidence/stb-adapter-v001'
OUT.mkdir(parents=True,exist_ok=False)
adapter=CANDIDATE/'handheld/src/cu66/local_usb.rs';local=CANDIDATE/'handheld/src/cu66/local.rs';stb=CANDIDATE/'handheld/src/cu66/stb1.rs'
text=adapter.read_text();begin=text.index("impl Bus for Adapter<'_>{");end=text.index('#[inline(never)]fn worker',begin)
(OUT/'actual-adapter-sdk-include.rs').write_text(text[begin:end])
text=local.read_text();begin=text.index('#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Error');end=text.index('#[derive(Debug,Clone,Copy)]pub struct Report',begin)
(OUT/'local-trait-sdk-include.rs').write_text(text[begin:end])
# Strip only module documentation and disable its separate test module; the complete production driver code is retained.
text='\n'.join(x for x in stb.read_text().splitlines() if not x.startswith('//!') and x!='#[cfg(test)] mod tests;')+'\n'
(OUT/'stb1-sdk-include.rs').write_text(text)
shutil.copyfile(HERE/'sdk_adapter_shim.rs',OUT/'sdk_adapter_shim.rs')
env=os.environ.copy();env['TEMP']=env['TMP']='C:/moon/tmp'
commands=[]
for label,cmd in [('compile',['C:/Users/lavat/.cargo/bin/rustc.exe','+stable','--edition=2021','--test',str(OUT/'sdk_adapter_shim.rs'),'-D','warnings','-o',str(OUT/'adapter-shim.exe')]),('test',[str(OUT/'adapter-shim.exe'),'--test-threads=1'])]:
 r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=120);(OUT/(label+'.log')).write_text(r.stdout+r.stderr);commands.append(dict(command=cmd,exit_code=r.returncode));
 if r.returncode:print(r.stdout+r.stderr);break
result=dict(commands=commands,status='PASS' if len(commands)==2 and commands[-1]['exit_code']==0 else 'FAIL',scope='Actual Adapter impl, host SDK mocks; not actual ESP-IDF build or physical SPI',source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in(adapter,local,stb,HERE/'sdk_adapter_shim.rs')})
(OUT/'execution.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['status']=='PASS'
