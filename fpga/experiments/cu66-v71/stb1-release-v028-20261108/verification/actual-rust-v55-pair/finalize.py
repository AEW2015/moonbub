from pathlib import Path
import hashlib,json,re,subprocess
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();b=json.loads((p/'bindings.json').read_text());run=json.loads((p/'rust-run-result.json').read_text());assert run['returncode']==0;log=(p/'native-run.log').read_text();assert 'STB1_KEY_P_SYSTEM_PASS'in log and 'panicked'not in log
for f,h in b['executed_RTL_CPP_support_inputs'].items():assert sha(f)==h,f
for f,h in b['harness_source_files'].items():assert sha(p/f)==h,f
assert sha(p/'actual-rust.exe')==b['compiled_host_executable_sha256']
for n in b['exact_firmware_source_match']:assert sha(p/'cu66'/n)==sha(Path(b['V55_origin'])/'handheld/src/cu66'/n),n
assert log.count('MODELED_PREPARE_DELAY_US=200000')==2
assert 'words_written: 42240, words_verified: 42240'in log
assert 'hud_cpu_us: [0, 0, 0]'in log
assert 'accepted: 2, presented: 2, rejected: 0, underruns: 0'in log
assert 'hu_extract_commands: [0, 0, 0]'in log
assert subprocess.run(['python',str(p/'compare.py')]).returncode==0
c=json.loads((p/'comparison.json').read_text());assert c['status'].startswith('PASS')
server=(p/'rtl-stderr.log').read_text();assert 'PLATFORM_SERVER_COMPLETE accepted=2 presented=2 rejected=0 underruns=0'in server and 'PLATFORM_FAIL'not in server
m=re.search(r'PLATFORM_SERVER_COMPLETE.*model_reads=(\d+) model_writes=(\d+) refreshes=(\d+)',server);assert m
result={'status':'PASS_EXACT_V55_RUST_STB1_FULL_SYSTEM_KEY_P_COMPOSITIONAL','accepted':2,'presented':2,'rejected':0,'underruns':0,'HUD_words_written':42240,'HUD_words_verified':42240,'canonical_mismatched_bytes':sum(x['canonical_mismatched_bytes']for x in c['frames']),'composed_mismatched_pixels':sum(x['composed_mismatched_pixels']for x in c['frames']),'displayed_HUD_mismatched_words':sum(x['displayed_HUD_mismatched_words']for x in c['frames']),'modeled_prepare_delay_us_per_frame':200000,'native_CPU_virtual_timer_us':0,'native_HU_scalar_extract_commands':0,'simulation_model_reads':int(m[1]),'simulation_model_writes':int(m[2]),'simulation_model_refreshes':int(m[3]),'replay_wall_seconds':run['wall_seconds'],'scope':'Exact V55 receiver Rust+host native FFI, selected STB1 controller/decoder/SDRAM model/HBU/scanout. Direct CSR RPC; no board SPI/IDF/radio or physical throughput claim.','binding_sha256':sha(p/'bindings.json'),'comparison_sha256':sha(p/'comparison.json')};(p/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
