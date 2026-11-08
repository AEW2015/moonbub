from pathlib import Path
import hashlib,json,re,subprocess
p=Path(__file__).resolve().parent.parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();b=json.loads((p/'bindings.json').read_text());run=json.loads((p/'rust-run-result.json').read_text());assert run['returncode']==0;log=(p/'native-run.log').read_text();assert 'STB1_VIDEO12_SYSTEM_PASS'in log and 'panicked'not in log
for f,h in b['executed_RTL_CPP_support_inputs'].items():assert sha(f)==h,f

layout_binding=json.loads((p/'layout-v2/bindings.json').read_text());assert sha(p/'bindings.json')==layout_binding['original_run_bindings_sha256']
for filename,expected in layout_binding['files_sha256'].items():assert sha(filename)==expected,filename
proof=json.loads((p/'layout-v2/independent-layout-proof.json').read_text());assert proof['status']=='PASS_PREQUALIFIED_PAIR_AND_TWO_INDEPENDENT_SERIALIZERS_NEW12' and not proof['DUT_outputs_read']
for filename,expected in proof['source_sha256'].items():assert sha(filename)==expected,filename
for filename,expected in proof['goldens_sha256'].items():assert sha(p/filename)==expected,filename


for f,h in b['independent_goldens']['goldens_sha256'].items():assert sha(p/f)==h,f
for f,h in b['package_packet_files_sha256'].items():assert sha(p/f)==h,f
assert sha(p/'native-oracle/execution.json')==b['independent_goldens']['native_oracle_receipt_sha256']
assert sha(p/'python-reference-result.json')==b['independent_goldens']['Python_receipt_sha256']
pyref=json.loads((p/'python-reference-result.json').read_text())
for f,h in pyref['imported_sources_sha256'].items():assert sha(f)==h,f
assert b['source_package']['count']==b['source_package']['source_unique_frames']==12
m_alloc=re.search(r'allocator: \[([^\]]+)\]',log);assert m_alloc
allocator=[int(x.strip())for x in m_alloc[1].split(',')];assert len(allocator)==6 and allocator[0]==98304 and allocator[2]<=98304 and allocator[5]==0

for f,h in b['harness_source_files'].items():assert sha(p/f)==h,f
assert sha(p/'actual-rust.exe')==b['compiled_host_executable_sha256']
for n in b['exact_firmware_source_match']:assert sha(p/'cu66'/n)==sha(Path(b['V55_origin'])/'handheld/src/cu66'/n),n
assert log.count('MODELED_PREPARE_DELAY_US=200000')==12
assert 'words_written: 253440, words_verified: 253440'in log
assert 'hud_cpu_us: [0, 0, 0]'in log
assert 'accepted: 12, presented: 12, rejected: 0, underruns: 0'in log
assert 'hu_extract_commands: [0, 0, 0]'in log
assert subprocess.run(['python',str(p/'layout-v2/compare.py')]).returncode==0
c=json.loads((p/'layout-v2/comparison.json').read_text());assert c['status'].startswith('PASS')
server=(p/'rtl-stderr.log').read_text();assert 'PLATFORM_SERVER_COMPLETE accepted=12 presented=12 rejected=0 underruns=0'in server and 'PLATFORM_FAIL'not in server
witness=re.findall(r'STB1_POISON_FILLED words=(\d+) first=([0-9a-f]+) second=([0-9a-f]+) last=([0-9a-f]+)',server,re.I);assert len(witness)==1
assert (int(witness[0][0]),int(witness[0][1],16),int(witness[0][2],16),int(witness[0][3],16))==(16777216,0x8fa1,0x15c7,0xd9c7)
assert 'STB1_POISON_FILL_WITNESS_MISMATCH'not in server
m=re.search(r'PLATFORM_SERVER_COMPLETE.*model_reads=(\d+) model_writes=(\d+) refreshes=(\d+)',server);assert m
result={'status':'PASS_EXACT_V55_RUST_STB1_FULL_SYSTEM_VIDEO12_COMPOSITIONAL_LAYOUT_V2_SELECTED_V028_POISON','layout_proof_sha256':sha(p/'layout-v2/independent-layout-proof.json'),'golden_layout_proof_reused_from_completed_zero_init12':True,'selected_V028_RTL_unchanged':True,'CE_receiver_used':False,'runtime_array_witness_passed':True,'SDRAM_init':'deterministic nonzero address-dependent seedD14C5EED','modeled_yield_us':100,'front_bank_sequence':[x['front_bank']for x in c['frames']],'banks_exercised':sorted({x['front_bank']for x in c['frames']}),'native_arena':allocator,'source_frame_count':12,'source_unique_canvases':12,'source_PTS_span_seconds':0.366666667,'source_kind':'New local motion-test first 12 frames; not 120 seconds or live','actual_composed_video_pixels':4147200,'displayed_HUD_words':253440,'accepted':12,'presented':12,'rejected':0,'underruns':0,'HUD_words_written':253440,'HUD_words_verified':253440,'canonical_mismatched_bytes':sum(x['canonical_mismatched_bytes']for x in c['frames']),'composed_mismatched_pixels':sum(x['composed_mismatched_pixels']for x in c['frames']),'displayed_HUD_mismatched_words':sum(x['displayed_HUD_mismatched_words']for x in c['frames']),'modeled_prepare_delay_us_per_frame':200000,'native_CPU_virtual_timer_us':0,'native_HU_scalar_extract_commands':0,'simulation_model_reads':int(m[1]),'simulation_model_writes':int(m[2]),'simulation_model_refreshes':int(m[3]),'replay_wall_seconds':run['wall_seconds'],'scope':'Exact V55 receiver Rust+host native FFI, selected STB1 controller/decoder/SDRAM model/HBU/scanout. Direct CSR RPC; no board SPI/IDF/radio or physical throughput claim.','binding_sha256':sha(p/'bindings.json'),'comparison_sha256':sha(p/'layout-v2/comparison.json')};(p/'layout-v2/result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
