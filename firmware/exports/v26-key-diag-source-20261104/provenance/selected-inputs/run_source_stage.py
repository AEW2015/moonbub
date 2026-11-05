"""Offline source/adapters only. Never invokes ESP target build or hardware."""
from pathlib import Path
import subprocess,hashlib,json,difflib,re
P=Path(__file__).resolve().parent;E=P/'evidence';E.mkdir(exist_ok=True)
CARGO=Path.home()/'.cargo/bin/cargo.exe';FMT=Path.home()/'.cargo/bin/rustfmt.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,name):
 r=subprocess.run([str(x) for x in cmd],capture_output=True,text=True)
 (E/name).write_text(r.stdout+r.stderr,encoding='utf-8');r.check_returncode();return r.stdout+r.stderr
def sources():
 result={p.relative_to(P).as_posix():sha(p) for folder in ['handheld','handheld-dfu','tests','tools'] for p in (P/folder).rglob('*') if p.is_file() and not any(x in p.parts for x in ['target','__pycache__','.git'])}
 for rel in json.loads((P/'parent-v25.json').read_text())['sources']:
  if rel not in result:result[rel]=sha(P/rel)
 return result
def main():
 parent=json.loads((P/'parent-v25.json').read_text());base=Path(parent['origin'])
 assert sha(base/'evidence/manifest.json')==parent['manifest_sha256']
 for rel,h in parent['sources'].items():assert sha(base/rel)==h,rel
 for rel,row in parent['artifacts'].items():assert sha(base/rel)==row['sha256'],rel
 run(['python',P/'run_core_tests.py'],'model-runner.log')
 log=run([CARGO,'+stable','test','--offline','--manifest-path',P/'tests/sdk-host/Cargo.toml','--','--test-threads=1','--nocapture'],'sdk-host-tests.log')
 tests=int(re.search(r'test result: ok\. (\d+) passed; 0 failed',log)[1])
 current=sources();changed={rel:h for rel,h in current.items() if parent['sources'].get(rel)!=h}
 diffs=[];parsed=[]
 for rel in sorted(changed):
  if not rel.endswith('.rs'):continue
  f=P/rel;old=(base/rel).read_text(encoding='utf-8') if (base/rel).exists() else ''
  diffs.extend(difflib.unified_diff(old.splitlines(True),f.read_text(encoding='utf-8').splitlines(True),fromfile='v25/'+rel,tofile='v26/'+rel))
  # --emit stdout parses without mutating existing SDK source formatting.
  r=subprocess.run([str(FMT),'+stable','--edition','2021','--emit','stdout','--config','skip_children=true',str(f)],capture_output=True,text=True)
  assert r.returncode==0,(rel,r.stderr);parsed.append(rel)
 (E/'integration.diff').write_text(''.join(diffs),encoding='utf-8')
 # These exact production sources must not gain a relaxed wire/audio identity.
 unchanged=['streaming/av_wire.rs','streaming/protocol.rs','streaming/audio_io.rs','streaming/audio_snapshot.rs','streaming/adpcm.rs','streaming/compressed_queue.rs']
 for rel in unchanged:assert current['handheld/src/'+rel]==parent['sources']['handheld/src/'+rel],rel
 for rel,h in parent['sources'].items():
  if 'sdkconfig' in rel or rel.endswith('Cargo.toml') or rel.endswith('Cargo.lock'):
   assert current[rel]==h,rel
 src=P/'handheld/src';driver=(src/'device/drivers/fpga/mod.rs').read_text()
 program=driver[driver.index('    pub fn program('):driver.index('    pub fn set_system_clock_rate')]
 assert program.index('authorization.begin()')<program.index('self.program_epoch.begin_program()')<program.index('self.pin_program_b.set_low()')
 assert 'CONTROL' not in program.replace('// Token-local check MUST precede epoch/pins; never locks CONTROL.','')
 assert 'v26-key-diag-access-20261104' in (src/'diag_pages.rs').read_text()
 assert (src/'streaming/mod.rs').read_text().count('.fpga.program(')==1
 assert (src/'bitstream/mod.rs').read_text().count('.program(')==2
 inventory=E/'source-bindings.json';inventory.write_text(json.dumps(current,sort_keys=True,indent=2)+'\n')
 model=json.loads((E/'core-results.json').read_text())
 contract=P.parents[2]/'docs/AKD1-COMPUTE-DIAGNOSTIC-20261104.md'
 result={'status':'SOURCE_ADAPTER_REVIEW_PASS','overall':'INCOMPLETE','source_inputs':len(current),'source_inventory_sha256':sha(inventory),'changed_sources':changed,'parsed_changed_rust':parsed,'model_tests':model['tests'],'compiler_expected_rejections':len(model['compiler_rejections']),'SDK_host_tests':tests,'SDK_host_layout':re.search(r'HOST_LAYOUT .*',log)[0],'resource_max_payload_bytes':int(re.search(r'RESOURCE_PAGE max_payload=(\d+)',log)[1]),'payload_lengths':[int(x) for x in re.findall(r'key_page index=\d+ bytes=(\d+)',log)],'parent':{'manifest_sha256':parent['manifest_sha256'],'source_inputs':len(parent['sources']),'artifacts':len(parent['artifacts']),'status':'UNCHANGED'},'wire_audio_SDK_defaults':'UNCHANGED','AKD1_contract_sha256':sha(contract),'worker_stack_declared_bytes':4096,'existing_stack_defaults':'UNCHANGED','target_check_build':'NOT_RUN_PENDING_ROOT_REVIEW','target_ELF_stack_and_heap':'NOT_RUN','physical_stack_log_framing_overhead_and_function':'NOT_RUN','hardware_actions':'NONE','limits':'Fake SDK callback evidence is not ESP ABI/HAL, physical exclusion/drain, timing or runtime stack evidence. External FPGA reset ABA remains unobservable under AKD1.'}
 result['review_inputs']={name:sha(P/name) for name in ['README.md','run_source_stage.py','run_core_tests.py','parent-v25.json']}
 result['artifacts']={p.name:sha(p) for p in E.iterdir() if p.is_file() and p.name not in ['source-stage-manifest.json'] and p.suffix not in ['.exe','.pdb']}
 (E/'source-stage-manifest.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
 print('SOURCE_ADAPTER_REVIEW_PASS',model['tests'],'model;',tests,'SDK-host;',len(model['compiler_rejections']),'expected rejects; target NOT_RUN; parent unchanged')
if __name__=='__main__':main()
