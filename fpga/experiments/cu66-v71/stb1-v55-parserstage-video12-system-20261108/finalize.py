from pathlib import Path
import hashlib,json,re,subprocess
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
b=json.loads((p/'bindings.json').read_text());run=json.loads((p/'rust-run-result.json').read_text());assert run['returncode']==0
log=(p/'native-run.log').read_text();assert 'STB1_VIDEO12_SYSTEM_PASS'in log and 'panicked'not in log
for f,h in b['executed_RTL_CPP_support_inputs'].items():assert sha(f)==h,f
for f,h in b['harness_source_files'].items():assert sha(p/f)==h,f
for f,h in b['copied_Rust_all_files_sha256'].items():assert sha(p/f)==h,f
for f,h in b['package_packet_files_sha256'].items():assert sha(p/f)==h,f
for n in b['exact_firmware_source_match']:assert sha(p/'cu66'/n)==sha(Path(b['V55_origin'])/'handheld/src/cu66'/n),n
assert sha(p/'actual-rust.exe')==json.loads((p/'rust-compile-result.json').read_text())['compiled_executable_sha256']
for f,h in b['independent_goldens']['goldens_sha256'].items():assert sha(p/f)==h,f
assert len(b['independent_goldens']['goldens_sha256'])==48 and b['independent_goldens']['selected_oracle']=='layout-v2/goldens'
assert sha(p/'native-oracle/execution.json')==b['independent_goldens']['native_oracle_receipt_sha256']
assert sha(p/'python-reference-result.json')==b['independent_goldens']['Python_receipt_sha256']
assert sha(p/'layout-v2/independent-layout-proof.json')==b['independent_goldens']['independent_layout_proof_sha256']
proof=json.loads((p/'layout-v2/independent-layout-proof.json').read_text());assert proof['status']=='PASS_PREQUALIFIED_PAIR_AND_TWO_INDEPENDENT_SERIALIZERS_NEW12' and not proof['DUT_outputs_read']
for f,h in proof['source_sha256'].items():assert sha(f)==h,f
pyref=json.loads((p/'python-reference-result.json').read_text())
for f,h in pyref['imported_sources_sha256'].items():assert sha(f)==h,f
native=json.loads((p/'native-binary-binding.json').read_text())
for f,r in native['binaries'].items():assert sha(p/f)==r['executed_sha256']==sha(r['origin'])
assert b['source_package']['count']==b['source_package']['source_unique_frames']==12
assert log.count('MODELED_PREPARE_DELAY_US=200000')==12
for marker in ['words_written: 253440, words_verified: 253440','hud_cpu_us: [0, 0, 0]','accepted: 12, presented: 12, rejected: 0, underruns: 0','hu_extract_commands: [0, 0, 0]']:assert marker in log,marker
m_alloc=re.search(r'allocator: \[([^\]]+)\]',log);assert m_alloc
allocator=[int(x.strip())for x in m_alloc[1].split(',')];assert len(allocator)==6 and allocator[0]==98304 and allocator[2]<=98304 and allocator[5]==0
server=(p/'rtl-stderr.log').read_text();assert 'PLATFORM_SERVER_COMPLETE accepted=12 presented=12 rejected=0 underruns=0'in server and 'PLATFORM_FAIL'not in server
assert server.count('PARSER_STAGE19_EXECUTED visits=12')==1
assert subprocess.run(['python',str(p/'layout-v2/compare.py')]).returncode==0
c=json.loads((p/'layout-v2/comparison.json').read_text());assert c['status'].startswith('PASS')
stats=re.search(r'PLATFORM_SERVER_COMPLETE.*model_reads=(\d+) model_writes=(\d+) refreshes=(\d+)',server);assert stats
envelopes=[]
for i in range(12):
 packet=(p/f'packets/frame{i:03}.cu66').read_bytes();inner=int.from_bytes(packet[68:72],'little');magic=packet[76+inner:80+inner].decode('ascii');envelopes.append(magic)
assert envelopes==['HX33']*9+['HU25']*3,envelopes
result={'status':'PASS_EXACT_V55_RUST_STB1_CE_PLUS_PARSER_STAGE_VIDEO12','production_RTL_deltas':b['production_RTL_deltas_vs_selected_V028'],'parser_state19_visits':12,'accepted':12,'presented':12,'rejected':0,'underruns':0,'HUD_words_written':253440,'HUD_words_verified':253440,'canonical_mismatched_bytes':sum(x['canonical_mismatched_bytes']for x in c['frames']),'composed_mismatched_pixels':sum(x['composed_mismatched_pixels']for x in c['frames']),'displayed_HUD_mismatched_words':sum(x['displayed_HUD_mismatched_words']for x in c['frames']),'actual_composed_video_pixels':4147200,'native_arena':allocator,'front_bank_sequence':[x['front_bank']for x in c['frames']],'banks_exercised':sorted({x['front_bank']for x in c['frames']}),'bank2_covered':False,'HUD_envelopes':envelopes,'source_PTS_span_seconds':0.366666667,'source_kind':'NEW local motion-test first12; not120s or live','SDRAM_init':'zero','modeled_yield_us':100,'modeled_Prepare_us':200000,'native_CPU_virtual_timer_us':0,'model_reads':int(stats[1]),'model_writes':int(stats[2]),'model_refreshes':int(stats[3]),'wall_seconds':run['wall_seconds'],'binding_sha256':sha(p/'bindings.json'),'comparison_sha256':sha(p/'layout-v2/comparison.json'),'scope':'Positive functional composition only; no hardware, SDK/radio/SPI throughput, target fragmentation, SDF or fault-injection claim.'}
assert result['canonical_mismatched_bytes']==result['composed_mismatched_pixels']==result['displayed_HUD_mismatched_words']==0
(p/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
