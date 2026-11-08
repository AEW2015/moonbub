"""Finalize only after native replay and independent actual-pixel comparison pass."""
from pathlib import Path
import hashlib,json,re
p=Path(__file__).resolve().parent;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def win(p):return Path(p.replace('/mnt/c/','C:/'))
source=json.loads((p/'source-binding.json').read_text());fixtures=json.loads((p/'fixture-binding.json').read_text());native=json.loads((p/'native-result.json').read_text());comparison=json.loads((p/'comparison.json').read_text());compile=json.loads((p/'compile-result.json').read_text());run=json.loads((p/'run-result.json').read_text())
assert compile['returncode']==run['returncode']==0
assert native['counts']==[2,2,0,0,0] and comparison['status']=='PASS_STB1_KEY_P_CANONICAL_HUD_RASTER'
assert native['HUD_words_written_compared']==42240 and native['alias_u32_writes']==10909
assert native['native_stats'][0]==98304 and native['native_stats'][2]<=98304 and native['native_stats'][5]==0
assert native['commands'].get('21',0)==0
assert all(sha(Path(f))==h for f,h in source['files_sha256'].items())
assert all(sha(Path(f))==h for f,h in fixtures['files_sha256'].items())
overlay=Path(source['overlay']);freeze=json.loads((overlay/'source-freeze.json').read_text());assert all(sha(overlay/'inputs'/f)==h for f,h in freeze.items())
assert 'PLATFORM_SERVER_COMPLETE accepted=2 presented=2 rejected=0 underruns=0'in(p/'rtl-stderr.log').read_text()
assert 'PLATFORM_FAIL'not in(p/'rtl-stderr.log').read_text()
result={'supported_raw_SPI_max_bytes':1024,'arbitrary_oversized_raw_burst_failclosed':False,'wrap_limitation_diagnostic':'wrap-limit-v001/result.json','status':'PASS_STB1_KEY_P_FULL_SYSTEM_COMPOSITIONAL','frames':2,'accepted':2,'presented':2,'rejected':0,'underruns':0,'native_staging_faults':0,'actual_HUD_SDRAM_words_written':42240,'actual_HUD_SDRAM_words_compared':42240,'canonical_and_composed_scanout':comparison,'native_and_model':native,'compile_seconds':compile['seconds'],'run_wall_seconds':run['seconds'],'all_bound_sources_and_fixture_hashes_rechecked':True,'source_binding_count':len(source['files_sha256']),'overlay_source_freeze_sha256':sha(overlay/'source-freeze.json'),'tool_versions':json.loads((p/'tool-versions.json').read_text()),'assumptions':source['service_assumptions'],'scope':'Exact selected STB1 controller + V027 decoder/memory/cache/scanout RTL and retained SDRAM pin model; direct CSR RPC, actual host native endpoint; explicit200ms modeled Prepare delay; no physical SPI/CDC/PLL in this harness, no hardware or target CPU throughput claim; separate pin test qualifies transport composition.'}
(p/'result.json').write_text(json.dumps(result,indent=2));print(result['status'],result['run_wall_seconds'])
