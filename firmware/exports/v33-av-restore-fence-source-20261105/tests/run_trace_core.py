"""Standalone core checks. Never builds ESP firmware or accesses hardware."""
from pathlib import Path
import argparse,hashlib,json,subprocess,re
p=Path(__file__).resolve().parent
a=argparse.ArgumentParser();a.add_argument('--out',required=True);x=a.parse_args();out=Path(x.out).resolve();assert not out.exists();out.mkdir(parents=True)
rustc=Path.home()/'.cargo/bin/rustc.exe';exe=out/'trace-core-tests.exe';cmd=[str(rustc),'+stable','--edition=2021','--test',str(p/'trace_core.rs'),'-o',str(exe)]
for name,command in [('compile',cmd),('run',[str(exe),'--nocapture','--test-threads=1'])]:
 r=subprocess.run(command,capture_output=True,text=True);(out/(name+'.log')).write_text(r.stdout+r.stderr);r.check_returncode()
log=(out/'run.log').read_text();n=int(re.search(r'test result: ok\. (\d+) passed; 0 failed',log)[1]);size=int(re.search(r'TRACE_STORAGE_BYTES=(\d+)',log)[1]);assert size<=9*1024
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
(out/'result.json').write_text(json.dumps({'status':'PASS','tests':n,'host_static_storage_bytes':size,'source_sha256':sha(p.parent/'handheld/src/streaming/diagnostic_trace.rs'),'test_sha256':sha(p/'trace_core.rs'),'compile_command':cmd,'hardware':'NONE','scope':'Pure core only; target ABI/static storage and integration remain separate gates'},indent=2)+'\n');print('TRACE_CORE_PASS',n,'tests;',size,'bytes')
