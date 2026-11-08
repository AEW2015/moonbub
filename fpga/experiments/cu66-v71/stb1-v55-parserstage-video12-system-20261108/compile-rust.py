from pathlib import Path
import json,hashlib,subprocess,os
p=Path(__file__).resolve().parent;b=json.loads((p/'bindings.json').read_text());sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
for f,h in b['executed_RTL_CPP_support_inputs'].items():assert sha(f)==h,f
for f,h in b['harness_source_files'].items():assert sha(p/f)==h,f
for f,h in b['copied_Rust_all_files_sha256'].items():assert sha(p/f)==h,f
for n in b['exact_firmware_source_match']:assert sha(p/'cu66'/n)==sha(Path(b['V55_origin'])/'handheld/src/cu66'/n),n
with(p/'rust-compile.log').open('x')as log:r=subprocess.run(b['rust_compile_command'],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TEMP='C:/moon/tmp',TMP='C:/moon/tmp'),timeout=180)
(p/'rust-compile-result.json').write_text(json.dumps({'returncode':r.returncode,'command':b['rust_compile_command'],'compiled_executable_sha256':sha(p/'actual-rust.exe')if r.returncode==0 else None},indent=2));raise SystemExit(r.returncode)
