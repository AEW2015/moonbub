from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];BASE=Path('C:/moon/dev/experiments/v52-stb1-candidate-20261108');HOST=Path('C:/moon/builds/v54-host01')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(root,dirs):return{str(p.relative_to(root)).replace('\\','/'):sha(p)for d in dirs for p in(root/d).rglob('*')if p.is_file()and '__pycache__'not in p.parts}
assert json.loads((HOST/'source-check.json').read_text())==dict(unchanged=True,files=194)
assert all(x['returncode']==0 for x in json.loads((HOST/'execution.json').read_text()))
decoder=json.loads((ROOT/'evidence/host-decoder-v001/result.json').read_text());assert decoder['status']=='PASS' and decoder['actual_Rust_vectors']==2
before=manifest(BASE,('handheld','handheld-dfu','native'));after=manifest(ROOT,('handheld','handheld-dfu','native'))
delta=[key for key,value in after.items()if before.get(key)!=value]
expected=['handheld/src/cu66/mod.rs','handheld/src/cu66/network_io.rs','handheld/src/cu66/network_usb.rs','handheld/src/cu66/stb_failure.rs','handheld/src/diag_pages.rs']
assert sorted(delta)==sorted(expected)
for key in('handheld/src/cu66/network_driver.rs','handheld/src/cu66/stb1.rs','handheld/src/cu66/local.rs','handheld/src/cu66/local_usb.rs','handheld/src/cu66/report_snapshot.rs','handheld/src/cu66/report_export.rs','handheld/src/cu66/network_wire.rs','handheld/src/cu66/framing.rs','handheld/sdkconfig.defaults'):
 assert after[key]==before[key]
assert manifest(ROOT,('native',))==manifest(BASE,('native',))
counts={}
for p in HOST.glob('*-test.log'):
 m=re.search(r'test result: ok\. (\d+) passed',p.read_text())
 if m:counts[p.name]=int(m[1])
assert sum(counts.values())==213
result=dict(status='SOURCE_CANDIDATE_HOST_GATES_PASS_PENDING_REVIEW_AND_TARGET',variant='v54-dy71-stb1-failure-diag-20261108',base=str(BASE),changed_application_files=sorted(delta),native_STB1_Adapter_SDK_and_guards_unchanged=True,normal_path_added_SPI_or_logs=False,max_CSR_reads=13,attempts_per_CSR=1,sampling_budget='20,000us PRE-CALL only, not hard deadline',context=['Progress active/ordinal/frame/generation/phase/localtimestamp/storedprefix','cached current DYN1 session/capture_us/frame/reference; validity explicit'],records=4,max_payload_bytes=186,delivery='BEST_EFFORT_NONATOMIC_POST_FAILURE; not paced reexport',checksum='IEEECRC32 over fixed LE metadata/context/13 values',Rust_test_executions=213,new_diagnostic_cases=10,new_diagnostic_executions_including_framing=12,Python_decoder_tests=6,actual_Rust_to_Python_vectors=2,host_snapshot_bytes=136,target_build='NOT_RUN; awaiting root review',physical='NO_HARDWARE_OR_NETWORK',evidence=dict(host_execution=str(HOST/'execution.json'),host_source_check=str(HOST/'source-check.json'),decoder=str(ROOT/'evidence/host-decoder-v001/result.json')))
(ROOT/'V54-READINESS.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'final-source-bindings.json').write_text(json.dumps(manifest(ROOT,('handheld','handheld-dfu','native','tests','tools')),indent=2)+'\n')
print(json.dumps(result))
