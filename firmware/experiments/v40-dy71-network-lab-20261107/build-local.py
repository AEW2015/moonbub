"""Isolated V40 build/check only. Never flashes or connects to a device."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,time
p=Path(__file__).resolve().parent;u=Path(os.environ['USERPROFILE']);e=p/'evidence'
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def sources():return {f.relative_to(p).as_posix():h(f)for folder in ('handheld','handheld-dfu','native','tests','tools')for f in sorted((p/folder).rglob('*'))if f.is_file()and not any(n in f.parts for n in ('target','.embuild','__pycache__','.git'))}
before=sources();(e/'source-snapshot-v001.json').write_text(json.dumps(dict(variant='v40-dy71-network-lab-20261107',files=before,hardware=False),indent=2)+'\n')
env=dict(os.environ)
env['PATH']=';'.join(str(u/n)for n in ('.cargo/bin','.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin','.espressif/python_env/idf5.4_py3.11_env/Scripts','.espressif/tools/cmake/3.30.2/bin','.espressif/tools/ninja/1.12.1'))+';'+env['PATH']
env['LIBCLANG_PATH']=str(u/'.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin/libclang.dll');env['CARGO_TARGET_DIR']='C:/mv38a';env['IDF_PATH']=str(u/'.espressif/esp-idf/v5.4.3');env['GIT_CEILING_DIRECTORIES']=str(p);env.pop('NoDefaultCurrentDirectoryInExePath',None)
target=Path('C:/mv38a/xtensa-esp32s3-espidf/release/handheld')
if target.exists():
 q=e/'target-before-reuse.elf';assert not q.exists();shutil.copyfile(target,q)
 (e/'target-before-reuse.json').write_text(json.dumps(dict(path=str(target),sha256=h(q)),indent=2)+'\n')
for action in ('check','build'):
 assert sources()==before
 cmd=[str(u/'.cargo/bin/cargo.exe'),'+esp193',action,'--offline','--locked','--release','--features','rev4']
 start=time.monotonic()
 with(e/('target-'+action+'-v001.log')).open('x')as f:r=subprocess.run(cmd,cwd=p/'handheld',env=env,stdout=f,stderr=subprocess.STDOUT)
 result=dict(command=cmd,target='C:/mv38a',returncode=r.returncode,seconds=time.monotonic()-start,source_unchanged=sources()==before,hardware=False)
 (e/('target-'+action+'-v001.json')).write_text(json.dumps(result,indent=2)+'\n');print(action,json.dumps(result),flush=True)
 assert r.returncode==0 and result['source_unchanged']
release=p/'release-network-lab-v001';release.mkdir(exist_ok=False);shutil.copyfile(target,release/'moonshine-rev4.elf')
config=list(target.parent.glob('build/esp-idf-sys-*/out/build/config/sdkconfig.h'));assert len(config)==1;shutil.copyfile(config[0],e/'compiled-sdkconfig.h')
print('V40_ELF_BUILT_NOT_PACKAGED_OR_INSTALLED',h(release/'moonshine-rev4.elf'),flush=True)
