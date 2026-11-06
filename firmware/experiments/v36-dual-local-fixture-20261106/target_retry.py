from pathlib import Path
import subprocess,os,json,time,sys
p=Path(__file__).resolve().parent;u=Path(os.environ['USERPROFILE']);e=dict(os.environ)
e['PATH']=';'.join(str(u/n)for n in ['.cargo/bin','.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin','.espressif/python_env/idf5.4_py3.11_env/Scripts','.espressif/tools/cmake/3.30.2/bin','.espressif/tools/ninja/1.12.1'])+';'+e['PATH']
e['LIBCLANG_PATH']=str(u/'.rustup/toolchains/esp193/xtensa-esp32-elf-clang/esp-clang/bin/libclang.dll');e['CARGO_TARGET_DIR']='C:/mv36a';e['IDF_PATH']=str(u/'.espressif/esp-idf/v5.4.3');e['GIT_CEILING_DIRECTORIES']=str(p);e.pop('NoDefaultCurrentDirectoryInExePath',None)
subprocess.run([sys.executable,str(p/'review_source.py')],check=True)
probe=subprocess.run(['python','--version'],env=e,capture_output=True);assert probe.stdout.startswith(b'Python '),(probe.stdout,probe.stderr)
action=sys.argv[1]if len(sys.argv)>1 else 'check';cmd=[str(u/'.cargo/bin/cargo.exe'),'+esp193',action,'--offline','--locked','--release','--features','rev4'];log=p/f'evidence/target-{action}-v001.log';assert not log.exists();record={'command':cmd,'target':'C:/mv36a','python_stdout':probe.stdout.decode(),'NoDefaultCurrentDirectoryInExePath':'removed in owned child only','hardware':False};start=time.monotonic()
with log.open('wb')as f:r=subprocess.run(cmd,cwd=p/'handheld',env=e,stdout=f,stderr=subprocess.STDOUT)
record.update(returncode=r.returncode,seconds=time.monotonic()-start);subprocess.run([sys.executable,str(p/'review_source.py')],check=True);(p/f'evidence/target-{action}-v001.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));raise SystemExit(r.returncode)
