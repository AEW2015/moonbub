"""Cross-check real Rust-emitted records against independent Python parsing/CRC."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
import decode_stb_failure as decoder
ROOT=Path(__file__).resolve().parents[1]
HOST=Path(sys.argv[1]);OUT=ROOT/'evidence/host-decoder-v001';OUT.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env['PATH']=str(HOST)+';C:/msys64/ucrt64/bin;'+env.get('PATH','');env['TEMP']=env['TMP']='C:/moon/tmp'
cmd=[str(HOST/'stb_failure.exe'),'--exact','emit_fixture_for_host_decoder','--nocapture','--test-threads=1']
r=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=60);(OUT/'rust-vectors.log').write_text(r.stdout+r.stderr);assert r.returncode==0
lines=[]
for line in r.stdout.splitlines():
 if 'STBF1 'in line:lines.append(line[line.index('STBF1 '):])
assert len(lines)==8
decoded=[]
for i in(0,4):
 records=lines[i:i+4];decoded.append(decoder.decode(records));(OUT/f'vector{i//4}.txt').write_text('\n'.join(records)+'\n')
assert decoded[0]['context']['session']==2**64-1 and decoded[0]['valid_mask']==8191
assert decoded[1]['first_error_code']==1 and decoded[1]['result_flags']&8 and decoded[1]['context']['frame']!=decoded[1]['context']['identity_frame']
(OUT/'decoded-vectors.json').write_text(json.dumps(decoded,indent=2)+'\n')
cmd2=[sys.executable,str(ROOT/'tools/test_decode_stb_failure.py')];t=subprocess.run(cmd2,env=env,capture_output=True,text=True,timeout=60);(OUT/'python-tests.log').write_text(t.stdout+t.stderr);assert t.returncode==0
result=dict(status='PASS',actual_Rust_vectors=2,Python_tests=6,max_record_payload_bytes=max(map(len,lines)),commands=[dict(argv=cmd,exit_code=r.returncode),dict(argv=cmd2,exit_code=t.returncode)],source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in(ROOT/'handheld/src/cu66/stb_failure.rs',ROOT/'tests/stb_failure.rs',ROOT/'tools/decode_stb_failure.py',ROOT/'tools/test_decode_stb_failure.py',ROOT/'tools/qualify_host_decoder.py')},physical_status='NO_HARDWARE_OR_NETWORK')
(OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
